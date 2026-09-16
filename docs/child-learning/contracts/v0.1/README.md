# Contract prototypes v0.1.0

These draft-2020-12 prototypes supplement, not replace, the installed plugin's draft-07 schemas. They define six records in [contracts.schema.json](contracts.schema.json); named wrapper schemas reference that single owner. [examples.json](examples.json) contains synthetic fixtures only. No learner placement or instructional claim follows from those examples.

Use Python 3.10+ with `jsonschema>=4.18,<5` and `referencing` available, then run `python docs/child-learning/contracts/v0.1/validate.py` from the repository root. The helper resolves only the local bundled schema; it does not fetch schemas, call providers or inspect private data.

The helper tests schema integrity, positive examples and selected invalid mutations, including session target/asset/answer/termination consistency. It does not implement a curriculum compiler, authentication, scoring service, offline runtime, full graph validation or release admission. Those remain the acceptance cases in [the implementation plan](../../IMPLEMENTATION.md).

Only instruction, choice and end node kinds are admitted by this prototype. Extend via reviewed typed variants; do not bypass it with free-form JavaScript, HTML or arbitrary activity configuration.

A consumer must pin the producer commit, version and digests. This directory is a design-development contract, not a published production release.
