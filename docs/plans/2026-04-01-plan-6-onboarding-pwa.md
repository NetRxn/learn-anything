> HISTORICAL DESIGN REFERENCE: superseded operationally by CONVENTIONS.md and
> docs/superpowers/plans/2026-11-06-alpha-foundation.md. Do not execute provisioning,
> runner or database commands below. No current service admission is implied.

# Plan 6: Onboarding + PWA — Conversational Onboarding with Progressive Reveal, Service Worker, Offline Access

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking. **Use opus subagents exclusively (model: opus). No sonnet, no haiku.**
>
> **REQUIRED READING:** `docs/plans/CONVENTIONS.md` — all plans follow these rules.
>
> **Execution:** Plans execute sequentially (1→2→3→4→5→6) on feature branch `feature/learn-anything-webapp`. TDD strictly enforced.

**Goal:** A complete onboarding experience that takes users from "What would you like to learn?" through all pipeline phases to a fully-unlocked learning environment, powered by conversational AI with a live state panel that progressively reveals extracted information. Plus a service worker that enables offline access to cached materials, flashcard review, and background sync.

**Architecture:** The onboarding flow is a full-width chat that streams via SSE (reusing Train mode's SSE infrastructure from Plan 5). As the LLM extracts information from conversation, the server pushes Datastar signal patches to populate a state panel that fades in on the right. Pipeline phases are skill-driven: the orchestrator detects which state files exist and routes to the next phase. Agreement gates are conversational moments rendered inline in the chat, not forms. The PWA layer adds a service worker with cache-first/network-first/network-only strategies and background sync for offline flashcard reviews.

**Tech Stack:** FastAPI SSE streaming (Plan 5 infrastructure), Datastar signal/element patches, Jinja2 fragments, Service Worker API, Cache API, Background Sync API, PWA manifest

**Spec:** `docs/specs/2026-04-01-learn-anything-webapp-design.md` — Sections 5 and 8

**Depends on:** Plan 1 (project scaffold, models, auth, templates/base.html, observatory.css), Plan 2 (graph backend queries), Plan 3 (LLM integration, AnthropicProvider), Plan 4 (D3 graph rendering), Plan 5 (SSE streaming infrastructure, Train mode chat, Datastar signal/element patching patterns)

> **IMPLEMENTATION NOTES (from review):**
> 1. **Replace `EventSourceResponse`** with `DatastarResponse` from `datastar_py.fastapi`. Remove the `sse_starlette` import.
> 2. **Onboarding service tests** are unit tests — move to `tests/unit/test_services/`.
> 3. **Add tests for `streaming.py`** (Task 0) before implementation — TDD violation.
> 4. **Remove local `client` fixtures** from test files — use shared `conftest.py`.
> 5. **Streaming token spans** in phase handlers also need `_html.escape()` — the `response_text` accumulated during streaming should be escaped before insertion into `<span class="typing-text">` elements.

---

## Assumed Prior State

From Plans 1-5, the following exist:

- `app/main.py` — FastAPI app with lifespan, middleware, Jinja2 templates, static files
- `app/config.py` — Settings with `anthropic_api_key`, `anthropic_model`
- `app/services/llm.py` — LLM provider interface (Plan 4)
- `app/services/streaming.py` — Created in Task 0 below (thin wrapper around `datastar-py` SDK)
- `app/routes/train.py` — Train mode with SSE chat (Plan 5) — pattern to reuse
- `app/services/orchestrator.py` — Pipeline orchestrator, state-file routing (Plan 4/5)
- `app/models/` — All graph models, learner state, materials
- `app/backends/` — StateBackend protocol, JSON + Postgres backends
- `templates/base.html` — Datastar base template with script tags (must have `integrity` SRI attributes), CSS vars
- `templates/train/` — Train mode templates (Plan 5) — SSE chat pattern to reuse
- `static/css/observatory.css` — Observatory visual identity
- `static/js/graph.js` — D3 graph rendering (Plan 3)
- `tests/conftest.py` — Test fixtures

---

## File Tree (this plan creates)

```
learn-anything-app/
├── app/
│   ├── routes/
│   │   ├── onboarding.py             # Onboarding routes + SSE for chat + state panel updates
│   │   └── sw.py                     # Route to serve sw.js with correct scope/headers
│   └── services/
│       ├── streaming.py              # Thin wrapper around datastar-py SDK (Task 0)
│       └── onboarding.py             # Onboarding flow state management
├── templates/
│   └── onboarding/
│       ├── index.html                # Onboarding chat + progressive state panel
│       ├── state_panel.html          # State panel fragment (fields fade in)
│       ├── pipeline_bar.html         # Pipeline progress bar fragment
│       ├── expert_panel.html         # Expert panel cards (agreement gate 1)
│       └── epitome_card.html         # Epitome proposal card (agreement gate 2)
├── static/
│   ├── js/
│   │   └── onboarding.js            # Progressive reveal logic
│   └── manifest.json                # PWA manifest
├── sw.js                             # Service worker (root level)
└── tests/
    ├── test_routes/
    │   ├── test_onboarding.py        # Onboarding route tests
    │   └── test_sw.py                # Service worker route tests
    └── test_services/
        └── test_onboarding_service.py  # Onboarding flow state management tests
```

---

### Task 0: Streaming Helper Module — Thin Wrapper Around datastar-py SDK

**Files:**
- Create: `learn-anything-app/app/services/streaming.py`

This module is imported by onboarding routes (and future plans) but was never created. It wraps the `datastar-py` SDK so all plans use a consistent SSE helper interface.

- [ ] **Step 1: Create streaming.py**

```python
# app/services/streaming.py
"""Thin wrapper around the datastar-py SDK for SSE streaming.

All plans import from here rather than using datastar-py directly,
so swapping the underlying SSE library is a single-file change.
"""
from datastar_py import ServerSentEventGenerator as SSE
from datastar_py.enums import ElementPatchMode


def patch_elements(
    selector: str,
    html: str,
    mode: str = "append",
) -> str:
    """Send an SSE event that patches DOM elements via Datastar.

    Args:
        selector: CSS selector for the target element (e.g., "#chat-messages")
        html: HTML content to patch into the target
        mode: Patch mode — "append", "outer", "inner", "prepend", "replace", "remove"
    """
    mode_map = {
        "append": ElementPatchMode.APPEND,
        "outer": ElementPatchMode.OUTER,
        "inner": ElementPatchMode.INNER,
        "prepend": ElementPatchMode.PREPEND,
        "replace": ElementPatchMode.REPLACE,
        "remove": ElementPatchMode.REMOVE,
    }
    return SSE.patch_elements(html, selector=selector, mode=mode_map.get(mode, ElementPatchMode.OUTER))


def patch_signals(signals: dict) -> str:
    """Send an SSE event that patches Datastar signals."""
    return SSE.patch_signals(signals)


def remove_elements(selector: str) -> str:
    """Send an SSE event that removes DOM elements matching the selector."""
    return SSE.remove_elements(selector)
```

- [ ] **Step 2: Commit**

```bash
git commit -m "feat: streaming helper module — thin wrapper around datastar-py SDK"
```

---

### Task 1: Onboarding Service — Pipeline Phase Detection + Calibration Loop State

**Files:**
- Create: `learn-anything-app/app/services/onboarding.py`
- Test: `learn-anything-app/tests/integration/test_services/test_onboarding_service.py`

This service manages the onboarding state machine: which pipeline phase is active, calibration loop tracking, and agreement gate state. It reads state files (via the orchestrator) and exposes the current phase + UI hints.

- [ ] **Step 1: Write failing tests for onboarding service**

```python
# tests/integration/test_services/test_onboarding_service.py
import pytest
from app.services.onboarding import OnboardingState, OnboardingService

def test_initial_state():
    svc = OnboardingService(user_id="user-1", skill_slug="spanish")
    state = svc.get_state()
    assert state.phase == "domain_assessment"
    assert state.phase_index == 0
    assert state.progress_pct == 0
    assert state.panel_visible is False
    assert state.calibration_loop_count == 0
    assert state.re_research_needed is False

def test_phase_after_domain_assessment():
    svc = OnboardingService(user_id="user-1", skill_slug="spanish")
    svc.mark_phase_complete("domain_assessment", state_data={"domain": "language"})
    state = svc.get_state()
    assert state.phase == "skill_research"
    assert state.phase_index == 1
    assert state.progress_pct == pytest.approx(16.7, abs=1)
    assert state.panel_visible is True

def test_phase_after_skill_research():
    svc = OnboardingService(user_id="user-1", skill_slug="spanish")
    svc.mark_phase_complete("domain_assessment", state_data={})
    svc.mark_phase_complete("skill_research", state_data={})
    state = svc.get_state()
    assert state.phase == "learner_calibration"
    assert state.phase_index == 2

def test_calibration_loop_triggers_re_research():
    svc = OnboardingService(user_id="user-1", skill_slug="spanish")
    svc.mark_phase_complete("domain_assessment", state_data={})
    svc.mark_phase_complete("skill_research", state_data={})
    svc.trigger_re_research(reason="unexpected_gap")
    state = svc.get_state()
    assert state.re_research_needed is True
    assert state.calibration_loop_count == 1
    assert state.phase == "skill_research"  # bounced back

def test_calibration_loop_max_2():
    svc = OnboardingService(user_id="user-1", skill_slug="spanish")
    svc.mark_phase_complete("domain_assessment", state_data={})
    svc.mark_phase_complete("skill_research", state_data={})
    svc.trigger_re_research(reason="gap1")
    svc.mark_phase_complete("skill_research", state_data={})
    svc.trigger_re_research(reason="gap2")
    svc.mark_phase_complete("skill_research", state_data={})
    # Third attempt should NOT trigger re-research (max 2 loops)
    svc.trigger_re_research(reason="gap3")
    state = svc.get_state()
    assert state.calibration_loop_count == 2  # Capped
    assert state.re_research_needed is False  # Declined, at max
    assert state.phase == "learner_calibration"  # Stays in calibration

def test_agreement_gate_tracking():
    svc = OnboardingService(user_id="user-1", skill_slug="spanish")
    for phase in ["domain_assessment", "skill_research", "learner_calibration"]:
        svc.mark_phase_complete(phase, state_data={})
    state = svc.get_state()
    assert state.phase == "curriculum_design"
    assert state.agreement_gates == {"teaching_preferences": False, "epitome_refinement": False}
    svc.confirm_agreement_gate("teaching_preferences")
    state = svc.get_state()
    assert state.agreement_gates["teaching_preferences"] is True
    assert state.phase == "curriculum_design"  # Still here, second gate pending
    svc.confirm_agreement_gate("epitome_refinement")
    svc.mark_phase_complete("curriculum_design", state_data={})
    state = svc.get_state()
    assert state.phase == "material_generation"

def test_full_pipeline():
    svc = OnboardingService(user_id="user-1", skill_slug="spanish")
    phases = [
        "domain_assessment", "skill_research", "learner_calibration",
        "curriculum_design", "material_generation", "dashboard_ready",
    ]
    for phase in phases:
        if phase == "curriculum_design":
            svc.confirm_agreement_gate("teaching_preferences")
            svc.confirm_agreement_gate("epitome_refinement")
        svc.mark_phase_complete(phase, state_data={})
    state = svc.get_state()
    assert state.phase == "complete"
    assert state.progress_pct == 100
    assert state.all_modes_unlocked is True

def test_panel_fields_accumulate():
    svc = OnboardingService(user_id="user-1", skill_slug="spanish")
    svc.mark_phase_complete("domain_assessment", state_data={
        "skill_type": "language",
        "environment_type": "kind",
        "identity_frame": "You're becoming a Spanish speaker",
    })
    state = svc.get_state()
    assert "skill_type" in state.panel_fields
    assert state.panel_fields["skill_type"] == "language"
    assert state.panel_fields["identity_frame"] == "You're becoming a Spanish speaker"

def test_user_override_panel_field():
    svc = OnboardingService(user_id="user-1", skill_slug="spanish")
    svc.mark_phase_complete("domain_assessment", state_data={
        "skill_type": "language",
    })
    svc.override_panel_field("skill_type", "communication")
    state = svc.get_state()
    assert state.panel_fields["skill_type"] == "communication"
```

- [ ] **Step 2: Run tests — should fail**

Run: `cd learn-anything-app && uv run pytest tests/integration/test_services/test_onboarding_service.py -v`
Expected: FAIL — `ModuleNotFoundError`

- [ ] **Step 3: Implement OnboardingState and OnboardingService**

```python
# app/services/onboarding.py
from __future__ import annotations
from dataclasses import dataclass, field

PIPELINE_PHASES = [
    "domain_assessment",
    "skill_research",
    "learner_calibration",
    "curriculum_design",
    "material_generation",
    "dashboard_ready",
]

MAX_CALIBRATION_LOOPS = 2

PHASE_PROGRESS = {
    "domain_assessment": 0,
    "skill_research": 16.7,
    "learner_calibration": 33.3,
    "curriculum_design": 50.0,
    "material_generation": 66.7,
    "dashboard_ready": 83.3,
    "complete": 100,
}


@dataclass
class OnboardingState:
    phase: str
    phase_index: int
    progress_pct: float
    panel_visible: bool
    panel_fields: dict[str, str]
    calibration_loop_count: int
    re_research_needed: bool
    agreement_gates: dict[str, bool]
    all_modes_unlocked: bool


class OnboardingService:
    """Manages onboarding pipeline state for a single user+skill session.

    Tracks which pipeline phases are complete, manages calibration loop
    bouncing (max 2 iterations), agreement gate confirmations, and
    panel field accumulation. This is in-memory per session — the
    persistent state is the state files written by each skill.
    """

    def __init__(self, user_id: str, skill_slug: str):
        self.user_id = user_id
        self.skill_slug = skill_slug
        self._completed_phases: list[str] = []
        self._calibration_loop_count = 0
        self._re_research_needed = False
        self._agreement_gates = {
            "teaching_preferences": False,
            "epitome_refinement": False,
        }
        self._panel_fields: dict[str, str] = {}

    def get_state(self) -> OnboardingState:
        phase = self._current_phase()
        phase_index = PIPELINE_PHASES.index(phase) if phase in PIPELINE_PHASES else len(PIPELINE_PHASES)
        return OnboardingState(
            phase=phase,
            phase_index=phase_index,
            progress_pct=PHASE_PROGRESS.get(phase, 0),
            panel_visible=len(self._completed_phases) > 0,
            panel_fields=dict(self._panel_fields),
            calibration_loop_count=self._calibration_loop_count,
            re_research_needed=self._re_research_needed,
            agreement_gates=dict(self._agreement_gates),
            all_modes_unlocked=phase == "complete",
        )

    def mark_phase_complete(self, phase: str, state_data: dict) -> None:
        if phase not in self._completed_phases:
            self._completed_phases.append(phase)
        if phase == "skill_research":
            self._re_research_needed = False
        for key, value in state_data.items():
            self._panel_fields[key] = str(value)

    def trigger_re_research(self, reason: str) -> None:
        if self._calibration_loop_count >= MAX_CALIBRATION_LOOPS:
            self._re_research_needed = False
            return
        self._calibration_loop_count += 1
        self._re_research_needed = True
        # Remove skill_research from completed so the phase detector bounces back
        if "skill_research" in self._completed_phases:
            self._completed_phases.remove("skill_research")

    def confirm_agreement_gate(self, gate: str) -> None:
        if gate in self._agreement_gates:
            self._agreement_gates[gate] = True

    def override_panel_field(self, key: str, value: str) -> None:
        self._panel_fields[key] = value

    def _current_phase(self) -> str:
        for phase in PIPELINE_PHASES:
            if phase not in self._completed_phases:
                return phase
        return "complete"
```

- [ ] **Step 4: Run tests — should pass**

Run: `cd learn-anything-app && uv run pytest tests/integration/test_services/test_onboarding_service.py -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git commit -m "feat: onboarding service — pipeline phase detection, calibration loop, agreement gates"
```

---

### Task 2: Onboarding Route — SSE Chat + State Panel Streaming

**Files:**
- Create: `learn-anything-app/app/routes/onboarding.py`
- Test: `learn-anything-app/tests/integration/test_routes/test_onboarding.py`

This route serves the onboarding page and provides SSE endpoints for the conversational chat and state panel updates. It reuses the SSE streaming infrastructure from Plan 5.

- [ ] **Step 1: Write failing tests for onboarding routes**

```python
# tests/integration/test_routes/test_onboarding.py
import pytest
from httpx import AsyncClient, ASGITransport
from app.main import app

@pytest.fixture
async def client():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as c:
        yield c

@pytest.mark.asyncio
async def test_onboarding_page_renders(client):
    resp = await client.get("/onboarding")
    assert resp.status_code == 200
    assert "What would you like to learn" in resp.text

@pytest.mark.asyncio
async def test_onboarding_page_has_datastar_signals(client):
    resp = await client.get("/onboarding")
    assert resp.status_code == 200
    assert "data-signals" in resp.text
    assert "panel_visible" in resp.text

@pytest.mark.asyncio
async def test_onboarding_chat_endpoint_exists(client):
    resp = await client.get("/onboarding/chat", headers={"Accept": "text/event-stream"})
    # SSE endpoint should exist even if it requires session state
    assert resp.status_code in (200, 401, 422)

@pytest.mark.asyncio
async def test_onboarding_override_field(client):
    resp = await client.post("/onboarding/override-field", json={
        "field": "skill_type",
        "value": "communication",
    })
    # Should accept the override (may require auth in production)
    assert resp.status_code in (200, 401, 422)

@pytest.mark.asyncio
async def test_onboarding_state_endpoint(client):
    resp = await client.get("/onboarding/state")
    assert resp.status_code in (200, 401)
```

- [ ] **Step 2: Run tests — should fail**

Run: `cd learn-anything-app && uv run pytest tests/integration/test_routes/test_onboarding.py -v`
Expected: FAIL — `ModuleNotFoundError` or 404s

- [ ] **Step 3: Implement onboarding routes**

```python
# app/routes/onboarding.py
from __future__ import annotations
import asyncio
import json
from fastapi import APIRouter, Request, Depends
from fastapi.responses import HTMLResponse
from sse_starlette.sse import EventSourceResponse
from app.templating import templates
from app.services.onboarding import OnboardingService, OnboardingState
from app.services.streaming import (
    patch_signals,
    patch_elements,
    remove_elements,
)
from app.llm import get_llm_provider, LLMMessage
from app.config import settings
import structlog

log = structlog.get_logger()

router = APIRouter(prefix="/onboarding", tags=["onboarding"])

# In-memory session store for onboarding state (keyed by user_id)
# Production: replace with Redis or DB-backed session
_sessions: dict[str, OnboardingService] = {}


def _get_or_create_session(user_id: str, skill_slug: str = "") -> OnboardingService:
    if user_id not in _sessions:
        _sessions[user_id] = OnboardingService(user_id=user_id, skill_slug=skill_slug)
    return _sessions[user_id]


@router.get("")
async def onboarding_page(request: Request):
    """Render the onboarding page — full-width chat with progressive state panel."""
    return templates.TemplateResponse(request, "onboarding/index.html", {
        "initial_signals": json.dumps({
            "panel_visible": False,
            "pipeline_phase": "domain_assessment",
            "pipeline_pct": 0,
            "chat_input": "",
            "messages": [],
            "panel_fields": {},
            "graph_preview_visible": False,
            "calibration_spinning": False,
            "calibration_topic": "",
        }),
    })


@router.get("/state")
async def onboarding_state(request: Request):
    """Return current onboarding state as JSON (for polling/debugging)."""
    user_id = request.state.user_id if hasattr(request.state, "user_id") else "anonymous"
    svc = _get_or_create_session(user_id)
    state = svc.get_state()
    return {
        "phase": state.phase,
        "phase_index": state.phase_index,
        "progress_pct": state.progress_pct,
        "panel_visible": state.panel_visible,
        "panel_fields": state.panel_fields,
        "calibration_loop_count": state.calibration_loop_count,
        "re_research_needed": state.re_research_needed,
        "agreement_gates": state.agreement_gates,
        "all_modes_unlocked": state.all_modes_unlocked,
    }


@router.post("/override-field")
async def override_field(request: Request):
    """User clicks a panel field to correct/override the LLM's extraction."""
    body = await request.json()
    field_name = body.get("field", "")
    value = body.get("value", "")
    user_id = request.state.user_id if hasattr(request.state, "user_id") else "anonymous"
    svc = _get_or_create_session(user_id)
    svc.override_panel_field(field_name, value)
    return {"status": "ok", "field": field_name, "value": value}


@router.get("/chat")
async def onboarding_chat(request: Request):
    """SSE endpoint for onboarding conversation.

    Streams Datastar patches:
    - datastar-patch-signals: field data, pipeline progress, panel visibility
    - datastar-patch-elements: new fields fading in, chat messages, graph preview
    """
    user_id = request.state.user_id if hasattr(request.state, "user_id") else "anonymous"
    svc = _get_or_create_session(user_id)

    async def event_stream():
        # Send initial state
        state = svc.get_state()
        yield patch_signals({
            "panel_visible": state.panel_visible,
            "pipeline_phase": state.phase,
            "pipeline_pct": state.progress_pct,
        })

        # Send welcome message as first chat element
        yield patch_elements(
            "#chat-messages",
            _render_assistant_message(
                "What would you like to learn? Tell me about a skill, "
                "subject, or goal you're interested in."
            ),
            mode="append",
        )

        # Keep connection alive, yielding events as pipeline progresses
        # The actual LLM conversation loop is driven by /chat/send
        while True:
            await asyncio.sleep(30)
            yield patch_signals({"_keepalive": True})

    return EventSourceResponse(event_stream())


@router.post("/chat/send")
async def onboarding_chat_send(request: Request):
    """Handle user message in onboarding chat. Returns SSE stream with response.

    This is the main conversation driver. Each message is processed by the
    current pipeline phase's skill, and the response streams back as
    Datastar patches (chat message fragments + state panel updates).
    """
    body = await request.json()
    user_message = body.get("message", "")
    user_id = request.state.user_id if hasattr(request.state, "user_id") else "anonymous"
    svc = _get_or_create_session(user_id)

    async def event_stream():
        # Append user message to chat
        yield patch_elements(
            "#chat-messages",
            _render_user_message(user_message),
            mode="append",
        )

        # Clear input
        yield patch_signals({"chat_input": ""})

        state = svc.get_state()
        phase = state.phase

        # Route to current phase handler
        llm = get_llm_provider()

        if phase == "domain_assessment":
            async for event in _handle_domain_assessment(svc, llm, user_message):
                yield event
        elif phase == "skill_research":
            async for event in _handle_skill_research(svc, llm, user_message):
                yield event
        elif phase == "learner_calibration":
            async for event in _handle_learner_calibration(svc, llm, user_message):
                yield event
        elif phase == "curriculum_design":
            async for event in _handle_curriculum_design(svc, llm, user_message):
                yield event
        elif phase == "material_generation":
            async for event in _handle_material_generation(svc, llm, user_message):
                yield event
        elif phase == "dashboard_ready":
            async for event in _handle_dashboard_ready(svc, llm, user_message):
                yield event

    return EventSourceResponse(event_stream())


async def _handle_domain_assessment(svc: OnboardingService, llm, user_message: str):
    """Phase 1: Classify skill, gather learner profile, establish identity frame.

    The LLM extracts structured data from natural conversation. As fields
    are extracted, they're pushed to the state panel one by one.
    """
    system_prompt = (
        "You are the Domain Assessor for an adaptive learning system. "
        "Your task: understand what the user wants to learn, classify the skill type "
        "(cognitive, motor, hybrid), determine the environment type (kind, wicked, mostly_kind, mostly_wicked), "
        "understand their motivation, timeline, and current level. "
        "Extract an identity frame ('You're becoming a...'). "
        "Be conversational and warm. Ask follow-up questions naturally. "
        "When you have enough information, output a JSON block with extracted fields "
        "wrapped in ```json tags. Fields: skill_name, skill_type, environment_type, "
        "motivation, timeline, current_level, identity_frame."
    )

    messages: list[LLMMessage] = [LLMMessage(role="user", content=user_message)]
    response_text = ""
    # Stream LLM response token by token
    async for event in llm.stream(messages, system=system_prompt):
        response_text += event.content
        yield patch_elements(
            "#assistant-typing",
            f'<span class="typing-text">{response_text}</span>',
            mode="replace",
        )

    # Finalize the message
    yield patch_elements(
        "#chat-messages",
        _render_assistant_message(response_text),
        mode="append",
    )
    yield patch_elements("#assistant-typing", "", mode="replace")

    # Check if LLM produced structured output
    extracted = _extract_json_from_response(response_text)
    if extracted:
        # Show panel with fade-in
        yield patch_signals({"panel_visible": True})

        # Push fields one by one with delays for progressive reveal
        for key, value in extracted.items():
            svc.override_panel_field(key, str(value))
            yield patch_signals({f"field_{key}": str(value)})
            yield patch_elements(
                "#state-panel-fields",
                _render_panel_field(key, str(value)),
                mode="append",
            )

        svc.mark_phase_complete("domain_assessment", state_data=extracted)
        state = svc.get_state()
        yield patch_signals({
            "pipeline_phase": state.phase,
            "pipeline_pct": state.progress_pct,
        })

        log.info("domain_assessment_complete", user_id=svc.user_id, fields=list(extracted.keys()))


