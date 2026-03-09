# Deep Research Prompt: Closing Implementation Gaps for the Meta-Learning Plugin System

## Context

I am building an AI-powered meta-learning plugin system (Claude skills with an orchestrator) that takes any target skill and produces a complete, adaptive training program. The system synthesizes Tim Ferriss' DiSSS/CaFE frameworks with evidence-based enhancements from cognitive psychology, instructional design, and motivation science. Two prior research rounds have established the theoretical foundation, and an architecture sketch (included below in full) defines the system's components, data model, and interaction patterns.

### Research completed so far

**Round 1** produced a foundation synthesis of Ferriss' frameworks: DiSSS (Deconstruction, Selection, Sequencing, Stakes), CaFE (Compression, Frequency, Encoding), the Minimum Effective Dose principle, and the expert interview protocol.

**Round 2** produced an evidence-based critique identifying five structural upgrades to the Ferriss foundation:

First, add a Domain Assessment gate before Deconstruction. This involves rating the target domain on Hogarth's kind/wicked spectrum, identifying skill type (motor/cognitive/perceptual/social), and estimating the Bloom's taxonomy ceiling. This determines which downstream techniques apply and sets realistic but constructive expectations.

Second, replace the MED philosophy with a "durable minimum dose" calibrated to the desired retention interval. Budget explicitly for desirable difficulties — spacing, interleaving, retrieval practice — as necessary "inefficiencies" that produce durable learning. The system should distinguish between performance during practice and actual learning (Soderstrom and Bjork, 2015).

Third, formalize Selection with data-driven methods. Corpus-based frequency analysis, prerequisite dependency graphs, and power-law verification replace intuitive 80/20 application. Expert validation is mandatory for novice learners; AI-assisted deconstruction serves as a scaffold, not a substitute.

Fourth, upgrade Sequencing from heuristics to instructional design science. The 4C/ID model's whole-task approach with fading scaffolding (g = 0.76), productive failure for conceptual building blocks (d = 0.36–0.58), and mastery gates between complexity levels provide a far more rigorous sequencing engine.

Fifth, build a layered motivation architecture replacing single-layer stakes. The seven layers are: identity foundation, process goals (d = 1.36), competence feedback, flow/deliberate practice alternation, relatedness through learning communities, plateau protocols, and strategic stakes only as a final layer for low-intrinsic-interest behaviors.

### Implementation scope and constraints

**The plugin is domain-agnostic.** It works for learning Spanish, guitar, negotiation, programming, pharmacology, wine tasting, swimming, chess, or anything else. The target skill is always a user input, never hardcoded.

**External tools handle persistence and heavy scheduling.** SRS review scheduling, flashcard study sessions, and persistent progress databases are not the plugin's job. The plugin generates high-quality exports (Anki-compatible decks, structured JSON, PDFs, Markdown) and provides effective conversational teaching and assessment.

**The data model targets Postgres / pgvector / Apache AGE.** All structured outputs should be compatible with this stack: AGE for the knowledge and dependency graphs (vertex/edge traversal, centrality, path operations), pgvector for embedding-based similarity search (transfer pathway identification, semantic matching), and standard Postgres for relational data (sessions, assessments, schedules, materials, learner profiles). The plugin currently stores data as JSON files within a Claude Project, using schemas that mirror the target database structure for direct portability.

**Training Conductor sessions are scoped to ~150k tokens** to prevent context loss during teaching. This constrains session design: the Conductor loads only what's needed for today's session, maintains graceful session boundaries, and writes state after each session rather than carrying full history.

**Output formats:** Anki .apkg packages, PDF reference materials, Markdown documents, structured JSON for all data artifacts, Mermaid/SVG visualizations, external resource lists.

---

## Full Architecture Sketch (v2)

The following is the complete current system architecture. The research gaps at the end of this document target the specific areas where practical design guidance is needed before implementation.

### Central Artifact: The Knowledge Graph

The system's most important data structure is a dual-layer knowledge graph that evolves throughout the learning engagement.

**Layer 1 — Skill Dependency Graph:** The territory to be learned. Nodes are skill components (concepts, techniques, sub-skills); edges are prerequisite, similarity, and reinforcement relationships. Produced by the Skill Researcher and identical for all learners targeting the same skill.

