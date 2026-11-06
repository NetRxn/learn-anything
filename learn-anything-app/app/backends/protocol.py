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
