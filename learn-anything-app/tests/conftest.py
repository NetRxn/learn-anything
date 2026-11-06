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
from app.models.user import User  # noqa: F401
from app.models.config import AppConfig  # noqa: F401
from app.models.graph_nodes import Concept, SkillNode, Domain  # noqa: F401
from app.models.graph_edges import GraphEdge  # noqa: F401
from app.models.learner_state import LearnerState, MasteryTransition  # noqa: F401
from app.models.material import Reference, Material, MaterialTeaches, SourcedFrom, MaterialPrerequisite, MaterialCites  # noqa: F401

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
    from app.main import SetupGuardMiddleware
    SetupGuardMiddleware._setup_complete_cache = None

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as c:
        yield c