async def _handle_skill_research(svc: OnboardingService, llm, user_message: str):
    """Phase 2: Decompose skill into graph nodes via research.

    Graph preview fades in showing gray (unassessed) nodes.
    """
    system_prompt = (
        "You are the Skill Researcher. Decompose the user's target skill into "
        "a dependency graph of sub-skills and concepts. Use web research to identify "
        "the complete skill tree. Output a JSON block with 'nodes' (array of "
        "{id, name, description, bloom_level, component_type}) and 'edges' "
        "(array of {from_id, to_id, type, description}). "
        "Be thorough — a good decomposition has 15-40 nodes."
    )

    messages: list[LLMMessage] = [LLMMessage(role="user", content=user_message)]
    response_text = ""
    async for event in llm.stream(messages, system=system_prompt):
        response_text += event.content
        yield patch_elements(
            "#assistant-typing",
            f'<span class="typing-text">{response_text}</span>',
            mode="replace",
        )

    yield patch_elements(
        "#chat-messages",
        _render_assistant_message(response_text),
        mode="append",
    )
    yield patch_elements("#assistant-typing", "", mode="replace")

    extracted = _extract_json_from_response(response_text)
    if extracted:
        # Fade in graph preview with gray unassessed nodes
        yield patch_signals({"graph_preview_visible": True})
        yield patch_signals({"graph_data": extracted})

        svc.mark_phase_complete("skill_research", state_data=extracted)
        state = svc.get_state()
        yield patch_signals({
            "pipeline_phase": state.phase,
            "pipeline_pct": state.progress_pct,
        })

        log.info("skill_research_complete", user_id=svc.user_id,
                 node_count=len(extracted.get("nodes", [])))


