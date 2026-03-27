# Learn-Anything Plugin v2.0 Comprehensive Update

**Date:** 2026-03-27
**Status:** Draft
**Version:** 1.0.3 → 2.0.0

## Executive Summary

This spec covers a four-phase update to the learn-anything plugin based on real-world testing across three domains (PWA, Claude Agent SDK, SK-EFT Hawking Physics) and a comprehensive code review. The phases are ordered by pipeline dependency — early pipeline fixes first, since they cascade through everything downstream.

**Implementation rule:** All work uses feature branches with PR+merge to main. No direct pushes.

---

## Problem Statement

The plugin produces deeply personalized curricula but requires significant real-time user intervention to get good results. Nine specific pain points were identified through testing:

1. Premature closure on epitome/lesson plan without conversational refinement
2. Knowledge mapping fails for cutting-edge fields; Ferriss interview simulation is skipped
3. No curriculum update workflow for evolving fields
4. Material Forge generates incomplete content; light-on-light color issues; defaults to Mermaid over detailed visuals
5. Learning style/instructor personality not captured or persisted
6. Session transcripts not saved
7. README is stale
8. No relaxed conversational mentor mode
9. Cross-cutting code quality issues (writing style, schema-process gaps, missing validation)

A baseline code review additionally identified: inconsistent imperative/second-person voice across 4/8 skills, empty reference directories, missing schema validation steps, handoff gaps between skills, and no worked examples in any skill.

---

## Phase Overview

| Phase | Theme | Pain Points | Pipeline Stage | Effort |
|-------|-------|-------------|----------------|--------|
| **A** | Code Quality & Polish | 9, 7 | All skills | Small-Medium |
| **B** | Content Quality | 2, 4 | Skill Researcher (early) + Material Forge (late) | Large |
| **C** | Learner Experience | 1, 5, 8 | Curriculum Architect (mid) + Training Conductor (late) | Medium-Large |
| **D** | Lifecycle & Data | 3, 6 | Orchestrator (cross-cutting) + Training Conductor | Medium |

---

## Phase A: Code Quality & Polish

**Goal:** Clean foundation — fix inconsistencies, close schema-process gaps, and update documentation so all subsequent work builds on solid ground.

**Branch:** `phase-a/code-quality`

### A1. Writing Style Normalization

**Problem:** 4 of 8 skills use second-person ("You are...", "Your job...") instead of imperative/infinitive form per plugin-dev best practices.

**Affected files:**
- `skills/orchestrator/SKILL.md` — Lines 8, 148+ use "you are", "you should"
- `skills/domain-assessor/SKILL.md` — Lines 8+ use "Your job is to..."
- `skills/material-forge/SKILL.md` — Inconsistent capitalization ("Material Forge" vs "material forge" vs "the Forge")
- `skills/skill-researcher/SKILL.md` — Minor instances ("You are the research engine...")

**Changes:**
- Rewrite all second-person constructions to imperative form
- Standardize capitalization of skill names across all files
- Preserve all functional content — this is a voice pass, not a content change

**Validation:** Grep for "You are", "Your job", "you should" across all SKILL.md files; count should be zero (excluding quoted learner-facing example messages).

### A2. Schema-Process Gap Closure

**Problem:** Several schema fields have no corresponding generation instructions in SKILL.md files.

**Gaps identified:**

| Schema Field | Schema File | Missing From |
|---|---|---|
| `cognitive_load_type` | skill-dossier.schema.json | skill-researcher SKILL.md |
| `embedding` | skill-dossier.schema.json | skill-researcher SKILL.md |
| `cluster_id` | skill-dossier.schema.json | skill-researcher SKILL.md |
| `assessment_criteria` | skill-dossier.schema.json | skill-researcher SKILL.md |

**Resolution strategy per field:**
- `cognitive_load_type`: Add instruction in skill-researcher Step 3 to classify each component as intrinsic/extraneous/germane
- `embedding`: Mark as optional/deferred in schema (not generateable in current architecture — no vector DB)
- `cluster_id`: Add instruction in skill-researcher Step 4 to assign cluster IDs based on semantic grouping during graph construction
- `assessment_criteria`: Add instruction in skill-researcher Step 3 to generate brief assessment criteria per component

