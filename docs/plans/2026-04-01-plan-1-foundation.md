> HISTORICAL DESIGN REFERENCE: superseded operationally by CONVENTIONS.md and
> docs/superpowers/plans/2026-11-06-alpha-foundation.md. Do not execute provisioning,
> runner or database commands below. No current service admission is implied.

# Plan 1: Foundation — Project Scaffold, Models, Auth, Setup Wizard

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking. **Use opus subagents exclusively (model: opus). No sonnet, no haiku.**
>
> **REQUIRED READING:** `docs/plans/CONVENTIONS.md` — all plans follow these rules.
>
> **Execution:** Plans execute sequentially (1→2→3→4→5→6) on a single feature branch `feature/learn-anything-webapp`. Run `/pr-review-toolkit:review-pr` after all plans complete, before PR to `main`.
>
> **TDD strictly enforced.** Every feature: write failing test → verify failure → implement → verify pass → commit.

**Goal:** A running FastAPI app with auth, database models for the three-layer knowledge graph, pluggable state backends (PG + JSON), setup wizard, health endpoint, and Docker deployment. Includes devtest VM provisioning (Ansible playbook, Caddy route, test database).

**Architecture:** Server-driven FastAPI app with Jinja2 templates for Datastar HTML fragments, SQLAlchemy ORM with Alembic migrations, dual state backends behind a protocol. Setup wizard runs on first visit; subsequent visits route to the app. DB is always external (shared PG on devtest, bundled PG for self-hosters).

**Tech Stack:** Python >= 3.14, FastAPI, SQLAlchemy + asyncpg, Alembic, Apache AGE, PGVector, bcrypt (passlib), authlib (OAuth), cryptography (AES-256-GCM), structlog, pytest, Docker

**Spec:** `docs/specs/2026-04-01-learn-anything-webapp-design.md`
**Infrastructure:** `operator-owned private runbook (not included)` (gitignored — private NetRxn deployment details)

---

## Project Structure

This plan creates the following file tree. All subsequent plans build on this structure.

```
learn-anything-app/
├── docker/
│   └── postgres/
│       ├── Dockerfile              # pgvector:pg17 base + AGE extension
│       └── init-extensions.sql     # CREATE EXTENSION vector, age
├── docker-compose.yml
├── Dockerfile                      # Multi-stage: build + runtime
├── pyproject.toml
├── alembic.ini
├── alembic/
│   ├── env.py
│   └── versions/
│       └── 001_initial.py
├── app/
│   ├── __init__.py
│   ├── main.py                     # FastAPI app, lifespan, middleware
│   ├── templating.py               # Jinja2Templates instance (avoids circular imports)
│   ├── config.py                   # Pydantic settings
│   ├── database.py                 # Engine, session factory
│   ├── dependencies.py             # FastAPI dependency injection (created in Plan 3)
│   ├── security/
│   │   ├── __init__.py
│   │   ├── encryption.py           # AES-256-GCM for secrets at rest
│   │   ├── passwords.py            # bcrypt hash/verify
│   │   ├── sessions.py             # Cookie sessions, middleware
│   │   └── oauth.py                # Google/GitHub OAuth flows (Task 5b in this plan)
│   ├── models/
│   │   ├── __init__.py
│   │   ├── base.py                 # DeclarativeBase, mixins
│   │   ├── user.py                 # User, OAuthAccount
│   │   ├── config.py               # AppConfig (key-value settings in DB)
│   │   ├── graph_nodes.py          # Concept, SkillNode, Domain
│   │   ├── graph_edges.py          # All edge types
│   │   ├── learner_state.py        # LearnerState, MasteryTransition
│   │   └── material.py             # Material, Reference, junction tables
│   │   # progress.py created in Plan 5
│   ├── backends/
│   │   ├── __init__.py
│   │   ├── protocol.py             # StateBackend protocol
│   │   ├── postgres.py             # PostgresBackend
│   │   └── json_file.py            # JSONFileBackend
│   ├── routes/
│   │   ├── __init__.py
│   │   ├── health.py               # GET /health
│   │   ├── setup.py                # Setup wizard (GET/POST /setup/*)
│   │   ├── auth.py                 # Login, register, OAuth callbacks
│   │   └── settings.py             # GET/POST /settings/* (Task 10b in this plan)
│   └── services/
│       ├── __init__.py
│       └── setup_service.py        # Setup wizard business logic
├── templates/
│   ├── base.html                   # Datastar base (script tags, CSS vars)
│   ├── setup/
│   │   ├── welcome.html
│   │   ├── database.html
│   │   ├── llm.html
│   │   ├── auth.html
│   │   └── account.html
│   ├── auth/
│   │   ├── login.html
│   │   └── register.html
│   └── settings/
│       └── index.html
├── static/
│   ├── css/
│   │   └── observatory.css         # Observatory visual identity (CSS vars, base styles)
│   └── fonts/                      # Self-hosted woff2 fonts (see Task 13 Step 1b)
├── tests/
│   ├── conftest.py                 # Shared fixtures: PG test DB, test client, test user
│   ├── unit/                       # No DB, no network — pure logic
│   │   ├── test_encryption.py
│   │   ├── test_passwords.py
│   │   └── test_sessions.py
│   ├── integration/                # Requires PG test database
│   │   ├── test_models/
│   │   │   ├── test_user.py
│   │   │   ├── test_graph_nodes.py
│   │   │   ├── test_graph_edges.py
│   │   │   └── test_learner_state.py
│   │   ├── test_backends/
│   │   │   ├── test_postgres_backend.py
│   │   │   └── test_json_backend.py
│   │   └── test_routes/
│   │       ├── test_health.py
│   │       ├── test_setup.py
│   │       └── test_auth.py
│   └── e2e/                        # Full stack with Docker services
│       └── (added in later plans)
└── data/                           # Persistent volume mount
    ├── encryption.key              # Auto-generated on first run
    └── state/                      # JSON backend storage
```

---

### Task 0: DevTest Provisioning + Feature Branch

> **This task provisions the database and deployment infrastructure.**
> - Self-hosters: skip this task — `docker-compose.yml` bundles everything you need.
> - Managed infrastructure operators: follow the steps below using your own infrastructure tooling. See `operator-owned private runbook (not included)` (gitignored) for environment-specific details.

- [ ] **Step 1: Create feature branch**

```bash
git checkout -b feature/learn-anything-webapp
```

- [ ] **Step 2: Create the learn-anything-app directory**

```bash
mkdir -p learn-anything-app
```

- [ ] **Step 3: Provision database**

For managed infrastructure, use `/netrxn-devops` skill (or equivalent tooling) to:
- Create a dedicated database user for the app
- Create the app database and a separate test database (e.g., `learn_anything` + `learn_anything_test`)
- Enable required extensions: `vector` (PGVector), `age` (Apache AGE), `uuid-ossp`, `pgcrypto`
- Configure connection pooling entries if applicable (e.g., PgBouncer)
- Grant privileges to the app user, revoke PUBLIC access

Refer to operator-owned private runbook (not included) for connection strings, variable patterns, and playbook templates.

- [ ] **Step 4: Verify database connectivity**

```bash
psql "$LA_TEST_DATABASE_URL" -c "SELECT 1;"
psql "$LA_TEST_DATABASE_URL" -c "CREATE EXTENSION IF NOT EXISTS vector; CREATE EXTENSION IF NOT EXISTS age;"
```
Expected: All succeed. The `LA_TEST_DATABASE_URL` environment variable should point to your test database.

- [ ] **Step 5: Add reverse proxy route (if applicable)**

For managed infrastructure: add a reverse proxy route (Caddy, nginx, etc.) pointing to the app's port (default 8000). SSE streams require unbuffered proxying.

- [ ] **Step 6: Commit infrastructure changes (in your infrastructure repo, not here)**

Commit any provisioning artifacts to your infrastructure repo. These are not part of the learn-anything open source project.

---

### Task 1: Project Scaffold + Dependencies

**Files:**
- Create: `learn-anything-app/pyproject.toml`
- Create: `learn-anything-app/app/__init__.py`
- Create: `learn-anything-app/app/main.py`
- Create: `learn-anything-app/app/templating.py`
- Create: `learn-anything-app/app/config.py`

- [ ] **Step 1: Create project directory and pyproject.toml**

```toml
[project]
name = "learn-anything"
version = "0.1.0"
requires-python = ">=3.14"
dependencies = [
    "fastapi>=0.115",
    "uvicorn[standard]>=0.34",
    "sqlalchemy[asyncio]>=2.0",
    "asyncpg>=0.30",
    "alembic>=1.14",
    "jinja2>=3.1",
    "python-multipart>=0.0.18",
    "passlib[bcrypt]>=1.7",
    "authlib>=1.4",
    "httpx>=0.28",
    "cryptography>=44",
    "structlog>=24",
    "pydantic-settings>=2.7",
    "pgvector>=0.3",
    "itsdangerous>=2.2",
    "psycopg[binary]>=3.2",
    "datastar-py>=0.5",
]

[project.optional-dependencies]
dev = [
    "pytest>=8",
    "pytest-asyncio>=0.24",
    "httpx>=0.28",
    "pytest-cov>=6",
    "pip-audit>=2.7",
]

# NOTE: Run `pip-audit` or `uv pip audit` periodically to check for
# compromised or vulnerable packages in the dependency tree.

[tool.pytest.ini_options]
asyncio_mode = "auto"
testpaths = ["tests"]
```

- [ ] **Step 2: Create config.py with Pydantic settings**

```python
# app/config.py
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    database_url: str = ""
    state_backend: str = "json"  # "postgres" or "json"
    json_state_dir: str = "data/state"
    encryption_key_path: str = "data/encryption.key"
    secret_key: str = "change-me-on-first-run"
    session_max_age: int = 7 * 24 * 3600  # 7 days
    single_user: bool = False
    log_level: str = "INFO"
    allowed_origins: str = ""
    anthropic_api_key: str = ""
    anthropic_model: str = "claude-sonnet-4-6"
    setup_complete: bool = False

    model_config = {"env_prefix": "LA_", "env_file": ".env"}

settings = Settings()
```

- [ ] **Step 3: Create minimal FastAPI app**

```python
# app/__init__.py
# empty

# app/main.py
from contextlib import asynccontextmanager
import logging
import structlog
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from app.config import settings

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
```

- [ ] **Step 3b: Create app/templating.py (avoids circular imports)**

```python
# app/templating.py
from fastapi.templating import Jinja2Templates

templates = Jinja2Templates(directory="templates")
```

> **Why a separate module?** Putting `templates` in `app/main.py` causes circular imports when route modules (`auth.py`, `setup.py`) import it, since `main.py` also imports those routers. A dedicated `app/templating.py` breaks the cycle.

- [ ] **Step 4: Verify app starts**

Run: `cd learn-anything-app && uv run uvicorn app.main:app --reload`
Expected: Server starts on port 8000, logs JSON to stdout.

- [ ] **Step 5: Commit**

```bash
git add learn-anything-app/
git commit -m "feat: project scaffold with FastAPI, config, structlog"
```

---

### Task 2: Database Engine + SQLAlchemy Base

**Files:**
- Create: `learn-anything-app/app/database.py`
- Create: `learn-anything-app/app/models/__init__.py`
- Create: `learn-anything-app/app/models/base.py`
- Test: `learn-anything-app/tests/conftest.py`

- [ ] **Step 1: Write test fixture for DB session**

