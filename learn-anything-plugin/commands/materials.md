---
description: "Generate or regenerate learning materials for the active skill"
argument-hint: "[type] [task-class]"
---

The user has invoked `/materials` with: `$ARGUMENTS`

Read `learn-anything/active-skill.json` to find the active skill slug.

If no active skill exists, tell the user to start with `/learn <topic>` first.

If an active skill exists, read `learn-anything/<slug>/learning-plan.json` to determine the curriculum structure.

**Parse arguments:**
- If no arguments: generate all missing material types for all task classes
- If a type is specified: generate only that type. Valid types: `worked-examples`, `visuals`, `flashcards`, `assessments`, `practice-sets`, `references`, `encoding-aids`, `all`
- If a task class is specified (e.g., `tc1`, `tc2`): generate only for that task class
- Combinations work: `/materials flashcards tc2`, `/materials all`, `/materials visuals tc1`

**Determine what exists vs what's missing:**
- Check `learn-anything/<slug>/materials/` for existing files by type
- Check `learn-anything/<slug>/srs-cards.json` for existing flashcards
- Report to the user: "You have [X] of [Y] material types for [N] task classes. Missing: [list]"

Invoke the `material-forge` skill with the appropriate scope (full generation for 'all' or missing types, targeted generation for specific type/task-class combinations).
