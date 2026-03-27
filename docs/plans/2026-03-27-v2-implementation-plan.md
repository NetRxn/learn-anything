# Learn-Anything v2.0 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Comprehensive update of the learn-anything plugin across 4 phases: code quality, content quality, learner experience, and lifecycle/data — addressing 9 user pain points and baseline code review findings.

**Architecture:** This is a Claude Code plugin consisting entirely of markdown skills (SKILL.md), JSON schemas, markdown commands, and markdown agent definitions. All changes are to prompt/schema files — no traditional application code except the existing `generate_anki.py` script (unchanged). Each phase uses a feature branch with PR+merge to main.

**Tech Stack:** Markdown (SKILL.md files), JSON Schema draft-07, Claude Code plugin framework (auto-discovery of skills/, commands/, agents/)

**Spec:** `docs/specs/2026-03-27-v2-comprehensive-update-design.md`

---

## File Map

All paths relative to `learn-anything-plugin/`.

### Existing files to edit

| File | Phases | Responsibility |
|------|--------|---------------|
| `skills/orchestrator/SKILL.md` | A, C, D | Pipeline routing, state management, handoffs |
| `skills/domain-assessor/SKILL.md` | A, C | Skill classification, learner profile, teaching preferences |
| `skills/skill-researcher/SKILL.md` | A, B, C, D | Skill decomposition, Ferriss interviews, expert panel, freshness, update mode |
| `skills/learner-calibrator/SKILL.md` | A | Diagnostic assessment, knowledge graph overlay |
| `skills/curriculum-architect/SKILL.md` | A, C, D | Curriculum design, epitome refinement, update mode |
| `skills/material-forge/SKILL.md` | A, B | Material generation orchestration, subagent dispatch |
| `skills/training-conductor/SKILL.md` | A, C, D | Session teaching, persona, mentor mode, transcripts |
| `skills/dashboard-generator/SKILL.md` | A | Progress visualization |
| `skills/material-forge/references/card-design-guide.md` | B | Card design rules, color palette |
| `skills/material-forge/references/quality-rubrics.md` | B | QA checks for all material types |
| `skills/skill-researcher/references/expert-interview-protocol.md` | B | Ferriss interview questions and search strategies |
| `skills/training-conductor/references/session-templates.md` | C | Session templates A-E (adding F) |
| `commands/train.md` | C | /train command with mode argument |
| `schemas/domain-assessment.schema.json` | C | Adding teaching_preferences |
| `schemas/skill-dossier.schema.json` | A, B, C | Field annotations, freshness_assessment, expert_panel |
| `.claude-plugin/plugin.json` | A | Version bump |
| `README.md` (plugin) | A | Full documentation update |
| `../README.md` (root) | A | Marketplace quick-start update |
| `../.claude-plugin/marketplace.json` (root) | A | Version bump |

### New files to create

| File | Phase | Responsibility |
|------|-------|---------------|
| `skills/domain-assessor/references/classification-guide.md` | A | Skill type decision tree, environment rubric |
| `skills/orchestrator/references/routing-flowchart.md` | A | Routing logic, schema field map, handoff protocols |
| `commands/materials.md` | B | /materials command |
| `commands/update.md` | D | /update command |
| `agents/visual-material-generator.md` | B | SVG visual generation subagent |
| `agents/worked-example-generator.md` | B | Worked example generation subagent |
| `agents/flashcard-generator.md` | B | SRS flashcard generation subagent |
| `agents/assessment-generator.md` | B | Assessment instrument generation subagent |

---

## Phase A: Code Quality & Polish

**Branch:** `phase-a/code-quality`

### Task 1: Create feature branch

**Files:** None (git operation)

- [ ] **Step 1: Create and switch to feature branch**

```bash
cd /Users/johnroehm/Programming/Infrastructure/Plugin-Library/learn-anything
git checkout -b phase-a/code-quality
```

- [ ] **Step 2: Verify clean state**

```bash
git status
```

Expected: `On branch phase-a/code-quality`, clean working tree.

---

### Task 2: Writing Style Normalization — orchestrator

**Files:**
- Modify: `learn-anything-plugin/skills/orchestrator/SKILL.md`

- [ ] **Step 1: Fix opening paragraph (line 8)**

Replace:
```
You are the central coordinator of a meta-learning plugin system that helps people learn any skill efficiently. You route between seven component skills, manage persistent state, and ensure the pipeline flows smoothly from initial goal-setting through ongoing training.
```

With:
```
Act as the central coordinator of a meta-learning plugin system that helps people learn any skill efficiently. Route between seven component skills, manage persistent state, and ensure the pipeline flows smoothly from initial goal-setting through ongoing training.
```

- [ ] **Step 2: Fix all remaining second-person instances**

Search the file for "you are", "you should", "your job", "you will", "you need", "you must" (case-insensitive, excluding text inside quoted learner-facing messages). Replace each with imperative form. Examples:

- "you should orient the learner" → "Orient the learner"
- "you will need to" → "It is necessary to" or simply use imperative
- "your goal is to" → "The goal is to"

- [ ] **Step 3: Validate**

```bash
cd /Users/johnroehm/Programming/Infrastructure/Plugin-Library/learn-anything
grep -in "you are\|your job\|you should\|you will\|you need\|you must" learn-anything-plugin/skills/orchestrator/SKILL.md | grep -v "learner\|user\|\"" | head -20
```

Expected: Zero matches outside of quoted learner-facing messages.

- [ ] **Step 4: Commit**

```bash
git add learn-anything-plugin/skills/orchestrator/SKILL.md
git commit -m "style(orchestrator): normalize to imperative voice

Remove second-person constructions ('You are...', 'Your job...')
and replace with imperative/infinitive form per plugin-dev best practices."
```

---

### Task 3: Writing Style Normalization — domain-assessor

**Files:**
- Modify: `learn-anything-plugin/skills/domain-assessor/SKILL.md`

- [ ] **Step 1: Fix opening paragraph (lines 8-9)**

Replace:
```
You are the entry point of a meta-learning system that helps people learn any skill efficiently. Your job is to classify the target skill, understand the learner's starting point, and set a constructive strategy for everything downstream.
```

With:
```
Serve as the entry point of a meta-learning system that helps people learn any skill efficiently. Classify the target skill, understand the learner's starting point, and set a constructive strategy for everything downstream.
```

- [ ] **Step 2: Fix all remaining second-person instances**

Search the file for "you are", "you should", "your job", "you will", "you need", "you must" (case-insensitive, excluding text inside quoted learner-facing messages). Replace each with imperative form:
- "you are the..." → "Act as the..." or "Serve as the..."
- "your job is to..." → imperative verb: "Classify...", "Map...", etc.
- "you should..." → direct imperative: "Orient the learner...", "Check..."
- "you will need to..." → "It is necessary to..." or direct imperative
- "you must..." → "Ensure..." or direct imperative

- [ ] **Step 3: Validate**

```bash
grep -in "you are\|your job\|you should\|you will\|you need" learn-anything-plugin/skills/domain-assessor/SKILL.md | grep -v "learner\|user\|\"" | head -20
```

Expected: Zero matches outside quoted messages.

- [ ] **Step 4: Commit**

```bash
git add learn-anything-plugin/skills/domain-assessor/SKILL.md
git commit -m "style(domain-assessor): normalize to imperative voice"
```

---

### Task 4: Writing Style Normalization — skill-researcher

**Files:**
- Modify: `learn-anything-plugin/skills/skill-researcher/SKILL.md`

- [ ] **Step 1: Fix opening paragraph (lines 8-9)**

Replace:
```
You are the research engine of a meta-learning system. Your job is to deeply investigate a target skill, decompose it into its fundamental components, build a dependency graph, identify which components matter most, find transfer pathways from the learner's existing skills, and catalog common failure points.
```

With:
```
Act as the research engine of a meta-learning system. Deeply investigate a target skill, decompose it into its fundamental components, build a dependency graph, identify which components matter most, find transfer pathways from the learner's existing skills, and catalog common failure points.
```

- [ ] **Step 2: Fix all remaining second-person instances**

Search each file for "you are", "you should", "your job", "you will", "you need", "you must" (case-insensitive). Replace with imperative form per the patterns in Task 2 Step 2. Exclude text inside quoted learner-facing messages (strings inside `"..."` or example dialogue).

- [ ] **Step 3: Validate and commit**

```bash
grep -in "you are\|your job\|you should" learn-anything-plugin/skills/skill-researcher/SKILL.md | grep -v "learner\|user\|\"" | head -20
git add learn-anything-plugin/skills/skill-researcher/SKILL.md
git commit -m "style(skill-researcher): normalize to imperative voice"
```

---

### Task 5: Writing Style Normalization — remaining skills

**Files:**
- Modify: `learn-anything-plugin/skills/learner-calibrator/SKILL.md`
- Modify: `learn-anything-plugin/skills/curriculum-architect/SKILL.md`
- Modify: `learn-anything-plugin/skills/material-forge/SKILL.md`
- Modify: `learn-anything-plugin/skills/training-conductor/SKILL.md`
- Modify: `learn-anything-plugin/skills/dashboard-generator/SKILL.md`

- [ ] **Step 1: Fix learner-calibrator opening**

Replace:
```
You are the diagnostic engine of a meta-learning system. Your job is to efficiently map a learner's existing knowledge onto the skill dependency graph, producing the knowledge graph overlay — the precise "gap map" that tells the Curriculum Architect exactly what to teach and what to skip.
```

With:
```
Act as the diagnostic engine of a meta-learning system. Efficiently map a learner's existing knowledge onto the skill dependency graph, producing the knowledge graph overlay — the precise "gap map" that tells the Curriculum Architect exactly what to teach and what to skip.
```

- [ ] **Step 2: Fix curriculum-architect opening**

Replace:
```
You design the bridge between where the learner is and where they want to be. You work from the gap — not from scratch — leveraging existing knowledge as scaffolding and transfer pathways as accelerators.
```

With:
```
Design the bridge between where the learner is and where they want to be. Work from the gap — not from scratch — leveraging existing knowledge as scaffolding and transfer pathways as accelerators.
```

- [ ] **Step 3: Fix material-forge opening**

Replace:
```
You are the production engine of a meta-learning system. You generate all the tangible learning materials: flashcard decks, exercises, reference sheets, assessments, and visualizations. Quality is make-or-break — bad materials produce bad learning.
```

With:
```
Act as the production engine of a meta-learning system. Generate all tangible learning materials: flashcard decks, exercises, reference sheets, assessments, and visualizations. Quality is make-or-break — bad materials produce bad learning.
```

Also standardize capitalization: replace all instances of "material forge" (lowercase) and "the Forge" with "Material Forge" consistently.

- [ ] **Step 4: Fix training-conductor opening**

Replace:
```
You are the core teaching agent. You work with learners session-by-session over weeks or months — teaching, questioning, assessing, adapting, and motivating. Every session should feel like working with a skilled human tutor who knows exactly where you are, what to work on next, and how to push you just enough.
```

