from app.backends.postgres import PostgresBackend
from app.backends.protocol import StateBackend


def test_postgres_backend_implements_protocol():
    """Verify PostgresBackend has all methods from StateBackend protocol."""
    required_methods = ["read_graph", "write_graph", "query_transfer", "export_json", "import_json"]
    for method in required_methods:
        assert hasattr(PostgresBackend, method), f"Missing method: {method}"


import pytest


@pytest.mark.asyncio
async def test_unimplemented_graph_backend_never_claims_success():
    backend = PostgresBackend(None)
    for operation in [lambda: backend.read_graph("python"), lambda: backend.write_graph("python", {}),
                      lambda: backend.query_transfer([]), lambda: backend.export_json("python"), lambda: backend.import_json("python", {})]:
        with pytest.raises(NotImplementedError, match="graph"):
            await operation()
