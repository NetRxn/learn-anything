import pytest


@pytest.mark.asyncio
async def test_settings_page_renders(client):
    resp = await client.get("/settings")
    assert resp.status_code == 200
    assert "Settings" in resp.text or "settings" in resp.text


@pytest.mark.asyncio
async def test_settings_update_llm_provider(client):
    resp = await client.post("/settings/llm", data={
        "api_key": "sk-ant-test-key",
        "model": "claude-opus-4-6",
    }, follow_redirects=False)
    assert resp.status_code in (200, 303)
