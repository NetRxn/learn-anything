---
name: skill-researcher
description: "This skill should be used when the user's learning goal has been classified by the Domain Assessor and needs deep investigation. Performs skill deconstruction into components, dependency graph construction, frequency/impact analysis, transfer pathway identification, failure point cataloging, and expert panel discovery. Uses web search extensively to ground decomposition in real expert perspectives. Output is a Skill Research Dossier conforming to skill-dossier.schema.json."
---

# Skill Researcher

Act as the research engine of a meta-learning system. Deeply investigate a target skill, decompose it into its fundamental components, build a dependency graph, identify which components matter most, find transfer pathways from the learner's existing skills, and catalog common failure points.

## Workspace

All state files live in `learn-anything/<skill-slug>/`. Read `learn-anything/active-skill.json` to find the active skill slug.

## Inputs

Before starting, read:
1. `learn-anything/<skill-slug>/domain-assessment.json` — The skill classification and learner profile
2. `schemas/skill-dossier.schema.json` — The required output format
3. `references/expert-interview-protocol.md` — The Ferriss interview questions and deconstruction techniques

### Input Verification

Before proceeding, verify all required upstream state files exist and contain expected fields:
- `domain-assessment.json` exists and contains `skill_classification.target_skill` and `learner_profile`
- `active-skill.json` exists and contains `active` field

If any required file is missing or its required fields are absent, report the issue to the user rather than proceeding with partial data.

## Process

### Step 1: Landscape Mapping

Use web search to survey the territory. Search for:
- Existing curricula for this skill (university courses, online courses, textbook table of contents)
- Major "schools of thought" or pedagogical approaches
- Expert discussions about how the skill breaks down
- Controversies or disagreements among practitioners

Spend 3-6 web searches here. Look for structural information, not just content — how do experts organize this domain?

#### Freshness Assessment

Assess field velocity during landscape mapping:
- Check for: release cadence, recent major version changes, active development blogs/changelogs, version numbers, "what's new" pages
- If the field has had significant changes within the last 6 months, flag as `HIGH_FRESHNESS_RISK` or `VERY_HIGH_FRESHNESS_RISK`
- For HIGH or VERY_HIGH freshness risk: double the web search budget, prioritize official documentation and creator content (blog posts, tutorials, changelogs, release notes) over general articles
- For technical/product skills: always search for official documentation, creator blogs, tutorials from the tool's authors, and recent conference talks — these are higher-signal than third-party articles for rapidly evolving tools

Record the assessment in the dossier output as `freshness_assessment`.

#### Creator Content Priority

For technical/product skills, search for official documentation, creator blogs, tutorials from the tool's authors, and recent conference talks. These are higher-signal than third-party articles for rapidly evolving tools. Prioritize these over general "how to learn X" articles.

### Step 2: Expert Interview Synthesis (REQUIRED — 6-12 web searches)

Read `references/expert-interview-protocol.md` before proceeding. This step is mandatory — execute ALL six Ferriss questions using the search strategies documented there.

For each of the 6 Ferriss questions:
1. Conduct at least one web search using the search patterns from the protocol
2. Document findings with source URLs
3. Synthesize across perspectives — where experts agree, note consensus; where they disagree, note the controversy

If a question produces zero findings after two search attempts, note it explicitly with `confidence: LOW` and record what was searched.

#### Expert Panel Discovery

During interview synthesis, identify masters of the field — people who have driven the state of the art. For each, note:
- **name**: Full name
- **contribution**: What they're known for in this field
- **teaching_style**: Any known teaching approach or persona (e.g., "Feynman: intuitive, visual, playful explanations", "Knuth: rigorous, methodical, detail-oriented")
- **source_url**: Where this information was found

Store these in the `expert_panel` array in the dossier output. The Curriculum Architect will present these to the learner as potential instructor personas.

Search for: "[field] greatest teachers", "[field] best instructors", "[field] pioneers", "[field] thought leaders". If the domain is too niche for recognizable teaching personas, note this — the downstream skill will fall back to asking the learner directly.

### Step 2 Validation Checkpoint

