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
