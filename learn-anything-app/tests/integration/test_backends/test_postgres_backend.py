from app.backends.postgres import PostgresBackend
from app.backends.protocol import StateBackend


def test_postgres_backend_implements_protocol():
    """Verify PostgresBackend has all methods from StateBackend protocol."""
    required_methods = ["read_graph", "write_graph", "query_transfer", "export_json", "import_json"]
    for method in required_methods:
        assert hasattr(PostgresBackend, method), f"Missing method: {method}"
