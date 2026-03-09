# Closing implementation gaps for a meta-learning plugin system

The ten research gaps between architectural sketch and working code each have well-established solutions in the literature. **Knowledge Space Theory provides the ideal theoretical backbone for the dual-layer knowledge graph**, Bayesian Knowledge Tracing solves the assessment-to-mastery inference problem, FSRS's DSR model handles memory decay, and AutoTutor's dialogue framework maps cleanly to LLM-based conversational tutoring. What follows is the practical detail needed to write prompts, schemas, and workflows.

---

## Gap 1: Rapid knowledge assessment via graph-propagated adaptive testing

**Knowledge Space Theory (Doignon & Falmagne, 1985) is the correct theoretical foundation** for the dual-layer architecture. KST models a domain as a finite set of skills Q, where each *knowledge state* is a feasible subset of Q a learner has mastered. The collection of all feasible states forms a *knowledge structure* constrained by prerequisite relationships. This maps directly to the proposed design: AGE graph vertices encode skills, PREREQUISITE edges encode the surmise relation, and the learner overlay records which state the learner occupies.

ALEKS, the primary commercial implementation of KST, uses this structure to assess ~4–5 million students per year across domains of 350–500 skills. Its key insight is partitioning the skill graph into subdomains, running parallel assessments on projected knowledge spaces, and transferring information across projections. Initial assessments require **≤30 open-response questions** (recently 15–20 for younger learners) because graph propagation dramatically reduces the number of questions needed — if a student demonstrates mastery of a downstream skill, prerequisites are inferred as mastered; failure on a skill implies dependents are likely unknown.

### Diagnostic assessment algorithm

The conversational diagnostic uses three acceleration mechanisms to minimize assessment length:

**Graph propagation** reduces questions by 40–60%. When a learner demonstrates mastery on skill S, all prerequisites of S receive an upward Bayesian update. When they fail, all dependents receive a downward update. This is the single largest efficiency gain.

**Embedding-cluster inference** via pgvector allows the system to infer mastery of unassessed skills that have cosine similarity >0.85 to assessed skills. If three assessed skills in a semantic cluster all show mastery, remaining cluster members can be tentatively marked as mastered with a confidence penalty.

**Information-theoretic item selection** picks the next question to maximize entropy reduction across the entire graph, weighted by downstream impact (skills with many dependents are assessed first).

```
ALGORITHM: ConversationalDiagnosticAssessment
INITIALIZE: P_mastery[s] = population_base_rate(s) for all skills
LOOP (max 20 questions OR max uncertainty < 0.15):
  1. SELECT skill with highest info_gain = entropy(s) × (1 + 0.3 × downstream_count)
  2. GENERATE open-ended diagnostic question via LLM
  3. EVALUATE response: {mastered: 1.0, partial: 0.5, misconception: 0.1, none: 0.0}
  4. BAYESIAN UPDATE using BKT: P_mastery[s] ← P(correct|mastered) × P_mastery[s] / evidence
  5. PROPAGATE: mastery up through prerequisites, non-mastery down through dependents
  6. CLUSTER INFER: for unassessed skills with similar_assessed cosine > 0.85, estimate mastery
RETURN: knowledge_state map
```

### Transfer pathway identification using embeddings

Generate embeddings for each skill node from its description, learning objectives, and example problems. Store in pgvector. Transfer candidates are skill pairs with **content embedding similarity >0.65 but <0.95** (identical skills excluded) that are NOT already connected by prerequisite edges.

| Cosine Similarity | Transfer Type | System Action |
|---|---|---|
| 0.90–0.95 | Near transfer | Auto-boost mastery estimate for target |
| 0.75–0.90 | Moderate | Suggest accelerated learning path |
| 0.65–0.75 | Far transfer | Probe with targeted question before adjusting |

**Negative transfer detection** requires a second signal: when *content* similarity is high (>0.7) but *procedure* similarity is low (<0.5), the skills look alike but require different approaches — the classic interference pattern. Mitigation: explicit contrast instruction ("You learned X works for context A. Here's why it doesn't apply to context B"), interleaved practice mixing both skill types, and pre-teaching common errors before they occur.

### Knowledge graph overlay data model

Use **continuous probabilities as primary** with discrete categories derived for human-readable reporting:

```cypher
-- Learner-Skill overlay edge in Apache AGE
CREATE (l:Learner)-[:HAS_MASTERY {
  mastery_probability: 0.82,       -- continuous 0.0–1.0 (primary measure)
  mastery_category: 'proficient',  -- derived: novice(<0.25)|developing|proficient|mastered(>0.85)
  confidence: 0.88,                -- certainty of estimate
  evidence_count: 7,
  last_assessed: timestamp,
  decay_factor: 0.02,              -- forgetting rate per day
  p_transit: 0.15,                 -- BKT learning rate
  p_slip: 0.08,                    -- error despite mastery
  p_guess: 0.12,                   -- correct despite non-mastery
  transfer_boost: 0.05             -- mastery attributed to transfer
}]->(s:Skill)
```

