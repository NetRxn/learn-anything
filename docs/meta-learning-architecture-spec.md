# Meta-Learning Plugin System: Architecture & Technical Specification

## Design Philosophy

This system takes a user from "I want to learn X" to an active, adaptive training program. It synthesizes Tim Ferriss' DiSSS/CaFE frameworks with evidence-based enhancements from cognitive psychology, instructional design, and motivation science. The central design tension — speed vs. durability — is resolved by optimizing for **durable competence within the user's stated timeframe**, not apparent progress.

The system's posture is constructive. When a user's goals are ambitious, the system doesn't lecture about limitations — it builds a plan that delivers the most value within the stated timeframe *and* offers a longer-horizon roadmap for continued growth. Every learner gets a workable path forward, calibrated to where they are now and where they want to go.

The system is **domain-agnostic**. It works for learning Spanish, guitar, negotiation, programming, pharmacology, wine tasting, swimming, chess, or anything else. The target skill is always a user input, never hardcoded.

---

## Central Artifact: The Knowledge Graph

The system's most important data structure is a **dual-layer knowledge graph** that evolves throughout the learning engagement:

**Layer 1 — Skill Dependency Graph:** The territory to be learned. Nodes are skill components (concepts, techniques, sub-skills); edges are prerequisite, similarity, and reinforcement relationships. This is produced by the Skill Researcher and is the same for all learners targeting the same skill.

**Layer 2 — Learner State Overlay:** The learner's current knowledge mapped onto the skill graph. Each node carries a mastery state (unknown, exposed, developing, proficient, automatized) with timestamps, assessment evidence, and confidence scores. This overlay is produced by the Learner Calibrator and continuously updated by the Training Conductor and external data imports.

**The gap between these two layers *is* the curriculum.** The Curriculum Architect works from this gap — prioritizing the highest-impact unfilled nodes, leveraging existing knowledge as scaffolding, and identifying transfer pathways where the learner's prior experience accelerates acquisition of new components.

