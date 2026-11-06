"""Observable foundation checkpoints against a dedicated disposable PostgreSQL."""
import pytest
from httpx import AsyncClient, ASGITransport
from sqlalchemy import select
from sqlalchemy.ext.asyncio import async_sessionmaker
from app.models.user import User

ACCOUNT = {"email": "owner@example.com", "display_name": "Owner", "password": "correct horse battery"}


@pytest.fixture
async def fresh(engine, tmp_path):
    from app.main import create_app
    from app.config import Settings
    config = Settings(database_url="", encryption_key_path=str(tmp_path / "key"))
    app = create_app(config, session_factory=async_sessionmaker(engine, expire_on_commit=False))
    async with app.router.lifespan_context(app):
        async with AsyncClient(transport=ASGITransport(app=app, raise_app_exceptions=False), base_url="http://localhost", headers={"Origin": "http://localhost"}) as client:
            yield client, app


@pytest.mark.asyncio
async def test_setup_creates_real_admin_once(fresh):
    client, app = fresh
    assert (await client.post("/setup/account", data=ACCOUNT)).status_code == 303
    async with app.state.sessions() as db:
        owner = (await db.execute(select(User).where(User.email == ACCOUNT["email"]))).scalar_one()
        assert owner.is_admin and owner.password_hash != ACCOUNT["password"]
    assert (await client.post("/setup/account", data={**ACCOUNT, "email": "attacker@example.com"})).status_code == 409
    assert (await client.get("/setup")).status_code == 409
    assert (await client.post("/auth/register", data=ACCOUNT)).status_code == 404


@pytest.mark.asyncio
async def test_login_state_isolation_restart_and_logout(fresh):
    client, app = fresh
    assert (await client.get("/api/workspaces/python/graph")).status_code == 401
    await client.post("/setup/account", data=ACCOUNT)
    assert (await client.post("/auth/login", data={**ACCOUNT, "password": "wrong-password"})).status_code == 401
    login = await client.post("/auth/login", data=ACCOUNT)
    assert login.status_code == 303
    assert "httponly" in login.headers["set-cookie"].lower()
    assert "samesite=strict" in login.headers["set-cookie"].lower()
    token = client.cookies.get("session")
    assert token and token != "temp-user"
    assert (await client.put("/api/workspaces/python/graph", json={"revision": 0, "data": {"nodes": [{"id": "csv"}]}})).json()["revision"] == 1
    assert (await client.put("/api/workspaces/python/graph", json={"revision": 0, "data": {}})).status_code == 409
    from app.main import create_app
    restarted = create_app(app.state.config, session_factory=app.state.sessions)
    async with restarted.router.lifespan_context(restarted):
        async with AsyncClient(transport=ASGITransport(app=restarted), base_url="http://localhost", cookies={"session": token}, headers={"Origin": "http://localhost"}) as resume:
            assert (await resume.get("/api/workspaces/python/graph")).json()["data"] == {"nodes": [{"id": "csv"}]}
            await resume.post("/auth/logout")
            assert (await resume.get("/api/workspaces/python/graph")).status_code == 401
    from app.security.passwords import hash_password
    async with app.state.sessions() as db:
        db.add(User(email="other@example.com", display_name="Other", password_hash=hash_password(ACCOUNT["password"])))
        await db.commit()
    await client.post("/auth/login", data={**ACCOUNT, "email": "other@example.com"})
    assert (await client.get("/api/workspaces/python/graph")).status_code == 404
    assert (await client.get("/settings")).status_code == 403
    assert (await client.post("/settings/llm", data={"api_key": "dummy", "model": "example"})).status_code == 403


@pytest.mark.asyncio
async def test_settings_encrypts_and_masks_key_and_origin_is_required(fresh):
    client, app = fresh
    await client.post("/setup/account", data=ACCOUNT)
    await client.post("/auth/login", data=ACCOUNT)
    assert (await client.post("/settings/llm", headers={"Origin": "https://evil.example"}, data={"api_key": "dummy", "model": "example"})).status_code == 403
    assert (await client.post("/settings/llm", data={"api_key": "dummy-private-key", "model": "example-model"})).status_code == 303
    from app.models.config import AppConfig
    from app.security.encryption import SecretStore
    async with app.state.sessions() as db:
        stored = await db.get(AppConfig, "llm_api_key")
        assert stored.encrypted and "dummy-private-key" not in stored.value
        assert SecretStore(app.state.config.encryption_key_path).decrypt(stored.value) == "dummy-private-key"
    html = (await client.get("/settings")).text
    assert "example-model" in html and "dummy-private-key" not in html
    assert (await client.post("/settings/llm", data={"api_key": "", "model": "second-model"})).status_code == 303
    async with app.state.sessions() as db:
        assert SecretStore(app.state.config.encryption_key_path).decrypt((await db.get(AppConfig, "llm_api_key")).value) == "dummy-private-key"