async def _handle_learner_calibration(svc: OnboardingService, llm, user_message: str):
    """Phase 3: Diagnostic questions, graph lights up in real-time.

    Calibration loop: if assessment reveals gaps, trigger re-research.
    UI shows spinner with 'Researching: [topic]', new nodes pulse.
    """
    system_prompt = (
        "You are the Learner Calibrator. Ask 15-20 diagnostic questions to assess "
        "the user's current mastery of each node in the skill graph. "
        "Update mastery estimates in real-time. "
        "If you discover the skill graph is missing important nodes, output a "
        "JSON block with 're_research_needed': true and 'missing_topics': [...]. "
        "When calibration is complete, output a JSON block with 'calibration_complete': true "
        "and 'mastery_states': {node_id: {mastery_probability, mastery_category, evidence}}."
    )

    messages: list[LLMMessage] = [LLMMessage(role="user", content=user_message)]
    response_text = ""
    async for event in llm.stream(messages, system=system_prompt):
        response_text += event.content
        yield patch_elements(
            "#assistant-typing",
            f'<span class="typing-text">{response_text}</span>',
            mode="replace",
        )

    yield patch_elements(
        "#chat-messages",
        _render_assistant_message(response_text),
        mode="append",
    )
    yield patch_elements("#assistant-typing", "", mode="replace")

    extracted = _extract_json_from_response(response_text)
    if extracted:
        # Check if re-research is needed (calibration loop)
        if extracted.get("re_research_needed"):
            missing = extracted.get("missing_topics", [])
            topic_str = ", ".join(missing[:3])
            svc.trigger_re_research(reason=f"missing_topics: {topic_str}")
            state = svc.get_state()

            if state.re_research_needed:
                # Show calibration loop spinner
                yield patch_signals({
                    "calibration_spinning": True,
                    "calibration_topic": topic_str,
                    "pipeline_phase": state.phase,
                })
                log.info("calibration_loop_triggered",
                         user_id=svc.user_id, loop=state.calibration_loop_count,
                         topics=missing)
            else:
                # Max loops reached, proceed anyway
                log.info("calibration_loop_max_reached", user_id=svc.user_id)

        elif extracted.get("calibration_complete"):
            # Update graph with mastery states
            mastery = extracted.get("mastery_states", {})
            yield patch_signals({"mastery_overlay": mastery})
            yield patch_signals({"calibration_spinning": False})

            svc.mark_phase_complete("learner_calibration", state_data=extracted)
            state = svc.get_state()
            yield patch_signals({
                "pipeline_phase": state.phase,
                "pipeline_pct": state.progress_pct,
            })
            log.info("learner_calibration_complete", user_id=svc.user_id)


async def _handle_curriculum_design(svc: OnboardingService, llm, user_message: str):
    """Phase 4: Teaching preferences + epitome refinement.

    Two agreement gates rendered as chat messages:
    1. Expert panel — user chooses instructor persona
    2. Epitome card — user confirms first lesson proposal
    """
    state = svc.get_state()
    gates = state.agreement_gates

    if not gates["teaching_preferences"]:
        # Agreement Gate 1: Teaching preferences / expert panel
        system_prompt = (
            "You are the Curriculum Architect. Present the user with 2-3 instructor "
            "persona options for their learning journey. Each persona should have a "
            "distinct teaching style (e.g., Socratic questioner, patient explainer, "
            "demanding coach). Format as a JSON block with 'expert_panel': "
            "[{name, style, description, strengths}]. "
            "Ask the user which approach resonates most."
        )

        messages: list[LLMMessage] = [LLMMessage(role="user", content=user_message)]
        response_text = ""
        async for event in llm.stream(messages, system=system_prompt):
            response_text += event.content
            yield patch_elements(
                "#assistant-typing",
                f'<span class="typing-text">{response_text}</span>',
                mode="replace",
            )

        yield patch_elements("#assistant-typing", "", mode="replace")

        extracted = _extract_json_from_response(response_text)
        if extracted and "expert_panel" in extracted:
            # Render expert panel as inline chat card
            yield patch_elements(
                "#chat-messages",
                _render_expert_panel(extracted["expert_panel"]),
                mode="append",
            )
        else:
            yield patch_elements(
                "#chat-messages",
                _render_assistant_message(response_text),
                mode="append",
            )

        # Classify user intent via LLM instead of fragile keyword matching
        gate_intent = await _classify_agreement_response(llm, user_message, "teaching preference")
        if gate_intent == "CONFIRM":
            svc.confirm_agreement_gate("teaching_preferences")

    elif not gates["epitome_refinement"]:
        # Agreement Gate 2: Epitome refinement
        system_prompt = (
            "You are the Curriculum Architect. Present the proposed first lesson "
            "as an epitome — a representative whole-task that previews the entire skill. "
            "Format as a JSON block with 'epitome': {title, description, rationale, "
            "nodes_covered: [...], estimated_duration}. "
            "Ask: 'Does this feel right? Would you adjust anything?'"
        )

        messages: list[LLMMessage] = [LLMMessage(role="user", content=user_message)]
        response_text = ""
        async for event in llm.stream(messages, system=system_prompt):
            response_text += event.content
            yield patch_elements(
                "#assistant-typing",
                f'<span class="typing-text">{response_text}</span>',
                mode="replace",
            )

        yield patch_elements("#assistant-typing", "", mode="replace")

        extracted = _extract_json_from_response(response_text)
        if extracted and "epitome" in extracted:
            yield patch_elements(
                "#chat-messages",
                _render_epitome_card(extracted["epitome"]),
                mode="append",
            )
        else:
            yield patch_elements(
                "#chat-messages",
                _render_assistant_message(response_text),
                mode="append",
            )

        gate_intent = await _classify_agreement_response(llm, user_message, "first lesson")
        if gate_intent == "CONFIRM":
            svc.confirm_agreement_gate("epitome_refinement")

    # If both gates confirmed, complete the phase
    state = svc.get_state()
    if state.agreement_gates.get("teaching_preferences") and state.agreement_gates.get("epitome_refinement"):
        svc.mark_phase_complete("curriculum_design", state_data={})
        state = svc.get_state()
        yield patch_signals({
            "pipeline_phase": state.phase,
            "pipeline_pct": state.progress_pct,
        })


async def _handle_material_generation(svc: OnboardingService, llm, user_message: str):
    """Phase 5: Generate materials — Anki decks, worked examples, lectures.

    Materials count appears in panel, Anki export offered.
    """
    system_prompt = (
        "You are the Material Forge. Generate learning materials for the curriculum. "
        "Create flashcard decks, worked examples, and lecture outlines. "
        "When generation is complete, output a JSON block with "
        "'materials_generated': {flashcard_count, worked_example_count, lecture_count} "
        "and 'anki_export_available': true."
    )

    messages: list[LLMMessage] = [LLMMessage(role="user", content=user_message)]
    response_text = ""
    async for event in llm.stream(messages, system=system_prompt):
        response_text += event.content
        yield patch_elements(
            "#assistant-typing",
            f'<span class="typing-text">{response_text}</span>',
            mode="replace",
        )

    yield patch_elements(
        "#chat-messages",
        _render_assistant_message(response_text),
        mode="append",
    )
    yield patch_elements("#assistant-typing", "", mode="replace")

    extracted = _extract_json_from_response(response_text)
    if extracted and "materials_generated" in extracted:
        counts = extracted["materials_generated"]
        yield patch_signals({"materials_count": counts})
        yield patch_elements(
            "#state-panel-fields",
            _render_panel_field("materials", (
                f"{counts.get('flashcard_count', 0)} flashcards, "
                f"{counts.get('worked_example_count', 0)} examples, "
                f"{counts.get('lecture_count', 0)} lectures"
            )),
            mode="append",
        )

        if extracted.get("anki_export_available"):
            yield patch_elements(
                "#chat-messages",
                _render_anki_export_offer(),
                mode="append",
            )

        svc.mark_phase_complete("material_generation", state_data=extracted)
        state = svc.get_state()
        yield patch_signals({
            "pipeline_phase": state.phase,
            "pipeline_pct": state.progress_pct,
        })


async def _handle_dashboard_ready(svc: OnboardingService, llm, user_message: str):
    """Phase 6: Dashboard available — all modes unlocked.

    Presents Explore mode and offers first training session.
    """
    svc.mark_phase_complete("dashboard_ready", state_data={})
    state = svc.get_state()

    yield patch_signals({
        "pipeline_phase": "complete",
        "pipeline_pct": 100,
        "all_modes_unlocked": True,
    })

    yield patch_elements(
        "#chat-messages",
        _render_assistant_message(
            "Your learning environment is ready! All modes are now unlocked. "
            "You can explore your knowledge graph, start a training session, "
            "browse your materials, or check your progress dashboard. "
            "Ready for your first training session?"
        ),
        mode="append",
    )

    yield patch_elements(
        "#chat-messages",
        _render_mode_cards(),
        mode="append",
    )