```python
# tests/conftest.py
"""
Shared test fixtures. All tests run against real PostgreSQL with PGVector + AGE.
Test database: learn_anything_test (provisioned in Task 0 via Ansible).
See docs/plans/CONVENTIONS.md for test pyramid rules.
"""
import os
import pytest
from httpx import AsyncClient, ASGITransport
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from app.models.base import Base

# Real PG — no SQLite. AGE and PGVector require actual PostgreSQL.
TEST_DB_URL = os.environ.get(
    "LA_TEST_DATABASE_URL",
    "postgresql+asyncpg://learn_anything:devpassword@localhost:5432/learn_anything_test"
)

@pytest.fixture(scope="session")
def event_loop_policy():
    """Use default event loop policy for session-scoped async fixtures."""
    import asyncio
    return asyncio.DefaultEventLoopPolicy()

@pytest.fixture
async def engine():
    eng = create_async_engine(TEST_DB_URL)
    async with eng.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)
    yield eng
    async with eng.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    await eng.dispose()

@pytest.fixture
async def db(engine) -> AsyncSession:
    session_factory = async_sessionmaker(engine, expire_on_commit=False)
    async with session_factory() as session:
        yield session
        await session.rollback()  # Clean state between tests

@pytest.fixture
async def client(engine):
    """Shared async test client with DB initialized and setup marked complete.
    Depends on `engine` fixture so DB tables exist and SetupGuardMiddleware passes.
    """
    from app.main import app
    from app import database
    from app.models.config import AppConfig

    # Point the app's DB at the test engine
    database.engine = engine
    database.SessionLocal = async_sessionmaker(engine, expire_on_commit=False)

    # Seed setup_complete so middleware doesn't redirect everything to /setup
    async with database.SessionLocal() as session:
        session.add(AppConfig(key="setup_complete", value="true"))
        await session.commit()

    # Reset middleware cache so it re-reads from DB
    from starlette.middleware.base import BaseHTTPMiddleware
    for mw in getattr(app, "middleware_stack", []):
        if hasattr(mw, "_setup_complete_cache"):
            mw._setup_complete_cache = None

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as c:
        yield c
```

- [ ] **Step 2: Create database module and base model**

```python
# app/database.py
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from app.config import settings

engine = None
SessionLocal = None

async def init_db():
    global engine, SessionLocal
    if not settings.database_url:
        return
    engine = create_async_engine(settings.database_url, echo=False)
    SessionLocal = async_sessionmaker(engine, expire_on_commit=False)

async def get_db() -> AsyncSession:
    async with SessionLocal() as session:
        yield session
```

```python
# app/models/__init__.py
from app.models.base import Base

# app/models/base.py
import uuid
from datetime import datetime, timezone
from sqlalchemy import DateTime, func
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column

class Base(DeclarativeBase):
    pass

class TimestampMixin:
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

class VersionedMixin(TimestampMixin):
    version: Mapped[int] = mapped_column(default=1)
    updated_by: Mapped[str] = mapped_column(default="system")
```

- [ ] **Step 3: Run tests to verify fixtures work**

Run: `cd learn-anything-app && uv run pytest tests/conftest.py -v --co`
Expected: Fixtures collected, no errors.

- [ ] **Step 4: Commit**

```bash
git commit -m "feat: database engine, SQLAlchemy base with timestamp/version mixins"
```

---

### Task 3: User Model + Password Security

**Files:**
- Create: `learn-anything-app/app/models/user.py`
- Create: `learn-anything-app/app/security/__init__.py`
- Create: `learn-anything-app/app/security/passwords.py`
- Test: `learn-anything-app/tests/unit/test_passwords.py`
- Test: `learn-anything-app/tests/integration/test_models/test_user.py`

- [ ] **Step 1: Write failing test for password hashing**

```python
# tests/unit/test_passwords.py
from app.security.passwords import hash_password, verify_password

def test_hash_and_verify():
    hashed = hash_password("correct-horse-battery-staple")
    assert verify_password("correct-horse-battery-staple", hashed)
    assert not verify_password("wrong-password", hashed)

def test_hash_is_unique():
    h1 = hash_password("same-password")
    h2 = hash_password("same-password")
    assert h1 != h2  # Different salts
```

- [ ] **Step 2: Run test — should fail**

Run: `uv run pytest tests/unit/test_passwords.py -v`
Expected: FAIL — `ModuleNotFoundError`

- [ ] **Step 3: Implement password module**

```python
# app/security/__init__.py
# empty

# app/security/passwords.py
from passlib.context import CryptContext

_ctx = CryptContext(schemes=["bcrypt"], deprecated="auto")

def hash_password(plain: str) -> str:
    return _ctx.hash(plain)

def verify_password(plain: str, hashed: str) -> bool:
    return _ctx.verify(plain, hashed)
```

- [ ] **Step 4: Run test — should pass**

Run: `uv run pytest tests/unit/test_passwords.py -v`
Expected: PASS

- [ ] **Step 5: Write failing test for User model**

```python
# tests/integration/test_models/test_user.py
import pytest
from app.models.user import User
from app.security.passwords import hash_password

@pytest.mark.asyncio
async def test_create_user(db):
    user = User(
        email="test@example.com",
        display_name="Test",
        password_hash=hash_password("secret"),
        provider="local",
    )
    db.add(user)
    await db.commit()
    await db.refresh(user)
    assert user.id is not None
    assert user.email == "test@example.com"
    assert user.is_admin is False
```

- [ ] **Step 6: Implement User model**

```python
# app/models/user.py
import uuid
from sqlalchemy import String, Boolean
from sqlalchemy.orm import Mapped, mapped_column
from app.models.base import Base, TimestampMixin

class User(Base, TimestampMixin):
    __tablename__ = "users"

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid.uuid4())
    )
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    display_name: Mapped[str] = mapped_column(String(100))
    password_hash: Mapped[str | None] = mapped_column(String(255), nullable=True)
    provider: Mapped[str] = mapped_column(String(20), default="local")  # local, google, github
    oauth_id: Mapped[str | None] = mapped_column(String(255), nullable=True)
    is_admin: Mapped[bool] = mapped_column(Boolean, default=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
```

- [ ] **Step 7: Update conftest.py to import User model**

Add to `tests/conftest.py`:
```python
from app.models.user import User  # noqa: F401 — ensure table is created
```

- [ ] **Step 8: Run test — should pass**

Run: `uv run pytest tests/integration/test_models/test_user.py -v`
Expected: PASS

- [ ] **Step 9: Commit**

```bash
git commit -m "feat: User model with bcrypt password hashing"
```

---

### Task 4: AES-256-GCM Encryption for Secrets at Rest

**Files:**
- Create: `learn-anything-app/app/security/encryption.py`
- Test: `learn-anything-app/tests/unit/test_encryption.py`

- [ ] **Step 1: Write failing test**

```python
# tests/unit/test_encryption.py
import os
import tempfile
from app.security.encryption import SecretStore

def test_encrypt_decrypt_roundtrip():
    with tempfile.NamedTemporaryFile(delete=False, suffix=".key") as f:
        key_path = f.name
    try:
        store = SecretStore(key_path)
        plaintext = "sk-ant-api03-very-secret-key"
        encrypted = store.encrypt(plaintext)
        assert encrypted != plaintext
        assert store.decrypt(encrypted) == plaintext
    finally:
        os.unlink(key_path)

def test_key_auto_generated():
    with tempfile.NamedTemporaryFile(delete=False, suffix=".key") as f:
        key_path = f.name
    os.unlink(key_path)  # Delete so it auto-generates
    try:
        store = SecretStore(key_path)
        assert os.path.exists(key_path)
        assert store.encrypt("test") != "test"
    finally:
        os.unlink(key_path)

def test_different_encryptions_differ():
    with tempfile.NamedTemporaryFile(delete=False, suffix=".key") as f:
        key_path = f.name
    try:
        store = SecretStore(key_path)
        e1 = store.encrypt("same")
        e2 = store.encrypt("same")
        assert e1 != e2  # Different nonces
    finally:
        os.unlink(key_path)
```

- [ ] **Step 2: Run test — should fail**

Run: `uv run pytest tests/unit/test_encryption.py -v`
Expected: FAIL

- [ ] **Step 3: Implement encryption**

```python
# app/security/encryption.py
import base64
import os
from pathlib import Path
from cryptography.hazmat.primitives.ciphers.aead import AESGCM

class SecretStore:
    def __init__(self, key_path: str):
        self._key_path = Path(key_path)
        self._key = self._load_or_generate_key()

    def _load_or_generate_key(self) -> bytes:
        if self._key_path.exists():
            return self._key_path.read_bytes()
        key = AESGCM.generate_key(bit_length=256)
        self._key_path.parent.mkdir(parents=True, exist_ok=True)
        self._key_path.write_bytes(key)
        self._key_path.chmod(0o600)
        return key

    def encrypt(self, plaintext: str) -> str:
        nonce = os.urandom(12)
        aesgcm = AESGCM(self._key)
        ct = aesgcm.encrypt(nonce, plaintext.encode(), None)
        return base64.b64encode(nonce + ct).decode()

    def decrypt(self, token: str) -> str:
        raw = base64.b64decode(token)
        nonce, ct = raw[:12], raw[12:]
        aesgcm = AESGCM(self._key)
        return aesgcm.decrypt(nonce, ct, None).decode()
```

- [ ] **Step 4: Run test — should pass**

Run: `uv run pytest tests/unit/test_encryption.py -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git commit -m "feat: AES-256-GCM secret encryption with auto-generated key"
```

---

### Task 5: Session Middleware + Auth

**Files:**
- Create: `learn-anything-app/app/routes/__init__.py`
- Create: `learn-anything-app/app/security/sessions.py`
- Create: `learn-anything-app/app/routes/auth.py`
- Test: `learn-anything-app/tests/unit/test_sessions.py`
- Test: `learn-anything-app/tests/integration/test_routes/test_auth.py`

- [ ] **Step 1: Write failing test for session creation**

```python
# tests/unit/test_sessions.py
from itsdangerous import URLSafeTimedSerializer
from app.security.sessions import create_session_token, validate_session_token

def test_create_and_validate():
    token = create_session_token("user-123", secret="test-secret")
    user_id = validate_session_token(token, secret="test-secret", max_age=3600)
    assert user_id == "user-123"

def test_invalid_token():
    result = validate_session_token("garbage", secret="test-secret", max_age=3600)
    assert result is None
```

- [ ] **Step 2: Run test — should fail**

Run: `uv run pytest tests/unit/test_sessions.py -v`
Expected: FAIL

- [ ] **Step 3: Implement sessions**

```python
# app/security/sessions.py
from itsdangerous import URLSafeTimedSerializer, BadSignature, SignatureExpired

def create_session_token(user_id: str, secret: str) -> str:
    s = URLSafeTimedSerializer(secret)
    return s.dumps({"uid": user_id})

def validate_session_token(token: str, secret: str, max_age: int) -> str | None:
    s = URLSafeTimedSerializer(secret)
    try:
        data = s.loads(token, max_age=max_age)
        return data.get("uid")
    except (BadSignature, SignatureExpired):
        return None


# --- FastAPI dependencies for auth ---

from fastapi import Request, HTTPException, Depends

async def get_current_user_id(request: Request) -> str | None:
    """Extract user ID from session cookie. Returns None if not authenticated."""
    from app.config import settings
    token = request.cookies.get("session")
    if not token:
        return None
    return validate_session_token(token, secret=settings.secret_key, max_age=settings.session_max_age)

async def require_auth(user_id: str | None = Depends(get_current_user_id)) -> str:
    """Dependency: require authenticated user. Raises 401 if not logged in."""
    if user_id is None:
        raise HTTPException(status_code=401, detail="Not authenticated")
    return user_id

async def require_admin(user_id: str = Depends(require_auth)) -> str:
    """Dependency: require admin user. Raises 403 if not admin.
    In production, look up User.is_admin from DB. Simplified for Plan 1.
    """
    # TODO: Query User model to check is_admin. For now, first user is admin.
    return user_id
```