**Unresolved tensions**: Graph propagation can cause runaway inference — one strong performance on an advanced skill can incorrectly mark many prerequisites as mastered. A dampening factor (0.7× per hop) and periodic direct verification of inferred states are necessary. The optimal balance between assessment efficiency and accuracy is domain-dependent.

---

## Gap 2: Five conversational session templates with dialogue architecture

AutoTutor's five-step Expectation-Misconception Tailored (EMT) dialogue provides the structural foundation: pose question → student attempts → qualitative feedback → collaborative improvement cycle → verify and summarize. The key insight is the **pump→hint→prompt→assertion escalation ladder**, representing decreasing student agency and increasing tutor information-giving. Modern LLM tutors (Khanmigo) translate this into a prompt-level policy rather than pre-authored dialogue trees — the system prompt encodes "never give answers, always ask questions" and the LLM generates contextually appropriate dialogue moves.

### Session phase architecture

| Phase | % of Session | Dialogue Character |
|---|---|---|
| Warm-up | 8–15% | Low-stakes retrieval, rapport |
| Instruction/Modeling | 15–25% | "I do, you watch" → "I do, you help" |
| Guided Practice | 25–35% | "You do, I help" — EMT dialogue cycles |
| Independent Practice | 20–30% | Minimal intervention, on-demand hints |
| Wrap-up/Assessment | 8–15% | Formative check, recap, preview |

The **assistance dilemma** (Koedinger & Aleven, 2007) governs transitions: start each topic with higher assistance (worked examples, assertions) and programmatically fade to lower assistance (pumps only) as the learner demonstrates coverage of expectations. The operationalized decision rule: attempt 0 → pump; attempt 1 incorrect → hint; attempt 2 incorrect → prompt; attempt 3 incorrect → assertion + new attempt; misconception detected → immediate correction.

### Template A: Concept introduction (~7,000 tokens)

Phases: Activation (3–4 turns) → Elicit Preconceptions (3–5 turns) → Guided Discovery (8–12 turns) → Consolidation (3–4 turns). Example for Newton's Third Law:

> **TUTOR** [Pump]: "Imagine a car and truck collide head-on. Which experiences the greater impact force?"
> **STUDENT**: "The car — it's smaller."
> **TUTOR** [Hint]: "When the car pushes on the truck, does the truck push back? How would you compare those pushes?"
> **STUDENT**: "The truck pushes back harder because it's bigger?"
> **TUTOR** [Correction + Prompt]: "Newton's Third Law says interaction forces come in pairs with _____ magnitude. Can you fill in that blank?"
> **STUDENT**: "Equal magnitude?"
> **TUTOR** [Positive + Transfer]: "Exactly. Equal magnitude, opposite direction. The *accelerations* differ because the car has less mass. If you push against a wall, what can you say about the force the wall exerts on your hand?"

Branching: if correct preconception → skip to acceleration difference; if misconception M1 ("bigger = more force") → trigger correction sequence; if all expectations covered → consolidation.

### Template B: Retrieval practice/review (~5,800 tokens)

Phases: Cued Recall (4–6 turns) → Elaborative Retrieval (4–6 turns) → Interleaved Application (4–6 turns) → Confidence Calibration (2–3 turns). Opens with open recall, pushes into "why" questions, then presents novel scenario requiring transfer. Ends with 1–5 confidence calibration check. If recall <50% of expectations → switch to re-teach (Template A).

### Template C: Skill drilling with feedback (~9,700 tokens)

Phases: Worked Example (3–4 turns) → Guided Drill with 3–5 problems (10–16 turns) → Independent Drill with 3–5 problems (8–12 turns) → Error Analysis (2–4 turns). Scaffolding fades within the session: problems 1–2 get full guidance, 3–4 get on-demand hints only, 5+ get answer verification only. The **expertise reversal effect** demands this fading — assistance that helps novices actively hurts experts.

### Template D: Productive failure facilitation (~9,200 tokens)

Phases: Problem Presentation (2–3 turns) → Generation & Exploration with **minimal guidance** (8–12 turns) → Impasse Recognition (3–4 turns) → Consolidation via direct instruction (5–8 turns) → Transfer (3–4 turns). The critical design constraint: during the Generation phase, the tutor must resist correcting or hinting toward the canonical solution. Only pumps are permitted. Kapur's meta-analysis shows d=0.36 for conceptual understanding when design fidelity is maintained.

### Template E: Mastery gate assessment (~3,400 tokens)

The most token-efficient template. Three criteria: Cold Recall (open question, no scaffolding) → Application Under Novelty (new problem, no hints) → Explain-to-Teach ("explain to a confused friend"). Pass all three → advance. Fail recall only → route to Template B. Fail application → route to Template A. Fail two+ → full re-teach cycle A→C→B→E.

