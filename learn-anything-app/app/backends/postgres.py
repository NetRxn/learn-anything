# app/backends/postgres.py
from sqlalchemy.ext.asyncio import AsyncSession
from app.backends.protocol import TransferMatch


class PostgresBackend:
    def __init__(self, session_factory):
        self._session_factory = session_factory

    async def read_graph(self, skill_slug: str) -> dict:
        raise NotImplementedError("PostgreSQL graph engine is outside the foundation checkpoint")

    async def write_graph(self, skill_slug: str, graph: dict) -> None:
        raise NotImplementedError("PostgreSQL graph engine is outside the foundation checkpoint")

    async def query_transfer(self, embeddings: list[float]) -> list[TransferMatch]:
        raise NotImplementedError("PostgreSQL graph engine is outside the foundation checkpoint")

    async def export_json(self, skill_slug: str) -> dict:
        raise NotImplementedError("PostgreSQL graph engine is outside the foundation checkpoint")

    async def import_json(self, skill_slug: str, data: dict) -> None:
        raise NotImplementedError("PostgreSQL graph engine is outside the foundation checkpoint")
