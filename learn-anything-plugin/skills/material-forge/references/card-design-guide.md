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
| Spatial/structural/layered systems | Visual (diagram card) | Understand-Analyze |
| Process with branching or phases | Visual (diagram card) | Understand-Apply |

## Visual Cards

### When to Use Visuals

Not every card benefits from a diagram. Apply this heuristic:

**Use a visual when the concept is inherently spatial, sequential, or comparative** — i.e., a learner would naturally draw a picture to explain it. Signals:

- The concept involves **layers, stacks, or nesting** (protocol stacks, inheritance hierarchies, geological strata, OSI model)
- The concept is a **process with phases or branching** (state machines, lifecycles, decision trees, metabolic pathways)
- The concept involves **flow or movement** (data pipelines, signal paths, supply chains, blood circulation)
- The concept requires **comparing two similar structures** to see where they diverge (two algorithms, two architectures, before/after)
- The concept involves **quantitative relationships** that are easier to grasp visually (proportions, distributions, relative sizes)

**Stick with text when** the concept is definitional, terminological, rule-based, or factual without spatial structure. "What does X mean?" and "When should you use X?" are almost always better as text cards.

### Visual Card Formats

Visual cards use the same `card_type` values (basic, cloze, comparison) but include an `image_svg` field containing inline SVG. The SVG appears in the card HTML alongside any text.

**Diagram-label (visual cloze)**: Show a diagram with one element replaced by "???". The learner identifies the missing piece. Effective for spatial/sequential knowledge where the learner must internalize the structure.

**Scenario → diagram (visual basic)**: Front gives a text scenario or question. Back includes a diagram showing the answer. The learner should mentally construct the visual before flipping. Effective for process and mental-model knowledge.

**Side-by-side comparison (visual comparison)**: Two diagrams showing related but different structures, with the key divergence highlighted. Effective for combating interference between confusable concepts.

### SVG Design Constraints

Cards are viewed on phone screens in Anki. SVGs render inside a white "light box" container (the `.card-diagram` div), so design SVGs for a white background regardless of the user's Anki theme. All SVGs must:

- Use a viewBox with max logical width of 400 and scale proportionally
- Use transparent or no background — the white container handles it
- Use high-contrast colors against white: `#2563eb` (blue), `#dc2626` (red), `#16a34a` (green), `#9333ea` (purple), `#d97706` (amber), `#374151` (dark gray for text/lines)
- Never use white or near-white for text or lines (invisible against the container)
- Keep text at minimum 12px equivalent (legible on mobile)
- Limit to 8 or fewer labeled elements per diagram (cognitive load)
- Include a `<title>` element for accessibility
- Avoid fine detail that disappears at small sizes

### SVG in Card Fields

Place SVG in the card's `image_svg` field (not inline in `front`/`back`). The export script splits this into separate `FrontDiagram` and `BackDiagram` Anki fields based on `image_placement`. The `front` and `back` fields contain only the text portion of the card. This separation keeps the JSON readable and allows the export script to handle rendering.

```json
{
  "card_id": "example-visual-01",
  "card_type": "basic",
  "front": "What are the 3 layers of the TCP/IP model, from top to bottom?",
  "back": "Application → Transport → Internet (Network)",
  "image_svg": "<svg viewBox='0 0 300 200'>...</svg>",
  "image_placement": "back",
  "bloom_level": "remember",
  ...
}
```

`image_placement` controls where the SVG appears: `"front"` (on the question side), `"back"` (on the answer side), or `"both"`. Defaults to `"back"` if omitted.

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

7. **Visual audit**: After generating all cards for a vertex, ask: "Does this concept have a spatial, sequential, comparative, or structural dimension that text alone handles poorly?" If yes, add an `image_svg` to one or more cards. Not every vertex needs visuals — only add them where they meaningfully aid retrieval. See the Visual Cards section above for the heuristic and format.

## Comparison Cards (for confusable concepts)

When two concepts are easily confused (lists vs tuples, affect vs effect, major vs minor chords):

Front: "Compare [A] and [B]: what is the key difference and when would you use each?"
Back: Clear comparison with the distinguishing criterion and usage context.

These combat interference between similar concepts. Place them AFTER both concepts have been introduced.