**Changes:**
- Update skill-researcher SKILL.md with generation instructions for applicable fields
- Add `"description"` annotations to schema fields that are deferred/optional
- Document which fields are populated by which skill in a schema field map (add to orchestrator references)

### A3. Validation Steps

**Problem:** No skill instructs schema validation before writing JSON output. No error handling for malformed upstream state files.

**Changes (all 7 producer skills):**
- Add a "Validate Output" step before file write: "Verify the JSON output conforms to `schemas/<name>.schema.json`. Check all required fields are present and correctly typed."
- Add an "Input Verification" step at the start: "Verify upstream state files exist and contain required fields. If a file is missing or malformed, report the issue to the user rather than proceeding with partial data."

### A4. Empty Reference Directories

**Problem:** domain-assessor and orchestrator have no reference files despite being complex enough to benefit from them.

**Changes:**
- `skills/domain-assessor/references/classification-guide.md` — Decision tree for skill type classification (motor vs cognitive vs perceptual vs social vs hybrid), environment type assessment rubric, Bloom's ceiling determination. Extracted from inline SKILL.md content to keep SKILL.md lean.
- `skills/orchestrator/references/routing-flowchart.md` — Visual routing logic (which state files → which skill), handoff protocol details, calibration loop decision rules. Currently inline; move to reference for clarity.

### A5. Handoff Documentation

**Problem:** Skills don't consistently name their downstream consumer or explain the two-conversation onboarding model.

**Changes:**
- Each skill's SKILL.md gets a "Handoff" section at the end naming the downstream skill and what it expects
- Orchestrator SKILL.md gets explicit two-conversation model documentation with clear breakpoints

### A6. Frontmatter Description Standardization

**Problem:** Only the orchestrator uses the recommended "This skill should be used when..." trigger format.

**Changes:** Update all 7 non-orchestrator skill descriptions to use third-person format with specific trigger phrases per plugin-dev best practices.

### A7. README Update (Pain Point 7)

**Changes:**
- `learn-anything-plugin/README.md` — Update with current architecture, installation instructions, usage walkthrough (first session through ongoing training), slash command reference, known limitations
- Root `README.md` — Update marketplace description, version, quick start

### A8. Version Bump

- `learn-anything-plugin/.claude-plugin/plugin.json`: 1.0.3 → 2.0.0
- `.claude-plugin/marketplace.json` (root): match version
- Rebuild `learn-anything-plugin.zip`

---

## Phase B: Content Quality

**Goal:** Fix the earliest pipeline failure point (Skill Researcher) and the most visible output quality issues (Material Forge). These are the two skills where users see the biggest gap between expectations and results.

**Branch:** `phase-b/content-quality`

### B1. Ferriss Interview Execution (Pain Point 2)

**Problem:** The Skill Researcher's expert interview protocol (based on Tim Ferriss' 6 questions) is almost never executed. Confirmed: zero Ferriss-related references appear in any of the 3 test dossiers. The `references/expert-interview-protocol.md` exists but the SKILL.md doesn't enforce its use strongly enough.

**Root cause analysis:**
- The protocol reference exists but is listed as optional reading
- SKILL.md Step 2 mentions "simulated expert interviews" but doesn't mandate reading the reference
- Web search queries for interview synthesis are suggested but not required
- No validation check confirms interview data made it into the dossier

**Changes to `skills/skill-researcher/SKILL.md`:**

1. **Step 2 rewrite — make interview protocol mandatory:**
   - Change from "Simulated Expert Interviews (4-8 web searches)" to "Expert Interview Synthesis (REQUIRED — 6-12 web searches)"
   - Add explicit instruction: "Read `references/expert-interview-protocol.md` before proceeding. Execute ALL six Ferriss questions using the search strategies documented there."
   - Each Ferriss question must produce at least one web search and documented finding
   - Findings must be tagged with source URLs

2. **Add interview synthesis validation:**
   - After Step 2, add a checkpoint: "Verify that all 6 Ferriss questions produced at least one finding with a source URL. If any question produced zero findings, note it explicitly with confidence: LOW and conduct one additional targeted search."

