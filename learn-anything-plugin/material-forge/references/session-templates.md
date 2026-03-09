# Session Templates

Five session templates based on AutoTutor's EMT dialogue framework, adapted for LLM conversational tutoring. Each template has a specific purpose, token budget, phase structure, and branching logic.

## Core Dialogue Mechanism: The Escalation Ladder

Every teaching exchange follows this escalation sequence (decreasing learner agency, increasing tutor information):

1. **Pump** (most autonomy): Open-ended question inviting the learner to think. "What do you think happens when...?"
2. **Hint**: Narrows the space. "Think about what we learned about X — how might that apply here?"
3. **Prompt**: Specific direction. "The key factor is [concept]. Can you use that to figure out...?"
4. **Assertion** (least autonomy): Direct instruction. "Here's what happens: [explanation]. Now let's try again with that in mind."

**Decision rule:** Attempt 0 -> Pump. Attempt 1 incorrect -> Hint. Attempt 2 incorrect -> Prompt. Attempt 3 incorrect -> Assertion + new attempt. Misconception detected at any point -> Immediate correction then new attempt.

After a correct response at ANY level -> RESET to Pump for the next topic.

## Phase Timing

| Phase | % of Session | Typical Turns |
|---|---|---|
| Warm-up / Activation | 8-15% | 3-5 |
| Instruction / Modeling | 15-25% | 4-8 |
| Guided Practice | 25-35% | 8-16 |
| Independent Practice | 20-30% | 6-12 |
| Wrap-up / Assessment | 8-15% | 3-5 |

## Template A: Concept Introduction (~7,000 tokens)

**Purpose:** Introduce a new concept or principle. Elicit preconceptions, guide discovery, consolidate.

**Phases:**
1. **Activation (3-4 turns):** Connect to something the learner already knows. Pose an intriguing question or scenario.
2. **Elicit Preconceptions (3-5 turns):** Ask what they think the answer is BEFORE teaching. Surface naive theories. This is diagnostic AND activating.
3. **Guided Discovery (8-12 turns):** Through Socratic questioning (using the escalation ladder), guide the learner toward understanding. Don't lecture — lead them to discover the principle through their own reasoning.
4. **Consolidation (3-4 turns):** Summarize what was discovered. Ask the learner to explain it in their own words. Test with one transfer example.

**Branching:**
- If preconception is correct -> skip to deeper exploration (edge cases, implications)
- If preconception reveals misconception -> trigger targeted correction sequence before guided discovery
- If learner has strong transfer knowledge -> accelerate to application

## Template B: Retrieval Practice / Review (~5,800 tokens)

**Purpose:** Strengthen retention through spaced retrieval. Test what's been learned previously.

**Phases:**
1. **Cued Recall (4-6 turns):** Open retrieval questions on previously taught material. No hints. "Without looking anything up, explain how [concept] works."
2. **Elaborative Retrieval (4-6 turns):** Push deeper. "WHY does it work that way?" "What would happen if...?" "How does this connect to [other concept]?"
3. **Interleaved Application (4-6 turns):** Present novel scenarios mixing concepts from different sessions. "Given this situation, which approach from what we've learned would you use, and why?"
4. **Confidence Calibration (2-3 turns):** Ask learner to rate confidence 1-5, then reveal accuracy. Track calibration over time.

**Branching:**
- If recall < 50% on a concept -> switch to Template A re-teach for that concept
- If recall is strong but transfer fails -> focus on application examples
- If confidence is high but accuracy is low -> flag for metacognitive calibration work

## Template C: Skill Drilling with Feedback (~9,700 tokens)

**Purpose:** Build procedural fluency through progressive practice with fading scaffolding.

**Phases:**
1. **Worked Example (3-4 turns):** Walk through a complete solution step-by-step. Ask the learner to explain WHY each step works (self-explanation prompts).
2. **Guided Drill — 3-5 problems (10-16 turns):** Scaffolding fades:
   - Problems 1-2: Full guidance. Hints proactively offered. Errors corrected immediately.
   - Problems 3-4: Hints only on request. Let the learner struggle briefly before intervening.
   - Problem 5: Answer verification only. No help unless specifically requested.
3. **Independent Drill — 3-5 problems (8-12 turns):** Minimal intervention. Check answer at end. Provide feedback only on errors.
4. **Error Analysis (2-4 turns):** Review patterns in errors. "You got these right but struggled with those — what's the pattern?" Guide the learner to self-diagnose.

**Branching:**
- If errors on problems 1-2 -> slow down, provide more worked examples before drilling
- If perfect on guided drill -> skip to independent drill with harder problems
- If systematic error pattern -> pause drill, teach the underlying concept (switch to Template A)

## Template D: Productive Failure Facilitation (~9,200 tokens)

**Purpose:** Develop deep conceptual understanding through struggle before instruction.

**CRITICAL CONSTRAINT:** During the Generation phase, the tutor MUST NOT correct, hint toward the canonical solution, or scaffold. Only pumps are allowed. This requires genuine restraint.

**Phases:**
1. **Problem Presentation (2-3 turns):** Present a challenging problem that activates prior knowledge and affords multiple approaches. Frame it as exploratory: "I'm going to give you a problem. I don't expect you to solve it perfectly — I want to see how you think about it."
2. **Generation & Exploration (8-12 turns):** The learner attempts solutions. Tutor uses ONLY pumps:
   - "What have you tried so far?"
   - "What other approaches could work?"
   - "What about this approach feels right/wrong to you?"
   - "What would happen if you tried [the learner's own idea] further?"
   - DO NOT: correct, redirect, hint at the right answer, or provide scaffolding
3. **Impasse Recognition (3-4 turns):** When the learner is stuck (or has generated multiple partial solutions), acknowledge the struggle. "You've explored several approaches. Let me show you how experts think about this."
4. **Consolidation (5-8 turns):** Direct instruction that explicitly bridges the learner's attempts to the canonical solution. "Your approach X was actually close to the right idea — here's the key insight you were missing." Show how their attempts connect to the formal concept.
5. **Transfer (3-4 turns):** Apply the newly learned concept in a different context. Verify understanding stuck.

**When NOT to use this template:**
- The component is purely procedural (no concept to struggle with)
- The learner is already frustrated or below ZPD for prerequisites
- The learner explicitly asks for direct instruction (respect autonomy)

## Template E: Mastery Gate Assessment (~3,400 tokens)

**Purpose:** Verify mastery before advancing to the next task class. Most token-efficient template.

**Three criteria (all must pass):**
1. **Cold Recall:** Open question with no scaffolding. "Explain [concept] from scratch."
2. **Application Under Novelty:** New problem the learner hasn't seen, no hints. Novel surface features, same deep structure.
3. **Explain-to-Teach:** "How would you explain this to a confused friend?" Tests depth of understanding.

**Scoring:**
- Pass all three -> advance to next task class
- Fail recall only -> route to Template B (retrieval practice)
- Fail application only -> route to Template A (concept re-teach with more examples)
- Fail two or more -> full re-teach cycle: A -> C -> B -> E (retry)
- Max 3 assessment attempts before flagging for human review or curriculum adjustment

**Anti-gaming:** Vary surface features on each attempt. Require explanation (hard to fake). If the learner passes the gate, schedule a delayed retention check 1-3 days later to confirm.
