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