With:
```
Act as the core teaching agent. Work with learners session-by-session over weeks or months — teaching, questioning, assessing, adapting, and motivating. Every session should feel like working with a skilled human tutor who knows exactly where the learner is, what to work on next, and how to push them just enough.
```

- [ ] **Step 5: Fix dashboard-generator opening**

Replace:
```
You generate a React artifact (.jsx) that serves as the learner's visual home base. It displays their knowledge graph with mastery overlay, curriculum position, key metrics, and upcoming agenda.
```

With:
```
Generate a React artifact (.jsx) that serves as the learner's visual home base. Display the knowledge graph with mastery overlay, curriculum position, key metrics, and upcoming agenda.
```

- [ ] **Step 6: Fix all remaining second-person across all 5 files**

For each file, grep and fix remaining instances. Exclude learner-facing quoted messages.

- [ ] **Step 7: Validate all 8 SKILL.md files**

```bash
for f in learn-anything-plugin/skills/*/SKILL.md; do
  echo "=== $f ==="
  grep -in "^[^\"]*\(you are\|your job\|you should\)" "$f" | head -5
done
```

Expected: Zero matches across all files (outside quotes).

- [ ] **Step 8: Commit**

```bash
git add learn-anything-plugin/skills/learner-calibrator/SKILL.md \
        learn-anything-plugin/skills/curriculum-architect/SKILL.md \
        learn-anything-plugin/skills/material-forge/SKILL.md \
        learn-anything-plugin/skills/training-conductor/SKILL.md \
        learn-anything-plugin/skills/dashboard-generator/SKILL.md
git commit -m "style: normalize remaining 5 skills to imperative voice

Consistent imperative/infinitive form across all 8 SKILL.md files.
Standardize 'Material Forge' capitalization."
```

---

### Task 6: Frontmatter Description Standardization

**Files:**
- Modify: All 7 non-orchestrator SKILL.md files (frontmatter only)

The orchestrator already uses the correct format. Update the other 7 to use third-person "This skill should be used when..." format with specific trigger phrases.

- [ ] **Step 1: Update domain-assessor frontmatter**

Replace the existing `description:` line with:
```yaml
description: "This skill should be used when the user states a learning goal — any phrase like 'I want to learn X', 'teach me X', 'help me get better at X', or 'how do I learn X'. Classifies the skill type (motor/cognitive/perceptual/social), assesses the learning environment (kind vs. wicked), gathers the learner's background for transfer learning, and produces a constructive approach strategy. This is always the first step in the meta-learning pipeline. Output is structured JSON conforming to domain-assessment.schema.json."
```

- [ ] **Step 2: Update skill-researcher frontmatter**

Replace:
```yaml
description: "This skill should be used when the user's learning goal has been classified by the Domain Assessor and needs deep investigation. Performs skill deconstruction into components, dependency graph construction, frequency/impact analysis, transfer pathway identification, failure point cataloging, and expert panel discovery. Uses web search extensively to ground decomposition in real expert perspectives. Output is a Skill Research Dossier conforming to skill-dossier.schema.json."
```

- [ ] **Step 3: Update learner-calibrator frontmatter**

Replace:
```yaml
description: "This skill should be used when the Skill Researcher has produced a dependency graph and the learner's existing knowledge needs mapping. Walks through the graph conversationally, assessing mastery at key nodes using graph propagation and information-theoretic item selection to minimize questions needed. Produces the knowledge graph overlay (the 'gap map') that drives curriculum design. Output is structured JSON conforming to knowledge-graph.schema.json."
```

- [ ] **Step 4: Update curriculum-architect frontmatter**

Replace:
```yaml
description: "This skill should be used when the Learner Calibrator has produced the gap map and a learning plan needs designing. Applies 4C/ID whole-task instruction, Elaboration Theory epitome design, productive failure placement, and a seven-layer motivation architecture. Produces a sequenced curriculum with task classes, a dual-timeline schedule, assessment criteria, and plateau protocols. Includes a conversational checkpoint for epitome refinement with the learner. Output is structured JSON conforming to learning-plan.schema.json."
```

- [ ] **Step 5: Update material-forge frontmatter**

Replace:
```yaml
description: "This skill should be used when the Curriculum Architect has produced a learning plan and learning materials need generating, or on-demand when the Training Conductor needs new materials, or when the user invokes '/materials'. Orchestrates dedicated subagents to generate worked examples with fading, visual materials, SRS flashcard decks, assessment instruments, reference one-pagers, dependency graph visualizations, productive failure scenarios, interleaved practice sets, and encoding aids. All outputs conform to the system's JSON schemas and are exportable to Anki (.apkg), PDF, and Markdown."
```

- [ ] **Step 6: Update training-conductor frontmatter**

Replace:
```yaml
description: "This skill should be used when a learner is ready for a training session — they've been through the assessment/research/calibration/curriculum pipeline and have a learning plan, or when the user invokes '/train'. Manages session flow (warm-up, deliberate practice, integration), adaptive teaching using Socratic questioning and the EMT escalation ladder, real-time difficulty calibration, in-session retrieval probes, mastery gate assessments, knowledge graph updates, external data integration (Anki, self-reports), plateau detection, motivation management, instructor persona adoption, and mentor conversation mode. Sessions are scoped to ~150k tokens. State is read at session start and written at session end."
```

- [ ] **Step 7: Update dashboard-generator frontmatter**

Replace:
```yaml
description: "This skill should be used when the learning plan has been created (initial generation) or after each training session (update), or when the user asks to see their progress or dashboard. Generates and updates a React dashboard artifact that visualizes the learner's knowledge graph, curriculum progress, and key metrics. The dashboard is the learner's visual home base within the Claude Project, rendering an interactive knowledge graph with mastery overlay, curriculum roadmap, progress metrics, session history, and upcoming agenda."
```

- [ ] **Step 8: Commit**

```bash
git add learn-anything-plugin/skills/*/SKILL.md
git commit -m "style: standardize frontmatter descriptions to third-person trigger format

All 8 skills now use 'This skill should be used when...' format
with specific trigger phrases per plugin-dev best practices."
```

---

### Task 7: Schema-Process Gap Closure

**Files:**
- Modify: `learn-anything-plugin/skills/skill-researcher/SKILL.md`
- Modify: `learn-anything-plugin/schemas/skill-dossier.schema.json`

- [ ] **Step 1: Add cognitive_load_type instruction to skill-researcher**

In the skill-researcher SKILL.md, find Step 3 (Component Identification). After the existing component property list, add:

```markdown
- **cognitive_load_type**: Classify as `intrinsic` (inherent complexity of the component itself), `extraneous` (complexity from how it's presented — should be minimized), or `germane` (productive complexity that builds schema). Most components are intrinsic. Flag any that are primarily germane (learning-to-learn skills) or that risk extraneous load if poorly taught.
```

- [ ] **Step 2: Add cluster_id instruction to skill-researcher**

In Step 4 (Dependency Graph Construction), add:

```markdown
- **cluster_id**: Assign each vertex to a semantic cluster. Group components that naturally belong together (e.g., "foundations", "intermediate-techniques", "advanced-applications"). Use short kebab-case identifiers (e.g., `core-mechanics`, `strategy-layer`, `tooling`). Clusters inform the dashboard visualization and help the Curriculum Architect design task classes.
```

- [ ] **Step 3: Add assessment_criteria instruction to skill-researcher**

In Step 3 (Component Identification), add after the example field:

```markdown
- **assessment_criteria**: Brief description of how mastery of this component can be assessed. Be specific: "Can explain the difference between X and Y" or "Can perform X correctly under Y conditions". This feeds into the Learner Calibrator's question design and Material Forge's assessment instruments.
```

- [ ] **Step 4: Add description annotations to schema for deferred fields**

In `schemas/skill-dossier.schema.json`, update the `embedding` field description:

Replace:
```json
"embedding": { "type": "array", "items": { "type": "number" }, "description": "Semantic embedding vector for pgvector similarity search" },
```

With:
```json
"embedding": { "type": "array", "items": { "type": "number" }, "description": "DEFERRED — Semantic embedding vector for pgvector similarity search. Not generated in current architecture (no vector DB). Leave null/omitted." },
```

- [ ] **Step 5: Commit**

```bash
git add learn-anything-plugin/skills/skill-researcher/SKILL.md \
        learn-anything-plugin/schemas/skill-dossier.schema.json
git commit -m "fix(skill-researcher): close schema-process gaps

Add generation instructions for cognitive_load_type, cluster_id,
and assessment_criteria. Mark embedding field as deferred."
```

---

### Task 8: Validation Steps (all 7 producer skills)

**Files:**
- Modify: All 7 producer SKILL.md files (domain-assessor, skill-researcher, learner-calibrator, curriculum-architect, material-forge, training-conductor, dashboard-generator)

- [ ] **Step 1: Add Input Verification section to each skill**

At the start of each skill's Process section (after Inputs, before Step 1), add:

```markdown
### Input Verification

Before proceeding, verify all required upstream state files exist and contain the expected fields. If any file is missing or its required fields are absent, report the issue to the user rather than proceeding with partial data. Specifically check:
```

Then list the skill-specific inputs. For example, for skill-researcher:
```markdown
- `domain-assessment.json` exists and contains `skill_classification.target_skill` and `learner_profile`
- `active-skill.json` exists and contains `active` field
```

For curriculum-architect:
```markdown
- `knowledge-graph.json` exists and contains `graph.vertices` (non-empty array) and `gap_analysis`
- `domain-assessment.json` exists and contains `learner_profile.constraints` and `approach_strategy`
```

Adapt for each skill based on its documented inputs.

- [ ] **Step 2: Add Validate Output section to each skill**

At the end of each skill's Process section (before the final "Present summary" step), add:

```markdown
### Validate Output

Before writing the output file, verify:
1. The JSON conforms to `schemas/<relevant-schema>.schema.json` — all required fields present and correctly typed
2. All UUID fields are valid v4 UUIDs
3. All date-time fields are ISO 8601 format
4. All enum fields use values from the schema's enum lists
5. Array fields that should be non-empty are non-empty

If validation fails, fix the issue before writing. Do not write invalid JSON to the state file.
```

Replace `<relevant-schema>` with the actual schema name for each skill.

- [ ] **Step 3: Commit**

```bash
git add learn-anything-plugin/skills/*/SKILL.md
git commit -m "fix: add input verification and output validation to all producer skills

Each skill now checks upstream state files before processing
and validates JSON output against schema before writing."
```

---

### Task 9: Create Reference Files

**Files:**
- Create: `learn-anything-plugin/skills/domain-assessor/references/classification-guide.md`
- Create: `learn-anything-plugin/skills/orchestrator/references/routing-flowchart.md`

- [ ] **Step 1: Create classification-guide.md**