**Data model target:** Postgres with Apache AGE for native graph operations (vertex/edge traversal, shortest path, centrality computation), pgvector for embedding-based similarity search (finding transfer pathways between the learner's existing knowledge and target skill components), and standard Postgres tables for relational data (sessions, assessments, schedules, materials).

---

## System Overview

The plugin consists of **seven major components** organized as a pipeline with calibration loops and feedback loops:

```
User Input (skill + goal + timeframe)
        │
        ▼
┌─────────────────────────────────┐
│  1. DOMAIN ASSESSOR &           │  Classify skill, gather learner background,
│     INITIAL LEARNER PROFILE     │  set constructive expectations, establish identity frame
└─────────┬───────────────────────┘
          │ Learner profile informs research priorities
          ▼
┌─────────────────────────────────┐
│  2. SKILL RESEARCHER            │  Deep investigation: deconstruction, dependency graph,
│     Maps the territory          │  frequency analysis, transfer pathway identification
└─────────┬───────────────────────┘
          │ Dependency graph ready
          ▼
┌─────────────────────────────────┐
│  3. LEARNER CALIBRATOR          │  Focused assessment against the dependency graph
│     Maps the learner            │  → produces knowledge graph overlay (the "gap map")
└────┬────────────────┬───────────┘
     │                │
     │ ◄──────────────┘  Optional loop: calibration reveals
     │                    unexpected gaps/strengths → trigger
     ▼                    additional targeted research
┌─────────────────────────────────┐
│  4. CURRICULUM ARCHITECT        │  Selection, sequencing, scheduling, motivation architecture
│     Designs the bridge          │  — works from the gap, not from scratch
└─────────┬───────────────────────┘
          │
          ▼
┌─────────────────────────────────┐
│  5. MATERIAL FORGE              │  Generates all learning materials + exports
│     Creates resources           │  (Anki decks, PDFs, exercises, assessments)
└─────────┬───────────────────────┘
          │
          ▼
┌─────────────────────────────────┐
│  6. TRAINING CONDUCTOR          │  Session-by-session teaching, assessment, adaptation
│     Runs the program            │◄─── feedback loop (updates knowledge graph,
└─────────┬───────────────────────┘     can trigger re-runs of 2/3/4/5)
          │
          ▼
┌─────────────────────────────────┐
│  7. DASHBOARD                   │  React artifact consuming system outputs
│     Visual home base            │  Knowledge graph visualization, progress, metrics
└─────────────────────────────────┘

        ◄─────── External Data Import ───────►
        (Anki review stats, Obsidian notes, self-reports,
         any structured input → updates knowledge graph)
```

Each component is a distinct skill/agent invokable independently or as a pipeline. The orchestrator manages routing, handoffs, state, and the calibration loops.

---

## Component 1: Domain Assessor & Initial Learner Profile

**Purpose:** Classify the target skill and gather the learner's relevant background in a single pass. Sets the strategic approach and constructive expectations. Establishes the identity frame for motivation.

**Trigger:** User states a learning goal.

**Process:**

**1. Skill Classification** — Categorize the target:
- **Skill type:** Motor / Cognitive-lower / Cognitive-higher / Perceptual / Social / Hybrid
- **Environment type:** Kind (stable rules, clear feedback) → Wicked (ambiguous feedback, shifting rules)
- **Bloom's ceiling:** What cognitive level does the user's stated goal require?
- **Modularity:** Genuinely decomposable into independent sub-skills, or emergent properties?
- **Tacit knowledge ratio:** How much is articulable vs. implicit?

**2. Initial Learner Profile** — Broad background gathering (before deep research exists):
- What related skills or domains does the learner already have experience in?
- What's their learning history in adjacent areas? (e.g., for "learn guitar": any musical experience? other instruments? music theory? physical dexterity activities?)
- What frameworks, mental models, or vocabulary do they already carry that might transfer?
- What's their general experience level with structured learning / self-directed study?
- What are their constraints (time per day, equipment access, learning environment)?
- Why this skill? What's the deeper purpose? (Feeds identity framing)

**3. Approach Strategy** — Select the downstream methodology (constructive framing):
- For every skill + timeframe combination, produce *both*:
  - **Short-term plan:** What can we accomplish within the stated timeframe? Be specific and optimistic-but-honest about what that looks like.
  - **Extended roadmap:** If the user's ultimate goal requires more time, what does the continued path look like beyond the initial timeframe?
- Select the instructional approach:
  - **Standard DiSSS pipeline** — Kind, modular, motor/cognitive-lower skills
  - **Whole-task emphasis (4C/ID)** — Complex cognitive skills
  - **Categorical framework approach** — Perceptual skills
  - **Observation-practice-debrief cycle** — Social/tacit skills
  - **Hybrid** — Most real skills need elements from multiple approaches

**4. Identity Frame** — Establish motivation layer 1:
- Frame the learning engagement as identity adoption: "You're becoming a ___"
- Connect to the learner's stated purpose

**Output:** Domain Assessment Profile + Initial Learner Profile. These parameterize all downstream components and steer the Skill Researcher toward transfer-relevant investigations.

---

## Component 2: Skill Researcher

**Purpose:** Deep investigation of the specific skill. Ferriss' Deconstruction + expert interviews, enhanced with data-driven methods. Now informed by the learner profile to actively investigate transfer pathways.

**Trigger:** Domain Assessment + Initial Learner Profile complete.

**Process:**

**1. Landscape Mapping** (web search + LLM knowledge)
- Survey skill structure, sub-domains, common learning paths
- Identify major "schools of thought" and pedagogical traditions
- Find existing curricula, textbooks, courses — note sequencing choices
- Flag controversies or disagreements among experts

**2. Simulated Expert Interviews** — Ferriss' protocol via LLM + web search:
- "Who is good at [X] despite disadvantages? What do they do differently?"
- "What are the biggest mistakes and wastes of time?"
- "What are novice mistakes vs. pro-level mistakes?"
- "Best resources for self-teaching?"
- "4 weeks, million dollars on the line — what does training look like?"
- "What's the oddest/most unconventional thing that works?"
- Ground answers in real expert perspectives (search for interviews, AMAs, masterclasses, podcasts)

**3. Component Identification** (Deconstruction)
- Apply Ferriss' four sub-techniques (Reduce, Interview, Reverse, Translate) systematically
- For each component, classify:
  - **Type:** Recurrent (needs automation) vs. Non-recurrent (needs schema building)
  - **Cognitive load category:** Intrinsic / Extraneous / Germane
  - **Prerequisite dependencies**
  - **Bloom's level required**
  - **Embedding vector** — Semantic representation for similarity matching (stored in pgvector)

**4. Frequency / Impact Analysis** — Data-driven selection prep:
- Search for corpus data, usage statistics, performance analytics
- Estimate Pareto distribution shape for this domain
- Identify coverage thresholds and "gateway nodes" (high betweenness centrality)

**5. Dependency Graph Construction** — Build the skill graph (stored in AGE):
- **Nodes:** Skill components with properties (type, Bloom's level, frequency, impact score, embedding vector, confidence score)
- **Edges:** Prerequisite (directed), similarity (undirected, weighted by embedding distance), reinforcement (component A practice also strengthens component B)
- **Computed properties:** Topological sort, betweenness centrality, PageRank, natural clusters

**6. Transfer Pathway Identification** — Using the Initial Learner Profile:
- For each skill the learner reports having, generate embedding vectors
- Use pgvector similarity search to find high-similarity nodes between the learner's existing skills and the target dependency graph
- Flag these as potential transfer points: "your piano experience means chord theory is likely partially developed"
- Identify analogies and translation opportunities (Ferriss' Translate technique, informed by actual overlap)

**Transfer pathway classification by embedding similarity:**

| Cosine Similarity | Transfer Type | System Action |
|---|---|---|
| 0.90–0.95 | Near transfer | Auto-boost mastery estimate for target node |
| 0.75–0.90 | Moderate transfer | Suggest accelerated path; probe before boosting |
| 0.65–0.75 | Far transfer | Probe with targeted question before any adjustment |
| Content >0.7, Procedure <0.5 | Negative transfer risk | Flag for explicit contrast instruction |

**7. Failure Point Catalog**
- Common beginner failure points
- Known plateaus and timing
- Strategy transitions that trigger step-function improvements
- Domain-specific illusion-of-competence risks

**Output:** Skill Research Dossier containing component inventory, dependency graph (AGE-compatible), frequency analysis, transfer pathway map, failure point catalog, confidence scores per component.

**Confidence constraint:** AI-generated decompositions are treated as drafts. Flag confidence levels (HIGH/MEDIUM/LOW). LOW-confidence items must note "VERIFICATION NEEDED: [specific aspect]." Use multi-pass decomposition (top-down and bottom-up, then reconcile) and confabulation detection ("For each skill, provide one specific real-world example. If you cannot, flag the skill as potentially confabulated").

---

## Component 3: Learner Calibrator

**Purpose:** The focused second pass. Maps the learner's existing knowledge onto the dependency graph, producing the knowledge graph overlay — the precise "gap map" that drives curriculum design. Grounded in Knowledge Space Theory (Doignon & Falmagne, 1985).

**Trigger:** Dependency graph complete from Skill Researcher.

**Theoretical foundation:** KST models a domain as a finite set of skills Q where each knowledge state is a feasible subset of Q constrained by prerequisite relationships. The collection of feasible states forms a knowledge structure. The learner overlay records which state the learner occupies. ALEKS demonstrates this approach assesses 350–500 skill domains in ≤30 questions through graph propagation.

**Process:**

**1. Diagnostic Assessment Design**
- Walk the dependency graph, prioritizing gateway nodes and nodes flagged as potential transfer points
- For each major node cluster, design lightweight diagnostic questions that distinguish between "unknown," "exposed," "developing," and "proficient"
- Use adaptive questioning: start broad, drill down where uncertainty exists, skip branches where competence is clearly established or clearly absent
- Keep the assessment efficient — the goal is a useful map, not an exhaustive exam

**2. Diagnostic Assessment Algorithm**

Three acceleration mechanisms minimize assessment length:

**Graph propagation** reduces questions by 40–60%. When a learner demonstrates mastery on skill S, all prerequisites of S receive an upward Bayesian update (dampened 0.7× per hop). When they fail, all dependents receive a downward update.

**Embedding-cluster inference** via pgvector infers mastery of unassessed skills with cosine similarity >0.85 to assessed skills. Three mastered skills in a semantic cluster → remaining cluster members tentatively marked mastered with a confidence penalty.

**Information-theoretic item selection** picks the next question to maximize entropy reduction across the entire graph, weighted by downstream impact (skills with many dependents assessed first).

```
ALGORITHM: ConversationalDiagnosticAssessment
INITIALIZE: P_mastery[s] = population_base_rate(s) for all skills
LOOP (max 20 questions OR max uncertainty < 0.15):
  1. SELECT skill with highest info_gain = entropy(s) × (1 + 0.3 × downstream_count)
  2. GENERATE open-ended diagnostic question via LLM
  3. EVALUATE response: {mastered: 1.0, partial: 0.5, misconception: 0.1, none: 0.0}
  4. BAYESIAN UPDATE using BKT: P_mastery[s] ← P(correct|mastered) × P_mastery[s] / evidence
  5. PROPAGATE: mastery up through prerequisites (0.7× dampening/hop),
               non-mastery down through dependents
  6. CLUSTER INFER: for unassessed skills with similar_assessed cosine > 0.85,
                    estimate mastery with confidence penalty
RETURN: knowledge_state map
```

**3. Interactive Calibration Session**
- Present diagnostics conversationally — this should feel like an engaging conversation about what the learner already knows, not a test
- For flagged transfer points, probe specifically: "You mentioned you play piano — can you explain what a chord inversion is?"
- Record responses with mastery state classification per node

**4. Knowledge Graph Overlay Construction**
- Map assessment results onto the dependency graph
- Each node gets: mastery_probability (continuous 0.0–1.0), mastery_category (derived discrete), confidence, evidence_count, last_assessed, BKT parameters (p_transit, p_slip, p_guess), transfer_boost
- Compute: total graph coverage, gap clusters, transfer leverage
- Store overlay in AGE as learner-specific vertex properties

**5. Gap Analysis & Transfer Map**
- Identify highest-impact unfilled nodes (weighted by frequency × centrality × distance from knowledge frontier)
- Map transfer pathways: where can existing knowledge scaffold new learning?
- Estimate effective curriculum scope: "You already have ~35% of the component graph covered. The remaining gap looks like a 6-week curriculum rather than 12 weeks from scratch."

**6. Calibration Loop**
- If assessment reveals unexpected strengths or gaps that change research priorities, trigger additional targeted research via the Skill Researcher
- Loop until both the skill graph and learner overlay are stable enough for confident curriculum design

**Output:** Annotated Knowledge Graph (dependency graph + learner overlay), gap analysis, transfer map, effective scope estimate. This is the primary input to the Curriculum Architect.

---

## Component 4: Curriculum Architect

**Purpose:** Transform the gap analysis into a concrete, time-bound learning plan. Works from the gap, not from scratch — leveraging existing knowledge as scaffolding and transfer pathways as accelerators.

**Trigger:** Knowledge graph overlay (gap map) stable.

**Process:**

**1. Selection Engine** — Choose what to learn from the unfilled nodes:
- Weight by: frequency × prerequisite centrality × impact × (1 - current_mastery) × transfer_leverage
- Verify the Pareto split is domain-appropriate
- Include gateway concepts even if not highest-frequency
- Exclude or deprioritize nodes already proficient (from calibration)
- Produce ranked priority list with rationale for each inclusion/exclusion

**2. Sequencing Engine** — Determine learning order:
- **Elaboration Theory (Reigeluth):** Design the "epitome" — simplest complete representative task for lesson one. Leverage existing knowledge to make the epitome more sophisticated than it would be for a true beginner.
- **4C/ID Model (van Merriënboer):** Organize into 3–5 task classes ordered simple-to-complex. Within each class, tasks have equal complexity but decreasing support (worked → completion → conventional). Sawtooth scaffolding. Distinguish recurrent (automation via drill) from non-recurrent (schema building via varied practice). Ensure variability (surface features change, deep structure stays).
- **Productive Failure (Kapur):** Flag conceptual building blocks with common naive theories for struggle-first moments. Use instruction-first for purely procedural components. Never apply when learner is already frustrated.
- **Mastery Gates:** Assessable criteria between task classes using Template E (see Session Templates). Include delayed assessment. Three mastery criteria options: BKT P(Ln) ≥ 0.95, streak of 3+ consecutive correct, or ≥85% on 5+ items.
- **Interleaving Schedule:** Blocked introduction, then interleaved practice (25% current topic, 75% review weighted toward recent). Pre-frame the difficulty.
- **Transfer-Leveraged Sequencing:** Start with components where existing knowledge provides the strongest scaffold. Use familiar concepts as anchors for unfamiliar ones.

**3. Scheduling Engine** — Map to the user's timeframe:
- **Durable Minimum Dose:** Session frequency and spacing calibrated to desired retention interval (Cepeda: optimal gap ≈ 10-20% of retention target)
- **Session architecture** (scoped to stay within 150k tokens when conducted by the Training Conductor):
  - ~10-15 min: Flow-level warm-up + retrieval probes on previous material
  - ~25-35 min: Deliberate practice at the edge of ability
  - ~10-15 min: Flow-level integration + session close
- **Dual timeline:** Short-term plan (user's stated timeframe) + extended roadmap (for continued growth beyond)
- **Plateau pre-planning:** Schedule expected plateaus with breakthrough protocols
- **Overlearning budget:** For skills requiring durability, schedule practice beyond mastery
- **SRS export schedule:** Generate Anki-compatible card decks at each curriculum stage

**4. Motivation Architecture** — Seven-layer system:
- Layer 1 — Identity: Already established in Assessment; reinforced throughout
- Layer 2 — Process goals: Daily focus on process, not outcomes
- Layer 3 — Competence feedback: Visible progress via knowledge graph advancement (real retention, not just practice completion)
- Layer 4 — Flow/deliberate practice alternation: Built into session architecture
- Layer 5 — Relatedness: Community resources, practice partners, accountability
- Layer 6 — Plateau protocols: Pre-framed, scheduled, with breakthrough strategies
- Layer 7 — Strategic stakes: Last resort, autonomy-supportive, for low-intrinsic-interest tasks only

**Output:** Complete Learning Plan (prioritized components, sequenced curriculum with task classes, dual-timeline schedule, motivation architecture, assessment criteria, plateau protocols). Stored as structured JSON (Postgres-compatible) with graph references (AGE node IDs).

---

## Component 5: Material Forge

**Purpose:** Generate all learning materials as tangible, exportable artifacts. The primary production engine.

**Trigger:** Learning Plan complete, or on-demand from Training Conductor.

**Material Types:**

**1. Retrieval Practice Materials**
- **Anki-compatible flashcard decks** — Designed for recall, not recognition. Tagged with curriculum position, component ID (AGE node reference), Bloom's level, difficulty estimate. Exported as .apkg files via genanki or as structured CSV/JSON.
- **Self-testing protocols** — Per-session retrieval questions (generation effect)
- **Interleaved practice sets** — Mixed-topic exercises for discrimination and retention

**2. Whole-Task Scenarios** (per 4C/ID)
- **Simplified whole tasks** per task class — authentic, representative problems
- **Worked examples with fading** — Full solution → partial → minimal hints → independent
- **Productive failure challenges** — Struggle-first problems for conceptual building blocks

**3. Reference Materials**
- **Prescriptive one-pager (PDF)** — Rules/principles of the skill, compressed
- **Practice one-pager (PDF)** — Concrete examples showing principles in action
- **Dependency graph visualization (Mermaid/SVG)** — Visual map of skill components and relationships
- **Curriculum roadmap (Markdown)** — The learning plan as a readable document
- **External resource list** — Curated books, videos, courses, communities, tools

**4. Assessment Instruments**
- **Diagnostic assessments** — For the Learner Calibrator
- **Mastery gate assessments** — Per task-class boundary
- **Delayed retention tests** — Designed for administration after a gap
- **Transfer tasks** — Novel problems testing generalization
- **Self-assessment rubrics** — With metacognitive calibration training

**5. Encoding Aids**
- **Mnemonics and memory hooks** — Domain-specific
- **Analogies and translations** — Connecting to the learner's existing knowledge graph
- **Visual/spatial organizers** — Concept maps, diagrams

**6. Motivation & Framing Materials**
- **Identity reinforcement prompts**
- **Plateau anticipation briefs**
- **Progress narratives**

**Output formats:**
- Flashcards: Anki .apkg packages + structured JSON (Postgres-compatible)
- Reference materials: PDF + Markdown
- Assessments: Structured JSON with rubrics
- Visualizations: Mermaid diagrams, SVG
- All structured data: JSON with AGE node ID references for graph linkage

**Quality self-check rubric:** Every generated material passes four checks before presentation: **Accuracy** (all factual claims verifiable, math/logic verified step-by-step), **Difficulty calibration** (matches target level, prerequisites within learner's demonstrated knowledge), **Pedagogical quality** (builds on prior concepts, includes active engagement opportunity, avoids unnecessary jargon), and a **Red-team pass** (could a learner misinterpret this? Does it inadvertently teach a misconception?). If any accuracy check fails, regenerate.

### SRS Card Design Principles

Cards follow Matuschak's five principles: **focused** (one detail per card), **precise** (specific question, unambiguous answer), **consistent** (lights the same mental "bulbs" each time), **tractable** (~90% target accuracy), and **effortful** (genuine retrieval, not pattern matching).

**Card type by knowledge type:**
- Basic Q→A: facts, definitions (Remember)
- Cloze deletion: terminology in context (Remember/Understand)
- Reversed: bidirectional associations, vocabulary
- Open-ended/generative: Apply through Create levels
- Comparison cards: confusable concepts (Analyze)

**Anti-patterns to reject:** Kitchen Sink cards (paragraph answers → split into atoms), ambiguous cloze (multiple valid completions), Yes/No cards (50% guess rate), shopping lists ("List all 7..." → individual cards per item), pattern matching (recognizing surrounding text rather than retrieving).

### Worked Examples with Backward Fading

**Backward fading** removes the last solution step first, then progressively earlier steps. Each faded step includes a self-explanation prompt. Fading pace by learner level: novice = 1 step every 2 problems; intermediate = 1 step per problem; advanced = 2 steps per problem. For a 5-step procedure: novices need ~11 problems to reach independence; intermediates need ~6.

### Productive Failure Scenario Design

Kapur's four conditions: problem activates prior knowledge, affords multiple solution paths (3–5 approaches), presents appropriate challenge without frustration, and is followed by consolidation instruction bridging student attempts to canonical solution. **Critical:** during the generation phase, no scaffolding or correction is permitted — only pumps.

### Interleaved Practice Design

Composition: 25% current topic, 75% review (weight recent topics more). No two consecutive problems should use the same strategy. Include at least one pair with similar surface features but different deep structure.

### Dependency Graph Visualization

Use **Mermaid flowcharts** (`flowchart TD`) with subgraphs for module grouping. Color-code by mastery status: green=mastered, yellow=in-progress, gray=not-started, dashed=locked. Include Unicode progress bars in node labels. Limit to ≤20 nodes per diagram; split larger graphs into module views.

### Anki .apkg Generation

Use the `genanki` Python library. Implementation requirements:
- Model and Deck IDs **must be hardcoded** (generate once with `random.randrange(1 << 30, 1 << 31)`) — changing IDs creates duplicates on re-import
- Override GUID property with `genanki.guid_for(card_id)` for deterministic re-imports
- Fields are HTML (escape literal `<`, `>`, `&`)
- Cloze models require `model_type=genanki.Model.CLOZE` and at least 2 fields
- Use `::` separator for subdeck hierarchy
- Include a hidden `KnowledgeNodeID` field in each note linking back to the AGE graph vertex
- The `.apkg` file is a ZIP containing a SQLite database (`collection.anki2`) plus a `media` JSON mapping

---

## Component 6: Training Conductor

**Purpose:** The ongoing teaching agent. Session-by-session adaptive instruction, assessment, knowledge graph updates, and plan adaptation. The heart of the system.

**Trigger:** Learning Plan + initial materials ready; user initiates a session.

**Critical Constraint: 150k Token Session Budget.** Each session operates within ~150k tokens to prevent context loss mid-teaching. This means:
- System prompt + curriculum context + session state: ~15-25k tokens
- Available for conversational exchange: ~125-135k tokens
- The Conductor loads only what's needed for today's session, not the full history
- Sessions have natural arcs that complete within budget

**Token budget allocation:**
- System prompt: ~3–5K tokens (compressed, structured)
- Per-session learner context: ~1–3K (structured JSON)
- Current lesson material: ~5–15K
- Conversation history: ~20–40K with rolling compression
- Output reserve: ~15–30K

**Token management strategies:** Component isolation (each component in its own context), rolling compression (last 5–10 turns verbatim, compress earlier into structured summaries saving ~80% per phase), structured over narrative (JSON for learner state, not prose), proactive memory management (compress and archive at natural breakpoints).

**Session Loading Protocol:**
1. Read current progress state (from project files / structured JSON)
2. Check for imported external data (Anki stats, self-reports)
3. Identify what's due: retrieval probes (from SRS schedule), new material (from curriculum position), assessments (from mastery gate proximity)
4. Load relevant curriculum context, recent session summaries, and today's materials
5. Discard everything else — full history lives in project files, not the session window

### Session Templates

Five session templates with distinct dialogue architectures, based on AutoTutor's Expectation-Misconception Tailored (EMT) framework. Each uses the **pump→hint→prompt→assertion escalation ladder** (decreasing student agency, increasing tutor information-giving).

**Assistance dilemma decision rule:** attempt 0 → pump; attempt 1 incorrect → hint; attempt 2 incorrect → prompt; attempt 3 incorrect → assertion + new attempt; misconception detected → immediate correction.

**Session phase architecture:**

| Phase | % of Session | Dialogue Character |
|---|---|---|
| Warm-up | 8–15% | Low-stakes retrieval, rapport |
| Instruction/Modeling | 15–25% | "I do, you watch" → "I do, you help" |
| Guided Practice | 25–35% | "You do, I help" — EMT dialogue cycles |
| Independent Practice | 20–30% | Minimal intervention, on-demand hints |
| Wrap-up/Assessment | 8–15% | Formative check, recap, preview |

**Template A — Concept Introduction (~7,000 tokens)**
Phases: Activation (3–4 turns) → Elicit Preconceptions (3–5 turns) → Guided Discovery (8–12 turns) → Consolidation (3–4 turns). Branching: correct preconception → skip to deeper exploration; misconception → trigger correction sequence; all expectations covered → consolidation.

**Template B — Retrieval Practice/Review (~5,800 tokens)**
Phases: Cued Recall (4–6 turns) → Elaborative Retrieval (4–6 turns) → Interleaved Application (4–6 turns) → Confidence Calibration (2–3 turns). Opens with open recall, pushes into "why" questions, then novel scenario requiring transfer. Ends with 1–5 confidence self-rating. If recall <50% of expectations → switch to re-teach (Template A).

**Template C — Skill Drilling with Feedback (~9,700 tokens)**
Phases: Worked Example (3–4 turns) → Guided Drill 3–5 problems (10–16 turns) → Independent Drill 3–5 problems (8–12 turns) → Error Analysis (2–4 turns). Scaffolding fades within session: problems 1–2 full guidance, 3–4 on-demand hints only, 5+ answer verification only. Expertise reversal effect demands this fading.

**Template D — Productive Failure Facilitation (~9,200 tokens)**
Phases: Problem Presentation (2–3 turns) → Generation & Exploration with **minimal guidance** (8–12 turns) → Impasse Recognition (3–4 turns) → Consolidation via direct instruction (5–8 turns) → Transfer (3–4 turns). **Critical:** during Generation phase, tutor resists correcting or hinting toward canonical solution. Only pumps permitted.

**Template E — Mastery Gate Assessment (~3,400 tokens)**
Most token-efficient template. Three criteria: Cold Recall (open question, no scaffolding) → Application Under Novelty (new problem, no hints) → Explain-to-Teach ("explain to a confused friend"). Pass all three → advance. Fail recall only → route to Template B. Fail application → route to Template A. Fail two+ → full re-teach cycle A→C→B→E.

**In-conversation retrieval probes:** Probes supplement, don't replace, external SRS review. Each probe corresponds to an exportable card (shared card_id). Timing: after explaining a concept, wait 2–5 exchanges before testing (micro-spacing), interleave probes from earlier in session, end sessions with cumulative mini-quiz covering 3–5 key concepts.

### Adaptive Difficulty Calibration

**Observable signal taxonomy:**

*High-reliability:* Response correctness (rolling 5-question window), error pattern classification (systematic = misconception, random = slip), transfer signals (unprompted analogies, cross-topic references), question quality (recall → comprehension → application → metacognitive).

*Medium-high reliability:* Elaboration depth (unprompted elaboration = strong mastery indicator), hedging vs. confidence language, help-seeking quality (specific questions = partial understanding; vague "I don't get it" = confusion).

*Medium reliability:* Response latency cues, affective signals (frustration/boredom markers), engagement quality.

**Calibration decision logic:**
```
IF accuracy > 90% AND explanations elaborate AND unprompted connections:
  → MASTERY: increase difficulty, introduce transfer tasks
IF accuracy 75-90% AND explanations adequate AND occasional errors:
  → ZPD-OPTIMAL: maintain current difficulty with varied examples
IF accuracy 60-75% AND hedging frequent AND help requests specific:
  → STRUGGLING PRODUCTIVELY: maintain support, don't reduce difficulty
IF accuracy < 60% AND help requests vague AND frustration markers:
  → BELOW ZPD: reduce difficulty, check prerequisites, increase scaffolding
IF accuracy > 95% AND responses terse AND engagement low:
  → BORED: advance difficulty immediately
```

**Optimal accuracy targets by learning phase:** Initial exposure 90–95% (confidence building), guided practice 80–90%, independent practice 75–85% (sweet spot zone), transfer tasks 60–75%.

**Distinguishing temporary struggle from fundamental gaps:** Temporary struggle shows improving accuracy across a window, inconsistent errors, maintained engagement, increasingly specific help requests → maintain difficulty with increased scaffolding. Fundamental gaps show flat/declining accuracy over 5+ attempts, systematic repeated errors, inability to explain reasoning, prerequisite concepts shaky when probed → regress to prerequisites.

**Preventing over-correction:** Minimum observation window (never adjust on single responses), hysteresis (sustained evidence before significant changes), offer student choice when uncertain.

### Core Functions (continued)

**Assessment & Knowledge Graph Updates**
- Continuous micro-assessment through conversation
- Mastery gate checks before advancing task classes (Template E)
- Delayed retention probes at session start (Template B)
- After each session: update knowledge graph overlay with new assessment evidence
  - Write updated mastery states to progress file (JSON, Postgres-compatible)
  - Include: node_id, new_mastery_state, evidence_summary, confidence, timestamp

**External Data Integration**
- At session start, check for imported external data:
  - Anki review statistics (retention rates, difficulty flags per card → mapped to AGE nodes)
  - User self-reports (real-world practice outcomes)
  - Notes from other tools
- Incorporate into knowledge graph updates using multi-source fusion (see Data Integration section)
- Use to inform session planning: "Your Anki retention on modal interchange cards is low — let's work on that today"

**Plateau Detection & Response**
- Monitor progress metrics for flattening
- Normalize plateaus, offer strategy-shift prompts, deploy breakthrough protocols
- If persistent: trigger re-assessment via Calibrator or re-sequencing via Architect

**Motivation Management**
- Track engagement signals
- Identity reinforcement, process goals, competence feedback through knowledge graph advancement
- Diagnose and adapt to drops in engagement
- External stakes only as last resort, autonomy-supportive

**Plan Adaptation**
- Authority to trigger re-runs of upstream components (research, calibration, curriculum, materials)
- Transparent communication about changes
- Graceful session boundaries: if a topic needs more depth than one session allows, close at a natural stopping point and set up next session's agenda

**Persistent State (written after each session):**
- Current curriculum position (task class, component focus)
- Knowledge graph updates (per-node mastery state changes with evidence)
- SRS review state (what's due, intervals — for in-session probes; full SRS scheduling is external)
- Session log (date, duration, topics, assessment results, difficulty observations)
- Motivation state (engagement trend, plateau status, identity reinforcement moments)
- Next session agenda

**State format:** Structured JSON, compatible with Postgres import. Graph-referencing fields use AGE vertex IDs.

---

## Component 7: Dashboard

**Purpose:** A React artifact within the Claude Project that serves as the learner's visual home base. Consumes the system's structured data outputs and renders the knowledge graph, progress metrics, and curriculum state.

**Displays:**
- **Knowledge graph visualization** — The dependency graph with the learner's mastery overlay. Nodes colored by mastery state (unknown → exposed → developing → proficient → automatized). Interactive: click nodes to see details, evidence, and connections.
- **Curriculum roadmap** — Current position, what's next, projected timeline for short-term and extended plans
- **Key metrics** — Delayed retention scores, components mastered, practice consistency, transfer performance, self-assessment calibration accuracy
- **Session history** — Recent sessions with topics and outcomes
- **Upcoming** — Next session agenda, SRS items due, upcoming mastery gates

**Data consumption:** Reads the structured JSON outputs from the other components. Can be regenerated/updated after any session.

**Design principles:**
- Show metrics that reflect actual learning (retention, transfer), not just effort (hours, streaks)
- The knowledge graph visualization is the primary view — it shows where the learner is, where they're going, and how their existing knowledge connects to new material
- Honest and motivating: progress is real and visible, gaps are clear without being demoralizing

**Progress reporting anti-patterns to avoid:** Completion ≠ mastery (completing 85% of lessons means nothing if retention is 40%). Vanity XP (points that accumulate monotonically regardless of quality). Hidden decay (showing "Mastered" badges from 6 months ago with no decay indication). Streak anxiety (loss-aversion mechanics creating stress). Instead: show retrievability-adjusted strength meters that fade over time, distinguish recognition from production (Bloom's level labeling), use dual metrics (breadth + depth), celebrate real milestones (first transfer task, maintained mastery after 30 days), make decay visible but non-punitive ("This is ready for a refresher").

---

## Cross-Cutting: Data Architecture

### Apache AGE Graph Layer

**Vertex types:**

`Domain` — Top-level subject (e.g., "Python Programming," "Classical Guitar")
- Properties: id, name, description, skill_type, environment_type, blooms_ceiling

`Concept` — Abstract knowledge unit
- Properties: id, name, description, embedding_id (FK to pgvector), blooms_level, frequency_score, impact_score, confidence, type (recurrent/non-recurrent)

`Skill` — Assessable ability tied to concepts
- Properties: id, name, description, embedding_id, blooms_level, assessment_criteria_json

`LearnerState` — Per-learner overlay on concepts/skills
- Properties: mastery_probability (0.0–1.0, primary), mastery_category (derived: novice/developing/proficient/mastered), confidence, evidence_count, last_assessed, fsrs_difficulty (1.0–10.0), fsrs_stability (days), p_transit (BKT learning rate), p_slip, p_guess, transfer_boost

**Edge types:**

`PREREQUISITE` — Directed, from prerequisite to dependent
- Properties: strength (0.0–1.0), type (hard/soft)

`RELATED` — Undirected, similarity-based
- Properties: similarity_score, transfer_coefficient

`REINFORCEMENT` — Practicing A strengthens B
- Properties: weight

`COMPOSES` — Skill→Concept relationship
- Properties: weight

`HAS_STATE_FOR` — Learner overlay → Concept/Skill
- Properties: (all LearnerState properties above)

### pgvector Embedding Layer

`component_embeddings` table:
- id UUID, component_id TEXT (AGE vertex ref), embedding VECTOR(1536), domain TEXT, embedding_type TEXT (content/procedure), created_at TIMESTAMP

HNSW index for fast similarity search. Used for: transfer pathway identification (cross-domain similarity), finding analogies between learner's existing knowledge and target skill components, semantic search across material library, unstructured import processing (matching Obsidian notes to graph nodes).

### PostgreSQL Relational Layer

```sql
-- Core entities
CREATE TABLE learners (
  id UUID PRIMARY KEY,
  profile JSONB NOT NULL,           -- initial learner profile from Domain Assessor
  fsrs_params JSONB,                -- personalized FSRS parameters
  created_at TIMESTAMP DEFAULT NOW()
);

CREATE TABLE learning_plans (
  id UUID PRIMARY KEY,
  learner_id UUID REFERENCES learners,
  skill_domain TEXT NOT NULL,       -- AGE Domain vertex ref
  plan_json JSONB NOT NULL,         -- full curriculum structure
  short_term_target TEXT,
  extended_target TEXT,
  created_at TIMESTAMP DEFAULT NOW(),
  updated_at TIMESTAMP DEFAULT NOW()
);

-- Session tracking
CREATE TABLE learning_sessions (
  id UUID PRIMARY KEY,
  learner_id UUID REFERENCES learners,
  plan_id UUID REFERENCES learning_plans,
  session_date TIMESTAMP NOT NULL,
  duration_minutes INTEGER,
  template_used TEXT,               -- A|B|C|D|E
  topics_json JSONB,                -- AGE vertex IDs touched
  assessment_results_json JSONB,
  difficulty_observations JSONB,
  next_agenda JSONB,
  created_at TIMESTAMP DEFAULT NOW()
);

CREATE TABLE session_messages (
  id UUID PRIMARY KEY,
  session_id UUID REFERENCES learning_sessions,
  role TEXT NOT NULL,                -- tutor|learner
  content TEXT NOT NULL,
  bloom_level_demonstrated TEXT,
  correctness DECIMAL(3,2),
  embedding_id UUID,                -- FK to component_embeddings for semantic search
  sequence_num INTEGER NOT NULL,
  created_at TIMESTAMP DEFAULT NOW()
);

-- Assessment
CREATE TABLE assessments (
  id UUID PRIMARY KEY,
  learner_id UUID REFERENCES learners,
  session_id UUID REFERENCES learning_sessions,
  component_id TEXT NOT NULL,       -- AGE vertex ref
  assessment_type TEXT NOT NULL,    -- diagnostic|mastery_gate|retention|transfer
  bloom_level TEXT NOT NULL,
  item_type TEXT NOT NULL,          -- recall|explain|apply|analyze|near_transfer|far_transfer
  score_binary BOOLEAN,
  score_partial DECIMAL(5,4),
  confidence_pre SMALLINT,          -- 1-5 self-rated before answering
  response_time_ms INTEGER,
  surface_features JSONB,
  deep_structure_id UUID,           -- links structurally equivalent items
  gaming_flag BOOLEAN DEFAULT FALSE,
  created_at TIMESTAMP DEFAULT NOW()
);

CREATE TABLE mastery_transitions (
  id UUID PRIMARY KEY,
  learner_id UUID REFERENCES learners,
  component_id TEXT NOT NULL,       -- AGE vertex ref
  from_state TEXT NOT NULL,
  to_state TEXT NOT NULL,
  trigger_type TEXT NOT NULL,       -- assessment|decay|import|propagation
  trigger_source TEXT,              -- session_id, import_id, etc.
  reason TEXT,
  created_at TIMESTAMP DEFAULT NOW()
);

-- SRS Cards
CREATE TABLE srs_cards (
  card_id UUID PRIMARY KEY,
  plan_id UUID REFERENCES learning_plans,
  component_id TEXT NOT NULL,       -- AGE vertex ref
  card_type TEXT NOT NULL,          -- basic|cloze|reversed|open_ended|comparison
  front TEXT NOT NULL,
  back TEXT NOT NULL,
  bloom_level TEXT NOT NULL,
  knowledge_type TEXT NOT NULL,     -- fact|concept|procedure|principle|mental_model
  topic_tags TEXT[] NOT NULL,       -- hierarchical: ["harmony::chord-progressions::cadences"]
  difficulty_estimate NUMERIC(3,2),
  curriculum_position INTEGER,
  source_type TEXT DEFAULT 'curriculum',
  ease_factor NUMERIC(4,2) DEFAULT 2.50,
  interval_days INTEGER DEFAULT 0,
  next_review DATE,
  lapses INTEGER DEFAULT 0,
  created_at TIMESTAMP DEFAULT NOW()
);

-- External data imports
CREATE TABLE external_imports (
  id UUID PRIMARY KEY,
  learner_id UUID REFERENCES learners,
  source TEXT NOT NULL,             -- anki|obsidian|self_report|other
  data_json JSONB NOT NULL,
  processed BOOLEAN DEFAULT FALSE,
  processing_results JSONB,
  imported_at TIMESTAMP DEFAULT NOW()
);

-- Materials
CREATE TABLE materials (
  id UUID PRIMARY KEY,
  plan_id UUID REFERENCES learning_plans,
  material_type TEXT NOT NULL,      -- worked_example|productive_failure|practice_set|reference|assessment
  content TEXT NOT NULL,
  component_ids TEXT[] NOT NULL,    -- AGE vertex refs
  format TEXT NOT NULL,             -- markdown|pdf|json|mermaid|apkg
  metadata JSONB,
  created_at TIMESTAMP DEFAULT NOW()
);
```

### FSRS Decay Model at the Graph Level

Each LearnerState vertex maintains FSRS parameters: Difficulty (D, 1.0–10.0), Stability (S, days for retrievability to decay from 100% to 90%), and Retrievability (R, computed on-the-fly).

**Forgetting curve:** `R(t, S) = (1 + t/(9·S))^(−1)` where t = days since last review. At t=0, R=1.0. At t=S, R≈0.9.

**Compute R on-the-fly** when queried (it changes constantly). **Store S and D persistently** (they only change on review events).

**State transition rules:**
```
PROMOTION:
P1: NOT_STARTED + score ≥ 0.70 → FAMILIAR
P2: NOT_STARTED + score = 1.0 → PROFICIENT (skip promotion)
P5: FAMILIAR + score = 1.0 → PROFICIENT
P6: PROFICIENT + score = 1.0 + spaced_review → MASTERED

DEMOTION:
D1: MASTERED + score 0.70–0.99 → PROFICIENT
D2: MASTERED + score < 0.70 → FAMILIAR (double demotion)

DECAY (time-based, using FSRS retrievability):
DECAY1: MASTERED + R < 0.70 → PROFICIENT
DECAY2: PROFICIENT + R < 0.60 → FAMILIAR
DECAY3: FAMILIAR + R < 0.50 → ATTEMPTED
```

**Effective mastery score** combines level and FSRS: `effective_mastery = base_mastery(level) × R(t, S)` where base_mastery maps NOT_STARTED=0.0, ATTEMPTED=0.25, FAMILIAR=0.50, PROFICIENT=0.80, MASTERED=1.0.

**Cross-layer integration pattern:** Graph node UUIDs are the canonical identifiers used across both AGE and Postgres. Cross-layer queries use AGE's `cypher()` function in SQL to get graph results, then JOIN with relational tables.

---

## Bidirectional Data Flow

### Exports (plugin → external tools)

- Anki .apkg packages via genanki (with hidden KnowledgeNodeID field for round-trip tracking)
- Structured JSON for all artifacts (curriculum, progress, assessments, cards) — schemas match Postgres tables
- PDF reference materials and one-pagers
- Markdown documents (study guides, curriculum roadmap, progress summaries)
- Mermaid/SVG dependency graph visualizations

### Imports (external tools → plugin)

**Anki review history round-trip:**
1. **Export:** Plugin generates .apkg with hardcoded Model/Deck IDs and deterministic GUIDs. Each note includes hidden KnowledgeNodeID field.
2. **User reviews in Anki:** Standard workflow. FSRS scheduler manages intervals.
3. **Import:** Extract `collection.anki2` from .apkg ZIP. JOIN `revlog` with `cards` and `notes` to recover KnowledgeNodeID from note fields (split on `0x1f`). Parse each review: ease (1-4), interval, factor, review time, review type.
4. **Graph update:** Map reviews to mastery deltas. Again (ease=1) → −0.15 × lapse_multiplier. Good (ease=3) → +0.05 × (1.2 − R), crediting harder successful recalls more. Update FSRS stability using FSRS-6 formulas. Propagate 10% of mastery delta to prerequisite nodes.
5. **Adapt:** Updated graph informs next session's card selection, difficulty, and routing.

**Obsidian/unstructured notes import:**
- Extract wikilinks for direct high-confidence matches to graph nodes
- Chunk remaining text (256 tokens, 50-token overlap), embed via text-embedding-3-small
- Query pgvector for nearest graph nodes (cosine >0.75)
- Classify signal type: explanations/examples → small positive delta; questions/confusion → small negative delta
- Weight: SOURCE_WEIGHT['obsidian'] = 0.12

**Self-report import schema:**
```json
{
  "timestamp": "ISO-8601",
  "component_id": "AGE vertex ref (optional)",
  "component_description": "free text if no ID",
  "activity_type": "practice|observation|application|reflection",
  "duration_minutes": 30,
  "self_assessed_quality": 3,  // 1-5
  "observations": "free text",
  "outcome": "free text"
}
```

### Multi-Source Confidence Fusion

| Source | Base Weight | Rationale |
|---|---|---|
| Anki Reviews (FSRS) | 0.45 | Direct behavioral evidence of recall |
| Plugin Assessments | 0.35 | Controlled test conditions |
| Obsidian Notes | 0.12 | Indirect signal; studying ≠ mastery |
| Self-Reports | 0.08 | Subjective; Dunning-Kruger effect |

Each source's effective weight decays exponentially with age (half-life ~23 days).

**Fused mastery score:** `Σ(mastery_i × weight_i × confidence_i × recency_i) / Σ(weight_i × confidence_i × recency_i)`

**Conflict resolution:** Anki "Easy" but assessment shows gaps → recognition-vs-application gap; halve Anki's influence, generate application-focused cards. Anki lapses but assessment strong → suspect card quality; flag cards for reformulation. Self-report always yields to behavioral data. Exception: for motor/perceptual skills, self-reports may be the only between-session signal — weight increases to 0.20 for these skill types.

---

## Domain-Specific Adaptation

The system's components require fundamentally different configurations by skill type. The AI's comparative advantage is strongest for cognitive skills (infinite practice, code verification, Socratic dialogue) and weakest for perceptual skills (cannot provide sensory stimuli). Motor and perceptual domains require the AI to function primarily as a **coach-between-sessions**.

**Training Conductor adaptations:**
- **Cognitive (Python):** Socratic dialogue with code verification, Parsons problems, bug hunts
- **Motor (guitar):** External-focus verbal cues, Perform-Report-Refine self-description loop
- **Language (Mandarin):** Text conversation simulation, grammar/character drills, recommend external audio tools
- **Perceptual (wine):** Structure real-world tasting exercises, debrief experiences verbally
- **Social (negotiation):** AI role-play with coaching pauses, post-simulation structured debriefs

**Material Forge adaptations:**
- **Cognitive:** Worked examples, faded examples, Parsons problems, bug-hunting exercises
- **Motor:** Practice routines with external-focus cues, self-assessment checklists, troubleshooting guides
- **Language:** Graded reading passages, character decomposition mnemonics, grammar drills, tone-pair practice
- **Perceptual:** Comparative tasting/listening protocols, vocabulary cards tied to standardized frameworks, descriptive scenario quizzes
- **Social:** Case briefs, BATNA worksheets, role-play scenarios with AI persona definitions, debrief questionnaires

**Cross-cutting principles:** External focus of attention (Wulf, 2013) for motor/perceptual domains. 4C/ID whole-task approach applies universally. Verbal overshadowing risk for perceptual skills — co-develop vocabulary and perceptual expertise in parallel.

---

## Assessment Architecture

### Four Assessment Types

**Diagnostic** (Calibrator) — Maps existing knowledge. Breadth: 3–5 items per KC at varying difficulty. Low-stakes. Adaptive item selection via graph propagation. Output: knowledge state map.

**Mastery Gate** (Curriculum advancement) — Confirms learning. Depth: minimum 3 items per KC (5+ preferred), at or one Bloom level above taught level, varied surface features. Template E structure (Cold Recall → Application Under Novelty → Explain-to-Teach). Failure → targeted re-teach, retest with new items, max 3 attempts.

**Delayed Retention** — Verifies long-term memory. Schedule at 1–3, 7–14, and 30+ days after mastery. No hints or scaffolding. Items vary surface features from original instruction.

**Transfer** — Tests generalization. Administer after mastery + one successful retention check. Near transfer first (same principle, different context), then far transfer (different domain). Design: identify deep structure, systematically vary domain/objects/context while holding relational structure constant.

### Mastery Criteria by Bloom's Level

| Level | Item Type | Threshold | Items Needed |
|---|---|---|---|
| Remember | Recall, matching, fill-in-blank | 90–95% | 3–5 |
| Understand | Explain in own words, classify | 85–90% with rubric | 3–5 |
| Apply | Solve novel problems | 85% | 3+ varied |
| Analyze | Compare, find patterns | 80% with rubric | 3+ cases |
| Evaluate | Judge, critique | 75–80% rubric-scored | 2–3 |
| Create | Design, produce | Holistic rubric | Portfolio |

### Anti-Gaming Strategies

Procedural content generation (randomized surface features per assessment), explanation requirements (cannot game free-form explanation), unpredictable assessment timing, delayed mastery confirmation (even after passing a gate, require at least one delayed retention check), cross-KC consistency checks (advanced mastery + prerequisite failure → trigger diagnostic review).

---

## Prompt Architecture

### General Principles

Prompts should be **~70% behavioral instructions, ~30% learning theory rationale**. Encode consequences of learning theory as behavioral rules rather than expecting the LLM to derive pedagogy from theory. Example: instead of "Vygotsky's ZPD suggests tasks at the edge of ability," write "If the learner answers correctly 3 times in a row with no hesitation, increase difficulty."

### Six Critical Failure Mode Guardrails

**Being too agreeable:** "When a learner provides an answer, NEVER begin with agreement unless the answer is fully correct. If partially correct: 'You're on the right track with [specific correct part], but let's examine [specific incorrect part].' Before validating any answer, internally verify it step-by-step."

**Over-scaffolding:** Four-level protocol — Level 1: open-ended question; Level 2: narrowed focus; Level 3: provide a choice; Level 4: concrete analogy then return. "NEVER skip to Level 4 without exhausting earlier levels. After correct response at any level, RESET to Level 1."

**Hallucination:** "For mathematical/logical content: show your work step-by-step internally before presenting. If uncertain about a factual claim, say 'I believe X, but this should be verified.' NEVER fabricate citations."

**Defaulting to lecture mode:** "Your responses should contain at least one question for every 3 sentences of explanation. Maximum explanation length: 150 words before requiring learner interaction."

**Failing to push back on overconfidence:** "If learner says 'I already know this,' probe deeper: 'Can you explain why [underlying principle] works that way?' Present edge cases as challenges."

**Inconsistent difficulty:** "Do not adjust difficulty based on emotional appeals. Adjust ONLY based on performance data: success rate, time-to-answer, scaffold levels needed."

### Component-Specific Prompt Guidance

**Skill Researcher:** Multi-pass decomposition (top-down then bottom-up, reconcile). Each skill must be independently assessable and MECE. Confidence flagging mandatory (HIGH/MEDIUM/LOW). LOW-confidence items must note "VERIFICATION NEEDED: [specific aspect]." Confabulation detection: "For each skill, provide one specific real-world example. If you cannot, flag the skill as potentially confabulated."

**Curriculum Architect:** Encode 4C/ID as: design 3–5 task classes simple-to-complex; within each class, tasks have equal complexity but decreasing support (worked → completion → conventional); ensure variability. Encode Elaboration Theory as: create epitome, elaborate in layers, use spiral sequencing. Flag productive failure insertion points for concepts with common naive theories.

**Material Forge:** Self-check every output against the four-check rubric (accuracy, difficulty calibration, pedagogical quality, red-team pass) before presenting. Regenerate if any check fails.

### Orchestrator Routing Logic

```
ROUTING LOGIC:
IF phase == "ONBOARDING":
  IF NOT domain_assessment_exists → ROUTE to ASSESSOR
  IF NOT skill_tree_exists → ROUTE to RESEARCHER
  ELIF NOT calibration_complete → ROUTE to CALIBRATOR
  ELIF NOT curriculum_exists → ROUTE to ARCHITECT
  ELSE → generate initial materials via FORGE → TRANSITION to "LEARNING"

IF phase == "LEARNING":
  IF needs_new_material → ROUTE to FORGE
  IF learner_active → ROUTE to CONDUCTOR
  IF lesson_complete → ROUTE to ASSESSOR (mastery gate)
  IF assessment_complete → UPDATE graph
    IF recalibration_needed → CALIBRATOR
    IF resequencing_needed → ARCHITECT

ERROR RECOVERY:
- Any component fails twice → fallback (generic skill tree, simplified material,
  conservative difficulty estimate, structured Q&A mode)
- Always preserve learner state on error
```

---

## User Experience Flow

**Day 1: Setup (one or two conversations)**

Conversation 1 — Assessment & Research (~30-45 min):
1. User: "I want to learn [X] to [level] in [timeframe]"
2. Domain Assessor runs: classifies skill, gathers learner background, establishes identity frame, presents approach strategy with constructive dual timeline
3. Skill Researcher runs: deep investigation informed by learner profile, produces dependency graph and transfer pathway map
4. User reviews highlights, validates/adds context

Conversation 2 — Calibration & Plan (~30-45 min):
5. Learner Calibrator runs: diagnostic assessment against the dependency graph, produces the gap map
6. (Optional calibration loop if surprises emerge)
7. Curriculum Architect runs: builds the learning plan from the gap map, presents curriculum and schedule
8. User approves/modifies
9. Material Forge generates initial materials + Anki deck export + dashboard
10. User receives: learning plan, session schedule, Anki deck, reference PDFs, dashboard, identity frame

**Day 2+: Training Sessions (~30-60 min each, within 150k token budget)**
1. User opens a session with the Training Conductor
2. Conductor: loads state, imports any external data, runs retrieval probes, delivers new content, facilitates practice, closes with assessment and next-session preview
3. Between sessions: user reviews Anki cards, practices independently, optionally imports external data
4. Dashboard updates after each session

**Periodic: Adaptation**
- Conductor detects plateau → deploys breakthrough protocol, or triggers re-assessment
- User's goals evolve → re-run relevant upstream components
- Materials exhausted → Forge generates more
- Significant external data import → recalibrate knowledge graph overlay

---

## Implementation: Skill Suite Architecture

**Orchestrator** — The meta-skill that routes between components, manages state, and handles the calibration loops. Its prompt encodes:
- Pipeline phase detection (where is the user in the overall flow?)
- Component invocation logic (when to call which skill)
- State management (read/write the JSON artifacts)
- Handoff protocols (what context to pass between components)
- Calibration loop management (when to bounce back to research from calibration)

**Individual Skills:**
- `domain-assessor` — Classification + learner profile + constructive expectation setting
- `skill-researcher` — Deep investigation + dependency graph construction + transfer pathway ID
- `learner-calibrator` — Diagnostic assessment + knowledge graph overlay + gap analysis
- `curriculum-architect` — Selection + sequencing + scheduling + motivation architecture
- `material-forge` — All material generation + export formatting (Anki, PDF, Markdown, JSON)
- `training-conductor` — Session management + adaptive teaching + assessment + knowledge graph updates + external data import
- `dashboard-generator` — React artifact generation/update from structured data

**Project container:** A Claude Project holds the persistent artifacts (JSON files, generated materials, dashboard). The project instructions encode the overall methodology and component descriptions. Individual skills are invoked within this project context.

---

## Quality Guardrails

- **Confidence scoring:** Every AI-generated decomposition carries a confidence score. Specialized domains get explicit recommendations for expert validation.
- **Constructive framing:** The system always builds a workable plan. Limitations are handled as design constraints the system works around, not warnings presented to the user.
- **Performance-learning distinction:** The system's internal logic distinguishes between practice performance and durable learning. This shapes assessment design and progress reporting. Learners are educated about this distinction through the experience (desirable difficulties are framed as features) rather than through lectures about cognitive science.
- **Motivation safety:** External stakes are a last resort. The system watches for demotivation and adapts.
- **Session scope:** Training sessions stay within 150k tokens. Graceful boundaries at natural stopping points.
- **Data portability:** All structured outputs use schemas compatible with Postgres/pgvector/AGE. Nothing is locked into a proprietary format.
