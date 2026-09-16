# Pedagogy compiler and Reading / Mathematics P-12 coverage

Status: design specification. The complete P-12 graphs are NOT contained in this package. Contract examples are synthetic, not released instruction.

## Build the map before improvising lessons

Publish one maintained graph per domain/language with standards mappings and an explicit coverage report. Grade bands are navigation views, not eligibility gates. A learner can be ahead on one strand and need support on another.

Reading coverage spans oral language/listening, phonological and phonemic awareness, grapheme-phoneme mapping, decoding, word recognition, spelling/encoding, morphology, fluency, vocabulary, syntax, text structure, comprehension, inference, evidence use, cross-text/disciplinary reading and research literacy. Writing is linked where it supports reading; a complete composition curriculum is a separate future domain, not silently included.

Math spans number/quantity, counting/cardinality, operations, place value, fractions, decimals/percent, ratio/proportional reasoning, measurement, geometry, data/statistics/probability, expressions/equations, functions, algebra, proof and modeling. High-school coverage must name its course tracks, including optional advanced statistics/calculus, rather than equating P-12 with one required linear sequence. Conceptual understanding, fluency, representation and application get distinct success criteria where needed.

## Source and graph workflow

1. **Register:** record source ID, title, issuer, exact URL/version, language/age/task scope, rights/access status and retrieval state. Standards describe expectations; they do not by themselves establish an instructional dependency.
2. **Extract:** propose competencies, instructional claims, relationships, assessment methods and common errors with exact source locators. Preserve source observations separately from agent interpretation.
3. **Normalize:** deduplicate with reviewed mappings, not embedding similarity alone. Keep stable IDs; semantic changes require a revision/migration decision.
4. **Reconcile:** inspect prerequisites, alternatives, missing strands, representation dependencies, conflicting recommendations and inaccessible evidence. Record uncertainty rather than making every proposed edge hard.
5. **Design evidence:** define what an independent response demonstrates, what assistance changes, and how delayed/novel-item evidence differs. Do not publish answer-bearing teacher materials to external media providers.
6. **Review and compile:** schema validation plus semantic graph/assessment checks, then a named content review. An agent checking its own output is an author check, not independent acceptance.
7. **Release:** pin graph, source register, policy, assessment bank and compiler versions with hashes. Emit a coverage matrix: outlined / sourced / assessed / reviewed / playable. A database projection is disposable and reproducible.

Suggested responsibilities map to native Learn Anything skills: Researcher coordinates source/extraction/reconciliation agents; Calibrator owns learner probes; Architect attaches sequencing policy; Forge produces items/activity variants; Conductor consumes admitted releases. Stop targeted calibration research after the native maximum two loops and preserve unresolved gaps.

## A-to-B plan from strengths

Resolve the target competency and the learner's directly supported strengths. Walk backward through applicable prerequisite groups, identify the nearest admissible frontier, select a small number of probes when uncertainty matters, then generate instruction/review/transfer activities. Record why each selected activity is useful and which strength it leverages. Do not infer readiness only from grade or chat fluency.

Progression policy separates instruction, supported practice, independent performance, retention and transfer. An unrelated wrong answer or unclear microphone capture cannot erase established mastery. The MVP can use transparent rules; BKT/FSRS parameters are experimental estimator choices, not default calibrated child measurements.

## Reading content requirements

Keep listening comprehension distinct from independently read comprehension. A decoded word is not proof of passage comprehension. Independent-reader text carries taught grapheme/phoneme patterns, reviewed exceptions and an explicit reading mode; shared-reading text can use richer vocabulary. Generated stories must be checked against those constraints. Reviewed audio must pronounce teaching sounds correctly; a generic narration model is not the authority on phoneme rendering.

Do not require fully developed oral phonemic awareness as a universal blocking gate before any letter exposure. Sequencing relationships must support interleaved/co-developed skills where the selected pedagogy permits them.

## Math content requirements

Do not let literacy or fine-motor demands accidentally become the math gate. Bind evidence to representation and scaffolding. Distinguish quantity understanding from numeral recognition and a memorized fact from an explainable strategy. Include multiple representations and later unfamiliar applications, with accommodations recorded rather than counted as cheating.

## Initial source register

These official HTML guide pages were checked on 2026-09-16. Full-guide/page-level extraction remains the compiler's work, not completed research in this PR.

| ID | Source | Scope / intended use |
| --- | --- | --- |
| IES-R21 | https://ies.ed.gov/ncee/wwc/practiceguide/21 | K-3 foundational reading; initial instructional recommendations |
| IES-R14 | https://ies.ed.gov/ncee/wwc/practiceguide/14 | K-3 reading comprehension; keep comprehension distinct from decoding |
| IES-M18 | https://ies.ed.gov/ncee/wwc/practiceguide/18 | Preschool/kindergarten math; developmental progressions and monitoring |
| IES-INDEX | https://ies.ed.gov/ncee/wwc/practiceguides | Discovery queue for older grades and uncovered strands |

Next register preschool language/literacy, adolescent reading, fractions, algebra and jurisdiction-specific standards. No proprietary Mentava or Alpha curriculum is assumed available; product inspiration is not a source for uninspected prerequisite edges. Keep references and permitted excerpts in Git, not an indiscriminate archive of third-party books.

## First release and extension gate

First validate a few synthetic nodes, then research roughly 20-50 competencies per early-domain slice with actual source/assessment coverage. This is an implementation target, not a claimed inventory. Expand the graph independently of playable content: the full P-12 map can advance while the first tablet release teaches a narrow slice. Track map completeness and activity coverage separately.
