# Decision records and open choices

Namespace: CL-ADR. Date: 2026-09-16. Accepted direction records the owner's conversation; detailed contract/implementation refinements remain proposed until reviewed. Committed documentation is not deployed behavior.

| ID | Accepted direction | Consequence / remaining choice |
| --- | --- | --- |
| CL-ADR-001 | Separate child runtime repo | `NetRxn/kids-learn-everything`; no permanent child branch in learn-anything |
| CL-ADR-002 | Share competency definitions across ages | Separate teaching/evidence/experience policies; preserve language and task distinctions |
| CL-ADR-003 | Motivation is first-class and separate | Planning consumes it; mastery does not derive from engagement |
| CL-ADR-004 | Version reusable curriculum in Git | Private learner state is excluded; runtime graph indexes are projections |
| CL-ADR-005 | Reading P-12 and Math P-12 first | Build coverage maps; implement narrow playable slices before claiming complete instruction |
| CL-ADR-006 | Tablet-first PWA, iPad primary | Native wrapper remains an escape hatch after device testing |
| CL-ADR-007 | UI framework remains open | Compare lightweight DOM/components and a renderer; React is not selected |
| CL-ADR-008 | Wasm is optional, workload-driven | Profile first; no battery-efficiency claim without measurements |
| CL-ADR-009 | No network LLM in routine feedback | Local registered evaluators and bounded branching; optional live escalation |
| CL-ADR-010 | Offline-capable sessions | Downloaded pack required; foreground sync and storage recovery are essential |
| CL-ADR-011 | Asynchronous generation, deterministic fallback | No blocking spinner or assumed tablet background execution |
| CL-ADR-012 | Capability-oriented media adapters | No silent loss of reference identity, approved provider scope or output type |
| CL-ADR-013 | Chat/voice parent authoring | Voice is intent capture; executing tools depends on the actual admitted chat surface |
| CL-ADR-014 | AmazeBook stays separate | Optional downstream studio, not an MVP learning dependency |
| CL-ADR-015 | Scene is cross-media creative primitive | Page/spread/shot are renderings; game sprites need their own asset affordances |
| CL-ADR-016 | Competency, motivation, world and session state differ | Observation ledger is the shared evidence source, not one combined score |
| CL-ADR-017 | Evidence ledger before estimates | Assistance/modality/versioned scorer retained; imported estimates remain imported |
| CL-ADR-018 | Same-session reusable creations after MVP | Immediate usable fallback, later art upgrade; no fixed generation-time guarantee |
| CL-ADR-019 | Separate parent and child surfaces | No model settings, GitHub access or raw mastery probabilities in child gameplay |

## Review refinements - proposed

**CL-ADR-020: content publication is separate from Git.** A parent-approved immutable pack is staged, verified and atomically activated. Code/PR success does not activate learning content. Rationale: prevents unfinished or stale generated lessons reaching the child.

**CL-ADR-021: one private application service initially.** Logical planner, store and worker boundaries need not become separate network services. A full personal KG, Helix and a distributed scheduler are not prerequisites. Rationale: preserve portability without platform overhead.

**CL-ADR-022: docs-only contract staging.** Keep prototypes under documentation until compatibility tests and packaging changes deliberately promote them. Rationale: the existing marketplace remains usable and its ZIP stays consistent.

**CL-ADR-023: generation jobs are server-owned.** The PWA only requests/observes a durable job, reconciles it on foreground and handles late results without duplicate inventory awards. Rationale: no dependence on browser lifetime or guaranteed background sync.

## Open implementation choices

The framework, renderer, Rust/Wasm modules, native wrapper, minimum supported iPadOS/device, private database, Helix deployment mode, default media/speech providers, print fulfillment, mastery estimator and motivation weights are not selected here. Conduct a small hardware/framework spike before resolving them. Specific learning thresholds and durations are tunable policy proposals, not established constants.

A UI framework decision must compare actual activities on the same target iPad: launch/load, input response, accessibility, animation, offline behavior, audio, memory and measured energy/thermal behavior. Existing AmazeBook React code is a reuse factor, not sufficient selection evidence.
