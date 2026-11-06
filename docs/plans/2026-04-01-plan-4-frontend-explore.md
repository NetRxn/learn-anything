> HISTORICAL DESIGN REFERENCE: superseded operationally by CONVENTIONS.md and
> docs/superpowers/plans/2026-11-06-alpha-foundation.md. Do not execute provisioning,
> runner or database commands below. No current service admission is implied.

# Plan 4: Frontend Shell + Explore Mode — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking. **Use opus subagents exclusively (model: opus). No sonnet, no haiku.**
>
> **REQUIRED READING:** `docs/plans/CONVENTIONS.md` — all plans follow these rules.
>
> **Execution:** Plans execute sequentially (1→2→3→4→5→6) on feature branch `feature/learn-anything-webapp`. TDD strictly enforced.

**Goal:** A fully styled Datastar app shell with top navigation, skill switcher, and identity frame. The Explore mode renders the knowledge graph via D3 in a morph-safe island, with three interaction states (single-click detail, multi-select, lesson pre-selection) backed by SSE endpoints that push HTML fragments. The Observatory + Neural visual identity is fully implemented including celestial background, breathing node animations, constellation-style edges, and tiered rendering for desktop/mobile/reduce-motion.

**Architecture:** Server pushes HTML fragments via SSE (`text/event-stream` with `datastar-merge-fragments` events) using the `datastar-py` SDK (`DatastarResponse`, `SSE.patch_elements()`, `SSE.patch_signals()`). D3 runs inside a `data-ignore-morph` container. Signals live in `data-*` attributes — no JavaScript state management. D3 communicates outward by dispatching CustomEvents on the graph container element, which Datastar picks up via `data-on:<event-name>` attributes to update signals and trigger SSE requests. Real URLs, real `<a>` tags, no client-side router.

**Tech Stack:** Datastar (~14KB, CDN script tag via `@starfederation/datastar` with pinned version), D3.js (ES module), Jinja2 templates (server-rendered HTML fragments pushed via SSE using `datastar-py` SDK), CSS (no build step — extend `static/css/observatory.css` from Plan 1)

**Spec:** `docs/specs/2026-04-01-learn-anything-webapp-design.md` — Sections 4 (Frontend Layout & Modes) and 7 (D3 + Datastar Integration)

**Depends on:** Plan 1 (project scaffold, models, auth, base template, observatory.css foundation). Plan 2 (database backends — routes use the `StateBackend` protocol to read graph data).

---

## Project Structure (new and modified files)

```
learn-anything-app/
├── templates/
│   ├── base.html                         # MODIFY: add Datastar CDN (if not present from Plan 1)
│   ├── shell.html                        # CREATE: app shell with nav, mode containers
│   └── explore/
│       ├── graph.html                    # CREATE: knowledge graph container + detail panel
│       ├── detail_single.html            # CREATE: single node detail fragment
│       ├── detail_multi.html             # CREATE: multi-select detail fragment
│       └── detail_lesson.html            # CREATE: lesson pre-selection fragment
├── static/
│   ├── css/
│   │   └── observatory.css              # MODIFY: extend with shell, graph, detail panel, full visual identity
│   └── js/
│       └── graph.js                     # CREATE: D3 knowledge graph rendering
├── app/
│   └── routes/
│       └── explore.py                   # CREATE: Explore mode routes (graph data SSE, detail fragments)
└── tests/
    └── test_routes/
        └── test_explore.py              # CREATE: route response tests
```

---

### Task 1: Explore Route Tests (TDD)

**Files:**
- Create: `learn-anything-app/tests/integration/test_routes/test_explore.py`

- [ ] **Step 1: Write failing tests for explore routes**

```python
# tests/integration/test_routes/test_explore.py
import pytest
from httpx import AsyncClient, ASGITransport
from app.main import app


@pytest.fixture
async def client():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as c:
        yield c


@pytest.mark.asyncio
async def test_explore_page_renders(client):
    resp = await client.get("/explore")
    assert resp.status_code == 200
    assert "data-ignore-morph" in resp.text
    assert "knowledge-graph" in resp.text


@pytest.mark.asyncio
async def test_explore_graph_data_sse(client):
    resp = await client.get(
        "/explore/graph-data",
        params={"skill_slug": "test-skill"},
        headers={"Accept": "text/event-stream"},
    )
    assert resp.status_code == 200
    assert resp.headers["content-type"].startswith("text/event-stream")


@pytest.mark.asyncio
async def test_detail_single_returns_sse_fragment(client):
    resp = await client.get(
        "/explore/detail/single",
        params={"node_id": "node-1"},
    )
    assert resp.status_code == 200
    assert resp.headers["content-type"].startswith("text/event-stream")
    assert "detail-panel" in resp.text


@pytest.mark.asyncio
async def test_detail_multi_returns_sse_fragment(client):
    resp = await client.get(
        "/explore/detail/multi",
        params={"node_ids": "node-1,node-2"},
    )
    assert resp.status_code == 200
    assert resp.headers["content-type"].startswith("text/event-stream")
    assert "detail-panel" in resp.text


@pytest.mark.asyncio
async def test_detail_lesson_returns_sse_fragment(client):
    resp = await client.get(
        "/explore/detail/lesson",
        params={"lesson_id": "lesson-1"},
    )
    assert resp.status_code == 200
    assert resp.headers["content-type"].startswith("text/event-stream")
    assert "detail-panel" in resp.text


@pytest.mark.asyncio
async def test_explore_graph_data_returns_nodes_and_edges(client):
    """SSE response body should contain datastar event format with graph JSON."""
    resp = await client.get(
        "/explore/graph-data",
        params={"skill_slug": "test-skill"},
        headers={"Accept": "text/event-stream"},
    )
    body = resp.text
    # Datastar SSE format: event lines followed by data lines
    assert "event:" in body or "data:" in body
```

- [ ] **Step 2: Run tests — should fail**

Run: `cd learn-anything-app && uv run pytest tests/integration/test_routes/test_explore.py -v`
Expected: FAIL — no explore routes registered.

- [ ] **Step 3: Commit**

```bash
git commit -m "test: failing tests for explore routes — graph SSE, detail fragments"
```

---

### Task 2: Explore Routes (Server Side)

**Files:**
- Create: `learn-anything-app/app/routes/explore.py`
- Modify: `learn-anything-app/app/main.py` (register router)

- [ ] **Step 1: Create explore routes**

