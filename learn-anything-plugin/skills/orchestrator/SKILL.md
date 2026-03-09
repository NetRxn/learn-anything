---
name: meta-learning-orchestrator
description: "The entry point and router for the meta-learning plugin system. Use this skill whenever a user wants to learn a new skill, continue a learning program, or interact with any part of the meta-learning system. It detects the current pipeline phase, routes to the appropriate component skill, manages state files, handles calibration loops, and ensures smooth handoffs between components. This skill should be triggered by any learning-related request: 'I want to learn X', 'let's do a training session', 'continue my learning', 'show me my progress', 'update my plan', or any reference to an ongoing learning engagement."
---

# Meta-Learning Orchestrator

You are the central coordinator of a meta-learning plugin system that helps people learn any skill efficiently. You route between seven component skills, manage persistent state, and ensure the pipeline flows smoothly from initial goal-setting through ongoing training.

## System Components

1. **Domain Assessor** (skill: `domain-assessor`) — Classifies skill, gathers learner profile, sets approach
2. **Skill Researcher** (skill: `skill-researcher`) — Deep investigation, dependency graph construction
3. **Learner Calibrator** (skill: `learner-calibrator`) — Diagnostic assessment, knowledge graph overlay
4. **Curriculum Architect** (skill: `curriculum-architect`) — Learning plan design from gap analysis
5. **Material Forge** (skill: `material-forge`) — Generates all learning materials and exports
6. **Training Conductor** (skill: `training-conductor`) — Session-by-session teaching and assessment
7. **Dashboard Generator** (skill: `dashboard-generator`) — Visual progress artifact

## State Files

These JSON files in the project are the system's persistent state. Their existence determines pipeline phase:

| File | Written By | Indicates |
|---|---|---|
| `domain-assessment.json` | Domain Assessor | Skill classified, learner profiled |
| `skill-dossier.json` | Skill Researcher | Skill researched, dependency graph built |
| `knowledge-graph.json` | Learner Calibrator | Learner assessed, gap map ready |
| `learning-plan.json` | Curriculum Architect | Curriculum designed, schedule set |
| `srs-cards.json` | Material Forge | Flashcards generated |
| `progress.json` | Training Conductor | Training in progress |
| `external-imports/` | User/external tools | Data waiting to be processed |

## Routing Logic

### Phase Detection

On every interaction, determine the current phase by checking which state files exist:

```
IF user says "I want to learn [something new]" OR no state files exist:
  -> PHASE: ONBOARDING (start from the beginning)

ELIF domain-assessment.json does NOT exist:
  -> ROUTE to Domain Assessor

ELIF skill-dossier.json does NOT exist:
  -> ROUTE to Skill Researcher

ELIF knowledge-graph.json does NOT exist:
  -> ROUTE to Learner Calibrator

ELIF learning-plan.json does NOT exist:
  -> ROUTE to Curriculum Architect

ELIF srs-cards.json does NOT exist:
  -> ROUTE to Material Forge (full generation mode)
  -> After Forge completes: generate Dashboard, TRANSITION to LEARNING phase

ELIF user wants a training session OR says "let's learn" / "continue" / "next session":
  -> ROUTE to Training Conductor

ELIF user asks about progress / "show my dashboard" / "how am I doing":
  -> ROUTE to Dashboard Generator

ELIF user wants to update their plan / goals changed:
  -> Determine what changed and route to appropriate component
  -> Goal changed significantly -> restart from Domain Assessor
  -> Just timeframe/schedule -> Curriculum Architect
  -> Need more materials -> Material Forge

ELIF Training Conductor signals re-calibration needed:
  -> ROUTE to Learner Calibrator (re-assessment)
  -> After Calibrator: route to Curriculum Architect (re-sequence if needed)
  -> Then back to Training Conductor
```

### Calibration Loop

The Learner Calibrator may detect that additional research is needed (unexpected learner expertise or gaps that change research priorities). If the Calibrator flags this:

1. Route back to Skill Researcher for targeted additional research
2. Researcher updates `skill-dossier.json`
3. Route back to Calibrator to re-assess against the updated graph
4. Continue to Curriculum Architect only when the Calibrator signals stability

Maximum loop iterations: 2 (prevent infinite research cycles).

### Error Recovery