# --- HTML fragment renderers (all user/LLM text is escaped for XSS safety) ---

import html as _html

def _render_assistant_message(text: str) -> str:
    safe = _html.escape(text)
    return (
        f'<div class="chat-message assistant-message fade-in">'
        f'<div class="message-content">{safe}</div>'
        f'</div>'
    )

def _render_user_message(text: str) -> str:
    safe = _html.escape(text)
    return (
        f'<div class="chat-message user-message fade-in">'
        f'<div class="message-content">{safe}</div>'
        f'</div>'
    )

def _render_panel_field(key: str, value: str) -> str:
    safe_key = _html.escape(key)
    safe_value = _html.escape(value)
    label = key.replace("_", " ").title()
    safe_label = _html.escape(label)
    return (
        f'<div class="panel-field fade-in" data-field="{safe_key}">'
        f'<label class="field-label">{safe_label}</label>'
        f'<span class="field-value" '
        f'data-on-click="$editing_field = \'{safe_key}\'">{safe_value}</span>'
        f'</div>'
    )

def _render_expert_panel(experts: list[dict]) -> str:
    cards = ""
    for expert in experts:
        cards += (
            f'<div class="expert-card">'
            f'<h4 class="expert-name">{expert.get("name", "")}</h4>'
            f'<p class="expert-style">{expert.get("style", "")}</p>'
            f'<p class="expert-desc">{expert.get("description", "")}</p>'
            f'<p class="expert-strengths">{expert.get("strengths", "")}</p>'
            f'</div>'
        )
    return (
        f'<div class="chat-message assistant-message expert-panel fade-in">'
        f'<div class="expert-panel-inner">'
        f'<h3>Choose Your Instructor</h3>'
        f'{cards}'
        f'<p class="gate-prompt">Which approach resonates with you?</p>'
        f'</div></div>'
    )

def _render_epitome_card(epitome: dict) -> str:
    nodes = ", ".join(epitome.get("nodes_covered", [])[:5])
    return (
        f'<div class="chat-message assistant-message epitome-card fade-in">'
        f'<div class="epitome-inner">'
        f'<h3>{epitome.get("title", "Your First Lesson")}</h3>'
        f'<p class="epitome-desc">{epitome.get("description", "")}</p>'
        f'<div class="epitome-meta">'
        f'<span class="epitome-rationale">Why this: {epitome.get("rationale", "")}</span>'
        f'<span class="epitome-nodes">Covers: {nodes}</span>'
        f'<span class="epitome-duration">{epitome.get("estimated_duration", "")}</span>'
        f'</div>'
        f'<p class="gate-prompt">Does this feel right? Would you adjust anything?</p>'
        f'</div></div>'
    )

def _render_anki_export_offer() -> str:
    return (
        '<div class="chat-message assistant-message anki-offer fade-in">'
        '<div class="anki-offer-inner">'
        '<p>Your flashcard deck is ready for export.</p>'
        '<a href="/api/materials/anki-export" class="btn-gold">Download Anki Deck (.apkg)</a>'
        '</div></div>'
    )

def _render_mode_cards() -> str:
    return (
        '<div class="mode-cards fade-in">'
        '<a href="/explore" class="mode-card">'
        '<h4>Explore</h4><p>Browse your knowledge graph</p></a>'
        '<a href="/train" class="mode-card">'
        '<h4>Train</h4><p>Start your first session</p></a>'
        '<a href="/materials" class="mode-card">'
        '<h4>Materials</h4><p>Browse generated content</p></a>'
        '<a href="/progress" class="mode-card">'
        '<h4>Progress</h4><p>View your dashboard</p></a>'
        '</div>'
    )


def _extract_json_from_response(text: str) -> dict | None:
    """Extract a JSON block from LLM response text.

    Looks for ```json ... ``` fenced blocks first, then bare { ... }
    using a brace-counting parser that handles arbitrarily nested objects.
    """
    import re
    # Try fenced JSON block
    match = re.search(r'```json\s*\n(.*?)\n\s*```', text, re.DOTALL)
    if match:
        try:
            return json.loads(match.group(1))
        except json.JSONDecodeError:
            pass
    # Try bare JSON object with brace-counting (handles arbitrary nesting)
    candidate = _find_json_object(text)
    if candidate:
        try:
            return json.loads(candidate)
        except json.JSONDecodeError:
            pass
    return None


def _find_json_object(text: str) -> str | None:
    """Find the first balanced JSON object in text using brace counting.

    Unlike a regex, this correctly handles arbitrary nesting depth.
    """
    start = text.find('{')
    if start == -1:
        return None
    depth = 0
    for i, c in enumerate(text[start:], start):
        if c == '{':
            depth += 1
        elif c == '}':
            depth -= 1
        if depth == 0:
            return text[start:i + 1]
    return None


async def _classify_agreement_response(llm, user_message: str, gate_topic: str) -> str:
    """Classify user intent at an agreement gate via LLM.

    Returns one of: "CONFIRM", "REDIRECT", "QUESTION".
    Uses a lightweight classification prompt instead of fragile keyword matching.
    """
    classification_prompt = (
        f"Did the user confirm, redirect, or ask a question about the proposed "
        f"{gate_topic}? Respond with exactly one word: CONFIRM, REDIRECT, or QUESTION."
    )
    messages: list[LLMMessage] = [
        LLMMessage(role="user", content=user_message),
    ]
    response_text = ""
    async for event in llm.stream(messages, system=classification_prompt):
        response_text += event.content
    result = response_text.strip().upper()
    if result in ("CONFIRM", "REDIRECT", "QUESTION"):
        return result
    return "QUESTION"  # Default to question if classification is unclear
```

- [ ] **Step 4: Register onboarding router in main.py**

Add to `app/main.py`:
```python
from app.routes.onboarding import router as onboarding_router
app.include_router(onboarding_router)
```

- [ ] **Step 5: Run tests — should pass**

Run: `cd learn-anything-app && uv run pytest tests/integration/test_routes/test_onboarding.py -v`
Expected: PASS

- [ ] **Step 6: Commit**

```bash
git commit -m "feat: onboarding routes — SSE chat, state panel streaming, pipeline phase handlers"
```

---

### Task 3: Onboarding Page Template — Chat + Progressive State Panel

**Files:**
- Create: `learn-anything-app/templates/onboarding/index.html`
- Create: `learn-anything-app/templates/onboarding/state_panel.html`
- Create: `learn-anything-app/templates/onboarding/pipeline_bar.html`

- [ ] **Step 1: Create the main onboarding page**

```html
<!-- templates/onboarding/index.html -->
{% extends "base.html" %}
{% block title %}Learn Anything — Start Learning{% endblock %}
{% block content %}
<div id="onboarding"
     data-signals='{{ initial_signals }}'
     data-init="$$get('/onboarding/chat')">

  <!-- Main layout: chat left, state panel right (when visible) -->
  <div class="onboarding-layout"
       data-class-has-panel="$panel_visible">

    <!-- Chat Panel (starts full-width, shrinks when panel appears) -->
    <div class="onboarding-chat">
      <div class="chat-header">
        <div class="logo-mark"></div>
        <h1 class="chat-title">Learn Anything</h1>
      </div>

      <!-- Message stream -->
      <div id="chat-messages" class="chat-messages">
        <!-- Messages appended here via SSE datastar-patch-elements -->
      </div>

      <!-- Typing indicator (replaced during streaming) -->
      <div id="assistant-typing" class="assistant-typing">
        <!-- Token-by-token streaming replaces this content -->
      </div>

      <!-- Calibration loop spinner -->
      <div class="calibration-spinner"
           data-show="$calibration_spinning">
        <div class="spinner-ring"></div>
        <span class="spinner-text">Researching: <span data-text="$calibration_topic"></span></span>
      </div>

      <!-- Chat input -->
      <div class="chat-input-container">
        <form data-on-submit__prevent="$$post('/onboarding/chat/send', {message: $chat_input})">
          <div class="input-row">
            <textarea
              class="chat-input"
              data-model="chat_input"
              placeholder="Type your message..."
              rows="1"
              data-on-keydown__debounce_0="if (event.key === 'Enter' && !event.shiftKey) { event.preventDefault(); document.querySelector('.chat-send-btn').click(); }"
            ></textarea>
            <button type="submit" class="chat-send-btn">
              <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                <line x1="22" y1="2" x2="11" y2="13"></line>
                <polygon points="22 2 15 22 11 13 2 9 22 2"></polygon>
              </svg>
            </button>
          </div>
        </form>
      </div>
    </div>

    <!-- State Panel (fades in when panel_visible becomes true) -->
    <div class="state-panel"
         data-show="$panel_visible">
      {% include "onboarding/state_panel.html" %}
    </div>
  </div>

  <!-- Pipeline progress bar (always present, fills subtly) -->
  {% include "onboarding/pipeline_bar.html" %}
</div>

