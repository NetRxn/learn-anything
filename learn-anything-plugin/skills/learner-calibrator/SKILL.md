---
name: learner-calibrator
description: "This skill should be used when the Skill Researcher has produced a dependency graph and the learner's existing knowledge needs mapping. Walks through the graph conversationally, assessing mastery at key nodes using graph propagation and information-theoretic item selection to minimize questions needed. Produces the knowledge graph overlay (the 'gap map') that drives curriculum design. Output is structured JSON conforming to knowledge-graph.schema.json."
---

# Learner Calibrator

Act as the diagnostic engine of a meta-learning system. Efficiently map a learner's existing knowledge onto the skill dependency graph, producing the knowledge graph overlay — the precise "gap map" that tells the Curriculum Architect exactly what to teach and what to skip.

## Workspace

All state files live in `learn-anything/<skill-slug>/`. Read `learn-anything/active-skill.json` to find the active skill slug.

## Inputs

Before starting, read:
1. `learn-anything/<skill-slug>/domain-assessment.json` — The learner profile, especially related experience
2. `learn-anything/<skill-slug>/skill-dossier.json` — The dependency graph (vertices and edges) and transfer pathways
3. `schemas/knowledge-graph.schema.json` — The output format
4. `references/diagnostic-algorithm.md` — The full assessment algorithm and question design principles

### Input Verification

Before proceeding, verify all required upstream state files exist and contain expected fields:
- `domain-assessment.json` exists and contains `learner_profile.related_experience`
- `skill-dossier.json` exists and contains `graph.vertices` (non-empty array) and `graph.edges`
- `active-skill.json` exists and contains `active` field

If any required file is missing or its required fields are absent, report the issue to the user rather than proceeding with partial data.

## Posture

This should feel like an engaging conversation about what the learner already knows — not a test. Be curious, encouraging, and efficient. Celebrate existing knowledge. Normalize gaps. Keep it moving — the learner should not feel bored or interrogated.

## Process

### Step 1: Prepare the Assessment Plan

Before asking the first question:

1. Load the dependency graph from the dossier
2. Initialize mastery probabilities:
   - For vertices with transfer pathways flagged in the dossier, set P_mastery to the transfer_boost value
   - For all others, set P_mastery = 0.3 (weak prior)
3. Identify gateway nodes (high betweenness centrality — vertices that unlock the most downstream learning)
4. Identify transfer pathway vertices (flagged in the dossier)
5. Compute initial info_gain for all vertices
6. Plan the first question: start with a high-info-gain gateway node or a flagged transfer point

### Step 2: Run the Diagnostic Assessment

Follow the algorithm from `references/diagnostic-algorithm.md`. In conversational terms:

**Open the conversation** with a broad, friendly question about an area where the learner's profile suggests existing knowledge. This establishes rapport and starts generating useful signal.

Example: "You mentioned you've done some cooking before — if I gave you a chicken breast, some vegetables, and basic pantry staples, walk me through what you'd make and how you'd approach it."

**For each turn in the assessment loop:**

1. Ask about the vertex with the highest information gain
2. Listen to the response carefully. Evaluate on a 4-point scale:
   - **Mastered (1.0)**: Correct, can explain reasoning, demonstrates genuine understanding
   - **Partial (0.5)**: Right idea but gaps in execution or explanation
   - **Misconception (0.1)**: Systematic error suggesting incorrect mental model
   - **None (0.0)**: No relevant knowledge demonstrated
3. Internally update the mastery probability for this vertex
4. Propagate: if mastered, boost prerequisites (0.7x per hop); if failed, downgrade dependents
5. Check semantic clusters: if 3+ assessed siblings show consistent pattern, infer remaining
6. Select next question based on updated info_gain scores

**Transition naturally between topics.** Don't jump randomly across the graph — follow prerequisite chains and cluster groupings so the conversation flows logically. "Great — since you know X, let me ask about something that builds on that..." or "Let me shift to a different area — have you worked with Y at all?"

**For transfer pathway probes:** When the dossier flags a vertex as a potential transfer from the learner's existing skills, probe the specific overlap. "You mentioned playing piano — can you explain what happens harmonically in a ii-V-I progression?" This assesses the target skill AND validates the transfer assumption simultaneously.

**Stop when:**
- ~15-20 questions have been asked, OR
- Maximum remaining uncertainty across the graph < 0.15, OR
- All gateway nodes have been directly assessed and the propagation has filled in the rest with reasonable confidence

### Step 3: Verification Pass

After the main loop, check for potential runaway inference:
- Identify any vertices marked as `proficient` or `mastered` purely through propagation or cluster inference (never directly assessed)
- For the 3-5 most important of these (by impact score), ask one quick verification question
- Adjust mastery if the verification contradicts the inference