3. **Update output requirements:**
   - `research_sources` in skill-dossier.json must include entries with `type: "expert_interview"` — at minimum 3 sources
   - Add validation: "If research_sources contains fewer than 3 expert_interview entries, the research phase is incomplete."

### B2. Knowledge Mapping for Cutting-Edge Fields (Pain Point 2)

**Problem:** For rapidly evolving fields (e.g., Claude Agent SDK), the initial skill decomposition reflects LLM training data, not current state. The SDK curriculum's entire first pass was wrong — missing new features, ignoring creator content (blog posts, tutorials, changelogs).

**Changes to `skills/skill-researcher/SKILL.md`:**

1. **Add freshness detection in Step 1 (Landscape Mapping):**
   - "Assess field velocity: How rapidly is this domain evolving? Check for: release cadence, recent major changes, active development blogs/changelogs, version numbers."
   - "If the field has had significant changes within the last 6 months, flag as HIGH_FRESHNESS_RISK."
   - "For HIGH_FRESHNESS_RISK fields: double the web search budget, prioritize official documentation and creator content (blog posts, tutorials, changelogs, release notes) over general articles, and explicitly note which components may be affected by recent changes."

2. **Add freshness metadata to dossier output:**
   - New optional field in skill-dossier.schema.json: `freshness_assessment: { risk_level: "low" | "medium" | "high" | "very_high", last_major_change: "<date or description>", evolution_notes: "<string>" }`
   - Downstream skills (especially Curriculum Architect) can use this to flag content that may need updating

3. **Add creator content search pattern:**
   - In Step 1, add: "For technical/product skills, search for official documentation, creator blogs, tutorials from the tool's authors, and recent conference talks. These are higher-signal than third-party articles for rapidly evolving tools."

### B3. Material Forge Reliability (Pain Point 4)

**Problem:** Material Forge doesn't reliably generate the full set of course materials. It defaults to Mermaid diagrams instead of detailed visuals. Light-on-light and dark-on-dark color issues appear in diagrams/flashcards. This is the most user-visible quality issue.

**Sub-problems and fixes:**

#### B3a. Generation Completeness via Dedicated Subagents

**Root cause:** Material Forge tries to generate everything in one pass, which is token-intensive. When context fills up, later material types get skipped or abbreviated. The most important outputs (lesson-by-lesson visuals, worked examples) are the ones most likely to suffer.

**Strategy change:** Instead of one monolithic generation pass, Material Forge becomes an **orchestrator of dedicated subagents**, each with its own context window, detailed templates, and QA checks.

**Changes to `skills/material-forge/SKILL.md`:**

1. **Subagent architecture for material generation:**
   - Material Forge reads the learning plan and knowledge graph, then dispatches dedicated subagents for each material type
   - Each subagent gets: the relevant task class data, vertex details, learner context, and a detailed generation template
   - Subagents run in parallel where possible (e.g., worked examples and visual materials for different task classes can generate simultaneously)

2. **Priority ordering (most important first):**
   - Worked examples with fading and detailed visuals (highest priority — these ARE the lessons)
   - Reference one-pagers with visual aids
   - Assessment instruments
   - SRS flashcards
   - Dependency graph visualization
   - Interleaved practice sets
   - Productive failure scenarios
   - Encoding aids

3. **Per-subagent QA:** Each subagent runs its own quality check against the relevant section of quality-rubrics.md before returning results. Material Forge aggregates and does a final cross-check.

4. **Completeness tracking:**
   - After all subagents complete, run a completeness check: "Verify all material types were generated for all applicable task classes. List any gaps."
   - If any subagent failed or produced incomplete output, report to the user and offer to regenerate via `/materials`

**New plugin agents (create in `learn-anything-plugin/agents/`):**
- `visual-material-generator.md` — Generates inline SVG visuals, worked example diagrams, concept illustrations. Detailed templates for common visual patterns (process flows, comparison diagrams, layered architectures, timelines). Enforces color contrast rules.
- `worked-example-generator.md` — Generates worked examples with backward fading sequences. Templates for different skill types (cognitive: step-by-step solutions, motor: perform-report-refine, language: pattern drills).
- `flashcard-generator.md` — Generates SRS cards per card-design-guide.md. Runs anti-pattern checks and visual audit.
- `assessment-generator.md` — Generates mastery gate items, delayed retention tests, transfer tasks per assessment-types.md.