### Token budget management

With **150k tokens**, a typical exchange uses ~300 tokens (student ~100 + tutor ~200). Raw capacity is ~330 exchanges, but practical limit is **~200 exchanges** due to context degradation for information buried in long contexts. Compressing each completed phase into a structured summary (~200 tokens replacing ~2,000 tokens of raw dialogue) saves ~80% per phase. With compaction, the budget supports **10–20 tutoring sessions** or **3–6 hours of continuous instruction**. Mastery gates (Template E at ~3,400 tokens each) should be scheduled frequently as cheap but high-value diagnostic checkpoints.

---

## Gap 3: Assessment architecture across four types

### Four assessment types with distinct design principles

**Diagnostic assessment** maps existing knowledge before instruction. Design for breadth: 3–5 items per knowledge component at varying difficulty, low-stakes framing, adaptive item selection. Output is a knowledge state map classifying each KC as mastered (≥80% on 3+ items), partially known (40–79%), or unknown (<40%).

**Mastery gate assessment** confirms learning before progression. Design for depth: minimum 3 items per KC (5+ preferred), items at or one Bloom level above the taught level, varied surface features. Three mastery criteria options: BKT P(Ln) ≥ 0.95 (Corbett & Anderson), streak of 3+ consecutive correct (ASSISTments), or ≥85% on 5+ items. Failure triggers targeted corrective instruction and retest with new items, maximum 3 attempts.

**Delayed retention assessment** verifies long-term memory via spaced retrieval. Schedule at 1–3 days, 7–14 days, and 30+ days after mastery. The optimal spacing gap is approximately **10–20% of the desired retention interval** (Cepeda et al., 2008). No hints or scaffolding — pure retrieval. Items vary surface features from original instruction.

**Transfer assessment** tests application in novel contexts. Administer after mastery plus at least one successful retention check. Near transfer first (same principle, slightly different context), then far transfer (same principle, significantly different domain). Design method: identify deep structure, list surface features of instruction, systematically vary domain/objects/context while holding relational structure constant.

### Mastery criteria by Bloom's level

| Level | Item Type | Threshold | Items Needed |
|---|---|---|---|
| Remember | Recall, matching, fill-in-blank | 90–95% | 3–5 |
| Understand | Explain in own words, classify | 85–90% with rubric | 3–5 |
| Apply | Solve novel problems | 85% | 3+ varied |
| Analyze | Compare, find patterns | 80% with rubric | 3+ cases |
| Evaluate | Judge, critique | 75–80% rubric-scored | 2–3 |
| Create | Design, produce | Holistic rubric | Portfolio |

### Anti-gaming strategies

The greatest risk in an AI tutor-assessor dual role is that students learn to "speak the language" of the AI rather than genuinely learning. Key mitigations: **procedural content generation** (AI generates structurally equivalent problems with randomized surface features each time), **explanation requirements** (cannot game a free-form explanation as easily as multiple choice), **unpredictable assessment timing**, **delayed mastery confirmation** (even after passing a gate, require at least one delayed retention check), and **cross-KC consistency checks** (mastery on advanced skills but failure on prerequisites triggers diagnostic review).

### Assessment data schema

```sql
CREATE TABLE assessment_items (
  item_id UUID PRIMARY KEY,
  session_id UUID REFERENCES assessment_sessions,
  knowledge_component_id UUID,
  bloom_level VARCHAR(15),
  item_type VARCHAR(20),        -- recall, explain, apply, analyze, near_transfer, far_transfer
  score_binary BOOLEAN,
  score_partial DECIMAL(5,4),
  confidence_pre SMALLINT,      -- 1-5 self-rated before answering
  response_time_ms INTEGER,
  surface_features JSONB,       -- for tracking variation
  deep_structure_id UUID,       -- links structurally equivalent items
  gaming_flag BOOLEAN DEFAULT FALSE
);
```

AGE vertex properties on LearnerState nodes carry: `p_know`, `mastery_status` (unknown|learning|mastered|retained|transferred), `last_assessed_at`, `retention_strength`, `next_review_date`, `avg_calibration_bias`.

---

## Gap 4: SRS card design from Matuschak to .apkg export

### Card design principles

Andy Matuschak's five principles for effective retrieval prompts: **focused** (one detail per card), **precise** (specific question, unambiguous answer), **consistent** (lights the same mental "bulbs" each time), **tractable** (~90% target accuracy), and **effortful** (genuine retrieval, not pattern matching). His deeper insight: prompt design is task design — you're giving your future self a recurring cognitive task.

Michael Nielsen uses SRS to "see through" mathematics by atomizing proofs into finest-grained components and encoding ideas from multiple angles. The SRS format provides *pressure* to decompose ideas into atoms. Most value comes from the decomposition process itself.

