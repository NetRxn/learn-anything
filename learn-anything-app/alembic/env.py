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