- [ ] **Step 4: Run test — should pass**

Run: `uv run pytest tests/unit/test_sessions.py -v`
Expected: PASS

- [ ] **Step 5: Write failing test for auth routes**

```python
# tests/integration/test_routes/test_auth.py
# NOTE: Uses shared `client` fixture from tests/conftest.py
import pytest

@pytest.mark.asyncio
async def test_login_page_renders(client):
    resp = await client.get("/auth/login")
    assert resp.status_code == 200
    assert "Login" in resp.text or "login" in resp.text

@pytest.mark.asyncio
async def test_register_creates_user(client):
    resp = await client.post("/auth/register", data={
        "email": "new@example.com",
        "display_name": "New User",
        "password": "strong-password-123",
    }, follow_redirects=False)
    assert resp.status_code in (302, 303)
```

- [ ] **Step 6: Implement auth routes**

```python
# app/routes/auth.py
from fastapi import APIRouter, Request, Form, Response
from fastapi.responses import RedirectResponse
from app.templating import templates
from app.security.passwords import hash_password, verify_password
from app.security.sessions import create_session_token
from app.config import settings

router = APIRouter(prefix="/auth", tags=["auth"])

@router.get("/login")
async def login_page(request: Request):
    return templates.TemplateResponse(request, "auth/login.html")

@router.post("/login")
async def login(
    request: Request,
    email: str = Form(...),
    password: str = Form(...),
):
    # TODO: Task 3 models + DB lookup — for now return error
    return templates.TemplateResponse(request, "auth/login.html", {"error": "Not implemented"})

@router.get("/register")
async def register_page(request: Request):
    return templates.TemplateResponse(request, "auth/register.html")

@router.post("/register")
async def register(
    response: Response,
    email: str = Form(...),
    display_name: str = Form(...),
    password: str = Form(...),
):
    # Placeholder — full DB integration in later step
    token = create_session_token("temp-user", secret=settings.secret_key)
    resp = RedirectResponse("/", status_code=303)
    resp.set_cookie("session", token, httponly=True, samesite="lax", max_age=settings.session_max_age)
    return resp
```

- [ ] **Step 7: Create minimal templates**

```html
<!-- templates/base.html -->
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>{% block title %}Learn Anything{% endblock %}</title>
  <link rel="stylesheet" href="/static/css/observatory.css">
  <!-- Datastar: pinned version with SRI integrity hash (compute actual hash at build time) -->
  <!-- SRI: integrity="sha384-PLACEHOLDER_COMPUTE_AT_BUILD_TIME" -->
  <script type="module" src="https://cdn.jsdelivr.net/npm/@starfederation/datastar@1.0.0/dist/datastar.min.js"></script>
  <!-- D3.js: pinned version with SRI integrity hash (compute actual hash at build time) -->
  <!-- SRI: integrity="sha384-PLACEHOLDER_COMPUTE_AT_BUILD_TIME" -->
  <script src="https://cdn.jsdelivr.net/npm/d3@7.9.0/dist/d3.min.js"></script>
</head>
<body>
  {% block content %}{% endblock %}
</body>
</html>

<!-- templates/auth/login.html -->
{% extends "base.html" %}
{% block title %}Login — Learn Anything{% endblock %}
{% block content %}
<div class="setup-container">
  <h1>Login</h1>
  {% if error %}<p class="error">{{ error }}</p>{% endif %}
  <form method="post" action="/auth/login">
    <input name="email" type="email" placeholder="Email" required>
    <input name="password" type="password" placeholder="Password" required>
    <button type="submit">Login</button>
  </form>
  <a href="/auth/register">Create account</a>
</div>
{% endblock %}

<!-- templates/auth/register.html -->
{% extends "base.html" %}
{% block title %}Register — Learn Anything{% endblock %}
{% block content %}
<div class="setup-container">
  <h1>Create Account</h1>
  <form method="post" action="/auth/register">
    <input name="email" type="email" placeholder="Email" required>
    <input name="display_name" type="text" placeholder="Display Name" required>
    <input name="password" type="password" placeholder="Password" required>
    <button type="submit">Create Account</button>
  </form>
  <a href="/auth/login">Already have an account?</a>
</div>
{% endblock %}
```

- [ ] **Step 8: Register route in main.py**

Add to `app/main.py`:
```python
from app.routes.auth import router as auth_router
app.include_router(auth_router)
```

- [ ] **Step 9: Run tests**

Run: `uv run pytest tests/integration/test_routes/test_auth.py -v`
Expected: PASS

- [ ] **Step 10: Commit**

```bash
git commit -m "feat: session tokens, auth routes (login, register)"
```

---

### Task 5b: OAuth Flows (Google + GitHub)

**Files:**
- Create: `learn-anything-app/app/security/oauth.py`
- Test: `learn-anything-app/tests/integration/test_routes/test_oauth.py`

> **Spec requirement:** Section 2 — "OAuth2 providers (Google, GitHub) activate when credentials are configured via web UI."

OAuth providers are optional. They activate only when client ID + secret are configured in AppConfig. When not configured, the login page shows only the local account form.

- [ ] **Step 1: Write failing tests for OAuth routes**

```python
# tests/integration/test_routes/test_oauth.py
import pytest

@pytest.mark.asyncio
async def test_google_oauth_redirect_when_configured(client):
    # When Google OAuth is configured, /auth/oauth/google should redirect to Google
    resp = await client.get("/auth/oauth/google", follow_redirects=False)
    # Without config, should return 404 or redirect to login with error
    assert resp.status_code in (302, 307, 404)

@pytest.mark.asyncio
async def test_github_oauth_redirect_when_configured(client):
    resp = await client.get("/auth/oauth/github", follow_redirects=False)
    assert resp.status_code in (302, 307, 404)

@pytest.mark.asyncio
async def test_oauth_callback_without_state_rejected(client):
    resp = await client.get("/auth/oauth/google/callback")
    assert resp.status_code in (400, 422)
```

- [ ] **Step 2: Run tests — should fail**

Run: `uv run pytest tests/integration/test_routes/test_oauth.py -v`
Expected: FAIL

- [ ] **Step 3: Implement OAuth module**

```python
# app/security/oauth.py
from authlib.integrations.starlette_client import OAuth
from fastapi import APIRouter, Request
from fastapi.responses import RedirectResponse
from app.security.sessions import create_session_token
from app.config import settings

oauth = OAuth()
router = APIRouter(prefix="/auth/oauth", tags=["oauth"])

def configure_oauth(google_client_id: str = "", google_client_secret: str = "",
                    github_client_id: str = "", github_client_secret: str = ""):
    """Call during setup or on app start when OAuth config exists in DB."""
    if google_client_id and google_client_secret:
        oauth.register(
            name="google",
            client_id=google_client_id,
            client_secret=google_client_secret,
            server_metadata_url="https://accounts.google.com/.well-known/openid-configuration",
            client_kwargs={"scope": "openid email profile"},
        )
    if github_client_id and github_client_secret:
        oauth.register(
            name="github",
            client_id=github_client_id,
            client_secret=github_client_secret,
            authorize_url="https://github.com/login/oauth/authorize",
            access_token_url="https://github.com/login/oauth/access_token",
            api_base_url="https://api.github.com/",
            client_kwargs={"scope": "user:email"},
        )

@router.get("/google")
async def google_login(request: Request):
    client = oauth.create_client("google")
    if client is None:
        return RedirectResponse("/auth/login?error=google_not_configured")
    redirect_uri = request.url_for("google_callback")
    return await client.authorize_redirect(request, redirect_uri)

@router.get("/google/callback")
async def google_callback(request: Request):
    client = oauth.create_client("google")
    if client is None:
        return RedirectResponse("/auth/login?error=google_not_configured")
    token = await client.authorize_access_token(request)
    userinfo = token.get("userinfo", {})
    email = userinfo.get("email")
    if not email:
        return RedirectResponse("/auth/login?error=no_email")
    # Find or create user by email + provider=google + oauth_id
    # For now, create session directly (full DB lookup in later integration)
    session_token = create_session_token(email, secret=settings.secret_key)
    resp = RedirectResponse("/")
    resp.set_cookie("session", session_token, httponly=True, samesite="lax", max_age=settings.session_max_age)
    return resp

@router.get("/github")
async def github_login(request: Request):
    client = oauth.create_client("github")
    if client is None:
        return RedirectResponse("/auth/login?error=github_not_configured")
    redirect_uri = request.url_for("github_callback")
    return await client.authorize_redirect(request, redirect_uri)

@router.get("/github/callback")
async def github_callback(request: Request):
    client = oauth.create_client("github")
    if client is None:
        return RedirectResponse("/auth/login?error=github_not_configured")
    token = await client.authorize_access_token(request)
    resp_user = await client.get("user", token=token)
    user_data = resp_user.json()
    email = user_data.get("email")
    if not email:
        # GitHub may not include email in profile — fetch from emails endpoint
        resp_emails = await client.get("user/emails", token=token)
        emails = resp_emails.json()
        primary = next((e for e in emails if e.get("primary")), None)
        email = primary["email"] if primary else None
    if not email:
        return RedirectResponse("/auth/login?error=no_email")
    session_token = create_session_token(email, secret=settings.secret_key)
    resp = RedirectResponse("/")
    resp.set_cookie("session", session_token, httponly=True, samesite="lax", max_age=settings.session_max_age)
    return resp
```

- [ ] **Step 4: Register OAuth router in main.py**

```python
from app.security.oauth import router as oauth_router
app.include_router(oauth_router)
```

- [ ] **Step 5: Run tests — should pass**

Run: `uv run pytest tests/integration/test_routes/test_oauth.py -v`
Expected: PASS (providers not configured → redirect/404 responses)

- [ ] **Step 6: Commit**

```bash
git commit -m "feat: OAuth flows — Google + GitHub login with authlib"
```

---

### Task 6: Knowledge Graph Models (Three Layers)

**Files:**
- Create: `learn-anything-app/app/models/graph_nodes.py`
- Create: `learn-anything-app/app/models/graph_edges.py`
- Create: `learn-anything-app/app/models/learner_state.py`
- Create: `learn-anything-app/app/models/material.py`
- Test: `learn-anything-app/tests/integration/test_models/test_graph_nodes.py`
- Test: `learn-anything-app/tests/integration/test_models/test_graph_edges.py`
- Test: `learn-anything-app/tests/integration/test_models/test_learner_state.py`

- [ ] **Step 1: Write failing test for Concept + SkillNode**

```python
# tests/integration/test_models/test_graph_nodes.py
import pytest
from app.models.graph_nodes import Concept, SkillNode, Domain

@pytest.mark.asyncio
async def test_create_concept(db):
    c = Concept(
        name="Harmonic Intervals",
        description="Frequency ratios between musical notes",
        abstraction_level="abstract",
        bloom_level="understand",
        field_freshness="stable",
    )
    db.add(c)
    await db.commit()
    await db.refresh(c)
    assert c.id is not None
    assert c.version == 1

@pytest.mark.asyncio
async def test_create_skill_node(db):
    d = Domain(name="Jazz Piano", skill_type="hybrid", environment_type="mostly_kind")
    db.add(d)
    await db.commit()
    s = SkillNode(
        name="Voicings",
        domain_id=d.id,
        description="Chord voicing techniques for jazz piano",
        component_type="recurrent",
        bloom_level="apply",
        frequency_score=0.8,
        impact_score=0.9,
        field_freshness="stable",
    )
    db.add(s)
    await db.commit()
    await db.refresh(s)
    assert s.id is not None
    assert s.domain_id == d.id
```

