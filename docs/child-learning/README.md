# Child learning architecture - reviewed baseline v0.2

Date: 2026-09-16. Scope: design, contract prototypes and implementation planning; not a deployed child runtime.

This package supersedes the chat-exported 2026-09-16 architecture package v0.1. The child application is `NetRxn/kids-learn-everything`, a separate repository rather than a long-lived child branch. This directory owns the cross-product learning design; it does not replace the existing plugin marketplace or adult workflow.

## Read progressively

| Question | Start here |
| --- | --- |
| Responsibilities, state and compatibility? | [Architecture](ARCHITECTURE.md) |
| Reading/math graph and research process? | [Pedagogy compiler](PEDAGOGY-COMPILER.md) |
| Session, evidence, motivation and authoring contracts? | [Contracts](CONTRACTS.md) |
| What is accepted versus proposed? | [Decision records](DECISIONS.md) |
| What to implement, in what order, and test? | [Implementation plan](IMPLEMENTATION.md) |
| What changed in this review? | [Review and sources](REVIEW.md) |
| Machine-readable contract prototypes? | [Contract index](contracts/v0.1/README.md) |

## Authority and delivery

Learn Anything owns curriculum semantics, evidence interpretation and learning policies. The child repository owns its application service, local runtime and private family state. AmazeBook owns optional creative publishing. Chat control-plane routes authorized requests without replacing any native orchestrator. KG and Idea Factory provide optional context, not mastery or release authority.

Git stores reusable curriculum, specifications, source metadata and synthetic fixtures. Real learner observations, profiles, motivational preferences, photos, transcripts and personalized assets belong in parent-controlled application storage, never these source repositories or public CI logs.

Detailed new schemas are PROPOSED, versioned under documentation. They are not installed into `learn-anything-plugin/schemas/`, do not change plugin manifests or the distributable ZIP, and do not activate new runtime commands. Promotion requires a separate compatibility-tested implementation change.

The PWA's framework, graph database, speech backend, image backend and native-wrapper choice remain open. Helix is an optional projection candidate, not an MVP dependency.
