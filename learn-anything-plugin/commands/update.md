---
description: "Update an existing curriculum to reflect new developments in the field"
argument-hint: "[what changed or 'full refresh']"
---

The user has invoked `/update` with: `$ARGUMENTS`

Read `learn-anything/active-skill.json` to find the active skill slug.

If no active skill exists, tell the user to start with `/learn <topic>` first.

If an active skill exists:

1. Read `learn-anything/<slug>/domain-assessment.json` for context
2. Read `learn-anything/<slug>/skill-dossier.json` for current state (check `freshness_assessment` if present)

3. **Archive current state:** Copy all state files (domain-assessment.json, skill-dossier.json, knowledge-graph.json, learning-plan.json, srs-cards.json) to `learn-anything/<slug>/archive/<YYYY-MM-DD>/`

4. **Determine update scope:**
   - If arguments contain "full refresh": invoke full re-research
   - Otherwise: invoke targeted update with the user's description of what changed

5. **Route the update cascade:**
   - Invoke the `skill-researcher` skill with update mode directive and the user's description
   - After dossier update, invoke the `learner-calibrator` skill to re-assess new/changed vertices only
   - After calibration, invoke the `curriculum-architect` skill with update mode to re-sequence
   - Ask user if they want new materials generated for updated content

The update workflow is entirely user-initiated. Freshness assessment from the dossier serves as a guide for the user, not an automatic trigger.
