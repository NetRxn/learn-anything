import pytest
from app.models.user import User
from app.security.passwords import hash_password


@pytest.mark.asyncio
async def test_create_user(db):
    user = User(
        email="test@example.com",
        display_name="Test",
        password_hash=hash_password("secret"),
        provider="local",
    )
    db.add(user)
    await db.commit()
    await db.refresh(user)
    assert user.id is not None
    assert user.email == "test@example.com"
    assert user.is_admin is False