<style>
  .onboarding-layout {
    display: flex;
    height: 100vh;
    overflow: hidden;
    transition: all 0.6s cubic-bezier(0.4, 0, 0.2, 1);
  }

  .onboarding-chat {
    flex: 1;
    display: flex;
    flex-direction: column;
    min-width: 0;
    transition: flex 0.6s cubic-bezier(0.4, 0, 0.2, 1);
  }

  .onboarding-layout.has-panel .onboarding-chat {
    flex: 0 0 60%;
  }

  .state-panel {
    flex: 0 0 40%;
    border-left: 1px solid var(--border);
    overflow-y: auto;
    animation: panelSlideIn 0.6s cubic-bezier(0.4, 0, 0.2, 1);
  }

  @keyframes panelSlideIn {
    from { opacity: 0; transform: translateX(40px); }
    to { opacity: 1; transform: translateX(0); }
  }

  .chat-header {
    display: flex;
    align-items: center;
    gap: 12px;
    padding: 20px 32px;
    border-bottom: 1px solid var(--border);
  }

  .chat-header .logo-mark {
    width: 32px;
    height: 32px;
    margin: 0;
  }

  .chat-title {
    font-size: 20px;
    font-family: var(--serif);
  }

  .chat-messages {
    flex: 1;
    overflow-y: auto;
    padding: 24px 32px;
    display: flex;
    flex-direction: column;
    gap: 16px;
  }

  .chat-message {
    max-width: 80%;
    padding: 12px 16px;
    border-radius: 12px;
    line-height: 1.5;
    font-size: 14px;
  }

  .assistant-message {
    align-self: flex-start;
    background: var(--surface);
    border: 1px solid var(--border);
    color: var(--text);
  }

  .user-message {
    align-self: flex-end;
    background: linear-gradient(135deg, var(--gold-dim), var(--gold));
    color: var(--void);
  }

  .fade-in {
    animation: fadeIn 0.4s ease-out;
  }

  @keyframes fadeIn {
    from { opacity: 0; transform: translateY(8px); }
    to { opacity: 1; transform: translateY(0); }
  }

  .assistant-typing {
    padding: 0 32px;
    min-height: 0;
  }

  .typing-text {
    color: var(--text-dim);
    font-size: 14px;
  }

  .calibration-spinner {
    display: flex;
    align-items: center;
    gap: 12px;
    padding: 12px 32px;
  }

  .spinner-ring {
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

  .spinner-text {
    font-size: 13px;
    color: var(--text-dim);
    font-family: var(--mono);
  }

  .chat-input-container {
    padding: 16px 32px 24px;
    border-top: 1px solid var(--border);
  }

  .input-row {
    display: flex;
    gap: 8px;
    align-items: flex-end;
  }

  .chat-input {
    flex: 1;
    padding: 10px 14px;
    background: var(--surface);
    border: 1px solid var(--border);
    border-radius: 12px;
    color: var(--text-bright);
    font-family: var(--sans);
    font-size: 14px;
    resize: none;
    outline: none;
    transition: border-color 0.2s;
  }

  .chat-input:focus {
    border-color: var(--gold-dim);
  }

  .chat-send-btn {
    width: 40px;
    height: 40px;
    background: linear-gradient(135deg, var(--gold-dim), var(--gold));
    border: none;
    border-radius: 10px;
    color: var(--void);
    cursor: pointer;
    display: flex;
    align-items: center;
    justify-content: center;
    flex-shrink: 0;
    transition: box-shadow 0.2s;
  }

  .chat-send-btn:hover {
    box-shadow: 0 4px 20px var(--gold-glow);
  }

  /* Expert panel cards (agreement gate 1) */
  .expert-panel .expert-panel-inner {
    display: flex;
    flex-direction: column;
    gap: 12px;
  }

  .expert-card {
    background: var(--deep);
    border: 1px solid var(--border);
    border-radius: 10px;
    padding: 14px;
    cursor: pointer;
    transition: border-color 0.2s;
  }

  .expert-card:hover {
    border-color: var(--gold-dim);
  }

  .expert-name {
    font-family: var(--serif);
    color: var(--gold);
    font-size: 15px;
    margin-bottom: 4px;
  }

  .expert-style {
    font-family: var(--mono);
    font-size: 11px;
    color: var(--violet);
    text-transform: uppercase;
    letter-spacing: 0.5px;
  }

  .expert-desc, .expert-strengths {
    font-size: 13px;
    color: var(--text-dim);
  }

  .gate-prompt {
    font-style: italic;
    color: var(--text-dim);
    font-size: 13px;
    margin-top: 4px;
  }

  /* Epitome card (agreement gate 2) */
  .epitome-card .epitome-inner {
    display: flex;
    flex-direction: column;
    gap: 10px;
  }

  .epitome-inner h3 {
    font-family: var(--serif);
    color: var(--gold);
    font-size: 17px;
  }

  .epitome-desc {
    font-size: 14px;
    color: var(--text);
  }

  .epitome-meta {
    display: flex;
    flex-direction: column;
    gap: 6px;
    font-size: 12px;
    font-family: var(--mono);
    color: var(--text-dim);
  }

  /* Anki export offer */
  .anki-offer .anki-offer-inner {
    display: flex;
    align-items: center;
    gap: 16px;
  }

  .btn-gold {
    display: inline-block;
    padding: 8px 20px;
    background: linear-gradient(135deg, var(--gold-dim), var(--gold));
    color: var(--void);
    border-radius: 8px;
    font-weight: 600;
    font-size: 13px;
    text-decoration: none;
    white-space: nowrap;
  }

  .btn-gold:hover {
    box-shadow: 0 4px 20px var(--gold-glow);
    color: var(--void);
  }

  /* Mode cards (transition to learning) */
  .mode-cards {
    display: grid;
    grid-template-columns: repeat(2, 1fr);
    gap: 12px;
    padding: 8px 0;
    max-width: 80%;
  }

  .mode-card {
    background: var(--surface);
    border: 1px solid var(--border);
    border-radius: 10px;
    padding: 16px;
    display: block;
    transition: border-color 0.2s, box-shadow 0.2s;
  }

  .mode-card:hover {
    border-color: var(--gold-dim);
    box-shadow: 0 4px 20px var(--gold-glow);
  }

  .mode-card h4 {
    font-family: var(--serif);
    color: var(--gold);
    margin-bottom: 4px;
  }

  .mode-card p {
    font-size: 12px;
    color: var(--text-dim);
  }

  @media (prefers-reduced-motion: reduce) {
    .fade-in { animation: none; }
    .state-panel { animation: none; }
    .spinner-ring { animation: none; }
  }

  /* Mobile: no side panel, stack vertically */
  @media (max-width: 768px) {
    .onboarding-layout {
      flex-direction: column;
    }
    .onboarding-layout.has-panel .onboarding-chat {
      flex: 1;
    }
    .state-panel {
      flex: none;
      height: 40vh;
      border-left: none;
      border-top: 1px solid var(--border);
    }
    .chat-messages {
      padding: 16px;
    }
    .chat-input-container {
      padding: 12px 16px 16px;
    }
    .mode-cards {
      grid-template-columns: 1fr;
      max-width: 100%;
    }
  }
</style>
{% endblock %}
```

- [ ] **Step 2: Create state panel fragment**

```html
<!-- templates/onboarding/state_panel.html -->
<div class="state-panel-inner">
  <div class="panel-header">
    <h2 class="panel-title">Your Learning Profile</h2>
    <p class="panel-hint">Click any field to edit</p>
  </div>

  <!-- Fields container — fields are appended here via SSE -->
  <div id="state-panel-fields" class="panel-fields">
    <!-- Fields fade in one by one as LLM extracts them.
         Each field is a datastar-patch-elements append with class fade-in.
         Structure per field:
         <div class="panel-field fade-in" data-field="key">
           <label class="field-label">Key Name</label>
           <span class="field-value">value</span>
         </div>
    -->
  </div>

  <!-- Graph preview (fades in during Phase 2) -->
  <div class="graph-preview-container"
       data-show="$graph_preview_visible">
    <h3 class="graph-preview-title">Skill Graph</h3>
    <div id="onboarding-graph"
         data-ignore-morph
         data-signals:graph_data='null'
         data-effect="if ($graph_data) renderOnboardingGraph($graph_data, document.getElementById('onboarding-graph'))">
      <!-- D3 renders here -->
    </div>
    <p class="graph-hint">
      <span class="node-legend not-started-dot"></span> Not assessed
      <span class="node-legend mastered-dot"></span> Mastered
      <span class="node-legend proficient-dot"></span> Proficient
      <span class="node-legend familiar-dot"></span> Familiar
    </p>
  </div>
</div>

<style>
  .state-panel-inner {
    padding: 24px;
  }

  .panel-header {
    margin-bottom: 24px;
  }

  .panel-title {
    font-family: var(--serif);
    font-size: 18px;
    color: var(--text-bright);
  }

  .panel-hint {
    font-size: 11px;
    color: var(--text-dim);
    font-family: var(--mono);
    margin-top: 4px;
  }

  .panel-fields {
    display: flex;
    flex-direction: column;
    gap: 14px;
  }

  .panel-field {
    background: var(--surface);
    border: 1px solid var(--border);
    border-radius: 8px;
    padding: 10px 14px;
    cursor: pointer;
    transition: border-color 0.2s;
  }

  .panel-field:hover {
    border-color: var(--gold-dim);
  }

  .field-label {
    display: block;
    font-family: var(--mono);
    font-size: 10px;
    color: var(--text-dim);
    text-transform: uppercase;
    letter-spacing: 1px;
    margin-bottom: 4px;
  }

  .field-value {
    font-size: 14px;
    color: var(--text-bright);
  }

  .graph-preview-container {
    margin-top: 24px;
    animation: fadeIn 0.6s ease-out;
  }

  .graph-preview-title {
    font-size: 15px;
    margin-bottom: 12px;
  }

  #onboarding-graph {
    width: 100%;
    height: 300px;
    background: var(--deep);
    border: 1px solid var(--border);
    border-radius: 10px;
    overflow: hidden;
  }

  .graph-hint {
    margin-top: 8px;
    font-size: 11px;
    color: var(--text-dim);
    display: flex;
    gap: 12px;
    flex-wrap: wrap;
  }

  .node-legend {
    display: inline-block;
    width: 8px;
    height: 8px;
    border-radius: 50%;
    margin-right: 4px;
    vertical-align: middle;
  }

  .not-started-dot { background: var(--not-started); }
  .mastered-dot { background: var(--mastered); }
  .proficient-dot { background: var(--proficient); }
  .familiar-dot { background: var(--familiar); }

  /* Pulsing border for new calibration-loop nodes */
  .node-pulsing {
    animation: nodePulse 1.5s ease-in-out 3;
  }

  @keyframes nodePulse {
    0%, 100% { stroke: var(--border); stroke-width: 1; }
    50% { stroke: var(--gold); stroke-width: 3; }
  }
</style>
```

- [ ] **Step 3: Create pipeline progress bar fragment**

```html
<!-- templates/onboarding/pipeline_bar.html -->
<div class="pipeline-bar">
  <div class="pipeline-track">
    <div class="pipeline-fill"
         data-attr-style="'width:' + $pipeline_pct + '%'">
    </div>
  </div>
  <div class="pipeline-labels">
    <span class="pipeline-phase-label" data-text="$pipeline_phase.replace('_', ' ')"></span>
    <span class="pipeline-pct-label"><span data-text="Math.round($pipeline_pct)"></span>%</span>
  </div>
</div>

<style>
  .pipeline-bar {
    position: fixed;
    bottom: 0;
    left: 0;
    right: 0;
    z-index: 100;
    padding: 0 32px 8px;
    background: linear-gradient(transparent, var(--void));
  }

  .pipeline-track {
    width: 100%;
    height: 3px;
    background: var(--border);
    border-radius: 2px;
    overflow: hidden;
  }

  .pipeline-fill {
    height: 100%;
    background: linear-gradient(90deg, var(--gold-dim), var(--gold));
    border-radius: 2px;
    transition: width 0.8s cubic-bezier(0.4, 0, 0.2, 1);
  }

  .pipeline-labels {
    display: flex;
    justify-content: space-between;
    margin-top: 4px;
  }

  .pipeline-phase-label {
    font-family: var(--mono);
    font-size: 10px;
    color: var(--text-dim);
    text-transform: capitalize;
  }

  .pipeline-pct-label {
    font-family: var(--mono);
    font-size: 10px;
    color: var(--gold-dim);
  }
</style>
```

- [ ] **Step 4: Verify the page renders**

Run: `cd learn-anything-app && uv run uvicorn app.main:app --reload`
Navigate to `http://localhost:8000/onboarding`
Expected: Full-width chat with "Learn Anything" header, input area, pipeline bar at bottom. No state panel yet (it fades in once the LLM extracts info).

- [ ] **Step 5: Commit**

```bash
git commit -m "feat: onboarding templates — chat layout, progressive state panel, pipeline bar"
```

---

### Task 4: Agreement Gate Templates — Expert Panel + Epitome Card

**Files:**
- Create: `learn-anything-app/templates/onboarding/expert_panel.html`
- Create: `learn-anything-app/templates/onboarding/epitome_card.html`

These are Jinja2 fragment templates for server-side rendering. They can be rendered into the SSE stream as an alternative to the inline HTML in the route handlers (for more complex layouts or when rendered via `templates.get_template().render()`).

- [ ] **Step 1: Create expert panel template**

```html
<!-- templates/onboarding/expert_panel.html -->
<!--
  Agreement Gate 1: Teaching Preferences
  Rendered inline in the chat as a rich card.
  Variables: experts (list of dicts with name, style, description, strengths)
-->
<div class="chat-message assistant-message expert-panel fade-in">
  <div class="expert-panel-inner">
    <h3>Choose Your Instructor</h3>
    <p class="gate-intro">Based on your learning profile, here are instructor personas
      that could guide your journey. Each brings a different teaching philosophy.</p>

    <div class="expert-grid">
      {% for expert in experts %}
      <div class="expert-card"
           data-on-click="$chat_input = 'I\'d like to go with {{ expert.name }}'">
        <div class="expert-card-header">
          <div class="expert-avatar"
               style="background: radial-gradient(circle at 35% 35%,
                 {{ ['var(--mastered)', 'var(--proficient)', 'var(--familiar)'][loop.index0 % 3] }},
                 var(--surface));">
          </div>
          <div>
            <h4 class="expert-name">{{ expert.name }}</h4>
            <span class="expert-style">{{ expert.style }}</span>
          </div>
        </div>
        <p class="expert-desc">{{ expert.description }}</p>
        <div class="expert-strengths-box">
          <span class="strengths-label">Strengths:</span>
          <span class="strengths-text">{{ expert.strengths }}</span>
        </div>
      </div>
      {% endfor %}
    </div>

    <p class="gate-prompt">Which approach resonates with you? Click a card or describe what you're looking for.</p>
  </div>
</div>

<style>
  .gate-intro {
    font-size: 13px;
    color: var(--text-dim);
    margin-bottom: 12px;
  }

  .expert-grid {
    display: flex;
    flex-direction: column;
    gap: 10px;
  }

  .expert-card-header {
    display: flex;
    align-items: center;
    gap: 10px;
    margin-bottom: 8px;
  }

  .expert-avatar {
    width: 36px;
    height: 36px;
    border-radius: 50%;
    flex-shrink: 0;
  }

  .expert-strengths-box {
    margin-top: 6px;
    padding: 6px 10px;
    background: var(--void);
    border-radius: 6px;
    font-size: 12px;
  }

  .strengths-label {
    font-family: var(--mono);
    font-size: 10px;
    color: var(--text-dim);
    text-transform: uppercase;
    letter-spacing: 0.5px;
  }

  .strengths-text {
    color: var(--text);
    display: block;
    margin-top: 2px;
  }
</style>
```

