# Orchestrator Routing Logic

## Pipeline Phase Detection

Check state files in this order to determine current phase:

```
1. Does learn-anything/active-skill.json exist?
   NO + learning intent → ONBOARDING: Route to Domain Assessor
   NO + no learning intent → Inform user about /learn command

2. Read active-skill.json → get <slug>
   Check learn-anything/<slug>/ for state files:

   Missing domain-assessment.json → Route to Domain Assessor
   Missing skill-dossier.json    → Route to Skill Researcher
   Missing knowledge-graph.json  → Route to Learner Calibrator
   Missing learning-plan.json    → Route to Curriculum Architect
   Missing srs-cards.json        → Route to Material Forge (full mode)
                                    Then → Dashboard Generator
                                    Then → LEARNING phase

3. All files present → LEARNING phase
   Training request    → Route to Training Conductor
   Progress request    → Route to Dashboard Generator
   Update request      → Route to update workflow (see Update Mode)
   Material request    → Route to Material Forge (on-demand mode)
```

## Schema Field Map

Which skill populates which fields:

| Schema File | Field | Producer Skill |
|---|---|---|
| domain-assessment | skill_classification | Domain Assessor |
| domain-assessment | learner_profile | Domain Assessor |
| domain-assessment | approach_strategy | Domain Assessor |
| domain-assessment | identity_frame | Domain Assessor |
| domain-assessment | teaching_preferences | Domain Assessor (Phase C) |
| skill-dossier | graph.vertices | Skill Researcher |
| skill-dossier | graph.edges | Skill Researcher |
| skill-dossier | frequency_analysis | Skill Researcher |
| skill-dossier | transfer_pathways | Skill Researcher |
| skill-dossier | failure_points | Skill Researcher |
| skill-dossier | research_sources | Skill Researcher |
| skill-dossier | freshness_assessment | Skill Researcher (Phase B) |
| skill-dossier | expert_panel | Skill Researcher (Phase C) |
| knowledge-graph | graph (with learner_state) | Learner Calibrator (initial), Training Conductor (updates) |
| knowledge-graph | gap_analysis | Learner Calibrator |
| learning-plan | curriculum | Curriculum Architect |
| learning-plan | schedule | Curriculum Architect |
| learning-plan | motivation_architecture | Curriculum Architect |
| srs-cards | decks, cards | Material Forge |
| progress | sessions, current_state | Training Conductor |

## Two-Conversation Onboarding Model

**Conversation 1: Assessment + Research**
- Domain Assessor: classify skill, gather learner profile (~15-20 min)
- Skill Researcher: deep investigation, dependency graph (~10-15 min with web search)
- Natural stopping point: "I've mapped out the skill. Next time we'll assess what you already know and design your curriculum."

**Conversation 2: Calibration + Plan + Materials + Dashboard**
- Learner Calibrator: diagnostic assessment (~15-20 questions) → typically triggers calibration loop (1-2 rounds of targeted re-research)
- Curriculum Architect: design learning plan (with epitome refinement checkpoint)
- Material Forge: generate initial materials
- Dashboard Generator: create progress visualization
- Transition to LEARNING phase

## Calibration Loop

The Learner Calibrator will typically trigger at least one round of re-research — assessment almost always reveals gaps or surprises the initial research didn't anticipate. Max 2 iterations to prevent indefinite cycling.

1. Calibrator flags re-research triggers (unexpected expertise, gaps in assumed prerequisites, undocumented approaches, low confidence across >30% of vertices)
2. Route back to Skill Researcher for targeted additional research (not a full re-run)
3. Researcher updates skill-dossier.json with new/modified vertices
4. Route back to Calibrator to re-assess only new/changed vertices (preserving existing mastery data)
5. Continue to Curriculum Architect when Calibrator signals stability (no new triggers)

## Training Conductor Feedback Loops

During ongoing training, the Conductor may signal the need to revisit upstream components:

| Signal | Route To | When |
|---|---|---|
| New concepts not in dossier, or field evolved | Skill Researcher (update mode) | Learner encounters undocumented techniques or asks about recent changes |
| Mastery estimates drifted significantly | Learner Calibrator (targeted) | Observed performance diverges from graph across 3+ sessions, or learner reports significant external learning |
| Prerequisite gaps or consistent pacing mismatch | Curriculum Architect (update mode) | Pattern across 3+ sessions, not a single bad session |
| Materials exhausted or wrong format | Material Forge (on-demand) | Via `/materials` or orchestrator routing |
| Plateau detected, protocols exhausted | Curriculum Architect (re-sequence) | Plateau protocols from the learning plan have been tried without improvement |

These are judgment calls based on accumulated evidence, not automatic triggers.

## Handoff Protocol

When transitioning between skills:
1. Verify the outgoing skill's output file was written successfully
2. Orient the learner conversationally: brief summary of what was accomplished, what comes next
3. Do not repeat information the learner already provided
