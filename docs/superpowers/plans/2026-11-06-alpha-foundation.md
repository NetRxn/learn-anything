# Alpha identity and persistence checkpoint

> Execute inline with superpowers:executing-plans. Owner explicitly authorized
> Codex, an isolated branch, current guidance, and stable checkpoint merges;
> parent independently reviews before push/merge. No release tags.

**Goal:** A real first-admin setup → login → authenticated learner state save/read
→ resume after process restart checkpoint, without a model or graph learning UI.
**Architecture:** Keep FastAPI/SQLAlchemy/PostgreSQL. Persist identity, settings,
revocable sessions and versioned opaque learner documents; never accept user IDs
from clients. DB URL is bootstrap operator configuration, never a public form
that probes arbitrary hosts. Initial setup is loopback-only and closes atomically.
**Tech stack:** Python 3.14, FastAPI, SQLAlchemy, asyncpg, Alembic, pytest/httpx.
**Spec:** This bounded owner instruction supersedes the six-plan execution batch;
the April design remains the longer-term product vision.

## Constraints and review focus

No shared services, credentials, providers, deployment, tags or plugin behavior
changes. Core PG may be tested without graph extensions, clearly reported.
Require safe test DB selection, setup takeover prevention, auth/admin enforcement,
identity isolation, stale-write conflict handling, malformed input rejection and
restart durability. Freeze unused OAuth until real identity mapping exists.

## Tasks

1. Preserve sanitized app/public design snapshot and update AGENTS/conventions.
   Archive April operational assumptions as non-authoritative. Verify no private
   files, actual credentials or learner data are staged; commit snapshot.
2. Add meaningful failing tests for disposable-DB gating and the complete HTTP
   checkpoint (setup locked after first admin; wrong-password and anonymous denial;
   settings persist encrypted secrets; second learner cannot read first learner's
   documents; revisions reject stale writes; session survives app re-creation).
   Run failures before adding the implementation. Replace dangerous fixture defaults.
3. Implement database-backed account/setup/settings/session/document services and
   ordinary HTML/API routes; persist token signing secret and enforce same-origin
   mutations. Keep public registration/OAuth disabled until deliberately designed.
   Run regression/unit/full suite against isolated PG; commit implementation/tests.
4. Document exact startup/migration/scope/test evidence; independent parent review
   fixes any material findings before merge. No hosted/teaching alpha claim.

## Ledger

- Plan written before implementation. Existing isolated clone verified on
  codex/alpha-foundation at current remote main; owner checkout untouched.
- Local PG17 binaries available; AGE/PGVector not installed. Foundation tests
  cover core PG only. Graph readiness remains unverified.
- Read-only cached Python runtime copied into ignored local scratch; no package
  installation, provider calls or shared database access.
