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
- **PostgreSQL** with AGE and PGVector extensions (primary, full features)
- **JSON file backend** (fallback, single-user, degraded — no cross-skill transfer, no graph traversal queries, no multi-user)
- Backend selection via setup wizard; import/export between backends so users aren't locked in
- Custom Docker image required: build from `pgvector/pgvector:pg16` base, add AGE extension

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

### Authentication & Sessions
- Local accounts with bcrypt + per-user salts (always on, zero-config)
- OAuth2 providers (Google, GitHub) activate when credentials are configured via web UI
- `SINGLE_USER=true` mode skips login page for personal deployments
- All secrets encrypted at rest with AES-256-GCM, encryption key auto-generated on first run, stored in Docker volume (or Ansible vault for managed infrastructure)
- Sessions: httponly secure cookies with server-side session store. SSE streams authenticate on initial connect via session cookie. Session timeout configurable (default 7 days).

### State Backend

Two pluggable backends behind a shared `StateBackend` protocol. User chooses during setup; import/export enables switching without data loss.

**PostgreSQL (recommended):** Full feature set — cross-skill transfer detection (PGVector), graph traversal (AGE), multi-user, aggregate queries for Progress dashboard.

**JSON files (local mode):** Single-user, single-skill graphs loaded into memory. No cross-skill transfer, no graph traversal queries, no multi-user. Suitable for quick evaluation or offline use. Subtle banner: "Running in local mode — connect to PostgreSQL for the full experience."

```python
class StateBackend(Protocol):
    async def read_graph(self, skill_slug) -> KnowledgeGraph: ...
    async def write_graph(self, skill_slug, graph) -> None: ...
    async def query_transfer(self, embeddings) -> list[TransferMatch]: ...
    async def export_json(self, skill_slug) -> dict: ...
    async def import_json(self, skill_slug, data: dict) -> None: ...
```

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

**Phase 6: Progress Dashboard**
- Progress Mode becomes available — metrics computed server-side (PG: SQL/AGE queries; JSON: in-memory from loaded state)
- PG mode: rich aggregate queries (cross-skill coverage, retention trends, transfer success rates)
- JSON mode: simplified dashboard from single-skill in-memory state
- This replaces the plugin's Dashboard Generator skill — the web frontend subsumes it

**Transition to Learning:** Explore mode presented, curriculum shown, first training session offered. All modes unlocked. Training Conductor writes `progress.json` (JSON backend) or progress records (PG backend) after each session.

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

### Migration Tooling
- **Alembic** for SQLAlchemy schema migrations, versioned in `alembic/versions/`
- Migrations run automatically on application startup (`alembic upgrade head`)
- Self-hosters upgrading: `docker compose pull && docker compose up` triggers auto-migration
- Rollback supported via `alembic downgrade`

### Edge Type Mapping (existing → new)
- `RELATED` → `SIMILAR_TO` (with cosine similarity field added)
- `REINFORCEMENT` → `REINFORCES` (renamed for consistency)
- `PREREQUISITE` → `PREREQUISITE` (unchanged)
- New: `EMBODIES`, `GENERALIZES`, `NEGATIVE_TRANSFER`, `SOURCED_FROM`, `TEACHES`, `PREREQUISITE_MATERIAL`, `CITES`

### What's Covered (no changes needed)
- Skill graph vertices (Concept/Skill labels, bloom_level, frequency/impact scores)
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
    environment:
      - DATABASE_URL=postgresql://learn_anything:${LA_DB_PASSWORD}@db:5432/learn_anything
    
  db:
    build: ./docker/postgres  # Custom: pgvector base + AGE extension
    volumes: ["pgdata:/var/lib/postgresql/data"]
    environment:
      - POSTGRES_DB=learn_anything
      - POSTGRES_USER=learn_anything
      - POSTGRES_PASSWORD=${LA_DB_PASSWORD}
