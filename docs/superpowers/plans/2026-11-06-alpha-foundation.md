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

- Task1 complete: snapshot commit `0c84876`, sanitized public plan import and current
  AGENTS/conventions. No private runbook, environment or learner data copied.
- Task2: setup persisted-user assertion failed on old303/no-write behavior.
  New factory tests then failed on absent factory; later cases caught plaintext
  encrypted-config writes, concurrent key loss, silent graph stubs, invalid JSON
  and integer500s, and lost-key replacement. All corrected before final suite.
- Ruling: ordinary server HTML/API replaces unused placeholder Datastar/OAuth
  surfaces in this checkpoint. No learning UI or provider execution is claimed.
- Ruling: reject corrupt/empty key files rather than silently rotate them; old
  tempfile fixtures updated to create missing paths. Concurrent publication uses
  a complete0600 file and atomic hard-link, preventing first-use key loss.
- Ruling: plain isolated PG validates identity/document persistence only. Existing
  graph model tests validate relational schema, not AGE/PGVector functionality.
- Migration upgrade→base→head and independent-process save/resume are run by the
  disposable runner. All generated DBs/tokens/keys are temporary and excluded.
- Final validation: disposable PG17 upgrade→base→head succeeded; independent
  process authenticated readback PASS; full suite54 passed in21.31s. New
  foundation/model/encryption coverage93%. Unit-only9 passed in1.36s without DB.
  No-DB full run15 passed/35 skipped before the four additional PG boundary cases.
- Dependency security audit was not run (no advisory service/network access used).
  Containers, extension engine, browser layout, infra, deployment and owner
  acceptance are unverified. Parent independent review precedes push/merge.

- Independent review fixes: percent-encoded credentials reproduced an Alembic
  ConfigParser error; regression now verifies exact encoded URL reaches the
  SQLAlchemy boundary. Escaped percent signs only for ConfigParser storage.
  PG JSONB NUL keys/values and lone surrogates reproduced HTTP500; explicit
  recursive validation now422, valid escape text/Unicode round-trip unchanged.
- Reviewed-fix full verification:58 passed in18.63s, coverage93%; migration replay
  and independent-process authenticated readback PASS. No provider calls.

- Separate authorized adapter scope: a repository-native Codex skill gateway
  reads canonical plugin roles/references rather than copying them; normal Codex
  requests map to learn/train/materials/update semantics, Claude slash commands
  stay intact. Root README separates client setup. No plugin files changed.
- Adapter baseline: repository discovery/path tests failed with missing gateway;
  after implementation2 structural checks passed and bundled skill-creator
  quick_validate reported valid frontmatter. All8 canonical roles,4 command
  files,7 schema files and referenced specialist resources resolve locally.
  Per explicit no-modelcalls scope, no behavioral/teaching invocation validation
  was performed; no provider or learning-outcome claim is made.

- Independent root verification: disposable PG run58 passed in18.76s; migration
  replay and fresh-process authenticated readback passed. Reviewer approved the
  migration/JSONB fixes plus adapter structural checks and10 unit tests.
- Final docs-only cleanup reconciles root README's four Claude commands, optional
  export dependency, conditional private-fork authentication and dual-client
  product description. Canonical plugin files remain unchanged. Push/merge have
  not been performed by this implementation worker; no release tags created.