```python
# app/routes/explore.py
import json
from fastapi import APIRouter, Request, Query
from datastar_py import ServerSentEventGenerator as SSE
from datastar_py.fastapi import DatastarResponse
from app.templating import templates

router = APIRouter(prefix="/explore", tags=["explore"])


async def _graph_data_stream(skill_slug: str):
    """SSE generator that pushes graph data as Datastar signals.

    In production this reads from the StateBackend.
    For Plan 4 bootstrap, push demo data so D3 has something to render.
    """
    demo_nodes = [
        {
            "id": "n1", "name": "Fundamentals", "description": "Core concepts",
            "bloom_level": "remember", "mastery": "proficient",
            "mastery_probability": 0.72, "x": 400, "y": 300,
            "frequency_score": 0.9, "impact_score": 0.95,
        },
        {
            "id": "n2", "name": "Intermediate", "description": "Building blocks",
            "bloom_level": "apply", "mastery": "familiar",
            "mastery_probability": 0.45, "x": 600, "y": 200,
            "frequency_score": 0.7, "impact_score": 0.8,
        },
        {
            "id": "n3", "name": "Advanced", "description": "Deep techniques",
            "bloom_level": "analyze", "mastery": "not_started",
            "mastery_probability": 0.0, "x": 800, "y": 350,
            "frequency_score": 0.5, "impact_score": 0.7,
        },
        {
            "id": "n4", "name": "Practical Application", "description": "Real-world usage",
            "bloom_level": "apply", "mastery": "attempted",
            "mastery_probability": 0.18, "x": 500, "y": 450,
            "frequency_score": 0.8, "impact_score": 0.85,
        },
        {
            "id": "n5", "name": "Mastery", "description": "Full command",
            "bloom_level": "create", "mastery": "mastered",
            "mastery_probability": 0.95, "x": 200, "y": 250,
            "frequency_score": 0.6, "impact_score": 0.6,
        },
    ]
    demo_edges = [
        {
            "from_id": "n1", "to_id": "n2", "edge_type": "PREREQUISITE",
            "strength": 0.9, "prerequisite_type": "hard",
            "description": "Fundamentals must be understood before attempting intermediate material — core vocabulary and mental models are prerequisites.",
        },
        {
            "from_id": "n2", "to_id": "n3", "edge_type": "PREREQUISITE",
            "strength": 0.7, "prerequisite_type": "soft",
            "description": "Intermediate concepts provide the scaffolding for advanced techniques, though some learners can bridge the gap.",
        },
        {
            "from_id": "n1", "to_id": "n4", "edge_type": "REINFORCES",
            "strength": 0.6,
            "description": "Practical application reinforces fundamental understanding — the feedback loop strengthens both.",
        },
        {
            "from_id": "n5", "to_id": "n1", "edge_type": "PREREQUISITE",
            "strength": 0.95, "prerequisite_type": "hard",
            "description": "Mastery of the foundational mental model is the seed from which all other concepts grow.",
        },
        {
            "from_id": "n3", "to_id": "n4", "edge_type": "REINFORCES",
            "strength": 0.5,
            "description": "Advanced theoretical knowledge makes practical application more precise and intentional.",
        },
    ]
    graph_data = {"nodes": demo_nodes, "edges": demo_edges, "skill_slug": skill_slug}
    yield from SSE.patch_signals({"graph_data": graph_data})


@router.get("")
async def explore_page(request: Request):
    # Initial page load (browser navigation) — TemplateResponse is correct here.
    # DatastarResponse is for Datastar @get() triggered endpoints only.
    return templates.TemplateResponse(request, "shell.html", {"active_mode": "explore"})


@router.get("/graph-data")
async def graph_data_sse(skill_slug: str = Query("demo-skill")):
    return DatastarResponse(_graph_data_stream(skill_slug))


@router.get("/detail/single")
async def detail_single(request: Request, node_id: str = Query(...)):
    # In production: look up node from StateBackend, fetch edges, materials, mastery
    demo_node = {
        "id": node_id,
        "name": "Demo Node",
        "description": "This node represents a concept in the knowledge graph. Full edge descriptions explain the WHY of each connection.",
        "bloom_level": "apply",
        "mastery": "familiar",
        "mastery_probability": 0.45,
        "evidence_count": 5,
        "last_assessed": "2026-03-28",
    }
    demo_edges = [
        {
            "target_name": "Fundamentals",
            "edge_type": "PREREQUISITE",
            "prerequisite_type": "hard",
            "description": "This concept requires fundamental vocabulary and mental models as prerequisites.",
        },
        {
            "target_name": "Advanced",
            "edge_type": "REINFORCES",
            "description": "Understanding this concept reinforces and deepens advanced techniques.",
        },
    ]
    demo_materials = [
        {"title": "Introduction Lecture", "type": "lecture", "format": "markdown"},
        {"title": "Practice Deck", "type": "flashcard_deck", "format": "apkg"},
    ]
    html = templates.get_template("explore/detail_single.html").render({
        "node": demo_node,
        "edges": demo_edges,
        "materials": demo_materials,
    })
    return DatastarResponse(SSE.patch_elements(html))


@router.get("/detail/multi")
async def detail_multi(request: Request, node_ids: str = Query(...)):
    node_id_list = [nid.strip() for nid in node_ids.split(",") if nid.strip()]
    # In production: aggregate mastery, find internal/external edges, gap analysis
    demo_nodes = [
        {"id": nid, "name": f"Node {nid}", "mastery": "familiar", "mastery_probability": 0.45}
        for nid in node_id_list
    ]
    aggregate_mastery = sum(n["mastery_probability"] for n in demo_nodes) / max(len(demo_nodes), 1)
    demo_internal_edges = [
        {
            "from_name": demo_nodes[0]["name"] if len(demo_nodes) > 0 else "",
            "to_name": demo_nodes[1]["name"] if len(demo_nodes) > 1 else "",
            "edge_type": "PREREQUISITE",
            "description": "These concepts are sequentially dependent.",
        },
    ] if len(demo_nodes) > 1 else []
    html = templates.get_template("explore/detail_multi.html").render({
        "nodes": demo_nodes,
        "node_count": len(demo_nodes),
        "aggregate_mastery": round(aggregate_mastery, 2),
        "internal_edges": demo_internal_edges,
        "gaps": ["No worked examples for Node node-2"] if len(demo_nodes) > 1 else [],
    })
    return DatastarResponse(SSE.patch_elements(html))


@router.get("/detail/lesson")
async def detail_lesson(request: Request, lesson_id: str = Query(...)):
    # In production: look up lesson from learning plan, get scope nodes, retrieval probes
    demo_lesson = {
        "id": lesson_id,
        "title": "Session 3: Building Blocks",
        "narrative": "This session connects your understanding of fundamentals to intermediate techniques. We will work through two key transitions and reinforce with a worked example.",
        "scope_node_ids": ["n1", "n2", "n4"],
        "scope_nodes": [
            {"id": "n1", "name": "Fundamentals", "mastery": "proficient"},
            {"id": "n2", "name": "Intermediate", "mastery": "familiar"},
            {"id": "n4", "name": "Practical Application", "mastery": "attempted"},
        ],
        "retrieval_probes": [
            "What are the three core properties of the fundamental model?",
            "How does intermediate technique X differ from fundamental approach Y?",
        ],
    }
    html = templates.get_template("explore/detail_lesson.html").render({
        "lesson": demo_lesson,
    })
    return DatastarResponse(SSE.patch_elements(html))


@router.get("/synthesize")
async def synthesize(request: Request, node_ids: str = Query(...)):
    """LLM synthesis of selected graph nodes — stub for Plan 4, wired to LLM in Plan 3/5."""
    node_id_list = [nid.strip() for nid in node_ids.split(",") if nid.strip()]
    html = f'<div id="detail-panel" class="detail-panel"><div class="detail-panel__section"><p class="subtitle">LLM synthesis for {len(node_id_list)} nodes — available after Plan 3 LLM integration.</p></div></div>'
    return DatastarResponse(SSE.patch_elements(html))
```

- [ ] **Step 2: Register the explore router in main.py**

Add to `app/main.py` alongside the existing router registrations:

```python
from app.routes.explore import router as explore_router
app.include_router(explore_router)
```

- [ ] **Step 3: Run tests — should fail (templates not yet created)**

Run: `cd learn-anything-app && uv run pytest tests/integration/test_routes/test_explore.py -v`
Expected: FAIL — template files missing.

- [ ] **Step 4: Commit**

```bash
git commit -m "feat: explore routes — graph data SSE, single/multi/lesson detail fragments"
```

---

### Task 3: Observatory + Neural Visual Identity CSS

**Files:**
- Modify: `learn-anything-app/static/css/observatory.css`

This extends the foundation CSS from Plan 1 with the full Observatory + Neural visual identity: nebula background, node styles, constellation edges, graph chrome, detail panel, app shell, and tiered rendering.

- [ ] **Step 1: Add celestial background and grain overlay styles**

Append to `static/css/observatory.css`:

```css
/* ============================================================
   PLAN 4: APP SHELL + EXPLORE MODE
   ============================================================ */

/* --- Celestial Background --- */

.celestial-bg {
  position: fixed;
  inset: 0;
  z-index: -2;
  background:
    radial-gradient(ellipse at 20% 50%, rgba(30,20,80,0.4) 0%, transparent 60%),
    radial-gradient(ellipse at 80% 30%, rgba(15,40,80,0.3) 0%, transparent 50%),
    radial-gradient(ellipse at 50% 80%, rgba(60,20,50,0.2) 0%, transparent 55%),
    var(--void);
  overflow: hidden;
}

.celestial-bg__image {
  position: absolute;
  inset: 0;
  background-size: cover;
  background-position: center;
  background-repeat: no-repeat;
  opacity: 0.2;
  will-change: transform;
  transition: transform 0.1s linear;
}

.celestial-bg__tint {
  position: absolute;
  inset: 0;
  background: linear-gradient(
    180deg,
    rgba(4,6,14,0.85) 0%,
    rgba(8,12,26,0.7) 40%,
    rgba(14,19,40,0.8) 100%
  );
  mix-blend-mode: multiply;
}

/* Grain texture overlay */
.grain-overlay {
  position: fixed;
  inset: 0;
  z-index: 9999;
  pointer-events: none;
  opacity: 0.035;
  background-image: url("data:image/svg+xml,%3Csvg viewBox='0 0 256 256' xmlns='http://www.w3.org/2000/svg'%3E%3Cfilter id='n'%3E%3CfeTurbulence type='fractalNoise' baseFrequency='0.85' numOctaves='4' stitchTiles='stitch'/%3E%3C/filter%3E%3Crect width='100%25' height='100%25' filter='url(%23n)'/%3E%3C/svg%3E");
  background-repeat: repeat;
  background-size: 256px 256px;
}

/* --- App Shell --- */

.app-shell {
  display: flex;
  flex-direction: column;
  min-height: 100vh;
  position: relative;
}

/* --- Top Navigation Bar --- */

.top-nav {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0 24px;
  height: 56px;
  background: rgba(8,12,26,0.85);
  backdrop-filter: blur(16px);
  border-bottom: 1px solid var(--border);
  position: sticky;
  top: 0;
  z-index: 100;
}

.top-nav__brand {
  display: flex;
  align-items: center;
  gap: 10px;
  text-decoration: none;
}

.top-nav__logo {
  width: 28px;
  height: 28px;
  border-radius: 50%;
  background: radial-gradient(circle at 40% 40%, var(--gold), var(--gold-dim));
  box-shadow: 0 0 16px var(--gold-glow);
  flex-shrink: 0;
}

.top-nav__title {
  font-family: var(--serif);
  font-size: 16px;
  font-weight: 600;
  color: var(--text-bright);
  letter-spacing: -0.3px;
}

.top-nav__tabs {
  display: flex;
  gap: 4px;
  list-style: none;
}

.top-nav__tab {
  display: block;
  padding: 8px 18px;
  border-radius: 6px;
  font-family: var(--mono);
  font-size: 11px;
  font-weight: 400;
  letter-spacing: 0.8px;
  text-transform: uppercase;
  color: var(--text-dim);
  text-decoration: none;
  transition: color 0.15s, background 0.15s;
}

.top-nav__tab:hover {
  color: var(--text);
  background: rgba(255,255,255,0.04);
}

.top-nav__tab--active {
  color: var(--gold);
  background: rgba(212,150,74,0.08);
}

.top-nav__right {
  display: flex;
  align-items: center;
  gap: 16px;
}

/* --- Skill Switcher Dropdown --- */

.skill-switcher {
  position: relative;
}

.skill-switcher__button {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 6px 12px;
  background: var(--surface);
  border: 1px solid var(--border);
  border-radius: 6px;
  color: var(--text);
  font-family: var(--sans);
  font-size: 13px;
  cursor: pointer;
  transition: border-color 0.15s;
}

.skill-switcher__button:hover {
  border-color: var(--border-glow);
}

.skill-switcher__caret {
  display: inline-block;
  width: 0;
  height: 0;
  border-left: 4px solid transparent;
  border-right: 4px solid transparent;
  border-top: 4px solid var(--text-dim);
  transition: transform 0.15s;
}

.skill-switcher__dropdown {
  position: absolute;
  top: calc(100% + 4px);
  right: 0;
  min-width: 220px;
  background: var(--surface);
  border: 1px solid var(--border);
  border-radius: 8px;
  box-shadow: 0 8px 32px rgba(0,0,0,0.5);
  padding: 4px;
  display: none;
  z-index: 200;
}

.skill-switcher__dropdown--open {
  display: block;
}

.skill-switcher__item {
  display: block;
  width: 100%;
  padding: 8px 12px;
  text-align: left;
  background: none;
  border: none;
  border-radius: 4px;
  color: var(--text);
  font-family: var(--sans);
  font-size: 13px;
  cursor: pointer;
}

.skill-switcher__item:hover {
  background: rgba(255,255,255,0.05);
}

.skill-switcher__item--active {
  color: var(--gold);
}

/* --- Identity Frame --- */

.identity-frame {
  font-family: var(--serif);
  font-size: 13px;
  font-style: italic;
  color: var(--text-dim);
}

.identity-frame__role {
  color: var(--gold);
  font-style: normal;
  font-weight: 600;
}

/* --- Scope Toggle (This Skill / All Skills) --- */

.scope-toggle {
  display: inline-flex;
  border: 1px solid var(--border);
  border-radius: 6px;
  overflow: hidden;
}

.scope-toggle__option {
  padding: 5px 12px;
  font-family: var(--mono);
  font-size: 10px;
  letter-spacing: 0.5px;
  text-transform: uppercase;
  color: var(--text-dim);
  background: none;
  border: none;
  cursor: pointer;
  transition: color 0.15s, background 0.15s;
}

.scope-toggle__option:hover {
  color: var(--text);
}

.scope-toggle__option--active {
  color: var(--text-bright);
  background: var(--surface-light);
}

/* --- Mode Container --- */

.mode-container {
  flex: 1;
  position: relative;
  overflow: hidden;
}
```

- [ ] **Step 2: Commit**

```bash
git commit -m "feat: observatory CSS — celestial background, grain overlay, app shell, nav, skill switcher"
```

---

### Task 4: Graph + Detail Panel CSS

**Files:**
- Modify: `learn-anything-app/static/css/observatory.css`

- [ ] **Step 1: Add graph viewport and node/edge styles**

Append to `static/css/observatory.css`:

```css
/* --- Explore Mode Layout --- */

.explore-layout {
  display: flex;
  height: calc(100vh - 56px);
  position: relative;
}

.explore-layout__graph {
  flex: 1;
  position: relative;
  overflow: hidden;
}

.explore-layout__panel {
  width: 380px;
  min-width: 320px;
  max-width: 480px;
  background: rgba(8,12,26,0.92);
  backdrop-filter: blur(20px);
  border-left: 1px solid var(--border);
  overflow-y: auto;
  padding: 24px;
  transition: width 0.2s ease;
}

.explore-layout__panel--collapsed {
  width: 0;
  min-width: 0;
  padding: 0;
  border-left: none;
  overflow: hidden;
}

/* --- Graph Viewport (D3 Container) --- */

.graph-viewport {
  width: 100%;
  height: 100%;
  position: relative;
}

.graph-viewport svg {
  width: 100%;
  height: 100%;
  display: block;
}

/* --- Graph Legend --- */

.graph-legend {
  position: absolute;
  bottom: 20px;
  left: 20px;
  background: rgba(8,12,26,0.88);
  backdrop-filter: blur(12px);
  border: 1px solid var(--border);
  border-radius: 10px;
  padding: 14px 18px;
  z-index: 10;
}

.graph-legend__title {
  font-family: var(--mono);
  font-size: 10px;
  text-transform: uppercase;
  letter-spacing: 1px;
  color: var(--text-dim);
  margin-bottom: 10px;
}

.graph-legend__items {
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.graph-legend__item {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 11px;
  color: var(--text);
}

.graph-legend__swatch {
  width: 10px;
  height: 10px;
  border-radius: 50%;
  flex-shrink: 0;
}

.graph-legend__swatch--mastered { background: var(--mastered); box-shadow: 0 0 6px var(--mastered-glow); }
.graph-legend__swatch--proficient { background: var(--proficient); box-shadow: 0 0 6px var(--proficient-glow); }
.graph-legend__swatch--familiar { background: var(--familiar); box-shadow: 0 0 6px var(--familiar-glow); }
.graph-legend__swatch--attempted { background: var(--attempted); }
.graph-legend__swatch--not-started { background: var(--not-started); }

.graph-legend__divider {
  height: 1px;
  background: var(--border);
  margin: 6px 0;
}

.graph-legend__line {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 11px;
  color: var(--text);
}

.graph-legend__line-sample {
  width: 24px;
  height: 2px;
  flex-shrink: 0;
}

.graph-legend__line-sample--prerequisite { background: var(--edge-blue); }
.graph-legend__line-sample--reinforces { background: var(--edge-teal); }
.graph-legend__line-sample--transfer { background: none; height: 0; border-top: 2px dashed var(--violet); }

/* --- D3 Node Styles (SVG) --- */

/* Node base group — hover target */
.graph-node { cursor: pointer; }

.graph-node__halo {
  opacity: 0.5;
  transition: opacity 0.2s;
}

.graph-node:hover .graph-node__halo {
  opacity: 0.8;
}

.graph-node__core {
  transition: r 0.2s;
}

.graph-node:hover .graph-node__core {
  filter: brightness(1.2);
}

.graph-node__label {
  font-family: 'DM Sans', system-ui, sans-serif;
  font-size: 11px;
  fill: var(--text);
  text-anchor: middle;
  pointer-events: none;
  user-select: none;
}

.graph-node--selected .graph-node__halo {
  opacity: 1;
  animation: none;
}

.graph-node--dimmed {
  opacity: 0.2;
  pointer-events: none;
}

.graph-node--scope-highlight .graph-node__halo {
  opacity: 0.9;
}

/* Breathing pulse animation */
@keyframes node-breathe {
  0%, 100% { opacity: 0.4; }
  50% { opacity: 0.7; }
}

.graph-node__halo--breathing {
  animation: node-breathe 4s ease-in-out infinite;
}

/* --- D3 Edge Styles (SVG) --- */

.graph-edge {
  fill: none;
  stroke-linecap: round;
}

.graph-edge--prerequisite {
  stroke: var(--edge-blue);
  stroke-width: 1.5;
}

.graph-edge--reinforces {
  stroke: var(--edge-teal);
  stroke-width: 1.2;
}

.graph-edge--transfer {
  stroke: var(--violet);
  stroke-width: 1;
  stroke-dasharray: 6 4;
}

.graph-edge--dimmed {
  opacity: 0.08;
}

.graph-edge--highlighted {
  stroke-width: 2.5;
  filter: url(#edge-glow);
}

.graph-edge__label-bg {
  fill: rgba(8,12,26,0.9);
  rx: 4;
  ry: 4;
}

.graph-edge__label {
  font-family: 'DM Sans', system-ui, sans-serif;
  font-size: 9px;
  fill: var(--text-dim);
  text-anchor: middle;
  pointer-events: none;
}

/* --- Selection Rectangle (multi-select drag) --- */

.selection-rect {
  fill: rgba(212,150,74,0.08);
  stroke: var(--gold-dim);
  stroke-width: 1;
  stroke-dasharray: 4 3;
}
```

- [ ] **Step 2: Add detail panel styles**

Append to `static/css/observatory.css`:

```css
/* --- Detail Panel --- */

.detail-panel {
  font-size: 13px;
}

.detail-panel__header {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  margin-bottom: 20px;
}

.detail-panel__title {
  font-family: var(--serif);
  font-size: 20px;
  color: var(--text-bright);
  font-weight: 600;
}

.detail-panel__close {
  background: none;
  border: none;
  color: var(--text-dim);
  cursor: pointer;
  padding: 4px;
  font-size: 18px;
  line-height: 1;
}

.detail-panel__close:hover {
  color: var(--text);
}

.detail-panel__description {
  color: var(--text);
  line-height: 1.65;
  margin-bottom: 20px;
}

/* Mastery badge */
.mastery-badge {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  padding: 4px 10px;
  border-radius: 12px;
  font-family: var(--mono);
  font-size: 10px;
  text-transform: uppercase;
  letter-spacing: 0.5px;
}

.mastery-badge--mastered { background: rgba(90,240,216,0.12); color: var(--mastered); }
.mastery-badge--proficient { background: rgba(110,192,255,0.12); color: var(--proficient); }
.mastery-badge--familiar { background: rgba(240,218,108,0.1); color: var(--familiar); }
.mastery-badge--attempted { background: rgba(240,147,126,0.1); color: var(--attempted); }
.mastery-badge--not-started { background: rgba(58,64,96,0.3); color: var(--not-started); }

.mastery-badge__dot {
  width: 6px;
  height: 6px;
  border-radius: 50%;
  background: currentColor;
}

/* Mastery bar */
.mastery-bar {
  width: 100%;
  height: 4px;
  background: var(--surface-light);
  border-radius: 2px;
  overflow: hidden;
  margin: 8px 0;
}

.mastery-bar__fill {
  height: 100%;
  border-radius: 2px;
  transition: width 0.4s ease;
}

.mastery-bar__fill--mastered { background: var(--mastered); }
.mastery-bar__fill--proficient { background: var(--proficient); }
.mastery-bar__fill--familiar { background: var(--familiar); }
.mastery-bar__fill--attempted { background: var(--attempted); }
.mastery-bar__fill--not-started { background: var(--not-started); }

/* Section dividers in panel */
.detail-panel__section {
  margin-bottom: 20px;
}

.detail-panel__section-title {
  font-family: var(--mono);
  font-size: 10px;
  text-transform: uppercase;
  letter-spacing: 1px;
  color: var(--text-dim);
  margin-bottom: 10px;
  padding-bottom: 6px;
  border-bottom: 1px solid var(--border);
}

/* Edge list in detail panel */
.edge-list {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.edge-card {
  background: var(--surface);
  border: 1px solid var(--border);
  border-radius: 8px;
  padding: 12px;
}

.edge-card__header {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 6px;
}

.edge-card__type {
  font-family: var(--mono);
  font-size: 9px;
  text-transform: uppercase;
  letter-spacing: 0.8px;
  padding: 2px 6px;
  border-radius: 3px;
}

.edge-card__type--prerequisite { background: rgba(74,124,204,0.15); color: var(--edge-blue-bright); }
.edge-card__type--reinforces { background: rgba(58,170,154,0.15); color: var(--edge-teal); }
.edge-card__type--transfer { background: rgba(155,142,196,0.15); color: var(--violet); }

.edge-card__target {
  font-size: 12px;
  color: var(--text-bright);
  font-weight: 500;
}

.edge-card__description {
  font-size: 12px;
  color: var(--text);
  line-height: 1.55;
}

/* Materials list in detail panel */
.material-list {
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.material-item {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 8px 10px;
  background: var(--surface);
  border: 1px solid var(--border);
  border-radius: 6px;
  text-decoration: none;
  color: var(--text);
  font-size: 12px;
  transition: border-color 0.15s;
}

.material-item:hover {
  border-color: var(--border-glow);
  color: var(--text-bright);
}

.material-item__icon {
  width: 20px;
  height: 20px;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 14px;
  flex-shrink: 0;
}

.material-item__type {
  font-family: var(--mono);
  font-size: 9px;
  color: var(--text-dim);
  text-transform: uppercase;
  letter-spacing: 0.5px;
}

/* Action buttons in detail panel */
.detail-action {
  display: block;
  width: 100%;
  padding: 10px 16px;
  border-radius: 8px;
  font-family: var(--sans);
  font-size: 13px;
  font-weight: 500;
  cursor: pointer;
  text-align: center;
  text-decoration: none;
  transition: background 0.15s, box-shadow 0.15s;
  border: none;
}

.detail-action--primary {
  background: linear-gradient(135deg, var(--gold-dim), var(--gold));
  color: var(--void);
  box-shadow: 0 4px 20px var(--gold-glow);
}

.detail-action--primary:hover {
  box-shadow: 0 4px 30px rgba(212,150,74,0.25);
}

.detail-action--secondary {
  background: var(--surface);
  border: 1px solid var(--border);
  color: var(--text);
}

.detail-action--secondary:hover {
  border-color: var(--border-glow);
  color: var(--text-bright);
}

/* Multi-select aggregate */
.aggregate-mastery {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 12px;
  background: var(--surface);
  border: 1px solid var(--border);
  border-radius: 8px;
  margin-bottom: 16px;
}

.aggregate-mastery__value {
  font-family: var(--serif);
  font-size: 28px;
  color: var(--text-bright);
  font-weight: 600;
  line-height: 1;
}

.aggregate-mastery__label {
  font-family: var(--mono);
  font-size: 10px;
  text-transform: uppercase;
  letter-spacing: 0.8px;
  color: var(--text-dim);
}

/* Gap analysis items */
.gap-item {
  display: flex;
  align-items: flex-start;
  gap: 8px;
  padding: 8px 0;
  font-size: 12px;
  color: var(--familiar);
}

.gap-item::before {
  content: "!";
  display: flex;
  align-items: center;
  justify-content: center;
  width: 16px;
  height: 16px;
  border-radius: 50%;
  background: rgba(240,218,108,0.12);
  font-size: 10px;
  font-weight: 700;
  flex-shrink: 0;
}

/* Lesson pre-selection */
.lesson-header {
  margin-bottom: 20px;
}

.lesson-header__title {
  font-family: var(--serif);
  font-size: 20px;
  color: var(--text-bright);
  margin-bottom: 8px;
}

.lesson-header__narrative {
  font-size: 13px;
  color: var(--text);
  line-height: 1.65;
}

.retrieval-probes {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.retrieval-probe {
  padding: 10px 12px;
  background: rgba(110,192,255,0.06);
  border: 1px solid rgba(110,192,255,0.12);
  border-radius: 6px;
  font-size: 12px;
  color: var(--proficient);
  line-height: 1.5;
  font-style: italic;
}

/* Scope node list */
.scope-nodes {
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.scope-node {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 8px 10px;
  background: var(--surface);
  border: 1px solid var(--border);
  border-radius: 6px;
  font-size: 12px;
}

.scope-node__name {
  color: var(--text-bright);
}

/* Loading indicator (data-indicator) */
.loading-indicator {
  display: none;
  align-items: center;
  justify-content: center;
  padding: 24px;
}

.loading-indicator--active {
  display: flex;
}

.loading-spinner {
  width: 20px;
  height: 20px;
  border: 2px solid var(--border);
  border-top-color: var(--gold);
  border-radius: 50%;
  animation: spin 0.8s linear infinite;
}

@keyframes spin {
  to { transform: rotate(360deg); }
}
```

- [ ] **Step 3: Add tiered rendering media queries**

Append to `static/css/observatory.css`:

```css
/* --- Tiered Rendering --- */

/* Mobile: CSS gradient fallback, no parallax, no large image */
@media (max-width: 768px) {
  .celestial-bg__image {
    display: none;
  }

  .top-nav {
    padding: 0 12px;
    height: 48px;
  }

  .top-nav__brand {
    gap: 6px;
  }

  .top-nav__title {
    display: none;
  }

  .top-nav__tab {
    padding: 6px 10px;
    font-size: 10px;
  }

  .identity-frame {
    display: none;
  }

  .explore-layout {
    flex-direction: column;
  }

  .explore-layout__graph {
    height: 50vh;
  }

  .explore-layout__panel {
    width: 100%;
    max-width: 100%;
    height: 50vh;
    border-left: none;
    border-top: 1px solid var(--border);
  }

  .explore-layout__panel--collapsed {
    height: 0;
    min-width: unset;
  }

  .graph-legend {
    bottom: 10px;
    left: 10px;
    padding: 10px 12px;
  }
}

/* Reduce motion: static everything, no animations */
@media (prefers-reduced-motion: reduce) {
  *,
  *::before,
  *::after {
    animation-duration: 0s !important;
    animation-iteration-count: 1 !important;
    transition-duration: 0s !important;
  }

  .celestial-bg__image {
    transition: none !important;
    will-change: auto;
  }

  .graph-node__halo--breathing {
    animation: none !important;
    opacity: 0.5;
  }
}
```

- [ ] **Step 4: Commit**

```bash
git commit -m "feat: observatory CSS — graph viewport, node/edge styles, detail panel, tiered rendering"
```

---

### Task 5: App Shell Template

**Files:**
- Create: `learn-anything-app/templates/shell.html`

- [ ] **Step 1: Create the app shell template**

