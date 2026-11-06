# NOTE: Uses shared `client` fixture from tests/conftest.py
import pytest


@pytest.mark.asyncio
async def test_setup_welcome_renders(client):
    resp = await client.get("/setup")
    assert resp.status_code == 200
    assert "Learn Anything" in resp.text


@pytest.mark.asyncio
async def test_setup_steps_render(client):
    for step in ["database", "llm", "auth", "account"]:
        resp = await client.get(f"/setup/{step}")
        assert resp.status_code == 200