#### B3b. Color Contrast Enforcement

**Root cause:** SVG generation doesn't enforce WCAG contrast ratios. The card-design-guide.md specifies colors but doesn't enforce contrast against backgrounds.

**Changes to `skills/material-forge/references/card-design-guide.md`:**

1. **Replace color palette with contrast-guaranteed pairs:**
   ```
   MANDATORY COLOR RULES:
   - ALL text: minimum #374151 (dark gray) or darker
   - ALL backgrounds: #ffffff (white) or #f9fafb (near-white)
   - NEVER use light colors (#93c5fd, #86efac, #fde68a, etc.) for text or lines
   - NEVER use dark backgrounds with dark text
   - Stroke colors for shapes: use the existing palette (#2563eb, #dc2626, #16a34a, #9333ea, #d97706) — these have sufficient contrast against white
   - Fill colors for shapes: use 10-15% opacity versions of stroke colors (e.g., rgba(37,99,235,0.1))
   ```

2. **Add to quality-rubrics.md visual quality check:**
   - "CONTRAST CHECK: Verify no text or line element uses a color lighter than #6b7280 against a white/light background. Verify no text uses white or near-white against a light background."

**Changes to `skills/material-forge/SKILL.md`:**

3. **Add explicit contrast instruction in SRS generation section:**
   - "Before finalizing any SVG, verify all text elements use colors darker than #6b7280 and all line/stroke elements use colors from the approved high-contrast palette. Light-on-light rendering is a critical defect — check every diagram."

#### B3c. Detailed Visuals vs Mermaid Default

**Root cause:** Mermaid is easier to generate (text-based) but produces generic diagrams. The skill should prefer inline SVG for flashcards and learning materials, reserving Mermaid for dependency graph overviews only.

**Changes to `skills/material-forge/SKILL.md`:**

1. **Clarify when to use each format:**
   - "Mermaid: ONLY for dependency graph visualizations (Section 6) and curriculum roadmaps"
   - "Inline SVG: For ALL flashcard diagrams, worked example illustrations, and reference material visuals"
   - "When a visual is needed for a flashcard (per the visual audit pass), generate inline SVG with the `image_svg` field. Do NOT substitute a Mermaid code block."

#### B3d. `/materials` Slash Command

**Problem:** No easy way for users to request ad-hoc material generation.

**New file: `commands/materials.md`**

```yaml
---
name: materials
description: Generate or regenerate learning materials for the active skill
argument_hint: "[type] [task-class]"
---
```

Body: Read active-skill.json, determine what materials exist vs what's missing, generate requested type (or all missing types). Types: flashcards, worked-examples, practice-sets, references, assessments, visuals, encoding-aids, all.

---

## Phase C: Learner Experience

**Goal:** Make the learning experience feel collaborative, personalized, and adaptable. These changes primarily affect the Curriculum Architect (mid-pipeline) and Training Conductor (late pipeline).

**Branch:** `phase-c/learner-experience`

### C1. Conversational Epitome Refinement (Pain Point 1)

**Problem:** The Curriculum Architect jumps from research completion to telling the user what's most important without pausing for input. If the epitome is even slightly misaligned with user desires, the user feels misunderstood and loses investment in the process.

**Root cause:** The curriculum-architect SKILL.md has no conversational checkpoint between epitome design and the rest of the curriculum. It treats epitome creation as an internal step, not a collaborative one.

**Changes to `skills/curriculum-architect/SKILL.md`:**

