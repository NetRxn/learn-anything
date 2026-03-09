# SRS Card Design Guide

## Five Core Principles (Matuschak)

1. **Focused**: One detail per card. If you need two ideas, make two cards.
2. **Precise**: Specific question, unambiguous answer. There should be exactly one correct response.
3. **Consistent**: Lights the same mental "bulbs" each time you see it. Avoid contextual ambiguity.
4. **Tractable**: Target ~90% accuracy. If consistently easy (>95%), it's too simple. If often wrong (<80%), it's too hard or poorly designed.
5. **Effortful**: Require genuine retrieval, not pattern matching from surrounding text.

## Card Type Selection

| Knowledge Type | Best Card Types | Bloom's Level |
|---|---|---|
| Fact, definition | Basic Q->A | Remember |
| Term in context | Cloze deletion | Remember/Understand |
| Vocabulary, bidirectional associations | Reversed | Remember |
| Procedure (steps) | Ordered cloze (one step per card) | Apply |
| Concept relationship | Comparison card | Analyze |
| Principle, mental model | Open-ended/generative | Apply-Create |

## Anti-Patterns to Reject

**Kitchen Sink**: "Describe the HTTP request lifecycle" -> Split into: "What are the 4 main HTTP methods?", "What does a 301 status code indicate?", etc.

**Ambiguous Cloze**: "Python uses {{c1::indentation}} for blocks" -> Multiple valid answers. Fix: "Python uses {{c1::indentation (whitespace)}} instead of curly braces to define code blocks."

**Yes/No**: "Is Python dynamically typed?" -> 50% guess rate. Fix: "Python is {{c1::dynamically}} typed, meaning variable types are determined at {{c2::runtime}} rather than compile time."

**Shopping List**: "What are the 5 mother sauces?" -> Make 5 individual cards, each asking for one sauce and its base ingredients.

**Pattern Matching**: If the answer is obvious from the card's wording without knowing the concept, rephrase. Test: could someone who doesn't know the topic guess correctly from context clues?

## Generation Rules

For each knowledge graph vertex that needs SRS cards:

1. **Determine how many cards**: 2-4 cards per concept (covering different angles). 1-2 cards per fact. 3-5 cards per procedure (one per step + overall).

2. **Vary the angle**: Don't just ask the same question different ways. Ask: "What is X?", "Why does X matter?", "When would you use X vs. Y?", "Give an example of X."

3. **Include the component_id**: Every card must reference its knowledge graph vertex. This enables round-trip tracking through Anki.

4. **Tag hierarchically**: Use `::` separator. Example: `python::data-structures::lists::comprehensions`

5. **Set difficulty_estimate**: 0.0 (trivial, everyone gets it) to 1.0 (very hard, specialized knowledge). Base on Bloom's level and the learner's current mastery of prerequisites.

6. **Set curriculum_position**: Cards should be introduced in the order the curriculum prescribes. Don't export advanced cards with the first deck.

## Comparison Cards (for confusable concepts)

When two concepts are easily confused (lists vs tuples, affect vs effect, major vs minor chords):

Front: "Compare [A] and [B]: what is the key difference and when would you use each?"
Back: Clear comparison with the distinguishing criterion and usage context.

These combat interference between similar concepts. Place them AFTER both concepts have been introduced.