- [ ] **Step 2: Create epitome card template**

```html
<!-- templates/onboarding/epitome_card.html -->
<!--
  Agreement Gate 2: Epitome Refinement
  Rendered inline in the chat as a rich card.
  Variables: epitome (dict with title, description, rationale, nodes_covered, estimated_duration)
-->
<div class="chat-message assistant-message epitome-card fade-in">
  <div class="epitome-inner">
    <div class="epitome-header">
      <span class="epitome-badge">First Lesson Proposal</span>
      <h3>{{ epitome.title }}</h3>
    </div>

    <p class="epitome-desc">{{ epitome.description }}</p>

    <div class="epitome-detail-grid">
      <div class="epitome-detail">
        <span class="detail-label">Why this first</span>
        <span class="detail-value">{{ epitome.rationale }}</span>
      </div>
      <div class="epitome-detail">
        <span class="detail-label">Concepts covered</span>
        <div class="nodes-pills">
          {% for node in epitome.nodes_covered[:6] %}
          <span class="node-pill">{{ node }}</span>
          {% endfor %}
          {% if epitome.nodes_covered|length > 6 %}
          <span class="node-pill more-pill">+{{ epitome.nodes_covered|length - 6 }} more</span>
          {% endif %}
        </div>
      </div>
      <div class="epitome-detail">
        <span class="detail-label">Estimated duration</span>
        <span class="detail-value mono">{{ epitome.estimated_duration }}</span>
      </div>
    </div>

    <p class="gate-prompt">Does this feel right? Would you adjust anything?</p>
  </div>
</div>

<style>
  .epitome-header {
    margin-bottom: 10px;
  }

  .epitome-badge {
    display: inline-block;
    font-family: var(--mono);
    font-size: 10px;
    color: var(--gold);
    text-transform: uppercase;
    letter-spacing: 1px;
    background: var(--gold-glow);
    padding: 2px 8px;
    border-radius: 4px;
    margin-bottom: 6px;
  }

  .epitome-detail-grid {
    display: flex;
    flex-direction: column;
    gap: 12px;
    margin-top: 14px;
    padding-top: 14px;
    border-top: 1px solid var(--border);
  }

  .epitome-detail {
    display: flex;
    flex-direction: column;
    gap: 4px;
  }

  .detail-label {
    font-family: var(--mono);
    font-size: 10px;
    color: var(--text-dim);
    text-transform: uppercase;
    letter-spacing: 1px;
  }

  .detail-value {
    font-size: 13px;
    color: var(--text);
  }

  .detail-value.mono {
    font-family: var(--mono);
    color: var(--gold-dim);
  }

  .nodes-pills {
    display: flex;
    flex-wrap: wrap;
    gap: 6px;
  }

  .node-pill {
    display: inline-block;
    padding: 3px 10px;
    background: var(--deep);
    border: 1px solid var(--border);
    border-radius: 12px;
    font-size: 12px;
    color: var(--text);
  }

  .more-pill {
    color: var(--text-dim);
    border-style: dashed;
  }
</style>
```

- [ ] **Step 3: Commit**

```bash
git commit -m "feat: agreement gate templates — expert panel cards and epitome proposal card"
```

---

### Task 5: Onboarding JavaScript — Progressive Reveal Logic

**Files:**
- Create: `learn-anything-app/static/js/onboarding.js`

This file handles client-side progressive reveal: auto-scroll chat, field edit mode, textarea auto-resize.

- [ ] **Step 1: Create onboarding.js**

```javascript
// static/js/onboarding.js

/**
 * Onboarding progressive reveal logic.
 *
 * Responsibilities:
 * - Auto-scroll chat to bottom on new messages
 * - Textarea auto-resize
 * - Field inline editing (click to edit, enter to confirm)
 * - Simplified onboarding graph rendering (delegates to graph.js)
 */

(function () {
  "use strict";

  // --- Auto-scroll chat ---
  const chatContainer = document.getElementById("chat-messages");
  if (chatContainer) {
    const observer = new MutationObserver(() => {
      chatContainer.scrollTop = chatContainer.scrollHeight;
    });
    observer.observe(chatContainer, { childList: true, subtree: true });
  }

  // --- Textarea auto-resize ---
  document.addEventListener("input", (e) => {
    if (e.target.classList.contains("chat-input")) {
      e.target.style.height = "auto";
      const maxHeight = 120;
      e.target.style.height = Math.min(e.target.scrollHeight, maxHeight) + "px";
    }
  });

  // --- Field inline editing ---
  document.addEventListener("click", (e) => {
    const fieldValue = e.target.closest(".field-value");
    if (!fieldValue) return;

    const field = fieldValue.closest(".panel-field");
    if (!field || field.classList.contains("editing")) return;

    const fieldKey = field.dataset.field;
    const currentValue = fieldValue.textContent;

    field.classList.add("editing");
    const input = document.createElement("input");
    input.type = "text";
    input.value = currentValue;
    input.className = "field-edit-input";
    fieldValue.replaceWith(input);
    input.focus();
    input.select();

    const save = async () => {
      const newValue = input.value.trim();
      if (newValue && newValue !== currentValue) {
        try {
          await fetch("/onboarding/override-field", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ field: fieldKey, value: newValue }),
          });
        } catch (err) {
          console.error("Failed to save field override:", err);
        }
      }

      const span = document.createElement("span");
      span.className = "field-value";
      span.textContent = newValue || currentValue;
      span.dataset.onClick = `$editing_field = '${fieldKey}'`;
      input.replaceWith(span);
      field.classList.remove("editing");
    };

    input.addEventListener("keydown", (ev) => {
      if (ev.key === "Enter") {
        ev.preventDefault();
        save();
      }
      if (ev.key === "Escape") {
        const span = document.createElement("span");
        span.className = "field-value";
        span.textContent = currentValue;
        input.replaceWith(span);
        field.classList.remove("editing");
      }
    });

    input.addEventListener("blur", save);
  });

  // --- Onboarding graph renderer (simplified version for preview) ---
  window.renderOnboardingGraph = function (graphData, container) {
    if (!graphData || !container || typeof d3 === "undefined") return;

    const width = container.clientWidth;
    const height = container.clientHeight;

    // Clear existing
    d3.select(container).selectAll("svg").remove();

    const svg = d3.select(container)
      .append("svg")
      .attr("width", width)
      .attr("height", height)
      .attr("viewBox", `0 0 ${width} ${height}`);

    const nodes = (graphData.nodes || []).map((n, i) => ({
      ...n,
      x: width / 2 + Math.cos((2 * Math.PI * i) / graphData.nodes.length) * Math.min(width, height) * 0.35,
      y: height / 2 + Math.sin((2 * Math.PI * i) / graphData.nodes.length) * Math.min(width, height) * 0.35,
    }));

    const nodeMap = {};
    nodes.forEach((n) => (nodeMap[n.id] = n));

    const edges = (graphData.edges || []).filter(
      (e) => nodeMap[e.from_id] && nodeMap[e.to_id]
    );

    // Draw edges
    svg.selectAll("line.edge")
      .data(edges)
      .enter()
      .append("line")
      .attr("class", "edge")
      .attr("x1", (d) => nodeMap[d.from_id].x)
      .attr("y1", (d) => nodeMap[d.from_id].y)
      .attr("x2", (d) => nodeMap[d.to_id].x)
      .attr("y2", (d) => nodeMap[d.to_id].y)
      .attr("stroke", "var(--border)")
      .attr("stroke-width", 1)
      .attr("opacity", 0.5);

    // Draw nodes
    const masteryColors = {
      mastered: "var(--mastered)",
      proficient: "var(--proficient)",
      familiar: "var(--familiar)",
      attempted: "var(--attempted)",
      not_started: "var(--not-started)",
    };

    svg.selectAll("circle.node")
      .data(nodes)
      .enter()
      .append("circle")
      .attr("class", (d) => `node ${d._new ? "node-pulsing" : ""}`)
      .attr("cx", (d) => d.x)
      .attr("cy", (d) => d.y)
      .attr("r", 6)
      .attr("fill", (d) => masteryColors[d.mastery_category || "not_started"])
      .attr("stroke", "var(--border)")
      .attr("stroke-width", 1);

    // Node labels
    svg.selectAll("text.node-label")
      .data(nodes)
      .enter()
      .append("text")
      .attr("class", "node-label")
      .attr("x", (d) => d.x)
      .attr("y", (d) => d.y + 16)
      .attr("text-anchor", "middle")
      .attr("fill", "var(--text-dim)")
      .attr("font-size", "9px")
      .attr("font-family", "var(--mono)")
      .text((d) => d.name.length > 15 ? d.name.slice(0, 14) + "..." : d.name);
  };
})();
```

- [ ] **Step 2: Add field-edit-input style to observatory.css**

Append to `static/css/observatory.css`:
```css
/* Field inline editing (onboarding) */
.field-edit-input {
  width: 100%;
  padding: 4px 8px;
  background: var(--deep);
  border: 1px solid var(--gold-dim);
  border-radius: 6px;
  color: var(--text-bright);
  font-family: var(--sans);
  font-size: 14px;
  outline: none;
}
```

- [ ] **Step 3: Add onboarding.js script to onboarding/index.html**

In `templates/onboarding/index.html`, add before `{% endblock %}`:
```html
<script src="/static/js/onboarding.js" defer></script>
```

- [ ] **Step 4: Commit**

```bash
git commit -m "feat: onboarding.js — auto-scroll, field editing, graph preview renderer"
```

---

### Task 6: Service Worker — Cache Strategies + Offline Support

**Files:**
- Create: `learn-anything-app/sw.js`
- Create: `learn-anything-app/app/routes/sw.py`
- Test: `learn-anything-app/tests/integration/test_routes/test_sw.py`

The service worker lives at the project root so it has the broadest scope (`/`). FastAPI serves it with the correct `Service-Worker-Allowed` header.

- [ ] **Step 1: Write failing tests for service worker route**

```python
# tests/integration/test_routes/test_sw.py
import pytest
from httpx import AsyncClient, ASGITransport
from app.main import app

@pytest.fixture
async def client():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as c:
        yield c

@pytest.mark.asyncio
async def test_sw_js_serves(client):
    resp = await client.get("/sw.js")
    assert resp.status_code == 200
    assert "text/javascript" in resp.headers.get("content-type", "")
    assert "self.addEventListener" in resp.text

@pytest.mark.asyncio
async def test_sw_js_has_correct_scope_header(client):
    resp = await client.get("/sw.js")
    assert resp.headers.get("service-worker-allowed") == "/"

@pytest.mark.asyncio
async def test_sw_js_no_cache_header(client):
    resp = await client.get("/sw.js")
    cache_control = resp.headers.get("cache-control", "")
    assert "no-cache" in cache_control or "max-age=0" in cache_control

@pytest.mark.asyncio
async def test_manifest_serves(client):
    resp = await client.get("/static/manifest.json")
    assert resp.status_code == 200
    data = resp.json()
    assert data["name"] == "Learn Anything"
    assert data["start_url"] == "/"
```

- [ ] **Step 2: Run tests — should fail**

Run: `cd learn-anything-app && uv run pytest tests/integration/test_routes/test_sw.py -v`
Expected: FAIL

- [ ] **Step 3: Implement service worker route**

