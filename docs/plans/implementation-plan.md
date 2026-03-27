# Meta-Learning Plugin System: Implementation Plan

## What We're Building

A Claude skill suite with an orchestrator that takes any target skill and produces an adaptive training program. Seven components, implemented as individual skills within a Claude Project. The full architecture and technical spec are in `meta-learning-architecture-spec.md`.

This plan covers: what to build first, what the MVP looks like, what decisions to make upfront, and how to iterate toward the full vision.

---

## Upfront Decisions

These need to be settled before writing the first skill, because every component depends on them.

### File Structure

```
meta-learning/
├── orchestrator/
│   └── SKILL.md                    # Routing, state management, phase detection
├── domain-assessor/
│   └── SKILL.md                    # Skill classification + learner profile
├── skill-researcher/
│   ├── SKILL.md                    # Deconstruction + dependency graph
│   └── references/
│       └── expert-interview-protocol.md
├── learner-calibrator/
│   ├── SKILL.md                    # Diagnostic assessment + knowledge graph overlay
│   └── references/
│       └── diagnostic-algorithm.md
├── curriculum-architect/
│   ├── SKILL.md                    # Selection, sequencing, scheduling
│   └── references/
│       ├── 4cid-encoding.md        # 4C/ID rules as behavioral instructions
│       └── motivation-architecture.md
├── material-forge/
│   ├── SKILL.md                    # Material generation + export
│   ├── scripts/
│   │   └── generate_anki.py        # genanki-based .apkg export
│   └── references/
│       ├── card-design-guide.md
│       ├── session-templates.md     # Templates A-E for Conductor reference too
│       └── quality-rubrics.md
├── training-conductor/
│   ├── SKILL.md                    # Session management + adaptive teaching
│   └── references/
│       ├── session-templates.md     # Templates A-E with dialogue patterns
│       ├── difficulty-calibration.md
│       └── assessment-types.md
├── dashboard-generator/
│   └── SKILL.md                    # React artifact generation
└── schemas/
    ├── domain-assessment.schema.json
    ├── skill-dossier.schema.json
    ├── knowledge-graph.schema.json
    ├── learning-plan.schema.json
    ├── progress.schema.json
    ├── srs-cards.schema.json
    └── external-import.schema.json
```

The `schemas/` directory is shared across all skills. Each schema mirrors the target Postgres/AGE structure and defines the JSON format for project file artifacts. Skills read/write these files; the schemas are the contract between components.

### State Management Convention

All persistent state lives as JSON files in the Claude Project:
- `domain-assessment.json` — Written by Assessor, read by all
- `skill-dossier.json` — Written by Researcher, read by Calibrator/Architect/Forge
- `knowledge-graph.json` — Written by Calibrator, updated by Conductor and imports
- `learning-plan.json` — Written by Architect, read by Forge/Conductor
- `progress.json` — Written by Conductor after each session
- `srs-cards.json` — Written by Forge, read by Conductor for in-session probes

Every component reads state at the start, writes updated state at the end. The orchestrator manages which files exist (to determine pipeline phase) and validates state transitions.

### JSON Schema Approach

Schemas are defined once and referenced everywhere. Each schema maps directly to the Postgres/AGE target — same field names, same types, same relationships. The `component_id` field is always a string matching an AGE vertex ID. Arrays of component_ids always use `TEXT[]` compatible format. Timestamps are ISO-8601. Embeddings are stored as JSON arrays of floats (portable to pgvector `VECTOR` type).

The schemas are the first thing to build. Everything else depends on them.

---

## Build Order & Phases

### Phase 0: Foundations (before any skill)

**Build the JSON schemas.** Define the data contract for every inter-component artifact. This is ~1 day of careful work but prevents cascading mismatches later.