```html
<!-- templates/shell.html -->
{% extends "base.html" %}
{% block title %}Explore — Learn Anything{% endblock %}
{% block content %}

<div class="celestial-bg">
  <div class="celestial-bg__image" id="celestial-parallax"
       style="background-image: url('/static/img/celestial-bg.jpg');">
  </div>
  <div class="celestial-bg__tint"></div>
</div>
<div class="grain-overlay"></div>

<div class="app-shell"
     data-signals:active_mode="'{{ active_mode | default('explore') }}'"
     data-signals:active_skill="'demo-skill'"
     data-signals:skill_dropdown_open="false"
     data-signals:selected_nodes="[]"
     data-signals:graph_scope="'skill'"
     data-signals:graph_data="{}"
     data-signals:detail_mode="'none'"
     data-signals:detail_loading="false">

  <!-- Top Navigation Bar -->
  <nav class="top-nav">
    <a href="/" class="top-nav__brand">
      <div class="top-nav__logo"></div>
      <span class="top-nav__title">Learn Anything</span>
    </a>

    <ul class="top-nav__tabs">
      <li>
        <a href="/explore"
           class="top-nav__tab{% if active_mode == 'explore' %} top-nav__tab--active{% endif %}">
          Explore
        </a>
      </li>
      <li>
        <a href="/train"
           class="top-nav__tab{% if active_mode == 'train' %} top-nav__tab--active{% endif %}">
          Train
        </a>
      </li>
      <li>
        <a href="/materials"
           class="top-nav__tab{% if active_mode == 'materials' %} top-nav__tab--active{% endif %}">
          Materials
        </a>
      </li>
      <li>
        <a href="/progress"
           class="top-nav__tab{% if active_mode == 'progress' %} top-nav__tab--active{% endif %}">
          Progress
        </a>
      </li>
    </ul>

    <div class="top-nav__right">
      <!-- Scope Toggle: This Skill / All Skills -->
      <div class="scope-toggle">
        <button class="scope-toggle__option"
                data-on:click="$graph_scope = 'skill'"
                data-class:scope-toggle__option--active="$graph_scope === 'skill'">
          This Skill
        </button>
        <button class="scope-toggle__option"
                data-on:click="$graph_scope = 'all'"
                data-class:scope-toggle__option--active="$graph_scope === 'all'">
          All Skills
        </button>
      </div>

      <!-- Skill Switcher -->
      <div class="skill-switcher">
        <button class="skill-switcher__button"
                data-on:click="$skill_dropdown_open = !$skill_dropdown_open">
          <span data-text="$active_skill">demo-skill</span>
          <span class="skill-switcher__caret"></span>
        </button>
        <div class="skill-switcher__dropdown"
             data-class:skill-switcher__dropdown--open="$skill_dropdown_open">
          <button class="skill-switcher__item"
                  data-class:skill-switcher__item--active="$active_skill === 'demo-skill'"
                  data-on:click="$active_skill = 'demo-skill'; $skill_dropdown_open = false">
            demo-skill
          </button>
        </div>
      </div>

      <!-- Identity Frame -->
      <div class="identity-frame">
        You're becoming a <span class="identity-frame__role">learner</span>
      </div>
    </div>
  </nav>

  <!-- Mode Container -->
  <main class="mode-container">
    {% if active_mode == 'explore' %}
      {% include "explore/graph.html" %}
    {% else %}
      <div style="display:flex;align-items:center;justify-content:center;height:100%;color:var(--text-dim);">
        <p>{{ active_mode | capitalize }} mode — coming in a future plan.</p>
      </div>
    {% endif %}
  </main>

</div>

{% endblock %}
```

- [ ] **Step 2: Commit**

```bash
git commit -m "feat: app shell template — nav bar, skill switcher, scope toggle, identity frame"
```

---

### Task 6: Explore Graph Template

**Files:**
- Create: `learn-anything-app/templates/explore/graph.html`

- [ ] **Step 1: Create the graph + detail panel layout**

```html
<!-- templates/explore/graph.html -->
<div class="explore-layout"
     data-init="@get('/explore/graph-data?skill_slug=' + $active_skill)">

  <!-- D3 Knowledge Graph Island -->
  <div class="explore-layout__graph">
    <div id="knowledge-graph"
         class="graph-viewport"
         data-ignore-morph
         data-on:node-selected="$selected_nodes = [evt.detail.nodeId]; $detail_mode = 'single'; @get('/explore/detail/single?node_id=' + evt.detail.nodeId)"
         data-on:nodes-multi-selected="$selected_nodes = evt.detail.nodeIds; $detail_mode = evt.detail.nodeIds.length > 1 ? 'multi' : (evt.detail.nodeIds.length === 1 ? 'single' : 'none'); @get(evt.detail.nodeIds.length > 1 ? '/explore/detail/multi?node_ids=' + evt.detail.nodeIds.join(',') : '/explore/detail/single?node_id=' + evt.detail.nodeIds[0])"
         data-on:nodes-deselected="$selected_nodes = []; $detail_mode = 'none'"
         data-on:lesson-selected="@get('/explore/detail/lesson?lesson_id=' + evt.detail.lessonId)"
         data-indicator:detail_loading
         data-effect="if ($graph_data && $graph_data.nodes) { window.__renderGraph && window.__renderGraph($graph_data, $selected_nodes, $detail_mode) }">
    </div>

    <!-- Graph Legend -->
    <div class="graph-legend">
      <div class="graph-legend__title">Mastery</div>
      <div class="graph-legend__items">
        <div class="graph-legend__item">
          <div class="graph-legend__swatch graph-legend__swatch--mastered"></div>
          <span>Mastered</span>
        </div>
        <div class="graph-legend__item">
          <div class="graph-legend__swatch graph-legend__swatch--proficient"></div>
          <span>Proficient</span>
        </div>
        <div class="graph-legend__item">
          <div class="graph-legend__swatch graph-legend__swatch--familiar"></div>
          <span>Familiar</span>
        </div>
        <div class="graph-legend__item">
          <div class="graph-legend__swatch graph-legend__swatch--attempted"></div>
          <span>Attempted</span>
        </div>
        <div class="graph-legend__item">
          <div class="graph-legend__swatch graph-legend__swatch--not-started"></div>
          <span>Not Started</span>
        </div>
      </div>
      <div class="graph-legend__divider"></div>
      <div class="graph-legend__items">
        <div class="graph-legend__line">
          <div class="graph-legend__line-sample graph-legend__line-sample--prerequisite"></div>
          <span>Prerequisite</span>
        </div>
        <div class="graph-legend__line">
          <div class="graph-legend__line-sample graph-legend__line-sample--reinforces"></div>
          <span>Reinforces</span>
        </div>
        <div class="graph-legend__line">
          <div class="graph-legend__line-sample graph-legend__line-sample--transfer"></div>
          <span>Transfer</span>
        </div>
      </div>
    </div>
  </div>

  <!-- Detail Panel -->
  <div class="explore-layout__panel"
       id="detail-panel-container"
       data-class:explore-layout__panel--collapsed="$detail_mode === 'none'">
    <div id="detail-panel">
      <!-- Fragments injected here by SSE responses -->
      <div class="loading-indicator" data-class:loading-indicator--active="$detail_loading">
        <div class="loading-spinner"></div>
      </div>
    </div>
  </div>

</div>

<!-- D3 is loaded globally in base.html (pinned + SRI hash). graph.js uses window.d3. -->
<script src="/static/js/graph.js" defer></script>
```

- [ ] **Step 2: Commit**

```bash
git commit -m "feat: explore graph template — D3 island, legend, detail panel container"
```

---

### Task 7: Detail Panel Fragment Templates

**Files:**
- Create: `learn-anything-app/templates/explore/detail_single.html`
- Create: `learn-anything-app/templates/explore/detail_multi.html`
- Create: `learn-anything-app/templates/explore/detail_lesson.html`

- [ ] **Step 1: Create single-node detail fragment**