```

**Three deployment paths:**

1. **Quick Setup (Docker Compose, bundled):** Everything in one `docker-compose.yml` — app + custom PG image with AGE/PGVector. Single user, minimal config. Good for evaluation.

2. **Custom Setup (Docker Compose, external PG):** User provides connection string to their own PostgreSQL instance. Setup wizard verifies AGE and PGVector extensions. Multi-user, OAuth.

3. **Managed Infrastructure:** For operators running shared PostgreSQL alongside other apps. The application connects to an existing PG instance (dedicated database + user), sits behind an existing reverse proxy (Caddy, nginx, etc.), and is deployed via the operator's existing tooling (Ansible, Terraform, etc.). The app ships as a single Docker image (`learn-anything:latest`) that takes a `DATABASE_URL` and standard environment variables. No bundled database. Deployment playbooks/templates are maintained separately in the operator's infrastructure repo, not in this project.

**Managed infrastructure requirements:**
- PostgreSQL 17+ with AGE and PGVector extensions enabled
- Dedicated database and user (not shared with other apps)
- Connection pooling recommended (PgBouncer in transaction mode)
- Reverse proxy must not buffer SSE streams (`proxy_buffering off` for nginx, automatic for Caddy)
- Health check endpoint: `GET /health`

### Backup & Restore
- **PG backend:** `pg_dump` via `/settings/backup` page (admin only). Scheduled backups configurable. Download as `.sql.gz`.
- **JSON backend:** Export all state files as `.zip` from `/settings/backup`.
- **Import:** Upload backup file via `/settings/restore`. PG backend runs `pg_restore`; JSON backend extracts to state directory.
- **Cross-backend migration:** Export from JSON → Import to PG (or vice versa) via the same JSON schema format. The `StateBackend.export_json()` / `import_json()` methods ensure format compatibility.

### Observability
- **Logging:** Python `structlog` with JSON output. Log level configurable via settings (`DEBUG` / `INFO` / `WARNING`). Logs to stdout (Docker captures).
- **Health check:** `GET /health` returns `200` with backend status (DB connected, LLM provider configured, extension versions). Used by Docker `healthcheck` and external monitoring.
- **Error recovery:** Pipeline stages are idempotent — if an LLM call fails mid-phase, the state file is not written, so the orchestrator retries the same phase on next interaction. After 2 consecutive failures, the system falls back to a simplified version of the phase and notifies the user.

### CORS & Reverse Proxy
- Same-origin by default (frontend and API served from same FastAPI instance).
- For reverse proxy deployments (nginx, Caddy): SSE requires `proxy_buffering off` (nginx) or equivalent. Document in deployment guide.
- Configurable `ALLOWED_ORIGINS` for split deployments.

### Rate Limiting
- Per-user LLM call budget: configurable requests/hour and tokens/day in `/settings`.
- Admin can set default budgets and per-user overrides.
- Budget exhaustion shows graceful message, not a crash. Resets on schedule.
- Cost tracking displayed in Progress mode (optional, disabled by default).

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

- All API keys and OAuth secrets encrypted at rest (AES-256-GCM). Encryption key auto-generated on first run, stored in persistent volume (`/data/encryption.key`). If key is lost, encrypted secrets must be re-entered via setup wizard. Key rotation: generate new key, re-encrypt all secrets, atomic swap.
- Passwords: bcrypt with per-user salts, never stored plaintext
- Datastar expressions use `Function()` constructors — requires `unsafe-eval` in CSP
- Signal values visible in source — never put secrets in signals
- All user input validated server-side
- Database: dedicated user and database (`learn_anything`), not shared with other applications. Connection string configurable for managed infrastructure (Ansible vaults, etc.)
- Per-user LLM rate limiting to prevent budget exhaustion in multi-user deployments
- SSE streams authenticated via session cookie on connect; no secret data in SSE event payloads
- Judge0 (when added) runs code in isolated containers
- LiteLLM deferred due to 2026-03-24 PyPI supply chain attack (TeamPCP). Resume integration once maintainer security hardening is confirmed.

---

## 13. Open Questions

- Celestial background image licensing (ESA Gaia data is CC BY-SA 4.0 — verify terms for self-hosted open-source distribution)
- Datastar LLM training gap — team acknowledges models fall back to SPA patterns. Mitigation: comprehensive Datastar docs page fed into LLM context during development, plus Ben's getting-started guide as required reading before implementation.
- Custom Docker image build: verify that AGE compiles cleanly on `pgvector/pgvector:pg16` base, document the Dockerfile
- Voice input/output API selection for Train mode (Web Speech API vs. third-party STT/TTS)
- PWA service worker invalidation strategy on backend updates — ensure cached frontend fragments don't mismatch new SSE event formats
