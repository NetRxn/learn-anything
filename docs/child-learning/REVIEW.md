# Review pass and source register

Date: 2026-09-16. Baseline: chat-exported architecture package v0.1; revised package v0.2. This is an author-side consistency and contract review, not an independent educational or security sign-off.

## Corrections incorporated

| Finding in v0.1 | Correction in v0.2 |
| --- | --- |
| New child repository still unnamed | Bind the intended runtime to `NetRxn/kids-learn-everything`; accessibility is a separate publication condition. |
| Same-session generation called post-MVP but required in the first MVP proof | Static/cached assets are the MVP; generative reward lifecycle is G1, with a separately testable prototype. |
| Generic four-state diagram hid observation vs inference | Keep raw observations, estimates, planner decisions and world state distinct and version-bound. |
| Schemas admitted arbitrary objects and ambiguous outcomes | Add typed prototype nodes, bounded fields, explicit unscored outcomes, local positive/negative fixtures and semantic pack checks. |
| Git-first language could imply committing children's data | Restrict Git to reusable artifacts and synthetic fixtures; private app storage holds learner data and personalized packs. |
| Curriculum graph treated as universally age/context independent | Share competencies where meaning matches, but retain language, representation demands, hard/soft/alternative prerequisites and validated mappings. |
| Helix looked mandatory | Optional runtime projection; no graph database blocks the first session runner. |
| Motivation graph described as proof of intrinsic motivation | Observed preferences and hypotheses only; no emotion/dopamine inference or time-on-app objective. |
| Online voice implied all connected tools are usable | Capability-test the actual mode; dictation/tool-capable text chat is a supported-workflow fallback, not an automatic background task. |
| Offline described without storage/OS lifecycle limits | Add HTTPS setup, preflight downloads, foreground retry, eviction recovery and app suspension tests. |
| Media rendering did not distinguish identity/ownership/readiness | Separate persistent creation, generation job, approved media and reveal; retry/cancel/delete and dedup rules. |
| File generation equated to child delivery | Require validation, parent approval, publication, download verification and checkpoint activation. |
| New design might replace native adult pipeline | Additive docs-only proposal; preserve state routing, maximum two calibration loops and existing recovery semantics. |
| Other repository designs could be silently replaced | Pin existing design PRs; keep their native contracts and authority rather than copying PM/knowledge stores. |

## Reviewed repository inputs

- Learn Anything `main`: `46404b01e7a844eeff5a95e84340df9391c9da61`. Read `CLAUDE.md`; checked tree and the previously inspected identical-revision orchestrator, schema, research and web draft. Current repository is a plugin marketplace, not a deployed child app.
- Child runtime repository access must be independently resolved before applying its staged files. No local-only code or undeclared defaults were assumed.
- Integration consumers retain their own private review records. This public package does not reproduce private implementation details or family records.

## Primary external references checked

These are implementation constraints and research entry points, not claims that a full pedagogy corpus or device test was completed.

- OpenAI Voice Mode FAQ: https://help.openai.com/en/articles/20001274 (accessed 2026-09-16). Current Live-mode connected-app limitations make actual mode/tool acceptance necessary; capture speech and execute an authorized request in a supported tool surface when needed.
- WebKit storage policy: https://webkit.org/blog/14403/updates-to-storage-policy/ (accessed 2026-09-16). Quota/persistence APIs do not make browser storage an unconditional durable server substitute.
- WebKit MediaRecorder: https://webkit.org/blog/11353/mediarecorder-api/ (accessed 2026-09-16). This historical implementation note is not an exhaustive current codec matrix; feature-detect and test supported encodings.
- W3C media capture: https://www.w3.org/TR/mediacapture-streams/ (accessed 2026-09-16). Secure-context and permission requirements inform device preflight.
- IES foundational reading guide: https://ies.ed.gov/ncee/wwc/practiceguide/21
- IES K-3 comprehension guide: https://ies.ed.gov/ncee/wwc/practiceguide/14
- IES early mathematics guide: https://ies.ed.gov/ncee/wwc/practiceguide/18
- IES guide index: https://ies.ed.gov/ncee/wwc/practiceguides

The IES HTML pages identify sources for the compiler work. Full document/page extraction, high-school coverage and edge-level evidence review remain future research tasks. Do not cite this pass as completed P-12 competency mapping.

## Verification performed

`python docs/child-learning/contracts/v0.1/validate.py` checks seven schemas, six synthetic positive examples and rejects 36 selected invalid mutations. It uses only the local schema bundle. Relative documentation links and code fences are also checked during packaging. These checks are not application tests, real child assessments, device/battery benchmarks, provider trials or independent review. Git upload receipts/readback are reported separately from validation and merge status.

## Prototype limits

The schema family is deliberately narrower than the target design. Alternative-prerequisite group logic, full competency-graph cycle/reference validation, learner-estimate records, structured motivation observations, character/scene records and release receipts need later versioned contracts. The current six prototypes cannot be admitted as a complete production curriculum or runtime API. Human-readable requirements take precedence over treating a missing prototype field as an implemented feature.
