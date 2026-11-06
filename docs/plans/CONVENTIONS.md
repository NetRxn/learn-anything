# Current application conventions (2026-11-06)

Owner authorization permits Codex implementation and stable reviewed checkpoint
merges, with no release tags. This supersedes the April Opus-only worker rule
and mandatory all-six-plans batch. April plans are historical design references;
they do not admit runners, authorize shared databases or grant deployment access.

- Separate plugin delivery from app development; preserve dirty owner workspaces.
- State a bounded plan before code, use meaningful failing tests first, and review
  actual source and test results before merging. No model/provider calls by default.
- Python >=3.14; no npm frontend/build dependencies; self-hosted assets preferred.
- Unit tests require no DB/network. Real PostgreSQL for persistence integration;
  no SQLite. This foundation checkpoint exercises core PG only; graph work must
  qualify AGE/PGVector separately. Record that distinction in results.
- Test fixtures may only use disposable job-local PostgreSQL explicitly marked
  for destruction. No fallback credentials, shared service, SSH tunnel, secret
  store, CI runner or private provisioning runbook is part of this workflow.
- Keep environment files, encryption keys, learner data and caches out of Git.
- Datastar SSE, when implemented, uses the SDK. This checkpoint uses ordinary
  server-rendered pages and HTTP APIs; no learning/streaming UI is claimed.
- `uv run pytest` from `learn-anything-app/` is the suite command; missing optional
  integration prerequisites must produce explicit skips, not fake successes.
- Infrastructure admission, deployment, browser acceptance and source tests are
  independent gates. The app ships no authority to mutate managed services.