1. **Split Step 2a (Design the Epitome) into two sub-steps:**

   **2a-i. Draft epitome internally:**
   - Design the epitome following existing 4C/ID rules (simplified complete first lesson)
   - Identify 2-3 candidate epitome designs if the skill allows multiple valid starting points

   **2a-ii. Present and refine with the learner (NEW — conversational checkpoint):**
   - Present the proposed epitome to the learner with clear reasoning: "Based on your goals and what the research found, here's what I'd suggest for your first lesson..."
   - Explain WHY this epitome was chosen: what makes it representative, how it connects to the learner's stated goals, what they'll be able to do after completing it
   - Explicitly ask: "Does this feel like the right starting point? Is there something more important to you that should come first?"
   - If the learner suggests changes, refine the epitome. This may require adjusting which vertices are included, the complexity level, or the framing.
   - Only proceed to Step 2b (Task Class Design) after the learner confirms the epitome direction

2. **Add guidance on handling misalignment:**
   - "If the learner's desired starting point conflicts with prerequisite structure (they want to start with something that requires foundational knowledge), explain the dependency constructively: 'I can see why X is exciting — to get there solidly, we'd want to cover Y first, which typically takes N sessions. Would you like to start with Y framed around getting to X?'"
   - "Never override the learner's priorities without explanation. The epitome should feel like THEIR starting point, not an imposed one."

### C2. Teaching Preferences & Instructor Persona (Pain Point 5)

**Problem:** Learning sessions can feel like interrogation. There's no mechanism to capture how the user wants to be taught, and instructor personality doesn't persist across sessions. The SK-EFT Hawking Physics course worked well with a Feynman persona, but that required manual prompting each time.

**Schema changes:**

