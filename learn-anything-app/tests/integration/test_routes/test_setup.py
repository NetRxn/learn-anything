import pytest


@pytest.mark.asyncio
async def test_setup_locked_after_first_admin(client):
    assert (await client.get("/setup")).status_code == 409


@pytest.mark.asyncio
async def test_unimplemented_setup_wizard_routes_not_exposed(client):
    for step in ["database", "llm", "auth"]:
        assert (await client.get(f"/setup/{step}")).status_code == 404

    assert (await client.get("/setup/account")).status_code == 405
