# Learn Anything contributor guidance

The Claude Code plugin (`learn-anything-plugin/`) and experimental FastAPI app
(`learn-anything-app/`) are separate products. Preserve plugin semantics and its
packaging unless the task explicitly changes them. The app is not a deployed
learning service. For app changes, read its README and checkpoint plan first.

Codex implementation is owner-authorized as of 2026-11-06. Earlier plan text
requiring Opus workers is superseded. Use the available agent/model; state scope,
inspect current source, write meaningful failing regressions, implement small
reviewable changes, run relevant checks and independently review before merging.
Do not fabricate model names, installed skills, tool capabilities or green checks.

Work on `codex/*` branches in isolated clones/worktrees. Preserve dirty owner
checkouts. Merge stable reviewed checkpoints as authorized; do not create release
tags. No providers, paid calls, credentials, shared infrastructure changes or
live deployment are authorized by this repository's instructions.

App tests: `cd learn-anything-app && uv run pytest`. Unit tests must run without a
DB. Integration tests require an explicitly disposable job-local PostgreSQL;
never connect fixtures that drop/create tables to a shared or production DB.
Graph tests additionally require AGE/PGVector. No SQLite substitute. Report unit,
core-PG integration, extension integration, browser, deployment and acceptance
separately. No npm frontend; use static assets and Python tooling.

Never commit `.env`, keys, learner state, private runbooks or runtime caches.
Historical April plans are design references, not current infrastructure authority.

Guidance informed by official OpenAI documentation:
https://learn.chatgpt.com/guides/best-practices

Learning sessions use `.agents/skills/learn-anything/SKILL.md` and canonical plugin
instructions. Contributor branch/test requirements govern source changes, not
ordinary learner sessions. Do not provision app infrastructure to use the gateway.
Structural adapter checks: `python3 -m unittest discover -s tests -v` from repo root.
