"""Local foundation HTTP surfaces: identity, settings, durable learner documents."""
from contextlib import asynccontextmanager
from datetime import datetime, timedelta, timezone
import hashlib
import ipaddress
import json
from pathlib import Path
import re
import secrets
from typing import Annotated, Literal

from fastapi import FastAPI, Request, Depends, HTTPException, Form, Path as PathParam
from fastapi.responses import RedirectResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, ConfigDict, Field
from sqlalchemy import select, text, delete
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from app.config import Settings
from app.models.user import User
from app.models.config import AppConfig
from app.models.workspace import LoginSession, WorkspaceDocument
from app.security.encryption import SecretStore
from app.security.passwords import hash_password, verify_password
from app.templating import templates

BASE = Path(__file__).resolve().parent.parent


class DocumentWrite(BaseModel):
    model_config = ConfigDict(extra="forbid")
    revision: int = Field(ge=0, le=2147483646, strict=True)
    data: dict


def digest(token):
    return hashlib.sha256(token.encode()).hexdigest()


def create_app(config: Settings, session_factory=None):
    @asynccontextmanager
    async def lifespan(app):
        engine = None
        if session_factory is None:
            if not config.database_url:
                raise RuntimeError("LA_DATABASE_URL is required; run migrations before startup")
            engine = create_async_engine(config.database_url)
            app.state.sessions = async_sessionmaker(engine, expire_on_commit=False)
        else:
            app.state.sessions = session_factory
        # Fail closed if migrations are absent; never create shared tables here.
        async with app.state.sessions() as db:
            await db.execute(select(AppConfig).limit(1))
        try:
            yield
        finally:
            if engine is not None:
                await engine.dispose()

    app = FastAPI(title="Learn Anything foundation", lifespan=lifespan)
    app.state.config = config
    app.mount("/static", StaticFiles(directory=BASE / "static"), name="static")

    @app.middleware("http")
    async def request_security(request, call_next):
        if request.method not in {"GET", "HEAD", "OPTIONS"}:
            # Browsers send Origin on same-origin POST forms and script requests.
            # Reject absent/null origin rather than permit form/login CSRF.
            expected = str(request.base_url).rstrip("/")
            if request.headers.get("origin") != expected:
                return JSONResponse({"detail": "Same-origin request required"}, status_code=403)
        response = await call_next(request)
        if not request.url.path.startswith("/static/"):
            response.headers["Cache-Control"] = "no-store"
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["Content-Security-Policy"] = "default-src 'self'; script-src 'none'; style-src 'self'; frame-ancestors 'none'; base-uri 'none'; form-action 'self'"
        return response

    async def current_user(request: Request):
        token = request.cookies.get("session", "")
        if not token or len(token) > 200:
            raise HTTPException(401, "Authentication required")
        async with app.state.sessions() as db:
            row = await db.get(LoginSession, digest(token))
            user = await db.get(User, row.user_id) if row and row.expires_at > datetime.now(timezone.utc) else None
            if user is None or not user.is_active:
                raise HTTPException(401, "Authentication required")
            return user

    async def admin(user: User = Depends(current_user)):
        if not user.is_admin:
            raise HTTPException(403, "Administrator required")
        return user

    async def setup_open(request: Request):
        try:
            local = request.client and ipaddress.ip_address(request.client.host).is_loopback
        except ValueError:
            local = False
        if not local or request.url.hostname not in {"localhost", "127.0.0.1", "::1"}:
            raise HTTPException(403, "Initial setup is available only on loopback")
        async with app.state.sessions() as db:
            if await db.get(AppConfig, "setup_complete"):
                raise HTTPException(409, "Setup is already complete")

    @app.get("/health")
    async def health():
        async with app.state.sessions() as db:
            await db.execute(text("SELECT 1"))
        return {"status": "ok", "version": "0.1.0", "database": "connected", "scope": "identity-and-documents", "graph_extensions": "unverified", "learning_engine": "not_implemented"}

    @app.get("/")
    async def root(request: Request):
        async with app.state.sessions() as db:
            complete = await db.get(AppConfig, "setup_complete")
        if complete is None:
            return RedirectResponse("/setup")
        if not request.cookies.get("session"):
            return RedirectResponse("/auth/login")
        user = await current_user(request)
        async with app.state.sessions() as db:
            docs = (await db.execute(select(WorkspaceDocument).where(WorkspaceDocument.user_id == user.id))).scalars().all()
        return templates.TemplateResponse(request, "workspace.html", {"user": user, "documents": docs})

    @app.get("/setup", dependencies=[Depends(setup_open)])
    async def setup(request: Request):
        return templates.TemplateResponse(request, "setup/account.html")

    @app.post("/setup/account", dependencies=[Depends(setup_open)])
    async def setup_account(email: str = Form(...), display_name: str = Form(...), password: str = Form(...)):
        email = email.strip().lower()
        name = display_name.strip()
        if not re.fullmatch(r"[^\s@]+@[^\s@]+\.[^\s@]+", email) or len(email) > 255 or not 1 <= len(name) <= 100 or not 12 <= len(password.encode()) <= 72:
            raise HTTPException(422, "Valid email/name and 12–72 byte password required")
        password_hash = hash_password(password)
        async with app.state.sessions() as db, db.begin():
            # Serialize competing initial admins across processes, not just requests.
            await db.execute(text("SELECT pg_advisory_xact_lock(624310097)"))
            if await db.get(AppConfig, "setup_complete"):
                raise HTTPException(409, "Setup is already complete")
            if (await db.execute(select(User.id).limit(1))).first():
                raise HTTPException(409, "Existing accounts require operator recovery")
            db.add(User(email=email, display_name=name, password_hash=password_hash, is_admin=True))
            db.add(AppConfig(key="setup_complete", value="true"))
        return RedirectResponse("/auth/login", status_code=303)

    @app.get("/auth/login")
    async def login_page(request: Request):
        return templates.TemplateResponse(request, "auth/login.html")

    @app.post("/auth/login")
    async def login(request: Request, email: str = Form(...), password: str = Form(...)):
        if len(password.encode()) > 72:
            raise HTTPException(401, "Invalid credentials")
        async with app.state.sessions() as db:
            user = (await db.execute(select(User).where(User.email == email.strip().lower(), User.provider == "local"))).scalar_one_or_none()
            # Always perform a hash check, including unknown accounts.
            valid = verify_password(password, user.password_hash if user and user.password_hash else app.state.dummy_hash)
            if not valid or user is None or not user.is_active:
                raise HTTPException(401, "Invalid credentials")
            old = request.cookies.get("session")
            if old:
                await db.execute(delete(LoginSession).where(LoginSession.token_hash == digest(old)))
            token = secrets.token_urlsafe(32)
            db.add(LoginSession(token_hash=digest(token), user_id=user.id, expires_at=datetime.now(timezone.utc) + timedelta(seconds=config.session_max_age)))
            await db.commit()
        response = RedirectResponse("/", status_code=303)
        response.set_cookie("session", token, httponly=True, secure=request.url.scheme == "https", samesite="strict", max_age=config.session_max_age)
        return response

    @app.post("/auth/logout")
    async def logout(request: Request, user: User = Depends(current_user)):
        async with app.state.sessions() as db:
            await db.execute(delete(LoginSession).where(LoginSession.token_hash == digest(request.cookies["session"])))
            await db.commit()
        response = RedirectResponse("/auth/login", status_code=303)
        response.delete_cookie("session")
        return response

    @app.get("/settings", dependencies=[Depends(admin)])
    async def settings_page(request: Request):
        async with app.state.sessions() as db:
            model = await db.get(AppConfig, "llm_model")
            key = await db.get(AppConfig, "llm_api_key")
        return templates.TemplateResponse(request, "settings/index.html", {"llm_model": model.value if model else "", "key_configured": key is not None})

    @app.post("/settings/llm", dependencies=[Depends(admin)])
    async def update_llm(api_key: str = Form(""), model: str = Form(...)):
        if not model.strip() or len(model) > 100 or len(api_key) > 4096:
            raise HTTPException(422, "Invalid model/key length")
        async with app.state.sessions() as db, db.begin():
            await db.execute(text("SELECT pg_advisory_xact_lock(624310098)"))
            values = [("llm_model", model.strip(), False)]
            if api_key:
                existing = await db.get(AppConfig, "llm_api_key")
                if existing and not Path(config.encryption_key_path).is_file():
                    raise HTTPException(503, "Encryption key unavailable; operator recovery required")
                try:
                    encrypted = SecretStore(config.encryption_key_path).encrypt(api_key)
                except (OSError, ValueError):
                    raise HTTPException(503, "Encryption key unavailable; operator recovery required") from None
                values.append(("llm_api_key", encrypted, True))
            for key, value, encrypted in values:
                stmt = insert(AppConfig).values(key=key, value=value, encrypted=encrypted)
                await db.execute(stmt.on_conflict_do_update(index_elements=[AppConfig.key], set_={"value": value, "encrypted": encrypted}))
        return RedirectResponse("/settings", status_code=303)

    Slug = Annotated[str, PathParam(pattern=r"^[a-z0-9][a-z0-9-]{0,99}$")]
    Kind = Literal["profile", "graph", "plan", "progress", "session"]

    @app.get("/api/workspaces/{skill_slug}/{document}")
    async def read_document(skill_slug: Slug, document: Kind, user: User = Depends(current_user)):
        async with app.state.sessions() as db:
            record = await db.get(WorkspaceDocument, (user.id, skill_slug, document))
            if record is None:
                raise HTTPException(404, "Document not found")
            return {"revision": record.revision, "data": record.data}

    @app.put("/api/workspaces/{skill_slug}/{document}")
    async def write_document(skill_slug: Slug, document: Kind, payload: DocumentWrite, user: User = Depends(current_user)):
        try:
            size = len(json.dumps(payload.data, allow_nan=False).encode())
        except ValueError:
            raise HTTPException(422, "Document must contain finite JSON values") from None
        if size > 256 * 1024:
            raise HTTPException(413, "Document exceeds 256 KiB")
        async with app.state.sessions() as db, db.begin():
            values = {"user_id": user.id, "skill_slug": skill_slug, "document": document, "revision": payload.revision + 1, "data": payload.data}
            stmt = insert(WorkspaceDocument).values(**values)
            if payload.revision == 0:
                stmt = stmt.on_conflict_do_nothing()
            else:
                # Updating an absent document is a conflict, never a phantom insert.
                from sqlalchemy import update
                stmt = update(WorkspaceDocument).where(WorkspaceDocument.user_id == user.id, WorkspaceDocument.skill_slug == skill_slug, WorkspaceDocument.document == document, WorkspaceDocument.revision == payload.revision).values(revision=payload.revision + 1, data=payload.data)
            record = (await db.execute(stmt.returning(WorkspaceDocument.revision))).first()
            if record is None:
                raise HTTPException(409, "Revision conflict; reload before saving")
        return {"revision": record[0], "data": payload.data}

    app.state.dummy_hash = hash_password(secrets.token_urlsafe(24))
    return app
