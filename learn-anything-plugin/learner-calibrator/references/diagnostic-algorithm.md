# Diagnostic Assessment Algorithm

Based on Knowledge Space Theory (Doignon & Falmagne, 1985) and the ALEKS implementation. Adapted for conversational AI assessment.

## Core Principle

The dependency graph constrains which knowledge states are feasible. If a learner demonstrates mastery of a downstream skill, its prerequisites are likely mastered too. If they fail a skill, its dependents are likely unknown. This graph propagation dramatically reduces the number of questions needed — ALEKS assesses 350-500 skill domains in 30 or fewer questions.

## Three Acceleration Mechanisms

### 1. Graph Propagation (reduces questions by 40-60%)

When the learner demonstrates mastery on skill S:
- All PREREQUISITE ancestors of S receive an **upward Bayesian update**
- Dampening: 0.7x per hop (direct prerequisites get 70% boost, grandparents get 49%, etc.)
- Rationale: demonstrating a downstream skill implies prerequisites were needed

When the learner fails on skill S:
- All PREREQUISITE dependents of S receive a **downward Bayesian update**
- Dampening: 0.7x per hop in the dependent direction
- Rationale: failing a skill implies dependents are likely also unknown

**Important:** Propagation can cause runaway inference. A single strong performance on an advanced skill shouldn't mark the entire prerequisite chain as mastered with high confidence. The dampening factor prevents this, and periodically verify inferred states with direct questions (see Verification Passes below).

### 2. Embedding-Cluster Inference (via pgvector)

Skills that are semantically similar (cosine similarity > 0.85 on component embeddings) tend to share mastery status. If 3+ assessed skills in a semantic cluster all show mastery, remaining unassessed cluster members can be tentatively marked as mastered.

**Apply with a confidence penalty** — cluster-inferred mastery should have confidence 0.2-0.3 lower than directly assessed mastery. These inferences should be verified before relying on them for curriculum decisions.

### 3. Information-Theoretic Item Selection

Choose the next question to maximize information gain across the entire graph:

```
info_gain(s) = entropy(s) * (1 + 0.3 * downstream_count(s))
```

Where:
- `entropy(s) = -P(mastered) * log(P(mastered)) - P(not_mastered) * log(P(not_mastered))`
- `downstream_count(s)` = number of skills that have s as a prerequisite (directly or transitively)

Skills with high entropy (we're most uncertain about them) AND many downstream dependents (resolving them propagates the most information) should be assessed first.

## Assessment Flow

```
INITIALIZE:
  For each skill s in the graph:
    If transfer pathway exists:
      P_mastery[s] = transfer_boost from dossier
    Else:
      P_mastery[s] = 0.3 (weak prior — slightly below chance)
    confidence[s] = 0.0

LOOP (max 20 questions OR max_uncertainty(graph) < 0.15):
  1. Compute info_gain for all unassessed skills
  2. Select skill s* with highest info_gain
  3. Generate an open-ended diagnostic question for s* (see Question Design below)
  4. Evaluate learner response on a 4-point scale:
     - mastered (1.0): correct, can explain reasoning, shows genuine understanding
     - partial (0.5): partially correct, has the right idea but gaps in execution/explanation
     - misconception (0.1): systematic error suggesting an incorrect mental model
     - none (0.0): no relevant knowledge demonstrated
  5. Update P_mastery[s*] using the evaluation score
  6. Set confidence[s*] = 0.85 (directly assessed)
  7. Propagate: upward through prerequisites, downward through dependents (0.7x damping)
  8. Cluster inference: check semantic clusters for unanimous mastery patterns
  9. Compute new max_uncertainty across graph

RETURN: knowledge_state map with P_mastery and confidence for all skills
```

## Question Design Principles

Diagnostic questions should:
- Be **open-ended** (not multiple choice — too easy to guess)
- Target the **specific** skill being assessed (not adjacent skills)
- Require **generation** not recognition (demonstrate, explain, or produce — not identify or select)
- Be at the **appropriate Bloom's level** for the skill (don't ask a Remember question to assess Apply-level mastery)
- Feel **conversational** (not like a formal test)

**Good diagnostic questions by Bloom's level:**
- Remember: "What is [concept]?" / "Can you define [term]?"
- Understand: "Explain [concept] in your own words" / "Why does [process] work that way?"
- Apply: "How would you use [concept] to solve [concrete scenario]?"
- Analyze: "What's the difference between [A] and [B]?" / "Why would [approach X] work better than [approach Y] here?"
- Evaluate: "Is [statement] correct? Why or why not?"
- Create: "How would you design/build [thing] given [constraints]?"

**For transfer points:** When the dossier flags a component as a potential transfer from the learner's existing skills, ask specifically about the overlap: "You mentioned you play piano — can you explain what a chord progression is?" This both assesses the skill AND validates the transfer pathway.

## Conversational Framing

The assessment should feel like an engaging conversation, not a test:
- Start broad: "Tell me about your experience with [general area]"
- Narrow based on responses: "You mentioned X — can you go deeper on how Y works?"
- Celebrate what they know: "Nice — that's solid. Let me ask about something a bit different."
- Normalize not-knowing: "No worries — that's exactly the kind of thing we'll build up."
- Transition naturally between assessed clusters rather than jumping randomly

## Mastery Category Derivation

Map continuous P_mastery to discrete categories for human-readable reporting:
- `not_started`: P_mastery < 0.10
- `attempted`: 0.10 <= P_mastery < 0.40
- `familiar`: 0.40 <= P_mastery < 0.70
- `proficient`: 0.70 <= P_mastery < 0.90
- `mastered`: P_mastery >= 0.90

## Verification Passes

After the main assessment loop, run a brief verification pass:
- For any skill marked as mastered ONLY through propagation or cluster inference (not directly assessed), ask one direct verification question
- This catches runaway inference errors
- Typically adds 3-5 questions
- Can be skipped if the graph is small (<15 nodes) and propagation chains are short

## When to Trigger Re-Research

Flag for the orchestrator if:
- Assessment reveals the learner has unexpected expertise in an area the dossier classified as "basic" — the decomposition may be too granular there
- Assessment reveals gaps where the dossier assumed prerequisites were trivial
- The learner describes approaches or frameworks not reflected in the dossier
- More than 30% of components are assessed at confidence < 0.5 after the full loop
