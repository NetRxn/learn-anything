# Assessment Types for the Training Conductor

Four assessment types, each with distinct purpose, design, and use within training sessions.

## In-Session Retrieval Probes (every session)

**Purpose:** Dual-purpose — provides retrieval practice (strengthens memory) AND measures retention (informs knowledge graph updates).

**Design:**
- Open-ended, requiring generation not recognition
- Correspond to exported SRS cards (shared card_id for tracking)
- Target material from previous sessions (micro-spacing: 2-5 exchanges after teaching, interleaved with new content, cumulative mini-quiz at session end)

**Timing within sessions:**
- Session start: 2-3 retrieval probes on material from the PREVIOUS session (delayed retrieval)
- Mid-session: Probe material taught earlier in THIS session (micro-spacing)
- Session end: Cumulative mini-quiz covering 3-5 key concepts from this and recent sessions

**Scoring:** Binary (correct/incorrect) or partial credit. Record: vertex_id, card_id, days_since_last_review, result, confidence_pre (1-5 self-rating before answering).

**Knowledge graph update:** Each probe result updates the corresponding vertex's mastery_probability. Strong retrieval after delay -> increase mastery estimate. Failed retrieval -> decrease estimate and flag for additional review.

## Mastery Gate Assessments (at task class boundaries)

**Purpose:** Verify competence before advancing to the next task class. Template E from session templates.

**Design:** Three mandatory criteria:
1. **Cold Recall**: Open question, no scaffolding. "Explain [concept] from scratch."
2. **Application Under Novelty**: Problem with novel surface features, no hints.
3. **Explain-to-Teach**: "How would you explain this to someone who's confused?"

**Criteria by Bloom's level:**

| Level | Item Type | Threshold | Items Needed |
|---|---|---|---|
| Remember | Recall, fill-in-blank | 90-95% | 3-5 |
| Understand | Explain in own words | 85-90% rubric | 3-5 |
| Apply | Solve novel problems | 85% | 3+ varied |
| Analyze | Compare, find patterns | 80% rubric | 3+ cases |
| Evaluate | Judge, critique | 75-80% rubric | 2-3 |
| Create | Design, produce | Holistic rubric | Portfolio |

**Failure routing:**
- Fail recall only -> Template B (retrieval practice)
- Fail application -> Template A (concept re-teach)
- Fail 2+ criteria -> Full cycle: A -> C -> B -> E (retest)
- Max 3 attempts before flagging for curriculum adjustment

**Anti-gaming:** Generate fresh items with different surface features on each attempt. Require explanation (hard to fake). After passing, schedule delayed retention check.

## Delayed Retention Assessments (1-3, 7-14, 30+ days after mastery)

**Purpose:** Verify that learning is durable, not just momentary performance.

**Design:**
- No hints, no scaffolding — pure retrieval
- Surface features differ from original instruction
- Same deep structure as what was taught
- Open-ended (generation, not recognition)

**Scheduling:**
- First check: 1-3 days after mastery gate passed
- Second check: 7-14 days after mastery gate
- Third check: 30+ days (if the engagement runs that long)

**In practice:** These are delivered as retrieval probes at the START of a training session, before new content. The Conductor checks progress.json for vertices that passed mastery gates and schedules retention probes at appropriate intervals.

**Knowledge graph update:** Retention performance is the STRONGEST signal for mastery estimation. Successful delayed retrieval -> significant mastery boost and FSRS stability increase. Failed delayed retrieval -> mastery downgrade and schedule for re-review.

## Transfer Assessments (after mastery + retention confirmed)

**Purpose:** Test whether learning generalizes beyond practiced contexts.

**Design:**
- **Near transfer**: Same principle, slightly different context (different domain objects, same structure)
- **Far transfer**: Same principle, significantly different domain (requires abstracting the principle from the original context)

**Administer:** Only after mastery gate passed AND at least one successful delayed retention check.

**Knowledge graph update:** Successful transfer -> mark vertex as truly mastered (highest confidence). Failed transfer -> mastery intact but transfer skill needs work. May generate additional practice with varied contexts.

## Multi-Source Fusion (for external data integration)

When integrating Anki review data, self-reports, or notes at session start:

| Source | Base Weight | Notes |
|---|---|---|
| Anki Reviews | 0.45 | Direct behavioral evidence of recall |
| Plugin Assessments | 0.35 | Controlled conditions |
| Obsidian Notes | 0.12 | Indirect signal only |
| Self-Reports | 0.08 | Subjective; increase to 0.20 for motor/perceptual skills |

**Conflict resolution:**
- Anki "Easy" + Assessment shows gaps -> recognition-vs-application gap. Halve Anki's influence for this vertex. Generate application-focused cards.
- Anki lapses + Assessment strong -> card quality issue. Flag cards for reformulation.
- Self-report confident + behavioral data weak -> trust behavioral data. Metacognitive miscalibration.
- All sources agree -> high confidence in the mastery estimate.

Each source's weight decays with age (half-life ~23 days). Recent data matters more.