```markdown
# Skill Classification Guide

## Skill Type Decision Tree

Determine the PRIMARY skill type by asking: "What does the learner physically/mentally DO when practicing this skill?"

### Motor
The learner's body performs movements that improve with physical repetition.
- Examples: guitar, swimming, surgery, dance, handwriting, pottery
- Key indicator: Physical practice is required — watching/reading alone won't build competence
- Teaching implication: External-focus cues, Perform-Report-Refine loops, video/mirror feedback

### Cognitive Lower (Remember/Understand/Apply)
The learner memorizes facts, understands concepts, or applies known procedures.
- Examples: vocabulary, exam prep (NAPLEX, bar exam), coding syntax, medical dosing tables
- Key indicator: Success is measurable by recall accuracy and procedural correctness
- Teaching implication: Heavy SRS, worked examples, interleaved practice, mastery gates

### Cognitive Higher (Analyze/Evaluate/Create)
The learner analyzes situations, evaluates options, or creates novel solutions.
- Examples: architecture design, debugging, literary analysis, investment strategy, negotiation
- Key indicator: No single correct answer — requires judgment, trade-off reasoning, synthesis
- Teaching implication: Case-based reasoning, Socratic dialogue, productive failure, portfolio assessment

### Perceptual
The learner discriminates sensory patterns that experts perceive but novices miss.
- Examples: wine tasting, radiology reading, bird identification, music ear training, quality inspection
- Key indicator: "I can't see/hear/taste what you're talking about" — the skill IS the perception
- Teaching implication: Vocabulary before discrimination, anchoring exemplars, contrast sets, verbal overshadowing risk

### Social
The learner navigates interpersonal dynamics with tacit knowledge components.
- Examples: sales, teaching, therapy, leadership, public speaking, negotiation
- Key indicator: High tacit knowledge — experts can't fully articulate what they do
- Teaching implication: AI role-play with coaching pauses, video analysis, framework practice

### Hybrid
Two or more types are equally important and intertwined.
- Examples: pharmacy informatics (cognitive + technical), conducting (motor + perceptual + social)
- Key indicator: Removing any one type would fundamentally change the skill
- Teaching implication: Alternate between type-specific approaches across sessions

## Environment Type Assessment

Assess based on feedback quality, not difficulty:

| Environment | Feedback | Examples |
|---|---|---|
| Kind | Fast, accurate, unambiguous | Chess puzzles, math, coding with tests |
| Mostly Kind | Generally reliable with some noise | Cooking (taste is subjective), most sports |
| Mixed | Reliable in some areas, noisy in others | Business strategy, teaching, investing |
| Mostly Wicked | Delayed, ambiguous, or misleading | Hiring, long-term health decisions |
| Wicked | Very delayed or systematically misleading | Political forecasting, some medical diagnoses |

## Bloom's Ceiling

Match to the learner's stated goal, not the domain's maximum:

- "I want to recognize X" → Remember
- "I want to understand how X works" → Understand
- "I want to be able to do X" → Apply
- "I want to figure out why X happens" → Analyze
- "I want to judge whether X is good" → Evaluate
- "I want to design/build/compose X" → Create
```

- [ ] **Step 2: Create routing-flowchart.md**

```markdown
# Orchestrator Routing Logic

## Pipeline Phase Detection

Check state files in this order to determine current phase:

```
1. Does learn-anything/active-skill.json exist?
   NO + learning intent → ONBOARDING: Route to Domain Assessor
   NO + no learning intent → Inform user about /learn command

2. Read active-skill.json → get <slug>
   Check learn-anything/<slug>/ for state files:

   Missing domain-assessment.json → Route to Domain Assessor
   Missing skill-dossier.json    → Route to Skill Researcher
   Missing knowledge-graph.json  → Route to Learner Calibrator
   Missing learning-plan.json    → Route to Curriculum Architect
   Missing srs-cards.json        → Route to Material Forge (full mode)
                                    Then → Dashboard Generator
                                    Then → LEARNING phase

3. All files present → LEARNING phase
   Training request    → Route to Training Conductor
   Progress request    → Route to Dashboard Generator
   Update request      → Route to update workflow (see Update Mode)
   Material request    → Route to Material Forge (on-demand mode)
```

## Schema Field Map

Which skill populates which fields:

| Schema File | Field | Producer Skill |
|---|---|---|
| domain-assessment | skill_classification | Domain Assessor |
| domain-assessment | learner_profile | Domain Assessor |
| domain-assessment | approach_strategy | Domain Assessor |
| domain-assessment | identity_frame | Domain Assessor |
| domain-assessment | teaching_preferences | Domain Assessor (Phase C) |
| skill-dossier | graph.vertices | Skill Researcher |
| skill-dossier | graph.edges | Skill Researcher |
| skill-dossier | frequency_analysis | Skill Researcher |
| skill-dossier | transfer_pathways | Skill Researcher |
| skill-dossier | failure_points | Skill Researcher |
| skill-dossier | research_sources | Skill Researcher |
| skill-dossier | freshness_assessment | Skill Researcher (Phase B) |
| skill-dossier | expert_panel | Skill Researcher (Phase C) |
| knowledge-graph | graph (with learner_state) | Learner Calibrator (initial), Training Conductor (updates) |
| knowledge-graph | gap_analysis | Learner Calibrator |
| learning-plan | curriculum | Curriculum Architect |
| learning-plan | schedule | Curriculum Architect |
| learning-plan | motivation_architecture | Curriculum Architect |
| srs-cards | decks, cards | Material Forge |
| progress | sessions, current_state | Training Conductor |

## Two-Conversation Onboarding Model

**Conversation 1: Assessment + Research**
- Domain Assessor: classify skill, gather learner profile (~15-20 min)
- Skill Researcher: deep investigation, dependency graph (~10-15 min with web search)
- Natural stopping point: "I've mapped out the skill. Next time we'll assess what you already know and design your curriculum."

**Conversation 2: Calibration + Plan + Materials + Dashboard**
- Learner Calibrator: diagnostic assessment (~15-20 questions)
- Curriculum Architect: design learning plan (with epitome refinement checkpoint)
- Material Forge: generate initial materials
- Dashboard Generator: create progress visualization
- Transition to LEARNING phase

## Calibration Loop

The Learner Calibrator may trigger re-research (max 2 iterations):
1. Calibrator detects unexpected expertise or gaps that change research priorities
2. Route back to Skill Researcher for targeted additional research
3. Researcher updates skill-dossier.json
4. Route back to Calibrator to re-assess against updated graph
5. Continue to Curriculum Architect only when Calibrator signals stability

## Handoff Protocol

When transitioning between skills:
1. Verify the outgoing skill's output file was written successfully
2. Orient the learner conversationally: brief summary of what was accomplished, what comes next
3. Do not repeat information the learner already provided
```

- [ ] **Step 3: Add references to SKILL.md files**

In domain-assessor SKILL.md, add to the Inputs section:
```markdown
- `references/classification-guide.md` — Decision trees for skill type, environment, and Bloom's ceiling classification
```

In orchestrator SKILL.md, add a References section after System Components:
```markdown
## References

- `references/routing-flowchart.md` — Detailed routing logic, schema field map, two-conversation model, calibration loop rules, and handoff protocol
```

- [ ] **Step 4: Commit**

```bash
git add learn-anything-plugin/skills/domain-assessor/references/classification-guide.md \
        learn-anything-plugin/skills/orchestrator/references/routing-flowchart.md \
        learn-anything-plugin/skills/domain-assessor/SKILL.md \
        learn-anything-plugin/skills/orchestrator/SKILL.md
git commit -m "docs: create reference files for domain-assessor and orchestrator

classification-guide.md: skill type decision tree, environment rubric, Bloom's ceiling
routing-flowchart.md: routing logic, schema field map, two-conversation model, handoffs"
```

---

### Task 10: Handoff Documentation

**Files:**
- Modify: All 7 non-orchestrator SKILL.md files

- [ ] **Step 1: Add Handoff section to each skill**

At the end of each skill's SKILL.md (after Key Rules or final section), add a Handoff section. The exact text for each:

**domain-assessor:**
```markdown
## Handoff

After writing domain-assessment.json, the Skill Researcher takes over. It reads the classification and learner profile to guide its decomposition research. Summarize for the learner: what was classified, the short-term plan, and that next comes skill research (which may involve web searches and take some time).
```

**skill-researcher:**
```markdown
## Handoff

After writing skill-dossier.json, the Learner Calibrator takes over. It reads the dependency graph and transfer pathways to design a diagnostic assessment. Summarize for the learner: the major component clusters found, key transfer pathways from their experience, and that next comes a conversational assessment of what they already know.
```

**learner-calibrator:**
```markdown
## Handoff

After writing knowledge-graph.json, the Curriculum Architect takes over. It reads the gap analysis to design the learning plan. Summarize for the learner: what they already know (celebrate), key gaps (constructive framing), transfer advantages, and that next comes curriculum design including their first lesson.
```

**curriculum-architect:**
```markdown
## Handoff

After writing learning-plan.json, the Material Forge takes over. It reads the curriculum to generate learning materials (worked examples, flashcards, assessments, visuals). Summarize for the learner: the epitome (first lesson), task class progression, schedule, and that materials generation is next.
```

**material-forge:**
```markdown
## Handoff

After writing srs-cards.json and materials/, the Dashboard Generator creates the progress visualization, then the system transitions to the LEARNING phase. Summarize for the learner: what materials were generated, how to import the Anki deck, and that training sessions are ready to begin.
```

**training-conductor:**
```markdown
## Handoff

At session end, write updated knowledge-graph.json and progress.json. The next invocation of Training Conductor (via /train or orchestrator) will read these files to plan the next session. Summarize for the learner: what was covered, mastery transitions, and the recommended next session focus.
```

**dashboard-generator:**
```markdown
## Handoff

After generating the React artifact, the system is ready for training sessions. No downstream skill consumes the dashboard — it is a terminal output for the learner's reference. The orchestrator routes subsequent requests to the Training Conductor.
```

- [ ] **Step 2: Commit**

```bash
git add learn-anything-plugin/skills/*/SKILL.md
git commit -m "docs: add Handoff section to all skills

Each skill now documents its downstream consumer and
provides guidance on learner-facing transition messaging."
```

---

### Task 11: README Updates

**Files:**
- Modify: `learn-anything-plugin/README.md`
- Modify: `README.md` (root)

- [ ] **Step 1: Update plugin README**

