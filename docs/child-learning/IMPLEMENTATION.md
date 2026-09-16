# Implementation sequence and acceptance

Status: planned work, not a completion ledger. Preserve native project task authority; this plan does not create a second PM database. Each later implementation change records actual test evidence at its exact commit.

## Milestones

| Milestone | Owner | Deliverable | Exit condition |
| --- | --- | --- | --- |
| D0 - documentation | All participating repos | Reviewed boundaries, ADRs, prototypes, source register, placement and pins | Docs/schema checks pass; no runtime activation implied |
| C1 - curriculum contract proof | learn-anything | Synthetic fixtures then source-reviewed early reading/math slices | Unique/resolvable IDs, reviewed prerequisite semantics, assessment and coverage checks |
| R1 - device spike | kids-learn-everything | One instruction and one interactive task on the target iPad | HTTPS install, touch, audio, permission denial, suspend/resume and offline loading tested; choose framework afterward |
| R2 - MVP thin runner | kids-learn-everything + learn-anything | Two isolated profiles, several registered activities, private event sync, static rewards | Complete bounded session offline after download; no LLM in routine feedback |
| A1 - parent authoring | Native planner + chat-control-plane | Parent request for 5-10 levels -> draft pack -> approval -> activation | Exact learner snapshot, supported transport, validation, rollback and stale-input handling |
| M1 - motivation refinement | learn-anything + runtime | Transparent preference observations and admissible activity ranking | Preferences alter presentation/selection but never mastery; stopping and overrides work |
| G1 - post-MVP creation | runtime/media worker | Same-session generative reward and persistent collection | Timeout/offline/duplicate/late results preserve one usable creation and never block play |
| B1 - publishing | AmazeBook | Curated StoryBrief -> editable digital project | Stable characters, selected child contributions, no raw assessment import |
| P12 - parallel research expansion | learn-anything | Complete mapped Reading/Math strands | Explicit source/review/assessment/playability coverage, not a single '100% complete' label |
| X1 - optional optimization | Owning repos | Wasm, speech scoring, animation, print/movie adapters | Actual workload and provider acceptance before activation |

## MVP scope correction

MVP is static/cached art, a small approved curriculum slice, local branching, durable observations, private profiles and a parent-mediated authoring/release loop. A live generative owl, a complete P-12 playable curriculum, independent child speech grading, a personal KG and AmazeBook integration are NOT MVP exit requirements. The contracts leave space for them. A simple preference setting can exist in MVP without an adaptive motivation graph implementation.

## Contract and compatibility gates

C-01: validate positive fixtures and negative mutations for every prototype schema; reject unknown properties and invalid values. C-02: semantic checks reject dangling targets, duplicate IDs, missing assets, absent terminals, unsupported evaluators and unbounded execution. C-03: existing adult workspace resolution, maximum two calibration loops and error recovery remain unchanged. C-04: legacy import is dry-run, preserves source labels and produces no fabricated evidence. C-05: graph release migration retains old session reproducibility and includes deprecation mappings.

## Runtime and sync gates

R-01: airplane mode after verified pack installation completes a session and records evidence. R-02: app termination after an attempt resumes without losing or double-counting that attempt. R-03: retry, reordered batches and concurrent sessions reconcile via event identity, not last-writer-wins mastery. R-04: quota failure/storage eviction yields a truthful recovery state, not a false saved badge. R-05: pack updates cannot mix media/content/scoring versions mid-session. R-06: a forged learner ID or wrong profile cannot read/write the other learner's state. R-07: unavailable mic/noisy input records unscored, not failure. R-08: tab hiding/interruption stops capture and unnecessary animation.

## Authoring and media gates

A-01: ordinary authorized Chat reads a dated progress summary; capture-only voice mode does not claim tool work. A-02: a new request referencing stale state replans or conflicts. A-03: repeated request identity cannot create two releases or provider charges without a deliberate retry policy. A-04: content validation, parent approval and activation have separate receipts. A-05: the child app has no repo or provider credentials. G-01: a late asset updates exactly one creation version; it does not force a replay or award twice. G-02: provider failure retains approved fallback. G-03: cancellation and deleted-child jobs cannot resurrect media.

## Research gates

Every released competency has observable success criteria and source-located instructional/relationship rationale. Separate standards coverage from pedagogy evidence. Explicitly check alternative/co-developed prerequisites, independent versus assisted outcomes, reading-language constraints and math representation demands. Budget research rounds and preserve incomplete coverage.

## Suggested first PRs after this documentation

1. learn-anything: promote a reviewed subset of contracts plus semantic validator and synthetic tests; no broad adult rewrite.
2. kids-learn-everything: device spike and framework ADR, then one offline session with two synthetic profiles.
3. learn-anything/runtime: first source-reviewed content slice and private event integration.
4. chat-control-plane: admit one bounded content-authoring capability using native authorities, not a generic learning service.

Do not deploy infrastructure, enable scheduled research, connect external accounts, spend on generation, place print orders or merge changes solely because these documents exist.
