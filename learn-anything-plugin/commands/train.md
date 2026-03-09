---
description: "Jump straight into a training session for your active skill."
argument-hint: "[optional context]"
---

The user has invoked `/train` with: `$ARGUMENTS`

Read `learn-anything/active-skill.json` to find the active skill slug.

If no active skill exists, tell the user to start with `/learn <topic>` first.

If an active skill exists, invoke the `training-conductor` skill directly. Pass the user's arguments as session context (e.g., "I'm stuck on chord transitions", "focus on grammar today"). The Training Conductor will load state, plan the session, and run it.