Update the Commands table to include the new commands (they'll be created in later phases but should be documented now with "(coming in v2.0)" notes):

In the Commands table, add rows:
```markdown
| `/materials [type] [task-class]` | Generate or regenerate learning materials *(v2.0)* |
| `/update [what changed]` | Update curriculum for evolving fields *(v2.0)* |
```

Update the Pipeline section's Training Conductor description to mention mentor mode:
```markdown
  Training Conductor
  (Socratic teaching, adaptive difficulty, mastery gates,
   spaced retrieval, plateau detection, progress tracking,
   instructor personas, mentor conversation mode)
```

Add a "What's New in v2.0" section after the Pipeline section:
```markdown
## What's New in v2.0

- **Conversational epitome refinement** — The Curriculum Architect now pauses to discuss your first lesson before building the full plan
- **Instructor personas** — Choose a teaching style inspired by masters of your field (e.g., Feynman for physics)
- **Mentor conversation mode** — Relaxed, exploratory discussions via `/train --mode mentor`
- **Session transcripts** — Full session logs saved to `transcripts/` for review
- **Curriculum updates** — `/update` command for evolving fields
- **Material generation** — `/materials` command for on-demand content
- **Improved research** — Ferriss interview protocol now mandatory, freshness detection for cutting-edge fields
- **Better visuals** — WCAG-compliant color contrast, inline SVG over Mermaid for learning materials
```

- [ ] **Step 2: Update root README**

Update the version reference and add the new commands to the command table. Keep the existing troubleshooting and structure sections.

- [ ] **Step 3: Commit**

```bash
git add learn-anything-plugin/README.md README.md
git commit -m "docs: update READMEs for v2.0

Add new commands, mentor mode, personas, transcripts to documentation.
Add What's New in v2.0 section."
```

---

### Task 12: Version Bump and Package

**Files:**
- Modify: `learn-anything-plugin/.claude-plugin/plugin.json`
- Modify: `.claude-plugin/marketplace.json`

- [ ] **Step 1: Bump plugin version**

In `learn-anything-plugin/.claude-plugin/plugin.json`, change:
```json
"version": "1.0.3"
```
to:
```json
"version": "2.0.0-alpha.1"
```

- [ ] **Step 2: Bump marketplace version**

In `.claude-plugin/marketplace.json`, change:
```json
"version": "1.0.3"
```
to:
```json
"version": "2.0.0-alpha.1"
```

- [ ] **Step 3: Rebuild zip**

```bash
cd /Users/johnroehm/Programming/Infrastructure/Plugin-Library/learn-anything
zip -r learn-anything-plugin.zip learn-anything-plugin/ -x "learn-anything-plugin/.git/*"
```

- [ ] **Step 4: Commit**

```bash
git add learn-anything-plugin/.claude-plugin/plugin.json \
        .claude-plugin/marketplace.json \
        learn-anything-plugin.zip
git commit -m "chore: bump version to 2.0.0-alpha.1 (Phase A complete)"
```

---

### Task 13: Phase A PR

- [ ] **Step 1: Push branch and create PR**

```bash
git push -u origin phase-a/code-quality
gh pr create --title "Phase A: Code Quality & Polish" --body "$(cat <<'EOF'
## Summary
- Normalize all 8 SKILL.md files to imperative voice
- Standardize frontmatter descriptions with third-person trigger phrases
- Close schema-process gaps (cognitive_load_type, cluster_id, assessment_criteria)
- Add input verification and output validation to all producer skills
- Create reference files for domain-assessor and orchestrator
- Add Handoff sections to all skills
- Update READMEs for v2.0
- Version bump to 2.0.0-alpha.1

## Test plan
- [ ] Grep all SKILL.md for second-person constructions — should be zero outside quotes
- [ ] Verify all frontmatter descriptions start with "This skill should be used when"
- [ ] Verify new reference files exist and are referenced from SKILL.md
- [ ] Run `claude plugin validate learn-anything-plugin/`
- [ ] Run `/learn` against one existing program to verify no regressions

Generated with [Claude Code](https://claude.com/claude-code)
EOF
)"
```

- [ ] **Step 2: After PR approval, merge**

```bash
gh pr merge --squash
git checkout main
git pull
```

---

## Phase B: Content Quality

**Branch:** `phase-b/content-quality`

### Task 14: Create feature branch

- [ ] **Step 1: Create branch from latest main**

```bash
git checkout main
git pull
git checkout -b phase-b/content-quality
```

---

### Task 15: Ferriss Interview Enforcement

**Files:**
- Modify: `learn-anything-plugin/skills/skill-researcher/SKILL.md`

- [ ] **Step 1: Rewrite Step 2 header and opening**

Find the Step 2 section and replace its header and opening instruction. Change from a suggestion to a requirement:

Replace:
```markdown
### Step 2: Simulated Expert Interviews
```
(or similar header)

With:
```markdown
### Step 2: Expert Interview Synthesis (REQUIRED — 6-12 web searches)

Read `references/expert-interview-protocol.md` before proceeding. This step is mandatory — execute ALL six Ferriss questions using the search strategies documented there.

For each of the 6 Ferriss questions:
1. Conduct at least one web search using the search patterns from the protocol
2. Document findings with source URLs
3. Synthesize across perspectives — where experts agree, note consensus; where they disagree, note the controversy

If a question produces zero findings after two search attempts, note it explicitly with `confidence: LOW` and record what was searched.
```

- [ ] **Step 2: Add interview validation checkpoint**

After Step 2, before Step 3, add:

```markdown
### Step 2 Validation Checkpoint

Before proceeding to component identification:
- Verify all 6 Ferriss questions produced at least one finding with a source URL
- Verify `research_sources` includes at least 3 entries with `type: "expert_interview"`
- If fewer than 3 expert_interview sources exist, the research phase is incomplete — conduct additional targeted searches

This checkpoint exists because the Ferriss interview protocol is frequently skipped, leading to decompositions that reflect LLM training data rather than real expert perspectives.
```

- [ ] **Step 3: Commit**

```bash
git add learn-anything-plugin/skills/skill-researcher/SKILL.md
git commit -m "fix(skill-researcher): make Ferriss interview protocol mandatory

Step 2 now requires reading expert-interview-protocol.md and executing
all 6 Ferriss questions with web search. Adds validation checkpoint
requiring minimum 3 expert_interview research sources."
```

---

### Task 16: Freshness Detection and Expert Panel

**Files:**
- Modify: `learn-anything-plugin/skills/skill-researcher/SKILL.md`
- Modify: `learn-anything-plugin/schemas/skill-dossier.schema.json`

- [ ] **Step 1: Add freshness detection to Step 1**

In the skill-researcher SKILL.md, in Step 1 (Landscape Mapping), add after the existing search guidance:

```markdown
#### Freshness Assessment

Assess field velocity during landscape mapping:
- Check for: release cadence, recent major version changes, active development blogs/changelogs, version numbers, "what's new" pages
- If the field has had significant changes within the last 6 months, flag as `HIGH_FRESHNESS_RISK` or `VERY_HIGH_FRESHNESS_RISK`
- For HIGH or VERY_HIGH freshness risk: double the web search budget, prioritize official documentation and creator content (blog posts, tutorials, changelogs, release notes) over general articles
- For technical/product skills: always search for official documentation, creator blogs, tutorials from the tool's authors, and recent conference talks — these are higher-signal than third-party articles for rapidly evolving tools

Record the assessment in the dossier output as `freshness_assessment`.
```

- [ ] **Step 2: Add expert panel discovery**

In Step 1 or Step 2, add:

```markdown
#### Expert Panel Discovery

During landscape mapping and expert interview synthesis, identify masters of the field — people who have driven the state of the art. For each, note:
- **name**: Full name
- **contribution**: What they're known for in this field
- **teaching_style**: Any known teaching approach or persona (e.g., "Feynman: intuitive, visual, playful explanations", "Knuth: rigorous, methodical, detail-oriented")
- **source_url**: Where this information was found

Store these in the `expert_panel` array in the dossier output. The Curriculum Architect will present these to the learner as potential instructor personas.

In almost all fields, there are recognized masters. Search for: "[field] greatest teachers", "[field] best instructors", "[field] pioneers", "[field] thought leaders". If the domain is too niche for recognizable teaching personas, note this — the downstream skill will fall back to asking the learner directly.
```

- [ ] **Step 3: Add freshness_assessment and expert_panel to schema**

In `schemas/skill-dossier.schema.json`, add these fields to the `properties` object at the root level (alongside `graph`, `frequency_analysis`, etc.):

```json
"freshness_assessment": {
  "type": "object",
  "properties": {
    "risk_level": {
      "type": "string",
      "enum": ["low", "medium", "high", "very_high"],
      "description": "How rapidly the field is evolving"
    },
    "last_major_change": {
      "type": "string",
      "description": "Date or description of most recent significant change"
    },
    "evolution_notes": {
      "type": "string",
      "description": "Notes on what's changing and how fast"
    }
  },
  "description": "Assessment of how rapidly this field is evolving — informs curriculum update frequency"
},

"expert_panel": {
  "type": "array",
  "items": {
    "type": "object",
    "required": ["name", "contribution"],
    "properties": {
      "name": { "type": "string" },
      "contribution": { "type": "string", "description": "What they're known for in this field" },
      "teaching_style": { "type": "string", "description": "Known teaching approach or persona, if applicable" },
      "source_url": { "type": "string" }
    }
  },
  "description": "Masters of the field identified during research — presented to learner as potential instructor personas"
}
```

- [ ] **Step 4: Commit**

```bash
git add learn-anything-plugin/skills/skill-researcher/SKILL.md \
        learn-anything-plugin/schemas/skill-dossier.schema.json
git commit -m "feat(skill-researcher): add freshness detection and expert panel discovery

Skill Researcher now assesses field velocity and identifies masters
of the field with teaching styles. Both stored in dossier for
downstream use by Curriculum Architect and Training Conductor."
```

---

### Task 17: Color Contrast Enforcement

**Files:**
- Modify: `learn-anything-plugin/skills/material-forge/references/card-design-guide.md`
- Modify: `learn-anything-plugin/skills/material-forge/references/quality-rubrics.md`
- Modify: `learn-anything-plugin/skills/material-forge/SKILL.md`

- [ ] **Step 1: Update card-design-guide.md color rules**

Find the existing color/SVG section in card-design-guide.md and replace the color palette with:

```markdown
### Mandatory Color Rules

These rules are non-negotiable. Light-on-light rendering is a critical defect that destroys credibility.

**Text colors:**
- ALL text elements: minimum #374151 (dark gray) or darker — NEVER lighter
- Labels, annotations, axis text: #1f2937 (near-black) preferred
- NEVER use light colors (#93c5fd, #86efac, #fde68a, #d1d5db, etc.) for text or lines

**Background colors:**
- ALL backgrounds: #ffffff (white) or #f9fafb (near-white)
- NEVER use dark backgrounds with dark text
- NEVER use colored backgrounds unless contrast ratio exceeds 4.5:1

**Shape colors:**
- Stroke colors for shapes: use the high-contrast palette — #2563eb (blue), #dc2626 (red), #16a34a (green), #9333ea (purple), #d97706 (amber), #374151 (dark gray)
- Fill colors for shapes: use 10-15% opacity versions of stroke colors (e.g., `fill="rgba(37,99,235,0.1)"` for light blue fill with #2563eb stroke)
- NEVER use a fill color as the only visual indicator — always pair with stroke or text

**Verification rule:** Before finalizing any SVG, verify no text or line element uses a color lighter than #6b7280 against a white/light background.
```

- [ ] **Step 2: Update quality-rubrics.md**

Find the SRS Flashcards visual quality section and add/replace with:

```markdown
**Visual Contrast Check (MANDATORY — check EVERY diagram):**
- No text element uses a color lighter than #6b7280 against a white/light background
- No text uses white or near-white (#f9fafb, #e5e7eb, etc.) against a light background
- No line or stroke element uses a color lighter than #9ca3af against white
- All fill+stroke combinations maintain WCAG 2.1 AA contrast ratio (minimum 4.5:1 for text, 3:1 for large text and graphical objects)
- SVG has `<title>` element for accessibility
- All text is minimum 12px at the rendered viewBox size
```

- [ ] **Step 3: Update material-forge SKILL.md**

Find the SRS generation section and add after the visual audit pass instruction:

```markdown
#### Color Contrast Enforcement

Before finalizing any SVG, run this check:
- Verify all text elements use colors darker than #6b7280 (minimum dark gray)
- Verify all line/stroke elements use colors from the approved high-contrast palette (#2563eb, #dc2626, #16a34a, #9333ea, #d97706, #374151)
- Verify no fill color is used as the sole visual indicator without accompanying stroke or text
- Light-on-light rendering is a critical defect — reject and regenerate any diagram that fails this check

Refer to `references/card-design-guide.md` for the complete color rules.
```

- [ ] **Step 4: Add Mermaid vs SVG guidance**

In material-forge SKILL.md, add to the Material Generation Process section:

```markdown
#### Visual Format Selection

- **Mermaid:** ONLY for dependency graph visualizations and curriculum roadmap overviews
- **Inline SVG:** For ALL flashcard diagrams, worked example illustrations, reference material visuals, and concept diagrams
- When a visual is needed for a flashcard (per the visual audit pass), generate inline SVG with the `image_svg` field. Do NOT substitute a Mermaid code block — Mermaid renders generically and cannot enforce the color contrast rules required for learning materials.
```

- [ ] **Step 5: Commit**

```bash
git add learn-anything-plugin/skills/material-forge/references/card-design-guide.md \
        learn-anything-plugin/skills/material-forge/references/quality-rubrics.md \
        learn-anything-plugin/skills/material-forge/SKILL.md
git commit -m "fix(material-forge): enforce WCAG color contrast, prefer SVG over Mermaid

Mandatory color rules: dark text on light backgrounds only.
Quality rubric now includes contrast verification checklist.
SVG preferred for all learning visuals; Mermaid only for dependency graphs."
```

---

### Task 18: Material Forge Subagent Architecture

**Files:**
- Modify: `learn-anything-plugin/skills/material-forge/SKILL.md`
- Create: `learn-anything-plugin/agents/visual-material-generator.md`
- Create: `learn-anything-plugin/agents/worked-example-generator.md`
- Create: `learn-anything-plugin/agents/flashcard-generator.md`
- Create: `learn-anything-plugin/agents/assessment-generator.md`

- [ ] **Step 1: Update material-forge SKILL.md generation architecture**

Replace the monolithic generation process with subagent orchestration. Find the "Material Generation Process" section and restructure:

```markdown
## Material Generation Architecture

Material Forge acts as an orchestrator, dispatching dedicated subagents for each material type. Each subagent has its own context window, detailed templates, and QA checks.

### Dispatch Protocol

1. Read the learning plan and knowledge graph
2. For each task class, determine which material types are needed
3. Dispatch subagents in priority order (most important first):
   - **worked-example-generator** — Worked examples with backward fading and detailed visuals (highest priority — these ARE the lessons)
   - **visual-material-generator** — Concept illustrations, process diagrams, reference visuals
   - **assessment-generator** — Mastery gate items, delayed retention tests, transfer tasks
   - **flashcard-generator** — SRS cards per card-design-guide.md
4. After all subagents complete, generate remaining materials directly:
   - Dependency graph visualization (Mermaid)
   - Interleaved practice sets
   - Productive failure scenarios
   - Encoding aids
   - Reference one-pagers
   - External resource lists

### Subagent Context

Each subagent receives:
- The relevant task class data from learning-plan.json
- Vertex details from knowledge-graph.json for the task class's vertices
- Learner context: teaching_preferences, related experience, constraints
- The applicable quality rubric section from references/quality-rubrics.md

### Per-Subagent QA

Each subagent runs its own quality check before returning results. Material Forge aggregates all outputs and does a final cross-check for:
- Completeness: all material types generated for all applicable task classes
- Consistency: terminology, vertex references, and difficulty levels align across materials
- Color contrast: spot-check SVG outputs against mandatory color rules

### Completeness Tracking

After all subagents complete, verify all material types were generated for all applicable task classes. List any gaps and report to the user. Offer to regenerate missing materials via `/materials`.
```

- [ ] **Step 2: Create visual-material-generator.md**

```bash
mkdir -p learn-anything-plugin/agents
```

Write to `learn-anything-plugin/agents/visual-material-generator.md`:

```markdown
---
name: visual-material-generator
description: "Use this agent to generate inline SVG visuals for learning materials: concept illustrations, process flow diagrams, comparison diagrams, layered architecture diagrams, timelines, and annotated figures. Dispatched by Material Forge for each task class. Enforces WCAG color contrast rules."
tools:
  - Read
  - Write
  - Grep
  - Glob
---

# Visual Material Generator

Generate inline SVG visuals for learning materials. Each visual should aid understanding of a specific concept or process from the curriculum.

## Inputs

Read from the dispatch context:
- Task class data: which vertices need visual treatment
- Vertex details: name, description, blooms_level, component_type
- Learner context: related experience (for analogy-based visuals)

Read the color rules from the Material Forge's card-design-guide:
- ALL text: minimum #374151 or darker
- ALL backgrounds: #ffffff or #f9fafb
- Stroke palette: #2563eb, #dc2626, #16a34a, #9333ea, #d97706, #374151
- Fill: 10-15% opacity of stroke colors

## Visual Templates

### Process Flow
For sequential processes (e.g., request lifecycle, compilation pipeline):
- Top-to-bottom or left-to-right flow
- Rounded rectangle nodes with short labels
- Directional arrows between steps
- Color-code stages by category using stroke palette
- Maximum 8 nodes per diagram; split into sub-diagrams if needed

### Comparison / Side-by-Side
For contrasting concepts (e.g., before/after, option A vs B):
- Two columns with aligned rows
- Shared labels on the left, divergent content in each column
- Use color to distinguish columns (e.g., blue vs green)

### Layered Architecture
For hierarchical systems (e.g., network stack, cache layers):
- Stacked rectangles with decreasing width (or equal width)
- Labels centered in each layer
- Arrows showing data flow direction
- Color gradient from top (lightest fill) to bottom (darkest fill)

### Timeline
For temporal sequences (e.g., learning progression, historical development):
- Horizontal line with marked points
- Labels above and below alternating
- Consistent spacing

### Annotated Concept
For single concepts needing visual explanation:
- Central element (shape, icon, or text)
- Annotation lines pointing to key aspects
- Brief label text at each annotation point

## Quality Checks

Before returning any SVG:
1. viewBox is set and width does not exceed 400px
2. All text colors are #374151 or darker
3. No fill color used as sole indicator without stroke
4. 8 or fewer labeled elements
5. `<title>` element present
6. No `<script>`, `on*` handlers, `javascript:` URIs, or `<foreignObject>` elements
7. Text is minimum 12px at rendered size

## Output

Write SVGs to the materials directory as standalone `.svg` files or embed in markdown documents. For flashcard integration, provide the SVG string for the `image_svg` field with `image_placement` recommendation.
```

- [ ] **Step 3: Create worked-example-generator.md**

Write to `learn-anything-plugin/agents/worked-example-generator.md`:

```markdown
---
name: worked-example-generator
description: "Use this agent to generate worked examples with backward fading sequences for learning materials. Creates full solutions, self-explanation prompts, and progressive fading versions. Dispatched by Material Forge for each task class."
tools:
  - Read
  - Write
  - Grep
  - Glob
---

# Worked Example Generator

Generate worked examples with backward fading for each task class. These are the core lesson materials — they demonstrate how to think through problems, not just what the answer is.

## Inputs

- Task class data: vertices, complexity level, support sequence
- Vertex details: name, description, blooms_level, assessment_criteria
- Learner context: related experience (for contextualized examples), teaching_preferences

## Generation Process

For each task class, generate a representative problem and solution:

### 1. Select a Representative Problem
- Choose a problem that exercises the core vertices of the task class
- Ensure it's at the appropriate Bloom's level
- Contextualize to the learner's background where possible

### 2. Write the Full Worked Solution
- Step-by-step solution with clear reasoning at each step
- Explain WHY each step works, not just WHAT to do
- Include self-explanation prompts: "Why does this step work?" "What would happen if we did X instead?"
- Use the instructor persona style if teaching_preferences.instructor_persona is set

### 3. Create Backward Fading Sequence
Generate 3-4 versions with progressive fading (remove last step first):
- **Version 1 (Worked Example):** Complete solution with all steps shown
- **Version 2 (Completion):** Last 1-2 steps removed — learner completes them
- **Version 3 (Guided):** Only first 1-2 steps shown, hints for the rest
- **Version 4 (Independent):** Problem statement only, no steps shown

### 4. Vary Surface Features
Across versions, change surface features (different numbers, scenarios, contexts) while keeping the deep structure identical. This prevents pattern matching and promotes transfer.

### Fading Pace Calibration
Adjust based on learner mastery from knowledge graph:
- Not started / attempted: 1 step removed per 2 problems (slow fading)
- Familiar: 1 step per problem (standard)
- Proficient: 2 steps per problem (fast fading)

## Quality Checks

Before returning:
1. Full solution is complete and correct
2. Self-explanation prompts are present at key decision points
3. Fading sequence removes steps from the END first (backward fading)
4. Surface features vary across versions
5. Difficulty matches task class complexity level

## Output

Write worked examples as markdown files to `materials/worked-examples/`:
- `tc<N>-worked-examples.md` — All versions for the task class
```

- [ ] **Step 4: Create flashcard-generator.md**

Write to `learn-anything-plugin/agents/flashcard-generator.md`:

```markdown
---
name: flashcard-generator
description: "Use this agent to generate SRS flashcard decks conforming to srs-cards.schema.json. Applies card design principles, anti-pattern rejection, visual audit, and color contrast enforcement. Dispatched by Material Forge."
tools:
  - Read
  - Write
  - Grep
  - Glob
  - Bash
---

# Flashcard Generator

Generate SRS flashcard decks for each task class conforming to `schemas/srs-cards.schema.json`.

## Inputs

- Task class data: vertices to cover, curriculum_position
- Vertex details from knowledge graph
- Read `references/card-design-guide.md` for design principles and anti-patterns
- Read `references/quality-rubrics.md` for the SRS Flashcards quality section

## Generation Process

For each task class:

### 1. Identify Vertices
List all vertices assigned to this task class from the learning plan.

### 2. Generate Cards Per Vertex
Apply the card type selection table from card-design-guide.md:
- Facts → Basic Q&A (2-4 cards)
- Terms in context → Cloze (1-2 cards)
- Vocabulary → Reversed (1-2 cards)
- Procedures → Ordered cloze (3-5 cards)
- Concept relationships → Comparison (1-2 cards)
- Principles → Open-ended (1-2 cards)
- Spatial/structural concepts → Visual cards with SVG (1-2 cards)

### 3. Anti-Pattern Check
Reject and regenerate any card matching these anti-patterns:
- **Kitchen Sink:** Card tests multiple concepts
- **Ambiguous Cloze:** Deleted text could be multiple valid answers
- **Yes/No:** Binary question with no reasoning
- **Shopping List:** Card is just a list to memorize
- **Pattern Matching:** Answer derivable from card structure, not knowledge

### 4. Visual Audit Pass
For each card, ask: "Does this concept have a spatial, sequential, comparative, or structural dimension that a diagram would clarify?" If yes, generate inline SVG using the color rules from card-design-guide.md and set the `image_svg` field.

### 5. Tagging
Each card gets:
- `component_id`: vertex ID from knowledge graph
- `topic_tags`: hierarchical with `::` separator (e.g., `Python::Data Structures::Lists`)
- `bloom_level`: from vertex
- `knowledge_type`: fact/concept/procedure/principle/mental_model
- `difficulty_estimate`: 0.0-1.0
- `curriculum_position`: from task class sequence

## Quality Checks

Before returning the deck:
1. All 5 Matuschak principles: Focused, Precise, Consistent, Tractable, Effortful
2. Zero anti-pattern cards
3. All component_ids reference valid knowledge graph vertices
4. All visual cards pass color contrast rules
5. Card count per vertex is within range (2-5)

## Output

Write to `srs-cards.json` conforming to schema. Include `anki_config` with deterministic IDs. Then run the Anki export:

```bash
python learn-anything-plugin/skills/material-forge/scripts/generate_anki.py <srs-cards.json> [output.apkg]
```
```

- [ ] **Step 5: Create assessment-generator.md**

Write to `learn-anything-plugin/agents/assessment-generator.md`:

```markdown
---
name: assessment-generator
description: "Use this agent to generate assessment instruments: mastery gate items, delayed retention tests, and transfer tasks. Dispatched by Material Forge for each task class."
tools:
  - Read
  - Write
  - Grep
  - Glob
---

# Assessment Generator

Generate assessment instruments for mastery gates, delayed retention checks, and transfer tasks.

## Inputs

- Task class data: mastery_gate criteria, vertex_ids, bloom_level_required
- Vertex details from knowledge graph
- Read `references/quality-rubrics.md` for assessment quality criteria
- Read `../training-conductor/references/assessment-types.md` for assessment type specifications

## Assessment Types

### Mastery Gate Items (at task class boundaries)

Generate 3-5 items per mastery gate. Each gate requires three types:
1. **Cold recall:** Open-ended retrieval without cues
2. **Application under novelty:** Apply concept to a new context not seen in instruction
3. **Explain-to-teach:** Explain the concept as if teaching someone else

**Thresholds by Bloom's level:**
- Remember: 90-95% accuracy (3-5 items)
- Understand: 85-90% rubric score (3-5 items)
- Apply: 85% accuracy (3+ varied items)
- Analyze: 80% rubric score (3+ cases)
- Evaluate: 75-80% rubric score (2-3 items)
- Create: Holistic rubric (portfolio)

### Delayed Retention Tests

Generate items for 3 time points: 1-3 days, 7-14 days, 30+ days post-mastery.
- No hints or scaffolding
- Different surface features from instruction (same deep structure)
- Open-ended format requiring generation, not recognition

### Transfer Tasks

Generate near-transfer and far-transfer items:
- **Near transfer:** Same principle, different context within the domain
- **Far transfer:** Same principle, different domain entirely

## Anti-Gaming Design

All assessment items must:
- Be open-ended (no multiple choice unless domain-appropriate)
- Require explanation of reasoning, not just the answer
- Use procedurally varied surface features
- Not be predictable from instruction sequence

## Quality Checks

1. Bloom's level alignment: items test at or above the required level
2. Surface features varied from instruction materials
3. Explicit scoring rubric for each item
4. Minimum 3 items per assessed component
5. Anti-gaming: requires genuine understanding, not pattern matching

## Output

Write assessment instruments as JSON to `materials/assessments/`:
- `tc<N>-mastery-gate.json`
- `delayed-retention-tests.json`
- `transfer-tasks.json`
```

- [ ] **Step 6: Commit**

```bash
git add learn-anything-plugin/skills/material-forge/SKILL.md \
        learn-anything-plugin/agents/visual-material-generator.md \
        learn-anything-plugin/agents/worked-example-generator.md \
        learn-anything-plugin/agents/flashcard-generator.md \
        learn-anything-plugin/agents/assessment-generator.md
git commit -m "feat(material-forge): subagent architecture for material generation

Material Forge now dispatches dedicated subagents for visual materials,
worked examples, flashcards, and assessments. Each has its own context
window, templates, and QA checks. Worked examples and visuals prioritized
over flashcards."
```

---

### Task 19: /materials Command

**Files:**
- Create: `learn-anything-plugin/commands/materials.md`

- [ ] **Step 1: Create materials command**

```markdown
---
description: "Generate or regenerate learning materials for the active skill"
argument-hint: "[type] [task-class]"
---

The user has invoked `/materials` with: `$ARGUMENTS`

Read `learn-anything/active-skill.json` to find the active skill slug.

If no active skill exists, tell the user to start with `/learn <topic>` first.

If an active skill exists, read `learn-anything/<slug>/learning-plan.json` to determine the curriculum structure.

**Parse arguments:**
- If no arguments: generate all missing material types for all task classes
- If a type is specified: generate only that type. Valid types: `worked-examples`, `visuals`, `flashcards`, `assessments`, `practice-sets`, `references`, `encoding-aids`, `all`
- If a task class is specified (e.g., `tc1`, `tc2`): generate only for that task class
- Examples: `/materials flashcards tc2`, `/materials all`, `/materials visuals`

**Determine what exists vs what's missing:**
- Check `learn-anything/<slug>/materials/` for existing files
- Check `learn-anything/<slug>/srs-cards.json` for existing flashcards
- Report: "You have [X] of [Y] material types for [N] task classes. Missing: [list]"

Invoke the `material-forge` skill with the appropriate scope (full or targeted generation).
```

- [ ] **Step 2: Commit**

```bash
git add learn-anything-plugin/commands/materials.md
git commit -m "feat: add /materials command for ad-hoc material generation

Supports targeted generation by type and task class,
or full generation of all missing materials."
```

---

### Task 20: Phase B Version Bump and PR

- [ ] **Step 1: Bump version**

Update `plugin.json` to `2.0.0-alpha.2`, `marketplace.json` to match.

- [ ] **Step 2: Rebuild zip, commit, push, PR**

```bash
cd /Users/johnroehm/Programming/Infrastructure/Plugin-Library/learn-anything
zip -r learn-anything-plugin.zip learn-anything-plugin/ -x "learn-anything-plugin/.git/*"
git add learn-anything-plugin/.claude-plugin/plugin.json \
        .claude-plugin/marketplace.json \
        learn-anything-plugin.zip
git commit -m "chore: bump version to 2.0.0-alpha.2 (Phase B complete)"
git push -u origin phase-b/content-quality
gh pr create --title "Phase B: Content Quality" --body "$(cat <<'EOF'
## Summary
- Ferriss interview protocol now mandatory with validation checkpoint
- Freshness detection for cutting-edge fields
- Expert panel discovery for instructor personas
- WCAG color contrast enforcement for all SVG visuals
- SVG preferred over Mermaid for learning materials
- Material Forge subagent architecture (4 dedicated agents)
- /materials command for ad-hoc generation

## Test plan
- [ ] Run /learn on a new topic — verify Ferriss interview executes (research_sources should contain expert_interview entries)
- [ ] Run /learn on a cutting-edge topic — verify freshness_assessment populated
- [ ] Run /materials — verify subagents dispatch and generate materials
- [ ] Inspect generated SVGs for color contrast compliance
- [ ] Run `claude plugin validate learn-anything-plugin/`

Generated with [Claude Code](https://claude.com/claude-code)
EOF
)"
```

- [ ] **Step 3: After approval, merge**

```bash
gh pr merge --squash
git checkout main && git pull
```

---

## Phase C: Learner Experience

**Branch:** `phase-c/learner-experience`

### Task 21: Create feature branch

- [ ] **Step 1:**

```bash
git checkout main && git pull
git checkout -b phase-c/learner-experience
```

---

### Task 22: Conversational Epitome Refinement

**Files:**
- Modify: `learn-anything-plugin/skills/curriculum-architect/SKILL.md`

- [ ] **Step 1: Split Step 2a into two sub-steps**

Find Step 2a (Design the Epitome) in curriculum-architect SKILL.md. Replace the single step with:

```markdown
### Step 2a: Design and Refine the Epitome

#### 2a-i. Draft Epitome Internally

Design the epitome following the rules in `references/4cid-encoding.md`: a simplified but complete first lesson that exercises the full skill loop at reduced complexity. If the skill allows multiple valid starting points, identify 2-3 candidate epitome designs.

The epitome should:
- Connect directly to the learner's stated goals and purpose (from domain-assessment.json)
- Leverage the learner's existing knowledge (from knowledge-graph.json transfer_leverage)
- Produce a meaningful, tangible output the learner can point to after the first session

#### 2a-ii. Present and Refine with the Learner (CONVERSATIONAL CHECKPOINT)

Present the proposed epitome to the learner with clear reasoning:
- "Based on your goals and what the research found, here's what I'd suggest for your first lesson: [epitome description]"
- Explain WHY this epitome was chosen: what makes it representative, how it connects to the learner's stated goals, what they'll be able to do after completing it
- Explicitly ask: "Does this feel like the right starting point? Is there something more important to you that should come first?"

If the learner suggests changes:
- Refine the epitome. This may require adjusting which vertices are included, the complexity level, or the framing.
- If the learner's desired starting point conflicts with prerequisite structure, explain the dependency constructively: "I can see why X is exciting — to get there solidly, we'd want to cover Y first, which typically takes N sessions. Would you like to start with Y framed around getting to X?"

**Never override the learner's priorities without explanation.** The epitome should feel like THEIR starting point, not an imposed one.

Only proceed to Step 2b (Task Class Design) after the learner confirms the epitome direction.
```

- [ ] **Step 2: Commit**

```bash
git add learn-anything-plugin/skills/curriculum-architect/SKILL.md
git commit -m "feat(curriculum-architect): add conversational epitome refinement

Split epitome design into draft + learner checkpoint. Learner must
confirm the first lesson direction before curriculum proceeds."
```

---

### Task 23: Teaching Preferences Schema

**Files:**
- Modify: `learn-anything-plugin/schemas/domain-assessment.schema.json`

- [ ] **Step 1: Add teaching_preferences field**

In `domain-assessment.schema.json`, add `teaching_preferences` to the `properties` object (alongside `skill_classification`, `learner_profile`, etc.):

```json
"teaching_preferences": {
  "type": "object",
  "description": "How the learner wants to be taught — persists across sessions",
  "properties": {
    "instructor_persona": {
      "type": "string",
      "description": "Name or description of the teaching style/personality to adopt. Examples: 'Feynman — intuitive, visual, playful explanations', 'Strict academic — precise, formal, rigorous', 'Socratic coach — questions-first, minimal direct instruction'"
    },
    "instruction_before_assessment": {
      "type": "boolean",
      "default": false,
      "description": "If true, teach concepts before quizzing on them. If false (default), use Socratic/assessment-first approach."
    },
    "session_tone": {
      "type": "string",
      "enum": ["formal", "conversational", "playful", "mentoring"],
      "default": "conversational"
    },
    "preferences_notes": {
      "type": "string",
      "description": "Free-form notes on teaching preferences"
    }
  }
}
```

Do NOT add `teaching_preferences` to the `required` array — it's optional for backward compatibility.

- [ ] **Step 2: Commit**

```bash
git add learn-anything-plugin/schemas/domain-assessment.schema.json
git commit -m "feat(schema): add teaching_preferences to domain-assessment

Optional field for instructor persona, instruction-before-assessment
preference, session tone, and free-form notes. Backward compatible."
```

---

### Task 24: Teaching Preference Collection and Persona Adoption

**Files:**
- Modify: `learn-anything-plugin/skills/curriculum-architect/SKILL.md`
- Modify: `learn-anything-plugin/skills/training-conductor/SKILL.md`
- Modify: `learn-anything-plugin/skills/orchestrator/SKILL.md`

- [ ] **Step 1: Add expert panel presentation to curriculum-architect**

In curriculum-architect SKILL.md, before the epitome step (Step 2a), add:

```markdown
### Step 1b: Present Expert Panel and Gather Teaching Preferences

If `skill-dossier.json` contains an `expert_panel` array with entries:
- Present the panel to the learner: "The research identified these masters of [field]: [list names with teaching styles]. You can choose none, one, or several as your virtual panel of experts. Your instructor will adopt their teaching approach during sessions."
- Record the learner's choice in domain-assessment.json under `teaching_preferences.instructor_persona`

If `expert_panel` is empty or absent:
- Ask the learner directly: "Do you have a favorite teacher, author, or mentor whose style resonates with you? If not, what tone works best — formal and precise, casual and conversational, or playful and exploratory?"

If the learner has no preference:
- Default to a generic expert teacher persona for the domain

Also ask about instruction style:
- "Would you prefer to be taught concepts first, then tested on them? Or would you rather be challenged with questions and discover concepts through discussion?"
- Record in `teaching_preferences.instruction_before_assessment`

Write the updated `teaching_preferences` to domain-assessment.json.
```

- [ ] **Step 2: Add persona adoption to training-conductor**

In training-conductor SKILL.md, add to the Session Loading Protocol section:

```markdown
#### Teaching Preferences

Read `teaching_preferences` from domain-assessment.json:
- If `instructor_persona` is set, adopt that persona's teaching style throughout the session. If the persona is "Feynman", use intuitive analogies, thought experiments, and playful language. If "strict academic", use precise terminology and formal structure. The persona affects communication style, not pedagogical rigor — all teaching modes still use evidence-based scaffolding and adaptive difficulty.
- If `instruction_before_assessment` is true, restructure the opening to present concepts BEFORE retrieval probes. Use Template A (Concept Introduction) as the default opening rather than Template B (Retrieval Practice).
- If `session_tone` is set, calibrate formality level accordingly.

Maintain the instructor persona consistently throughout the session. Do not break character unless the learner asks you to change style.
```

- [ ] **Step 3: Add persona change routing to orchestrator**

In orchestrator SKILL.md, add to the Special Requests section:

```markdown
- **Change teaching style / Update persona:** Route to Domain Assessor to update `teaching_preferences` in domain-assessment.json. If the skill dossier has an expert_panel, present it again for selection. Otherwise, ask directly about preferences. The change takes effect at the next training session.
```

- [ ] **Step 4: Commit**

```bash
git add learn-anything-plugin/skills/curriculum-architect/SKILL.md \
        learn-anything-plugin/skills/training-conductor/SKILL.md \
        learn-anything-plugin/skills/orchestrator/SKILL.md
git commit -m "feat: teaching preferences and instructor persona system

Curriculum Architect presents expert panel from research for persona selection.
Training Conductor adopts chosen persona and respects instruction-before-assessment.
Orchestrator routes persona change requests."
```

---

### Task 25: Mentor Conversation Mode

**Files:**
- Modify: `learn-anything-plugin/skills/training-conductor/references/session-templates.md`
- Modify: `learn-anything-plugin/skills/training-conductor/SKILL.md`
- Modify: `learn-anything-plugin/commands/train.md`

- [ ] **Step 1: Add Template F to session-templates.md**

At the end of the existing templates (after Template E), add:

```markdown
## Template F: Mentor Conversation (~8,000 tokens)

**Purpose:** Relaxed, exploratory discussion following learner interest. Invisible passive assessment.

**When to use:** User requests "let's just talk about [topic]", "mentor mode", "exploration mode", or invokes `/train --mode mentor`. Also appropriate when the learner seems burned out on structured sessions or wants to explore tangentially.

**Phase structure:**

### Opening (5%)
- "What's on your mind about [skill]?" or follow up on something from the last session
- No retrieval probes — this is not an assessment opening
- If instructor_persona is set, this should feel like settling into a conversation with that person

### Exploration (80%)
- Follow the learner's curiosity wherever it leads
- Use the dependency graph internally to identify when the conversation touches on assessable vertices, but DO NOT turn it into a quiz
- Ask genuine follow-up questions that deepen understanding: "What makes you think that?", "How does that connect to [related concept]?", "Have you seen that come up in your own work?"
- Gently steer toward adjacent topics that connect to curriculum gaps when natural opportunities arise, but never force a topic change
- Share relevant stories, analogies, and thought experiments in the persona's style
- If the learner asks a direct question, answer it fully — this is not a Socratic session

### Passive Assessment (invisible, throughout)
- When the learner demonstrates understanding of a vertex during natural conversation, note it internally
- When misconceptions surface, address them naturally within the conversation flow — don't flag them as "misconception detected"
- Track which vertices were touched and the quality of the learner's engagement with each

### Closing (15%)
- Brief synthesis: "We covered some interesting ground today — [summary of topics explored]"
- Note any insights: "I noticed you have a strong intuition about [X] — that's going to serve you well when we get to [Y]"
- If misconceptions were observed, plant seeds for correction without being heavy-handed: "One thing worth thinking about before next time is [gentle reframe]"
- Preview what's coming: "When you're ready for a focused session, we could dig into [curriculum gap that connects to today's discussion]"

### Assessment Protocol (session end)
- Update knowledge graph vertices that were naturally touched during conversation
- Use `evidence_source: "mentor_conversation"` to distinguish from formal assessment
- Apply 0.6x confidence weight compared to direct assessment (informal observations carry less certainty)
- For misconceptions observed but not fully corrected, flag the vertex for revisiting in the next structured session

### Key Principles
- The learner should never feel like they're being assessed during this mode
- This mode should feel most natural when an instructor_persona is set — like having coffee with the mentor
- Passive assessment stays invisible unless the learner explicitly asks "how am I doing?"
- A good teacher forms impressions during casual conversation — useful signal, but lower confidence than formal assessment
```

- [ ] **Step 2: Add Template F to training-conductor SKILL.md**

In the session template selection logic, add:

```markdown
- **Template F (Mentor Conversation):** If the learner asks for exploration, discussion, "let's just talk about" the topic, or uses `--mode mentor`. Also consider when the learner seems fatigued with structured sessions (declining engagement over 2+ sessions) — offer mentor mode as an alternative.
```

- [ ] **Step 3: Update train.md command**

Replace the existing train.md content with:

```markdown
---
description: "Jump straight into a training session for your active skill."
argument-hint: "[optional context or --mode mentor]"
---

The user has invoked `/train` with: `$ARGUMENTS`

Read `learn-anything/active-skill.json` to find the active skill slug.

If no active skill exists, tell the user to start with `/learn <topic>` first.

If an active skill exists, invoke the `training-conductor` skill directly. Pass the user's arguments as session context.

If arguments contain `--mode mentor` or `mentor mode`, instruct the Training Conductor to use Template F (Mentor Conversation) for this session.

Examples:
- `/train` → standard session based on next agenda
- `/train I'm stuck on chord transitions` → focused session on specific topic
- `/train --mode mentor` → relaxed exploratory discussion
- `/train mentor mode` → same as above
```

- [ ] **Step 4: Commit**

```bash
git add learn-anything-plugin/skills/training-conductor/references/session-templates.md \
        learn-anything-plugin/skills/training-conductor/SKILL.md \
        learn-anything-plugin/commands/train.md
git commit -m "feat: add Template F mentor conversation mode

Relaxed exploratory discussion with invisible passive assessment.
Activated via /train --mode mentor or natural language request.
0.6x confidence weight for informal observations."
```

---

### Task 26: Phase C Version Bump and PR

- [ ] **Step 1: Bump version**

In `learn-anything-plugin/.claude-plugin/plugin.json`, change version to `"2.0.0-alpha.3"`.
In `.claude-plugin/marketplace.json`, change version to `"2.0.0-alpha.3"`.

- [ ] **Step 2: Rebuild zip and commit**

```bash
cd /Users/johnroehm/Programming/Infrastructure/Plugin-Library/learn-anything
zip -r learn-anything-plugin.zip learn-anything-plugin/ -x "learn-anything-plugin/.git/*"
git add learn-anything-plugin/.claude-plugin/plugin.json \
        .claude-plugin/marketplace.json \
        learn-anything-plugin.zip
git commit -m "chore: bump version to 2.0.0-alpha.3 (Phase C complete)"
```

- [ ] **Step 3: Push and create PR**

```bash
git push -u origin phase-c/learner-experience
gh pr create --title "Phase C: Learner Experience" --body "$(cat <<'EOF'
## Summary
- Conversational epitome refinement with learner checkpoint
- Teaching preferences schema (instructor persona, tone, instruction style)
- Expert panel presentation from Skill Researcher output
- Training Conductor persona adoption
- Template F: Mentor Conversation mode
- /train --mode mentor support

## Test plan
- [ ] Run /learn on new topic — verify epitome checkpoint pauses for user confirmation
- [ ] Verify teaching_preferences written to domain-assessment.json
- [ ] Run /train — verify instructor persona adopted
- [ ] Run /train --mode mentor — verify Template F activates
- [ ] Run `claude plugin validate learn-anything-plugin/`

Generated with [Claude Code](https://claude.com/claude-code)
EOF
)"
```

- [ ] **Step 4: After approval, merge**

```bash
gh pr merge --squash
git checkout main && git pull
```

---

## Phase D: Lifecycle & Data

**Branch:** `phase-d/lifecycle-data`

### Task 27: Create feature branch

- [ ] **Step 1:**

```bash
git checkout main && git pull
git checkout -b phase-d/lifecycle-data
```

---

### Task 28: Session Transcript Storage

**Files:**
- Modify: `learn-anything-plugin/skills/training-conductor/SKILL.md`
- Modify: `learn-anything-plugin/skills/orchestrator/SKILL.md`

- [ ] **Step 1: Add transcript creation to training-conductor**

In the Session Loading Protocol section, add:

```markdown
#### Transcript Initialization

Create a transcript file at `learn-anything/<skill-slug>/transcripts/session-<N>-<YYYY-MM-DD>.md` where `<N>` is the session number (from progress.json session count + 1). Create the `transcripts/` directory if it doesn't exist.

Initialize with:
```markdown
# Session <N> — <YYYY-MM-DD>
## Session Metadata
- Skill: <skill-name>
- Template: <selected-template>
- Instructor Persona: <persona or "default">
- Difficulty Zone: <starting-zone>
```

```

- [ ] **Step 2: Add transcript writing to session flow**

In the session flow architecture section, add:

```markdown
#### Transcript Writing

As the session progresses, periodically append to the transcript file in two layers:

**Layer 1 — Verbatim Exchanges:**
For each significant exchange, append:
```markdown
### Topic: <vertex-name>
**Instructor:** <full question or teaching point>
**Learner:** <full response>
**Assessment:** <observation, mastery implication>
```

**Layer 2 — Teaching Decisions:**
When making difficulty adjustments, template switches, or scaffolding changes, note them inline:
```markdown
> *[Teaching note: Shifted from Template C to Template A — learner struggling with prerequisite concept]*
```

Write to the transcript at natural breakpoints (topic transitions, after assessment observations) rather than after every single exchange.
```

- [ ] **Step 3: Add session debrief to closing**

In the session closing section, add:

```markdown
#### Finalize Transcript

Append the Session Debrief to the transcript file:

```markdown
## Session Debrief
### What Went Well
- <specific moments, breakthroughs, strong responses>

### What Went Poorly
- <confusion points, misconceptions, pacing issues>

### Areas for Improvement
- <teaching approach adjustments, content gaps identified>

### Mastery Transitions
- <vertex-name>: <from_state> → <to_state>

### Next Session Recommendations
- <recommended agenda, topics to revisit, new content to introduce>
```

Update the Session Metadata with final values:
- Duration: <actual-minutes>
- Difficulty Zone: <start> → <end>
```

- [ ] **Step 4: Add transcript access to orchestrator**

In orchestrator SKILL.md, add to Special Requests:

```markdown
- **Review session notes / Show transcript:** Read the most recent transcript from `learn-anything/<skill-slug>/transcripts/`. If the user asks for a specific session, read that session's transcript. Summarize key takeaways if requested.
```

- [ ] **Step 5: Commit**

```bash
git add learn-anything-plugin/skills/training-conductor/SKILL.md \
        learn-anything-plugin/skills/orchestrator/SKILL.md
git commit -m "feat: session transcript storage

Training Conductor now writes verbatim transcripts with assessment
annotations and session debrief to transcripts/ directory.
Orchestrator can surface transcripts on request."
```

---

### Task 29: Curriculum Update Workflow

**Files:**
- Create: `learn-anything-plugin/commands/update.md`
- Modify: `learn-anything-plugin/skills/orchestrator/SKILL.md`
- Modify: `learn-anything-plugin/skills/skill-researcher/SKILL.md`
- Modify: `learn-anything-plugin/skills/curriculum-architect/SKILL.md`

- [ ] **Step 1: Create update command**

Write to `learn-anything-plugin/commands/update.md`:

```markdown
---
description: "Update an existing curriculum to reflect new developments in the field"
argument-hint: "[what changed or 'full refresh']"
---

The user has invoked `/update` with: `$ARGUMENTS`

Read `learn-anything/active-skill.json` to find the active skill slug.

If no active skill exists, tell the user to start with `/learn <topic>` first.

If an active skill exists:

1. Read `learn-anything/<slug>/domain-assessment.json` for context
2. Read `learn-anything/<slug>/skill-dossier.json` for current state (check `freshness_assessment` if present)

3. **Archive current state:** Copy all state files (domain-assessment.json, skill-dossier.json, knowledge-graph.json, learning-plan.json, srs-cards.json) to `learn-anything/<slug>/archive/<YYYY-MM-DD>/`

4. **Determine update scope:**
   - If arguments contain "full refresh": invoke full re-research
   - Otherwise: invoke targeted update with the user's description of what changed

5. **Route the update cascade:**
   - Invoke `skill-researcher` skill with update mode directive and the user's description
   - After dossier update, invoke `learner-calibrator` to re-assess new/changed vertices only
   - After calibration, invoke `curriculum-architect` with update mode to re-sequence
   - Ask user if they want new materials generated for updated content

The update workflow is entirely user-initiated. Freshness assessment from the dossier serves as a guide for the user, not an automatic trigger.
```

- [ ] **Step 2: Add update mode to skill-researcher**

In skill-researcher SKILL.md, add a new section:

```markdown
## Update Mode

When invoked for a curriculum update (not initial research), follow a modified process:

1. Read the existing `skill-dossier.json` first
2. Read the update directive (what changed, from the user)
3. Conduct targeted web research focused on the changes described
4. Compare findings against the existing graph:
   - **New components:** Add as new vertices with appropriate edges
   - **Changed components:** Update existing vertex descriptions, scores, and connections
   - **Deprecated components:** Mark vertices with a note in the description (do not delete — the learner may have progress on them)
5. Update `freshness_assessment` with current date and findings
6. Write the delta summary for the user: what was added, changed, and deprecated

Preserve all existing vertex IDs — changing IDs would break knowledge graph references. Add new IDs for new components.
```

- [ ] **Step 3: Add update mode to learner-calibrator**

In learner-calibrator SKILL.md, add:

```markdown
## Update Mode

When invoked for a curriculum update (not initial calibration):

1. Read the updated skill-dossier.json and identify new or changed vertices (compare vertex IDs against the existing knowledge-graph.json)
2. Only assess new/changed vertices — do not re-assess vertices with existing mastery data unless they were significantly restructured
3. For new vertices: run the standard diagnostic assessment but limit to the new content (2-5 questions, not the full 15-20)
4. For changed vertices: check if the change affects the learner's existing mastery estimate. If the vertex description changed substantially, probe with 1-2 questions.
5. Update knowledge-graph.json with new vertex states. Preserve all existing mastery data for unchanged vertices.
6. Recompute gap_analysis with the updated graph
```

- [ ] **Step 4: Add update mode to curriculum-architect**

In curriculum-architect SKILL.md, add:

```markdown
## Update Mode

When invoked for a curriculum update (not initial design):

1. Read the updated skill-dossier.json and knowledge-graph.json
2. Preserve completed task classes and the learner's progress — do not re-sequence work already done
3. Insert new content into the appropriate task class based on complexity and prerequisites
4. If new content changes the prerequisite structure significantly, create a new task class rather than disrupting existing ones
5. Update the schedule to reflect new content
6. Present changes to the learner: what was added/changed, how it affects their plan, estimated additional time
```

- [ ] **Step 4: Add update routing to orchestrator**

In orchestrator SKILL.md, add to the routing logic:

```markdown
### Update Routing

Detect update intent when: user mentions "things have changed", "new version", "update curriculum", "refresh", "field has evolved", or uses `/update` command.

Route through the update cascade:
1. Skill Researcher (update mode) → updated skill-dossier.json
2. Learner Calibrator → re-assess new/changed vertices only
3. Curriculum Architect (update mode) → re-sequenced learning-plan.json
4. Optionally Material Forge → new materials for updated content
```

- [ ] **Step 6: Commit**

```bash
git add learn-anything-plugin/commands/update.md \
        learn-anything-plugin/skills/orchestrator/SKILL.md \
        learn-anything-plugin/skills/skill-researcher/SKILL.md \
        learn-anything-plugin/skills/learner-calibrator/SKILL.md \
        learn-anything-plugin/skills/curriculum-architect/SKILL.md
git commit -m "feat: curriculum update workflow

/update command with targeted and full-refresh modes.
Skill Researcher, Learner Calibrator, and Curriculum Architect
support update mode. State file archiving before updates."
```

---

### Task 30: Phase D Version Bump and Final PR

- [ ] **Step 1: Bump to 2.0.0, rebuild zip, commit**

Update `plugin.json` to `"version": "2.0.0"`, `marketplace.json` to match.

```bash
cd /Users/johnroehm/Programming/Infrastructure/Plugin-Library/learn-anything
zip -r learn-anything-plugin.zip learn-anything-plugin/ -x "learn-anything-plugin/.git/*"
git add learn-anything-plugin/.claude-plugin/plugin.json \
        .claude-plugin/marketplace.json \
        learn-anything-plugin.zip
git commit -m "chore: release version 2.0.0"
```

- [ ] **Step 2: Push and create PR**

```bash
git push -u origin phase-d/lifecycle-data
gh pr create --title "Phase D: Lifecycle & Data" --body "$(cat <<'EOF'
## Summary
- Session transcript storage (verbatim + debrief)
- /update command for curriculum updates (targeted + full refresh)
- Update mode for Skill Researcher and Curriculum Architect
- State file archiving before updates
- Version 2.0.0 release

## Test plan
- [ ] Run /train — verify transcript created in transcripts/ directory
- [ ] Verify transcript contains verbatim exchanges and session debrief
- [ ] Run /update with a description — verify update cascade executes
- [ ] Verify state files archived before update
- [ ] Run `claude plugin validate learn-anything-plugin/`
- [ ] Full regression: /learn new topic through first training session

Generated with [Claude Code](https://claude.com/claude-code)
EOF
)"
```

- [ ] **Step 3: After approval, merge and tag**

```bash
gh pr merge --squash
git checkout main && git pull
git tag v2.0.0
git push --tags
```

---

## Post-Implementation Checklist

- [ ] All 4 PRs merged to main
- [ ] Version is 2.0.0 in plugin.json and marketplace.json
- [ ] learn-anything-plugin.zip rebuilt from final state
- [ ] `claude plugin validate learn-anything-plugin/` passes
- [ ] Manual test: `/learn` new topic through full onboarding pipeline
- [ ] Manual test: `/train` standard session with existing program
- [ ] Manual test: `/train --mode mentor` mentor conversation
- [ ] Manual test: `/materials flashcards` ad-hoc generation
- [ ] Manual test: `/update` curriculum update
- [ ] Verify session transcript written after training session
- [ ] Verify teaching preferences persisted and adopted across sessions
- [ ] CLAUDE.md updated to reflect v2.0 changes