```html
<!-- templates/explore/detail_single.html -->
<div id="detail-panel" class="detail-panel">
  <div class="detail-panel__header">
    <h2 class="detail-panel__title">{{ node.name }}</h2>
    <button class="detail-panel__close"
            data-on:click="$detail_mode = 'none'; $selected_nodes = []"
            title="Close panel">&times;</button>
  </div>

  <!-- Mastery State -->
  <div class="detail-panel__section">
    <span class="mastery-badge mastery-badge--{{ node.mastery }}">
      <span class="mastery-badge__dot"></span>
      {{ node.mastery | replace('_', ' ') | capitalize }}
    </span>
    <div class="mastery-bar">
      <div class="mastery-bar__fill mastery-bar__fill--{{ node.mastery }}"
           style="width: {{ (node.mastery_probability * 100) | round }}%"></div>
    </div>
    <div style="display:flex;justify-content:space-between;font-family:var(--mono);font-size:10px;color:var(--text-dim);">
      <span>{{ (node.mastery_probability * 100) | round }}% mastery</span>
      <span>{{ node.evidence_count }} evidence{{ 's' if node.evidence_count != 1 }}</span>
    </div>
  </div>

  <!-- Description -->
  <div class="detail-panel__section">
    <div class="detail-panel__section-title">Description</div>
    <p class="detail-panel__description">{{ node.description }}</p>
  </div>

  <!-- Bloom Level + Metadata -->
  <div class="detail-panel__section">
    <div class="detail-panel__section-title">Metadata</div>
    <div style="display:flex;gap:8px;flex-wrap:wrap;">
      <span class="mastery-badge" style="background:var(--surface);color:var(--text);">
        Bloom: {{ node.bloom_level | capitalize }}
      </span>
      {% if node.last_assessed %}
      <span class="mastery-badge" style="background:var(--surface);color:var(--text);">
        Last assessed: {{ node.last_assessed }}
      </span>
      {% endif %}
    </div>
  </div>

  <!-- Connected Edges (the WHY of each connection) -->
  <div class="detail-panel__section">
    <div class="detail-panel__section-title">Connections</div>
    <div class="edge-list">
      {% for edge in edges %}
      <div class="edge-card">
        <div class="edge-card__header">
          <span class="edge-card__type edge-card__type--{{ edge.edge_type | lower }}">
            {{ edge.edge_type }}{% if edge.prerequisite_type %} ({{ edge.prerequisite_type }}){% endif %}
          </span>
          <span class="edge-card__target">{{ edge.target_name }}</span>
        </div>
        <p class="edge-card__description">{{ edge.description }}</p>
      </div>
      {% endfor %}
    </div>
  </div>

  <!-- Materials -->
  {% if materials %}
  <div class="detail-panel__section">
    <div class="detail-panel__section-title">Materials</div>
    <div class="material-list">
      {% for mat in materials %}
      <a href="/materials/{{ mat.type }}" class="material-item">
        <span class="material-item__icon">
          {% if mat.type == 'lecture' %}&#128218;{% elif mat.type == 'flashcard_deck' %}&#127183;{% elif mat.type == 'worked_example' %}&#128221;{% elif mat.type == 'video' %}&#127909;{% else %}&#128196;{% endif %}
        </span>
        <span>
          {{ mat.title }}
          <br><span class="material-item__type">{{ mat.type | replace('_', ' ') }} &middot; {{ mat.format }}</span>
        </span>
      </a>
      {% endfor %}
    </div>
  </div>
  {% endif %}

  <!-- Action: Train on this topic -->
  <div class="detail-panel__section">
    <a href="/train?focus={{ node.id }}" class="detail-action detail-action--primary">
      Train on this topic
    </a>
  </div>
</div>
```

- [ ] **Step 2: Create multi-select detail fragment**

```html
<!-- templates/explore/detail_multi.html -->
<div id="detail-panel" class="detail-panel">
  <div class="detail-panel__header">
    <h2 class="detail-panel__title">{{ node_count }} Nodes Selected</h2>
    <button class="detail-panel__close"
            data-on:click="$detail_mode = 'none'; $selected_nodes = []"
            title="Close panel">&times;</button>
  </div>

  <!-- Aggregate Mastery -->
  <div class="aggregate-mastery">
    <div class="aggregate-mastery__value">{{ (aggregate_mastery * 100) | round }}%</div>
    <div>
      <div class="aggregate-mastery__label">Aggregate Mastery</div>
      <div class="mastery-bar" style="margin-top:6px;">
        <div class="mastery-bar__fill mastery-bar__fill--{% if aggregate_mastery >= 0.8 %}mastered{% elif aggregate_mastery >= 0.6 %}proficient{% elif aggregate_mastery >= 0.35 %}familiar{% elif aggregate_mastery > 0 %}attempted{% else %}not-started{% endif %}"
             style="width: {{ (aggregate_mastery * 100) | round }}%"></div>
      </div>
    </div>
  </div>

  <!-- Selected Nodes -->
  <div class="detail-panel__section">
    <div class="detail-panel__section-title">Selected Nodes</div>
    <div class="scope-nodes">
      {% for n in nodes %}
      <div class="scope-node">
        <span class="scope-node__name">{{ n.name }}</span>
        <span class="mastery-badge mastery-badge--{{ n.mastery }}">
          <span class="mastery-badge__dot"></span>
          {{ (n.mastery_probability * 100) | round }}%
        </span>
      </div>
      {% endfor %}
    </div>
  </div>

  <!-- Internal Edges -->
  {% if internal_edges %}
  <div class="detail-panel__section">
    <div class="detail-panel__section-title">Internal Connections</div>
    <div class="edge-list">
      {% for edge in internal_edges %}
      <div class="edge-card">
        <div class="edge-card__header">
          <span class="edge-card__type edge-card__type--{{ edge.edge_type | lower }}">
            {{ edge.edge_type }}
          </span>
          <span class="edge-card__target">{{ edge.from_name }} &rarr; {{ edge.to_name }}</span>
        </div>
        <p class="edge-card__description">{{ edge.description }}</p>
      </div>
      {% endfor %}
    </div>
  </div>
  {% endif %}

  <!-- Gap Analysis -->
  {% if gaps %}
  <div class="detail-panel__section">
    <div class="detail-panel__section-title">Gap Analysis</div>
    {% for gap in gaps %}
    <div class="gap-item">{{ gap }}</div>
    {% endfor %}
  </div>
  {% endif %}

  <!-- Actions -->
  <div class="detail-panel__section" style="display:flex;flex-direction:column;gap:8px;">
    <button class="detail-action detail-action--primary"
            data-on:click="@get('/explore/synthesize?node_ids={{ nodes | map(attribute='id') | join(',') }}')">
      Synthesize with LLM
    </button>
    <a href="/train?focus={{ nodes | map(attribute='id') | join(',') }}"
       class="detail-action detail-action--secondary">
      Train on selected
    </a>
  </div>
</div>
```

- [ ] **Step 3: Create lesson pre-selection detail fragment**

```html
<!-- templates/explore/detail_lesson.html -->
<div id="detail-panel" class="detail-panel">
  <div class="detail-panel__header">
    <h2 class="detail-panel__title">{{ lesson.title }}</h2>
    <button class="detail-panel__close"
            data-on:click="$detail_mode = 'none'; $selected_nodes = []"
            title="Close panel">&times;</button>
  </div>

  <!-- Narrative Context -->
  <div class="lesson-header">
    <p class="lesson-header__narrative">{{ lesson.narrative }}</p>
  </div>

  <!-- Scope Nodes (session agenda) -->
  <div class="detail-panel__section">
    <div class="detail-panel__section-title">Session Scope</div>
    <div class="scope-nodes">
      {% for n in lesson.scope_nodes %}
      <div class="scope-node">
        <span class="scope-node__name">{{ n.name }}</span>
        <span class="mastery-badge mastery-badge--{{ n.mastery }}">
          <span class="mastery-badge__dot"></span>
          {{ n.mastery | replace('_', ' ') | capitalize }}
        </span>
      </div>
      {% endfor %}
    </div>
  </div>

  <!-- Retrieval Probes from Prior Sessions -->
  {% if lesson.retrieval_probes %}
  <div class="detail-panel__section">
    <div class="detail-panel__section-title">Retrieval Probes</div>
    <div class="retrieval-probes">
      {% for probe in lesson.retrieval_probes %}
      <div class="retrieval-probe">{{ probe }}</div>
      {% endfor %}
    </div>
  </div>
  {% endif %}

  <!-- Begin Session -->
  <div class="detail-panel__section">
    <a href="/train?lesson={{ lesson.id }}"
       class="detail-action detail-action--primary">
      Begin Session
    </a>
  </div>
</div>
```

- [ ] **Step 4: Run tests — should now pass**

Run: `cd learn-anything-app && uv run pytest tests/integration/test_routes/test_explore.py -v`
Expected: All PASS. Templates exist, routes return correct content types and contain expected markers.

- [ ] **Step 5: Commit**

```bash
git commit -m "feat: detail panel templates — single node, multi-select, lesson pre-selection"
```

---

### Task 8: D3 Knowledge Graph Rendering (graph.js)

**Files:**
- Create: `learn-anything-app/static/js/graph.js`

- [ ] **Step 1: Create the D3 graph renderer**