- [ ] **Step 2: Run test — should fail**

Run: `uv run pytest tests/integration/test_models/test_graph_nodes.py -v`
Expected: FAIL

- [ ] **Step 3: Implement graph node models**

```python
# app/models/graph_nodes.py
import uuid
from sqlalchemy import String, Float, ForeignKey, Text, Enum as SAEnum
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.models.base import Base, VersionedMixin
import enum

class BloomLevel(str, enum.Enum):
    remember = "remember"
    understand = "understand"
    apply = "apply"
    analyze = "analyze"
    evaluate = "evaluate"
    create = "create"

class Freshness(str, enum.Enum):
    stable = "stable"
    evolving = "evolving"
    volatile = "volatile"

class Domain(Base):
    __tablename__ = "domains"
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    name: Mapped[str] = mapped_column(String(200), unique=True)
    skill_type: Mapped[str] = mapped_column(String(50))
    environment_type: Mapped[str] = mapped_column(String(50))

class Concept(Base, VersionedMixin):
    __tablename__ = "concepts"
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    name: Mapped[str] = mapped_column(String(200))
    description: Mapped[str] = mapped_column(Text)
    abstraction_level: Mapped[str] = mapped_column(String(20))  # concrete, abstract
    bloom_level: Mapped[str] = mapped_column(String(20))
    field_freshness: Mapped[str] = mapped_column(String(20), default="stable")
    # PGVector embedding added via Alembic migration (PG-only)

class SkillNode(Base, VersionedMixin):
    __tablename__ = "skill_nodes"
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    name: Mapped[str] = mapped_column(String(200))
    domain_id: Mapped[str] = mapped_column(ForeignKey("domains.id"))
    description: Mapped[str] = mapped_column(Text)
    component_type: Mapped[str] = mapped_column(String(20))  # recurrent, non_recurrent
    bloom_level: Mapped[str] = mapped_column(String(20))
    frequency_score: Mapped[float] = mapped_column(Float, default=0.0)
    impact_score: Mapped[float] = mapped_column(Float, default=0.0)
    field_freshness: Mapped[str] = mapped_column(String(20), default="stable")
    # PGVector embedding added via Alembic migration (PG-only)
```

- [ ] **Step 4: Run test — should pass**

Run: `uv run pytest tests/integration/test_models/test_graph_nodes.py -v`
Expected: PASS

- [ ] **Step 5: Write failing test for edges**

```python
# tests/integration/test_models/test_graph_edges.py
import pytest
from app.models.graph_nodes import Concept, SkillNode, Domain
from app.models.graph_edges import GraphEdge

@pytest.mark.asyncio
async def test_prerequisite_edge(db):
    c1 = Concept(name="A", description="a", abstraction_level="concrete", bloom_level="remember")
    c2 = Concept(name="B", description="b", abstraction_level="concrete", bloom_level="understand")
    db.add_all([c1, c2])
    await db.commit()
    edge = GraphEdge(
        from_node_id=c1.id,
        from_node_type="concept",
        to_node_id=c2.id,
        to_node_type="concept",
        edge_type="PREREQUISITE",
        strength=0.9,
        prerequisite_type="hard",
        description="A is required before B",
    )
    db.add(edge)
    await db.commit()
    await db.refresh(edge)
    assert edge.id is not None
    assert edge.edge_type == "PREREQUISITE"

@pytest.mark.asyncio
async def test_embodies_edge(db):
    d = Domain(name="Test", skill_type="cognitive", environment_type="kind")
    db.add(d)
    await db.commit()
    s = SkillNode(name="S", domain_id=d.id, description="s", component_type="recurrent", bloom_level="apply")
    c = Concept(name="C", description="c", abstraction_level="abstract", bloom_level="understand")
    db.add_all([s, c])
    await db.commit()
    edge = GraphEdge(
        from_node_id=s.id, from_node_type="skill_node",
        to_node_id=c.id, to_node_type="concept",
        edge_type="EMBODIES", strength=0.8,
        description="S implements concept C",
    )
    db.add(edge)
    await db.commit()
    assert edge.edge_type == "EMBODIES"
```

- [ ] **Step 6: Implement edge model**

```python
# app/models/graph_edges.py
import uuid
from sqlalchemy import String, Float, Text
from sqlalchemy.orm import Mapped, mapped_column
from app.models.base import Base, VersionedMixin

class GraphEdge(Base, VersionedMixin):
    __tablename__ = "graph_edges"
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    from_node_id: Mapped[str] = mapped_column(String(36), index=True)
    from_node_type: Mapped[str] = mapped_column(String(20))  # concept, skill_node
    to_node_id: Mapped[str] = mapped_column(String(36), index=True)
    to_node_type: Mapped[str] = mapped_column(String(20))
    edge_type: Mapped[str] = mapped_column(String(30), index=True)
    # PREREQUISITE, EMBODIES, SIMILAR_TO, GENERALIZES, REINFORCES, NEGATIVE_TRANSFER
    strength: Mapped[float] = mapped_column(Float, default=1.0)
    prerequisite_type: Mapped[str | None] = mapped_column(String(10), nullable=True)  # hard, soft
    cosine_similarity: Mapped[float | None] = mapped_column(Float, nullable=True)
    transfer_type: Mapped[str | None] = mapped_column(String(20), nullable=True)
    risk: Mapped[str | None] = mapped_column(Text, nullable=True)
    mitigation: Mapped[str | None] = mapped_column(Text, nullable=True)
    description: Mapped[str] = mapped_column(Text, default="")
```

- [ ] **Step 7: Run test — should pass**

Run: `uv run pytest tests/integration/test_models/test_graph_edges.py -v`
Expected: PASS

- [ ] **Step 8: Write failing test for LearnerState**

```python
# tests/integration/test_models/test_learner_state.py
import pytest
from app.models.graph_nodes import Concept
from app.models.user import User
from app.models.learner_state import LearnerState, MasteryTransition
from app.security.passwords import hash_password

@pytest.mark.asyncio
async def test_learner_state(db):
    user = User(email="l@t.com", display_name="L", password_hash=hash_password("x"), provider="local")
    concept = Concept(name="X", description="x", abstraction_level="concrete", bloom_level="remember")
    db.add_all([user, concept])
    await db.commit()
    state = LearnerState(
        user_id=user.id,
        node_id=concept.id,
        node_type="concept",
        mastery_probability=0.72,
        mastery_category="proficient",
        confidence=0.85,
        evidence_count=8,
        source="calibration",
    )
    db.add(state)
    await db.commit()
    await db.refresh(state)
    assert state.mastery_probability == 0.72

@pytest.mark.asyncio
async def test_mastery_transition(db):
    t = MasteryTransition(
        user_id="user-1",
        node_id="node-1",
        from_state="familiar",
        to_state="proficient",
        trigger_type="assessment",
        reason="Passed mastery gate TC1",
    )
    db.add(t)
    await db.commit()
    assert t.id is not None
```

- [ ] **Step 9: Implement LearnerState + MasteryTransition**

```python
# app/models/learner_state.py
import uuid
from datetime import datetime, timezone
from sqlalchemy import String, Float, Integer, Text, DateTime, func, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column
from app.models.base import Base

class LearnerState(Base):
    __tablename__ = "learner_states"
    __table_args__ = (UniqueConstraint("user_id", "node_id", name="uq_user_node"),)

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id: Mapped[str] = mapped_column(String(36), index=True)
    node_id: Mapped[str] = mapped_column(String(36), index=True)
    node_type: Mapped[str] = mapped_column(String(20))  # concept, skill_node
    mastery_probability: Mapped[float] = mapped_column(Float, default=0.0)
    mastery_category: Mapped[str] = mapped_column(String(20), default="not_started")
    confidence: Mapped[float] = mapped_column(Float, default=0.0)
    evidence_count: Mapped[int] = mapped_column(Integer, default=0)
    evidence_summary: Mapped[str] = mapped_column(Text, default="")
    last_assessed: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    fsrs_difficulty: Mapped[float] = mapped_column(Float, default=5.0)
    fsrs_stability: Mapped[float] = mapped_column(Float, default=0.0)
    bkt_p_transit: Mapped[float] = mapped_column(Float, default=0.15)
    bkt_p_slip: Mapped[float] = mapped_column(Float, default=0.08)
    bkt_p_guess: Mapped[float] = mapped_column(Float, default=0.12)
    transfer_boost: Mapped[float] = mapped_column(Float, default=0.0)
    source: Mapped[str] = mapped_column(String(30), default="calibration")
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

class MasteryTransition(Base):
    __tablename__ = "mastery_transitions"
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id: Mapped[str] = mapped_column(String(36), index=True)
    node_id: Mapped[str] = mapped_column(String(36), index=True)
    from_state: Mapped[str] = mapped_column(String(20))
    to_state: Mapped[str] = mapped_column(String(20))
    trigger_type: Mapped[str] = mapped_column(String(30))
    reason: Mapped[str] = mapped_column(Text, default="")
    timestamp: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
```

- [ ] **Step 10: Run tests — should pass**

Run: `uv run pytest tests/integration/test_models/ -v`
Expected: All PASS

- [ ] **Step 11: Implement Material + Reference models**

```python
# app/models/material.py
import uuid
from sqlalchemy import String, Float, Text, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column
from app.models.base import Base, VersionedMixin

class Reference(Base):
    __tablename__ = "references"
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    type: Mapped[str] = mapped_column(String(30))  # book, paper, video, website, course, podcast
    title: Mapped[str] = mapped_column(String(500))
    url: Mapped[str | None] = mapped_column(String(2000), nullable=True)
    author: Mapped[str | None] = mapped_column(String(200), nullable=True)
    date_published: Mapped[str | None] = mapped_column(String(20), nullable=True)
    date_accessed: Mapped[str | None] = mapped_column(String(20), nullable=True)
    credibility: Mapped[str] = mapped_column(String(20), default="community")  # peer_reviewed, expert_opinion, community, anecdotal
    content_hash: Mapped[str | None] = mapped_column(String(64), nullable=True)

class Material(Base, VersionedMixin):
    __tablename__ = "materials"
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    type: Mapped[str] = mapped_column(String(30))  # lecture, flashcard_deck, worked_example, video, etc.
    title: Mapped[str] = mapped_column(String(500))
    format: Mapped[str] = mapped_column(String(20))  # markdown, apkg, svg, mp4, youtube_embed
    source: Mapped[str] = mapped_column(String(20), default="generated")  # generated, curated, external
    url_or_path: Mapped[str | None] = mapped_column(String(2000), nullable=True)
    bloom_level: Mapped[str | None] = mapped_column(String(20), nullable=True)
    effectiveness_score: Mapped[float] = mapped_column(Float, default=0.0)
    content: Mapped[str | None] = mapped_column(Text, nullable=True)

class MaterialTeaches(Base):
    """Junction: Material -[:TEACHES]-> Concept|SkillNode"""
    __tablename__ = "material_teaches"
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    material_id: Mapped[str] = mapped_column(ForeignKey("materials.id"), index=True)
    node_id: Mapped[str] = mapped_column(String(36), index=True)  # Polymorphic: concept or skill_node
    node_type: Mapped[str] = mapped_column(String(20))  # "concept" or "skill_node"
    depth: Mapped[str] = mapped_column(String(20), default="introduction")
    modality: Mapped[str] = mapped_column(String(20), default="reading")

class SourcedFrom(Base):
    """Junction: Concept|SkillNode -[:SOURCED_FROM]-> Reference"""
    __tablename__ = "sourced_from"
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    node_id: Mapped[str] = mapped_column(String(36), index=True)  # Polymorphic: concept or skill_node
    node_type: Mapped[str] = mapped_column(String(20))
    reference_id: Mapped[str] = mapped_column(ForeignKey("references.id"), index=True)
    relevance: Mapped[float] = mapped_column(Float, default=1.0)
    excerpt: Mapped[str | None] = mapped_column(Text, nullable=True)
    page_or_timestamp: Mapped[str | None] = mapped_column(String(100), nullable=True)

class MaterialPrerequisite(Base):
    """Junction: Material -[:PREREQUISITE_MATERIAL]-> Material"""
    __tablename__ = "material_prerequisites"
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    material_id: Mapped[str] = mapped_column(ForeignKey("materials.id"), index=True)
    prerequisite_material_id: Mapped[str] = mapped_column(ForeignKey("materials.id"), index=True)

class MaterialCites(Base):
    """Junction: Material -[:CITES]-> Reference"""
    __tablename__ = "material_cites"
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    material_id: Mapped[str] = mapped_column(ForeignKey("materials.id"), index=True)
    reference_id: Mapped[str] = mapped_column(ForeignKey("references.id"), index=True)
```