Schemas to define:
1. `domain-assessment.schema.json` — Skill classification + learner profile
2. `skill-dossier.schema.json` — Component inventory + dependency graph (AGE vertex/edge format)
3. `knowledge-graph.schema.json` — Dependency graph + learner overlay (mastery states, BKT params, FSRS params)
4. `learning-plan.schema.json` — Curriculum structure, schedule, motivation architecture
5. `progress.schema.json` — Session logs, assessment results, mastery transitions, next agenda
6. `srs-cards.schema.json` — Card definitions with component refs, tags, difficulty, Bloom's level
7. `external-import.schema.json` — Anki reviews, self-reports, unstructured notes

Also build: `generate_anki.py` script (genanki wrapper). This is deterministic Python that doesn't need iteration — it takes a JSON array of cards and produces an .apkg file. Build it once, test it, done.

**Deliverables:** 7 schema files, 1 Python script, tested Anki round-trip.

### Phase 1: The Research Pipeline (Assessment → Research → Calibration)

These three components form the system's "intake" — they take a learning goal and produce the knowledge graph that everything else depends on. Build them together because they're tightly coupled and useless independently.

**Skill 1a: Domain Assessor**

The simplest skill. It runs a structured conversation gathering skill classification and learner background, then writes `domain-assessment.json`.