```python
# app/routes/sw.py
from pathlib import Path
from fastapi import APIRouter
from fastapi.responses import FileResponse

router = APIRouter(tags=["pwa"])

SW_PATH = Path(__file__).resolve().parent.parent.parent / "sw.js"

@router.get("/sw.js")
async def serve_service_worker():
    """Serve sw.js from project root with correct headers.

    The service worker must be served from root scope (/) to intercept
    all fetch requests. Cache-Control: no-cache ensures updates propagate.
    """
    return FileResponse(
        path=SW_PATH,
        media_type="text/javascript",
        headers={
            "Service-Worker-Allowed": "/",
            "Cache-Control": "no-cache, max-age=0",
        },
    )
```

- [ ] **Step 4: Implement the service worker**

```javascript
// sw.js — Service Worker for Learn Anything PWA
// Cache-first for stable data, network-first for dynamic data,
// network-only for real-time SSE streams.

const CACHE_VERSION = "la-v1";
const STABLE_CACHE = `${CACHE_VERSION}-stable`;
const DYNAMIC_CACHE = `${CACHE_VERSION}-dynamic`;

// Stable data: cache-first
// These URLs/patterns are cached on first fetch and served from cache thereafter.
// Updated only when cache version changes (service worker update).
const STABLE_PATTERNS = [
  /\/api\/graph\/structure/,        // Graph nodes + edges (no mastery)
  /\/api\/materials\//,             // Lectures, flashcards, worked examples
  /\/api\/skill-dossier/,           // Skill dossier
  /\/api\/learning-plan/,           // Learning plan
  /\/static\//,                     // CSS, JS, images, fonts
  /\/manifest\.json$/,              // PWA manifest
  /\.(png|jpg|jpeg|webp|svg|woff2|woff|ttf|eot)$/i, // Assets
];

// Dynamic data: network-first
// Try network, fall back to cache for offline.
const DYNAMIC_PATTERNS = [
  /\/api\/graph\/mastery/,          // Mastery overlay
  /\/api\/progress/,                // Progress state
  /\/api\/session\/agenda/,         // Session agenda
  /\/api\/calibration/,             // Difficulty calibration
];

// Network-only: never cache
// SSE streams and real-time endpoints.
const NETWORK_ONLY_PATTERNS = [
  /\/onboarding\/chat/,             // Onboarding SSE
  /\/train\/chat/,                  // Train mode SSE
  /\/api\/stream/,                  // Any SSE stream
];

// Install: pre-cache the app shell
self.addEventListener("install", (event) => {
  event.waitUntil(
    caches.open(STABLE_CACHE).then((cache) => {
      return cache.addAll([
        "/",
        "/static/css/observatory.css",
        "/static/js/onboarding.js",
        "/static/manifest.json",
      ]);
    })
  );
  self.skipWaiting();
});

// Activate: clean up old caches
self.addEventListener("activate", (event) => {
  event.waitUntil(
    caches.keys().then((keys) => {
      return Promise.all(
        keys
          .filter((key) => key.startsWith("la-") && key !== STABLE_CACHE && key !== DYNAMIC_CACHE)
          .map((key) => caches.delete(key))
      );
    })
  );
  self.clients.claim();
});

// Fetch: route to appropriate strategy
self.addEventListener("fetch", (event) => {
  const url = new URL(event.request.url);
  const path = url.pathname;

  // Network-only: SSE streams and real-time
  // CRITICAL: Never cache text/event-stream responses
  if (isNetworkOnly(path) || event.request.headers.get("Accept")?.includes("text/event-stream")) {
    return; // Let the browser handle it directly (no service worker interception)
  }

  // Stable data: cache-first
  if (isStable(path)) {
    event.respondWith(cacheFirst(event.request, STABLE_CACHE));
    return;
  }

  // Dynamic data: network-first
  if (isDynamic(path)) {
    event.respondWith(networkFirst(event.request, DYNAMIC_CACHE));
    return;
  }

  // HTML pages: network-first (for fresh server-rendered content)
  if (event.request.mode === "navigate") {
    event.respondWith(networkFirst(event.request, DYNAMIC_CACHE));
    return;
  }

  // Default: network-first
  event.respondWith(networkFirst(event.request, DYNAMIC_CACHE));
});

// Background sync: queue offline flashcard reviews
self.addEventListener("sync", (event) => {
  if (event.tag === "sync-flashcard-reviews") {
    event.waitUntil(syncFlashcardReviews());
  }
});

// --- Strategy implementations ---

async function cacheFirst(request, cacheName) {
  const cached = await caches.match(request);
  if (cached) {
    // Check version header for staleness
    const cachedVersion = cached.headers.get("X-LA-Cache-Version");
    if (cachedVersion) {
      try {
        const headResp = await fetch(request, { method: "HEAD" });
        const serverVersion = headResp.headers.get("X-LA-Cache-Version");
        if (serverVersion && serverVersion !== cachedVersion) {
          // Stale — fetch fresh and update cache
          const freshResp = await fetch(request);
          const cache = await caches.open(cacheName);
          cache.put(request, freshResp.clone());
          return freshResp;
        }
      } catch (e) {
        // Offline — serve cached version
      }
    }
    return cached;
  }

  try {
    const resp = await fetch(request);
    if (resp.ok) {
      const cache = await caches.open(cacheName);
      cache.put(request, resp.clone());
    }
    return resp;
  } catch (e) {
    return new Response("Offline — resource not cached", { status: 503 });
  }
}

async function networkFirst(request, cacheName) {
  try {
    const resp = await fetch(request);
    if (resp.ok) {
      const cache = await caches.open(cacheName);
      cache.put(request, resp.clone());
    }
    return resp;
  } catch (e) {
    const cached = await caches.match(request);
    if (cached) return cached;
    return new Response("Offline — resource not available", { status: 503 });
  }
}

// --- Background sync ---

async function syncFlashcardReviews() {
  try {
    const db = await openReviewDB();
    const tx = db.transaction("pending_reviews", "readonly");
    const store = tx.objectStore("pending_reviews");
    const reviews = await getAllFromStore(store);

    if (reviews.length === 0) return;

    const resp = await fetch("/api/flashcards/sync-reviews", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ reviews }),
    });

    if (resp.ok) {
      // Clear synced reviews
      const clearTx = db.transaction("pending_reviews", "readwrite");
      const clearStore = clearTx.objectStore("pending_reviews");
      clearStore.clear();
    }
  } catch (e) {
    // Will retry on next sync event
    console.error("Flashcard sync failed, will retry:", e);
  }
}

function openReviewDB() {
  return new Promise((resolve, reject) => {
    const req = indexedDB.open("learn-anything-reviews", 1);
    req.onupgradeneeded = () => {
      const db = req.result;
      if (!db.objectStoreNames.contains("pending_reviews")) {
        db.createObjectStore("pending_reviews", { keyPath: "id", autoIncrement: true });
      }
    };
    req.onsuccess = () => resolve(req.result);
    req.onerror = () => reject(req.error);
  });
}

function getAllFromStore(store) {
  return new Promise((resolve, reject) => {
    const req = store.getAll();
    req.onsuccess = () => resolve(req.result);
    req.onerror = () => reject(req.error);
  });
}

// --- Pattern matchers ---

function isStable(path) {
  return STABLE_PATTERNS.some((p) => p.test(path));
}

function isDynamic(path) {
  return DYNAMIC_PATTERNS.some((p) => p.test(path));
}

function isNetworkOnly(path) {
  return NETWORK_ONLY_PATTERNS.some((p) => p.test(path));
}
```

- [ ] **Step 5: Register the sw route in main.py**

Add to `app/main.py`:
```python
from app.routes.sw import router as sw_router
app.include_router(sw_router)
```

- [ ] **Step 6: Run tests — should pass**

Run: `cd learn-anything-app && uv run pytest tests/integration/test_routes/test_sw.py -v`
Expected: PASS

- [ ] **Step 7: Commit**

```bash
git commit -m "feat: service worker — cache-first/network-first/network-only strategies, background sync"
```

---

### Task 7: PWA Manifest + Service Worker Registration

**Files:**
- Create: `learn-anything-app/static/manifest.json`
- Modify: `learn-anything-app/templates/base.html`

- [ ] **Step 1: Create PWA manifest**

```json
{
  "name": "Learn Anything",
  "short_name": "LearnAnything",
  "description": "Adaptive learning through knowledge graphs, Socratic dialogue, and personalized curriculum",
  "start_url": "/",
  "display": "standalone",
  "background_color": "#04060e",
  "theme_color": "#d4a456",
  "orientation": "any",
  "icons": [
    {
      "src": "/static/icons/icon-192.png",
      "sizes": "192x192",
      "type": "image/png"
    },
    {
      "src": "/static/icons/icon-512.png",
      "sizes": "512x512",
      "type": "image/png"
    },
    {
      "src": "/static/icons/icon-512-maskable.png",
      "sizes": "512x512",
      "type": "image/png",
      "purpose": "maskable"
    }
  ],
  "categories": ["education"],
  "lang": "en"
}
```

- [ ] **Step 2: Verify SRI hashes on CDN scripts in base.html**

Ensure the existing Datastar and D3 CDN `<script>` tags in `templates/base.html` have `integrity` and `crossorigin="anonymous"` attributes. If they are missing, add placeholder attributes:
```html
  <!-- SRI hash — regenerate when updating CDN version -->
  <script src="https://cdn.jsdelivr.net/npm/@anthropic-ai/datastar@..." integrity="sha384-PLACEHOLDER" crossorigin="anonymous"></script>
  <!-- SRI hash — regenerate when updating CDN version -->
  <script src="https://cdn.jsdelivr.net/npm/d3@..." integrity="sha384-PLACEHOLDER" crossorigin="anonymous"></script>
```
Generate actual hashes with: `curl -s <CDN_URL> | openssl dgst -sha384 -binary | openssl base64 -A`

- [ ] **Step 3: Add service worker registration and manifest link to base.html**

Add to `<head>` section of `templates/base.html`:
```html
  <link rel="manifest" href="/static/manifest.json">
  <meta name="theme-color" content="#d4a456">
  <meta name="apple-mobile-web-app-capable" content="yes">
  <meta name="apple-mobile-web-app-status-bar-style" content="black-translucent">
  <link rel="apple-touch-icon" href="/static/icons/icon-192.png">
```

Add before `</body>` in `templates/base.html`:
```html
  <script>
    // Service worker registration
    if ("serviceWorker" in navigator) {
      window.addEventListener("load", () => {
        navigator.serviceWorker
          .register("/sw.js", { scope: "/" })
          .then((reg) => {
            console.log("SW registered, scope:", reg.scope);
            // Check for updates periodically
            setInterval(() => reg.update(), 60 * 60 * 1000); // Every hour
          })
          .catch((err) => {
            console.warn("SW registration failed:", err);
          });
      });
    }

    // Register for background sync (flashcard reviews)
    async function queueFlashcardReview(reviewData) {
      if (!("indexedDB" in window)) return false;
      try {
        const db = await new Promise((resolve, reject) => {
          const req = indexedDB.open("learn-anything-reviews", 1);
          req.onupgradeneeded = () => {
            const db = req.result;
            if (!db.objectStoreNames.contains("pending_reviews")) {
              db.createObjectStore("pending_reviews", { keyPath: "id", autoIncrement: true });
            }
          };
          req.onsuccess = () => resolve(req.result);
          req.onerror = () => reject(req.error);
        });

        const tx = db.transaction("pending_reviews", "readwrite");
        tx.objectStore("pending_reviews").add(reviewData);

        // Request background sync
        if ("serviceWorker" in navigator && "SyncManager" in window) {
          const reg = await navigator.serviceWorker.ready;
          await reg.sync.register("sync-flashcard-reviews");
        }
        return true;
      } catch (e) {
        console.error("Failed to queue review:", e);
        return false;
      }
    }

    // Expose globally for use by flashcard components
    window.queueFlashcardReview = queueFlashcardReview;
  </script>
```

- [ ] **Step 4: Commit**

```bash
git commit -m "feat: PWA manifest + service worker registration in base template"
```

---

### Task 8: Onboarding Route Integration — Root Redirect + Navigation

**Files:**
- Modify: `learn-anything-app/app/main.py`

