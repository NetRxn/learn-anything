# NOTE: Uses shared `client` fixture from tests/conftest.py
import pytest


@pytest.mark.asyncio
async def test_login_page_renders(client):
    resp = await client.get("/auth/login")
    assert resp.status_code == 200
    assert "Login" in resp.text or "login" in resp.text


@pytest.mark.asyncio
async def test_register_creates_user(client):
    resp = await client.post("/auth/register", data={
        "email": "new@example.com",
        "display_name": "New User",
        "password": "strong-password-123",
    }, follow_redirects=False)
    assert resp.status_code in (302, 303)
