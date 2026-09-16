# Architecture and compatibility

Status: reviewed design baseline v0.2. Decision authority is [DECISIONS.md](DECISIONS.md); implementation gates are [IMPLEMENTATION.md](IMPLEMENTATION.md).

## Product loop

Parent intent -> native learning planner -> validated content/session pack -> tablet runtime -> private observations -> learning and motivation projections -> next plan.

The ordinary child-action loop is local: input -> deterministic evaluation -> immediate feedback -> bounded branch. Online reasoning may plan ahead or answer an open question. Media generation never blocks routine gameplay. The app remains useful without ChatGPT, KG, Idea Factory, Helix, AmazeBook or a live model connection once a valid session pack is downloaded.

## Ownership, not a new collection of microservices

| Owner | Owns | Must not own |
| --- | --- | --- |
| learn-anything | Shared competency definitions, pedagogy/evidence policies, planning and assessment contracts | Child UI, family database deployment, fictional rewards |
| kids-learn-everything | PWA, device adapters, application API, private profiles/events, content activation, game/world inventory | An independent curriculum ontology or generic portfolio control plane |
| AmazeBook | Reusable creative character/scene records and publication renderers | Reading assessment or mandatory in-session orchestration |
| chat-control-plane | Project/partition resolution, bounded routing, exact-target Git actions, result receipts | A duplicate learning planner, automatic release authority |
| KG / Idea Factory | Optional owner-selected knowledge and idea context | Mastery writes, child surveillance, automatic curriculum publication |

Start with one application service, one private persistent store, an asset directory/object store and a small job worker. These are logical roles and can share one process/deployment. Do not add message brokers, a universal graph service or a second PM registry merely to match the diagram.

## Five kinds of state

1. **Canonical curriculum:** a versioned competency graph, sources, instructional policies, assessment definitions and coverage map. Reusable, not child-specific.
2. **Observation ledger:** immutable attempts and explicit corrections/retractions, with assistance, task, scorer, modality and exact content versions. Private.
3. **Learner projections:** competency estimates and a separate motivation model, both derived from observations with provenance and uncertainty. Unknown is not zero competence.
4. **World state:** creations, companions, collectibles and fictional continuity. A sticker is not a mastery transition.
5. **Session state:** pinned pack, deterministic branch history, local event sequence and a checkpoint. Session-end summaries are not the only durable state.

The application persists family state; Learn Anything defines and implements its interpretation. Projection ownership does not require storing user data in a repository. Sharing a canonical graph never shares learner overlays.

## Canonical competency versus pedagogy

Do not fork the same competency by age. But do not claim that every language, representation or context is interchangeable: reading graphs specify language/writing system; number concepts can have representation-specific evidence. Locale and standards mappings are metadata. Accommodation and presentation policies can vary without rewriting the skill's meaning.

Prerequisites represent reviewed instructional constraints, not universal laws. Distinguish hard, soft, alternative and co-development relationships. Only the released hard-prerequisite relation must be acyclic. Related, reinforcement and transfer relationships may form cycles. Model task conditions explicitly; an observed success does not license automatic mastery of all ancestors or semantically similar nodes.

A plan first satisfies prerequisite, accessibility, safety, direct-evidence and offline-readiness constraints. Only then does it rank admissible experiences using learning value and motivation. Engagement cannot override a missing prerequisite or create assessment evidence.

## Existing plugin remains authoritative

The current marketplace pipeline remains:
Domain Assessor -> Skill Researcher -> Learner Calibrator -> Curriculum Architect -> Material Forge -> Dashboard / Training Conductor.

Keep `learn-anything/active-skill.json` and `learn-anything/<skill-slug>/` adult resolution intact. Do not redirect the adult global active-skill pointer when a child changes profile. The future application supplies an explicit private `{learner_id, domain_id, graph_release_id}` partition on every state-bearing request and verifies ownership server-side.

Keep the maximum Researcher/Calibrator loop at two, preserve working state on failure, and retain existing adult simplified fallbacks. New child mode must not turn an unreviewed fallback graph or self-report overlay into an approved learning pack. When research/calibration is incomplete, continue only an already admitted pack, select an approved simpler activity, or return a blocked/unknown state.

Extend native components rather than introducing a competing orchestrator: Researcher gets a canonical-domain research mode; Calibrator writes observations plus estimates; Architect receives policy and motivation context; Forge emits declarative activities; Conductor plans packs and integrates observations. The local PWA executor is not another AI planner.

The adult April 2026 Datastar/D3/FastAPI document stays a draft for the adult workstation. It neither selects the child frontend nor mandates PostgreSQL/AGE/PGVector in the MVP.

## Migration and release boundaries

Legacy schemas use draft-07 and currently combine graph vertices with learner overlays. Documentation prototypes use draft 2020-12 and are separate. A future import adapter preserves original IDs, source labels and files, marks legacy estimates as imported, never fabricates attempt evidence, and supports dry-run plus backup. No silent in-place migration.

Separate events: authored -> structurally validated -> content reviewed -> parent-approved release digest -> published -> downloaded -> locally verified -> activated. Git commit, CI success and parent release approval are different events. Activation swaps packs atomically at a safe boundary; an active session stays on its pinned versions.

An acknowledged private server event is durable independently of projection success. Rebuild projections from the ledger and policy version; use request IDs and payload hashes for idempotency, not a promise of network-wide exactly-once processing.