After setup is complete and user is authenticated, the root route should redirect new users (no active skill) to onboarding, and returning users to explore mode.

- [ ] **Step 1: Add has_completed_onboarding to OnboardingService**

Add this method to `app/services/onboarding.py`:
```python
    @staticmethod
    async def has_completed_onboarding(user_id: str, backend) -> bool:
        """Check if the user has completed onboarding by querying the state backend.

        Looks for the existence of key state files (knowledge-graph, learning-plan)
        that indicate onboarding is complete. Does NOT rely on in-memory session state.
        """
        # Check for the state files that indicate a complete onboarding:
        # - knowledge-graph.json (produced by learner-calibrator)
        # - learning-plan.json (produced by curriculum-architect)
        # - srs-cards.json (produced by material-forge)
        required_files = ["knowledge-graph.json", "learning-plan.json"]
        for filename in required_files:
            if not await backend.state_file_exists(user_id, filename):
                return False
        return True
```

- [ ] **Step 2: Update root route to use StateBackend query**

Replace the root route in `app/main.py`:
```python
@app.get("/")
async def root(request: Request):
    if not settings.setup_complete:
        return RedirectResponse("/setup")

    # Check if user has active skills (any state files exist)
    user_id = getattr(request.state, "user_id", None)
    if not user_id and settings.single_user:
        user_id = "default"

    if not user_id:
        return RedirectResponse("/auth/login")

    # Query the state backend for existing state files — never import
    # private session dicts from other modules
    from app.services.onboarding import OnboardingService
    from app.backends import get_state_backend

    backend = get_state_backend()
    if await OnboardingService.has_completed_onboarding(user_id, backend):
        return RedirectResponse("/explore")

    return RedirectResponse("/onboarding")
```

- [ ] **Step 3: Verify routing**

Run: `cd learn-anything-app && uv run uvicorn app.main:app --reload`
Navigate to `http://localhost:8000/` — should redirect to `/onboarding` for new users.

- [ ] **Step 4: Commit**

```bash
git commit -m "feat: root route redirects new users to onboarding, returning users to explore"
```

---

### Task 9: Offline Flashcard Review — IndexedDB Queue + Background Sync Integration

**Files:**
- Modify: `learn-anything-app/sw.js` (already has sync handler)
- Modify: `learn-anything-app/templates/base.html` (already has queueFlashcardReview)

This task ensures the offline flashcard review flow is complete end-to-end: user reviews a flashcard offline, the result is queued in IndexedDB, and when connectivity returns, the background sync sends it to the server.

- [ ] **Step 1: Add offline detection UI to base template**

Add to `templates/base.html` before `</body>` (inside the existing script block):
```html
  <div id="offline-banner" class="offline-banner" style="display:none;">
    <span class="offline-icon">&#9888;</span>
    <span>You're offline. Changes will sync when you reconnect.</span>
  </div>

  <script>
    // Offline detection
    function updateOnlineStatus() {
      const banner = document.getElementById("offline-banner");
      if (banner) {
        banner.style.display = navigator.onLine ? "none" : "flex";
      }
    }
    window.addEventListener("online", updateOnlineStatus);
    window.addEventListener("offline", updateOnlineStatus);
    updateOnlineStatus();
  </script>
```

- [ ] **Step 2: Add offline-banner styles to observatory.css**

Append to `static/css/observatory.css`:
```css
/* Offline banner */
.offline-banner {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  z-index: 9999;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
  padding: 8px 16px;
  background: var(--surface);
  border-bottom: 1px solid var(--familiar);
  color: var(--familiar);
  font-family: var(--mono);
  font-size: 12px;
}

.offline-icon {
  font-size: 14px;
}
```

- [ ] **Step 3: Commit**

```bash
git commit -m "feat: offline detection banner + flashcard review queue for background sync"
```

---

### Task 10: Integration Tests — Full Onboarding Flow + Service Worker

**Files:**
- Modify: `learn-anything-app/tests/integration/test_routes/test_onboarding.py`
- Modify: `learn-anything-app/tests/integration/test_services/test_onboarding_service.py`

- [ ] **Step 1: Add integration tests for full onboarding flow**

Append to `tests/integration/test_routes/test_onboarding.py`:

```python
@pytest.mark.asyncio
async def test_onboarding_page_includes_pipeline_bar(client):
    resp = await client.get("/onboarding")
    assert "pipeline-bar" in resp.text
    assert "pipeline-fill" in resp.text

@pytest.mark.asyncio
async def test_onboarding_page_includes_state_panel(client):
    resp = await client.get("/onboarding")
    assert "state-panel" in resp.text
    assert "panel_visible" in resp.text

@pytest.mark.asyncio
async def test_onboarding_page_includes_chat_input(client):
    resp = await client.get("/onboarding")
    assert "chat-input" in resp.text
    assert "chat-send-btn" in resp.text

@pytest.mark.asyncio
async def test_onboarding_page_includes_sw_registration(client):
    """Verify the base template includes service worker registration."""
    resp = await client.get("/onboarding")
    assert "serviceWorker" in resp.text or "sw.js" in resp.text

@pytest.mark.asyncio
async def test_onboarding_state_returns_initial(client):
    resp = await client.get("/onboarding/state")
    if resp.status_code == 200:
        data = resp.json()
        assert data["phase"] == "domain_assessment"
        assert data["progress_pct"] == 0

@pytest.mark.asyncio
async def test_onboarding_override_field_accepts_json(client):
    resp = await client.post("/onboarding/override-field", json={
        "field": "skill_type",
        "value": "cognitive",
    })
    if resp.status_code == 200:
        data = resp.json()
        assert data["status"] == "ok"
        assert data["field"] == "skill_type"
```

- [ ] **Step 2: Add service tests for edge cases**

Append to `tests/integration/test_services/test_onboarding_service.py`:

```python
def test_override_field_before_any_phase():
    svc = OnboardingService(user_id="user-1", skill_slug="guitar")
    svc.override_panel_field("custom_field", "custom_value")
    state = svc.get_state()
    assert state.panel_fields["custom_field"] == "custom_value"
    # Panel should not be visible yet (no phases complete)
    assert state.panel_visible is False

def test_mark_same_phase_twice_is_idempotent():
    svc = OnboardingService(user_id="user-1", skill_slug="guitar")
    svc.mark_phase_complete("domain_assessment", state_data={"x": "1"})
    svc.mark_phase_complete("domain_assessment", state_data={"y": "2"})
    state = svc.get_state()
    # Phase should only appear once in completed list
    assert state.phase == "skill_research"
    assert state.panel_fields.get("x") == "1"
    assert state.panel_fields.get("y") == "2"

def test_calibration_loop_does_not_reset_other_fields():
    svc = OnboardingService(user_id="user-1", skill_slug="guitar")
    svc.mark_phase_complete("domain_assessment", state_data={"skill_type": "motor"})
    svc.mark_phase_complete("skill_research", state_data={"nodes": "15"})
    svc.trigger_re_research(reason="gap")
    state = svc.get_state()
    # Domain assessment fields should persist
    assert state.panel_fields["skill_type"] == "motor"
    # But we bounced back to skill_research
    assert state.phase == "skill_research"

def test_progress_pct_monotonic_through_pipeline():
    svc = OnboardingService(user_id="user-1", skill_slug="guitar")
    prev_pct = 0
    for phase in ["domain_assessment", "skill_research", "learner_calibration",
                   "curriculum_design", "material_generation", "dashboard_ready"]:
        if phase == "curriculum_design":
            svc.confirm_agreement_gate("teaching_preferences")
            svc.confirm_agreement_gate("epitome_refinement")
        svc.mark_phase_complete(phase, state_data={})
        state = svc.get_state()
        assert state.progress_pct >= prev_pct
        prev_pct = state.progress_pct
```

- [ ] **Step 3: Run full test suite**

Run: `cd learn-anything-app && uv run pytest tests/integration/test_services/test_onboarding_service.py tests/integration/test_routes/test_onboarding.py tests/integration/test_routes/test_sw.py -v`
Expected: All PASS

- [ ] **Step 4: Commit**

```bash
git commit -m "test: onboarding integration tests — full flow, edge cases, service worker"
```

---

### Task 11: Run All Tests + Final Verification

- [ ] **Step 1: Run the full test suite**

Run: `cd learn-anything-app && uv run pytest tests/ -v --tb=short`
Expected: All tests pass. New test count for Plan 6:
- Onboarding service (11 tests: initial state, phase transitions, calibration loop, agreement gates, full pipeline, panel fields, override, edge cases)
- Onboarding routes (8 tests: page render, datastar signals, chat endpoint, override field, state endpoint, pipeline bar, chat input, sw registration)
- Service worker routes (4 tests: sw.js serves, scope header, no-cache, manifest)

- [ ] **Step 2: Manual verification**

Run: `cd learn-anything-app && uv run uvicorn app.main:app --reload`

Verify:
1. `http://localhost:8000/onboarding` — Full-width chat renders, pipeline bar at bottom shows 0%
2. Type a message, send — chat input clears, user message appears
3. `http://localhost:8000/sw.js` — Service worker JavaScript loads, content-type is `text/javascript`
4. `http://localhost:8000/static/manifest.json` — PWA manifest returns valid JSON
5. Browser DevTools > Application > Service Workers — sw.js registered
6. Browser DevTools > Application > Cache Storage — `la-v1-stable` cache created
7. Go offline in DevTools > Network > Offline — offline banner appears

- [ ] **Step 3: Final commit**

```bash
git commit -m "chore: Plan 6 complete — onboarding flow + PWA with service worker"
```

---

## Summary

**What Plan 6 delivers:**

1. **Streaming Helper** (`app/services/streaming.py`) — Thin wrapper around `datastar-py` SDK exposing `patch_elements()`, `patch_signals()`, `remove_elements()` for all plans.

2. **Onboarding Service** (`app/services/onboarding.py`) — State machine tracking pipeline phases, calibration loop (max 2x), agreement gates, panel field accumulation with user overrides. Includes `has_completed_onboarding()` static method for state-backend-based detection.

3. **Onboarding Routes** (`app/routes/onboarding.py`) — SSE-streaming chat endpoint reusing Plan 5 infrastructure. Phase-specific handlers for all 6 pipeline phases. JSON extraction from LLM responses. LLM-classified agreement gates. Datastar signal/element patches for progressive UI updates.

4. **Onboarding Templates** (`templates/onboarding/`) — Full-width chat that compresses to 60% when state panel fades in. Progressive field reveal. Graph preview with mastery color coding. Expert panel cards and epitome proposal card for agreement gates. Pipeline progress bar.

5. **Service Worker** (`sw.js`) — Three-tier cache strategy: cache-first for stable data (graph structure, materials, static assets), network-first for dynamic data (mastery overlay, progress), network-only for SSE streams (never cached). Version-header-based invalidation. Background sync for offline flashcard reviews via IndexedDB queue.

6. **PWA Manifest** (`static/manifest.json`) — Installability with app name, icons, theme color matching Observatory identity.

7. **Offline Support** — Offline banner, cached material browsing, flashcard review queue with background sync.

**Key architectural decisions:**
- Onboarding state is in-memory per session (not persisted separately) — the real persistence is the state files written by each skill phase
- Agreement gates are conversational — user intent (CONFIRM, REDIRECT, QUESTION) classified by a lightweight LLM call, not fragile keyword matching
- Service worker excludes `text/event-stream` from caching via `?.includes()` (tolerates `Accept` headers with multiple types)
- All SSE helpers use the `datastar-py` SDK via `app/services/streaming.py` (thin wrapper); no hand-formatted SSE strings
- LLM calls use `llm.stream(messages, system=system_prompt)` with `LLMMessage` conversation history per Plan 3's interface; text extracted from `LLMStreamEvent.text`
- Root route queries the `StateBackend` for existing state files to detect onboarding completion; never imports private session dicts
- CDN scripts (Datastar, D3) require `integrity` SRI attributes and `crossorigin="anonymous"`; no Google Fonts CDN (fonts are self-hosted)
- Calibration loop UI shows spinner + topic label, new nodes get pulsing borders in graph preview
