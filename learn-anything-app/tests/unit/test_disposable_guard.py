import pytest
from tests import conftest


@pytest.mark.asyncio
async def test_shared_database_rejected_before_connect(monkeypatch):
    monkeypatch.setattr(conftest, "TEST_DB_URL", "postgresql+asyncpg://shared.example/learn_anything_test")
    monkeypatch.setenv("LA_TEST_DISPOSABLE_ROOT", "/private/tmp/la-disposable-example")
    with pytest.raises(RuntimeError, match="disposable"):
        await conftest.verify_disposable(None)