```javascript
// static/js/graph.js
//
// D3 knowledge graph island. Renders inside #knowledge-graph (data-ignore-morph).
// Communicates with Datastar by dispatching CustomEvents (node-selected,
// nodes-multi-selected, nodes-deselected) on the container element.
// Datastar picks these up via data-on:<event-name> attributes.
// Does NOT use fetch/XHR — Datastar handles all server communication.

(function () {
  "use strict";

  // Wait for D3 to load
  function waitForD3(callback) {
    if (window.d3) {
      callback(window.d3);
    } else {
      setTimeout(() => waitForD3(callback), 50);
    }
  }

  // ── Color palette (mirrors observatory.css variables) ──────────────
  const MASTERY_COLORS = {
    mastered:    { core: "#5af0d8", halo: "rgba(90,240,216,0.25)",  gradient: ["#5af0d8", "#3aaa9a"] },
    proficient:  { core: "#6ec0ff", halo: "rgba(110,192,255,0.22)", gradient: ["#6ec0ff", "#4a7ccc"] },
    familiar:    { core: "#f0da6c", halo: "rgba(240,218,108,0.18)", gradient: ["#f0da6c", "#c4a834"] },
    attempted:   { core: "#f0937e", halo: "rgba(240,147,126,0.15)", gradient: ["#f0937e", "#cc6a55"] },
    not_started: { core: "#3a4060", halo: "rgba(58,64,96,0.1)",     gradient: ["#4a5070", "#3a4060"] },
  };

  const EDGE_COLORS = {
    PREREQUISITE: "#4a7ccc",
    REINFORCES:   "#3aaa9a",
    SIMILAR_TO:   "#9b8ec4",
    EMBODIES:     "#9b8ec4",
    GENERALIZES:  "#9b8ec4",
    NEGATIVE_TRANSFER: "#f0937e",
  };

  // ── Node sizing ────────────────────────────────────────────────────
  function nodeRadius(d) {
    const freq = d.frequency_score || 0.5;
    const impact = d.impact_score || 0.5;
    return 12 + (freq * impact) * 20;
  }

  // ── SVG Defs (glow filters, gradients) ─────────────────────────────
  function createDefs(svg, nodes) {
    const defs = svg.append("defs");

    // Edge glow filter
    defs.append("filter")
      .attr("id", "edge-glow")
      .attr("x", "-50%").attr("y", "-50%")
      .attr("width", "200%").attr("height", "200%")
      .append("feGaussianBlur")
        .attr("stdDeviation", "3")
        .attr("result", "blur");
    defs.select("#edge-glow")
      .append("feMerge")
      .selectAll("feMergeNode")
      .data(["blur", "SourceGraphic"])
      .enter()
      .append("feMergeNode")
        .attr("in", d => d);

    // Node halo filter
    defs.append("filter")
      .attr("id", "node-halo-blur")
      .attr("x", "-100%").attr("y", "-100%")
      .attr("width", "300%").attr("height", "300%")
      .append("feGaussianBlur")
        .attr("stdDeviation", "8");

    // Per-node radial gradients
    nodes.forEach(n => {
      const mc = MASTERY_COLORS[n.mastery] || MASTERY_COLORS.not_started;
      const grad = defs.append("radialGradient")
        .attr("id", `node-grad-${n.id}`)
        .attr("cx", "35%").attr("cy", "35%").attr("r", "65%");
      grad.append("stop").attr("offset", "0%").attr("stop-color", mc.gradient[0]).attr("stop-opacity", 1);
      grad.append("stop").attr("offset", "100%").attr("stop-color", mc.gradient[1]).attr("stop-opacity", 0.8);
    });
  }

  // ── Parallax: link celestial background to graph pan ───────────────
  function updateParallax(transform) {
    if (window.matchMedia("(prefers-reduced-motion: reduce)").matches) return;
    const bgEl = document.getElementById("celestial-parallax");
    if (!bgEl) return;
    // 0.15x rate
    const px = -transform.x * 0.15;
    const py = -transform.y * 0.15;
    bgEl.style.transform = `translate(${px}px, ${py}px) scale(${1 + transform.k * 0.02})`;
  }

  // ── Main render function ───────────────────────────────────────────
  // Called by Datastar data-effect when $graph_data changes.
  function renderGraph(graphData, selectedNodes, detailMode) {
    const container = document.getElementById("knowledge-graph");
    if (!container || !window.d3) return;
    const d3 = window.d3;

    const nodes = graphData.nodes || [];
    const edges = graphData.edges || [];
    if (nodes.length === 0) return;

    const selectedSet = new Set(selectedNodes || []);
    const width = container.clientWidth;
    const height = container.clientHeight;

    // Clear previous render
    d3.select(container).select("svg").remove();

    const svg = d3.select(container)
      .append("svg")
      .attr("width", width)
      .attr("height", height)
      .attr("viewBox", `0 0 ${width} ${height}`);

    createDefs(svg, nodes);

    // Zoom + pan group
    const g = svg.append("g");

    const zoom = d3.zoom()
      .scaleExtent([0.3, 4])
      .on("zoom", (event) => {
        g.attr("transform", event.transform);
        updateParallax(event.transform);
      });

    svg.call(zoom);

    // Build node lookup
    const nodeMap = new Map(nodes.map(n => [n.id, n]));

    // ── Edges ──────────────────────────────────────────────────────
    const edgeGroup = g.append("g").attr("class", "edges");

    // Determine scope node IDs for lesson pre-selection dimming
    let scopeIds = null;
    if (detailMode === "lesson" && selectedNodes && selectedNodes.length > 0) {
      scopeIds = new Set(selectedNodes);
    }

    const edgeSelection = edgeGroup.selectAll(".graph-edge")
      .data(edges)
      .enter()
      .append("line")
        .attr("class", d => {
          const type = (d.edge_type || "PREREQUISITE").toUpperCase();
          const cssType = ['SIMILAR_TO','EMBODIES','GENERALIZES','NEGATIVE_TRANSFER'].includes(type) ? 'transfer' : type.toLowerCase();
          let cls = `graph-edge graph-edge--${cssType}`;
          // Dim edges not connected to selected/scope nodes
          if (scopeIds) {
            if (!scopeIds.has(d.from_id) || !scopeIds.has(d.to_id)) {
              cls += " graph-edge--dimmed";
            }
          } else if (selectedSet.size > 0) {
            const fromSel = selectedSet.has(d.from_id);
            const toSel = selectedSet.has(d.to_id);
            if (!fromSel && !toSel) {
              cls += " graph-edge--dimmed";
            } else if (fromSel && toSel) {
              cls += " graph-edge--highlighted";
            }
          }
          return cls;
        })
        .attr("x1", d => (nodeMap.get(d.from_id) || {}).x || 0)
        .attr("y1", d => (nodeMap.get(d.from_id) || {}).y || 0)
        .attr("x2", d => (nodeMap.get(d.to_id) || {}).x || 0)
        .attr("y2", d => (nodeMap.get(d.to_id) || {}).y || 0)
        .attr("stroke", d => EDGE_COLORS[(d.edge_type || "PREREQUISITE").toUpperCase()] || "#4a7ccc");

    // Edge labels on dark pill backgrounds
    const edgeLabelGroup = g.append("g").attr("class", "edge-labels");

    edges.forEach(e => {
      const from = nodeMap.get(e.from_id);
      const to = nodeMap.get(e.to_id);
      if (!from || !to) return;
      const mx = (from.x + to.x) / 2;
      const my = (from.y + to.y) / 2;
      const type = (e.edge_type || "PREREQUISITE").toUpperCase();
      const label = type.replace(/_/g, " ");

      // Dimming check
      if (scopeIds && (!scopeIds.has(e.from_id) || !scopeIds.has(e.to_id))) return;
      if (!scopeIds && selectedSet.size > 0 && !selectedSet.has(e.from_id) && !selectedSet.has(e.to_id)) return;

      const lg = edgeLabelGroup.append("g").attr("transform", `translate(${mx}, ${my})`);

      // Measure text width to size the pill
      const textNode = lg.append("text")
        .attr("class", "graph-edge__label")
        .text(label);
      const bbox = textNode.node().getBBox();
      const padX = 6, padY = 3;

      lg.insert("rect", "text")
        .attr("class", "graph-edge__label-bg")
        .attr("x", bbox.x - padX)
        .attr("y", bbox.y - padY)
        .attr("width", bbox.width + padX * 2)
        .attr("height", bbox.height + padY * 2);
    });

    // ── Nodes ──────────────────────────────────────────────────────
    const nodeGroup = g.append("g").attr("class", "nodes");

    const reducedMotion = window.matchMedia("(prefers-reduced-motion: reduce)").matches;

    const nodeG = nodeGroup.selectAll(".graph-node")
      .data(nodes)
      .enter()
      .append("g")
        .attr("class", d => {
          let cls = "graph-node";
          if (selectedSet.has(d.id)) cls += " graph-node--selected";
          if (scopeIds && !scopeIds.has(d.id)) cls += " graph-node--dimmed";
          return cls;
        })
        .attr("transform", d => `translate(${d.x}, ${d.y})`);

    // Glow halo (blurred circle behind node)
    nodeG.append("circle")
      .attr("class", d => {
        let cls = "graph-node__halo";
        if (!reducedMotion && !selectedSet.has(d.id)) cls += " graph-node__halo--breathing";
        return cls;
      })
      .attr("r", d => nodeRadius(d) + 12)
      .attr("fill", d => (MASTERY_COLORS[d.mastery] || MASTERY_COLORS.not_started).halo)
      .attr("filter", "url(#node-halo-blur)");

    // Core node circle with radial gradient
    nodeG.append("circle")
      .attr("class", "graph-node__core")
      .attr("r", d => nodeRadius(d))
      .attr("fill", d => `url(#node-grad-${d.id})`)
      .attr("stroke", d => (MASTERY_COLORS[d.mastery] || MASTERY_COLORS.not_started).core)
      .attr("stroke-width", 1.5)
      .attr("stroke-opacity", 0.6);

    // Bright highlight point (simulates specular reflection)
    nodeG.append("circle")
      .attr("cx", d => -nodeRadius(d) * 0.25)
      .attr("cy", d => -nodeRadius(d) * 0.25)
      .attr("r", d => nodeRadius(d) * 0.18)
      .attr("fill", "rgba(255,255,255,0.35)")
      .attr("pointer-events", "none");

    // Label below node
    nodeG.append("text")
      .attr("class", "graph-node__label")
      .attr("y", d => nodeRadius(d) + 16)
      .text(d => d.name);

    // ── Click interactions ─────────────────────────────────────────
    // D3 communicates with Datastar by dispatching CustomEvents on the
    // graph container. Datastar picks these up via data-on:<event-name>
    // attributes on #knowledge-graph and updates signals / triggers SSE.

    nodeG.on("click", function (event, d) {
      event.stopPropagation();

      if (event.shiftKey) {
        // Multi-select: toggle node in selection
        const idx = selectedNodes.indexOf(d.id);
        let newSelection;
        if (idx >= 0) {
          newSelection = [...selectedNodes];
          newSelection.splice(idx, 1);
        } else {
          newSelection = [...selectedNodes, d.id];
        }
        if (newSelection.length > 0) {
          container.dispatchEvent(new CustomEvent('nodes-multi-selected', { detail: { nodeIds: newSelection } }));
        } else {
          container.dispatchEvent(new CustomEvent('nodes-deselected'));
        }
      } else {
        // Single click: select this node only
        container.dispatchEvent(new CustomEvent('node-selected', { detail: { nodeId: d.id } }));
      }
    });

    // Click on empty space to deselect
    svg.on("click", function (event) {
      if (event.target === this || event.target.tagName === "svg") {
        container.dispatchEvent(new CustomEvent('nodes-deselected'));
      }
    });

    // ── Drag selection rectangle ───────────────────────────────────
    let dragStartX, dragStartY, selectionRect;

    svg.on("mousedown", function (event) {
      // Only start drag selection on direct SVG clicks, not on nodes
      if (event.target !== this && event.target.tagName !== "svg") return;
      if (event.button !== 0) return;
      // If shift is held, enter selection mode instead of pan
      if (!event.shiftKey) return;

      event.preventDefault();
      const [mx, my] = d3.pointer(event, g.node());
      dragStartX = mx;
      dragStartY = my;

      selectionRect = g.append("rect")
        .attr("class", "selection-rect")
        .attr("x", mx).attr("y", my)
        .attr("width", 0).attr("height", 0);

      // Disable zoom during drag select
      svg.on(".zoom", null);
    });

    svg.on("mousemove", function (event) {
      if (!selectionRect) return;
      const [mx, my] = d3.pointer(event, g.node());
      const x = Math.min(dragStartX, mx);
      const y = Math.min(dragStartY, my);
      const w = Math.abs(mx - dragStartX);
      const h = Math.abs(my - dragStartY);
      selectionRect.attr("x", x).attr("y", y).attr("width", w).attr("height", h);
    });

    svg.on("mouseup", function (event) {
      if (!selectionRect) return;
      const [mx, my] = d3.pointer(event, g.node());
      const x1 = Math.min(dragStartX, mx);
      const y1 = Math.min(dragStartY, my);
      const x2 = Math.max(dragStartX, mx);
      const y2 = Math.max(dragStartY, my);

      // Find nodes within the selection rectangle
      const selected = nodes
        .filter(n => n.x >= x1 && n.x <= x2 && n.y >= y1 && n.y <= y2)
        .map(n => n.id);

      selectionRect.remove();
      selectionRect = null;

      // Re-enable zoom
      svg.call(zoom);

      if (selected.length > 1) {
        container.dispatchEvent(new CustomEvent('nodes-multi-selected', { detail: { nodeIds: selected } }));
      } else if (selected.length === 1) {
        container.dispatchEvent(new CustomEvent('node-selected', { detail: { nodeId: selected[0] } }));
      }
    });

    // Center the graph
    const xExtent = d3.extent(nodes, d => d.x);
    const yExtent = d3.extent(nodes, d => d.y);
    const graphWidth = (xExtent[1] - xExtent[0]) || width;
    const graphHeight = (yExtent[1] - yExtent[0]) || height;
    const centerX = (xExtent[0] + xExtent[1]) / 2;
    const centerY = (yExtent[0] + yExtent[1]) / 2;
    const scale = Math.min(width / (graphWidth + 200), height / (graphHeight + 200), 1.5);
    const tx = width / 2 - centerX * scale;
    const ty = height / 2 - centerY * scale;

    svg.call(zoom.transform, d3.zoomIdentity.translate(tx, ty).scale(scale));
  }

  // Expose render function globally for Datastar data-effect
  window.__renderGraph = renderGraph;

  // Initial render attempt (Datastar may have already pushed signals)
  waitForD3(() => {
    // Graph will render when Datastar pushes graph_data via data-effect
  });
})();
```

- [ ] **Step 2: Verify the file loads without syntax errors**

Run: `cd learn-anything-app && node --check static/js/graph.js`
Expected: No syntax errors.

- [ ] **Step 3: Commit**

```bash
git commit -m "feat: D3 knowledge graph — nodes, edges, parallax, click/multi-select/drag interactions"
```

---

### Task 9: Create Static Image Directory

**Files:**
- Create: `learn-anything-app/static/img/.gitkeep`

The celestial background image will be placed here by the user. A placeholder is not committed (licensing TBD per spec Section 13).

- [ ] **Step 1: Create the directory**

```bash
mkdir -p learn-anything-app/static/img
touch learn-anything-app/static/img/.gitkeep
```

- [ ] **Step 2: Commit**

```bash
git commit -m "chore: static/img directory for celestial background image"
```

---

### Task 10: Wire Routes + Run Full Test Suite

**Files:**
- Modify: `learn-anything-app/app/main.py` (verify all routers registered)
- Modify: `learn-anything-app/tests/conftest.py` (ensure explore route imports if needed)

- [ ] **Step 1: Verify main.py has all route registrations**

The bottom of `app/main.py` should include (add if not already present from earlier tasks):

```python
from app.routes.health import router as health_router
from app.routes.auth import router as auth_router
from app.routes.setup import router as setup_router
from app.routes.explore import router as explore_router

