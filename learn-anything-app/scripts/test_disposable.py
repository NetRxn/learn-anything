"""Run pytest using a fresh job-local PG cluster; never target an existing server."""
import os
from pathlib import Path
import random
import subprocess
import sys
import tempfile


def main():
    bindir = Path(os.environ.get("PG_BINDIR", "/opt/homebrew/opt/postgresql@17/bin"))
    if not (bindir / "initdb").is_file():
        raise SystemExit("Set PG_BINDIR to local PostgreSQL binaries; no shared fallback")
    with tempfile.TemporaryDirectory(prefix="la-disposable-", dir="/private/tmp") as root:
        root = Path(root).resolve()
        data = root / "pgdata"
        port = str(random.randrange(20000, 60000))
        subprocess.run([str(bindir / "initdb"), "-D", str(data), "-A", "trust", "--no-locale", "--encoding=UTF8"], check=True, stdout=subprocess.DEVNULL)
        (root / "disposable-marker").write_text(str(data))
        subprocess.run([str(bindir / "pg_ctl"), "-D", str(data), "-l", str(root / "postgres.log"), "-o", f"-k {root} -p {port} -h ''", "-w", "start"], check=True, stdout=subprocess.DEVNULL)
        try:
            subprocess.run([str(bindir / "createdb"), "-h", str(root), "-p", port, "learn_anything_test"], check=True)
            env = {**os.environ, "LA_TEST_DATABASE_URL": f"postgresql+asyncpg:///learn_anything_test?host={root}&port={port}", "LA_TEST_DISPOSABLE_ROOT": str(root), "PYTHONDONTWRITEBYTECODE": "1"}
            # Never inherit runtime credentials/bootstrap configuration.
            for key in [k for k in env if k.startswith("LA_") and not k.startswith("LA_TEST_")]:
                del env[key]
            migration_env = {**env, "LA_DATABASE_URL": env["LA_TEST_DATABASE_URL"]}
            for target in ["head", "base", "head"]:
                command = "downgrade" if target == "base" else "upgrade"
                subprocess.run([sys.executable, "-m", "alembic", command, target], env=migration_env, check=True)
            for phase in ["save", "resume"]:
                subprocess.run([sys.executable, "-m", "scripts.checkpoint_smoke", phase], env=migration_env, check=True)
            result = subprocess.run([sys.executable, "-m", "pytest", *sys.argv[1:]], env=env)
        finally:
            subprocess.run([str(bindir / "pg_ctl"), "-D", str(data), "-m", "immediate", "-w", "stop"], check=True, stdout=subprocess.DEVNULL)
        return result.returncode


if __name__ == "__main__":
    sys.exit(main())