- [ ] **Step 12: Write tests for Material + Reference models**

```python
# tests/integration/test_models/test_material.py
import pytest
from app.models.material import Reference, Material, MaterialTeaches, SourcedFrom, MaterialPrerequisite, MaterialCites

@pytest.mark.asyncio
async def test_create_reference(db):
    ref = Reference(type="paper", title="Test Paper", credibility="peer_reviewed", url="https://example.com")
    db.add(ref)
    await db.commit()
    await db.refresh(ref)
    assert ref.id is not None
    assert ref.credibility == "peer_reviewed"

@pytest.mark.asyncio
async def test_create_material(db):
    mat = Material(type="lecture", title="Intro Lecture", format="markdown", source="generated", bloom_level="understand")
    db.add(mat)
    await db.commit()
    await db.refresh(mat)
    assert mat.id is not None
    assert mat.effectiveness_score == 0.0

@pytest.mark.asyncio
async def test_material_teaches_junction(db):
    mat = Material(type="flashcard_deck", title="Deck", format="apkg", source="generated")
    db.add(mat)
    await db.commit()
    teaches = MaterialTeaches(material_id=mat.id, node_id="concept-1", node_type="concept", depth="reinforcement", modality="interactive")
    db.add(teaches)
    await db.commit()
    assert teaches.id is not None

@pytest.mark.asyncio
async def test_sourced_from_with_page(db):
    ref = Reference(type="book", title="Textbook", credibility="expert_opinion")
    db.add(ref)
    await db.commit()
    sf = SourcedFrom(node_id="skill-1", node_type="skill_node", reference_id=ref.id, relevance=0.9, excerpt="Chapter 3", page_or_timestamp="p.42")
    db.add(sf)
    await db.commit()
    assert sf.page_or_timestamp == "p.42"

@pytest.mark.asyncio
async def test_material_prerequisite(db):
    m1 = Material(type="lecture", title="Lecture 1", format="markdown", source="generated")
    m2 = Material(type="lecture", title="Lecture 2", format="markdown", source="generated")
    db.add_all([m1, m2])
    await db.commit()
    prereq = MaterialPrerequisite(material_id=m2.id, prerequisite_material_id=m1.id)
    db.add(prereq)
    await db.commit()
    assert prereq.id is not None

@pytest.mark.asyncio
async def test_material_cites(db):
    mat = Material(type="lecture", title="Lecture", format="markdown", source="generated")
    ref = Reference(type="paper", title="Cited Paper", credibility="peer_reviewed")
    db.add_all([mat, ref])
    await db.commit()
    cite = MaterialCites(material_id=mat.id, reference_id=ref.id)
    db.add(cite)
    await db.commit()
    assert cite.id is not None
```

- [ ] **Step 12b: Update conftest.py imports and run all model tests**

Add to `tests/conftest.py`:
```python
from app.models.graph_nodes import Concept, SkillNode, Domain  # noqa
from app.models.graph_edges import GraphEdge  # noqa
from app.models.learner_state import LearnerState, MasteryTransition  # noqa
from app.models.material import Reference, Material, MaterialTeaches, SourcedFrom, MaterialPrerequisite, MaterialCites  # noqa
```

Run: `uv run pytest tests/integration/test_models/ -v`
Expected: All PASS

- [ ] **Step 13: Commit**

```bash
git commit -m "feat: three-layer knowledge graph models — concepts, skills, edges, learner state, materials, references"
```

---

### Task 7: AppConfig Model + Setup State Detection

**Files:**
- Create: `learn-anything-app/app/models/config.py`
- Create: `learn-anything-app/app/services/__init__.py`
- Create: `learn-anything-app/app/services/setup_service.py`
- Test: `learn-anything-app/tests/integration/test_services/test_setup_service.py`

- [ ] **Step 1: Write failing tests for setup service**

```python
# tests/integration/test_services/test_setup_service.py
import pytest
from app.models.config import AppConfig
from app.services.setup_service import is_setup_complete, get_config, set_config

@pytest.mark.asyncio
async def test_is_setup_complete_false_when_empty(db):
    result = await is_setup_complete(db)
    assert result is False

@pytest.mark.asyncio
async def test_is_setup_complete_true_when_set(db):
    db.add(AppConfig(key="setup_complete", value="true"))
    await db.commit()
    result = await is_setup_complete(db)
    assert result is True

@pytest.mark.asyncio
async def test_set_and_get_config(db):
    await set_config(db, "test_key", "test_value")
    result = await get_config(db, "test_key")
    assert result == "test_value"

@pytest.mark.asyncio
async def test_get_config_missing_returns_none(db):
    result = await get_config(db, "nonexistent")
    assert result is None

@pytest.mark.asyncio
async def test_set_config_updates_existing(db):
    await set_config(db, "key1", "v1")
    await set_config(db, "key1", "v2")
    result = await get_config(db, "key1")
    assert result == "v2"

@pytest.mark.asyncio
async def test_set_config_encrypted(db):
    from app.security.encryption import SecretStore
    import tempfile, os
    with tempfile.NamedTemporaryFile(delete=False, suffix=".key") as f:
        key_path = f.name
    try:
        store = SecretStore(key_path)
        await set_config(db, "secret", "my-api-key", encrypted=True, secret_store=store)
        # Raw value in DB should NOT be plaintext
        raw = await get_config(db, "secret")
        assert raw != "my-api-key"
        # Decrypted value should match
        decrypted = await get_config(db, "secret", secret_store=store)
        assert decrypted == "my-api-key"
    finally:
        os.unlink(key_path)
```

- [ ] **Step 2: Run tests — should fail**

Run: `uv run pytest tests/integration/test_services/test_setup_service.py -v`
Expected: FAIL — `ModuleNotFoundError`

- [ ] **Step 3: Create AppConfig model for DB-stored settings**

```python
# app/models/config.py
from sqlalchemy import String, Text
from sqlalchemy.orm import Mapped, mapped_column
from app.models.base import Base

class AppConfig(Base):
    __tablename__ = "app_config"
    key: Mapped[str] = mapped_column(String(100), primary_key=True)
    value: Mapped[str] = mapped_column(Text, default="")
    encrypted: Mapped[bool] = mapped_column(default=False)
```

- [ ] **Step 4: Create `app/services/__init__.py`**

```python
# app/services/__init__.py
# empty
```

- [ ] **Step 5: Create setup service**

```python
# app/services/setup_service.py
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.models.config import AppConfig
from app.security.encryption import SecretStore

async def is_setup_complete(db: AsyncSession) -> bool:
    result = await db.execute(select(AppConfig).where(AppConfig.key == "setup_complete"))
    row = result.scalar_one_or_none()
    return row is not None and row.value == "true"

async def get_config(db: AsyncSession, key: str, secret_store: SecretStore | None = None) -> str | None:
    result = await db.execute(select(AppConfig).where(AppConfig.key == key))
    row = result.scalar_one_or_none()
    if row is None:
        return None
    if row.encrypted and secret_store:
        return secret_store.decrypt(row.value)
    return row.value

async def set_config(db: AsyncSession, key: str, value: str, encrypted: bool = False, secret_store: SecretStore | None = None):
    stored_value = value
    if encrypted and secret_store:
        stored_value = secret_store.encrypt(value)
    result = await db.execute(select(AppConfig).where(AppConfig.key == key))
    existing = result.scalar_one_or_none()
    if existing:
        existing.value = stored_value
        existing.encrypted = encrypted
    else:
        db.add(AppConfig(key=key, value=stored_value, encrypted=encrypted))
    await db.commit()
```

- [ ] **Step 6: Run tests — should pass**

Run: `uv run pytest tests/integration/test_services/test_setup_service.py -v`
Expected: All PASS

- [ ] **Step 7: Commit**

```bash
git commit -m "feat: AppConfig model and setup service for DB-stored settings"
```

---

### Task 8: StateBackend Protocol + JSON Backend

**Files:**
- Create: `learn-anything-app/app/backends/__init__.py`
- Create: `learn-anything-app/app/backends/protocol.py`
- Create: `learn-anything-app/app/backends/json_file.py`
- Test: `learn-anything-app/tests/integration/test_backends/test_json_backend.py`

- [ ] **Step 0: Create package __init__.py**

```python
# app/backends/__init__.py
# empty
```

- [ ] **Step 1: Write failing test for JSON backend**

```python
# tests/integration/test_backends/test_json_backend.py
import pytest
import tempfile
import os
from app.backends.json_file import JSONFileBackend

@pytest.fixture
def backend(tmp_path):
    return JSONFileBackend(str(tmp_path))

@pytest.mark.asyncio
async def test_write_and_read_graph(backend):
    graph_data = {
        "vertices": [{"id": "v1", "name": "Test", "mastery_probability": 0.5}],
        "edges": [{"from_id": "v1", "to_id": "v2", "label": "PREREQUISITE"}],
    }
    await backend.write_graph("test-skill", graph_data)
    result = await backend.read_graph("test-skill")
    assert result["vertices"][0]["name"] == "Test"

@pytest.mark.asyncio
async def test_export_import_roundtrip(backend):
    graph_data = {"vertices": [{"id": "v1", "name": "Export Test"}], "edges": []}
    await backend.write_graph("test-skill", graph_data)
    exported = await backend.export_json("test-skill")
    assert exported["vertices"][0]["name"] == "Export Test"
    await backend.write_graph("new-skill", {})
    await backend.import_json("new-skill", exported)
    result = await backend.read_graph("new-skill")
    assert result["vertices"][0]["name"] == "Export Test"

@pytest.mark.asyncio
async def test_read_missing_returns_empty(backend):
    result = await backend.read_graph("nonexistent")
    assert result == {}

@pytest.mark.asyncio
async def test_query_transfer_returns_empty(backend):
    result = await backend.query_transfer([0.1, 0.2, 0.3])
    assert result == []  # JSON backend doesn't support transfer queries
```

