# Contracts, privacy and execution semantics

Status: proposed contract family v0.1. [Schema prototypes](contracts/v0.1/README.md) are deliberately outside the installed plugin. They are syntax contracts plus test fixtures, not endpoint implementations or calibrated educational measures.

## Records and authority

| Record | Canonical producer / state writer | Important binding |
| --- | --- | --- |
| Competency + relationship | Reviewed pedagogy release | Domain/language, stable ID, revision, success criteria, source locators |
| EvidenceEvent | Device observation, admitted by private application service | Learner, session, device/sequence, item/activity, graph/policy/scorer versions, assistance, outcome |
| LearnerEstimate | Learn Anything evidence integrator | Exact input event set/revision and estimator/policy version |
| MotivationState | Separate motivation projection | Observed choice, context, evidence refs, recency/saturation; never a diagnosis |
| AuthoringIntent | Parent request admitted by native application adapter | Idempotency key, exact learner snapshot, permitted output, constraints |
| SessionPack | Forge/planner, then release admission | Learner partition, graph/policy/runtime versions, bounded graph, assets |
| Creation / CharacterPack | Private creative/application service | Stable identity, asset versions, current usability, parent media policy |
| StoryBrief / SceneManifest | Curated session handoff, then AmazeBook | Selected contributions and media refs, not a raw transcript or learner database |

Observation, model inference and planning decisions must be separately recoverable. Do not manufacture observation records when importing old mastery estimates. Store an explanatory planner decision with admissibility checks and selection components, not just an opaque reward score.

## Session-pack semantic checks

JSON Schema alone cannot establish these invariants; the compiler and runtime admission tests must check them:

- IDs are unique; entry and all branch targets exist; reachable nodes can reach a terminal stop.
- Every competency resolves in the pinned release; every local evaluator is registered for that exact activity version.
- Declared assets resolve to safe relative paths and match byte counts/digests; reject traversal paths, executable script fields and arbitrary remote fetch URLs.
- Required instruction, audio and fallback assets are present before offline-ready is displayed.
- The learner/parent binding comes from the authenticated application, not caller-written JSON or a child profile tap.
- A signed or authenticated approved release manifest supplies the expected pack digest; a self-declared digest is not trust. The MVP can use an authenticated same-origin parent service rather than a separate signing infrastructure.
- Branch loops have an enforced transition/attempt budget and graceful terminal fallback. A correct/incorrect retry cannot loop forever.
- Active session revisions never change mid-attempt. New plans activate at a checkpoint with a new pack revision.

The prototype activity union covers instruction, choice and terminal nodes only. New game mechanics require registered renderers/evaluators and an explicit contract extension; arbitrary JSON is not an activity implementation.

## Evidence and synchronization

An EvidenceEvent records outcome as scored or unscored. Noisy audio, denied microphone permission, skipped activities and inaccessible controls are not wrong answers. The scorer identity/version, response modality, assistance and content identity travel with the observation. Timestamps aid reporting; per-device monotonic sequence numbers preserve local order without trusting clock accuracy.

The local transaction appends the event and updates its session checkpoint together. On reconnect/foreground/manual sync, transmit bounded batches. The server deduplicates `{learner, device, event_id}` and returns durable acknowledgement IDs. Repeated ID plus identical payload returns the same acknowledgement; different payload is CONFLICT. The client removes pending events only after acknowledgement. Do not merge mastery probabilities with last-writer-wins: replay admitted events through the authoritative estimator. Projection failure leaves accepted events durable and visibly pending.

Multi-device sessions retain separate session IDs. Stale plans can still yield historically valid evidence bound to their old release; they cannot silently override the latest curriculum or re-unlock a revoked pack. Quarantine incompatible records with a reason and offer recovery/export rather than discarding them.

Correction/retraction is explicit and triggers projection rebuild. Parent deletion additionally purges private media, derived motivational state and relevant indexes according to the application policy; an append-only ledger is not an exemption from deletion.

## Motivation policy

Represent observed preferences, choice opportunities and context, not assumed inner feelings. Badge-seeking is a reward preference, not proof of intrinsic motivation. Time-on-task is ambiguous; a child may be confused, interrupted or enjoying the activity. Preserve that uncertainty and parent/child overrides. Do not infer emotion from face/voice monitoring in MVP.

Rank only pedagogically eligible activities. Start with a transparent rule-based selector and a small bounded preference model; a graph projection is optional. Do not introduce reinforcement learning to maximize time-on-app, punish stopping, compare siblings, or make a companion depend on continued play.

## Private versus reusable artifacts

Reusable templates, canonical graphs and synthetic fixtures may live in source control. Compiled learner-specific packs, real event logs, motivational affinities, raw photos, recordings, API keys and personalized story projects live outside Git. Opaque IDs remain private when linked to real children. Public CI tests use synthetic values only. Parent progress read tools return a bounded, dated summary on an authorized private surface; no automatic cross-portfolio ingestion.

A parent approval for generation records allowed provider/asset use. A provider fallback must remain inside that allowance and retain required capabilities. Never place credentials or private URLs in content packs.

## Cross-repository pinning

Learn Anything owns this contract family. Consumers pin `{repository, commit, contract_version, relative_paths, digests}` after the producer commit exists; a mutable branch or placeholder is not an admitted release. Until the PRs merge, any consumer lock is a draft-development lock. Copies, when needed for an offline build, are generated and hash-checked, not independently edited.

Keep KG's own Knowledge Interface in KG and control-plane dispatch schemas in chat-control-plane. An AuthoringIntent is the project-owned request payload referenced by a generic capability envelope; it is not a second envelope or PM system.
