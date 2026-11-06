# Learn Anything application foundation

This is a separate experimental FastAPI app alongside the **working Claude Code
plugin** in `../learn-anything-plugin/`. No plugin behavior or release version
changes in this checkpoint. App scope is identity and document persistence, not
an end-to-end learning alpha.

## Implemented checkpoint

- First administrator creation on loopback only, serialized in PostgreSQL and
  permanently closed after completion. No public registration or OAuth.
- Password verification and opaque, high-entropy session cookies; only token
  hashes are stored. Sessions expire, can be logged out, and verify active DB
  identity/admin rights on every request. No default signing secret is used.
- Admin-only model/key settings. Keys are AES-GCM encrypted with an atomically
  created 0600 key file. Blank replacement preserves the current key. No provider
  calls are made. Back up the DB and key together; a missing/corrupt key requires
  deliberate operator recovery, never a silent key reset.
- Per-identity, per-skill documents (`profile`, `graph`, `plan`, `progress`,
  `session`) in PostgreSQL JSONB, maximum 256 KiB of serialized document data.
  Writes use optimistic revisions: zero creates, current revision updates;
  conflicts return 409. These are opaque documents, **not validated plugin state
  schemas or a working graph engine**. API user identity comes only from session.
- Server-rendered setup, login, settings and a saved-document list. Ordinary
  same-origin HTTP, no JavaScript dependency. Private responses use `no-store`;
  mutations require an exact Origin and cookies are HttpOnly/SameSite=Strict.

## Local startup

Python >=3.14 and a **dedicated local PostgreSQL database** are required. Plain
PG17 is sufficient for this checkpoint. AGE/PGVector are future graph prerequisites.
Do not point development at a shared or production database. No shared database,
runner, proxy or deployment admission is implied by this repository.

From this directory, install locked development dependencies with
`uv sync --locked --extra dev`. Set `LA_DATABASE_URL` explicitly to your dedicated
local asyncpg connection string; set `LA_ENCRYPTION_KEY_PATH` to a persistent
private file. The app does not load `.env` files. Do not put credentials in Git.

Run migrations explicitly before startup:

```sh
uv run alembic upgrade head
uv run uvicorn app.main:app --host 127.0.0.1 --port 8000
```

Open `http://localhost:8000/setup`, create the admin and log in. The DB URL is
bootstrap configuration, not a browser form that probes arbitrary network hosts.
Migrations do not auto-run at startup; startup fails if configuration/schema is
missing. Copying a Compose/Docker design example does not establish it works:
container builds, AGE/PGVector, volume permissions and managed deployment are
unverified. Compose publishes only to loopback and requires an explicit DB password.

## Document API

An authenticated same-origin request can `GET` or `PUT`
`/api/workspaces/{skill-slug}/{document}`. PUT JSON shape:

```json
{"revision": 0, "data": {"goal": "Analyze a small table"}}
```

The response includes persisted `revision` and `data`. Keep the returned revision
for the next write; reload on 409. Missing document returns 404. Invalid/slashed
skill identifiers, unsupported document types and extra top-level identity fields
are rejected. NUL and unpaired surrogate strings unsupported by PG JSONB
return 422; literal escape text and valid Unicode remain supported. A new skill needs no global shared graph. The UI lists saved
artifacts; a browser document editor is not implemented.

## Verification

```sh
uv run pytest                 # no DB configured: explicit integration skips
uv run pytest tests/unit -q   # no database or network needed
uv run python scripts/test_disposable.py -q
```

Set `PG_BINDIR` if local PostgreSQL binaries are not in the script's macOS default
location. The disposable runner creates a fresh UTF-8 cluster under `/private/tmp`,
with a unique Unix socket and **no TCP listener**. It replays migration
upgrade→base→head, then performs authenticated save/readback in two independent
Python processes, then runs pytest. It stops/removes the cluster on exit.
Integration fixtures verify the socket root, DB name, marker and actual server
`data_directory` **before** dropping tables. No default shared-service connection
exists. A sandbox may require permission for PostgreSQL OS shared memory.

As of this checkpoint: 58 tests passed on disposable PG17; 10 unit tests passed
without a DB. New foundation/model/encryption coverage 93%. These tests validate
core PG models and HTTP behavior, not AGE/PGVector graph queries. Dependency
security audit, container/browser QA, infrastructure admission, deployment and
owner acceptance are separate, unestablished gates.

## Remaining alpha work

No research/provider execution, assessment, curriculum generation, teaching,
material generation, graph visualization, adaptive engine, offline/PWA or full
backup/restore. Opaque JSON storage is a foundation for these, not their delivery.
No multiuser account-management UI is implemented. No password reset, login
throttling, session-management UI or hosted ingress hardening: keep this bound to
loopback. Do not expose it publicly. No release tags or deployment in this work.

Current scope: `../docs/superpowers/plans/2026-11-06-alpha-foundation.md`.
Historical April plans remain design references, not operational instructions.
