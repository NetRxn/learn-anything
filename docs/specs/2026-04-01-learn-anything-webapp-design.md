# Learn Anything Web Application — Design Specification

**Date:** 2026-04-01
**Status:** Draft
**Purpose:** Frontend and system design for a self-hostable web application that brings the learn-anything plugin system outside of Claude Code, with a rich visual experience built around the knowledge graph.

---

## 1. Overview

A web application that teaches any skill through knowledge graphs, Socratic dialogue, and adaptive curriculum. The system takes users from "I want to learn X" through structured onboarding, personalized curriculum design, and ongoing adaptive training sessions — all driven by a three-layer knowledge graph (concept ontology + skill graphs + learner state) backed by PostgreSQL.

The web app replaces the Claude Code CLI interface with a visual, multi-modal learning environment. The knowledge graph is the hero — the central artifact around which all learning activity revolves.

**Target:** Open-source, self-hostable. Users deploy their own instance via Docker Compose.

---

## 2. Technology Stack

### Frontend
- **Datastar** (~14KB) — Server-driven hypermedia framework, SSE-based
- **D3.js** — Knowledge graph visualization (runs in `data-ignore-morph` island)
- **No build step** — Single `<script>` tag for Datastar, D3 loaded as module

### Backend
- **FastAPI** (Python) — Async SSE streaming, Jinja2 templates for Datastar HTML fragments
- **SQLAlchemy + asyncpg** — Relational queries
- **Apache AGE** — Graph traversal, centrality analysis, shortest path, community detection
- **PGVector** — Embedding similarity for transfer detection

### Database
- **PostgreSQL** with AGE and PGVector extensions — bundled via Docker Compose

### LLM Integration
- **MVP:** Claude Agent SDK (primary provider, system designed for Claude)
- **Roadmap:** LiteLLM provider behind a shared `LLMProvider` interface, activated once supply chain concerns are resolved (see Section 12)
- Provider selection via web UI settings, not `.env` files

### Progressive Web App
- Service worker for offline material access
- Cache-first for stable data (graph structure, materials, lectures)
- Network-first for dynamic data (mastery overlay, progress state)
- Network-only for real-time (SSE streams, training sessions)
- Background sync for offline flashcard review data

### Authentication
- Local accounts with bcrypt + per-user salts (always on, zero-config)
- OAuth2 providers (Google, GitHub) activate when credentials are configured via web UI
- `SINGLE_USER=true` mode skips login page for personal deployments
- All secrets encrypted at rest with AES-256-GCM

---

## 3. Three-Layer Knowledge Graph

The graph architecture extends the existing plugin's dual-layer model with a shared concept ontology for cross-skill transfer learning.

### Layer 1: Concept Ontology (shared, grows across skills)

Domain-independent knowledge nodes that multiple skills reference.

```
(:Concept {
    id, name, description,
    abstraction_level,          -- concrete → abstract
    bloom_level,
    version: int,
    created_at, updated_at, updated_by,
    field_freshness: enum       -- stable / evolving / volatile
})
-- PGVector embedding on description for similarity detection
```

- Hierarchy via `GENERALIZES` edges
- Cross-concept similarity via `SIMILAR_TO` edges (auto-detected by PGVector cosine threshold)
- Each concept is versioned independently — `version` increments on modification, old versions archived

### Layer 2: Skill Graphs (per-domain decomposition)

Skill-specific nodes created by the Skill Researcher, linked to concepts.

```
(:SkillNode {
    id, name, domain, description,
    component_type,             -- recurrent / non_recurrent
    bloom_level,
    frequency_score, impact_score,
    version, created_at, updated_at, updated_by,
    field_freshness
})
-- PGVector embedding on description
```

**Edge types within and across layers:**
- `PREREQUISITE {type: hard|soft, strength}` — within domain
- `EMBODIES {strength, transfer_type}` — skill node → concept
- `SIMILAR_TO {cosine, transfer_type}` — concept ↔ concept (auto-detected)
- `GENERALIZES` — concept hierarchy
- `REINFORCES {strength}` — cross-domain mutual benefit
- `NEGATIVE_TRANSFER {risk, mitigation}` — interference between skills

**Full edge descriptions stored** — not just labels, but the *why* of each connection (e.g., "Symmetry breaking enables EFT power counting — Goldstone modes are the low-energy DOF").

