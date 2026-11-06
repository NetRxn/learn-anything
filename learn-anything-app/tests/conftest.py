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

# Model imports — ensure all tables are created
from app.models.workspace import LoginSession, WorkspaceDocument  # noqa: F401
from app.models.user import User  # noqa: F401
from app.models.config import AppConfig  # noqa: F401
from app.models.graph_nodes import Concept, SkillNode, Domain  # noqa: F401
from app.models.graph_edges import GraphEdge  # noqa: F401
from app.models.learner_state import LearnerState, MasteryTransition  # noqa: F401
from app.models.material import Reference, Material, MaterialTeaches, SourcedFrom, MaterialPrerequisite, MaterialCites  # noqa: F401

# Real PG — no SQLite. AGE and PGVector require actual PostgreSQL.
TEST_DB_URL = os.environ.get("LA_TEST_DATABASE_URL", "")


async def verify_disposable(eng):
    from pathlib import Path
    from sqlalchemy import text
    from sqlalchemy.engine import make_url
    root_value = os.environ.get("LA_TEST_DISPOSABLE_ROOT", "")
    if not TEST_DB_URL or not root_value:
        pytest.skip("Integration requires scripts/test_disposable.py; no shared DB fallback")
    root = Path(root_value).resolve()
    url = make_url(TEST_DB_URL)
    if (not root.name.startswith("la-disposable-") or root.parent != Path("/private/tmp")
            or url.database != "learn_anything_test" or url.host is not None
            or url.query.get("host") != str(root)
            or not (root / "disposable-marker").is_file()):
        raise RuntimeError("Refusing a database without disposable job-local proof")
    async with eng.connect() as conn:
        actual = await conn.scalar(text("SHOW data_directory"))
    if str(Path(actual).resolve()) != (root / "disposable-marker").read_text():
        raise RuntimeError("Connected server does not match disposable cluster")



@pytest.fixture
async def engine():
    if not TEST_DB_URL:
        pytest.skip("Integration requires scripts/test_disposable.py")
    eng = create_async_engine(TEST_DB_URL)
    await verify_disposable(eng)
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
async def client(engine, tmp_path):
    """Real admin session; no setup or authentication bypass in test fixtures."""
    from app.main import create_app
    from app.config import Settings
    app = create_app(Settings(database_url="", encryption_key_path=str(tmp_path / "key")),
                     session_factory=async_sessionmaker(engine, expire_on_commit=False))
    async with app.router.lifespan_context(app):
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://localhost",
                               headers={"Origin": "http://localhost"}) as c:
            account = {"email": "test@example.com", "display_name": "Tester", "password": "safe-test-password"}
            assert (await c.post("/setup/account", data=account)).status_code == 303
            assert (await c.post("/auth/login", data=account)).status_code == 303
            yield c