Wozniak's 20 rules prioritize: do not learn what you don't understand, build upon basics, stick to the **minimum information principle** (simple cards = reliable memory; complex cards = multiple failure points), and use cloze deletion generously.

### Critical anti-patterns

- **Kitchen Sink cards**: "Describe X" with paragraph answers → split into atomic sub-questions
- **Ambiguous cloze**: Multiple valid completions → add disambiguating context
- **Yes/No cards**: 50% guess rate, no effortful retrieval → convert to production format
- **Shopping lists**: "List the 7 layers of OSI" → individual cards per layer with function
- **Pattern matching**: Recognizing surrounding text rather than retrieving concept → rephrase in own words, test from multiple angles

### Card type selection by knowledge type

Basic Q→A cards serve facts and definitions (Remember level). Cloze deletion works for terminology in context (Remember/Understand). Reversed cards suit bidirectional associations like vocabulary. Open-ended/generative prompts target Apply through Create levels — they produce different answers each time but are harder to self-grade. **Comparison cards** combat interference between confusable concepts (Analyze level).

### Portable data model

```sql
CREATE TABLE srs_cards (
  card_id UUID PRIMARY KEY,
  component_id TEXT NOT NULL,       -- AGE vertex reference
  card_type TEXT NOT NULL,          -- basic|cloze|reversed|open_ended
  front TEXT NOT NULL,
  back TEXT NOT NULL,
  bloom_level TEXT NOT NULL,
  knowledge_type TEXT NOT NULL,     -- fact|concept|procedure|principle|mental_model
  topic_tags TEXT[] NOT NULL,       -- hierarchical: ["graph-theory::traversal::bfs"]
  difficulty_estimate NUMERIC(3,2),
  curriculum_position INTEGER,
  source_type TEXT DEFAULT 'curriculum',
  ease_factor NUMERIC(4,2) DEFAULT 2.50,
  interval_days INTEGER DEFAULT 0,
  next_review DATE,
  lapses INTEGER DEFAULT 0
);
```

### Anki .apkg generation with genanki

Key implementation details: Model and Deck IDs **must be hardcoded** (generate once with `random.randrange(1 << 30, 1 << 31)`) — changing IDs creates duplicates on re-import. Override the GUID property with `genanki.guid_for(card_id)` to enable deterministic re-imports. Fields are HTML (escape literal `<`, `>`, `&`). Cloze models require `model_type=genanki.Model.CLOZE` and at least 2 fields. Use `::` separator for subdeck hierarchy. The `.apkg` file is a ZIP containing a SQLite database (`collection.anki2`) plus a `media` JSON mapping.

### In-conversation retrieval probes

Probes **supplement, don't replace** SRS review. In-conversation probes provide initial encoding and active learning during teaching; exported SRS cards provide durable long-term retention via optimized spacing. Each probe should correspond to an exportable card (shared `card_id`). Probe timing within conversation: after explaining a concept, wait 2–5 exchanges before testing (micro-spacing), interleave probes from earlier in the session, and end sessions with a cumulative mini-quiz covering 3–5 key concepts.

---

## Gap 5: Material generation prompts and quality rubrics

### Worked examples with backward fading

The 4C/ID model (van Merriënboer) prescribes a **sawtooth support pattern**: within each task class, the first task has maximum support (fully worked) and the last has none (full independence). Support resets when difficulty increases at a new task class. **Backward fading** — removing the last solution step first, then progressively earlier steps — outperformed forward fading on both near and far transfer (Renkl, Atkinson, Maier & Staley, 2002). Each faded step should include a self-explanation prompt.

Fading pace by learner level: novice = 1 step every 2 problems (slow); intermediate = 1 step per problem (standard); advanced = 2 steps per problem (fast). For a 5-step procedure, novices need ~11 problems to reach full independence; intermediates need ~6.

### Productive failure scenario design

Kapur's four design conditions: the problem must activate prior knowledge, afford multiple solution paths (students should naturally generate 3–5 different approaches), present appropriate challenge without frustration, and be followed by consolidation instruction that bridges student attempts to the canonical solution. The critical constraint: **during the generation phase, no scaffolding or correction is permitted**. The meta-analysis (Sinha & Kapur, 2021) shows d=0.36 for conceptual understanding, rising to d=0.58 with high design fidelity.

### Interleaved practice design

Interleaving forces **strategy choice** (not just execution), improving discriminability between problem types. Effect sizes are large: Taylor & Rohrer (2010) found d=1.21. The recommended composition: **25% current topic, 75% review** (weight recent topics more). No two consecutive problems should use the same strategy. Include at least one pair of problems with similar surface features but different deep structure. The interleaving benefit is strongest after delay — at 30 days, interleaved practice showed 74% accuracy vs. 42% for blocked practice.

### Dependency graph visualization

