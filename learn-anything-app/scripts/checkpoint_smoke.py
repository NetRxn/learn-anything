"""Two-process smoke, invoked only by the disposable test runner."""
import asyncio
import os
from pathlib import Path
import sys
from httpx import AsyncClient, ASGITransport
from app.config import Settings
from app.main import create_app


async def main():
    root = Path(os.environ["LA_TEST_DISPOSABLE_ROOT"])
    if root.parent != Path("/private/tmp") or not root.name.startswith("la-disposable-") or not (root / "disposable-marker").is_file():
        raise RuntimeError("Disposable runner required")
    app = create_app(Settings(encryption_key_path=str(root / "secret.key")))
    token_path = root / "session-token"
    async with app.router.lifespan_context(app):
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://localhost", headers={"Origin": "http://localhost"}) as client:
            if sys.argv[1] == "save":
                account = {"email": "restart@example.com", "display_name": "Restart", "password": "disposable-test-password"}
                assert (await client.post("/setup/account", data=account)).status_code == 303
                assert (await client.post("/auth/login", data=account)).status_code == 303
                assert (await client.put("/api/workspaces/python/progress", json={"revision": 0, "data": {"checkpoint": "persisted"}})).status_code == 200
                fd = os.open(token_path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
                with os.fdopen(fd, "w") as stream:
                    stream.write(client.cookies["session"])
            else:
                client.cookies.set("session", token_path.read_text())
                assert (await client.get("/api/workspaces/python/progress")).json() == {"revision": 1, "data": {"checkpoint": "persisted"}}
                assert (await client.get("/")).status_code == 200
                print("Fresh-process authenticated document readback: PASS")


if __name__ == "__main__":
    asyncio.run(main())
