# app/main.py
from contextlib import asynccontextmanager
import logging
import structlog
from fastapi import FastAPI, Request
from fastapi.responses import RedirectResponse
from fastapi.staticfiles import StaticFiles
from starlette.middleware.base import BaseHTTPMiddleware
from app.config import settings
from app.templating import templates

structlog.configure(
    processors=[
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.JSONRenderer(),
    ],
    wrapper_class=structlog.make_filtering_bound_logger(
        getattr(logging, settings.log_level.upper(), logging.INFO)
    ),
)

log = structlog.get_logger()


@asynccontextmanager
async def lifespan(app: FastAPI):
    log.info("starting", version="0.1.0")
    from app.database import init_db
    await init_db()
    yield
    log.info("shutting_down")


app = FastAPI(title="Learn Anything", lifespan=lifespan)
app.mount("/static", StaticFiles(directory="static"), name="static")


# --- Routers ---
from app.routes.health import router as health_router
from app.routes.auth import router as auth_router
from app.security.oauth import router as oauth_router
from app.routes.setup import router as setup_router
from app.routes.settings import router as settings_router

app.include_router(health_router)
app.include_router(auth_router)
app.include_router(oauth_router)
app.include_router(setup_router)
app.include_router(settings_router)


# --- Setup Guard Middleware ---
class SetupGuardMiddleware(BaseHTTPMiddleware):
    """Redirects all non-setup requests to /setup until setup is complete.

    Checks the AppConfig table in the database rather than the static
    Settings object, so that completing setup takes effect without a restart.
    The result is cached in-memory after the first successful check to avoid
    a DB query on every request.
    """
    _setup_complete_cache: bool | None = None

    async def dispatch(self, request: Request, call_next):
        path = request.url.path
        # Allow health, static, and setup routes through unconditionally
        if path.startswith(("/health", "/static", "/setup")):
            return await call_next(request)
        # Check cached result first
        if self._setup_complete_cache is True:
            return await call_next(request)
        # Query the database for setup_complete flag
        from app.database import SessionLocal
        if SessionLocal is not None:
            from app.services.setup_service import is_setup_complete
            async with SessionLocal() as db:
                complete = await is_setup_complete(db)
            if complete:
                SetupGuardMiddleware._setup_complete_cache = True
                return await call_next(request)
        return RedirectResponse("/setup")


app.add_middleware(SetupGuardMiddleware)


@app.get("/")
async def root(request: Request):
    if settings.single_user:  # SINGLE_USER mode skips login
        return templates.TemplateResponse(request, "base.html")
    return RedirectResponse("/auth/login")