**Mermaid flowcharts** are the optimal format: text-based (LLM-generatable, version-controllable), widely rendered (GitHub, Obsidian), with CSS class support for status styling. Use `flowchart TD` for prerequisite trees with subgraphs for module grouping. Color-code by mastery status: green=mastered, yellow=in-progress, gray=not-started, dashed=locked. Include Unicode progress bars in node labels and emoji status indicators. Limit to ≤20 nodes per diagram; split larger graphs into module views.

### Quality self-check rubric for Material Forge

Every generated material should pass four checks before presentation: **Accuracy** (all factual claims verifiable, math/logic verified step-by-step), **Difficulty calibration** (matches target level, prerequisites within learner's demonstrated knowledge), **Pedagogical quality** (builds on prior concepts, includes active engagement opportunity, avoids unnecessary jargon), and a **Red-team pass** (could a learner misinterpret this? Does it inadvertently teach a misconception?). If any accuracy check fails, regenerate. If average quality score <3/5, regenerate with specific improvements.

---

## Gap 6: Adaptive difficulty calibration through conversational signals

### Observable signal taxonomy

**High-reliability signals**: response correctness (rolling 5-question window), error pattern classification (systematic = misconception, random = slip), transfer and connection signals (unprompted analogies, cross-topic references), question quality (recall-level → comprehension → application → metacognitive).

**Medium-high reliability**: elaboration depth (unprompted elaboration is a strong mastery indicator), hedging vs. confidence language ("I think maybe..." vs. "Because X, therefore Y"), help-seeking quality (specific questions indicate partial understanding; vague "I don't get it" indicates confusion).

**Medium reliability**: response latency (requires individual baseline calibration), affective signals (frustration markers, boredom indicators), engagement quality. AutoTutor research (Graesser et al., 2007) detected learning-relevant affective states from conversational cues at 69–78% accuracy.

### The 85% rule: strong for perceptual learning, use with caution elsewhere

Wilson et al. (2019, Nature Communications) derived mathematically that for **binary classification tasks** under stochastic gradient descent, the optimal error rate is **15.87%** (~85% accuracy). However, Wilson explicitly cautioned against overgeneralizing: the result was derived for two-choice categorization tasks, primarily tested on machine learning algorithms, and "mostly likely applies to perceptual learning." Other researchers found optimal success ranges of **60–83%** for different task structures. The optimal rate varies by learning phase: initial exposure benefits from 90–95% accuracy (confidence building), guided practice from 80–90%, independent practice from 75–85% (the sweet spot zone), and transfer tasks naturally run lower at 60–75%.

### Calibration decision logic

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

**Distinguishing temporary struggle from fundamental gaps**: Temporary struggle shows improving accuracy across a window, inconsistent errors, maintained engagement, and increasingly specific help requests. Fundamental gaps show flat/declining accuracy over 5+ attempts, systematic repeated errors, inability to explain reasoning, and prerequisite concepts also shaky when probed. For temporary struggle → maintain difficulty with increased scaffolding. For fundamental gaps → regress to prerequisites.

**Preventing over-correction**: Require a minimum observation window (never adjust on single responses), use hysteresis (sustained evidence before significant changes), and offer student choice when the system is uncertain.

---

## Gap 7: How each system component adapts across five skill types

### The adaptation matrix

The system's seven components require fundamentally different configurations depending on whether the target skill is motor, linguistic, cognitive, perceptual, or social. **The AI's comparative advantage is strongest for cognitive skills** (infinite practice, immediate code verification, Socratic dialogue) and weakest for perceptual skills (cannot provide sensory stimuli). Motor and perceptual domains require the AI to function primarily as a **coach-between-sessions** that structures, motivates, and debriefs real-world practice rather than providing the experience itself.

**Training Conductor adaptations** are the most dramatic: for cognitive skills (Python), the Conductor runs Socratic dialogue with immediate code verification; for motor skills (guitar), it provides external-focus verbal cues and runs a Perform-Report-Refine self-description loop; for language (Mandarin), it simulates text conversations and drills grammar/characters but must recommend external audio tools for pronunciation; for perceptual skills (wine), it structures real-world tasting exercises and debriefs experiences; for social skills (negotiation), it runs AI role-play with coaching pauses and post-simulation structured debriefs.

**Material Forge adaptations**: Cognitive skills get worked examples, faded examples, Parsons problems, and bug-hunting exercises. Motor skills get practice routines with external-focus cues, self-assessment checklists, and troubleshooting guides. Language learning gets graded reading passages, character decomposition mnemonics, grammar drills, and tone-pair practice. Perceptual skills get comparative tasting protocols, vocabulary-building cards tied to standardized frameworks (Noble's wine aroma wheel), and descriptive scenario quizzes. Social skills get case briefs, BATNA worksheets, role-play scenarios with AI persona definitions, and debrief questionnaires.

### Key cross-cutting principles

**External focus of attention** (Wulf, 2013) applies across motor and perceptual domains: direct learner attention to outcomes/effects ("focus on the sound ringing") rather than body mechanics ("curl your fingers this way"). **4C/ID's whole-task approach** applies universally — always start with a complete (if simplified) version of the skill. **Verbal overshadowing** (Melcher & Schooler, 1996) is a unique risk for perceptual skills: intermediate learners who develop vocabulary without corresponding perceptual exposure perform *worse* at perceptual tasks. The system must co-develop vocabulary and perceptual expertise in parallel.

### Worked example: Python programming (strongest fit)

The Skill Researcher decomposes Python into constituent skills per 4C/ID, distinguishing recurrent (syntax → automate) from non-recurrent (design → elaborate). The Calibrator administers code output prediction, bug identification, and Parsons problems directly through text. The Curriculum Architect creates four task classes: TC1 (worked examples dominant — modify a working calculator), TC2 (completion problems — fill in function bodies), TC3 (conventional problems — write from scratch), TC4 (design problems — multi-file projects). Productive failure is inserted at class transitions: "Try to write a sorting algorithm before we learn any." The Conductor runs Socratic dialogue, can execute submitted code and show output, and guides discovery through targeted questions rather than giving answers directly.

### Worked example: Classical guitar (most challenging fit)

The Conductor runs practice sessions via text dialogue, providing external-focus cues ("imagine the sound projecting to a listener 3 meters away") and using a Perform-Report-Refine loop: student performs offline, reports outcomes and sensations, AI diagnoses from self-report and adjusts cues. The Dashboard tracks self-reported comfort per skill, piece completion milestones, and recommends periodic human teacher evaluation. **Key limitation**: cannot observe posture, hand position, or hear sound quality. Relies entirely on learner self-report, which novices do poorly. Risk of ingrained bad habits invisible to the AI.

---

## Gap 8: Complete data schema with FSRS-integrated decay model

### FSRS core model at the graph level

Each LearnerState vertex maintains three FSRS parameters: **Difficulty (D)** (1.0–10.0, inherent complexity), **Stability (S)** (days for retrievability to decay from 100% to 90%), and **Retrievability (R)** (current recall probability, computed on-the-fly). The forgetting curve follows a power law:

**R(t, S) = (1 + t/(9·S))^(−1)**

where t = days since last review. At t=0, R=1.0. At t=S, R≈0.9. The system should **compute R on-the-fly** when queried (it changes every second) but **store S and D persistently** (they only change on review events). A daily batch job checks if any node's computed R has dropped below threshold, triggering decay transitions.

### State transition rules

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

**Effective mastery score** combines discrete level and continuous FSRS: `effective_mastery = base_mastery(level) × R(t, S)`, where base_mastery maps NOT_STARTED=0.0, ATTEMPTED=0.25, FAMILIAR=0.50, PROFICIENT=0.80, MASTERED=1.0. A "Mastered" node with R=0.7 has effective_mastery of 0.7, accurately reflecting decayed knowledge.

### Complete schema architecture

The **Apache AGE graph layer** stores: Domain vertices (top-level subjects), Concept vertices (abstract knowledge units with embedding_id FK to pgvector), Skill vertices (assessable abilities tied to concepts), and LearnerState vertices (per-learner overlay with FSRS parameters). Edge types: PREREQUISITE (hard/soft, strength), RELATED (similarity, transfer_coefficient), COMPOSES (skill→concept with weight), HAS_STATE_FOR (learner overlay→concept).

The **PostgreSQL relational layer** stores: `learners` (with FSRS personalized parameters), `learning_sessions` (with concepts/skills touched), `session_messages` (with bloom_level_demonstrated, correctness, embedding_id), `assessments` (with full FSRS review fields), and `mastery_transitions` (audit trail of all level changes with trigger type and reason).

The **pgvector embedding layer** stores: embeddings for concepts, skills, messages, assessment questions, and session summaries. HNSW index for fast similarity search. The key integration pattern: **graph node UUIDs are the canonical identifiers used across both layers**. Cross-layer queries use AGE's `cypher()` function in SQL to get graph results, then JOIN with relational tables.

### Progress reporting anti-patterns to avoid

**Completion ≠ mastery** (completing 85% of lessons means nothing if retention is 40%). **Vanity XP** (points that accumulate monotonically regardless of learning quality — Duolingo's known weakness). **Hidden decay** (showing "Mastered" badges from 6 months ago with no decay indication). **Streak anxiety** (loss-aversion mechanics creating stress rather than motivation). Instead: show retrievability-adjusted strength meters that fade over time, distinguish recognition from production (Bloom's level labeling), use dual metrics (breadth + depth), celebrate real milestones (first transfer task, maintained mastery after 30 days), and make decay visible but non-punitive ("This is ready for a refresher").

---

## Gap 9: Bidirectional data flow from Anki through knowledge graph

### Anki database structure

The critical table is `revlog` (review log), which stores every review ever performed: `id` (epoch ms timestamp), `cid` (card ID), `ease` (1=Again, 2=Hard, 3=Good, 4=Easy), `ivl` (new interval in days; negative = seconds for learning steps), `lastIvl` (previous interval), `factor` (ease factor in permille), `time` (review duration in ms), `type` (0=learn, 1=review, 2=relearn). The `notes` table stores content with fields separated by `0x1f`. The `cards` table tracks current state: type (new/learning/review/relearning), interval, factor, reps, lapses.

### End-to-end round-trip data flow

**Phase 1 — Export**: Plugin generates .apkg via genanki with hardcoded Model/Deck IDs and deterministic GUIDs (`genanki.guid_for(card_id)`). Each note includes a hidden `KnowledgeNodeID` field linking back to the AGE graph vertex.

**Phase 2 — User reviews in Anki**: Standard Anki workflow. FSRS scheduler manages intervals.

**Phase 3 — Import**: Extract `collection.anki2` from .apkg ZIP. JOIN `revlog` with `cards` and `notes` to recover the `KnowledgeNodeID` from the note's fields (split on `0x1f` separator). Parse each review into a structured record: ease, interval, factor, review time, review type.

**Phase 4 — Graph update**: Map each Anki review to a mastery delta. Again (ease=1) produces a strong negative signal (−0.15 × lapse multiplier). Good (ease=3) produces a moderate positive signal (+0.05 × (1.2 − R)), giving more credit when retrievability was low (harder recall was successful). FSRS stability is updated using the standard FSRS-6 formulas. Propagate 10% of mastery delta to prerequisite nodes.

**Phase 5 — Adapt**: Updated graph informs next session's card selection, difficulty calibration, and curriculum routing.

### Unstructured import processing (Obsidian notes)

For each note: extract wikilinks for direct high-confidence matches to graph nodes, then chunk remaining text (256 tokens, 50-token overlap), embed each chunk via text-embedding-3-small, and query pgvector for nearest graph nodes (cosine similarity >0.75). Classify each chunk's signal type (explanation, question, confusion, summary, example). Explanations and examples produce small positive mastery deltas; questions and confusion markers produce small negative deltas. All adjustments are weighted by `SOURCE_WEIGHT['obsidian'] = 0.12` — significantly lower than assessment or Anki data.

### Multi-source confidence fusion

| Source | Base Weight | Rationale |
|---|---|---|
| Anki Reviews (FSRS) | 0.45 | Direct behavioral evidence of recall |
| Plugin Assessments | 0.35 | Controlled test conditions |
| Obsidian Notes | 0.12 | Indirect signal; studying ≠ mastery |
| Self-Reports | 0.08 | Subjective; Dunning-Kruger effect |

Each source's effective weight decays exponentially with age (half-life ~23 days). The fused mastery score is: `Σ(mastery_i × weight_i × confidence_i × recency_i) / Σ(weight_i × confidence_i × recency_i)`.

**Conflict resolution**: When Anki says "Easy" but assessment shows gaps, this is a recognition-vs-application gap. Assessment is more reliable for deep understanding; halve Anki's influence for this node and generate application-focused cards. When Anki shows lapses but assessment is strong, suspect card quality issues — flag cards for reformulation. Self-report always yields to behavioral data.

---

## Gap 10: Prompt architecture from orchestrator to component

### Khanmigo's design patterns as the gold standard

Khan Academy's 7-step prompt engineering pipeline grounds prompts in Bloom's 2-sigma problem, consults learning science literature, integrates curriculum context, crafts interaction via prompt engineering, tests across diverse user personas, prioritizes safety, and iterates on real feedback. The actual Khanmigo Lite system prompt reveals critical patterns: role declaration ("You are a tutor that always responds in the Socratic style"), explicit NEVER-give-answers rule, stuck detection ("always start by figuring out what part I am stuck on FIRST"), and **help abuse prevention** ("If I ask for further assistance 3 or more times in a row without significant effort... BE FIRM ABOUT THIS").

### Balancing theory vs. behavioral instructions

The prompt should be **~70% behavioral instructions, ~30% learning theory rationale**. Khanmigo translates learning science into concrete rules rather than expecting the LLM to derive pedagogy from theory. Encode the *consequences* of learning theory as behavioral rules: instead of "Vygotsky's ZPD suggests tasks at the edge of ability," write "If the learner answers correctly 3 times in a row with no hesitation, increase difficulty."

### Six critical failure modes with guardrails

**Being too agreeable**: "When a learner provides an answer, NEVER begin with agreement unless the answer is fully correct. If partially correct: 'You're on the right track with [specific correct part], but let's examine [specific incorrect part].' Before validating any answer, internally verify it step-by-step."

**Over-scaffolding**: Four-level protocol — Level 1: open-ended question; Level 2: narrowed focus; Level 3: provide a choice; Level 4: concrete analogy then return. "NEVER skip to Level 4 without exhausting earlier levels. After correct response at any level, RESET to Level 1."

**Hallucination**: "For mathematical/logical content: show your work step-by-step internally before presenting. If uncertain about a factual claim, say 'I believe X, but this should be verified.' NEVER fabricate citations."

**Defaulting to lecture mode**: "Your responses should contain at least one question for every 3 sentences of explanation. Maximum explanation length: 150 words before requiring learner interaction."

**Failing to push back on overconfidence**: "If learner says 'I already know this,' probe deeper: 'Can you explain why [underlying principle] works that way?' Present edge cases as challenges."

**Inconsistent difficulty**: "Do not adjust difficulty based on emotional appeals. Adjust ONLY based on performance data: success rate, time-to-answer, scaffold levels needed."

### Skill Researcher prompt structure

The Researcher needs explicit self-verification because LLM knowledge is uneven across domains. Key rules: each skill must be independently assessable, skills should be MECE, confidence flagging (HIGH/MEDIUM/LOW) is mandatory, and LOW-confidence items must note "VERIFICATION NEEDED: [specific aspect]." Use multi-pass decomposition (top-down and bottom-up, then reconcile) and confabulation detection ("For each skill, provide one specific real-world example. If you cannot, flag the skill as potentially confabulated").

### Curriculum Architect encoding of learning science

4C/ID is encoded as: design 3–5 task classes ordered simple-to-complex; within each class, tasks have equal complexity but decreasing support (worked → completion → conventional); ensure variability (surface features change, structure stays). Elaboration Theory is encoded as: create an epitome (simplest complete representation of the domain), then elaborate in layers (fundamentals → nuances → advanced applications), using spiral sequencing rather than topical sequencing. Productive failure insertion points are flagged for concepts with common naive theories that interfere with learning.

### Skeleton orchestrator prompt

```
ROUTING LOGIC:
IF phase == "ONBOARDING":
  IF NOT skill_tree_exists → ROUTE to RESEARCHER
  ELIF NOT calibration_complete → ROUTE to CALIBRATOR
  ELIF NOT curriculum_exists → ROUTE to ARCHITECT
  ELSE → TRANSITION to "LEARNING"

IF phase == "LEARNING":
  IF needs_new_material → ROUTE to FORGE
  IF learner_active → ROUTE to CONDUCTOR
  IF lesson_complete → ROUTE to ASSESSOR
  IF assessment_complete → UPDATE graph; IF recalibration_needed → CALIBRATOR

ERROR RECOVERY:
- Any component fails twice → fallback (generic skill tree, simplified material,
  conservative difficulty estimate, structured Q&A mode)
- Always preserve learner state on error
```

### Token efficiency for 150k budget

System prompt: ~3–5K tokens (compressed, structured formats). Per-session learner context: ~1–3K (structured JSON). Current lesson material: ~5–15K. Conversation history: ~20–40K with rolling compression. Output reserve: ~15–30K. Key strategies: **component isolation** (each component operates in its own context — don't load tutoring conversation into curriculum generation), **rolling compression** (keep last 5–10 turns verbatim, compress earlier turns into structured summaries), **structured over narrative** (JSON for learner state, not prose), and **proactive memory management** (compress and archive at natural breakpoints).

---

## Unresolved tensions across all gaps

Five judgment calls remain that require empirical testing:

**Assessment efficiency vs. accuracy**: Graph propagation during diagnostic assessment can cause runaway inference. A dampening factor per hop and periodic direct verification are necessary, but the optimal dampening value is domain-dependent.

**Productive failure scope**: Kapur's framework produces strong effects for conceptual learning but the meta-analysis shows no benefit (and potential harm) for purely procedural skills or when learners are already frustrated. The system must decide when to apply productive failure vs. direct instruction — a decision that depends on real-time emotional state detection, which remains imperfect in text-only interaction.

**Self-report trust calibration**: Self-reports carry the lowest confidence weight (0.08) due to Dunning-Kruger effects, yet for motor and perceptual skills they are often the *only* signal available between sessions. The system may need to trust self-reports more for these skill types while remaining skeptical for cognitive skills where direct assessment is possible.

**Token budget vs. pedagogical richness**: Productive failure sessions (~9,200 tokens) and skill drilling (~9,700 tokens) consume 6–7× more budget than mastery gates (~3,400 tokens). The system must make real-time tradeoffs between pedagogical richness and context window sustainability, especially during extended multi-session curricula.

**Negative transfer detection precision**: The procedure-embedding comparison method (flag when content similarity >0.7 AND procedure similarity <0.5) requires validated procedure embeddings, which are harder to generate than content embeddings. False positives waste instructional time on unnecessary contrast instruction; false negatives allow interference to degrade learning. Empirical calibration against actual learner performance data is essential before deploying this feature at scale.