**Layer 2 — Learner State Overlay:** The learner's current knowledge mapped onto the skill graph. Each node carries a mastery state (unknown, exposed, developing, proficient, automatized) with timestamps, assessment evidence, and confidence scores. Produced by the Learner Calibrator and continuously updated by the Training Conductor and external data imports.

**The gap between these two layers *is* the curriculum.** The Curriculum Architect works from this gap — prioritizing the highest-impact unfilled nodes, leveraging existing knowledge as scaffolding, and identifying transfer pathways where prior experience accelerates acquisition.

**Data model:** AGE for native graph operations, pgvector for embedding similarity search (transfer pathways, analogies), Postgres for relational data. In the plugin context, stored as JSON mirroring these schemas.

### Component 1: Domain Assessor & Initial Learner Profile

Classifies the target skill (type, environment, Bloom's ceiling, modularity, tacit knowledge ratio) and gathers the learner's relevant background (related skills, adjacent experience, transferable frameworks, constraints, purpose/motivation). Selects the instructional approach and establishes the identity frame. For every skill + timeframe combination, produces both a short-term plan (what's achievable within the stated timeframe) and an extended roadmap (the path beyond). Framing is always constructive.

### Component 2: Skill Researcher

Deep investigation of the target skill. Runs simulated expert interviews using Ferriss' protocol via LLM + web search, applies the four deconstruction sub-techniques (Reduce, Interview, Reverse, Translate), identifies components with full classification (type, cognitive load, prerequisites, Bloom's level, embedding vector), runs frequency/impact analysis, builds the skill dependency graph (AGE-compatible), identifies transfer pathways using the initial learner profile and pgvector similarity search, and catalogs failure points, plateaus, and strategy transitions.

### Component 3: Learner Calibrator

The focused second pass. Takes the dependency graph and walks through it with the learner via adaptive diagnostic assessment, prioritizing gateway nodes and flagged transfer points. Produces the knowledge graph overlay (the gap map). Uses efficient questioning — broad first, drilling down where uncertain, skipping where clear. Computes total graph coverage, gap clusters, and transfer leverage. Can trigger additional targeted research if surprises emerge. Loops until the skill graph and learner overlay are stable enough for curriculum design.

### Component 4: Curriculum Architect

Works from the gap, not from scratch. Selection engine weights unfilled nodes by frequency × centrality × impact × (1 - mastery) × transfer_leverage. Sequencing engine synthesizes Elaboration Theory (epitome design), 4C/ID (task classes with sawtooth scaffolding, recurrent vs. non-recurrent distinction), Productive Failure (struggle-first for conceptual building blocks), mastery gates with delayed assessment, and interleaving with pre-framing. Transfer-leveraged sequencing starts with components where existing knowledge provides the strongest scaffold. Scheduling engine produces dual-timeline (short-term + extended), session architecture scoped to 150k token budget (flow warm-up → deliberate practice → flow integration), plateau pre-planning, overlearning budget, and SRS export schedule. Motivation architecture covers all seven layers.

### Component 5: Material Forge

Generates all learning materials as exportable artifacts. Material types: retrieval practice materials (Anki decks, self-testing protocols, interleaved practice sets), whole-task scenarios (simplified tasks, worked examples with fading, productive failure challenges), reference materials (prescriptive and practice one-pagers as PDF, dependency graph visualizations, curriculum roadmap, external resource lists), assessment instruments (diagnostic, mastery gate, delayed retention, transfer tasks, self-assessment rubrics), encoding aids (mnemonics, analogies to existing knowledge, visual organizers), and motivation/framing materials. All structured data uses schemas compatible with Postgres/pgvector/AGE.

### Component 6: Training Conductor

Ongoing adaptive teaching agent, operating within a 150k token session budget. Session loading protocol reads current state, identifies what's due (retrieval probes, new material, assessments), loads only relevant context. Core functions: session management (natural arc from open to close), adaptive teaching (Socratic questioning, scaffolded instruction, productive failure facilitation, deliberate practice coaching, interleaving management), assessment and knowledge graph updates (micro-assessment, mastery gates, delayed retention probes, writing updated mastery states after each session), difficulty calibration (ZPD targeting via observable conversational signals), external data integration (importing Anki stats, self-reports, and other structured inputs at session start), plateau detection and response, motivation management, and plan adaptation (authority to trigger upstream re-runs). State is written as structured JSON after each session.

### Component 7: Dashboard

A React artifact within the Claude Project serving as the learner's visual home base. Displays the knowledge graph with mastery overlay (nodes colored by state), curriculum roadmap with current position, key metrics (delayed retention, components mastered, transfer performance, calibration accuracy), session history, and upcoming agenda. Regenerated after sessions. Shows metrics reflecting actual learning, not just effort.

### Bidirectional Data Flow

Exports: Anki .apkg packages, structured JSON, PDFs, Markdown, Mermaid/SVG visualizations. Imports: Anki review history (mapped to graph nodes), self-reports, notes from external tools, any structured data with component references. Import processing maps external data to graph vertices (via component_id or pgvector similarity) and updates mastery states.

### Implementation: Skill Suite

An orchestrator meta-skill routes between seven individual skills (domain-assessor, skill-researcher, learner-calibrator, curriculum-architect, material-forge, training-conductor, dashboard-generator). A Claude Project holds persistent artifacts. JSON schemas mirror the target Postgres/pgvector/AGE structure.

---

## Research Gaps to Close

The architecture above is well-defined in structure but has ten specific gaps where practical, implementable design guidance is needed before building the plugin. For each gap, I need concrete details: templates, data models, dialogue patterns, prompt structures, schemas, and worked examples — not more theory.

---

### Gap 1: Learner Knowledge Assessment and Transfer Learning

This is the gap most critical to the system's differentiation. The Learner Calibrator needs to efficiently map a learner's existing knowledge onto the skill dependency graph, and the system needs to leverage that map for transfer learning. No existing meta-learning framework does this well.

**Research questions:**

How should diagnostic assessment be designed to efficiently map a learner's existing knowledge against a skill dependency graph? What does the literature on adaptive diagnostic testing (computerized adaptive testing, knowledge space theory, Bayesian knowledge tracing) say about efficient assessment strategies? How do systems like ALEKS or Knewton model student knowledge as a graph and assess it efficiently?

What is "knowledge space theory" (Doignon & Falmagne) and how does it formalize the relationship between a knowledge domain's structure and a learner's state within it? Is this the right theoretical foundation for the knowledge graph overlay concept?

How should transfer learning pathways be identified computationally? When a learner has skill A and wants to learn skill B, how do you find the components of B that are semantically similar to components of A? What role can embedding similarity (pgvector) play in this? Are there established methods from educational data mining for detecting and leveraging transfer?

What does the research say about how transfer actually works in practice? Under what conditions does prior knowledge genuinely accelerate new learning (positive transfer) vs. interfere with it (negative transfer)? How should the system detect and handle negative transfer risks — cases where the learner's existing mental models are actively counterproductive?

How should the diagnostic assessment be structured conversationally to feel engaging rather than tedious? What adaptive questioning strategies minimize assessment length while maximizing information gain? How many questions are typically needed to reach a useful confidence level for graph coverage estimation?

What's the optimal data model for the knowledge graph overlay? How should mastery states be represented (discrete categories vs. continuous probability estimates)? What metadata per node is essential for downstream curriculum design?

**Desired output:** A practical framework for rapid knowledge assessment against a dependency graph (including conversational question design principles, adaptive testing logic, and stopping criteria), a method for identifying and leveraging transfer pathways using embeddings, guidance on handling negative transfer, and a data model for the knowledge graph overlay that's compatible with AGE.

---

### Gap 2: Conversational Training Session Design Patterns

The Training Conductor runs teaching sessions through conversation within a 150k token budget. I need concrete dialogue templates, not tutoring theory.

**Research questions:**

What does effective AI-tutoring conversation look like structurally? What dialogue frameworks from intelligent tutoring systems research (AutoTutor's five-step dialogue frame, ICICLE, or other ITS models) map to a conversational LLM context? How do emerging LLM tutors (Khanmigo, Synthesis Tutor) structure their interactions?

How should the session architecture (flow warm-up → deliberate practice → flow integration) translate into conversational phases? What are the transition cues and dialogue moves for each phase boundary?

How should Socratic questioning work in practice for different learning modes? I need question sequences for: guiding concept discovery, correcting misconceptions without stating the answer directly, coaching procedural fluency, and facilitating productive failure with appropriate support.

What are the best practices for the "assistance dilemma" — when to hint vs. tell, how to scaffold without over-helping, and how to fade scaffolding as competence grows?

How should sessions handle skill types the AI can't directly observe (motor skills, physical performance, perceptual discrimination)?

Given the 150k token budget, what session duration and conversational density is realistic? How should the Conductor manage pacing to avoid running out of context during a critical teaching moment?

**Desired output:** Three to five concrete session templates showing conversational flow with example dialogue moves, branching logic (correct/partial/incorrect responses), phase transitions, and pacing estimates relative to the token budget. Templates should cover: concept introduction, retrieval practice/review, skill drilling with feedback, productive failure facilitation, and mastery gate assessment.

---

### Gap 3: Assessment Design for AI-Facilitated Learning

The system needs four distinct assessment types: diagnostic (for the Calibrator), mastery gate (for curriculum advancement), delayed retention (for measuring actual learning), and transfer (for testing generalization). All administered conversationally.

**Research questions:**

How should diagnostic assessment differ from mastery assessment in design and purpose? The Calibrator needs to efficiently classify existing knowledge across many nodes; mastery gates need to deeply verify competence at specific nodes. What item design principles apply to each?

What does mastery-based assessment look like in intelligent tutoring systems? What criteria determine "mastery" for different Bloom's levels? What accuracy thresholds and item counts are standard?

How do you operationalize "delayed" assessment in a conversational context where the user controls session timing? What's the minimum meaningful delay? How should the system request delayed testing naturally?

What are effective transfer task designs? How do you create near-transfer (same structure, different surface) vs. far-transfer (different structure, requires abstraction) problems? When is each appropriate in a learning progression?

How do you prevent assessment gaming when the same AI is teacher and assessor? Can item generation vary surface features while holding deep structure constant?

How should self-assessment and metacognitive calibration training work? Can asking learners to predict their performance before testing, then comparing prediction to result, improve their calibration accuracy over time?

How should assessment results be structured for both the knowledge graph overlay (AGE vertex properties) and the relational layer (Postgres assessment records)?

**Desired output:** Assessment design templates for each type (diagnostic, mastery gate, delayed retention, transfer), item design guidelines per Bloom's level, scoring approaches, a conversational administration framework, and a data schema for assessment results compatible with both AGE and Postgres.

---

### Gap 4: SRS Card Design and Export Architecture

The plugin generates spaced repetition materials as a primary deliverable. The scheduling lives in Anki or a downstream app; the plugin's job is to produce excellent cards and clean exports.

**Research questions:**

What makes an excellent SRS card that produces durable learning vs. a mediocre card that produces shallow recognition? What are Andy Matuschak's key principles for effective spaced repetition prompts? How does Michael Nielsen's approach to using SRS for deep understanding (not just fact recall) translate to automated card generation?

What are the established anti-patterns? Cards that are too complex, test recognition instead of recall, have ambiguous answers, create "illusions of knowing," or violate the "one card, one idea" principle.

What card types (basic, cloze, reversed, open-ended) work best for which kinds of knowledge (factual, conceptual, procedural, pattern recognition, vocabulary)?

What metadata should each card carry for effective organization? Consider: component_id (AGE vertex reference), topic tags, difficulty estimate, Bloom's level, card type, curriculum position, creation date. What schema serves both Anki export and Postgres storage?

What are the practical requirements for generating Anki-compatible .apkg files? What Python libraries (genanki, etc.) work? What are the gotchas?

How should in-conversation retrieval probes relate to the exported card deck? Same items, or deliberately different for transfer testing?

**Desired output:** Card design guide (principles, anti-patterns, type-specific templates), a portable data model for cards compatible with both Anki export and Postgres/AGE storage, and practical guidance on Anki export generation in Python.

---

### Gap 5: Material Generation — Prompt Engineering and Quality Standards

The Material Forge's output quality is make-or-break for the system. I need generative prompt patterns and quality rubrics for each material type.

**Research questions:**

**Worked examples with fading:** What are the 4C/ID design principles for deciding which steps to fade first and how quickly? How does this translate into a generative prompt for an arbitrary skill component?

**Productive failure scenarios:** Kapur's design conditions require activating prior knowledge, affording multiple solution paths, appropriate challenge level, and post-struggle instruction. How do you encode these as prompt constraints?

**Interleaved practice sets:** How do you select items for interleaving, set the old-to-new ratio, and sequence to maximize desirable difficulty without overwhelming the learner?

**Reference one-pagers:** What makes a reference sheet people actually use vs. one that gets forgotten? Layout and structure principles for PDF export.

**Scenario-based materials for social/tacit skills:** Design principles from simulation-based learning for AI-mediated role-play. What makes a scenario that develops judgment vs. one that teaches scripts?

**Dependency graph visualization:** What representation (Mermaid, SVG, structured outline) most helps learners orient in the curriculum?

**Desired output:** Prompt templates and quality rubrics for each material type, with at least one concrete worked example per type showing what "good" looks like.

---

### Gap 6: Adaptive Difficulty Calibration in Conversation

The Training Conductor targets the Zone of Proximal Development through conversational signals.

**Research questions:**

What observable conversational signals indicate learner ability relative to material difficulty? Consider: correctness, elaboration depth, ability to explain reasoning, unprompted connections, help requests, hedging language, transfer ability.

What do ITS systems (Cognitive Tutor, AutoTutor, ALEKS) use for real-time ability estimation? What algorithms or heuristics balance responsiveness against stability?

What concrete adjustment levers are available conversationally? When too easy: reduce scaffolding, increase interleaving, raise Bloom's level, add productive failure. When too hard: add worked examples, reduce complexity, return to blocked practice, provide analogies to existing knowledge (from the knowledge graph). What decision logic selects the right lever?

Is the "85% accuracy sweet spot" well-supported? Does optimal error rate vary by skill type or learning phase?

How should adaptive difficulty interact with curriculum progression? When to push through productive discomfort vs. consolidate?

**Desired output:** A practical calibration framework with observable signals, adjustment decision logic, target performance ranges, and guidelines for balancing adaptation against progression.

---

### Gap 7: Domain-Specific Adaptation Patterns

The system must behave differently for different skill types. I need concrete adaptation rules for each classification, not just general principles.

**Research questions:**

**Motor skills** (instrument, sport, cooking, drawing): How does AI instruction work without observing physical performance? Verbal coaching strategies? Role of video reference, self-description, outcome-based feedback? How do Fitts and Posner's stages change the system's behavior? What should the Material Forge produce differently?

**Language learning** (any language): Most effective AI-tutoring approaches? Balancing comprehensible input, communicative practice, grammar, and vocabulary? How does the Deconstruction Dozen generalize to non-Indo-European languages (tonal, SOV, non-Latin script, agglutinative)? Best SRS card designs per sub-skill?

**Cognitive/analytical skills** (programming, math, writing): How do worked examples, productive failure, and 4C/ID whole-task approaches apply concretely? What counts as a "simplified whole task" at each complexity level?

**Perceptual skills** (wine, medical imaging, ear training): Categorical framework construction in practice? Exposure volume requirements? How can AI facilitate perceptual learning without sharing the sensory experience?

**Social/tacit skills** (negotiation, leadership, therapy): Observation-practice-debrief via AI? Effectiveness of AI role-play? Handling wicked-environment dynamics and high tacit knowledge ratios?

**Desired output:** An adaptation matrix showing how each system component changes by skill type. One detailed worked example per type tracing a specific skill through the full pipeline: classical guitar (motor), Mandarin (language), Python programming (cognitive), wine tasting (perceptual), negotiation (social).

---

### Gap 8: Progress Data Model and Knowledge Graph Evolution

The knowledge graph is the system's central artifact. It needs a well-defined schema, evolution rules, and a way to be communicated to the learner that's both honest and motivating.

**Research questions:**

What metrics matter for learning progress? Accuracy over time, delayed retention (the strongest signal), transfer performance, time-to-mastery per component, practice consistency, self-assessment calibration accuracy, graph coverage and velocity, plateau/breakthrough events. Which are measurable through conversation alone vs. requiring external tool data?

How should the knowledge graph overlay evolve over time? What are the rules for state transitions (unknown → exposed → developing → proficient → automatized)? How does mastery decay without practice? What refresh schedule prevents skill atrophy? Should the system model decay explicitly using something like FSRS's stability/retrievability model at the graph level?

How should progress be communicated to be motivating without creating illusions? The research warns against streaks and hours as primary metrics. What works instead? How do you present the performance-learning distinction honestly without demoralizing?

What's the complete data schema for the knowledge graph overlay, session logs, and assessment history — designed for AGE (graph) + Postgres (relational) + pgvector (embeddings)? Include all entities, relationships, and computed views.

How should the Training Conductor summarize progress conversationally? What framing sustains motivation while maintaining accuracy?

What analytics approaches from Duolingo, Khan Academy, Anki, or adaptive platforms should we learn from? Which should we avoid (gamification rewarding activity over learning, streaks punishing rest, false mastery signals)?

**Desired output:** Complete data schema for the knowledge graph and progress system (AGE vertices/edges + Postgres tables + pgvector indices), state transition rules, mastery decay model, progress reporting guidelines, and anti-patterns.

---

### Gap 9: Bidirectional Data Integration

The system imports data from Anki, Obsidian, self-reports, and other tools, and exports structured data those tools can consume. The integration layer needs clear schemas and processing logic.

**Research questions:**

What does Anki review data look like structurally? What fields does a review record contain (card ID, timestamp, rating, interval, ease factor)? How should these be mapped to knowledge graph node updates? What's the confidence model — how many reviews are needed before the system trusts a retention estimate?

How should unstructured imports (Obsidian notes, free-text self-reports) be processed into knowledge graph updates? Can pgvector embedding similarity match unstructured text to graph nodes? What confidence threshold should be required before updating mastery states from unstructured input?

What export schemas does Anki expect for .apkg import? What are the practical requirements and Python tooling (genanki)? How should card metadata (component_id, tags, difficulty) survive the round-trip through Anki and back?

How should the import/export cycle work end-to-end? User exports Anki deck from the plugin → studies in Anki → exports review history → imports back into the plugin → knowledge graph updates → next session is informed by Anki performance. What's the data flow at each step?

What schema should self-report imports follow? If a learner practices guitar for an hour and wants to report results, what structured format captures useful information (component practiced, duration, self-assessed quality, specific observations)?

How should the system handle conflicting signals — e.g., the learner reports feeling confident about a skill but Anki retention data shows poor recall? Which source should be weighted more heavily?

**Desired output:** Import/export schemas for each data source (Anki, Obsidian/notes, self-reports), processing logic for mapping external data to knowledge graph updates, a confidence model for external data integration, and a practical end-to-end data flow diagram for the Anki round-trip.

---

### Gap 10: Prompt Architecture for the Plugin Components

Each component is a Claude skill powered by a system prompt. These prompts need to encode complex pedagogical behavior reliably.

**Research questions:**

What are the best practices for AI tutoring system prompts? How do existing LLM education projects (Khanmigo, Synthesis Tutor, Duolingo Max) structure their prompts? What instructor persona elements produce the best outcomes?

The Training Conductor is the most complex component. How should its prompt be structured for consistent pedagogical behavior across many sessions while adapting to the learner? What should be hard rules vs. flexible heuristics? How much theory belongs in the prompt vs. being distilled into behavioral instructions?

What are the known failure modes of "AI as tutor" — being too agreeable, over-scaffolding, generating incorrect domain content, losing pedagogical focus during long dialogue, defaulting to lecture mode, failing to push back on overconfidence, inconsistent expectations across sessions — and how should prompts guard against each?

How should the Skill Researcher's prompt produce reliable skill decompositions for domains where LLM knowledge may be shallow? What patterns (chain-of-thought, multi-pass, self-critique) produce the best results?

How should the Curriculum Architect's prompt encode 4C/ID, Elaboration Theory, and Productive Failure as actionable generation instructions? As procedures, constraint lists, examples to emulate, or a combination?

How should the Material Forge's prompt self-check quality? Can the generating prompt include evaluation criteria applied before finalizing?

How should the orchestrator's prompt handle routing between seven components, managing state, handling calibration loops, and maintaining coherence across a multi-session engagement?

Given the 150k token session constraint, how should the Training Conductor's prompt be structured for token efficiency? What context is essential to load vs. what can be omitted?

**Desired output:** Structural guidelines for each component's prompt, failure-mode guardrails, recommended patterns, and a skeleton orchestrator prompt showing routing logic and state management. Include concrete prompt fragments where possible.

---

## Desired Overall Output

For each of the 10 gaps, provide:

**Research synthesis** — What does the evidence and practical experience say? Key findings, researchers, papers, and existing implementations.

**Practical design guidance** — Specific, concrete, implementable recommendations. Enough detail to write prompts, design schemas, and build workflows.

**Templates or examples** — Actual templates, data models, dialogue examples, prompt skeletons, or worked examples wherever possible.

**Unresolved tensions** — Any remaining trade-offs that require judgment calls during implementation.

The goal is to have enough practical detail after this research round to move directly into building the plugin — writing the actual skills, prompts, export generators, data schemas, and workflow logic.
