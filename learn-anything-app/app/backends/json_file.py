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
