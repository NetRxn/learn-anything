# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What This Is

A Claude Code plugin marketplace containing `learn-anything` — a meta-learning plugin with 8 skills that form a pipeline from "I want to learn X" to adaptive, ongoing training. It is domain-agnostic (Spanish, guitar, programming, etc.). The system is built on Tim Ferriss' DiSSS/CaFE frameworks combined with cognitive psychology and instructional design research (4C/ID, Knowledge Space Theory, FSRS, productive failure).

## Repository Layout

This is a **Claude Code plugin marketplace repo**, not a traditional application. There is no build system, test suite, or linting.

- `.claude-plugin/marketplace.json` — Marketplace manifest (top-level, lists available plugins)
- `learn-anything-plugin/` — The single plugin in this marketplace
  - `.claude-plugin/plugin.json` — Plugin manifest (name, version, description)
  - `commands/` — Two slash commands: `/learn` and `/train` (both `.md` files)
  - `skills/` — 8 skill directories, each with a `SKILL.md` and optional `references/`
  - `schemas/` — 7 JSON schemas defining the contract between pipeline components
- `docs/` — Architecture spec, implementation plan, and research materials
- `learn-anything-plugin.zip` — Pre-built zip for distribution

## Architecture: The Pipeline

Skills execute in sequence, managed by the orchestrator. State files in `learn-anything/<skill-slug>/` determine pipeline phase (if the file exists, that phase is complete):

```
Domain Assessor → Skill Researcher → Learner Calibrator → Curriculum Architect → Material Forge → Dashboard Generator → Training Conductor (ongoing)
```

Each skill reads upstream state files and writes its own. The orchestrator detects which files exist and routes to the next incomplete phase. A calibration loop (max 2x) can bounce between Researcher and Calibrator if assessment reveals unexpected gaps.

### State File → Producer Mapping

| File | Producer Skill |
|---|---|
| `domain-assessment.json` | domain-assessor |
| `skill-dossier.json` | skill-researcher |
| `knowledge-graph.json` | learner-calibrator (+ training-conductor updates) |
| `learning-plan.json` | curriculum-architect |
| `srs-cards.json` | material-forge |
| `progress.json` | training-conductor |

All state files conform to schemas in `learn-anything-plugin/schemas/`.

### Central Data Structure

The **dual-layer knowledge graph** (`knowledge-graph.json`) is the system's core artifact:
- Layer 1: Skill dependency graph (same for all learners of a given skill)
- Layer 2: Learner state overlay (mastery states per node, updated by Training Conductor and Anki imports)

The gap between these layers *is* the curriculum.

## Only Code: generate_anki.py

The single Python script lives at `learn-anything-plugin/skills/material-forge/scripts/generate_anki.py`. It exports `srs-cards.json` to `.apkg` for Anki import.

**Run it:**
```bash
python learn-anything-plugin/skills/material-forge/scripts/generate_anki.py <srs-cards.json> [output.apkg]
```

**Dependency:** `genanki>=0.13.0` (install via `uv pip install genanki` or `pip install -r learn-anything-plugin/requirements.txt`)

**Key design constraints:**
- Model/Deck IDs in `anki_config` are hardcoded per plan — changing them creates duplicates on re-import
- GUIDs are deterministic via `genanki.guid_for(card_id)` so re-exports update existing cards
- Each note includes a hidden `KnowledgeNodeID` field for round-trip data flow (export → Anki review → reimport)
- SVGs are sanitized (script/event handler removal) before embedding in card HTML

## Editing Skills

Each skill is a self-contained `SKILL.md` file with YAML frontmatter (`name`, `description`) followed by the full skill prompt. The `description` field is critical — it determines when Claude Code auto-activates the skill. Reference materials in `references/` subdirectories are loaded by the skill at runtime.

When editing a skill:
- The `description` in frontmatter must be specific enough to trigger correctly and not false-positive on unrelated requests
- Skills read specific state files as inputs and write specific state files as outputs — respect the schema contracts in `schemas/`
- The orchestrator's routing logic in `skills/orchestrator/SKILL.md` must stay in sync with what each skill expects

## Packaging for Distribution

The `learn-anything-plugin.zip` is the distributable artifact. After making changes to the plugin, update the zip:

```bash
cd /Users/johnroehm/Programming/Infrastructure/Plugin-Library/learn-anything
zip -r learn-anything-plugin.zip learn-anything-plugin/ -x "learn-anything-plugin/.git/*"
```

Update the version in `learn-anything-plugin/.claude-plugin/plugin.json` when making releases.

## Plugin Validation

```bash
cd learn-anything-plugin
claude plugin validate .
```
