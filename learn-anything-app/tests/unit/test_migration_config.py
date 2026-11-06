"""Exercise the real Alembic env without connecting to any database."""
import runpy
from pathlib import Path
import pytest
from alembic import context
from alembic.config import Config
import sqlalchemy
from app.config import settings


def test_percent_encoded_database_credentials_reach_driver_unchanged(monkeypatch):
    url = "postgresql+asyncpg://learner:dummy%40pass%25word@localhost:55432/learn_anything_test"
    expected = "postgresql+psycopg://learner:dummy%40pass%25word@localhost:55432/learn_anything_test"
    config = Config()
    monkeypatch.setattr(context, "config", config, raising=False)
    monkeypatch.setattr(settings, "database_url", url)

    class ConnectionBoundaryReached(Exception):
        pass

    def boundary(configuration, **kwargs):
        assert configuration["sqlalchemy.url"] == expected
        raise ConnectionBoundaryReached

    monkeypatch.setattr(sqlalchemy, "engine_from_config", boundary)
    with pytest.raises(ConnectionBoundaryReached):
        runpy.run_path(str(Path(__file__).resolve().parents[2] / "alembic" / "env.py"))