@pytest.mark.asyncio
async def test_invalid_account_documents_and_cross_origin_are_rejected(fresh):
    client, _ = fresh
    assert (await client.post("/setup/account", data={**ACCOUNT, "password": "short"})).status_code == 422
    assert (await client.post("/setup/account", data={**ACCOUNT, "email": "invalid"})).status_code == 422
    assert (await client.post("/setup/account", headers={"Origin": "http://evil.example"}, data=ACCOUNT)).status_code == 403
    await client.post("/setup/account", data=ACCOUNT)
    await client.post("/auth/login", data=ACCOUNT)
    assert (await client.put("/api/workspaces/bad%20slug/graph", json={"revision": 0, "data": {}})).status_code == 422
    assert (await client.put("/api/workspaces/python/unknown", json={"revision": 0, "data": {}})).status_code == 422
    assert (await client.put("/api/workspaces/python/graph", json={"revision": 0, "data": {}, "user_id": "victim"})).status_code == 422
    client.headers.pop("Origin")
    assert (await client.put("/api/workspaces/python/graph", json={"revision": 0, "data": {}})).status_code == 403


@pytest.mark.asyncio
async def test_remote_setup_is_denied(engine, tmp_path):
    from app.main import create_app
    from app.config import Settings
    app = create_app(Settings(database_url="", encryption_key_path=str(tmp_path / "key")), session_factory=async_sessionmaker(engine))
    async with app.router.lifespan_context(app):
        async with AsyncClient(transport=ASGITransport(app=app, client=("198.51.100.1", 1234)), base_url="http://localhost", headers={"Origin": "http://localhost"}) as client:
            assert (await client.post("/setup/account", data=ACCOUNT)).status_code == 403


@pytest.mark.asyncio
async def test_concurrent_setup_and_updates_have_single_winner(fresh):
    import asyncio
    client, _ = fresh
    outcomes = await asyncio.gather(*[client.post("/setup/account", data={**ACCOUNT, "email": f"owner{i}@example.com"}) for i in range(2)])
    assert sorted(r.status_code for r in outcomes) == [303, 409]
    winner = next(i for i, r in enumerate(outcomes) if r.status_code == 303)
    await client.post("/auth/login", data={**ACCOUNT, "email": f"owner{winner}@example.com"})
    outcomes = await asyncio.gather(*[client.put("/api/workspaces/python/graph", json={"revision": 0, "data": {"winner": i}}) for i in range(2)])
    assert sorted(r.status_code for r in outcomes) == [200, 409]
    assert (await client.put("/api/workspaces/python/graph", json={"revision": 1, "data": {"version": 2}})).json()["revision"] == 2
    assert (await client.put("/api/workspaces/new/graph", json={"revision": 99, "data": {}})).status_code == 409


@pytest.mark.asyncio
async def test_expired_disabled_and_deleted_identity_sessions_fail_closed(fresh):
    from datetime import datetime, timedelta, timezone
    from app.models.workspace import LoginSession
    client, app = fresh
    await client.post("/setup/account", data=ACCOUNT)
    await client.post("/auth/login", data=ACCOUNT)
    async with app.state.sessions() as db:
        session = (await db.execute(select(LoginSession))).scalar_one()
        session.expires_at = datetime.now(timezone.utc) - timedelta(seconds=1)
        await db.commit()
    assert (await client.get("/api/workspaces/python/graph")).status_code == 401
    await client.post("/auth/login", data=ACCOUNT)
    async with app.state.sessions() as db:
        user = (await db.execute(select(User))).scalar_one()
        user.is_active = False
        await db.commit()
    assert (await client.get("/")).status_code == 401
    assert (await client.post("/auth/login", data=ACCOUNT)).status_code == 401
    client.cookies.set("session", "forged-token")
    assert (await client.get("/api/workspaces/python/graph")).status_code == 401


@pytest.mark.asyncio
@pytest.mark.parametrize("case", ["revision", "nonfinite", "size", "lost-key"])
async def test_storage_boundaries_and_missing_encryption_key_fail_closed(fresh, case):
    from pathlib import Path
    client, app = fresh
    await client.post("/setup/account", data=ACCOUNT)
    await client.post("/auth/login", data=ACCOUNT)
    if case == "revision":
        assert (await client.put("/api/workspaces/python/graph", json={"revision": 2147483648, "data": {}})).status_code == 422
    elif case == "nonfinite":
        assert (await client.put("/api/workspaces/python/graph", content='{"revision":0,"data":{"value":NaN}}', headers={"Content-Type": "application/json"})).status_code == 422
    elif case == "size":
        assert (await client.put("/api/workspaces/python/graph", json={"revision": 0, "data": {"long": "x" * (256 * 1024)}})).status_code == 413
    else:
        await client.post("/settings/llm", data={"api_key": "first-key", "model": "example"})
        Path(app.state.config.encryption_key_path).unlink()
        assert (await client.post("/settings/llm", data={"api_key": "replacement", "model": "example"})).status_code == 503