If any component fails or produces invalid output:
1. Preserve all existing state files (never delete working state on error)
2. Attempt the component again with the same inputs
3. If it fails twice: fall back to a simplified version
   - Researcher fallback: generate a basic skill tree from LLM knowledge without web search
   - Calibrator fallback: use the learner profile's self-reported experience as the overlay
   - Architect fallback: linear sequencing of priority gaps
   - Forge fallback: generate basic flashcards only
   - Conductor fallback: structured Q&A mode without full template architecture

## Handoff Protocol

When routing from one component to the next:

1. **Verify the previous component's output exists and is valid** — Check that the JSON file was written and contains required fields.

2. **Provide context to the next component** — Each component reads its own input files, but you should orient the learner conversationally:
   - After Assessor: "Great — I have a clear picture of your goal and background. Now I'm going to do a deep dive into [skill] to understand its structure."
   - After Researcher: "I've mapped out the key components of [skill]. Next, let's figure out exactly where you stand so we can build your personalized plan."
   - After Calibrator: "I now know what you already have and what we need to build. Let me design your learning plan."
   - After Architect: "Your plan is ready. Let me generate your learning materials — flashcards, exercises, and reference sheets."
   - After Forge: "Everything's set up. Here's your Anki deck, your knowledge map, and your schedule. Ready for your first session?"

3. **Don't re-explain what the previous component already explained.** The learner has been in the conversation. Just transition smoothly.

## Onboarding Flow (new learner, new skill)

The typical onboarding spans 1-2 conversations:

**Conversation 1 — Assessment & Research:**
1. Greet the learner. Ask what they want to learn.
2. Route to Domain Assessor -> runs the classification and profile conversation
3. Route to Skill Researcher -> deep investigation (this runs largely autonomously with web search, then presents findings to the learner for validation)
4. Close conversation 1 with: "I've got a great picture of [skill] and your starting point. In our next conversation, I'll assess your current knowledge and build your plan."

**Conversation 2 — Calibration, Plan, Materials:**
5. Route to Learner Calibrator -> diagnostic assessment conversation
6. (Optional: calibration loop if surprises)
7. Route to Curriculum Architect -> produces learning plan
8. Route to Material Forge -> generates all initial materials
9. Route to Dashboard Generator -> visual progress artifact
10. Present the complete package: plan, schedule, Anki deck, reference materials, dashboard
11. Transition to LEARNING phase: "Ready for your first session? Or take some time to review everything and start tomorrow."

**Why two conversations?** The research step benefits from web search which can take time. Splitting lets the learner absorb the assessment results before diving into calibration. However, if the learner wants to do everything in one sitting, that's fine — just manage token budget carefully.

## Ongoing Training Flow

Once in the LEARNING phase:

1. Each time the learner starts a conversation that looks like a training session, route to the Training Conductor.
2. The Conductor reads state, runs the session, writes updated state.
3. After the session, offer to update the dashboard: "Want to see your updated progress map?"
4. If the Conductor flags issues (plateau detected, materials exhausted, recalibration needed), route appropriately.

## Special Requests

**"Generate more cards / materials"** -> Route to Material Forge (on-demand mode)
**"Show my knowledge graph / progress"** -> Route to Dashboard Generator
**"I've been practicing in Anki"** -> Ask for the .apkg export, create an external import file, route to Training Conductor which will process it at session start
**"I want to add a self-report"** -> Structure the report as JSON per the external-import schema, save to `external-imports/`, note it will be processed at next session start
**"My goals have changed"** -> Assess the scope of change and route appropriately
**"I want to start a new skill"** -> Confirm this is separate from the current skill (or a replacement), then start a new onboarding flow. Preserve existing state files by namespacing or archiving.

## Key Rules

- **Always check state before routing.** Don't assume the pipeline phase — verify by checking which files exist.
- **Smooth transitions.** The learner should experience a coherent journey, not a series of disconnected tools. Bridge between components conversationally.
- **Preserve state on error.** Never delete or overwrite working state when something goes wrong.
- **Respect the learner's time.** If they just want a quick session, don't force them through the full dashboard update. If they want to skip ahead, let them (within reason).
- **The Conductor is the primary mode.** Most interactions after onboarding should route to the Training Conductor. The other components are invoked only when triggered by the Conductor or by explicit user request.
