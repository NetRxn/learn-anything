---
description: "Jump straight into a training session for your active skill."
argument-hint: "[optional context or --mode mentor]"
---

The user has invoked `/train` with: `$ARGUMENTS`

Read `learn-anything/active-skill.json` to find the active skill slug.

If no active skill exists, tell the user to start with `/learn <topic>` first.

If an active skill exists, invoke the `training-conductor` skill directly. Pass the user's arguments as session context.

If arguments contain `--mode mentor` or `mentor mode`, instruct the Training Conductor to use Template F (Mentor Conversation) for this session.

Examples:
- `/train` → standard session based on next agenda
- `/train I'm stuck on chord transitions` → focused session on specific topic
- `/train --mode mentor` → relaxed exploratory discussion
- `/train mentor mode` → same as above
