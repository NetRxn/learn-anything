# learn-anything

A Claude Code plugin that helps people learn any skill efficiently. It synthesizes Tim Ferriss' DiSSS/CaFE meta-learning frameworks with evidence-based enhancements from cognitive psychology, instructional design, and motivation science.

The system is domain-agnostic: Spanish, guitar, negotiation, programming, pharmacology, cooking, chess — any skill.

## Commands

| Command | Purpose |
|---|---|
| `/learn [topic or context]` | Primary interface — start, resume, or manage any skill |
| `/train [context or --mode mentor]` | Jump straight into a training session |
| `/materials [type] [task-class]` | Generate or regenerate learning materials *(v2.0)* |
| `/update [what changed]` | Update curriculum for evolving fields *(v2.0)* |

`/learn` delegates to the orchestrator, which handles everything: new skills, resuming, switching, progress checks, material generation, imports, and plan updates. Just describe what you want naturally — `/learn Spanish`, `/learn progress`, `/learn I'm stuck on chord transitions`.

`/train` is a shortcut that skips directly to the Training Conductor for your active skill.

The orchestrator also activates automatically for natural-language requests like "I want to learn Spanish" or "teach me guitar".

## Pipeline

Eight skills form a sequential pipeline, managed by the orchestrator:

```
Onboarding (1-2 conversations):

  Domain Assessor ──> Skill Researcher ──> Learner Calibrator
  (classify skill,     (decompose skill,    (diagnostic assessment,
   learner profile)     dependency graph)     knowledge overlay)

                           ↓ calibration loop (max 2x)

  Curriculum Architect ──> Material Forge ──> Dashboard Generator
  (4C/ID sequencing,       (Anki decks,       (React artifact,
   dual timeline)           exercises)          knowledge map)

Learning (ongoing, session-by-session):

  Training Conductor
  (Socratic teaching, adaptive difficulty, mastery gates,
   spaced retrieval, plateau detection, progress tracking,
   instructor personas, mentor conversation mode)
```

## What's New in v2.0

- **Conversational epitome refinement** — The Curriculum Architect pauses to discuss the first lesson before building the full plan
- **Instructor personas** — Choose a teaching style inspired by masters of the field (e.g., Feynman for physics)
- **Mentor conversation mode** — Relaxed, exploratory discussions via `/train --mode mentor`
- **Session transcripts** — Full session logs saved to `transcripts/` for review
- **Curriculum updates** — `/update` command for evolving fields
- **Material generation** — `/materials` command for on-demand content with dedicated subagents
- **Improved research** — Ferriss interview protocol now mandatory, freshness detection for cutting-edge fields
- **Better visuals** — WCAG-compliant color contrast, inline SVG over Mermaid for learning materials
- **Expert panel** — Skill Researcher identifies masters of the field for persona selection

## Skills

| Skill | Purpose |
|---|---|
| `meta-learning-orchestrator` | Central router — detects pipeline phase, manages state, handles handoffs |
| `domain-assessor` | Classifies skill type/environment, gathers learner profile, sets approach strategy |
| `skill-researcher` | Web-search-grounded decomposition, dependency graph, frequency/impact analysis |
| `learner-calibrator` | Adaptive diagnostic using Knowledge Space Theory, graph propagation, transfer probes |
| `curriculum-architect` | 4C/ID whole-task sequencing, Elaboration Theory epitome, productive failure placement |
| `material-forge` | Anki flashcards, worked examples, practice sets, assessments, Mermaid visualizations |
| `training-conductor` | Interactive sessions using 5 templates (A-E), escalation ladder, real-time calibration |
| `dashboard-generator` | React artifact with knowledge graph, curriculum roadmap, retention metrics |

## State Files

Each skill gets its own workspace under `learn-anything/<skill-slug>/` in the user's project. The active skill is tracked in `learn-anything/active-skill.json`. This supports learning multiple skills simultaneously without file collisions.

```
<user-project>/
└── learn-anything/
    ├── active-skill.json
    ├── spanish/
    │   ├── domain-assessment.json
    │   ├── skill-dossier.json
    │   ├── knowledge-graph.json
    │   ├── learning-plan.json
    │   ├── srs-cards.json
    │   ├── progress.json
    │   ├── materials/
    │   └── external-imports/
    └── classical-guitar/
        └── (same structure)
```

| File | Producer | Schema |
|---|---|---|
| `domain-assessment.json` | Domain Assessor | `schemas/domain-assessment.schema.json` |
| `skill-dossier.json` | Skill Researcher | `schemas/skill-dossier.schema.json` |
| `knowledge-graph.json` | Learner Calibrator + Training Conductor | `schemas/knowledge-graph.schema.json` |
| `learning-plan.json` | Curriculum Architect | `schemas/learning-plan.schema.json` |
| `srs-cards.json` | Material Forge | `schemas/srs-cards.schema.json` |
| `progress.json` | Training Conductor | `schemas/progress.schema.json` |
| `external-imports/` | User/external tools | `schemas/external-import.schema.json` |

## Prerequisites

Python 3 with the `genanki` package (required for Anki deck export by the Material Forge skill):

```bash
# Using uv (recommended)
uv pip install -r requirements.txt

# Or using pip
pip install -r requirements.txt
```

## Installation

### From a local path (for development or testing)

```bash
# from command line run
claude plugin marketplace add /path/to/learn-anything
```

```bash
# Not validated
# In Claude Code, run:
/plugin marketplace add /path/to/learn-anything
```

### From the marketplace

If this plugin is published to a GitHub-based marketplace:

```bash
# Not validated
# In Claude Code, run:
/plugin marketplace add NetRxn/learn-anything
```

Then enable the plugin when prompted. All 8 skills are auto-discovered from the `skills/` directory.


### Verify installation

Once installed, the `meta-learning-orchestrator` skill activates automatically when you say things like "I want to learn Spanish" or "teach me guitar". You can also check `/plugin` to confirm the plugin is enabled.

### Add to your project's .gitignore

The plugin writes learner state to a `learn-anything/` directory in your project. Add this to your project's `.gitignore`:

```
learn-anything/
```

## Key Frameworks

- **DiSSS**: Deconstruction, Selection, Sequencing, Stakes
- **CaFE**: Compression, Frequency, Encoding
- **4C/ID**: Whole-task instruction with sawtooth scaffolding (van Merrienboer)
- **Elaboration Theory**: Epitome-first design (Reigeluth)
- **Productive Failure**: Struggle-before-instruction for conceptual learning (Kapur)
- **FSRS**: Machine-learned spaced repetition scheduling
- **Knowledge Space Theory**: Efficient diagnostic assessment (Doignon & Falmagne)
- **Seven-Layer Motivation Architecture**: Identity, process goals, competence feedback, flow/deliberate practice, relatedness, plateau protocols, strategic stakes

## Anki Round-Trip

The plugin supports bidirectional data flow with Anki:

1. Material Forge generates `.apkg` with deterministic GUIDs and hidden `KnowledgeNodeID` fields
2. User reviews cards in Anki (using FSRS scheduler)
3. User exports review history back to the plugin
4. Training Conductor processes reviews, updates knowledge graph mastery estimates
5. Updated graph informs next session's content and difficulty