1. **New field in `domain-assessment.schema.json`:**
   ```json
   "teaching_preferences": {
     "type": "object",
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

2. **Expert panel discovery in Skill Researcher (prerequisite — Phase B changes):**
   - Add to `skills/skill-researcher/SKILL.md` Step 1 or 2: "Identify masters of the field — people who have driven the state of the art. For each, note any known teaching style or persona (e.g., Feynman: intuitive/visual/playful, Knuth: rigorous/methodical, Julia Child: warm/encouraging/hands-on). Store these in a new `expert_panel` field in the skill dossier."
   - New field in `skill-dossier.schema.json`:
     ```json
     "expert_panel": {
       "type": "array",
       "items": {
         "type": "object",
         "properties": {
           "name": { "type": "string" },
           "contribution": { "type": "string", "description": "What they're known for in this field" },
           "teaching_style": { "type": "string", "description": "Known teaching approach or persona, if applicable" },
           "source_url": { "type": "string" }
         },
         "required": ["name", "contribution"]
       }
     }
     ```

3. **Changes to `skills/domain-assessor/SKILL.md` (or curriculum-architect, since it runs after research):**
   - After the knowledge graph is built and before curriculum design, present the expert panel to the learner:
     - "The research identified these masters of [field]: [list with teaching styles]. You can choose none, one, or several as your virtual panel of experts. Your instructor will adopt their teaching approach during sessions."
   - If the research produced no clear expert panel, fall back to asking the user directly:
     - "Do you have a favorite teacher, author, or mentor whose style resonates? If not, what tone works best — formal, conversational, playful, or mentoring?"
   - If nothing by then, default to a generic expert teacher persona for the domain
   - Also ask about instruction-before-assessment preference:
     - "Would you prefer to be taught concepts first, or would you rather be challenged with questions and discover through discussion?"

3. **Changes to `skills/training-conductor/SKILL.md`:**
   - Add to Session Loading Protocol: "Read `teaching_preferences` from domain-assessment.json. If `instructor_persona` is set, adopt that persona's teaching style throughout the session."
   - Add to Session Flow Architecture: "If `instruction_before_assessment` is true, restructure the opening to present concepts BEFORE retrieval probes. Use Template A (Concept Introduction) as the default opening rather than Template B (Retrieval Practice)."
   - Add persona maintenance rule: "Maintain the instructor persona consistently throughout the session. If the persona is 'Feynman', use intuitive analogies, thought experiments, and playful language. If 'strict academic', use precise terminology and formal structure. The persona affects communication style, not pedagogical rigor — all teaching modes still use evidence-based scaffolding and adaptive difficulty."

4. **Changes to `skills/orchestrator/SKILL.md`:**
   - Add to Special Requests: "Change teaching style / Update persona: Route to Domain Assessor to update `teaching_preferences` in domain-assessment.json. The change takes effect at the next training session."

### C3. Conversational Mentor Mode (Pain Point 8)

**Problem:** Current training sessions are assessment-heavy. Users sometimes want a relaxed discussion mode — like chatting with a mentor — where exploration follows the student's interest and assessment happens passively in the background.

**Changes:**

1. **New session template in `skills/training-conductor/references/session-templates.md`:**

   **Template F: Mentor Conversation (~8,000 tokens)**
   - **Purpose:** Relaxed, exploratory discussion following learner interest. Invisible passive assessment.
   - **Trigger:** User requests "let's just talk about [topic]", "mentor mode", "exploration mode", or via `/train --mode mentor`
   - **Structure:**
     - Opening: "What's on your mind about [skill]?" or follow up on something from last session
     - Flow: Follow the learner's curiosity. Use the dependency graph to identify when the conversation touches on assessable vertices, but DON'T turn it into a quiz.
     - Passive assessment: When the learner demonstrates understanding (or misconception) of a vertex during natural conversation, note it internally. Update mastery estimates at session end.
     - Guidance: Gently steer toward adjacent topics that connect to curriculum gaps when natural opportunities arise, but never force a topic change.
     - Closing: Brief synthesis of what was explored, note any insights or misconceptions observed.
   - **Assessment protocol:** At session end, update knowledge graph vertices that were naturally touched during conversation. Use evidence_source: "mentor_conversation" to distinguish from formal assessment. Apply lower confidence weights (0.6x) compared to direct assessment since observations are informal.
   - **Persona integration:** If instructor_persona is set, this mode should feel most natural — like having coffee with the mentor and asking whatever comes to mind.

2. **Changes to `skills/training-conductor/SKILL.md`:**
   - Add Template F to the session template selection logic
   - Add mentor mode trigger detection: "If the learner asks for exploration, discussion, or 'just wants to talk about' the topic, use Template F."

3. **Changes to `/train` command (`commands/train.md`):**
   - Add `--mode` argument hint: `[optional context or --mode mentor]`
   - If `--mode mentor` is passed, instruct Training Conductor to use Template F

---

## Phase D: Lifecycle & Data

**Goal:** Add cross-cutting capabilities for data capture and curriculum maintenance that support long-term learning engagement.

**Branch:** `phase-d/lifecycle-data`

### D1. Session Transcript Storage (Pain Point 6)

**Problem:** No conversation logs are saved. This blocks: automated note-taking, QA review, building test fixtures, and debugging specific session issues.

**Changes:**

1. **Changes to `skills/training-conductor/SKILL.md`:**
   - Add to Session Loading Protocol: "Create a transcript file at `learn-anything/<skill-slug>/transcripts/session-<N>-<date>.md` at session start."
   - Add to session flow: "As the session progresses, append exchanges to the transcript file in TWO layers: (1) **Verbatim exchanges** — capture the full back-and-forth as it happens, and (2) **Assessment annotations** — inline notes on mastery implications, difficulty observations, and teaching decisions."
   - Add to session closing: "Finalize the transcript with a **Session Debrief** section: what went well, what went poorly, areas for improvement, mastery transitions, and next-session recommendations."
   - Transcript format:
     ```markdown
     # Session <N> — <date>
     ## Session Metadata
     - Skill: <skill-name>
     - Duration: <minutes>
     - Template: <template-used>
     - Instructor Persona: <persona or "default">
     - Difficulty Zone: <start> → <end>

     ## Transcript
     ### Topic: <vertex-name>
     **Instructor:** <full question or teaching point>
     **Learner:** <full response>
     **Assessment:** <observation, mastery implication>

     [... continues with verbatim exchanges ...]

     ## Session Debrief
     ### What Went Well
     - <specific moments, breakthroughs, strong responses>
     ### What Went Poorly
     - <confusion points, misconceptions, pacing issues>
     ### Areas for Improvement
     - <teaching approach adjustments, content gaps identified>
     ### Mastery Transitions
     - <vertex: from_state → to_state>
     ### Next Session Recommendations
     - <recommended agenda, topics to revisit, new content to introduce>
     ```

2. **Changes to `skills/orchestrator/SKILL.md`:**
   - Add to Special Requests: "Review session notes / Show transcript: Read the most recent transcript from `learn-anything/<skill-slug>/transcripts/`"

### D2. Curriculum Update Workflow (Pain Point 3)

**Problem:** No structured way to update an existing curriculum when the field evolves. Users can ask for updates ad-hoc, but there's no consistent workflow, and it's easy to create inconsistencies between state files.

**New file: `commands/update.md`**

```yaml
---
name: update
description: Update an existing curriculum to reflect new developments in the field
argument_hint: "[what changed or 'full refresh']"
---
```

**Workflow (implemented in command body):**

1. Read active-skill.json to find current skill
2. Read domain-assessment.json to check freshness_assessment (from Phase B)
3. Branch based on update scope:

   **Targeted update** (user specifies what changed):
   - Route to Skill Researcher with directive: "Update the skill dossier to incorporate: [user's description]. Do NOT rebuild from scratch — add new vertices, update existing ones, and mark deprecated ones."
   - After dossier update, route to Learner Calibrator: "Re-assess only the new/changed vertices against the learner's current state."
   - After calibration update, route to Curriculum Architect: "Re-sequence the learning plan to incorporate new content. Preserve completed task classes and session history."
   - Optionally route to Material Forge: "Generate materials for new/changed content only."

   **Full refresh** (user says "full refresh" or field has very_high freshness risk):
   - Route to Skill Researcher with directive: "Re-research the entire skill domain from scratch, comparing against the existing dossier. Flag what's new, what's changed, and what's been deprecated."
   - Follow the same downstream cascade but with broader scope

4. **State file versioning:**
   - Before any update, copy current state files to `learn-anything/<skill-slug>/archive/<date>/`
   - This preserves the ability to compare before/after and roll back if needed

5. **Changes to `skills/orchestrator/SKILL.md`:**
   - Add update routing logic alongside existing pipeline routing
   - Detect "update" intent: user mentions "things have changed", "new version", "update curriculum", "refresh", or uses `/update` command

6. **Changes to `skills/skill-researcher/SKILL.md`:**
   - Add "Update Mode" section: "When invoked for a curriculum update (not initial research), read the existing skill-dossier.json first. Compare the existing graph against fresh web research. Output a delta report alongside the updated dossier: which vertices were added, which were modified, which were marked deprecated."

7. **Changes to `skills/curriculum-architect/SKILL.md`:**
   - Add "Update Mode" section: "When invoked for a curriculum update, preserve completed task classes and the learner's progress. Insert new content into the appropriate task class based on complexity and prerequisites. Do not re-sequence completed work."

---

## Cross-Cutting Concerns

### State File Backward Compatibility

All schema changes in this spec are additive (new optional fields). Existing learning programs (PWA, SDK, Physics) will continue to work without migration. New fields will be populated when skills are next invoked.

### Implementation Order Within Phases

Each phase should be implemented in the order listed (A1 before A2, B1 before B2, etc.) as later items sometimes depend on earlier ones within the same phase.

### Testing Strategy

**During this update cycle:** Manual testing against the 3 existing learning programs after each phase. Run `/learn` and `/train` against at least one program per phase to verify no regressions.

**Post-stabilization:** Adopt the Anthropic skill-creator testing framework (draft → test → review → improve → repeat) for per-skill evaluation. Build test fixtures from the session transcripts captured in Phase D. The 14 autoresearch scenario profiles can be adapted as eval prompts.

### Packaging

After each phase merges to main:
1. Update version in plugin.json (2.0.0-alpha.1, .2, .3, .4)
2. Rebuild learn-anything-plugin.zip
3. Tag the release

Final 2.0.0 release after all four phases are complete and manually validated.

---

## Files Changed Summary

### Phase A (Code Quality)
| Action | File |
|--------|------|
| Edit | `skills/orchestrator/SKILL.md` |
| Edit | `skills/domain-assessor/SKILL.md` |
| Edit | `skills/skill-researcher/SKILL.md` |
| Edit | `skills/learner-calibrator/SKILL.md` |
| Edit | `skills/curriculum-architect/SKILL.md` |
| Edit | `skills/material-forge/SKILL.md` |
| Edit | `skills/training-conductor/SKILL.md` |
| Edit | `skills/dashboard-generator/SKILL.md` |
| Create | `skills/domain-assessor/references/classification-guide.md` |
| Create | `skills/orchestrator/references/routing-flowchart.md` |
| Edit | `schemas/skill-dossier.schema.json` (field annotations) |
| Edit | `learn-anything-plugin/README.md` |
| Edit | `README.md` |
| Edit | `learn-anything-plugin/.claude-plugin/plugin.json` |
| Edit | `.claude-plugin/marketplace.json` (root marketplace manifest) |

### Phase B (Content Quality)
| Action | File |
|--------|------|
| Edit | `skills/skill-researcher/SKILL.md` |
| Edit | `skills/skill-researcher/references/expert-interview-protocol.md` |
| Edit | `skills/material-forge/SKILL.md` |
| Edit | `skills/material-forge/references/card-design-guide.md` |
| Edit | `skills/material-forge/references/quality-rubrics.md` |
| Edit | `schemas/skill-dossier.schema.json` (freshness_assessment + expert_panel fields) |
| Create | `commands/materials.md` |
| Create | `agents/visual-material-generator.md` |
| Create | `agents/worked-example-generator.md` |
| Create | `agents/flashcard-generator.md` |
| Create | `agents/assessment-generator.md` |

### Phase C (Learner Experience)
| Action | File |
|--------|------|
| Edit | `skills/curriculum-architect/SKILL.md` |
| Edit | `skills/domain-assessor/SKILL.md` |
| Edit | `skills/skill-researcher/SKILL.md` (expert panel discovery) |
| Edit | `skills/training-conductor/SKILL.md` |
| Edit | `skills/training-conductor/references/session-templates.md` (Template F) |
| Edit | `skills/orchestrator/SKILL.md` |
| Edit | `schemas/domain-assessment.schema.json` (teaching_preferences) |
| Edit | `schemas/skill-dossier.schema.json` (expert_panel — may be done in Phase B) |
| Edit | `commands/train.md` |

### Phase D (Lifecycle & Data)
| Action | File |
|--------|------|
| Edit | `skills/training-conductor/SKILL.md` |
| Edit | `skills/orchestrator/SKILL.md` |
| Edit | `skills/skill-researcher/SKILL.md` |
| Edit | `skills/curriculum-architect/SKILL.md` |
| Create | `commands/update.md` |

---

## Resolved Design Decisions

1. **Transcript granularity:** Both verbatim AND summary. Transcripts capture full exchanges as they happen, plus a structured Session Debrief (what went well, what went poorly, areas for improvement, mastery transitions). This supports both QA review and automated note-taking.

2. **Mentor mode assessment weight:** 0.6x confidence accepted for now. The key principle: passive assessment must stay invisible to the user unless they explicitly ask "how am I doing?" Think of it like a good teacher forming impressions during casual conversation — useful signal, but lower confidence than formal assessment. Not critical to get perfect initially.

3. **Material Forge architecture:** Dedicated subagents, each with their own context window and detailed templates. Material Forge becomes an orchestrator dispatching specialized agents (visual-material-generator, worked-example-generator, flashcard-generator, assessment-generator). Lesson-by-lesson visual materials and worked examples are the highest priority, not flashcards. Each subagent runs its own QA pass.

4. **Teaching preference discovery:** The Skill Researcher identifies masters of the field during research (new `expert_panel` field in dossier). These are presented to the learner as a virtual panel of experts — user can choose none, one, or many. Fallback chain: expert panel from research → ask user directly about preferences → generic expert teacher persona for the domain.

5. **Curriculum update scope:** Entirely user-initiated for now via `/update` command. Freshness assessment serves as a guide for the user, not an automatic trigger. Future enhancement: optional parameter on `/update` for update suggestion frequency based on freshness risk (e.g., "suggest updates monthly if freshness risk is medium or higher").