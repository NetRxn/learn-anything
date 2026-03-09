---
description: "Start or continue learning any skill — the primary interface to the meta-learning system."
argument-hint: "[topic or context]"
---

The user has invoked `/learn` with: `$ARGUMENTS`

Invoke the `meta-learning-orchestrator` skill now. It contains all routing logic, phase detection, handoff protocols, and error recovery. Pass the user's arguments as context — the orchestrator will interpret intent (new skill, resume, progress check, switch, etc.) and route to the correct pipeline component.

Do not duplicate the orchestrator's logic here. Just invoke it.
