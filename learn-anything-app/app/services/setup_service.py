# app/services/setup_service.py
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.models.config import AppConfig
from app.security.encryption import SecretStore


async def is_setup_complete(db: AsyncSession) -> bool:
    result = await db.execute(select(AppConfig).where(AppConfig.key == "setup_complete"))
    row = result.scalar_one_or_none()
    return row is not None and row.value == "true"


async def get_config(db: AsyncSession, key: str, secret_store: SecretStore | None = None) -> str | None:
    result = await db.execute(select(AppConfig).where(AppConfig.key == key))
    row = result.scalar_one_or_none()
    if row is None:
        return None
    if row.encrypted and secret_store:
        return secret_store.decrypt(row.value)
    return row.value


async def set_config(db: AsyncSession, key: str, value: str, encrypted: bool = False, secret_store: SecretStore | None = None):
    stored_value = value
    if encrypted and secret_store:
        stored_value = secret_store.encrypt(value)
    result = await db.execute(select(AppConfig).where(AppConfig.key == key))
    existing = result.scalar_one_or_none()
    if existing:
        existing.value = stored_value
        existing.encrypted = encrypted
    else:
        db.add(AppConfig(key=key, value=stored_value, encrypted=encrypted))
    await db.commit()
