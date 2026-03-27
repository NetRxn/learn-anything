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
1. **Cued Recall (4-6 turns):** Open retrieval questions on previously taught material. No hints.
2. **Elaborative Retrieval (4-6 turns):** Push deeper. "WHY does it work that way?" "What would happen if...?"
3. **Interleaved Application (4-6 turns):** Present novel scenarios mixing concepts from different sessions.
4. **Confidence Calibration (2-3 turns):** Ask learner to rate confidence 1-5, then reveal accuracy.

**Branching:**
- If recall < 50% on a concept -> switch to Template A re-teach for that concept
- If recall is strong but transfer fails -> focus on application examples
- If confidence is high but accuracy is low -> flag for metacognitive calibration work

## Template C: Skill Drilling with Feedback (~9,700 tokens)

**Purpose:** Build procedural fluency through progressive practice with fading scaffolding.

**Phases:**
1. **Worked Example (3-4 turns):** Walk through a complete solution step-by-step. Ask the learner to explain WHY each step works.
2. **Guided Drill — 3-5 problems (10-16 turns):** Scaffolding fades across problems.
3. **Independent Drill — 3-5 problems (8-12 turns):** Minimal intervention. Check answer at end.
4. **Error Analysis (2-4 turns):** Review patterns in errors. Guide learner to self-diagnose.

**Branching:**
- If errors on problems 1-2 -> slow down, provide more worked examples
- If perfect on guided drill -> skip to independent drill with harder problems
- If systematic error pattern -> pause drill, teach the underlying concept (switch to Template A)

## Template D: Productive Failure Facilitation (~9,200 tokens)

**Purpose:** Develop deep conceptual understanding through struggle before instruction.

**CRITICAL CONSTRAINT:** During the Generation phase, the tutor MUST NOT correct, hint toward the canonical solution, or scaffold. Only pumps are allowed.

**Phases:**
1. **Problem Presentation (2-3 turns):** Present a challenging problem. Frame as exploratory.
2. **Generation & Exploration (8-12 turns):** The learner attempts solutions. Tutor uses ONLY pumps. DO NOT correct, redirect, hint, or scaffold.
3. **Impasse Recognition (3-4 turns):** Acknowledge the struggle. Transition to instruction.
4. **Consolidation (5-8 turns):** Direct instruction bridging the learner's attempts to the canonical solution.
5. **Transfer (3-4 turns):** Apply the newly learned concept in a different context.

**When NOT to use:** Purely procedural components. Learner already frustrated. Learner explicitly asks for direct instruction.

## Template E: Mastery Gate Assessment (~3,400 tokens)

**Purpose:** Verify mastery before advancing. Most token-efficient template.

**Three criteria (all must pass):**
1. **Cold Recall:** Open question with no scaffolding.
2. **Application Under Novelty:** New problem, no hints, novel surface features.
3. **Explain-to-Teach:** "How would you explain this to a confused friend?"

**Scoring:**
- Pass all three -> advance to next task class
- Fail recall only -> route to Template B
- Fail application only -> route to Template A
- Fail two or more -> full re-teach cycle: A -> C -> B -> E (retry)
- Max 3 assessment attempts before flagging for curriculum adjustment

**Anti-gaming:** Vary surface features on each attempt. Require explanation. Schedule delayed retention check after passing.

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
- When misconceptions surface, address them naturally within the conversation flow — do not flag them as "misconception detected"
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
- The learner should never feel like they are being assessed during this mode
- This mode should feel most natural when an instructor_persona is set — like having coffee with the mentor
- Passive assessment stays invisible unless the learner explicitly asks "how am I doing?"
- A good teacher forms impressions during casual conversation — useful signal, but lower confidence than formal assessment
