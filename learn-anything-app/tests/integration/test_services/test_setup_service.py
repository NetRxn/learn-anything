import pytest
from app.models.config import AppConfig
from app.services.setup_service import is_setup_complete, get_config, set_config


@pytest.mark.asyncio
async def test_is_setup_complete_false_when_empty(db):
    result = await is_setup_complete(db)
    assert result is False


@pytest.mark.asyncio
async def test_is_setup_complete_true_when_set(db):
    db.add(AppConfig(key="setup_complete", value="true"))
    await db.commit()
    result = await is_setup_complete(db)
    assert result is True


@pytest.mark.asyncio
async def test_set_and_get_config(db):
    await set_config(db, "test_key", "test_value")
    result = await get_config(db, "test_key")
    assert result == "test_value"


@pytest.mark.asyncio
async def test_get_config_missing_returns_none(db):
    result = await get_config(db, "nonexistent")
    assert result is None


@pytest.mark.asyncio
async def test_set_config_updates_existing(db):
    await set_config(db, "key1", "v1")
    await set_config(db, "key1", "v2")
    result = await get_config(db, "key1")
    assert result == "v2"


@pytest.mark.asyncio
async def test_set_config_encrypted(db):
    from app.security.encryption import SecretStore
    import tempfile, os
    with tempfile.NamedTemporaryFile(delete=False, suffix=".key") as f:
        key_path = f.name
    os.unlink(key_path)
    try:
        store = SecretStore(key_path)
        await set_config(db, "secret", "my-api-key", encrypted=True, secret_store=store)
        # Raw value in DB should NOT be plaintext
        raw = await get_config(db, "secret")
        assert raw != "my-api-key"
        # Decrypted value should match
        decrypted = await get_config(db, "secret", secret_store=store)
        assert decrypted == "my-api-key"
    finally:
        os.unlink(key_path)


@pytest.mark.asyncio
async def test_encrypted_config_without_key_store_is_rejected(db):
    with pytest.raises(ValueError, match="SecretStore"):
        await set_config(db, "private_key", "must-not-persist", encrypted=True)
    assert await get_config(db, "private_key") is None