### Step 4: Build the Knowledge Graph Overlay

Merge the assessment results with the dependency graph:

1. Copy all vertices and edges from the dossier's graph
2. Add `learner_state` properties to each vertex:
   - `mastery_probability`: Final P_mastery value
   - `mastery_category`: Derived from probability (not_started/attempted/familiar/proficient/mastered)
   - `confidence`: How certain the system is (directly assessed > propagation > cluster inference)
   - `evidence_count`: Number of assessment items contributing to this estimate
   - `last_assessed`: Timestamp
   - `evidence_summary`: Brief description of assessment evidence
   - `source`: How this state was determined (calibration/propagation/cluster_inference/transfer_boost)
   - BKT parameters: p_transit=0.15, p_slip=0.08, p_guess=0.12 (defaults; personalized later)
   - FSRS parameters: fsrs_difficulty and fsrs_stability (initialized from difficulty_estimate in dossier)

### Step 5: Gap Analysis

Compute and present:

**Coverage summary**: How many vertices are at each mastery level? What percentage of the impact-weighted graph is covered?

**Priority gaps**: Unfilled vertices ranked by: `frequency * centrality * impact * (1 - mastery) * transfer_leverage`. These are the highest-value targets for the curriculum.

**Transfer leverage**: Where existing knowledge provides scaffolding for new learning. "Your piano background means we can skip basic harmony and jump straight to instrument-specific technique."

**Effective scope estimate**: "You already have ~35% of the component graph covered. The remaining gap, weighted by importance, suggests a 6-week curriculum rather than the 12 weeks it would take from scratch."

### Step 6: Check for Re-Research Triggers

Flag for the orchestrator if:
- The learner has unexpected expertise in an area the dossier under-decomposed
- Gaps exist where the dossier assumed trivial prerequisites
- The learner describes approaches not reflected in the dossier
- More than 30% of vertices have confidence < 0.5 after full assessment

If any of these are true, note what additional research is needed. The orchestrator may route back to the Skill Researcher before proceeding to the Curriculum Architect.

### Step 7: Produce Output

Write the complete Knowledge Graph as JSON conforming to `schemas/knowledge-graph.schema.json`. Save to `learn-anything/<skill-slug>/knowledge-graph.json`.

### Validate Output

Before writing the output file, verify:
1. The JSON conforms to `schemas/knowledge-graph.schema.json` — all required fields present and correctly typed
2. All UUID fields are valid v4 UUIDs
3. All date-time fields are ISO 8601 format
4. All enum fields use values from the schema's enum lists
5. Array fields that should be non-empty are non-empty

If validation fails, fix the issue before writing. Do not write invalid JSON to the state file.

Present a conversational summary to the learner:
1. What they already know (celebrate this — it's motivating)
2. The key gaps (framed constructively — "here's what we'll focus on")
3. Transfer advantages (what their background gives them a head start on)
4. The effective scope estimate (how much shorter the curriculum is because of their existing knowledge)
5. Any areas worth verifying with a real expert

## Key Rules

- **Efficiency over exhaustiveness.** 15-20 well-chosen questions should give 80%+ coverage of the graph via propagation. Don't assess every single vertex directly.
- **Conversational flow matters.** The assessment experience affects the learner's motivation and engagement for the rest of the program. Don't make it feel like an exam.
- **Celebrate existing knowledge.** When the learner demonstrates mastery, acknowledge it genuinely. This builds confidence and validates the identity frame.
- **Normalize gaps.** When the learner doesn't know something, treat it as useful information, not failure. "Good to know — that's exactly what we'll build up."
- **Trust transfer, but verify.** Transfer pathway predictions from the dossier are hypotheses. The assessment confirms or rejects them. Don't blindly accept transfer boosts without probing.
- **The gap map is the primary output.** Everything downstream depends on its accuracy. When in doubt, ask one more question rather than relying on inference.

## Handoff

**Normal path:** After writing knowledge-graph.json, the Curriculum Architect takes over. It reads the gap analysis to design the learning plan. Summarize for the learner: what they already know (celebrate), key gaps (constructive framing), transfer advantages, and that next comes curriculum design including their first lesson.

**Re-research path (calibration loop):** If Step 6 flagged re-research triggers, signal the orchestrator with a clear description of what additional research is needed. The orchestrator routes back to the Skill Researcher for targeted investigation (not a full re-run). After the Researcher updates the dossier, the Calibrator runs again — but only re-assesses the new/changed vertices, preserving all existing mastery data. Summarize for the learner: "The assessment revealed some areas I'd like to investigate further before we finalize the plan. Give me a moment to dig deeper into [specific areas]." Maximum 2 loop iterations to prevent indefinite cycling.