- [ ] **Step 2: Run test — should fail**

Run: `uv run pytest tests/integration/test_backends/test_json_backend.py -v`
Expected: FAIL

- [ ] **Step 3: Implement protocol and JSON backend**

```python
# app/backends/protocol.py
from typing import Protocol, Any

class TransferMatch:
    def __init__(self, node_id: str, node_type: str, name: str, cosine: float, transfer_type: str):
        self.node_id = node_id
        self.node_type = node_type
        self.name = name
        self.cosine = cosine
        self.transfer_type = transfer_type

class StateBackend(Protocol):
    async def read_graph(self, skill_slug: str) -> dict: ...
    async def write_graph(self, skill_slug: str, graph: dict) -> None: ...
    async def query_transfer(self, embeddings: list[float]) -> list[TransferMatch]: ...
    async def export_json(self, skill_slug: str) -> dict: ...
    async def import_json(self, skill_slug: str, data: dict) -> None: ...
```

```python
# app/backends/json_file.py
import json
from pathlib import Path
from app.backends.protocol import StateBackend, TransferMatch

class JSONFileBackend:
    def __init__(self, base_dir: str):
        self._base = Path(base_dir)
        self._base.mkdir(parents=True, exist_ok=True)

    def _graph_path(self, skill_slug: str) -> Path:
        return self._base / skill_slug / "knowledge-graph.json"

    async def read_graph(self, skill_slug: str) -> dict:
        path = self._graph_path(skill_slug)
        if not path.exists():
            return {}
        return json.loads(path.read_text())

    async def write_graph(self, skill_slug: str, graph: dict) -> None:
        path = self._graph_path(skill_slug)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(graph, indent=2))

    async def query_transfer(self, embeddings: list[float]) -> list[TransferMatch]:
        return []  # Not supported in JSON mode

    async def export_json(self, skill_slug: str) -> dict:
        return await self.read_graph(skill_slug)

    async def import_json(self, skill_slug: str, data: dict) -> None:
        await self.write_graph(skill_slug, data)
```

- [ ] **Step 4: Run test — should pass**

Run: `uv run pytest tests/integration/test_backends/test_json_backend.py -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git commit -m "feat: StateBackend protocol + JSON file backend"
```

---

### Task 9: Health Endpoint

**Files:**
- Create: `learn-anything-app/app/routes/health.py`
- Test: `learn-anything-app/tests/integration/test_routes/test_health.py`

- [ ] **Step 1: Write failing test**

```python
# tests/integration/test_routes/test_health.py
# NOTE: Uses shared `client` fixture from tests/conftest.py
import pytest

@pytest.mark.asyncio
async def test_health_returns_200(client):
    resp = await client.get("/health")
    assert resp.status_code == 200
    data = resp.json()
    assert "status" in data
    assert data["status"] in ("ok", "degraded")
    assert "database" in data
```

- [ ] **Step 2: Implement health route**

```python
# app/routes/health.py
import structlog
from fastapi import APIRouter
from sqlalchemy import text
from app.config import settings

log = structlog.get_logger()
router = APIRouter(tags=["health"])

@router.get("/health")
async def health():
    db_status = "not_configured"
    if settings.database_url:
        try:
            from app.database import SessionLocal
            if SessionLocal is not None:
                async with SessionLocal() as session:
                    await session.execute(text("SELECT 1"))
                db_status = "connected"
            else:
                db_status = "not_initialized"
        except Exception as exc:
            log.warning("health_db_check_failed", error=str(exc))
            db_status = "unreachable"

    return {
        "status": "ok" if db_status in ("connected", "not_configured") else "degraded",
        "version": "0.1.0",
        "state_backend": settings.state_backend,
        "database": db_status,
    }
```

Register in `app/main.py`:
```python
from app.routes.health import router as health_router
app.include_router(health_router)
```

- [ ] **Step 3: Run test — should pass**

Run: `uv run pytest tests/integration/test_routes/test_health.py -v`
Expected: PASS

- [ ] **Step 4: Commit**

```bash
git commit -m "feat: health endpoint at GET /health"
```

---

### Task 10: Setup Wizard Routes

**Files:**
- Create: `learn-anything-app/app/routes/setup.py`
- Create: `learn-anything-app/templates/setup/welcome.html`
- Create: `learn-anything-app/templates/setup/database.html`
- Create: `learn-anything-app/templates/setup/llm.html`
- Create: `learn-anything-app/templates/setup/auth.html`
- Create: `learn-anything-app/templates/setup/account.html`
- Test: `learn-anything-app/tests/integration/test_routes/test_setup.py`

- [ ] **Step 1: Write failing test**

```python
# tests/integration/test_routes/test_setup.py
# NOTE: Uses shared `client` fixture from tests/conftest.py
import pytest

@pytest.mark.asyncio
async def test_setup_welcome_renders(client):
    resp = await client.get("/setup")
    assert resp.status_code == 200
    assert "Learn Anything" in resp.text

@pytest.mark.asyncio
async def test_setup_steps_render(client):
    for step in ["database", "llm", "auth", "account"]:
        resp = await client.get(f"/setup/{step}")
        assert resp.status_code == 200
```

- [ ] **Step 2: Run test — should fail**

- [ ] **Step 3: Implement setup routes**

```python
# app/routes/setup.py
from fastapi import APIRouter, Request, Form
from fastapi.responses import RedirectResponse
from app.templating import templates

router = APIRouter(prefix="/setup", tags=["setup"])

@router.get("")
async def welcome(request: Request):
    return templates.TemplateResponse(request, "setup/welcome.html", {"step": 1})

@router.get("/database")
async def database_step(request: Request):
    return templates.TemplateResponse(request, "setup/database.html", {"step": 2})

@router.post("/database")
async def database_save(request: Request, database_url: str = Form("")):
    # Validate connection, store config
    return RedirectResponse("/setup/llm", status_code=303)

@router.get("/llm")
async def llm_step(request: Request):
    return templates.TemplateResponse(request, "setup/llm.html", {"step": 3})

@router.post("/llm")
async def llm_save(request: Request, api_key: str = Form(""), model: str = Form("claude-sonnet-4-6")):
    return RedirectResponse("/setup/auth", status_code=303)

@router.get("/auth")
async def auth_step(request: Request):
    return templates.TemplateResponse(request, "setup/auth.html", {"step": 4})

@router.post("/auth")
async def auth_save(request: Request):
    return RedirectResponse("/setup/account", status_code=303)

@router.get("/account")
async def account_step(request: Request):
    return templates.TemplateResponse(request, "setup/account.html", {"step": 5})

@router.post("/account")
async def account_save(
    request: Request,
    email: str = Form(...),
    display_name: str = Form(...),
    password: str = Form(...),
):
    # Create admin user, mark setup complete
    return RedirectResponse("/", status_code=303)
```

- [ ] **Step 4: Create setup templates (minimal, Observatory-styled)**

```html
<!-- templates/setup/welcome.html -->
{% extends "base.html" %}
{% block content %}
<div class="setup-container" data-signals:track="'quick'">
  <div class="logo-mark"></div>
  <h1>Welcome to Learn Anything</h1>
  <p class="subtitle">Let's get your instance configured. This takes about 5 minutes.</p>
  <div class="setup-options">
    <a href="/setup/database?track=quick" class="setup-card active">
      <h3>Quick Setup</h3>
      <p>Bundled Postgres, single user, just need an LLM API key</p>
      <span class="time">~2 minutes</span>
    </a>
    <a href="/setup/database?track=custom" class="setup-card">
      <h3>Custom Setup</h3>
      <p>Bring your own Postgres, configure OAuth, multi-user</p>
      <span class="time">~5 minutes</span>
    </a>
  </div>
</div>
{% endblock %}

<!-- templates/setup/database.html -->
{% extends "base.html" %}
{% block content %}
<div class="setup-container">
  <h2>Database</h2>
  <form method="post" action="/setup/database">
    <label>PostgreSQL Connection URL</label>
    <input name="database_url" placeholder="postgresql://user:pass@host:5432/dbname">
    <p class="hint">Leave empty to use bundled database (Quick Setup)</p>
    <button type="submit">Continue</button>
  </form>
</div>
{% endblock %}

<!-- templates/setup/llm.html -->
{% extends "base.html" %}
{% block content %}
<div class="setup-container">
  <h2>LLM Provider</h2>
  <form method="post" action="/setup/llm">
    <label>Anthropic API Key</label>
    <input name="api_key" type="password" placeholder="sk-ant-api03-...">
    <label>Model</label>
    <select name="model">
      <option value="claude-opus-4-6">Claude Opus 4</option>
      <option value="claude-sonnet-4-6" selected>Claude Sonnet 4</option>
      <option value="claude-haiku-4-5-20251001">Claude Haiku 4</option>
    </select>
    <button type="submit">Continue</button>
  </form>
</div>
{% endblock %}

<!-- templates/setup/auth.html -->
{% extends "base.html" %}
{% block content %}
<div class="setup-container">
  <h2>Authentication</h2>
  <form method="post" action="/setup/auth">
    <p>Local accounts are always enabled.</p>
    <label><input type="checkbox" name="single_user"> Single User Mode (skip login)</label>
    <h3>OAuth (optional)</h3>
    <label>Google Client ID</label>
    <input name="google_client_id" placeholder="Optional">
    <label>Google Client Secret</label>
    <input name="google_client_secret" type="password" placeholder="Optional">
    <button type="submit">Continue</button>
  </form>
</div>
{% endblock %}

<!-- templates/setup/account.html -->
{% extends "base.html" %}
{% block content %}
<div class="setup-container">
  <h2>Create Admin Account</h2>
  <form method="post" action="/setup/account">
    <input name="display_name" placeholder="Display Name" required>
    <input name="email" type="email" placeholder="Email" required>
    <input name="password" type="password" placeholder="Password" required>
    <button type="submit">Launch Learn Anything</button>
  </form>
</div>
{% endblock %}
```

- [ ] **Step 5: Register setup router in main.py**

```python
from app.routes.setup import router as setup_router
app.include_router(setup_router)
```

- [ ] **Step 6: Run test — should pass**

Run: `uv run pytest tests/integration/test_routes/test_setup.py -v`
Expected: PASS

- [ ] **Step 7: Commit**

```bash
git commit -m "feat: setup wizard — 5-step flow (welcome, database, LLM, auth, account)"
```

---

### Task 10b: Settings Page (Post-Setup Configuration)

**Files:**
- Create: `learn-anything-app/app/routes/settings.py`
- Create: `learn-anything-app/templates/settings/index.html`
- Test: `learn-anything-app/tests/integration/test_routes/test_settings.py`

> **Spec requirement:** Section 6 — "All configuration accessible at `/settings`. No `.env` editing, no server restarts."

The settings page reads/writes AppConfig entries. Encrypted values (API keys, OAuth secrets) are decrypted for display (masked) and re-encrypted on save.

- [ ] **Step 1: Write failing tests for settings routes**

```python
# tests/integration/test_routes/test_settings.py
import pytest

@pytest.mark.asyncio
async def test_settings_page_renders(client):
    resp = await client.get("/settings")
    assert resp.status_code == 200
    assert "Settings" in resp.text or "settings" in resp.text

@pytest.mark.asyncio
async def test_settings_update_llm_provider(client):
    resp = await client.post("/settings/llm", data={
        "api_key": "sk-ant-test-key",
        "model": "claude-opus-4-6",
    }, follow_redirects=False)
    assert resp.status_code in (200, 303)
```

