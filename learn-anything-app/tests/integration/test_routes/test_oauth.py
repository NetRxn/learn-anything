import pytest


@pytest.mark.asyncio
async def test_oauth_is_not_exposed_until_real_identity_mapping_exists(client):
    for path in ["google", "github", "google/callback", "github/callback"]:
        assert (await client.get(f"/auth/oauth/{path}")).status_code == 404
