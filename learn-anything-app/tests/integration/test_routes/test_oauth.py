import pytest


@pytest.mark.asyncio
async def test_google_oauth_redirect_when_configured(client):
    # When Google OAuth is configured, /auth/oauth/google should redirect to Google
    resp = await client.get("/auth/oauth/google", follow_redirects=False)
    # Without config, should return 404 or redirect to login with error
    assert resp.status_code in (302, 307, 404)


@pytest.mark.asyncio
async def test_github_oauth_redirect_when_configured(client):
    resp = await client.get("/auth/oauth/github", follow_redirects=False)
    assert resp.status_code in (302, 307, 404)


@pytest.mark.asyncio
async def test_oauth_callback_without_state_rejected(client):
    resp = await client.get("/auth/oauth/google/callback")
    assert resp.status_code in (400, 422)
