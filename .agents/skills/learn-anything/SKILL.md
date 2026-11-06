---
name: learn-anything
description: Use when a learner wants to start or resume a Learn Anything program, practice a subject, discuss it with a mentor, generate learning materials, inspect progress, or update a curriculum in this repository.
---

# Learn Anything in Codex

This gateway adapts the existing learning instructions to Codex. Keep the full
repository available: the canonical roles, references and state schemas live in
`learn-anything-plugin/`, not in this skill folder. No FastAPI app or database is
needed for these file-based learning sessions.

Read the [orchestrator](../../../learn-anything-plugin/skills/orchestrator/SKILL.md)
and its relevant references first. Route the learner's request using existing
workspace state. When a role is selected, read that role's instruction file and
only its relevant references; follow them directly rather than attempting to
invoke an unavailable Claude-specific skill tool.

| Learner intent | Canonical command semantics |
| --- | --- |
| Start, resume, switch subject, progress or plan changes | [learn](../../../learn-anything-plugin/commands/learn.md) |
| Practice, focused session or mentor conversation | [train](../../../learn-anything-plugin/commands/train.md) |
| Generate missing or requested materials | [materials](../../../learn-anything-plugin/commands/materials.md) |
| Refresh an existing curriculum | [update](../../../learn-anything-plugin/commands/update.md) |

The plugin's `/learn`, `/train`, `/materials` and `/update` slash commands belong
to Claude Code. In Codex, use `$learn-anything` with ordinary language, for example
`$learn-anything I want to learn Python for data analysis`. Pass the learner's
intent as the command's argument context; mentor requests select the existing
mentor teaching mode, without requiring a Codex `/train` command.

Canonical roles (load the selected one, not all at once):
[Domain Assessor](../../../learn-anything-plugin/skills/domain-assessor/SKILL.md),
[Skill Researcher](../../../learn-anything-plugin/skills/skill-researcher/SKILL.md),
[Learner Calibrator](../../../learn-anything-plugin/skills/learner-calibrator/SKILL.md),
[Curriculum Architect](../../../learn-anything-plugin/skills/curriculum-architect/SKILL.md),
[Material Forge](../../../learn-anything-plugin/skills/material-forge/SKILL.md),
[Training Conductor](../../../learn-anything-plugin/skills/training-conductor/SKILL.md),
[Dashboard Generator](../../../learn-anything-plugin/skills/dashboard-generator/SKILL.md).
Resolve each role's `references/` paths relative to that role's own directory.

Keep learner state under the chosen project's `learn-anything/` directory using
the canonical [state schemas](../../../learn-anything-plugin/schemas). Read and
validate existing state before updating it; preserve completed work and history.
Back up personal state and keep it out of source commits. Do not commit, publish
or upload learning files merely because a learning session writes them.

Use tools actually available in the current Codex environment. Adapt Claude
file/search tool names to those equivalents. If web research, generated dashboard
rendering or optional Anki export tools are unavailable, state the limitation and
preserve pending work; do not invent research, mastery evidence or a rendered
artifact. The gateway grants no credentials, provider access or deployment rights.