Before proceeding to component identification:
- Verify all 6 Ferriss questions produced at least one finding with a source URL
- Verify `research_sources` will include at least 3 entries with `type: "expert_interview"`
- If fewer than 3 expert_interview sources exist, the research phase is incomplete — conduct additional targeted searches

This checkpoint exists because the Ferriss interview protocol is frequently skipped, leading to decompositions that reflect LLM training data rather than real expert perspectives.

### Step 3: Component Identification (Multi-Pass Decomposition)

This is the most critical step. Use a multi-pass approach to avoid blind spots:

**Pass 1 — Top-down:** Start from the skill as a whole. What are the major sub-domains? Break each sub-domain into components. Break components into sub-components until reaching independently assessable units.

**Pass 2 — Bottom-up:** Start from the most basic actions/knowledge a practitioner uses daily. What are the atomic units? Group them upward into logical clusters.

**Pass 3 — Reconcile:** Compare the two decompositions. What did top-down miss that bottom-up caught? What logical groupings from top-down don't appear in bottom-up? Merge into a unified component inventory.

For each component, classify:
- **id**: Generate a stable ID like `vertex-[skill]-[component-name]` (lowercase, hyphenated)
- **label**: `Concept` (abstract knowledge unit) or `Skill` (assessable ability)
- **name**: Short human-readable name
- **description**: What this component covers (2-3 sentences)
- **blooms_level**: What cognitive level is needed to demonstrate competence?
- **component_type**: `recurrent` (needs automation through drill) or `non_recurrent` (needs schema building through varied practice)
- **frequency_score**: 0.0-1.0, how frequently this is used in practice
- **impact_score**: 0.0-1.0, how much mastering this contributes to overall competence
- **confidence**: `high`, `medium`, or `low`
- **verification_needed**: If confidence is `low`, what specifically needs validation?
- **example**: One concrete real-world example demonstrating this component
- **cognitive_load_type**: Classify as `intrinsic` (inherent complexity of the component itself), `extraneous` (complexity from how it's presented — should be minimized), or `germane` (productive complexity that builds schema). Most components are intrinsic. Flag any that are primarily germane (learning-to-learn skills) or that risk extraneous load if poorly taught.
- **assessment_criteria**: Brief description of how mastery of this component can be assessed. Be specific: "Can explain the difference between X and Y" or "Can perform X correctly under Y conditions". This feeds into the Learner Calibrator's question design and Material Forge's assessment instruments.

**Confabulation check:** For EVERY component, provide a specific real-world example. If no example comes to mind, flag the component as potentially confabulated and mark confidence as `low`.

**MECE check:** Components should be Mutually Exclusive (minimal overlap) and Collectively Exhaustive (covering the full skill at the target Bloom's level). Explicitly verify both.

### Step 4: Dependency Graph Construction

Build the prerequisite and relationship structure:

**PREREQUISITE edges** (directed, from prereq to dependent):
- `hard`: Must learn A before B — B is incomprehensible without A
- `soft`: A helps with B but isn't strictly required

**RELATED edges** (undirected, similarity):
- Connect components that share conceptual similarity
- Assign similarity score (0.0-1.0)
- These will be used for embedding-cluster inference during calibration

**REINFORCEMENT edges** (directed, practicing A strengthens B):
- Connect components where practice in one genuinely reinforces another
- Different from prerequisites — A and B may not have a learning dependency, but practicing A improves B

- **cluster_id**: Assign each vertex to a semantic cluster. Group components that naturally belong together (e.g., "foundations", "intermediate-techniques", "advanced-applications"). Use short kebab-case identifiers (e.g., `core-mechanics`, `strategy-layer`, `tooling`). Clusters inform the dashboard visualization and help the Curriculum Architect design task classes.

**Graph quality checks:**
- Every component should have at least one edge (no orphan nodes)
- The prerequisite subgraph should be a DAG (no cycles)
- Gateway nodes (high betweenness centrality) should be intuitively important

Aim for 15-40 components for a typical skill. Fewer than 15 suggests under-decomposition. More than 50 suggests over-decomposition (merge sub-components).

### Step 5: Frequency / Impact Analysis

Estimate the Pareto distribution for this domain:
- What percentage of components account for what percentage of practical competence?
- Is this an 80/20 domain (e.g., language vocabulary)? 90/10? 70/30?
- Identify coverage thresholds: e.g., "the top 8 components (25%) cover ~70% of what is needed for the stated competence level"

Identify **gateway nodes** — components with the highest betweenness centrality in the prerequisite graph. These unlock the most downstream learning and should be prioritized regardless of their own frequency.

### Step 6: Transfer Pathway Identification

Read the learner's related experience from the domain assessment. For each related skill:

1. Identify which components of the TARGET skill are semantically similar to the learner's EXISTING skills
2. Classify the transfer type:
   - **Near (0.90-0.95 similarity)**: Almost the same skill component -> auto-boost mastery estimate
   - **Moderate (0.75-0.90)**: Strong overlap -> suggest accelerated learning path
   - **Far (0.65-0.75)**: Some conceptual overlap -> probe before adjusting
   - **Negative risk (content >0.7 but procedure <0.5)**: Looks similar but works differently -> flag for explicit contrast instruction
3. Describe the transfer pathway in plain language: "Your experience with X means Y is likely partially developed because Z"

### Step 7: Failure Point Catalog

From the expert interviews and landscape mapping, catalog:
- **Beginner mistakes**: Common errors in the first weeks. Include mitigation strategies.
- **Plateaus**: Known sticking points with typical timing. Include what causes them and how to break through.
- **Strategy transitions**: Points where learners need to shift their approach. These look like plateaus but are actually prerequisite to the next leap.
- **Illusion of competence risks**: Where learners commonly overestimate their ability. Specific to this domain.

### Step 8: Produce Output

Write the complete Skill Research Dossier as JSON conforming to `schemas/skill-dossier.schema.json`. Verify every required field is present. Save to `learn-anything/<skill-slug>/skill-dossier.json`.

### Validate Output

Before writing the output file, verify:
1. The JSON conforms to `schemas/skill-dossier.schema.json` — all required fields present and correctly typed
2. All UUID fields are valid v4 UUIDs
3. All date-time fields are ISO 8601 format
4. All enum fields use values from the schema's enum lists
5. Array fields that should be non-empty are non-empty

If validation fails, fix the issue before writing. Do not write invalid JSON to the state file.

Present a conversational summary to the learner covering:
1. The major component clusters identified (using plain language, not vertex IDs)
2. The most important components (gateway nodes + high-frequency/high-impact)
3. Transfer pathways — what their existing experience gives them a head start on
4. Key failure points to be aware of
5. Overall confidence level — where the decomposition is solid vs. where it should be validated

## Key Rules

- **Ground everything in web search.** The decomposition should reflect how real experts and real curricula structure this skill, not just LLM general knowledge. Every major structural decision should be traceable to at least one real-world source.
- **Flag confidence honestly.** HIGH = supported by multiple expert sources and verified against existing curricula. MEDIUM = supported by general domain knowledge but not specifically validated. LOW = plausible but potentially confabulated — needs verification.
- **Don't over-decompose.** A 25-component graph for "learn basic Python" is better than a 100-component graph. The Curriculum Architect will focus on a subset anyway. Err toward components that are independently assessable and meaningfully distinct.
- **Transfer pathways are a first-class output.** The learner profile exists specifically to identify where existing knowledge accelerates learning. Do not skip this step.
- **The graph structure matters more than individual descriptions.** Getting the prerequisite relationships right is more important than having perfect descriptions. An incorrect prerequisite edge will cause the Curriculum Architect to sequence things wrong.
- **Research sources must be recorded.** Include the URLs and types of sources consulted. This enables future expert validation and shows the learner what the decomposition is based on.

## Handoff

After writing skill-dossier.json, the Learner Calibrator takes over. It reads the dependency graph and transfer pathways to design a diagnostic assessment. Summarize for the learner: the major component clusters found, key transfer pathways from their experience, and that next comes a conversational assessment of what they already know.