- [ ] **Step 2: Run tests — should fail**

Run: `uv run pytest tests/integration/test_routes/test_settings.py -v`
Expected: FAIL

- [ ] **Step 3: Implement settings routes**

```python
# app/routes/settings.py
from fastapi import APIRouter, Request, Form
from fastapi.responses import RedirectResponse
from app.templating import templates

router = APIRouter(prefix="/settings", tags=["settings"])

@router.get("")
async def settings_page(request: Request):
    # In production: read all config from AppConfig, mask encrypted values
    return templates.TemplateResponse(request, "settings/index.html", {
        "llm_provider": "Anthropic Claude",
        "llm_model": "claude-sonnet-4-6",
        "llm_key_masked": "sk-ant-...****",
        "google_configured": False,
        "github_configured": False,
        "single_user": False,
    })

@router.post("/llm")
async def update_llm(request: Request, api_key: str = Form(""), model: str = Form("claude-sonnet-4-6")):
    # In production: encrypt api_key via SecretStore, save to AppConfig
    return RedirectResponse("/settings", status_code=303)

@router.post("/auth")
async def update_auth(request: Request):
    # In production: save OAuth config, toggle single_user
    return RedirectResponse("/settings", status_code=303)
```

- [ ] **Step 4: Create settings template**

```html
<!-- templates/settings/index.html -->
{% extends "base.html" %}
{% block title %}Settings — Learn Anything{% endblock %}
{% block content %}
<div class="setup-container">
  <h1>Settings</h1>
  <p class="subtitle">All changes take effect immediately. No server restart needed.</p>

  <h2>LLM Provider</h2>
  <form method="post" action="/settings/llm">
    <label>API Key</label>
    <input name="api_key" type="password" placeholder="{{ llm_key_masked }}" value="">
    <p class="hint">Leave empty to keep current key</p>
    <label>Model</label>
    <select name="model">
      <option value="claude-opus-4-6" {{ 'selected' if llm_model == 'claude-opus-4-6' }}>Claude Opus 4</option>
      <option value="claude-sonnet-4-6" {{ 'selected' if llm_model == 'claude-sonnet-4-6' }}>Claude Sonnet 4</option>
      <option value="claude-haiku-4-5-20251001" {{ 'selected' if llm_model == 'claude-haiku-4-5-20251001' }}>Claude Haiku 4</option>
    </select>
    <button type="submit">Save</button>
  </form>

  <h2>Authentication</h2>
  <form method="post" action="/settings/auth">
    <label><input type="checkbox" name="single_user" {{ 'checked' if single_user }}> Single User Mode</label>
    <h3>Google OAuth</h3>
    <label>Client ID</label>
    <input name="google_client_id" placeholder="{{ 'Configured' if google_configured else 'Not configured' }}">
    <label>Client Secret</label>
    <input name="google_client_secret" type="password" placeholder="{{ 'Configured' if google_configured else 'Not configured' }}">
    <h3>GitHub OAuth</h3>
    <label>Client ID</label>
    <input name="github_client_id" placeholder="{{ 'Configured' if github_configured else 'Not configured' }}">
    <label>Client Secret</label>
    <input name="github_client_secret" type="password" placeholder="{{ 'Configured' if github_configured else 'Not configured' }}">
    <button type="submit">Save</button>
  </form>
</div>
{% endblock %}
```

- [ ] **Step 5: Register settings router in main.py**

```python
from app.routes.settings import router as settings_router
app.include_router(settings_router)
```

- [ ] **Step 6: Run tests — should pass**

Run: `uv run pytest tests/integration/test_routes/test_settings.py -v`
Expected: PASS

- [ ] **Step 7: Commit**

```bash
git commit -m "feat: settings page — post-setup config for LLM provider, auth, OAuth"
```

---

### Task 11: Alembic + Initial Migration

**Files:**
- Create: `learn-anything-app/alembic.ini`
- Create: `learn-anything-app/alembic/env.py`
- Create: `learn-anything-app/alembic/versions/001_initial.py`

- [ ] **Step 1: Create alembic.ini**

```ini
[alembic]
script_location = alembic
sqlalchemy.url = driver://user:pass@localhost/dbname
# Overridden by env.py at runtime

[loggers]
keys = root,sqlalchemy,alembic

[handlers]
keys = console

[formatters]
keys = generic

[logger_root]
level = WARN
handlers = console

[logger_sqlalchemy]
level = WARN
handlers =
qualname = sqlalchemy.engine

[logger_alembic]
level = INFO
handlers =
qualname = alembic

[handler_console]
class = StreamHandler
args = (sys.stderr,)
level = NOTSET
formatter = generic

[formatter_generic]
format = %(levelname)-5.5s [%(name)s] %(message)s
```

- [ ] **Step 2: Create alembic/env.py**

```python
# alembic/env.py
from alembic import context
from app.models.base import Base
from app.models.user import User  # noqa
from app.models.config import AppConfig  # noqa
from app.models.graph_nodes import Concept, SkillNode, Domain  # noqa
from app.models.graph_edges import GraphEdge  # noqa
from app.models.learner_state import LearnerState, MasteryTransition  # noqa
from app.models.material import Reference, Material, MaterialTeaches, SourcedFrom, MaterialPrerequisite, MaterialCites  # noqa
from app.config import settings

config = context.config
if settings.database_url:
    # Alembic runs migrations synchronously — use psycopg (sync) driver,
    # not asyncpg which crashes in synchronous contexts.
    sync_url = settings.database_url.replace("+asyncpg", "").replace(
        "postgresql://", "postgresql+psycopg://"
    )
    config.set_main_option("sqlalchemy.url", sync_url)

target_metadata = Base.metadata

def run_migrations_online():
    from sqlalchemy import engine_from_config, pool
    connectable = engine_from_config(
        config.get_section(config.config_ini_section),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )
    with connectable.connect() as connection:
        context.configure(connection=connection, target_metadata=target_metadata)
        with context.begin_transaction():
            context.run_migrations()

run_migrations_online()
```

- [ ] **Step 3: Auto-generate initial migration**

Run: `cd learn-anything-app && uv run alembic revision --autogenerate -m "initial schema"`
Expected: Creates migration file in `alembic/versions/`

- [ ] **Step 4: Commit**

```bash
git commit -m "feat: Alembic migrations with initial schema"
```

---

### Task 12: Docker Image + Compose

**Files:**
- Create: `learn-anything-app/Dockerfile`
- Create: `learn-anything-app/docker/postgres/Dockerfile`
- Create: `learn-anything-app/docker/postgres/init-extensions.sql`
- Create: `learn-anything-app/docker-compose.yml`

- [ ] **Step 1: Create custom Postgres Dockerfile**

```dockerfile
# docker/postgres/Dockerfile
FROM pgvector/pgvector:pg17

# Install AGE build dependencies
RUN apt-get update && apt-get install -y \
    build-essential libreadline-dev zlib1g-dev flex bison \
    postgresql-server-dev-17 git \
    && rm -rf /var/lib/apt/lists/*

# Build Apache AGE from source
RUN git clone --branch release/PG17/1.5.0 https://github.com/apache/age.git /tmp/age \
    && cd /tmp/age \
    && make install \
    && rm -rf /tmp/age

COPY init-extensions.sql /docker-entrypoint-initdb.d/
```

```sql
-- docker/postgres/init-extensions.sql
CREATE EXTENSION IF NOT EXISTS vector;
CREATE EXTENSION IF NOT EXISTS age;
SET search_path = ag_catalog, "$user", public;
```

- [ ] **Step 2: Create app Dockerfile**

```dockerfile
# Dockerfile
# No npm/node — frontend served via CDN + static files only

# --- Build stage: install dependencies ---
FROM python:3.14-slim AS builder

WORKDIR /app
RUN pip install uv

# Copy all source first so non-editable install can resolve the package
COPY pyproject.toml .
COPY app/ app/
COPY templates/ templates/
COPY static/ static/
COPY alembic/ alembic/
COPY alembic.ini .

# Non-editable install for runtime (no -e flag)
RUN uv pip install --system "."

# --- Production stage: lean runtime image ---
FROM python:3.14-slim AS runtime

WORKDIR /app

# Copy installed packages from builder
COPY --from=builder /usr/local/lib/python3.14/site-packages /usr/local/lib/python3.14/site-packages
COPY --from=builder /usr/local/bin /usr/local/bin

# Copy application code
COPY --from=builder /app /app

EXPOSE 8000

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

- [ ] **Step 3: Create docker-compose.yml (self-hosters — bundles PG)**

```yaml
# docker-compose.yml — Self-hosted deployment (bundles PG for convenience)
# For devtest/managed infrastructure, use docker-compose.dev.yml instead
services:
  app:
    build: .
    ports: ["8000:8000"]
    depends_on:
      db:
        condition: service_healthy
    environment:
      - LA_DATABASE_URL=postgresql+asyncpg://learn_anything:${LA_DB_PASSWORD:-devpassword}@db:5432/learn_anything
      - LA_STATE_BACKEND=postgres
      - LA_SECRET_KEY=${LA_SECRET_KEY:-change-me-in-production}
    volumes:
      - app_data:/app/data
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/health"]
      interval: 30s
      timeout: 10s
      retries: 3
      start_period: 15s

  db:
    build: ./docker/postgres
    volumes:
      - pgdata:/var/lib/postgresql/data
    environment:
      - POSTGRES_DB=learn_anything
      - POSTGRES_USER=learn_anything
      - POSTGRES_PASSWORD=${LA_DB_PASSWORD:-devpassword}
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U learn_anything"]
      interval: 10s
      timeout: 5s
      retries: 5

volumes:
  pgdata:
  app_data:
```

- [ ] **Step 3b: Create docker-compose.dev.yml (development — app only, shared PG)**

```yaml
# docker-compose.dev.yml — Development on devtest VM or local with shared PG
# DB is external (shared PG on devtest VM). App only, with hot-reload.
services:
  app:
    build:
      context: .
      target: builder  # Use builder stage for dev (has all deps)
    ports: ["8000:8000"]
    environment:
      - LA_DATABASE_URL=${LA_DATABASE_URL}  # Set in .env or shell
      - LA_STATE_BACKEND=postgres
      - LA_SECRET_KEY=${LA_SECRET_KEY:-dev-secret}
      - LA_LOG_LEVEL=DEBUG
    volumes:
      - .:/app:rw          # Mount source for hot-reload
      - app_data:/app/data
    command: ["uvicorn", "app.main:app", "--reload", "--host", "0.0.0.0", "--port", "8000"]
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/health"]
      interval: 30s
      timeout: 10s
      retries: 3
      start_period: 10s
    networks:
      - cluster-network

networks:
  cluster-network:
    external: true  # Pre-existing network for managed infrastructure

volumes:
  app_data:
```

- [ ] **Step 4: Test Docker build**

Run: `cd learn-anything-app && docker compose build`
Expected: Both images build successfully.

- [ ] **Step 5: Test Docker Compose up**

Run: `docker compose up -d && sleep 10 && curl http://localhost:8000/health`
Expected: `{"status":"ok",...}`

- [ ] **Step 6: Commit**

```bash
git commit -m "feat: Docker image + Compose with custom Postgres (AGE + PGVector)"
```

---

### Task 13: Observatory CSS Foundation

**Files:**
- Create: `learn-anything-app/static/css/observatory.css`

- [ ] **Step 1: Create Observatory CSS variables and base styles**