app.include_router(health_router)
app.include_router(auth_router)
app.include_router(setup_router)
app.include_router(explore_router)
```

Also add a root route that redirects to explore:

```python
@app.get("/")
async def root(request: Request):
    return RedirectResponse("/explore")
```

- [ ] **Step 2: Update the SetupGuardMiddleware to allow explore routes**

In the `SetupGuardMiddleware.dispatch` method, update the path check to also allow `/explore` during development. In production this would be guarded, but for Plan 4 testing we need the route accessible:

```python
class SetupGuardMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        path = request.url.path
        if path.startswith(("/health", "/static", "/setup", "/explore")):
            return await call_next(request)
        if not settings.setup_complete:
            return RedirectResponse("/setup")
        return await call_next(request)
```

- [ ] **Step 3: Run the full test suite**

Run: `cd learn-anything-app && uv run pytest tests/ -v --tb=short`
Expected: All tests pass — both existing Plan 1 tests and new Plan 4 explore tests.

- [ ] **Step 4: Manual visual verification**

Start the dev server:
```bash
cd learn-anything-app && uv run uvicorn app.main:app --reload
```

Open `http://localhost:8000/explore` in a browser. Verify:
1. Celestial gradient background renders (no image yet, CSS gradient fallback)
2. Grain texture overlay is visible but subtle
3. Top nav bar with Explore/Train/Materials/Progress tabs
4. Explore tab is highlighted (gold)
5. Skill switcher dropdown toggles on click
6. Scope toggle (This Skill / All Skills) switches
7. Graph legend renders in bottom-left
8. D3 renders 5 demo nodes with radial gradients and glow halos
9. Constellation-style edges connect nodes with type-colored lines
10. Edge labels on dark pill backgrounds at edge midpoints
11. Breathing animation on node halos (unless prefers-reduced-motion)
12. Single click on a node opens detail panel on right with edges, materials, mastery
13. Shift+click adds to multi-selection, panel shows aggregate mastery
14. Drag selection (shift+mousedown) on empty space creates selection rectangle
15. Panning the graph moves the celestial background at 0.15x rate
16. Detail panel close button works

- [ ] **Step 5: Mobile verification**

Resize browser to < 768px width. Verify:
1. Celestial background falls back to CSS gradient (no image element)
2. Navigation collapses (title hidden, smaller tabs)
3. Graph takes top half, detail panel takes bottom half
4. Identity frame hidden on mobile

- [ ] **Step 6: Reduce-motion verification**

Enable "Reduce motion" in OS accessibility settings. Verify:
1. No breathing animation on node halos
2. No transition animations
3. Parallax disabled (background stays static)

- [ ] **Step 7: Commit**

```bash
git commit -m "feat: Plan 4 complete — app shell, explore mode with D3 graph, detail panels, Observatory visual identity"
```

---

## Summary

| Task | What It Does | Tests |
|------|-------------|-------|
| 1 | TDD: Write failing route tests | 7 tests |
| 2 | Explore routes (SSE graph data, SSE detail fragment endpoints via datastar-py) | Makes tests pass (templates still needed) |
| 3 | Observatory CSS: celestial bg, grain, app shell, nav, skill switcher | Visual |
| 4 | Observatory CSS: graph viewport, node/edge styles, detail panel, tiered rendering | Visual |
| 5 | App shell template (nav, skill switcher, scope toggle, identity frame, mode container) | Visual |
| 6 | Graph template (D3 island, legend, detail panel container) | Visual |
| 7 | Detail fragment templates (single, multi, lesson) | Tests pass |
| 8 | D3 graph.js (nodes, edges, parallax, click/multi-select/drag) | Manual visual |
| 9 | Static image directory | N/A |
| 10 | Wire everything, full test suite, manual visual verification | All pass |

**Total new files:** 8 created, 2 modified
**Total commits:** 10
**Estimated time:** 60-90 minutes
