# Adaptive Difficulty Calibration

Real-time difficulty management through conversational signals. Target the Zone of Proximal Development: challenging enough to grow, not so hard the learner shuts down.

## Observable Signals

### High-Reliability Signals
- **Response correctness** (rolling 5-question window): The most direct signal. Track as a rolling average.
- **Error patterns**: Systematic errors (same mistake type repeating) = misconception -> needs targeted correction. Random errors (different mistakes each time) = slip -> maintain difficulty, they're learning.
- **Transfer signals**: Unprompted analogies, cross-topic references, application to novel examples = strong mastery indicator.
- **Question quality from learner**: Recall-level questions ("What is X?") -> still learning. Comprehension questions ("Why does X work?") -> developing. Application questions ("Could X work for Y?") -> proficient. Metacognitive questions ("How would I know when to use X vs Y?") -> mastery.

### Medium-High Reliability
- **Elaboration depth**: Unprompted elaboration (adding detail without being asked) = strong mastery. Terse, minimal answers = either confusion or boredom (disambiguate with other signals).
- **Hedging vs. confidence**: "I think maybe..." / "I'm not sure but..." = developing understanding. "Because X, therefore Y" / definitive statements = confidence (verify it's warranted).
- **Help-seeking quality**: Specific questions ("I understand A but not how it connects to B") = productive partial understanding. Vague requests ("I don't get it") = deeper confusion.

### Medium Reliability
- **Affective signals**: Frustration markers (short responses, expressions of confusion, "this doesn't make sense"), boredom markers (terse responses, low engagement, "yeah I know"). Detected at 69-78% accuracy in text (Graesser et al., 2007).
- **Engagement quality**: Declining response length, fewer questions from the learner, less elaboration over time = dropping engagement.

## Calibration Zones

```
IF accuracy > 90% AND explanations elaborate AND unprompted connections:
  -> MASTERY: increase difficulty, introduce transfer tasks

IF accuracy 75-90% AND explanations adequate AND occasional errors:
  -> ZPD-OPTIMAL: maintain current difficulty with varied examples. This is the sweet spot.

IF accuracy 60-75% AND hedging frequent AND help requests specific:
  -> STRUGGLING PRODUCTIVELY: maintain difficulty, increase scaffolding slightly.
    This CAN be the learning zone — don't reduce difficulty just because it's hard.

IF accuracy < 60% AND help requests vague AND frustration markers:
  -> BELOW ZPD: reduce difficulty, check prerequisites, increase scaffolding.
    Probe prerequisite concepts — if those are also weak, regress.

IF accuracy > 95% AND responses terse AND engagement low:
  -> BORED: advance difficulty immediately. Skip ahead in the task class.
```

## Optimal Accuracy Targets by Phase

| Learning Phase | Target Accuracy | Rationale |
|---|---|---|
| Initial exposure | 90-95% | Build confidence, establish foundation |
| Guided practice | 80-90% | Challenge within support |
| Independent practice | 75-85% | The sweet spot for durable learning |
| Transfer tasks | 60-75% | Naturally harder; lower accuracy is expected |

## Distinguishing Temporary Struggle from Fundamental Gaps

**Temporary struggle** (maintain difficulty, increase scaffolding):
- Accuracy improving across the rolling window
- Errors are inconsistent (different each time)
- Learner remains engaged and asking questions
- Help requests are becoming more specific

**Fundamental gaps** (regress to prerequisites):
- Accuracy flat or declining over 5+ attempts
- Same errors repeating systematically
- Cannot explain reasoning even when answer is correct
- Prerequisite concepts also weak when probed

## Adjustment Levers

### When too easy (MASTERY or BORED)
- Reduce scaffolding level (move from hints to open-ended questions)
- Increase interleaving (mix in more review from diverse topics)
- Raise Bloom's level (from Apply to Analyze, from Recall to Explain)
- Add variability (novel surface features, edge cases)
- Introduce productive failure moments
- Ask for explanations instead of answers ("Why?" not "What?")
- Consider advancing to the next task class

### When too hard (BELOW ZPD)
- Add worked examples before attempting independently
- Reduce problem complexity (fewer variables, simpler scenarios)
- Return to blocked practice (focus on one thing at a time)
- Provide analogies to existing knowledge (from the knowledge graph)
- Break the problem into smaller steps
- Offer comparison with a similar problem they've already solved
- Probe prerequisites — if those are weak, regress there first

## Preventing Over-Correction

- **Minimum observation window**: Never adjust difficulty based on a single response. Wait for 3-5 data points.
- **Hysteresis**: Require sustained evidence before making significant difficulty changes. Don't bounce between levels on every turn.
- **Student choice**: When the system is uncertain, offer the learner a choice: "Want to try a harder version, or practice more at this level?"
- **Preserve productive struggle**: If the learner is at 60-75% accuracy but engaged and making progress, DO NOT reduce difficulty. This is where durable learning happens.