```css
/* static/css/observatory.css */

/* Self-hosted fonts — no external CDN requests.
   woff2 files live in static/fonts/ (see Task 13 Step 1b for download instructions). */

/* Cormorant Garamond */
@font-face {
  font-family: 'Cormorant Garamond';
  src: url('/static/fonts/CormorantGaramond-Regular.woff2') format('woff2');
  font-weight: 400; font-style: normal; font-display: swap;
}
@font-face {
  font-family: 'Cormorant Garamond';
  src: url('/static/fonts/CormorantGaramond-Italic.woff2') format('woff2');
  font-weight: 400; font-style: italic; font-display: swap;
}
@font-face {
  font-family: 'Cormorant Garamond';
  src: url('/static/fonts/CormorantGaramond-SemiBold.woff2') format('woff2');
  font-weight: 600; font-style: normal; font-display: swap;
}
@font-face {
  font-family: 'Cormorant Garamond';
  src: url('/static/fonts/CormorantGaramond-Bold.woff2') format('woff2');
  font-weight: 700; font-style: normal; font-display: swap;
}

/* DM Sans */
@font-face {
  font-family: 'DM Sans';
  src: url('/static/fonts/DMSans-Light.woff2') format('woff2');
  font-weight: 300; font-style: normal; font-display: swap;
}
@font-face {
  font-family: 'DM Sans';
  src: url('/static/fonts/DMSans-Regular.woff2') format('woff2');
  font-weight: 400; font-style: normal; font-display: swap;
}
@font-face {
  font-family: 'DM Sans';
  src: url('/static/fonts/DMSans-Medium.woff2') format('woff2');
  font-weight: 500; font-style: normal; font-display: swap;
}
@font-face {
  font-family: 'DM Sans';
  src: url('/static/fonts/DMSans-SemiBold.woff2') format('woff2');
  font-weight: 600; font-style: normal; font-display: swap;
}

/* JetBrains Mono */
@font-face {
  font-family: 'JetBrains Mono';
  src: url('/static/fonts/JetBrainsMono-Light.woff2') format('woff2');
  font-weight: 300; font-style: normal; font-display: swap;
}
@font-face {
  font-family: 'JetBrains Mono';
  src: url('/static/fonts/JetBrainsMono-Regular.woff2') format('woff2');
  font-weight: 400; font-style: normal; font-display: swap;
}

:root {
  --void: #04060e;
  --deep: #080c1a;
  --surface: #0e1328;
  --surface-light: #151c3a;
  --border: #1c2550;
  --border-glow: #283570;
  --text: #c4c9e0;
  --text-bright: #e8eaf6;
  --text-dim: #6b7199;
  --gold: #d4a456;
  --gold-dim: #9a7535;
  --gold-glow: rgba(212,150,74,0.15);
  --edge-blue: #4a7ccc;
  --edge-blue-bright: #6a9ef0;
  --edge-teal: #3aaa9a;
  --mastered: #5af0d8;
  --mastered-glow: rgba(90,240,216,0.25);
  --proficient: #6ec0ff;
  --proficient-glow: rgba(110,192,255,0.22);
  --familiar: #f0da6c;
  --familiar-glow: rgba(240,218,108,0.18);
  --attempted: #f0937e;
  --not-started: #3a4060;
  --violet: #9b8ec4;
  --serif: 'Cormorant Garamond', Georgia, serif;
  --sans: 'DM Sans', system-ui, sans-serif;
  --mono: 'JetBrains Mono', monospace;
}

*, *::before, *::after { margin: 0; padding: 0; box-sizing: border-box; }

body {
  background: var(--void);
  color: var(--text);
  font-family: var(--sans);
  font-weight: 400;
  line-height: 1.6;
}

h1, h2, h3 { font-family: var(--serif); color: var(--text-bright); font-weight: 600; }
h1 { font-size: 28px; letter-spacing: -0.5px; }
h2 { font-size: 22px; }
h3 { font-size: 16px; }

.subtitle { color: var(--text-dim); font-size: 14px; }
code, .mono { font-family: var(--mono); font-size: 12px; }

a { color: var(--violet); text-decoration: none; }
a:hover { color: var(--text-bright); }

/* Setup & form styles */
.setup-container {
  max-width: 640px;
  margin: 60px auto;
  padding: 40px;
}

.setup-container input,
.setup-container select {
  width: 100%;
  padding: 10px 14px;
  background: var(--surface);
  border: 1px solid var(--border);
  border-radius: 8px;
  color: var(--text-bright);
  font-family: var(--sans);
  font-size: 14px;
  margin-bottom: 16px;
}

.setup-container button {
  width: 100%;
  padding: 12px;
  background: linear-gradient(135deg, var(--gold-dim), var(--gold));
  border: none;
  border-radius: 8px;
  color: var(--void);
  font-family: var(--sans);
  font-size: 14px;
  font-weight: 600;
  cursor: pointer;
  box-shadow: 0 4px 20px var(--gold-glow);
  margin-top: 8px;
}

.setup-container label {
  display: block;
  font-family: var(--mono);
  font-size: 11px;
  color: var(--text-dim);
  text-transform: uppercase;
  letter-spacing: 1px;
  margin-bottom: 6px;
}

.hint { font-size: 12px; color: var(--text-dim); margin-top: -8px; margin-bottom: 16px; }
.error { color: var(--attempted); font-size: 13px; }

.setup-options { display: flex; gap: 16px; margin-top: 24px; }
.setup-card {
  flex: 1;
  background: var(--surface);
  border: 1px solid var(--border);
  border-radius: 12px;
  padding: 20px;
  text-align: center;
  display: block;
}
.setup-card.active { border-color: var(--gold-dim); }
.setup-card h3 { margin-bottom: 4px; }
.setup-card p { font-size: 12px; color: var(--text-dim); }
.setup-card .time { font-size: 11px; color: var(--gold); font-family: var(--mono); }

.logo-mark {
  width: 48px;
  height: 48px;
  border-radius: 50%;
  background: radial-gradient(circle at 40% 40%, var(--gold), var(--gold-dim));
  box-shadow: 0 0 30px var(--gold-glow);
  margin: 0 auto 16px;
}

/* Reduced motion */
@media (prefers-reduced-motion: reduce) {
  * { animation-duration: 0s !important; transition-duration: 0s !important; }
}
```

- [ ] **Step 1b: Download self-hosted font files**

Download woff2 files from Google Fonts (or the font foundry) into `static/fonts/`:

```bash
mkdir -p learn-anything-app/static/fonts

# Cormorant Garamond: 400, 400i, 600, 700
# Download from https://fonts.google.com/specimen/Cormorant+Garamond
# Select weights 400, 600, 700 and italic 400, download, extract woff2 files:
#   CormorantGaramond-Regular.woff2
#   CormorantGaramond-Italic.woff2
#   CormorantGaramond-SemiBold.woff2
#   CormorantGaramond-Bold.woff2

# DM Sans: 300, 400, 500, 600
# Download from https://fonts.google.com/specimen/DM+Sans
#   DMSans-Light.woff2
#   DMSans-Regular.woff2
#   DMSans-Medium.woff2
#   DMSans-SemiBold.woff2

# JetBrains Mono: 300, 400
# Download from https://fonts.google.com/specimen/JetBrains+Mono
#   JetBrainsMono-Light.woff2
#   JetBrainsMono-Regular.woff2
```

> **Tip:** Use `google-webfonts-helper` (https://gwfh.mranftl.com/) to get direct woff2 download links for each family/weight combination.

- [ ] **Step 2: Commit**

```bash
git commit -m "feat: Observatory CSS foundation — variables, typography, self-hosted fonts"
```

---

### Task 14: Setup Redirect Middleware + Root Route

**Files:**
- Modify: `learn-anything-app/app/main.py`

- [ ] **Step 1: Add middleware that redirects to setup if not complete**

Add to `app/main.py`:
```python
from fastapi import Request
from fastapi.responses import RedirectResponse
from starlette.middleware.base import BaseHTTPMiddleware
from app.templating import templates

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
```

- [ ] **Step 2: Run all tests**

Run: `uv run pytest tests/ -v`
Expected: All PASS

- [ ] **Step 3: Commit**

```bash
git commit -m "feat: setup guard middleware — redirects to /setup when unconfigured"
```

---

### Task 15: PostgresBackend (stub)

**Files:**
- Create: `learn-anything-app/app/backends/postgres.py`
- Test: `learn-anything-app/tests/integration/test_backends/test_postgres_backend.py`

- [ ] **Step 1: Write test for Postgres backend interface conformance**

```python
# tests/integration/test_backends/test_postgres_backend.py
from app.backends.postgres import PostgresBackend
from app.backends.protocol import StateBackend

def test_postgres_backend_implements_protocol():
    """Verify PostgresBackend has all methods from StateBackend protocol."""
    required_methods = ["read_graph", "write_graph", "query_transfer", "export_json", "import_json"]
    for method in required_methods:
        assert hasattr(PostgresBackend, method), f"Missing method: {method}"
```

- [ ] **Step 2: Implement PostgresBackend stub**

```python
# app/backends/postgres.py
from sqlalchemy.ext.asyncio import AsyncSession
from app.backends.protocol import TransferMatch

class PostgresBackend:
    def __init__(self, session_factory):
        self._session_factory = session_factory

    async def read_graph(self, skill_slug: str) -> dict:
        # Full implementation in Plan 2
        return {}

    async def write_graph(self, skill_slug: str, graph: dict) -> None:
        pass  # Full implementation in Plan 2

    async def query_transfer(self, embeddings: list[float]) -> list[TransferMatch]:
        return []  # Full implementation in Plan 2

    async def export_json(self, skill_slug: str) -> dict:
        return {}  # Full implementation in Plan 2

    async def import_json(self, skill_slug: str, data: dict) -> None:
        pass  # Full implementation in Plan 2
```

- [ ] **Step 3: Run test — should pass**

Run: `uv run pytest tests/integration/test_backends/ -v`
Expected: PASS

- [ ] **Step 4: Commit**

```bash
git commit -m "feat: PostgresBackend stub — interface conformance, implementation in Plan 2"
```

---

### Task 16: Final Integration Test

**Files:**
- Verify: `learn-anything-app/tests/conftest.py` (shared `client` fixture already added in Task 2)

- [ ] **Step 0: Audit dependencies for known vulnerabilities**

Run: `cd learn-anything-app && uv pip audit` (or `pip-audit` if `uv pip audit` is not available)
Expected: No critical vulnerabilities. Address any findings before shipping.

- [ ] **Step 1: Run full test suite**

Run: `uv run pytest tests/ -v --tb=short`
Expected: All tests pass. Count should be ~20+ tests covering:
- Password hashing (2)
- Encryption (3)
- Sessions (2)
- User model (1)
- Graph nodes (2)
- Graph edges (2)
- Learner state (2)
- JSON backend (4)
- Postgres backend interface (1)
- Health endpoint (1)
- Auth routes (2)
- Setup routes (2)

- [ ] **Step 2: Run Docker Compose end-to-end**

```bash
cd learn-anything-app
docker compose up -d --build
sleep 15
curl -s http://localhost:8000/health | python -m json.tool
curl -s -o /dev/null -w "%{http_code}" http://localhost:8000/
# Should be 307 (redirect to /setup)
curl -s -o /dev/null -w "%{http_code}" http://localhost:8000/setup
# Should be 200
docker compose down
```

- [ ] **Step 3: Commit**

```bash
git commit -m "feat: Plan 1 complete — foundation with auth, models, backends, setup wizard, Docker"
```