### Layer 3: Learner State (overlay on both layers)

Mastery tracking on every concept and skill node.

```
(:LearnerState {
    mastery_probability: 0.0-1.0,
    mastery_category,           -- not_started / attempted / familiar / proficient / mastered
    confidence: 0.0-1.0,
    evidence_count, last_assessed, evidence_summary,
    fsrs_difficulty, fsrs_stability,
    bkt_p_transit, bkt_p_slip, bkt_p_guess,
    transfer_boost,
    source                      -- calibration / assessment / conductor / anki_import / self_report / propagation / cluster_inference
})
```

- Full mastery transition audit trail
- Transfer boost tracking with source attribution
- Mastery propagates bidirectionally: master a skill node → concept gets boosted → other skill nodes embodying that concept get transfer credit

### Transfer Detection

When a new skill is researched, every node gets embedded via PGVector. Cosine similarity against all existing concept nodes:

| Cosine | Transfer Type | System Action |
|--------|--------------|---------------|
| > 0.85 | Near transfer | Auto-boost mastery estimate |
| 0.70–0.85 | Moderate | Probe first, then adjust |
| < 0.70 | Independent | Learn fresh |

**Compound interest:** Each new skill benefits from a richer concept layer. The system improves at curriculum design the more the user learns.

### References as Graph Nodes

```
(:Reference {
    id, type, title, url,
    author, date_published, date_accessed,
    credibility: enum,          -- peer_reviewed / expert_opinion / community / anecdotal
    content_hash                -- detect if source has changed
})

(:SkillNode|Concept)-[:SOURCED_FROM {relevance, excerpt, page_or_timestamp}]->(:Reference)
```

- Per-node provenance — track which paper/video/textbook backs each concept
- Staleness detection via content_hash
- Credibility weighting for conflict resolution
- Feeds the frontend — learners can access source material directly

### Materials as Graph Nodes

```
(:Material {
    id, type,                   -- lecture / flashcard_deck / worked_example / video / exercise / reference_sheet / visualization
    title, format,              -- markdown / apkg / svg / mp4 / youtube_embed
    source: enum,               -- generated / curated / external
    url_or_path,
    created_at, version,
    bloom_level,
    effectiveness_score         -- updated based on learner outcomes
})

(:Material)-[:TEACHES {
    depth: enum,                -- introduction / reinforcement / mastery / assessment
    modality: enum              -- visual / auditory / kinesthetic / reading / interactive
}]->(:Concept | :SkillNode)

(:Material)-[:PREREQUISITE_MATERIAL]->(:Material)
(:Material)-[:CITES]->(:Reference)
```

- Smart material recommendation by concept, modality, and effectiveness
- Gap detection: "concept X has no visual materials"
- Materials inherit staleness from their source references

---

## 4. Frontend Layout & Modes

### Overall Pattern

Mode-based full-screen layout with top navigation tabs. Each mode gets the full viewport. Skill switcher in the top bar with "This Skill / All Skills" graph toggle.

### Visual Identity: Observatory + Neural

**Aesthetic direction:** Knowledge as a star chart / celestial map.