Prompt structure: Classification rubric (skill type, environment, Bloom's ceiling, modularity, tacit ratio) as a checklist the LLM works through, followed by learner interview questions. The output is deterministic in structure — the LLM fills in the fields.

This is a good first skill to build because it's low-risk (no complex generation, just structured questioning) and immediately testable. Run it for 3-4 different skills (Python, guitar, negotiation, Mandarin) and verify the classifications make sense.

**Skill 1b: Skill Researcher**

The most intellectually ambitious skill. It runs the full Ferriss deconstruction protocol enhanced with web search, builds the dependency graph, does frequency analysis, and identifies transfer pathways using the learner profile.

This is where prompt engineering matters most. The multi-pass decomposition approach (top-down, then bottom-up, then reconcile), confidence flagging, and confabulation detection need careful encoding. The reference file `expert-interview-protocol.md` carries the Ferriss questions and the web search strategy.

The critical output is the dependency graph in AGE-compatible JSON. Each node needs: id, name, description, type, blooms_level, frequency_score, impact_score, confidence. Each edge needs: from_id, to_id, type, strength. This structure must match the schema exactly.

Test by researching 3-4 diverse skills and verifying: graph structure is plausible, confidence flags appear where expected, frequency analysis produces reasonable distributions, and the output JSON validates against the schema.

**Skill 1c: Learner Calibrator**

Takes the dependency graph and walks through it with the learner via adaptive diagnostic assessment. Produces the knowledge graph overlay.

The diagnostic algorithm (graph propagation, embedding-cluster inference, information-theoretic item selection) is described procedurally in the spec, but in the plugin context the LLM executes it conversationally — it doesn't run actual Bayesian math. Instead, the prompt encodes the *behavior*: "Start with gateway nodes. If the learner demonstrates mastery on a skill, mark its prerequisites as likely mastered (lower confidence). If they fail, mark dependents as likely unknown. Choose the next question to resolve the most uncertainty."

The key challenge: making the assessment feel like a conversation, not an exam. The reference file should include example diagnostic dialogues.

Test by running calibration against the dependency graphs from 1b with different learner backgrounds (complete beginner, adjacent expert, partial knowledge) and verifying the overlay makes sense.

**Phase 1 integration test:** Run all three in sequence for a real skill. Verify the full pipeline from "I want to learn X" through to a completed knowledge graph with learner overlay. The gap analysis should read as a sensible curriculum scope estimate.

**Deliverables:** 3 skills, tested individually and as a pipeline.

### Phase 2: Curriculum & Materials (Architect → Forge)

With the knowledge graph in hand, these two components design and produce the learning program.

**Skill 2a: Curriculum Architect**

Takes the gap map and produces the learning plan. This is where 4C/ID, Elaboration Theory, productive failure, and the motivation architecture get encoded.

The prompt is the densest in the system — it needs to encode complex instructional design frameworks as behavioral rules. The reference files do the heavy lifting: `4cid-encoding.md` translates van Merriënboer into step-by-step curriculum generation instructions, `motivation-architecture.md` defines the seven layers.

The key output is the sequenced curriculum with task classes, the dual timeline, and the session schedule. Each curriculum entry references specific knowledge graph nodes by ID.

Test by generating curricula for the same 3-4 skills from Phase 1 and evaluating: Does the epitome make sense? Do task classes increase in complexity? Are productive failure moments placed at conceptual building blocks? Does the schedule respect spacing research? Is the motivation architecture present and appropriate for the skill type?

**Skill 2b: Material Forge**

The production engine. Takes the learning plan and generates all materials — flashcards, worked examples, practice sets, assessments, reference sheets.

This skill is wide rather than deep — it generates many material types, each with different quality criteria. The reference files are critical: `card-design-guide.md` (Matuschak's principles + anti-patterns), `quality-rubrics.md` (four-check rubric for every output), and the genanki script for Anki export.

Build the Anki export as the first deliverable from the Forge — it's the most tangible output and immediately useful. Flashcard generation is also the easiest to evaluate (cards are either good or bad; the anti-patterns are well-defined).

Then add: worked examples with backward fading, reference one-pagers (PDF via the pdf skill), dependency graph visualization (Mermaid), and assessment instruments.

Test by generating materials for one complete curriculum and evaluating against the quality rubric. Export an Anki deck, import it, verify the round-trip (including KnowledgeNodeID preservation).

**Phase 2 integration test:** Full pipeline from assessment through materials. User should receive: a learning plan document, an Anki deck, reference PDFs, and a Mermaid visualization of their knowledge graph.

**Deliverables:** 2 skills, Anki export tested end-to-end, material quality validated.

### Phase 3: The Training Conductor

The big one. This is where the user spends 90% of their time, and it's the most complex skill in the system.

Build incrementally within a single skill:

**3a: Session skeleton** — Session loading protocol (read progress state, identify what's due, load context), session open/close, state writing after each session. Test that state persists correctly across multiple conversations.

**3b: Retrieval probes** — At session start, run delayed retention probes on previously taught material. Map results to knowledge graph updates. This validates the SRS-in-conversation mechanism and the state update pipeline.

**3c: Template A (concept introduction)** — Implement the first teaching template. Socratic dialogue with the EMT escalation ladder. This is where the six failure mode guardrails get their first real test.

**3d: Template C (skill drilling)** — Implement the scaffolded practice template with fading. Tests the difficulty calibration logic.

**3e: Template E (mastery gate)** — Implement assessment. Tests the mastery criteria and the routing logic (pass → advance, fail → re-teach).

**3f: Templates B and D** — Retrieval practice/review and productive failure facilitation. These are important but can come after the core teach/practice/assess loop works.

**3g: External data integration** — Import processing for Anki review stats and self-reports. Update knowledge graph from external data at session start.

**3h: Plateau detection and plan adaptation** — Monitor progress metrics, trigger re-assessment or re-sequencing when needed.

**Phase 3 integration test:** Run a multi-session learning engagement (3-5 sessions) for a real skill. Verify: state persists across sessions, retrieval probes reference previous material, difficulty adapts based on performance, mastery gates control progression, and the knowledge graph evolves with each session.

**Deliverables:** 1 skill (the largest), tested across multiple sessions.

### Phase 4: Dashboard & Orchestrator

**Skill 4a: Dashboard Generator**

Build the React artifact that visualizes the knowledge graph, progress, and curriculum state. This reads the JSON files produced by the other components.

The primary view is the knowledge graph with mastery overlay — nodes colored by state, with the curriculum path highlighted. Use a force-directed graph layout or a hierarchical tree depending on graph structure. Include: progress metrics (delayed retention, breadth/depth), curriculum position, session history, and upcoming agenda.

**Skill 4b: Orchestrator (full version)**

The orchestrator has been implicit during Phases 1-3 (we've been invoking components manually). Now formalize it as the entry-point skill that detects the pipeline phase, routes to the correct component, manages handoffs, and handles the calibration loop.

The routing logic from the spec:
```
IF phase == "ONBOARDING":
  IF NOT domain_assessment_exists → ASSESSOR
  IF NOT skill_tree_exists → RESEARCHER
  IF NOT calibration_complete → CALIBRATOR
  IF NOT curriculum_exists → ARCHITECT
  ELSE → FORGE → TRANSITION to "LEARNING"

IF phase == "LEARNING":
  IF needs_new_material → FORGE
  IF learner_active → CONDUCTOR
  ...
```

Test the full end-to-end flow: user says "I want to learn X," orchestrator routes through all components, user receives their complete setup, then transitions into training sessions.

**Deliverables:** Dashboard artifact, orchestrator skill, full end-to-end pipeline validated.

---

## MVP Definition

**The MVP is Phases 0-2 plus the Conductor skeleton (3a-3e).** This delivers:

A user can say "I want to learn [skill] to [level] in [timeframe]" and receive:
- A classified skill assessment with constructive dual timeline
- A researched dependency graph of skill components
- A calibrated knowledge graph showing their current state and gaps
- A sequenced curriculum with task classes, schedule, and motivation architecture
- An Anki flashcard deck exported as .apkg
- Reference materials as PDF/Markdown
- A visual dependency graph (Mermaid)
- Interactive teaching sessions with concept introduction, practice, and assessment
- Persistent progress tracking across sessions

What the MVP does **not** include:
- Productive failure facilitation (Template D) — available in Phase 3f
- External data import (Anki review stats back into the system) — Phase 3g
- Plateau detection and automatic plan adaptation — Phase 3h
- Dashboard artifact — Phase 4
- Full orchestrator routing — Phase 4

The MVP is a complete learning system. It just doesn't have the feedback loops and visualization that make the full system adaptive over long engagements.

---

## Testing Strategy

Each skill gets tested at three levels:

**Unit testing:** Run the skill in isolation with 3-4 diverse inputs (different skill types, learner backgrounds). Verify output structure matches schemas, content is reasonable, and edge cases don't break it.

**Integration testing:** Run the pipeline through the dependency chain. Assessor → Researcher → Calibrator → Architect → Forge → Conductor. Verify handoff data is correct, references resolve, and the downstream component produces sensible output given its inputs.

**User testing:** Run a real multi-session learning engagement. Pick a skill you (the user) actually want to learn, go through the full pipeline, do 3-5 training sessions over a week. This surfaces problems that synthetic testing misses — pacing issues, motivation failures, calibration drift, material quality under real use.

The test skills should span the skill taxonomy: one cognitive (programming or math), one motor-adjacent (cooking or music), one language, and one social/analytical (negotiation or writing). This ensures domain-specific adaptations are working.

---

## Implementation Sequence Summary

| Phase | Components | Depends On | Key Deliverable |
|-------|-----------|------------|-----------------|
| 0 | Schemas + Anki script | Nothing | Data contracts, tested .apkg export |
| 1 | Assessor + Researcher + Calibrator | Phase 0 | Knowledge graph with learner overlay |
| 2 | Architect + Forge | Phase 1 | Complete learning plan + materials |
| 3 | Conductor (incremental) | Phase 2 | Multi-session teaching capability |
| 4 | Dashboard + Orchestrator | Phase 3 | Visual home base + automated routing |

Estimated effort: Phase 0 is a day. Phase 1 is the most iteration-heavy (the Researcher prompt needs tuning). Phase 2 is medium (Forge is wide but each material type is straightforward). Phase 3 is the longest (Conductor is complex and needs multi-session testing). Phase 4 is relatively quick (Dashboard is a React artifact, orchestrator is routing logic).

---

## First Session: What to Build

Start with **Phase 0**: the JSON schemas and the genanki script. This is foundational, testable, and unblocks everything else. Once schemas exist, move immediately into the Domain Assessor (the simplest skill, the fastest to validate) and then the Skill Researcher (the most important skill, the most iteration needed).