- **Background:** Static high-res celestial image (Milky Way panorama), darkened to 15-25% opacity with palette-matched tint overlay. Parallax-shifted at 0.15x rate when user pans the knowledge graph. CSS gradient nebula as fallback.
- **Nodes:** Bold Neural-style treatment — strong radial gradients with bright highlight points, prominent glow halos, breathing pulse animations. Node size scales with importance (frequency × impact).
- **Edges:** Prominent constellation-style lines — the visual backbone of the graph. SVG glow filters, color-coded by type (blue for prerequisites, teal for reinforcement, violet dashed for transfer). Labeled with edge type on dark pill backgrounds.
- **Color palette:** Deep space blacks (#04060e), warm gold accents for interactive elements, mastery colors: teal (mastered), blue (proficient), amber (familiar), coral (attempted), gray (not started).
- **Typography:** Cormorant Garamond (serif display), DM Sans (body), JetBrains Mono (data/code).
- **Texture:** Subtle grain overlay for depth. No starfield dots (compete with nodes).

**Tiered rendering:**
1. Desktop: Full celestial background with parallax
2. Mobile: Static CSS gradient nebula (no parallax, no large image)
3. Reduce-motion: Static background, no breathing animations

### Explore Mode

Knowledge graph is the hero. D3 renders in a `data-ignore-morph` island. Three interaction states on one surface:

**Single click:** Node details in right panel — full edge descriptions (the *why* of each connection), mastery state, materials links, "Train on this topic" button. Connected edges highlight on graph.

**Multi-select (drag or shift+click):** All internal edges with full context, external edges dimmed, aggregate mastery, gap analysis. **"Synthesize with LLM" button** asks the LLM to explain how the selected concepts relate.

**Lesson pre-selection:** Session agenda auto-highlights its scope on the graph. Non-scope nodes dim. Panel shows narrative context (why these concepts are grouped), retrieval probes from prior sessions, "Begin Session" button.

These compose naturally — default is browse, hold shift or drag to multi-select, open a lesson and the graph auto-highlights.

### Train Mode

Resizable split panel with draggable vertical divider. Default ratio: 30% voice chat / 70% content. User adjusts to preference.

**Left panel (chat):** Voice-first input (mic button primary, text fallback). Session template indicator. Socratic back-and-forth with instructor persona. Compact message bubbles.

**Right panel (content):** AI-controlled, with tabs: Worked Example, Diagram, Graph, Video, Flashcards. The LLM decides what's on the right based on the current teaching moment:
- Worked examples with backward fading (steps hide progressively)
- Embedded YouTube videos with AI annotations and pause-and-discuss flow
- Diagrams and SVG visualizations
- Interactive flashcard review
- Mini knowledge graph showing focus nodes with live mastery updates

### Materials Mode

Browse/search hub for all generated and curated content. Organized by skill, type, curriculum position, modality.

**Inline feedback system on every material element:**
- Per-step/per-card: thumbs up, comment, or flag button
- Flagging with context: user writes what's wrong, gets options to regenerate, ask LLM to expand, edit directly, or dismiss
- Batch actions: regenerate all flagged items, LLM review entire deck, re-export Anki
- Quality stats: approved/flagged/unreviewed counts per material set

### Progress Mode

Dashboard with learning-focused metrics (NOT effort metrics).

**Primary metrics:** Delayed retention rate, transfer task success, real mastery transitions, calibration accuracy, curriculum velocity.

**Not shown prominently:** Hours practiced, streak counts, total cards reviewed.

**Additional elements:**
- Curriculum roadmap with task class progression, mastery gates, plateau indicators
- Session history with template types and outcomes
- Knowledge graph coverage over time
- Identity frame at top: "You're becoming a..."
- Decay shown as fading (not red/alarming), tooltip: "Ready for a refresher"

### Mobile

Focused single-panel layouts with easy navigation. Modes collapse to one surface at a time. Chat goes full-width in Train. Graph gets simplified touch interactions. CSS gradient nebula background (no large image, no parallax).

---

## 5. Onboarding Flow

### Pattern: Conversational + Live State Panel with Progressive Reveal

No wizard steps, no locked forms. Skills drive the flow, not the UI.

**How it works:**
- Starts as full-width conversation — clean, no panels. "What would you like to learn?"
- User describes their goal in natural language
- As the LLM extracts information, a state panel fades in on the right with editable fields
- Fields appear one by one as discovered — nothing shows until earned
- User can click any field to correct or override
- Pipeline progress bar fills subtly at the bottom

### Pipeline (skill-driven, state-file routing)

The orchestrator routes based on which state files exist. Each skill writes its output file, which triggers the next phase.

**Phase 1: Domain Assessment**
- LLM classifies skill, gathers learner profile, establishes identity frame
- State panel populates with profile fields
- Output: `domain-assessment.json`

**Phase 2: Skill Research**
- LLM decomposes skill into graph nodes via web research
- Graph preview fades in showing gray (unassessed) nodes
- Output: `skill-dossier.json`

**Phase 3: Learner Calibration + Calibration Loop**
- 15-20 diagnostic questions, graph lights up in real-time as mastery is assessed
- Transfer boosts from existing skills show immediately
- **Calibration loop (max 2 iterations):** Assessment almost always reveals surprises — the Calibrator flags re-research triggers, Researcher does a targeted update (new vertices), Calibrator re-assesses only the new/changed nodes. The UI shows this naturally: spinner with "Researching: [topic]", new nodes appear with pulsing borders, then 2-5 follow-up questions.
- Output: `knowledge-graph.json`

**Phase 4: Curriculum Design + Agreement Gates**
- Two conversational checkpoints where the learner confirms direction:
  1. **Teaching preferences:** Expert panel presented in chat (if available), learner chooses instructor persona and instruction style preference
  2. **Epitome refinement:** Proposed first lesson presented as a rich card with rationale. "Does this feel right?" Learner can redirect. Only proceeds when confirmed.
- These are NOT forms — they are natural dialogue moments rendered inline in the chat
- Output: `learning-plan.json`

**Phase 5: Material Generation**
- Anki decks, worked examples, lectures, reference sheets generated
- Materials count appears in panel, Anki export offered
- Output: `srs-cards.json` + `materials/`

**Transition to Learning:** Dashboard presented (Explore mode), curriculum shown, first training session offered. All modes unlocked.

**No artificial stops.** The orchestrator manages transitions. The UI reflects the state machine — it doesn't impose its own flow.

### Learning Phase Feedback Loops

The Training Conductor may signal upstream updates based on evidence:

| Signal | Routes To | Trigger |
|--------|-----------|---------|
| Field evolved, new concepts | Skill Researcher (update) → Calibrator → Architect | Undocumented techniques encountered |
| Mastery estimates drifted | Calibrator (targeted re-assessment) | Performance diverges across 3+ sessions |
| Pacing mismatch | Curriculum Architect (update) | Pattern across 3+ sessions |
| Materials exhausted | Material Forge (on-demand) | Via Materials mode or orchestrator |
| Plateau, protocols exhausted | Curriculum Architect (re-sequence) | Breakthrough strategies tried without improvement |

All updates preserve completed work and learner progress. These are evidence-based judgment calls, not knee-jerk reactions.

---

## 6. Self-Host Setup Wizard

First-run experience at `/setup`. Appears only when the instance has no configuration.

### Two Tracks

**Quick Setup (~2 min):** Bundled Postgres via Docker, just need an LLM API key. Single user mode.

**Custom Setup (~5 min):** Bring your own Postgres, configure OAuth, multi-user.

### Five Steps

1. **Welcome** — Choose Quick or Custom
2. **Database** — Quick: auto-configured. Custom: connection string, test connection, AGE/PGVector extension verification
3. **LLM Provider** — Card selection (Claude recommended, OpenRouter/Local "Coming Soon"). Inline step-by-step guide with links to provider console. API key entry (masked, encrypted at rest). Model selection. "Test Connection" with latency readout.
4. **Authentication** — Local accounts always on. Single User Mode toggle. OAuth providers with inline setup guides that expand when toggled on. Per-provider "Test Connection."
5. **Create Account + Launch** — Admin account creation, configuration summary, launch button.

### Post-Setup Settings

All configuration accessible at `/settings`. No `.env` editing, no server restarts. Secret rotation supported. All API keys and OAuth secrets encrypted at rest with AES-256-GCM, decrypted only in memory during API calls.

---

## 7. D3 + Datastar Integration

D3 runs in a `data-ignore-morph` island. Data flows via Datastar signals:

```html
<div id="knowledge-graph"
     data-ignore-morph
     data-signals:graph_data='${server_json}'
     data-effect="renderGraph($graph_data)">
</div>
```

1. Server pushes graph data as Datastar signals (JSON via SSE `datastar-patch-signals`)
2. D3 renders inside the `data-ignore-morph` container
3. Mastery updates → server pushes new signal → D3 re-renders
4. User clicks node in D3 → D3 updates a Datastar signal (`$selected_nodes`) → server pushes detail panel HTML fragment

For large cross-skill graphs, server computes layout (via AGE or layout algorithm) and sends pre-computed positions. D3 renders, doesn't force-layout.

---

## 8. PWA Caching Strategy

### Stable Data (cache-first)
- Knowledge graph structure (nodes, edges, descriptions)
- Learning materials (lectures, flashcards, worked examples, visualizations)
- Skill dossier, learning plan, reference sheets
- Generated SVGs, embedded content
- Celestial background image

### Dynamic Data (network-first)
- Mastery overlay
- Progress state, session agenda, difficulty calibration
- Retrieval probe results

### Real-Time (network-only)
- SSE streams (chat, training sessions, live mastery updates)

### Offline Capabilities
- Browse all cached materials, lectures, flashcards
- View knowledge graph with last-known mastery overlay
- Review flashcards offline with background sync
- Version headers on cacheable responses for invalidation

---

## 9. Schema Migration

The existing plugin schemas need these additions for the three-layer architecture:

### What's Covered (no changes needed)
- Skill graph (vertices with Concept/Skill labels, edges with PREREQUISITE/RELATED/REINFORCEMENT)
- Learner state overlay (mastery_probability, BKT, FSRS, confidence, evidence tracking)
- Transfer metadata (transfer_coefficient, transfer_boost, transfer_pathways)
- Mastery transition audit trail

### What's New
- Shared concept ontology as a distinct layer with independent versioning
- `EMBODIES` edge type (skill node → concept)
- `GENERALIZES`, `SIMILAR_TO` edge types for concept hierarchy
- Per-node/per-edge versioning: `version`, `created_at`, `updated_at`, `updated_by`, `field_freshness`
- Reference nodes with `SOURCED_FROM` edges (per-node provenance, credibility, content_hash)
- Material nodes with `TEACHES` edges (type, modality, bloom_level, effectiveness_score)

---

## 10. Deployment Architecture

```yaml
# docker-compose.yml
services:
  app:
    build: .
    ports: ["8000:8000"]
    depends_on: [db]
    
  db:
    image: apache/age  # Postgres + AGE + PGVector
    volumes: ["pgdata:/var/lib/postgresql/data"]
```

Quick Setup bundles everything. Custom Setup supports external Postgres.

---

## 11. Roadmap Items

### LiteLLM Integration (deferred)

`LLMProvider` interface defined at MVP. LiteLLM adapter built once supply chain concerns are resolved (TeamPCP compromise of PyPI packages on 2026-03-24). The interface:

```python
class LLMProvider(Protocol):
    async def generate(self, messages, tools, **kwargs) -> Response: ...
    async def stream(self, messages, tools, **kwargs) -> AsyncIterator[Event]: ...
```

MVP ships with `AgentSDKProvider` (Claude). `LiteLLMProvider` roadmapped for OpenRouter, Ollama, local models.

### Interactive Celestial Sphere Background

Three.js/WebGL celestial sphere rendered once on page load, then used as static parallax background. Procedural generation for unique-per-instance appearance. CSS gradient nebula remains as fallback. Deferred until a suitable open-source celestial sphere asset or generator is identified.

### Code Execution Environment

For programming-related skills, an embedded coding environment:

**MVP candidate:** Monaco editor (code editing, ~2MB) + Judge0 (execution, self-hosted Docker sidecar). Supports 60+ languages. The LLM pushes code challenges to Monaco, user writes code, Judge0 executes, results stream back via SSE.

**Later:** WebContainers for richer JS/TS environments (full npm, filesystem). Theia IDE for project-based learning skills.

Monaco embeds as another `data-ignore-morph` island. Judge0 runs as a Docker service — one line in `docker-compose.yml`. Material Forge generates executable exercises with test cases, hints, and fading scaffolding.

---

## 12. Security Considerations

- All API keys and OAuth secrets encrypted at rest (AES-256-GCM)
- Passwords: bcrypt with per-user salts, never stored plaintext
- Datastar expressions use `Function()` constructors — requires `unsafe-eval` in CSP
- Signal values visible in source — never put secrets in signals
- All user input validated server-side
- Judge0 (when added) runs code in isolated containers
- LiteLLM deferred due to 2026-03-24 PyPI supply chain attack (TeamPCP). Resume integration once maintainer security hardening is confirmed.

---

## 13. Open Questions

- Celestial background image licensing (ESA Gaia data is CC BY-SA 4.0 — verify terms for self-hosted open-source distribution)
- Datastar LLM training gap — team acknowledges models fall back to SPA patterns. Mitigation: comprehensive Datastar docs page fed into LLM context during development, plus Ben's getting-started guide as required reading before implementation.
- AGE Docker image maturity — verify that the bundled AGE+PGVector image is production-ready for self-hosters
- Voice input/output API selection for Train mode (Web Speech API vs. third-party STT/TTS)
