> HISTORICAL DESIGN REFERENCE: superseded operationally by CONVENTIONS.md and
> docs/superpowers/plans/2026-11-06-alpha-foundation.md. Do not execute provisioning,
> runner or database commands below. No current service admission is implied.

# Plan 5: Train Mode, Materials Mode, Progress Mode

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking. **Use opus subagents exclusively (model: opus). No sonnet, no haiku.**
>
> **REQUIRED READING:** `docs/plans/CONVENTIONS.md` — all plans follow these rules.
>
> **Execution:** Plans execute sequentially (1→2→3→4→5→6) on feature branch `feature/learn-anything-webapp`. TDD strictly enforced.

**Goal:** Three new application modes — Train (voice-first Socratic tutoring with AI-driven content), Materials (browseable content hub with inline feedback), and Progress (learning-focused dashboard). All server-driven via Datastar SSE, mobile-responsive, Observatory-styled.

**Architecture:** Resizable split-panel Train mode with SSE-streamed chat and LLM-pushed content fragments. Materials mode with server-rendered browse/search and feedback via `@post()`. Progress mode with SQL/AGE-computed metrics (PG) or in-memory simplified metrics (JSON). No SPA patterns anywhere — all state changes are SSE fragment pushes or form posts that return updated fragments.

**Tech Stack:** FastAPI + Jinja2 (templates), Datastar (SSE hypermedia), Web Speech API (STT), vanilla JS (split panel, voice), D3.js (mini graph in Train, coverage chart in Progress), Claude Agent SDK (LLM streaming), SQLAlchemy (queries), Observatory CSS (extended)

**Spec:** `docs/specs/2026-04-01-learn-anything-webapp-design.md` — Section 4

**Depends on:** Plan 1 (project scaffold, models, auth, CSS foundation), Plan 2 (Postgres backend, graph queries), Plan 3 (LLM integration, orchestrator, rate limiting), Plan 4 (Frontend shell, Explore mode, D3 graph, Datastar SSE patterns)

> **IMPLEMENTATION NOTES (from review):**
> 1. **Migration** for this plan is `004` (revising `003` from Plan 3). Use `--rev-id 004` with alembic.
> 2. **Create `__init__.py`** for any new test directories not already created by prior plans.
> 3. **Remove local `client` fixtures** from test files — use the shared fixture from `conftest.py`.
> 4. **Flag modal**: Ensure all 4 options from spec are present: regenerate, expand, edit directly, dismiss.

---

## Project Structure Additions

This plan adds the following files to the `learn-anything-app/` tree established in Plan 1.

```
learn-anything-app/
├── app/
│   ├── models/
│   │   └── progress.py             # TrainingSession, SessionTopic, MaterialFeedback
│   ├── routes/
│   │   ├── train.py                # Train mode routes + SSE chat streaming
│   │   ├── materials.py            # Materials browse/search/feedback routes
│   │   └── progress.py             # Progress dashboard routes
│   └── services/
│       ├── training.py             # Training session management, LLM orchestration
│       └── metrics.py              # Progress metrics computation (PG + JSON backends)
├── templates/
│   ├── train/
│   │   ├── index.html              # Train mode layout (split panel, mode shell)
│   │   ├── chat.html               # Chat panel fragment (message list + input)
│   │   ├── content.html            # Content panel fragment (tab container)
│   │   ├── content_example.html    # Worked example with backward fading
│   │   ├── content_diagram.html    # Diagram/SVG display
│   │   ├── content_graph.html      # Mini knowledge graph (D3 island)
│   │   ├── content_video.html      # YouTube embed with annotations
│   │   └── content_flashcards.html # Flashcard review interface
│   ├── materials/
│   │   ├── index.html              # Materials browser (search + filters + grid)
│   │   ├── card.html               # Material card with feedback controls
│   │   ├── feedback_modal.html     # Flag/comment modal fragment
│   │   └── quality_stats.html      # Approved/flagged/unreviewed counts
│   └── progress/
│       ├── index.html              # Progress dashboard layout
│       ├── metrics.html            # Primary metrics cards fragment
│       ├── roadmap.html            # Curriculum roadmap fragment
│       ├── session_history.html    # Session history list fragment
│       └── coverage_chart.html     # Knowledge graph coverage over time (D3)
├── static/
│   ├── js/
│   │   ├── split-panel.js          # Resizable split panel (vanilla JS)
│   │   └── voice.js                # Web Speech API integration
│   └── css/
│       └── observatory.css         # Extended with train, materials, progress styles
└── tests/
    └── test_routes/
        ├── test_train.py           # Train mode route tests
        ├── test_materials.py       # Materials route tests
        └── test_progress.py        # Progress route tests
```

---

### Task 1: Progress Models — TrainingSession, SessionTopic, MaterialFeedback

**Files:**
- Create: `learn-anything-app/app/models/progress.py`
- Test: `learn-anything-app/tests/integration/test_models/test_progress.py`

These models store training session records, per-topic performance, and material feedback. They back all three modes: Train writes sessions, Progress reads them, Materials reads/writes feedback.

- [ ] **Step 1: Write failing test for TrainingSession model**

```python
# tests/integration/test_models/test_progress.py
import pytest
from app.models.progress import TrainingSession, SessionTopic, MaterialFeedback


@pytest.mark.asyncio
async def test_create_training_session(db):
    session = TrainingSession(
        user_id="user-1",
        skill_slug="jazz-piano",
        template_used="A_concept_intro",
        focus_vertex_ids='["v1","v2"]',
        duration_minutes=45,
        difficulty_zone_start="zpd_optimal",
        difficulty_zone_end="mastery",
        session_summary="Introduced voicing concepts. Learner grasped shell voicings quickly.",
    )
    db.add(session)
    await db.commit()
    await db.refresh(session)
    assert session.id is not None
    assert session.template_used == "A_concept_intro"
    assert session.session_number is None  # Set by service layer


@pytest.mark.asyncio
async def test_create_session_topic(db):
    topic = SessionTopic(
        session_id="sess-1",
        vertex_id="v1",
        vertex_name="Shell Voicings",
        activity_type="introduction",
        accuracy=0.85,
        scaffold_level_needed=2,
        bloom_level_demonstrated="apply",
        notes="Strong grasp of root position, needs work on inversions",
    )
    db.add(topic)
    await db.commit()
    await db.refresh(topic)
    assert topic.id is not None
    assert topic.accuracy == 0.85


@pytest.mark.asyncio
async def test_create_material_feedback(db):
    feedback = MaterialFeedback(
        user_id="user-1",
        material_id="mat-1",
        card_id="card-1",
        step_index=2,
        feedback_type="flag",
        comment="Step 3 has an error in the chord spelling",
        resolution="pending",
    )
    db.add(feedback)
    await db.commit()
    await db.refresh(feedback)
    assert feedback.id is not None
    assert feedback.feedback_type == "flag"
    assert feedback.resolution == "pending"


@pytest.mark.asyncio
async def test_material_feedback_approve(db):
    feedback = MaterialFeedback(
        user_id="user-1",
        material_id="mat-2",
        feedback_type="approve",
    )
    db.add(feedback)
    await db.commit()
    assert feedback.resolution is None  # Approvals don't need resolution
```

- [ ] **Step 2: Run test — should fail**

Run: `cd learn-anything-app && uv run pytest tests/integration/test_models/test_progress.py -v`
Expected: FAIL — `ModuleNotFoundError`

- [ ] **Step 3: Implement progress models**

```python
# app/models/progress.py
import uuid
from datetime import datetime, timezone
from sqlalchemy import String, Float, Integer, Text, DateTime, ForeignKey, JSON, func
from sqlalchemy.orm import Mapped, mapped_column
from app.models.base import Base


class TrainingSession(Base):
    __tablename__ = "training_sessions"

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid.uuid4())
    )
    user_id: Mapped[str] = mapped_column(ForeignKey("users.id"), index=True)
    skill_slug: Mapped[str] = mapped_column(String(100), index=True)
    session_number: Mapped[int | None] = mapped_column(Integer, nullable=True)
    template_used: Mapped[str] = mapped_column(String(30))
    # A_concept_intro, B_retrieval_review, C_skill_drill,
    # D_productive_failure, E_mastery_gate, F_mentor_conversation
    focus_vertex_ids: Mapped[list] = mapped_column(JSON, default=list)
    # JSON array of vertex IDs — use JSON column for PG query support
    duration_minutes: Mapped[int | None] = mapped_column(Integer, nullable=True)
    difficulty_zone_start: Mapped[str | None] = mapped_column(
        String(30), nullable=True
    )
    difficulty_zone_end: Mapped[str | None] = mapped_column(String(30), nullable=True)
    rolling_accuracy: Mapped[float | None] = mapped_column(Float, nullable=True)
    scaffold_level: Mapped[int | None] = mapped_column(Integer, nullable=True)
    session_summary: Mapped[str] = mapped_column(Text, default="")
    started_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    ended_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )


class SessionTopic(Base):
    __tablename__ = "session_topics"

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid.uuid4())
    )
    session_id: Mapped[str] = mapped_column(ForeignKey("training_sessions.id"), index=True)
    vertex_id: Mapped[str] = mapped_column(String(36), index=True)
    vertex_name: Mapped[str] = mapped_column(String(200))
    activity_type: Mapped[str] = mapped_column(String(30))
    # introduction, practice, review, assessment, productive_failure
    accuracy: Mapped[float | None] = mapped_column(Float, nullable=True)
    scaffold_level_needed: Mapped[int | None] = mapped_column(Integer, nullable=True)
    bloom_level_demonstrated: Mapped[str | None] = mapped_column(
        String(20), nullable=True
    )
    notes: Mapped[str] = mapped_column(Text, default="")
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )


class MaterialFeedback(Base):
    __tablename__ = "material_feedback"

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid.uuid4())
    )
    user_id: Mapped[str] = mapped_column(ForeignKey("users.id"), index=True)
    material_id: Mapped[str] = mapped_column(ForeignKey("materials.id"), index=True)
    card_id: Mapped[str | None] = mapped_column(String(36), nullable=True)
    step_index: Mapped[int | None] = mapped_column(Integer, nullable=True)
    feedback_type: Mapped[str] = mapped_column(String(20))
    # approve, flag, comment
    comment: Mapped[str | None] = mapped_column(Text, nullable=True)
    resolution: Mapped[str | None] = mapped_column(String(20), nullable=True)
    # pending, regenerated, expanded, edited, dismissed
    resolved_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
```

- [ ] **Step 4: Update conftest.py imports**

Add to `tests/conftest.py`:
```python
from app.models.progress import TrainingSession, SessionTopic, MaterialFeedback  # noqa
```

- [ ] **Step 5: Run test — should pass**

Run: `cd learn-anything-app && uv run pytest tests/integration/test_models/test_progress.py -v`
Expected: PASS

- [ ] **Step 6: Commit**

```bash
git commit -m "feat: progress models — TrainingSession, SessionTopic, MaterialFeedback"
```

---

### Task 2: Training Service — Session Lifecycle + LLM Streaming

**Files:**
- Create: `learn-anything-app/app/services/training.py`
- Test: `learn-anything-app/tests/test_services/test_training.py`

The training service manages session lifecycle: creation, message processing, LLM streaming, content tab decisions, and session closing. It bridges the Train routes to the LLM and database.

- [ ] **Step 1: Write failing test for training service**

```python
# tests/test_services/test_training.py
import pytest
import json
from app.services.training import TrainingService, SessionState


def test_session_state_initialization():
    state = SessionState(
        session_id="sess-1",
        user_id="user-1",
        skill_slug="jazz-piano",
        template="A_concept_intro",
        focus_vertex_ids=["v1", "v2"],
    )
    assert state.session_id == "sess-1"
    assert state.message_count == 0
    assert state.difficulty_zone == "zpd_optimal"
    assert state.active_content_tab == "example"
    assert state.rolling_accuracy is None


def test_session_state_add_message():
    state = SessionState(
        session_id="sess-1",
        user_id="user-1",
        skill_slug="jazz-piano",
        template="A_concept_intro",
        focus_vertex_ids=["v1"],
    )
    state.add_message("user", "What are shell voicings?")
    state.add_message("assistant", "Great question! Shell voicings use...")
    assert state.message_count == 2
    assert state.messages[0]["role"] == "user"
    assert state.messages[1]["role"] == "assistant"


def test_session_state_update_accuracy():
    state = SessionState(
        session_id="sess-1",
        user_id="user-1",
        skill_slug="jazz-piano",
        template="C_skill_drill",
        focus_vertex_ids=["v1"],
    )
    state.record_assessment("v1", accuracy=0.8, bloom="apply")
    state.record_assessment("v1", accuracy=0.9, bloom="apply")
    state.record_assessment("v1", accuracy=0.7, bloom="analyze")
    assert state.rolling_accuracy == pytest.approx(0.8, abs=0.01)


def test_session_state_to_db_record():
    state = SessionState(
        session_id="sess-1",
        user_id="user-1",
        skill_slug="jazz-piano",
        template="A_concept_intro",
        focus_vertex_ids=["v1", "v2"],
    )
    state.difficulty_zone = "mastery"
    record = state.to_db_record()
    assert record["template_used"] == "A_concept_intro"
    assert record["focus_vertex_ids"] == '["v1", "v2"]'
    assert record["difficulty_zone_end"] == "mastery"
```

- [ ] **Step 2: Run test — should fail**

Run: `cd learn-anything-app && uv run pytest tests/test_services/test_training.py -v`
Expected: FAIL — `ModuleNotFoundError`

- [ ] **Step 3: Implement training service**

```python
# app/services/training.py
import json
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import AsyncIterator

from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.progress import TrainingSession, SessionTopic
from app.models.learner_state import LearnerState
from app.models.graph_nodes import SkillNode


@dataclass
class AssessmentRecord:
    vertex_id: str
    accuracy: float
    bloom_level: str
    timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc))


@dataclass
class SessionState:
    session_id: str
    user_id: str
    skill_slug: str
    template: str
    focus_vertex_ids: list[str]
    difficulty_zone: str = "zpd_optimal"
    active_content_tab: str = "example"
    rolling_accuracy: float | None = None
    scaffold_level: int = 2
    message_count: int = 0
    messages: list[dict] = field(default_factory=list)
    assessments: list[AssessmentRecord] = field(default_factory=list)
    _accuracy_window: list[float] = field(default_factory=list)

    def add_message(self, role: str, content: str) -> None:
        self.messages.append({
            "role": role,
            "content": content,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        })
        self.message_count += 1

    def record_assessment(
        self, vertex_id: str, accuracy: float, bloom: str
    ) -> None:
        self.assessments.append(
            AssessmentRecord(vertex_id=vertex_id, accuracy=accuracy, bloom_level=bloom)
        )
        self._accuracy_window.append(accuracy)
        # Rolling window of last 5 assessments
        if len(self._accuracy_window) > 5:
            self._accuracy_window = self._accuracy_window[-5:]
        self.rolling_accuracy = (
            sum(self._accuracy_window) / len(self._accuracy_window)
        )

    def to_db_record(self) -> dict:
        return {
            "id": self.session_id,
            "user_id": self.user_id,
            "skill_slug": self.skill_slug,
            "template_used": self.template,
            "focus_vertex_ids": json.dumps(self.focus_vertex_ids),
            "difficulty_zone_start": "zpd_optimal",
            "difficulty_zone_end": self.difficulty_zone,
            "rolling_accuracy": self.rolling_accuracy,
            "scaffold_level": self.scaffold_level,
        }


# Active sessions stored in memory (keyed by session_id)
_active_sessions: dict[str, SessionState] = {}


async def create_session(
    db: AsyncSession,
    user_id: str,
    skill_slug: str,
    template: str,
    focus_vertex_ids: list[str],
) -> SessionState:
    """Create a new training session and return its state."""
    # Determine session number
    result = await db.execute(
        select(func.count(TrainingSession.id)).where(
            TrainingSession.user_id == user_id,
            TrainingSession.skill_slug == skill_slug,
        )
    )
    count = result.scalar() or 0

    session_id = str(uuid.uuid4())
    session = TrainingSession(
        id=session_id,
        user_id=user_id,
        skill_slug=skill_slug,
        session_number=count + 1,
        template_used=template,
        focus_vertex_ids=json.dumps(focus_vertex_ids),
    )
    db.add(session)
    await db.commit()

    state = SessionState(
        session_id=session_id,
        user_id=user_id,
        skill_slug=skill_slug,
        template=template,
        focus_vertex_ids=focus_vertex_ids,
    )
    _active_sessions[session_id] = state
    return state


def get_session(session_id: str) -> SessionState | None:
    """Retrieve an active session by ID."""
    return _active_sessions.get(session_id)


async def close_session(
    db: AsyncSession,
    session_id: str,
    summary: str = "",
    duration_minutes: int | None = None,
) -> None:
    """Finalize a training session — write to DB, remove from memory."""
    state = _active_sessions.pop(session_id, None)
    if state is None:
        return

    result = await db.execute(
        select(TrainingSession).where(TrainingSession.id == session_id)
    )
    session = result.scalar_one_or_none()
    if session is None:
        return

    session.session_summary = summary
    session.duration_minutes = duration_minutes
    session.difficulty_zone_end = state.difficulty_zone
    session.rolling_accuracy = state.rolling_accuracy
    session.scaffold_level = state.scaffold_level
    session.ended_at = datetime.now(timezone.utc)

    # Write per-topic records
    for assessment in state.assessments:
        topic = SessionTopic(
            session_id=session_id,
            vertex_id=assessment.vertex_id,
            vertex_name=assessment.vertex_id,  # Resolved by caller
            activity_type="assessment",
            accuracy=assessment.accuracy,
            bloom_level_demonstrated=assessment.bloom_level,
        )
        db.add(topic)

    await db.commit()


def build_system_prompt(state: SessionState, learner_context: dict) -> str:
    """Build the LLM system prompt for a training session.

    The system prompt instructs the LLM to act as the training conductor:
    - Adopt the instructor persona
    - Follow the session template
    - Use the escalation ladder (Pump -> Hint -> Prompt -> Assertion)
    - Include content-push directives as structured JSON in its responses
    """
    template_descriptions = {
        "A_concept_intro": "Concept Introduction: Activate prior knowledge, elicit preconceptions, guided discovery through Socratic questioning, consolidation.",
        "B_retrieval_review": "Retrieval Practice: Cued recall, elaborative 'why' questions, interleaved novel application, confidence calibration.",
        "C_skill_drill": "Skill Drilling: Worked example, guided drill with fading scaffolding, independent drill, error analysis.",
        "D_productive_failure": "Productive Failure: Present challenge with NO guidance (only pumps), acknowledge impasse, consolidate with direct instruction, transfer.",
        "E_mastery_gate": "Mastery Gate Assessment: Cold recall, application under novelty, explain-to-teach. All three must pass to advance.",
        "F_mentor_conversation": "Mentor Conversation: Open exploration and discussion. Follow the learner's curiosity while subtly guiding toward productive territory.",
    }

    persona = learner_context.get("instructor_persona", "a skilled, encouraging tutor")
    identity_frame = learner_context.get("identity_frame", "")
    template_desc = template_descriptions.get(
        state.template, "Adaptive teaching session."
    )

    return f"""You are {persona}, conducting a training session.

SESSION TEMPLATE: {state.template}
{template_desc}

FOCUS VERTICES: {', '.join(state.focus_vertex_ids)}
CURRENT DIFFICULTY ZONE: {state.difficulty_zone}
SCAFFOLD LEVEL: {state.scaffold_level} (1=open-ended, 4=direct instruction)
{"IDENTITY FRAME: " + identity_frame if identity_frame else ""}

RULES:
- Never give answers too quickly. Use the escalation ladder: Pump -> Hint -> Prompt -> Assertion.
- Exhaust each level before escalating. Reset to Pump after every correct response.
- Include at least one question for every 3 sentences of explanation.
- Maximum explanation length: 150 words before requiring learner interaction.
- Adjust difficulty ONLY based on performance data, not emotional appeals.
- Never begin agreement with an answer unless it's fully correct.

CONTENT DIRECTIVES:
When you want to show content on the right panel, include a JSON directive at the END of your message on its own line:
{{"content_push": {{"tab": "<tab_type>", "data": {{...}}}}}}

Tab types and their data shapes:
- "example": {{"title": "...", "steps": [{{"label": "...", "content": "...", "visible": true/false}}], "fading_level": 0-3}}
- "diagram": {{"title": "...", "svg_content": "...", "caption": "..."}}
- "graph": {{"focus_ids": ["..."], "highlight_edges": true}}
- "video": {{"youtube_id": "...", "title": "...", "annotations": [{{"time_seconds": N, "text": "..."}}]}}
- "flashcards": {{"cards": [{{"front": "...", "back": "...", "bloom_level": "..."}}]}}

ASSESSMENT RECORDING:
When you observe learner performance, include an assessment directive:
{{"assessment": {{"vertex_id": "...", "accuracy": 0.0-1.0, "bloom_level": "...", "notes": "..."}}}}

Only include directives when pedagogically appropriate. Most messages should be pure conversation."""


def _find_json_object(text: str, start_key: str) -> dict | None:
    """Extract a JSON object containing `start_key` using brace-counting.

    More robust than regex for nested/multiline JSON directives.
    """
    idx = text.find(f'"{start_key}"')
    if idx == -1:
        return None
    brace_start = text.rfind('{', 0, idx)
    if brace_start == -1:
        return None
    depth = 0
    for i, c in enumerate(text[brace_start:], brace_start):
        if c == '{':
            depth += 1
        elif c == '}':
            depth -= 1
        if depth == 0:
            try:
                return json.loads(text[brace_start:i + 1])
            except json.JSONDecodeError:
                return None
    return None


def _find_all_json_objects(text: str, start_key: str) -> list[dict]:
    """Find all JSON objects containing `start_key` in text."""
    results = []
    search_from = 0
    while True:
        idx = text.find(f'"{start_key}"', search_from)
        if idx == -1:
            break
        brace_start = text.rfind('{', 0, idx)
        if brace_start == -1:
            search_from = idx + 1
            continue
        depth = 0
        found = False
        for i, c in enumerate(text[brace_start:], brace_start):
            if c == '{':
                depth += 1
            elif c == '}':
                depth -= 1
            if depth == 0:
                try:
                    obj = json.loads(text[brace_start:i + 1])
                    results.append(obj)
                except json.JSONDecodeError:
                    pass
                search_from = i + 1
                found = True
                break
        if not found:
            break
    return results


async def stream_chat_response(
    state: SessionState,
    user_message: str,
    llm_provider,
) -> AsyncIterator[str]:
    """Stream LLM response tokens for the chat panel.

    Yields individual tokens/chunks as they arrive from the LLM.
    Consumes `LLMStreamEvent` objects from Plan 3's `LLMProvider`.
    Content-push directives are extracted from the completed response
    and yielded as separate tagged events so the route layer can push
    them to different Datastar targets.
    """
    state.add_message("user", user_message)

    messages = [{"role": m["role"], "content": m["content"]} for m in state.messages]

    buffer = ""
    async for event in llm_provider.stream(messages):
        token = event.text if hasattr(event, 'text') else event.get("text", "")
        buffer += token

        # Check for content-push directive at end of buffer
        if '{"content_push"' in buffer or '{"assessment"' in buffer:
            # Don't yield directive tokens to chat — they'll be extracted
            # after the full message is assembled
            continue

        yield token

    # Extract and process any directives from the full response
    state.add_message("assistant", buffer)

    # Parse content_push directives using brace-counting parser
    for directive in _find_all_json_objects(buffer, "content_push"):
        try:
            tab = directive["content_push"]["tab"]
            state.active_content_tab = tab
            yield f"\n__CONTENT_PUSH__{json.dumps(directive)}"
        except KeyError:
            pass

    # Parse assessment directives using brace-counting parser
    for directive in _find_all_json_objects(buffer, "assessment"):
        try:
            a = directive["assessment"]
            state.record_assessment(
                vertex_id=a["vertex_id"],
                accuracy=a["accuracy"],
                bloom=a["bloom_level"],
            )
            yield f"\n__ASSESSMENT__{json.dumps(directive)}"
        except KeyError:
            pass
```

- [ ] **Step 4: Run test — should pass**

Run: `cd learn-anything-app && uv run pytest tests/test_services/test_training.py -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git commit -m "feat: training service — session lifecycle, LLM prompt building, streaming"
```

---

### Task 3: Metrics Service — Progress Computation for Both Backends

**Files:**
- Create: `learn-anything-app/app/services/metrics.py`
- Test: `learn-anything-app/tests/test_services/test_metrics.py`

Computes learning-focused metrics for the Progress dashboard. PG backend uses rich SQL/AGE aggregate queries. JSON backend computes simplified metrics from in-memory state.

- [ ] **Step 1: Write failing test for metrics service**

```python
# tests/test_services/test_metrics.py
import pytest
from datetime import datetime, timezone, timedelta
from app.services.metrics import (
    compute_retention_rate,
    compute_mastery_transitions,
    compute_curriculum_velocity,
    compute_coverage_over_time,
    ProgressMetrics,
)


def test_compute_retention_rate_perfect():
    """All retrieval probes correct = 100% retention."""
    probes = [
        {"vertex_id": "v1", "result": "correct", "days_since": 3},
        {"vertex_id": "v2", "result": "correct", "days_since": 7},
        {"vertex_id": "v3", "result": "correct", "days_since": 14},
    ]
    rate = compute_retention_rate(probes)
    assert rate == 1.0


def test_compute_retention_rate_mixed():
    """Mixed results weighted by delay."""
    probes = [
        {"vertex_id": "v1", "result": "correct", "days_since": 7},
        {"vertex_id": "v2", "result": "incorrect", "days_since": 7},
        {"vertex_id": "v3", "result": "partial", "days_since": 3},
    ]
    rate = compute_retention_rate(probes)
    # correct=1.0, incorrect=0.0, partial=0.5 -> (1.0+0.0+0.5)/3 = 0.5
    assert rate == pytest.approx(0.5, abs=0.01)


def test_compute_retention_rate_empty():
    rate = compute_retention_rate([])
    assert rate is None


def test_compute_mastery_transitions():
    """Count real mastery state changes."""
    transitions = [
        {"from_state": "not_started", "to_state": "attempted"},
        {"from_state": "attempted", "to_state": "familiar"},
        {"from_state": "familiar", "to_state": "proficient"},
        {"from_state": "proficient", "to_state": "familiar"},  # Regression
    ]
    result = compute_mastery_transitions(transitions)
    assert result["forward"] == 3
    assert result["backward"] == 1
    assert result["net"] == 2


def test_compute_curriculum_velocity():
    """Task classes completed per week."""
    sessions = [
        {
            "date": (datetime.now(timezone.utc) - timedelta(days=12)).isoformat(),
            "task_class_completed": True,
        },
        {
            "date": (datetime.now(timezone.utc) - timedelta(days=5)).isoformat(),
            "task_class_completed": True,
        },
        {
            "date": (datetime.now(timezone.utc) - timedelta(days=2)).isoformat(),
            "task_class_completed": False,
        },
    ]
    velocity = compute_curriculum_velocity(sessions)
    # 2 task classes completed over ~2 weeks = ~1.0 per week
    assert velocity > 0


def test_compute_coverage_over_time():
    """Coverage snapshots at different points."""
    snapshots = [
        {"date": "2026-03-01", "total_vertices": 20, "coverage": 0.0},
        {"date": "2026-03-08", "total_vertices": 20, "coverage": 0.15},
        {"date": "2026-03-15", "total_vertices": 20, "coverage": 0.35},
        {"date": "2026-03-22", "total_vertices": 20, "coverage": 0.50},
    ]
    result = compute_coverage_over_time(snapshots)
    assert len(result) == 4
    assert result[-1]["coverage"] == 0.50
```

- [ ] **Step 2: Run test — should fail**

Run: `cd learn-anything-app && uv run pytest tests/test_services/test_metrics.py -v`
Expected: FAIL — `ModuleNotFoundError`

- [ ] **Step 3: Implement metrics service**

```python
# app/services/metrics.py
from dataclasses import dataclass
from datetime import datetime, timezone, timedelta
from typing import Any

from sqlalchemy import select, func, case
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.progress import TrainingSession, SessionTopic
from app.models.learner_state import LearnerState, MasteryTransition
from app.models.graph_nodes import SkillNode, Concept


MASTERY_ORDER = ["not_started", "attempted", "familiar", "proficient", "mastered"]


@dataclass
class ProgressMetrics:
    delayed_retention_rate: float | None
    transfer_task_success: float | None
    mastery_transitions_forward: int
    mastery_transitions_backward: int
    mastery_transitions_net: int
    calibration_accuracy: float | None
    curriculum_velocity: float | None
    total_vertices: int
    coverage_by_category: dict[str, int]
    coverage_percentage: float
    identity_frame: str
    sessions_completed: int
    current_task_class: str | None
    plateau_status: str | None


def compute_retention_rate(probes: list[dict]) -> float | None:
    """Compute delayed retention rate from retrieval probe results.

    Only counts probes with >= 1 day delay (delayed recall, not immediate).
    Partial credit: correct=1.0, partial=0.5, incorrect=0.0
    """
    if not probes:
        return None
    scores = []
    for p in probes:
        result = p.get("result", "incorrect")
        if result == "correct":
            scores.append(1.0)
        elif result == "partial":
            scores.append(0.5)
        else:
            scores.append(0.0)
    return sum(scores) / len(scores)


def compute_mastery_transitions(transitions: list[dict]) -> dict[str, int]:
    """Count forward and backward mastery transitions."""
    forward = 0
    backward = 0
    for t in transitions:
        from_idx = MASTERY_ORDER.index(t["from_state"]) if t["from_state"] in MASTERY_ORDER else 0
        to_idx = MASTERY_ORDER.index(t["to_state"]) if t["to_state"] in MASTERY_ORDER else 0
        if to_idx > from_idx:
            forward += 1
        elif to_idx < from_idx:
            backward += 1
    return {"forward": forward, "backward": backward, "net": forward - backward}


def compute_curriculum_velocity(sessions: list[dict]) -> float | None:
    """Compute task classes completed per week."""
    if not sessions:
        return None
    completed = [s for s in sessions if s.get("task_class_completed")]
    if not completed:
        return 0.0
    dates = []
    for s in sessions:
        d = s.get("date", "")
        if isinstance(d, str) and d:
            try:
                dates.append(datetime.fromisoformat(d))
            except ValueError:
                pass
    if len(dates) < 2:
        return float(len(completed))
    span_days = (max(dates) - min(dates)).days
    if span_days == 0:
        return float(len(completed))
    weeks = span_days / 7.0
    return len(completed) / weeks


def compute_coverage_over_time(
    snapshots: list[dict],
) -> list[dict]:
    """Return coverage snapshots as-is for charting."""
    return snapshots


async def compute_progress_metrics_pg(
    db: AsyncSession,
    user_id: str,
    skill_slug: str,
    learning_plan: dict,
) -> ProgressMetrics:
    """Compute full progress metrics using PostgreSQL aggregate queries.

    This is the rich version — cross-skill transfer detection, graph
    traversal, time-series aggregates.
    """
    # Count sessions
    session_count_result = await db.execute(
        select(func.count(TrainingSession.id)).where(
            TrainingSession.user_id == user_id,
            TrainingSession.skill_slug == skill_slug,
        )
    )
    sessions_completed = session_count_result.scalar() or 0

    # Get mastery transitions
    transition_result = await db.execute(
        select(MasteryTransition).where(
            MasteryTransition.user_id == user_id,
        ).order_by(MasteryTransition.timestamp)
    )
    transitions = [
        {"from_state": t.from_state, "to_state": t.to_state}
        for t in transition_result.scalars().all()
    ]
    transition_counts = compute_mastery_transitions(transitions)

    # Coverage by category
    state_result = await db.execute(
        select(
            LearnerState.mastery_category,
            func.count(LearnerState.id),
        )
        .where(LearnerState.user_id == user_id)
        .group_by(LearnerState.mastery_category)
    )
    coverage_by_category = {cat: 0 for cat in MASTERY_ORDER}
    total_vertices = 0
    for category, count in state_result.all():
        coverage_by_category[category] = count
        total_vertices += count

    # Weighted coverage
    coverage_pct = 0.0
    if total_vertices > 0:
        weighted_result = await db.execute(
            select(func.avg(LearnerState.mastery_probability)).where(
                LearnerState.user_id == user_id,
            )
        )
        coverage_pct = weighted_result.scalar() or 0.0

    # Identity frame and curriculum position from learning plan
    identity_frame = learning_plan.get("motivation_architecture", {}).get(
        "identity_frame", ""
    )
    curriculum = learning_plan.get("curriculum", {})
    task_classes = curriculum.get("task_classes", [])
    current_task_class = task_classes[0]["name"] if task_classes else None

    return ProgressMetrics(
        delayed_retention_rate=None,  # Computed from retrieval probes in sessions
        transfer_task_success=None,  # Computed from mastery gate results
        mastery_transitions_forward=transition_counts["forward"],
        mastery_transitions_backward=transition_counts["backward"],
        mastery_transitions_net=transition_counts["net"],
        calibration_accuracy=None,  # Requires comparison of predictions vs outcomes
        curriculum_velocity=None,  # Requires session date analysis
        total_vertices=total_vertices,
        coverage_by_category=coverage_by_category,
        coverage_percentage=coverage_pct,
        identity_frame=identity_frame,
        sessions_completed=sessions_completed,
        current_task_class=current_task_class,
        plateau_status=None,
    )


def compute_progress_metrics_json(
    progress_data: dict,
    knowledge_graph: dict,
    learning_plan: dict,
) -> ProgressMetrics:
    """Compute simplified progress metrics from JSON state files.

    No cross-skill transfer, no graph traversal. Single-skill only.
    """
    sessions = progress_data.get("sessions", [])
    vertices = knowledge_graph.get("graph", {}).get("vertices", [])

    # Coverage by category
    coverage_by_category = {cat: 0 for cat in MASTERY_ORDER}
    for v in vertices:
        ls = v.get("learner_state", {})
        cat = ls.get("mastery_category", "not_started")
        coverage_by_category[cat] = coverage_by_category.get(cat, 0) + 1

    total_vertices = len(vertices)
    coverage_pct = 0.0
    if total_vertices > 0:
        coverage_pct = sum(
            v.get("learner_state", {}).get("mastery_probability", 0.0)
            for v in vertices
        ) / total_vertices

    # Mastery transitions from log
    transition_log = progress_data.get("mastery_transition_log", [])
    transitions = [
        {"from_state": t["from_state"], "to_state": t["to_state"]}
        for t in transition_log
    ]
    transition_counts = compute_mastery_transitions(transitions)

    # Retention from session retrieval probes
    all_probes = []
    for s in sessions:
        for p in s.get("retrieval_probe_results", []):
            all_probes.append({
                "vertex_id": p.get("vertex_id"),
                "result": p.get("result", "incorrect"),
                "days_since": p.get("days_since_last_review", 0),
            })
    retention = compute_retention_rate(
        [p for p in all_probes if p.get("days_since", 0) >= 1]
    )

    # Identity frame
    identity_frame = learning_plan.get("motivation_architecture", {}).get(
        "identity_frame", ""
    )

    # Current position
    current_state = progress_data.get("current_state", {})
    pos = current_state.get("curriculum_position", {})
    plateau = current_state.get("motivation_state", {}).get("plateau_status")

    return ProgressMetrics(
        delayed_retention_rate=retention,
        transfer_task_success=None,
        mastery_transitions_forward=transition_counts["forward"],
        mastery_transitions_backward=transition_counts["backward"],
        mastery_transitions_net=transition_counts["net"],
        calibration_accuracy=None,
        curriculum_velocity=compute_curriculum_velocity(
            [
                {
                    "date": s.get("date"),
                    "task_class_completed": s.get("task_class_completed", False),
                }
                for s in sessions
            ]
        ),
        total_vertices=total_vertices,
        coverage_by_category=coverage_by_category,
        coverage_percentage=coverage_pct,
        identity_frame=identity_frame,
        sessions_completed=len(sessions),
        current_task_class=pos.get("task_class_name"),
        plateau_status=plateau,
    )
```

- [ ] **Step 4: Run test — should pass**

Run: `cd learn-anything-app && uv run pytest tests/test_services/test_metrics.py -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git commit -m "feat: metrics service — retention rate, mastery transitions, curriculum velocity, dual backends"
```

---

### Task 4: Split Panel JS — Resizable Draggable Divider

**Files:**
- Create: `learn-anything-app/static/js/split-panel.js`

Vanilla JS, no dependencies. The split panel stores its ratio in a Datastar signal so the server can read it if needed. Desktop: draggable vertical divider. Mobile: full-width panels with tab switching.

- [ ] **Step 1: Create split panel JavaScript**

```javascript
// static/js/split-panel.js
//
// Resizable split panel for Train mode.
// Default: 30% left (chat), 70% right (content).
// Stores ratio in Datastar signal `$split_ratio`.
// Mobile (<768px): single panel with tab toggle.

(function () {
  "use strict";

  const MIN_RATIO = 0.15;
  const MAX_RATIO = 0.60;
  const DEFAULT_RATIO = 0.30;
  const MOBILE_BREAKPOINT = 768;

  let isDragging = false;
  let container = null;
  let divider = null;
  let leftPanel = null;
  let rightPanel = null;

  function getStoredRatio() {
    try {
      const stored = localStorage.getItem("la-split-ratio");
      if (stored) {
        const val = parseFloat(stored);
        if (val >= MIN_RATIO && val <= MAX_RATIO) return val;
      }
    } catch (e) {
      // localStorage unavailable
    }
    return DEFAULT_RATIO;
  }

  function setRatio(ratio) {
    ratio = Math.max(MIN_RATIO, Math.min(MAX_RATIO, ratio));
    leftPanel.style.width = (ratio * 100) + "%";
    rightPanel.style.width = ((1 - ratio) * 100) + "%";

    try {
      localStorage.setItem("la-split-ratio", ratio.toString());
    } catch (e) {
      // ignore
    }

    // Update Datastar signal if available
    if (window.__ds && window.__ds.signals) {
      window.__ds.signals.split_ratio = ratio;
    }
  }

  function onMouseDown(e) {
    if (window.innerWidth < MOBILE_BREAKPOINT) return;
    isDragging = true;
    document.body.style.cursor = "col-resize";
    document.body.style.userSelect = "none";
    e.preventDefault();
  }

  function onMouseMove(e) {
    if (!isDragging || !container) return;
    const rect = container.getBoundingClientRect();
    const ratio = (e.clientX - rect.left) / rect.width;
    setRatio(ratio);
  }

  function onMouseUp() {
    if (!isDragging) return;
    isDragging = false;
    document.body.style.cursor = "";
    document.body.style.userSelect = "";
  }

  // Touch support for tablets
  function onTouchStart(e) {
    if (window.innerWidth < MOBILE_BREAKPOINT) return;
    isDragging = true;
    e.preventDefault();
  }

  function onTouchMove(e) {
    if (!isDragging || !container) return;
    const touch = e.touches[0];
    const rect = container.getBoundingClientRect();
    const ratio = (touch.clientX - rect.left) / rect.width;
    setRatio(ratio);
  }

  function onTouchEnd() {
    isDragging = false;
  }

  function handleResize() {
    if (window.innerWidth < MOBILE_BREAKPOINT) {
      // Mobile: remove inline widths, CSS handles full-width
      if (leftPanel) leftPanel.style.width = "";
      if (rightPanel) rightPanel.style.width = "";
    } else {
      // Desktop: restore ratio
      setRatio(getStoredRatio());
    }
  }

  function init() {
    container = document.getElementById("train-split");
    if (!container) return;

    divider = container.querySelector(".split-divider");
    leftPanel = container.querySelector(".split-left");
    rightPanel = container.querySelector(".split-right");

    if (!divider || !leftPanel || !rightPanel) return;

    // Set initial ratio
    if (window.innerWidth >= MOBILE_BREAKPOINT) {
      setRatio(getStoredRatio());
    }

    // Mouse events
    divider.addEventListener("mousedown", onMouseDown);
    document.addEventListener("mousemove", onMouseMove);
    document.addEventListener("mouseup", onMouseUp);

    // Touch events
    divider.addEventListener("touchstart", onTouchStart, { passive: false });
    document.addEventListener("touchmove", onTouchMove, { passive: false });
    document.addEventListener("touchend", onTouchEnd);

    // Responsive
    window.addEventListener("resize", handleResize);

    // Double-click to reset
    divider.addEventListener("dblclick", function () {
      setRatio(DEFAULT_RATIO);
    });
  }

  // Initialize when DOM is ready
  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", init);
  } else {
    init();
  }

  // Re-init if Datastar morphs the page (new train page loaded)
  const observer = new MutationObserver(function () {
    if (!document.getElementById("train-split")) return;
    if (!container || !document.body.contains(container)) {
      init();
    }
  });
  observer.observe(document.body, { childList: true, subtree: true });
})();
```

- [ ] **Step 2: Visual test**

Open the Train mode page in browser, verify:
- Divider is visible and styled (thin gold line with hover effect)
- Dragging left/right resizes panels smoothly
- Ratio persists across page reloads
- Double-click resets to 30/70
- Below 768px width, panels stack vertically

- [ ] **Step 3: Commit**

```bash
git commit -m "feat: split-panel.js — resizable draggable divider with mobile fallback"
```

---

### Task 5: Voice Input JS — Web Speech API Integration

**Files:**
- Create: `learn-anything-app/static/js/voice.js`

Web Speech API for speech-to-text. Mic button primary, text fallback always available. Transcription is sent to the server via the same `@post()` as typed text.

- [ ] **Step 1: Create voice input JavaScript**

```javascript
// static/js/voice.js
//
// Web Speech API integration for Train mode.
// Provides a mic button that captures speech and fills the input field.
// Falls back gracefully when Speech API is unavailable.

(function () {
  "use strict";

  let recognition = null;
  let isListening = false;
  let micButton = null;
  let inputField = null;
  let statusIndicator = null;

  const SpeechRecognition =
    window.SpeechRecognition || window.webkitSpeechRecognition;

  function isSupported() {
    return !!SpeechRecognition;
  }

  function init() {
    micButton = document.getElementById("voice-mic-btn");
    inputField = document.getElementById("chat-input");
    statusIndicator = document.getElementById("voice-status");

    if (!micButton || !inputField) return;

    if (!isSupported()) {
      micButton.classList.add("voice-unsupported");
      micButton.title = "Voice input not supported in this browser";
      micButton.disabled = true;
      return;
    }

    recognition = new SpeechRecognition();
    recognition.continuous = false;
    recognition.interimResults = true;
    recognition.lang = document.documentElement.lang || "en-US";
    recognition.maxAlternatives = 1;

    recognition.onstart = function () {
      isListening = true;
      micButton.classList.add("voice-active");
      if (statusIndicator) statusIndicator.textContent = "Listening...";
    };

    recognition.onresult = function (event) {
      let interim = "";
      let final = "";

      for (let i = event.resultIndex; i < event.results.length; i++) {
        const transcript = event.results[i][0].transcript;
        if (event.results[i].isFinal) {
          final += transcript;
        } else {
          interim += transcript;
        }
      }

      if (final) {
        // Append final transcript to existing input value
        const current = inputField.value;
        const separator = current && !current.endsWith(" ") ? " " : "";
        inputField.value = current + separator + final;
        // Update Datastar signal
        inputField.dispatchEvent(new Event("input", { bubbles: true }));
      }

      if (statusIndicator) {
        statusIndicator.textContent = interim || (final ? "Done" : "Listening...");
      }
    };

    recognition.onerror = function (event) {
      isListening = false;
      micButton.classList.remove("voice-active");

      if (event.error === "not-allowed") {
        if (statusIndicator) statusIndicator.textContent = "Mic access denied";
      } else if (event.error === "no-speech") {
        if (statusIndicator) statusIndicator.textContent = "No speech detected";
      } else {
        if (statusIndicator) statusIndicator.textContent = "";
      }
    };

    recognition.onend = function () {
      isListening = false;
      micButton.classList.remove("voice-active");
      if (statusIndicator && statusIndicator.textContent === "Listening...") {
        statusIndicator.textContent = "";
      }
    };

    micButton.addEventListener("click", toggleListening);

    // Keyboard shortcut: Ctrl+Shift+M to toggle mic
    document.addEventListener("keydown", function (e) {
      if (e.ctrlKey && e.shiftKey && e.key === "M") {
        e.preventDefault();
        toggleListening();
      }
    });
  }

  function toggleListening() {
    if (!recognition) return;

    if (isListening) {
      recognition.stop();
    } else {
      try {
        recognition.start();
      } catch (e) {
        // Already started — ignore
      }
    }
  }

  // Initialize
  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", init);
  } else {
    init();
  }

  // Re-init on Datastar morph
  const observer = new MutationObserver(function () {
    if (
      document.getElementById("voice-mic-btn") &&
      (!micButton || !document.body.contains(micButton))
    ) {
      init();
    }
  });
  observer.observe(document.body, { childList: true, subtree: true });
})();
```

- [ ] **Step 2: Visual test**

Open Train mode in Chrome/Edge (Speech API supported):
- Mic button appears and is clickable
- Clicking starts listening (button pulses gold)
- Speaking fills the text input
- Clicking again or silence stops listening
- In Firefox/Safari: mic button shows as disabled with tooltip

- [ ] **Step 3: Commit**

```bash
git commit -m "feat: voice.js — Web Speech API mic input with graceful fallback"
```

---

### Task 6: Observatory CSS — Train, Materials, Progress Styles

**Files:**
- Modify: `learn-anything-app/static/css/observatory.css`

Extends the existing Observatory CSS foundation from Plan 1 with styles for all three new modes, plus mobile-responsive rules and the nebula background fallback.

- [ ] **Step 1: Add Train mode styles to observatory.css**

Append to `learn-anything-app/static/css/observatory.css`:

```css
/* ==========================================================================
   TRAIN MODE
   ========================================================================== */

.train-layout {
  display: flex;
  height: calc(100vh - 56px); /* Below nav bar */
  overflow: hidden;
}

/* Split panel */
#train-split {
  display: flex;
  width: 100%;
  height: 100%;
  position: relative;
}

.split-left {
  height: 100%;
  overflow-y: auto;
  display: flex;
  flex-direction: column;
  background: var(--deep);
  border-right: 1px solid var(--border);
}

.split-right {
  height: 100%;
  overflow-y: auto;
  flex: 1;
  background: var(--void);
}

.split-divider {
  width: 6px;
  cursor: col-resize;
  background: var(--border);
  position: relative;
  flex-shrink: 0;
  transition: background 0.15s;
  z-index: 10;
}

.split-divider:hover,
.split-divider:active {
  background: var(--gold-dim);
}

.split-divider::after {
  content: "";
  position: absolute;
  top: 50%;
  left: 50%;
  transform: translate(-50%, -50%);
  width: 2px;
  height: 32px;
  background: var(--text-dim);
  border-radius: 1px;
}

/* Chat panel */
.chat-panel {
  display: flex;
  flex-direction: column;
  height: 100%;
  padding: 0;
}

.chat-header {
  padding: 12px 16px;
  border-bottom: 1px solid var(--border);
  display: flex;
  align-items: center;
  gap: 10px;
  flex-shrink: 0;
}

.session-template-badge {
  font-family: var(--mono);
  font-size: 11px;
  padding: 3px 8px;
  border-radius: 4px;
  background: var(--surface-light);
  color: var(--gold);
  border: 1px solid var(--border);
  letter-spacing: 0.5px;
}

.chat-messages {
  flex: 1;
  overflow-y: auto;
  padding: 16px;
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.chat-bubble {
  max-width: 85%;
  padding: 10px 14px;
  border-radius: 12px;
  font-size: 14px;
  line-height: 1.5;
  word-break: break-word;
}

.chat-bubble.user {
  align-self: flex-end;
  background: var(--surface-light);
  color: var(--text-bright);
  border-bottom-right-radius: 4px;
}

.chat-bubble.assistant {
  align-self: flex-start;
  background: var(--surface);
  color: var(--text);
  border-bottom-left-radius: 4px;
  border: 1px solid var(--border);
}

.chat-input-area {
  padding: 12px 16px;
  border-top: 1px solid var(--border);
  display: flex;
  align-items: center;
  gap: 8px;
  flex-shrink: 0;
  background: var(--deep);
}

#chat-input {
  flex: 1;
  padding: 10px 14px;
  background: var(--surface);
  border: 1px solid var(--border);
  border-radius: 20px;
  color: var(--text-bright);
  font-family: var(--sans);
  font-size: 14px;
  outline: none;
  transition: border-color 0.15s;
}

#chat-input:focus {
  border-color: var(--gold-dim);
}

#chat-input::placeholder {
  color: var(--text-dim);
}

/* Voice mic button */
#voice-mic-btn {
  width: 40px;
  height: 40px;
  border-radius: 50%;
  border: 1px solid var(--border);
  background: var(--surface);
  color: var(--text);
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
  transition: all 0.15s;
}

#voice-mic-btn:hover {
  border-color: var(--gold-dim);
  color: var(--gold);
}

#voice-mic-btn.voice-active {
  background: var(--gold-dim);
  border-color: var(--gold);
  color: var(--void);
  animation: voice-pulse 1.5s ease-in-out infinite;
}

#voice-mic-btn.voice-unsupported {
  opacity: 0.3;
  cursor: not-allowed;
}

@keyframes voice-pulse {
  0%, 100% { box-shadow: 0 0 0 0 var(--gold-glow); }
  50% { box-shadow: 0 0 0 8px var(--gold-glow); }
}

.chat-send-btn {
  width: 40px;
  height: 40px;
  border-radius: 50%;
  border: none;
  background: linear-gradient(135deg, var(--gold-dim), var(--gold));
  color: var(--void);
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
}

#voice-status {
  font-size: 11px;
  color: var(--gold);
  font-family: var(--mono);
  min-height: 14px;
  padding: 0 16px 4px;
}

/* Content panel */
.content-panel {
  display: flex;
  flex-direction: column;
  height: 100%;
}

.content-tabs {
  display: flex;
  padding: 0 16px;
  border-bottom: 1px solid var(--border);
  gap: 0;
  flex-shrink: 0;
  overflow-x: auto;
}

.content-tab {
  padding: 10px 16px;
  font-family: var(--mono);
  font-size: 11px;
  letter-spacing: 0.5px;
  text-transform: uppercase;
  color: var(--text-dim);
  border-bottom: 2px solid transparent;
  cursor: pointer;
  white-space: nowrap;
  transition: all 0.15s;
  background: none;
  border-top: none;
  border-left: none;
  border-right: none;
}

.content-tab:hover {
  color: var(--text);
}

.content-tab.active {
  color: var(--gold);
  border-bottom-color: var(--gold);
}

.content-body {
  flex: 1;
  overflow-y: auto;
  padding: 24px;
}

/* Worked example with backward fading */
.worked-example {
  max-width: 720px;
}

.worked-example h3 {
  margin-bottom: 16px;
}

.example-step {
  padding: 12px 16px;
  margin-bottom: 8px;
  background: var(--surface);
  border: 1px solid var(--border);
  border-radius: 8px;
  transition: opacity 0.3s, filter 0.3s;
}

.example-step .step-label {
  font-family: var(--mono);
  font-size: 11px;
  color: var(--text-dim);
  margin-bottom: 4px;
}

.example-step .step-content {
  font-size: 14px;
  color: var(--text);
  line-height: 1.6;
}

.example-step.faded {
  opacity: 0.15;
  filter: blur(4px);
  cursor: pointer;
}

.example-step.faded:hover {
  opacity: 0.5;
  filter: blur(1px);
}

/* Video embed */
.video-container {
  position: relative;
  max-width: 720px;
}

.video-embed {
  width: 100%;
  aspect-ratio: 16 / 9;
  border-radius: 8px;
  border: 1px solid var(--border);
}

.video-annotations {
  margin-top: 12px;
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.video-annotation {
  display: flex;
  gap: 10px;
  padding: 8px 12px;
  background: var(--surface);
  border-radius: 6px;
  font-size: 13px;
  cursor: pointer;
}

.video-annotation:hover {
  background: var(--surface-light);
}

.video-annotation .ann-time {
  font-family: var(--mono);
  color: var(--gold);
  min-width: 50px;
}

/* Mini knowledge graph in train */
.mini-graph-container {
  height: 300px;
  border: 1px solid var(--border);
  border-radius: 8px;
  overflow: hidden;
}

/* Flashcard review */
.flashcard-review {
  max-width: 520px;
  margin: 0 auto;
}

.flashcard {
  background: var(--surface);
  border: 1px solid var(--border);
  border-radius: 12px;
  padding: 32px;
  text-align: center;
  min-height: 200px;
  display: flex;
  flex-direction: column;
  justify-content: center;
  cursor: pointer;
  transition: border-color 0.15s;
}

.flashcard:hover {
  border-color: var(--border-glow);
}

.flashcard .card-face {
  font-size: 16px;
  line-height: 1.6;
  color: var(--text-bright);
}

.flashcard .card-bloom {
  font-family: var(--mono);
  font-size: 10px;
  color: var(--text-dim);
  margin-top: 16px;
  text-transform: uppercase;
  letter-spacing: 1px;
}

.flashcard-nav {
  display: flex;
  justify-content: center;
  gap: 12px;
  margin-top: 16px;
}

.flashcard-nav button {
  padding: 8px 20px;
  border-radius: 6px;
  border: 1px solid var(--border);
  background: var(--surface);
  color: var(--text);
  font-family: var(--sans);
  font-size: 13px;
  cursor: pointer;
}

.flashcard-nav button:hover {
  border-color: var(--gold-dim);
  color: var(--gold);
}

/* ==========================================================================
   MATERIALS MODE
   ========================================================================== */

.materials-layout {
  padding: 24px;
  max-width: 1200px;
  margin: 0 auto;
}

.materials-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 24px;
  flex-wrap: wrap;
  gap: 12px;
}

.materials-search {
  display: flex;
  gap: 8px;
  flex: 1;
  max-width: 480px;
}

.materials-search input {
  flex: 1;
  padding: 10px 14px;
  background: var(--surface);
  border: 1px solid var(--border);
  border-radius: 8px;
  color: var(--text-bright);
  font-family: var(--sans);
  font-size: 14px;
}

.materials-filters {
  display: flex;
  gap: 8px;
  flex-wrap: wrap;
}

.materials-filter-btn {
  padding: 6px 14px;
  border-radius: 20px;
  border: 1px solid var(--border);
  background: var(--surface);
  color: var(--text-dim);
  font-family: var(--sans);
  font-size: 12px;
  cursor: pointer;
  transition: all 0.15s;
}

.materials-filter-btn:hover {
  border-color: var(--text-dim);
  color: var(--text);
}

.materials-filter-btn.active {
  background: var(--surface-light);
  border-color: var(--gold-dim);
  color: var(--gold);
}

.materials-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(320px, 1fr));
  gap: 16px;
}

/* Material card */
.material-card {
  background: var(--surface);
  border: 1px solid var(--border);
  border-radius: 12px;
  padding: 20px;
  transition: border-color 0.15s;
}

.material-card:hover {
  border-color: var(--border-glow);
}

.material-card-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  margin-bottom: 8px;
}

.material-card-title {
  font-family: var(--serif);
  font-size: 16px;
  color: var(--text-bright);
  font-weight: 600;
}

.material-card-type {
  font-family: var(--mono);
  font-size: 10px;
  padding: 2px 8px;
  border-radius: 4px;
  text-transform: uppercase;
  letter-spacing: 0.5px;
  flex-shrink: 0;
}

.material-card-type.flashcard_deck { background: var(--proficient-glow); color: var(--proficient); }
.material-card-type.worked_example { background: var(--familiar-glow); color: var(--familiar); }
.material-card-type.lecture { background: var(--mastered-glow); color: var(--mastered); }
.material-card-type.video { background: rgba(155,142,196,0.2); color: var(--violet); }

.material-card-meta {
  font-size: 12px;
  color: var(--text-dim);
  margin-bottom: 12px;
}

.material-card-content {
  font-size: 13px;
  color: var(--text);
  line-height: 1.5;
  margin-bottom: 12px;
}

/* Feedback controls on material card */
.material-feedback {
  display: flex;
  align-items: center;
  gap: 8px;
  padding-top: 12px;
  border-top: 1px solid var(--border);
}

.feedback-btn {
  width: 32px;
  height: 32px;
  border-radius: 6px;
  border: 1px solid var(--border);
  background: transparent;
  color: var(--text-dim);
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 14px;
  transition: all 0.15s;
}

.feedback-btn:hover {
  border-color: var(--text-dim);
  color: var(--text);
}

.feedback-btn.approved {
  border-color: var(--mastered);
  color: var(--mastered);
  background: var(--mastered-glow);
}

.feedback-btn.flagged {
  border-color: var(--attempted);
  color: var(--attempted);
  background: rgba(240,147,126,0.15);
}

.feedback-comment-btn {
  margin-left: auto;
  padding: 4px 10px;
  border-radius: 4px;
  border: 1px solid var(--border);
  background: transparent;
  color: var(--text-dim);
  font-size: 11px;
  cursor: pointer;
}

/* Quality stats bar */
.quality-stats {
  display: flex;
  gap: 16px;
  padding: 12px 20px;
  background: var(--surface);
  border: 1px solid var(--border);
  border-radius: 8px;
  margin-bottom: 20px;
}

.quality-stat {
  display: flex;
  align-items: center;
  gap: 6px;
}

.quality-stat-count {
  font-family: var(--mono);
  font-size: 16px;
  font-weight: 600;
}

.quality-stat-label {
  font-size: 11px;
  color: var(--text-dim);
  text-transform: uppercase;
  letter-spacing: 0.5px;
}

.quality-stat.approved .quality-stat-count { color: var(--mastered); }
.quality-stat.flagged .quality-stat-count { color: var(--attempted); }
.quality-stat.unreviewed .quality-stat-count { color: var(--text-dim); }

/* Batch action bar */
.batch-actions {
  display: flex;
  gap: 8px;
}

.batch-btn {
  padding: 8px 16px;
  border-radius: 6px;
  border: 1px solid var(--border);
  background: var(--surface);
  color: var(--text);
  font-size: 12px;
  cursor: pointer;
}

.batch-btn:hover {
  border-color: var(--gold-dim);
  color: var(--gold);
}

/* Flag modal */
.feedback-modal-overlay {
  position: fixed;
  inset: 0;
  background: rgba(4, 6, 14, 0.8);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 100;
}

.feedback-modal {
  background: var(--deep);
  border: 1px solid var(--border);
  border-radius: 12px;
  padding: 24px;
  width: 90%;
  max-width: 480px;
}

.feedback-modal h3 {
  margin-bottom: 12px;
}

.feedback-modal textarea {
  width: 100%;
  min-height: 80px;
  padding: 10px 14px;
  background: var(--surface);
  border: 1px solid var(--border);
  border-radius: 8px;
  color: var(--text-bright);
  font-family: var(--sans);
  font-size: 13px;
  resize: vertical;
  margin-bottom: 12px;
}

.feedback-modal-actions {
  display: flex;
  gap: 8px;
  flex-wrap: wrap;
}

.feedback-modal-actions button {
  padding: 8px 16px;
  border-radius: 6px;
  border: 1px solid var(--border);
  background: var(--surface);
  color: var(--text);
  font-size: 12px;
  cursor: pointer;
}

.feedback-modal-actions button.primary {
  background: linear-gradient(135deg, var(--gold-dim), var(--gold));
  border: none;
  color: var(--void);
  font-weight: 600;
}

/* ==========================================================================
   PROGRESS MODE
   ========================================================================== */

.progress-layout {
  padding: 24px;
  max-width: 1000px;
  margin: 0 auto;
}

/* Identity frame hero */
.identity-hero {
  text-align: center;
  padding: 32px 24px;
  margin-bottom: 24px;
}

.identity-hero .identity-text {
  font-family: var(--serif);
  font-size: 24px;
  color: var(--text-bright);
  font-weight: 600;
}

.identity-hero .identity-sub {
  font-size: 13px;
  color: var(--text-dim);
  margin-top: 4px;
}

/* Metrics cards */
.metrics-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(200px, 1fr));
  gap: 16px;
  margin-bottom: 24px;
}

.metric-card {
  background: var(--surface);
  border: 1px solid var(--border);
  border-radius: 12px;
  padding: 20px;
  text-align: center;
}

.metric-card .metric-value {
  font-family: var(--mono);
  font-size: 28px;
  font-weight: 600;
  color: var(--text-bright);
}

.metric-card .metric-label {
  font-size: 11px;
  color: var(--text-dim);
  text-transform: uppercase;
  letter-spacing: 0.5px;
  margin-top: 4px;
}

.metric-card .metric-trend {
  font-size: 11px;
  margin-top: 6px;
}

.metric-card .metric-trend.positive { color: var(--mastered); }
.metric-card .metric-trend.neutral { color: var(--text-dim); }
.metric-card .metric-trend.negative { color: var(--attempted); }

/* Secondary metrics (effort — less prominent) */
.secondary-metrics {
  display: flex;
  gap: 24px;
  margin-bottom: 24px;
  padding: 12px 20px;
  background: var(--surface);
  border: 1px solid var(--border);
  border-radius: 8px;
}

.secondary-metric {
  display: flex;
  align-items: baseline;
  gap: 6px;
  font-size: 12px;
  color: var(--text-dim);
}

.secondary-metric .sec-value {
  font-family: var(--mono);
  font-size: 14px;
  color: var(--text);
}

/* Curriculum roadmap */
.curriculum-roadmap {
  margin-bottom: 24px;
}

.roadmap-track {
  display: flex;
  gap: 0;
  overflow-x: auto;
  padding-bottom: 8px;
}

.roadmap-node {
  display: flex;
  flex-direction: column;
  align-items: center;
  min-width: 120px;
  padding: 12px;
  position: relative;
}

.roadmap-node::after {
  content: "";
  position: absolute;
  top: 26px;
  right: -1px;
  width: calc(100% - 40px);
  height: 2px;
  background: var(--border);
  left: calc(50% + 20px);
}

.roadmap-node:last-child::after {
  display: none;
}

.roadmap-dot {
  width: 20px;
  height: 20px;
  border-radius: 50%;
  border: 2px solid var(--border);
  margin-bottom: 8px;
  z-index: 1;
}

.roadmap-node.completed .roadmap-dot {
  background: var(--mastered);
  border-color: var(--mastered);
}

.roadmap-node.current .roadmap-dot {
  background: var(--gold);
  border-color: var(--gold);
  box-shadow: 0 0 12px var(--gold-glow);
}

.roadmap-node.upcoming .roadmap-dot {
  background: var(--surface);
  border-color: var(--border);
}

.roadmap-node.plateau .roadmap-dot {
  background: var(--familiar);
  border-color: var(--familiar);
  animation: plateau-breathe 3s ease-in-out infinite;
}

@keyframes plateau-breathe {
  0%, 100% { box-shadow: 0 0 0 0 var(--familiar-glow); }
  50% { box-shadow: 0 0 8px 4px var(--familiar-glow); }
}

.roadmap-label {
  font-size: 11px;
  color: var(--text-dim);
  text-align: center;
  max-width: 100px;
}

.roadmap-node.current .roadmap-label {
  color: var(--gold);
  font-weight: 500;
}

/* Mastery gate indicators */
.roadmap-gate {
  font-family: var(--mono);
  font-size: 9px;
  color: var(--violet);
  background: rgba(155, 142, 196, 0.15);
  padding: 1px 6px;
  border-radius: 3px;
  margin-top: 4px;
}

/* Session history */
.session-history {
  margin-bottom: 24px;
}

.session-list {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.session-item {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 12px 16px;
  background: var(--surface);
  border: 1px solid var(--border);
  border-radius: 8px;
}

.session-item .session-template {
  font-family: var(--mono);
  font-size: 11px;
  padding: 3px 8px;
  border-radius: 4px;
  background: var(--surface-light);
  color: var(--gold);
  min-width: 60px;
  text-align: center;
}

.session-item .session-date {
  font-family: var(--mono);
  font-size: 11px;
  color: var(--text-dim);
  min-width: 80px;
}

.session-item .session-summary {
  font-size: 13px;
  color: var(--text);
  flex: 1;
}

.session-item .session-accuracy {
  font-family: var(--mono);
  font-size: 13px;
}

/* Coverage chart container */
.coverage-chart {
  height: 200px;
  background: var(--surface);
  border: 1px solid var(--border);
  border-radius: 8px;
  padding: 16px;
  margin-bottom: 24px;
}

/* Decay shown as fading, not red */
.decay-indicator {
  opacity: 0.5;
  transition: opacity 0.3s;
}

.decay-indicator:hover {
  opacity: 1.0;
}

.decay-indicator .decay-tooltip {
  font-size: 11px;
  color: var(--text-dim);
  font-style: italic;
}

/* ==========================================================================
   NAVIGATION — MODE TABS
   ========================================================================== */

.mode-nav {
  display: flex;
  align-items: center;
  height: 56px;
  padding: 0 24px;
  background: var(--deep);
  border-bottom: 1px solid var(--border);
  gap: 0;
}

.mode-nav-brand {
  font-family: var(--serif);
  font-size: 18px;
  color: var(--gold);
  margin-right: 32px;
  font-weight: 600;
}

.mode-nav-tab {
  padding: 16px 20px;
  font-family: var(--sans);
  font-size: 13px;
  color: var(--text-dim);
  text-decoration: none;
  border-bottom: 2px solid transparent;
  transition: all 0.15s;
}

.mode-nav-tab:hover {
  color: var(--text);
}

.mode-nav-tab.active {
  color: var(--text-bright);
  border-bottom-color: var(--gold);
}

.mode-nav-spacer {
  flex: 1;
}

.skill-switcher {
  font-family: var(--mono);
  font-size: 11px;
  padding: 4px 10px;
  border-radius: 4px;
  background: var(--surface);
  border: 1px solid var(--border);
  color: var(--text-dim);
  cursor: pointer;
}

/* ==========================================================================
   MOBILE — CSS GRADIENT NEBULA BACKGROUND
   ========================================================================== */

.nebula-bg {
  background:
    radial-gradient(ellipse at 20% 50%, rgba(42, 27, 92, 0.4) 0%, transparent 60%),
    radial-gradient(ellipse at 80% 30%, rgba(20, 60, 100, 0.3) 0%, transparent 50%),
    radial-gradient(ellipse at 50% 80%, rgba(90, 30, 60, 0.2) 0%, transparent 60%),
    var(--void);
}

/* ==========================================================================
   MOBILE RESPONSIVE
   ========================================================================== */

@media (max-width: 768px) {
  /* Train mode: single panel */
  .train-layout {
    flex-direction: column;
  }

  #train-split {
    flex-direction: column;
  }

  .split-divider {
    display: none;
  }

  .split-left,
  .split-right {
    width: 100% !important;
    height: auto;
    border-right: none;
  }

  .split-right {
    display: none;
  }

  .split-right.mobile-visible {
    display: flex;
  }

  .split-left.mobile-hidden {
    display: none;
  }

  /* Mobile panel toggle */
  .mobile-panel-toggle {
    display: flex;
    gap: 0;
    border-bottom: 1px solid var(--border);
  }

  .mobile-panel-tab {
    flex: 1;
    padding: 10px;
    text-align: center;
    font-size: 12px;
    color: var(--text-dim);
    border-bottom: 2px solid transparent;
    cursor: pointer;
    background: none;
    border-top: none;
    border-left: none;
    border-right: none;
  }

  .mobile-panel-tab.active {
    color: var(--gold);
    border-bottom-color: var(--gold);
  }

  /* Materials: single column */
  .materials-grid {
    grid-template-columns: 1fr;
  }

  .materials-header {
    flex-direction: column;
    align-items: stretch;
  }

  .materials-search {
    max-width: 100%;
  }

  /* Progress: stack metrics */
  .metrics-grid {
    grid-template-columns: repeat(2, 1fr);
  }

  .secondary-metrics {
    flex-direction: column;
    gap: 8px;
  }

  .roadmap-track {
    flex-direction: column;
  }

  .roadmap-node {
    flex-direction: row;
    min-width: auto;
  }

  .roadmap-node::after {
    display: none;
  }

  /* Navigation: smaller */
  .mode-nav {
    padding: 0 12px;
    overflow-x: auto;
  }

  .mode-nav-tab {
    padding: 12px 12px;
    font-size: 12px;
    white-space: nowrap;
  }
}

/* Hide mobile-only elements on desktop */
@media (min-width: 769px) {
  .mobile-panel-toggle {
    display: none;
  }
}

/* Reduced motion */
@media (prefers-reduced-motion: reduce) {
  .voice-active { animation: none; }
  .roadmap-node.plateau .roadmap-dot { animation: none; }
}
```

- [ ] **Step 2: Visual test**

Open each mode template in browser. Verify:
- Train mode split panel is correctly styled with Observatory theme
- Chat bubbles differentiate user (right-aligned) from assistant (left-aligned)
- Material cards have visible feedback buttons
- Progress metrics use teal/gold/coral, not red for negative states
- Decay indicators fade rather than alarm
- At 768px breakpoint, layouts switch to mobile
- Nebula gradient background renders on mobile body

- [ ] **Step 3: Commit**

```bash
git commit -m "feat: Observatory CSS — train, materials, progress styles with mobile responsive"
```

---

### Task 7: Train Mode Templates — Layout, Chat, Content Fragments

**Files:**
- Create: `learn-anything-app/templates/train/index.html`
- Create: `learn-anything-app/templates/train/chat.html`
- Create: `learn-anything-app/templates/train/content.html`
- Create: `learn-anything-app/templates/train/content_example.html`
- Create: `learn-anything-app/templates/train/content_diagram.html`
- Create: `learn-anything-app/templates/train/content_graph.html`
- Create: `learn-anything-app/templates/train/content_video.html`
- Create: `learn-anything-app/templates/train/content_flashcards.html`

All templates use Datastar SSE patterns: chat messages arrive via `datastar-patch-elements` (append), content updates via fragment replacement. No SPA JavaScript.

- [ ] **Step 1: Create train mode index template**

```html
<!-- templates/train/index.html -->
{% extends "base.html" %}
{% block title %}Train — {{ skill_name }} — Learn Anything{% endblock %}
{% block content %}
<nav class="mode-nav">
  <span class="mode-nav-brand">Learn Anything</span>
  <a href="/explore" class="mode-nav-tab">Explore</a>
  <a href="/train/{{ skill_slug }}" class="mode-nav-tab active">Train</a>
  <a href="/materials/{{ skill_slug }}" class="mode-nav-tab">Materials</a>
  <a href="/progress/{{ skill_slug }}" class="mode-nav-tab">Progress</a>
  <span class="mode-nav-spacer"></span>
  <span class="skill-switcher">{{ skill_name }}</span>
</nav>

<div class="train-layout nebula-bg"
     data-signals:session_id="'{{ session_id }}'"
     data-signals:split_ratio="0.30"
     data-signals:active_panel="'chat'"
     data-signals:chat_input="''">

  <!-- Mobile panel toggle -->
  <div class="mobile-panel-toggle">
    <button class="mobile-panel-tab active"
            data-class:active="$active_panel === 'chat'"
            data-on:click="$active_panel = 'chat'">
      Chat
    </button>
    <button class="mobile-panel-tab"
            data-class:active="$active_panel === 'content'"
            data-on:click="$active_panel = 'content'">
      Content
    </button>
  </div>

  <div id="train-split">
    <div class="split-left"
         data-class:mobile-hidden="$active_panel !== 'chat'">
      <div id="chat-panel" data-init="@get('/train/{{ skill_slug }}/{{ session_id }}/chat')">
        <!-- Chat fragment loaded via SSE -->
      </div>
    </div>

    <div class="split-divider" title="Drag to resize. Double-click to reset."></div>

    <div class="split-right"
         data-class:mobile-visible="$active_panel === 'content'">
      <div id="content-panel" data-init="@get('/train/{{ skill_slug }}/{{ session_id }}/content')">
        <!-- Content fragment loaded via SSE -->
      </div>
    </div>
  </div>
</div>

<script src="/static/js/split-panel.js"></script>
<script src="/static/js/voice.js"></script>
{% endblock %}
```

- [ ] **Step 2: Create chat panel fragment**

```html
<!-- templates/train/chat.html -->
<div class="chat-panel" id="chat-panel">
  <div class="chat-header">
    <span class="session-template-badge">{{ template_label }}</span>
    <span class="subtitle">Session {{ session_number }}</span>
  </div>

  <div class="chat-messages" id="chat-messages">
    {% for msg in messages %}
    <div class="chat-bubble {{ msg.role }}">
      {{ msg.content }}
    </div>
    {% endfor %}
  </div>

  <div id="voice-status"></div>

  <div class="chat-input-area">
    <button id="voice-mic-btn" type="button" title="Voice input (Ctrl+Shift+M)">
      <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
        <path d="M12 1a3 3 0 0 0-3 3v8a3 3 0 0 0 6 0V4a3 3 0 0 0-3-3z"/>
        <path d="M19 10v2a7 7 0 0 1-14 0v-2"/>
        <line x1="12" y1="19" x2="12" y2="23"/>
        <line x1="8" y1="23" x2="16" y2="23"/>
      </svg>
    </button>

    <input id="chat-input"
           type="text"
           placeholder="Type or speak..."
           data-model="chat_input"
           data-on:keydown.enter="@post('/train/{{ skill_slug }}/{{ session_id }}/message', {input: $chat_input}); $chat_input = ''">

    <button class="chat-send-btn"
            data-on:click="@post('/train/{{ skill_slug }}/{{ session_id }}/message', {input: $chat_input}); $chat_input = ''">
      <svg width="16" height="16" viewBox="0 0 24 24" fill="currentColor">
        <path d="M2.01 21L23 12 2.01 3 2 10l15 2-15 2z"/>
      </svg>
    </button>
  </div>
</div>
```

- [ ] **Step 3: Create content panel fragment**

```html
<!-- templates/train/content.html -->
<div class="content-panel" id="content-panel">
  <div class="content-tabs">
    <button class="content-tab {{ 'active' if active_tab == 'example' }}"
            data-on:click="@get('/train/{{ skill_slug }}/{{ session_id }}/content?tab=example')">
      Example
    </button>
    <button class="content-tab {{ 'active' if active_tab == 'diagram' }}"
            data-on:click="@get('/train/{{ skill_slug }}/{{ session_id }}/content?tab=diagram')">
      Diagram
    </button>
    <button class="content-tab {{ 'active' if active_tab == 'graph' }}"
            data-on:click="@get('/train/{{ skill_slug }}/{{ session_id }}/content?tab=graph')">
      Graph
    </button>
    <button class="content-tab {{ 'active' if active_tab == 'video' }}"
            data-on:click="@get('/train/{{ skill_slug }}/{{ session_id }}/content?tab=video')">
      Video
    </button>
    <button class="content-tab {{ 'active' if active_tab == 'flashcards' }}"
            data-on:click="@get('/train/{{ skill_slug }}/{{ session_id }}/content?tab=flashcards')">
      Flashcards
    </button>
  </div>

  <div class="content-body" id="content-body">
    {% include content_template %}
  </div>
</div>
```

- [ ] **Step 4: Create content tab fragments**

```html
<!-- templates/train/content_example.html -->
<div class="worked-example">
  <h3>{{ example.title }}</h3>
  {% for step in example.steps %}
  <div class="example-step {{ 'faded' if not step.visible }}"
       {% if not step.visible %}data-on:click="@post('/train/{{ skill_slug }}/{{ session_id }}/reveal-step', {step_index: {{ loop.index0 }}})"{% endif %}>
    <div class="step-label">Step {{ loop.index }}</div>
    <div class="step-content">{{ step.content }}</div>
  </div>
  {% endfor %}
  <p class="subtitle" style="margin-top: 12px;">
    Fading level {{ example.fading_level }}/3 — faded steps hide progressively as you master the pattern.
  </p>
</div>

<!-- templates/train/content_diagram.html -->
<div class="diagram-display">
  <h3>{{ diagram.title }}</h3>
  <div class="diagram-svg" data-ignore-morph>
    {{ diagram.svg_content | safe }}
  </div>
  {% if diagram.caption %}
  <p class="subtitle" style="margin-top: 8px;">{{ diagram.caption }}</p>
  {% endif %}
</div>

<!-- templates/train/content_graph.html -->
<div class="mini-graph-container" data-ignore-morph id="mini-graph"
     data-signals:mini_graph_data='{{ graph_data | tojson }}'
     data-effect="renderMiniGraph($mini_graph_data)">
</div>
<p class="subtitle" style="padding: 8px 0;">
  Focus nodes highlighted. Mastery updates live during session.
</p>

<!-- templates/train/content_video.html -->
<div class="video-container">
  <h3>{{ video.title }}</h3>
  <iframe class="video-embed"
          src="https://www.youtube.com/embed/{{ video.youtube_id }}?enablejsapi=1"
          frameborder="0"
          allow="autoplay; encrypted-media"
          allowfullscreen
          data-ignore-morph>
  </iframe>
  {% if video.annotations %}
  <div class="video-annotations">
    {% for ann in video.annotations %}
    <div class="video-annotation"
         data-on:click="@post('/train/{{ skill_slug }}/{{ session_id }}/video-pause', {time: {{ ann.time_seconds }}})">
      <span class="ann-time">{{ ann.time_formatted }}</span>
      <span>{{ ann.text }}</span>
    </div>
    {% endfor %}
  </div>
  {% endif %}
</div>

<!-- templates/train/content_flashcards.html -->
<div class="flashcard-review"
     data-signals:show_back="false">
  {% if card %}
  <div class="flashcard" id="flashcard-current"
       data-on:click="$show_back = !$show_back">
    <div class="card-face" data-show="!$show_back">
      {{ card.front }}
    </div>
    <div class="card-face" data-show="$show_back">
      {{ card.back }}
    </div>
    <div class="card-bloom">{{ card.bloom_level }}</div>
  </div>

  <div class="flashcard-nav">
    <button data-on:click="$show_back = false; @post('/train/{{ skill_slug }}/{{ session_id }}/card-response', {card_index: {{ card_index }}, result: 'incorrect'}); @get('/train/{{ skill_slug }}/{{ session_id }}/flashcard?index={{ card_index + 1 }}')">
      Again
    </button>
    <button data-on:click="$show_back = false; @post('/train/{{ skill_slug }}/{{ session_id }}/card-response', {card_index: {{ card_index }}, result: 'partial'}); @get('/train/{{ skill_slug }}/{{ session_id }}/flashcard?index={{ card_index + 1 }}')">
      Hard
    </button>
    <button data-on:click="$show_back = false; @post('/train/{{ skill_slug }}/{{ session_id }}/card-response', {card_index: {{ card_index }}, result: 'correct'}); @get('/train/{{ skill_slug }}/{{ session_id }}/flashcard?index={{ card_index + 1 }}')">
      Good
    </button>
  </div>
  <p class="subtitle" style="margin-top: 8px;">Card {{ card_index + 1 }} of {{ total_cards }}</p>
  {% else %}
  <p class="subtitle">No flashcards queued for this session.</p>
  {% endif %}
</div>
```

- [ ] **Step 5: Commit**

```bash
git commit -m "feat: train mode templates — split panel, chat, content tabs (example, diagram, graph, video, flashcards)"
```

---

### Task 8: Train Mode Routes — SSE Chat Streaming + Content Push

**Files:**
- Create: `learn-anything-app/app/routes/train.py`
- Test: `learn-anything-app/tests/integration/test_routes/test_train.py`

The train route handles session creation, SSE chat streaming, and content fragment updates. Chat messages arrive as `datastar-patch-elements` with append mode. Content updates replace the `#content-body` fragment.

- [ ] **Step 1: Write failing test for train routes**

```python
# tests/integration/test_routes/test_train.py
import pytest
from httpx import AsyncClient, ASGITransport
from app.main import app


@pytest.fixture
async def client():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as c:
        yield c


@pytest.mark.asyncio
async def test_train_page_renders(client):
    resp = await client.get("/train/jazz-piano")
    assert resp.status_code == 200
    assert "train-split" in resp.text or "Train" in resp.text


@pytest.mark.asyncio
async def test_train_start_session(client):
    resp = await client.post(
        "/train/jazz-piano/start",
        json={"template": "A_concept_intro", "focus_vertex_ids": ["v1", "v2"]},
    )
    assert resp.status_code in (200, 303)


@pytest.mark.asyncio
async def test_train_chat_fragment(client):
    resp = await client.get("/train/jazz-piano/test-session/chat")
    # Should return HTML fragment or 404 if session doesn't exist
    assert resp.status_code in (200, 404)


@pytest.mark.asyncio
async def test_train_content_fragment(client):
    resp = await client.get("/train/jazz-piano/test-session/content")
    assert resp.status_code in (200, 404)


@pytest.mark.asyncio
async def test_train_content_tab_switch(client):
    resp = await client.get("/train/jazz-piano/test-session/content?tab=flashcards")
    assert resp.status_code in (200, 404)
```

- [ ] **Step 2: Run test — should fail**

Run: `cd learn-anything-app && uv run pytest tests/integration/test_routes/test_train.py -v`
Expected: FAIL

- [ ] **Step 3: Implement train routes**

```python
# app/routes/train.py
import json
import uuid
from markupsafe import escape
from fastapi import APIRouter, Request, Depends
from fastapi.responses import RedirectResponse, HTMLResponse
from datastar_py import ServerSentEventGenerator as SSE
from datastar_py.enums import ElementPatchMode
from datastar_py.fastapi import DatastarResponse
from app.templating import templates
from app.services.training import (
    create_session,
    get_session,
    close_session,
    build_system_prompt,
    stream_chat_response,
    SessionState,
)

router = APIRouter(prefix="/train", tags=["train"])

# Template label mapping
TEMPLATE_LABELS = {
    "A_concept_intro": "A - Concept Intro",
    "B_retrieval_review": "B - Retrieval",
    "C_skill_drill": "C - Drill",
    "D_productive_failure": "D - Productive Failure",
    "E_mastery_gate": "E - Mastery Gate",
    "F_mentor_conversation": "F - Mentor",
}


@router.get("/{skill_slug}")
async def train_page(request: Request, skill_slug: str):
    """Render the Train mode page. Creates or resumes a session."""
    # Check for existing active session (simplified — full version checks DB)
    session_id = request.query_params.get("session", str(uuid.uuid4()))
    return templates.TemplateResponse(
        request,
        "train/index.html",
        {
            "skill_slug": skill_slug,
            "skill_name": skill_slug.replace("-", " ").title(),
            "session_id": session_id,
        },
    )


@router.post("/{skill_slug}/start")
async def start_session(request: Request, skill_slug: str):
    """Start a new training session."""
    body = await request.json()
    template = body.get("template", "A_concept_intro")
    focus_vertex_ids = body.get("focus_vertex_ids", [])

    # In production, this would use the DB session from dependency injection
    session_id = str(uuid.uuid4())
    return RedirectResponse(
        f"/train/{skill_slug}?session={session_id}", status_code=303
    )


@router.get("/{skill_slug}/{session_id}/chat")
async def chat_fragment(request: Request, skill_slug: str, session_id: str):
    """Return the chat panel HTML fragment via DatastarResponse (invoked by data-init)."""
    state = get_session(session_id)
    if state is None:
        context = {
            "skill_slug": skill_slug,
            "session_id": session_id,
            "template_label": "New Session",
            "session_number": 1,
            "messages": [
                {"role": "assistant", "content": "Ready to begin. What would you like to work on?"}
            ],
        }
    else:
        context = {
            "skill_slug": skill_slug,
            "session_id": session_id,
            "template_label": TEMPLATE_LABELS.get(state.template, state.template),
            "session_number": 1,
            "messages": [{"role": m["role"], "content": m["content"]} for m in state.messages],
        }
    html = templates.get_template("train/chat.html").render(context)
    return DatastarResponse(SSE.patch_elements(html))


@router.post("/{skill_slug}/{session_id}/message")
async def send_message(request: Request, skill_slug: str, session_id: str):
    """Handle a chat message. Returns a DatastarResponse SSE stream that:
    1. Appends user message bubble to #chat-messages
    2. Streams assistant response tokens into a new bubble
    3. May push content fragment updates to #content-body

    Uses datastar-py SDK for all SSE formatting.
    """
    body = await request.json()
    user_input = body.get("input", "").strip()
    if not user_input:
        return HTMLResponse("")

    async def generate_sse():
        # 1. Push user message bubble (XSS-escaped)
        user_html = f'<div class="chat-bubble user">{escape(user_input)}</div>'
        yield from SSE.patch_elements(
            user_html,
            selector="#chat-messages",
            mode=ElementPatchMode.APPEND,
        )

        # 2. Start assistant bubble (will be filled by streaming)
        bubble_id = f"msg-{uuid.uuid4().hex[:8]}"
        yield from SSE.patch_elements(
            f'<div class="chat-bubble assistant" id="{bubble_id}"></div>',
            selector="#chat-messages",
            mode=ElementPatchMode.APPEND,
        )

        # 3. Stream LLM response
        state = get_session(session_id)
        if state is None:
            # No active LLM session — echo for now
            safe_input = str(escape(user_input))
            response_text = f"I heard: {safe_input}. (LLM not connected — start a session first.)"
            yield from SSE.patch_elements(
                response_text,
                selector=f"#{bubble_id}",
                mode=ElementPatchMode.INNER,
            )
        else:
            # In production, this would stream from the LLM via stream_chat_response
            # For now, simulate a response
            response_text = f"Let me think about that... (Session active: {state.template})"
            yield from SSE.patch_elements(
                response_text,
                selector=f"#{bubble_id}",
                mode=ElementPatchMode.INNER,
            )

    return DatastarResponse(generate_sse())


@router.get("/{skill_slug}/{session_id}/content")
async def content_fragment(
    request: Request, skill_slug: str, session_id: str
):
    """Return the content panel HTML fragment."""
    tab = request.query_params.get("tab", "example")

    # Map tab to template
    tab_templates = {
        "example": "train/content_example.html",
        "diagram": "train/content_diagram.html",
        "graph": "train/content_graph.html",
        "video": "train/content_video.html",
        "flashcards": "train/content_flashcards.html",
    }
    content_template = tab_templates.get(tab, "train/content_example.html")

    # Default placeholder data for each tab type
    context = {
        "skill_slug": skill_slug,
        "session_id": session_id,
        "active_tab": tab,
        "content_template": content_template,
    }

    if tab == "example":
        context["example"] = {
            "title": "Waiting for session content...",
            "steps": [
                {"label": "Step 1", "content": "Content will appear here as the session progresses.", "visible": True},
            ],
            "fading_level": 0,
        }
    elif tab == "diagram":
        context["diagram"] = {
            "title": "No diagram yet",
            "svg_content": '<svg width="200" height="100"><text x="10" y="50" fill="#6b7199">Diagram will appear here</text></svg>',
            "caption": "",
        }
    elif tab == "graph":
        context["graph_data"] = json.dumps({"nodes": [], "edges": []})
    elif tab == "video":
        context["video"] = {
            "title": "No video selected",
            "youtube_id": "",
            "annotations": [],
        }
    elif tab == "flashcards":
        context["card"] = None
        context["card_index"] = 0
        context["total_cards"] = 0

    html = templates.get_template("train/content.html").render(context)
    return DatastarResponse(SSE.patch_elements(html))


@router.post("/{skill_slug}/{session_id}/reveal-step")
async def reveal_step(request: Request, skill_slug: str, session_id: str):
    """Reveal a faded step in a worked example (backward fading interaction)."""
    body = await request.json()
    step_index = body.get("step_index", 0)
    # In production: update the session state, re-render the example fragment
    return HTMLResponse(f"<div>Step {step_index} revealed</div>")


@router.post("/{skill_slug}/{session_id}/card-response")
async def card_response(request: Request, skill_slug: str, session_id: str):
    """Record a flashcard review response."""
    body = await request.json()
    card_index = body.get("card_index", 0)
    result = body.get("result", "incorrect")
    # In production: record in session state, update mastery
    return HTMLResponse("")


@router.get("/{skill_slug}/{session_id}/flashcard")
async def flashcard_fragment(request: Request, skill_slug: str, session_id: str):
    """Return a single flashcard fragment at the requested index.

    Each navigation button GETs this route to fetch the next card,
    so the server controls which card is shown (no client-side array indexing).
    Returns a DatastarResponse that replaces the flashcard review container.
    """
    from datastar_py.fastapi import DatastarResponse

    index = int(request.query_params.get("index", 0))
    state = get_session(session_id)

    # In production: get cards from session state
    cards = []  # Populated from session state in production
    if state and hasattr(state, "flashcard_queue"):
        cards = state.flashcard_queue

    card = None
    if cards and index < len(cards):
        card = cards[index]
    context = {
        "card": card,
        "card_index": index,
        "total_cards": len(cards),
        "skill_slug": skill_slug,
        "session_id": session_id,
    }
    html = templates.get_template("train/content_flashcards.html").render(context)
    return DatastarResponse(SSE.patch_elements(html))


@router.post("/{skill_slug}/{session_id}/video-pause")
async def video_pause(request: Request, skill_slug: str, session_id: str):
    """Handle a video annotation pause point — inject discussion into chat."""
    body = await request.json()
    time = body.get("time", 0)
    # In production: push a discussion prompt to the chat panel via SSE
    return HTMLResponse("")
```

- [ ] **Step 4: Register route in main.py**

Add to `app/main.py`:
```python
from app.routes.train import router as train_router
app.include_router(train_router)
```

- [ ] **Step 5: Run test — should pass**

Run: `cd learn-anything-app && uv run pytest tests/integration/test_routes/test_train.py -v`
Expected: PASS

- [ ] **Step 6: Commit**

```bash
git commit -m "feat: train mode routes — SSE chat streaming, content fragments, session lifecycle"
```

---

### Task 9: Materials Mode Templates — Browser, Cards, Feedback

**Files:**
- Create: `learn-anything-app/templates/materials/index.html`
- Create: `learn-anything-app/templates/materials/card.html`
- Create: `learn-anything-app/templates/materials/feedback_modal.html`
- Create: `learn-anything-app/templates/materials/quality_stats.html`

Materials mode is a server-rendered browse/search hub. All interactions (filter, search, feedback) use Datastar `@post()` or `@get()` — no client-side routing.

- [ ] **Step 1: Create materials index template**

```html
<!-- templates/materials/index.html -->
{% extends "base.html" %}
{% block title %}Materials — {{ skill_name }} — Learn Anything{% endblock %}
{% block content %}
<nav class="mode-nav">
  <span class="mode-nav-brand">Learn Anything</span>
  <a href="/explore" class="mode-nav-tab">Explore</a>
  <a href="/train/{{ skill_slug }}" class="mode-nav-tab">Train</a>
  <a href="/materials/{{ skill_slug }}" class="mode-nav-tab active">Materials</a>
  <a href="/progress/{{ skill_slug }}" class="mode-nav-tab">Progress</a>
  <span class="mode-nav-spacer"></span>
  <span class="skill-switcher">{{ skill_name }}</span>
</nav>

<div class="materials-layout"
     data-signals:search_query="''"
     data-signals:active_filter="'all'"
     data-signals:show_flag_modal="false"
     data-signals:flag_material_id="''"
     data-signals:flag_comment="''">

  <div class="materials-header">
    <h1>Materials</h1>
    <div class="materials-search">
      <input type="text"
             placeholder="Search materials..."
             data-model="search_query"
             data-on:keydown.enter="@get('/materials/{{ skill_slug }}/search?q=' + $search_query)">
    </div>
  </div>

  <!-- Quality stats -->
  <div id="quality-stats"
       data-init="@get('/materials/{{ skill_slug }}/quality-stats')">
  </div>

  <!-- Filters -->
  <div class="materials-filters">
    <button class="materials-filter-btn active"
            data-class:active="$active_filter === 'all'"
            data-on:click="$active_filter = 'all'; @get('/materials/{{ skill_slug }}/list?filter=all')">
      All
    </button>
    <button class="materials-filter-btn"
            data-class:active="$active_filter === 'flashcard_deck'"
            data-on:click="$active_filter = 'flashcard_deck'; @get('/materials/{{ skill_slug }}/list?filter=flashcard_deck')">
      Flashcards
    </button>
    <button class="materials-filter-btn"
            data-class:active="$active_filter === 'worked_example'"
            data-on:click="$active_filter = 'worked_example'; @get('/materials/{{ skill_slug }}/list?filter=worked_example')">
      Worked Examples
    </button>
    <button class="materials-filter-btn"
            data-class:active="$active_filter === 'lecture'"
            data-on:click="$active_filter = 'lecture'; @get('/materials/{{ skill_slug }}/list?filter=lecture')">
      Lectures
    </button>
    <button class="materials-filter-btn"
            data-class:active="$active_filter === 'video'"
            data-on:click="$active_filter = 'video'; @get('/materials/{{ skill_slug }}/list?filter=video')">
      Videos
    </button>
  </div>

  <!-- Batch actions -->
  <div class="batch-actions" style="margin-top: 12px; margin-bottom: 16px;">
    <button class="batch-btn"
            data-on:click="@post('/materials/{{ skill_slug }}/batch/regenerate-flagged')">
      Regenerate All Flagged
    </button>
    <button class="batch-btn"
            data-on:click="@post('/materials/{{ skill_slug }}/batch/llm-review')">
      LLM Review Entire Deck
    </button>
    <button class="batch-btn"
            data-on:click="@post('/materials/{{ skill_slug }}/batch/export-anki')">
      Re-export Anki
    </button>
  </div>

  <!-- Material cards grid -->
  <div class="materials-grid" id="materials-grid"
       data-init="@get('/materials/{{ skill_slug }}/list')">
    <!-- Cards loaded via SSE fragment -->
  </div>

  <!-- Flag/comment modal -->
  <div class="feedback-modal-overlay"
       data-show="$show_flag_modal">
    <div class="feedback-modal">
      <h3>Flag Material</h3>
      <textarea placeholder="What's wrong with this material?"
                data-model="flag_comment"></textarea>
      <div class="feedback-modal-actions">
        <button data-on:click="@post('/materials/{{ skill_slug }}/feedback', {material_id: $flag_material_id, type: 'flag', comment: $flag_comment}); $show_flag_modal = false; $flag_comment = ''">
          Submit Flag
        </button>
        <button class="primary"
                data-on:click="@post('/materials/{{ skill_slug }}/feedback', {material_id: $flag_material_id, type: 'flag', comment: $flag_comment, action: 'regenerate'}); $show_flag_modal = false; $flag_comment = ''">
          Flag + Regenerate
        </button>
        <button data-on:click="$show_flag_modal = false; $flag_comment = ''">
          Cancel
        </button>
      </div>
    </div>
  </div>
</div>
{% endblock %}
```

- [ ] **Step 2: Create material card fragment**

```html
<!-- templates/materials/card.html -->
<div class="material-card" id="material-{{ material.id }}">
  <div class="material-card-header">
    <span class="material-card-title">{{ material.title }}</span>
    <span class="material-card-type {{ material.type }}">{{ material.type | replace('_', ' ') }}</span>
  </div>
  <div class="material-card-meta">
    {{ material.bloom_level | capitalize if material.bloom_level else '' }}
    {% if material.modality %} &middot; {{ material.modality }}{% endif %}
    {% if material.curriculum_position %} &middot; Position {{ material.curriculum_position }}{% endif %}
  </div>
  {% if material.preview %}
  <div class="material-card-content">{{ material.preview }}</div>
  {% endif %}
  <div class="material-feedback">
    <button class="feedback-btn {{ 'approved' if material.feedback_status == 'approved' }}"
            title="Approve"
            data-on:click="@post('/materials/{{ skill_slug }}/feedback', {material_id: '{{ material.id }}', type: 'approve'})">
      <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
        <path d="M14 9V5a3 3 0 0 0-3-3l-4 9v11h11.28a2 2 0 0 0 2-1.7l1.38-9a2 2 0 0 0-2-2.3zM7 22H4a2 2 0 0 1-2-2v-7a2 2 0 0 1 2-2h3"/>
      </svg>
    </button>
    <button class="feedback-btn {{ 'flagged' if material.feedback_status == 'flagged' }}"
            title="Flag issue"
            data-on:click="$flag_material_id = '{{ material.id }}'; $show_flag_modal = true">
      <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
        <path d="M4 15s1-1 4-1 5 2 8 2 4-1 4-1V3s-1 1-4 1-5-2-8-2-4 1-4 1z"/>
        <line x1="4" y1="22" x2="4" y2="15"/>
      </svg>
    </button>
    <button class="feedback-comment-btn"
            data-on:click="$flag_material_id = '{{ material.id }}'; $show_flag_modal = true">
      Comment
    </button>
  </div>
</div>
```

- [ ] **Step 3: Create quality stats fragment**

```html
<!-- templates/materials/quality_stats.html -->
<div class="quality-stats" id="quality-stats">
  <div class="quality-stat approved">
    <span class="quality-stat-count">{{ stats.approved }}</span>
    <span class="quality-stat-label">Approved</span>
  </div>
  <div class="quality-stat flagged">
    <span class="quality-stat-count">{{ stats.flagged }}</span>
    <span class="quality-stat-label">Flagged</span>
  </div>
  <div class="quality-stat unreviewed">
    <span class="quality-stat-count">{{ stats.unreviewed }}</span>
    <span class="quality-stat-label">Unreviewed</span>
  </div>
</div>
```

- [ ] **Step 4: Create feedback modal fragment**

```html
<!-- templates/materials/feedback_modal.html -->
<div class="feedback-modal">
  <h3>{{ 'Edit Flag' if feedback else 'Flag Material' }}</h3>
  <p class="subtitle" style="margin-bottom: 12px;">{{ material_title }}</p>
  <textarea placeholder="What's wrong with this material?"
            data-model="flag_comment">{{ feedback.comment if feedback else '' }}</textarea>
  <div class="feedback-modal-actions">
    <button data-on:click="@post('/materials/{{ skill_slug }}/feedback', {material_id: '{{ material_id }}', type: 'flag', comment: $flag_comment}); $show_flag_modal = false">
      Submit Flag
    </button>
    <button class="primary"
            data-on:click="@post('/materials/{{ skill_slug }}/feedback', {material_id: '{{ material_id }}', type: 'flag', comment: $flag_comment, action: 'regenerate'}); $show_flag_modal = false">
      Flag + Regenerate
    </button>
    <button data-on:click="@post('/materials/{{ skill_slug }}/feedback', {material_id: '{{ material_id }}', type: 'flag', comment: $flag_comment, action: 'expand'}); $show_flag_modal = false">
      Ask LLM to Expand
    </button>
    <button data-on:click="$show_flag_modal = false">
      Dismiss
    </button>
  </div>
</div>
```

- [ ] **Step 5: Commit**

```bash
git commit -m "feat: materials mode templates — browser grid, card with feedback, quality stats, flag modal"
```

---

### Task 10: Materials Mode Routes — Browse, Search, Feedback

**Files:**
- Create: `learn-anything-app/app/routes/materials.py`
- Test: `learn-anything-app/tests/integration/test_routes/test_materials.py`

- [ ] **Step 1: Write failing test for materials routes**

```python
# tests/integration/test_routes/test_materials.py
import pytest
from httpx import AsyncClient, ASGITransport
from app.main import app


@pytest.fixture
async def client():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as c:
        yield c


@pytest.mark.asyncio
async def test_materials_page_renders(client):
    resp = await client.get("/materials/jazz-piano")
    assert resp.status_code == 200
    assert "Materials" in resp.text


@pytest.mark.asyncio
async def test_materials_list(client):
    resp = await client.get("/materials/jazz-piano/list")
    assert resp.status_code == 200


@pytest.mark.asyncio
async def test_materials_list_filtered(client):
    resp = await client.get("/materials/jazz-piano/list?filter=flashcard_deck")
    assert resp.status_code == 200


@pytest.mark.asyncio
async def test_materials_search(client):
    resp = await client.get("/materials/jazz-piano/search?q=voicing")
    assert resp.status_code == 200


@pytest.mark.asyncio
async def test_materials_quality_stats(client):
    resp = await client.get("/materials/jazz-piano/quality-stats")
    assert resp.status_code == 200
    assert "approved" in resp.text.lower() or "Approved" in resp.text


@pytest.mark.asyncio
async def test_materials_feedback_approve(client):
    resp = await client.post(
        "/materials/jazz-piano/feedback",
        json={"material_id": "mat-1", "type": "approve"},
    )
    assert resp.status_code == 200


@pytest.mark.asyncio
async def test_materials_feedback_flag(client):
    resp = await client.post(
        "/materials/jazz-piano/feedback",
        json={
            "material_id": "mat-1",
            "type": "flag",
            "comment": "Chord spelling error",
        },
    )
    assert resp.status_code == 200


@pytest.mark.asyncio
async def test_materials_batch_export(client):
    resp = await client.post("/materials/jazz-piano/batch/export-anki")
    assert resp.status_code == 200
```

- [ ] **Step 2: Run test — should fail**

Run: `cd learn-anything-app && uv run pytest tests/integration/test_routes/test_materials.py -v`
Expected: FAIL

- [ ] **Step 3: Implement materials routes**

```python
# app/routes/materials.py
from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse
from app.templating import templates

router = APIRouter(prefix="/materials", tags=["materials"])


@router.get("/{skill_slug}")
async def materials_page(request: Request, skill_slug: str):
    """Render the Materials mode page."""
    return templates.TemplateResponse(
        request,
        "materials/index.html",
        {
            "skill_slug": skill_slug,
            "skill_name": skill_slug.replace("-", " ").title(),
        },
    )


@router.get("/{skill_slug}/list")
async def materials_list(request: Request, skill_slug: str):
    """Return HTML fragment with material cards, optionally filtered."""
    filter_type = request.query_params.get("filter", "all")

    # In production: query Material model from DB, filter by type/skill
    # For now, return placeholder cards
    materials = [
        {
            "id": "mat-1",
            "title": "Shell Voicing Fundamentals",
            "type": "worked_example",
            "bloom_level": "apply",
            "modality": "reading",
            "curriculum_position": 1,
            "preview": "Root position shell voicings for major 7th, minor 7th, and dominant 7th chords.",
            "feedback_status": None,
        },
        {
            "id": "mat-2",
            "title": "Basic Jazz Harmony Deck",
            "type": "flashcard_deck",
            "bloom_level": "remember",
            "modality": "interactive",
            "curriculum_position": 1,
            "preview": "32 cards covering chord symbols, scale degrees, and interval recognition.",
            "feedback_status": "approved",
        },
        {
            "id": "mat-3",
            "title": "Circle of Fifths Deep Dive",
            "type": "lecture",
            "bloom_level": "understand",
            "modality": "reading",
            "curriculum_position": 2,
            "preview": "How the circle of fifths governs harmonic motion in jazz standards.",
            "feedback_status": None,
        },
    ]

    if filter_type != "all":
        materials = [m for m in materials if m["type"] == filter_type]

    # Render each card and concatenate
    cards_html = ""
    for material in materials:
        cards_html += templates.get_template("materials/card.html").render(
            {"material": material, "skill_slug": skill_slug}
        )

    if not materials:
        cards_html = '<p class="subtitle">No materials found.</p>'

    return DatastarResponse(SSE.patch_elements(
        f'<div id="materials-grid" class="materials-grid">{cards_html}</div>'
    ))


@router.get("/{skill_slug}/search")
async def materials_search(request: Request, skill_slug: str):
    """Search materials by query string."""
    query = request.query_params.get("q", "").strip().lower()

    # In production: full-text search on Material model
    # For now, filter placeholder materials by title
    all_materials = [
        {
            "id": "mat-1",
            "title": "Shell Voicing Fundamentals",
            "type": "worked_example",
            "bloom_level": "apply",
            "modality": "reading",
            "preview": "Root position shell voicings...",
            "feedback_status": None,
        },
    ]

    results = [m for m in all_materials if query in m.get("title", "").lower()]

    from markupsafe import escape

    cards_html = ""
    for material in results:
        cards_html += templates.get_template("materials/card.html").render(
            {"material": material, "skill_slug": skill_slug}
        )

    if not results:
        cards_html = f'<p class="subtitle">No results for "{escape(query)}"</p>'

    return DatastarResponse(SSE.patch_elements(
        f'<div id="materials-grid" class="materials-grid">{cards_html}</div>'
    ))


@router.get("/{skill_slug}/quality-stats")
async def quality_stats(request: Request, skill_slug: str):
    """Return quality stats fragment."""
    # In production: query MaterialFeedback model for counts
    stats = {"approved": 8, "flagged": 2, "unreviewed": 22}
    html = templates.get_template("materials/quality_stats.html").render({"stats": stats})
    return DatastarResponse(SSE.patch_elements(html))


@router.post("/{skill_slug}/feedback")
async def submit_feedback(request: Request, skill_slug: str):
    """Handle material feedback (approve, flag, comment)."""
    body = await request.json()
    material_id = body.get("material_id", "")
    feedback_type = body.get("type", "comment")
    comment = body.get("comment", "")
    action = body.get("action")  # regenerate, expand, edit, dismiss

    # In production: create MaterialFeedback record in DB
    # If action is "regenerate", queue a regeneration job
    # If action is "expand", queue an LLM expansion job

    # Return updated card fragment
    # For now, return acknowledgment
    from markupsafe import escape
    status = "approved" if feedback_type == "approve" else "flagged"
    return DatastarResponse(SSE.patch_elements(
        f'<span id="feedback-status" class="subtitle">Feedback recorded: {escape(feedback_type)}</span>'
    ))


@router.post("/{skill_slug}/batch/regenerate-flagged")
async def batch_regenerate(request: Request, skill_slug: str):
    """Regenerate all flagged materials."""
    # In production: query all flagged MaterialFeedback, queue regeneration for each
    return DatastarResponse(SSE.patch_elements(
        '<span id="batch-status" class="subtitle">Regeneration queued for all flagged materials.</span>'
    ))


@router.post("/{skill_slug}/batch/llm-review")
async def batch_llm_review(request: Request, skill_slug: str):
    """Have the LLM review the entire material deck."""
    # In production: queue an LLM review job
    return DatastarResponse(SSE.patch_elements(
        '<span id="batch-status" class="subtitle">LLM review queued for entire deck.</span>'
    ))


@router.post("/{skill_slug}/batch/export-anki")
async def batch_export_anki(request: Request, skill_slug: str):
    """Re-export materials to Anki .apkg format."""
    # In production: call generate_anki.py or equivalent
    return DatastarResponse(SSE.patch_elements(
        '<span id="batch-status" class="subtitle">Anki export started. Download will appear shortly.</span>'
    ))
```

- [ ] **Step 4: Register route in main.py**

Add to `app/main.py`:
```python
from app.routes.materials import router as materials_router
app.include_router(materials_router)
```

- [ ] **Step 5: Run test — should pass**

Run: `cd learn-anything-app && uv run pytest tests/integration/test_routes/test_materials.py -v`
Expected: PASS

- [ ] **Step 6: Commit**

```bash
git commit -m "feat: materials mode routes — browse, search, feedback, batch actions"
```

---

### Task 11: Progress Mode Templates — Dashboard, Metrics, Roadmap

**Files:**
- Create: `learn-anything-app/templates/progress/index.html`
- Create: `learn-anything-app/templates/progress/metrics.html`
- Create: `learn-anything-app/templates/progress/roadmap.html`
- Create: `learn-anything-app/templates/progress/session_history.html`
- Create: `learn-anything-app/templates/progress/coverage_chart.html`

All progress data is computed server-side and pushed as HTML fragments. The D3 coverage chart runs in a `data-ignore-morph` island.

- [ ] **Step 1: Create progress index template**

```html
<!-- templates/progress/index.html -->
{% extends "base.html" %}
{% block title %}Progress — {{ skill_name }} — Learn Anything{% endblock %}
{% block content %}
<nav class="mode-nav">
  <span class="mode-nav-brand">Learn Anything</span>
  <a href="/explore" class="mode-nav-tab">Explore</a>
  <a href="/train/{{ skill_slug }}" class="mode-nav-tab">Train</a>
  <a href="/materials/{{ skill_slug }}" class="mode-nav-tab">Materials</a>
  <a href="/progress/{{ skill_slug }}" class="mode-nav-tab active">Progress</a>
  <span class="mode-nav-spacer"></span>
  <span class="skill-switcher">{{ skill_name }}</span>
</nav>

<div class="progress-layout">
  <!-- Identity frame hero -->
  <div class="identity-hero">
    <div class="identity-text" id="identity-text"
         data-init="@get('/progress/{{ skill_slug }}/identity')">
    </div>
  </div>

  <!-- Primary metrics -->
  <div id="metrics-section"
       data-init="@get('/progress/{{ skill_slug }}/metrics')">
  </div>

  <!-- Secondary (effort) metrics -->
  <div id="secondary-metrics"
       data-init="@get('/progress/{{ skill_slug }}/secondary-metrics')">
  </div>

  <!-- Curriculum roadmap -->
  <div id="roadmap-section"
       data-init="@get('/progress/{{ skill_slug }}/roadmap')">
  </div>

  <!-- Knowledge graph coverage over time -->
  <div id="coverage-chart-section"
       data-init="@get('/progress/{{ skill_slug }}/coverage-chart')">
  </div>

  <!-- Session history -->
  <div id="session-history-section"
       data-init="@get('/progress/{{ skill_slug }}/session-history')">
  </div>
</div>
{% endblock %}
```

- [ ] **Step 2: Create metrics fragment**

```html
<!-- templates/progress/metrics.html -->
<div id="metrics-section">
  <div class="metrics-grid">
    {% if metrics.delayed_retention_rate is not none %}
    <div class="metric-card">
      <div class="metric-value">{{ (metrics.delayed_retention_rate * 100) | round(0) | int }}%</div>
      <div class="metric-label">Delayed Retention</div>
      <div class="metric-trend {{ 'positive' if metrics.delayed_retention_rate >= 0.80 else 'neutral' if metrics.delayed_retention_rate >= 0.60 else 'negative' }}">
        {{ 'Strong' if metrics.delayed_retention_rate >= 0.80 else 'Building' if metrics.delayed_retention_rate >= 0.60 else 'Needs work' }}
      </div>
    </div>
    {% endif %}

    <div class="metric-card">
      <div class="metric-value">+{{ metrics.mastery_transitions_net }}</div>
      <div class="metric-label">Net Mastery Transitions</div>
      <div class="metric-trend {{ 'positive' if metrics.mastery_transitions_net > 0 else 'neutral' }}">
        {{ metrics.mastery_transitions_forward }} forward, {{ metrics.mastery_transitions_backward }} back
      </div>
    </div>

    <div class="metric-card">
      <div class="metric-value">{{ (metrics.coverage_percentage * 100) | round(0) | int }}%</div>
      <div class="metric-label">Graph Coverage</div>
      <div class="metric-trend neutral">
        {{ metrics.total_vertices }} concepts total
      </div>
    </div>

    {% if metrics.curriculum_velocity is not none %}
    <div class="metric-card">
      <div class="metric-value">{{ metrics.curriculum_velocity | round(1) }}</div>
      <div class="metric-label">Task Classes / Week</div>
      <div class="metric-trend neutral">Curriculum velocity</div>
    </div>
    {% endif %}

    {% if metrics.calibration_accuracy is not none %}
    <div class="metric-card">
      <div class="metric-value">{{ (metrics.calibration_accuracy * 100) | round(0) | int }}%</div>
      <div class="metric-label">Calibration Accuracy</div>
      <div class="metric-trend neutral">Self-assessment vs. performance</div>
    </div>
    {% endif %}
  </div>
</div>
```

- [ ] **Step 3: Create roadmap fragment**

```html
<!-- templates/progress/roadmap.html -->
<div id="roadmap-section" class="curriculum-roadmap">
  <h2 style="margin-bottom: 16px;">Curriculum Roadmap</h2>

  <div class="roadmap-track">
    {% for tc in task_classes %}
    <div class="roadmap-node {{ tc.status }}">
      <div class="roadmap-dot"></div>
      <div class="roadmap-label">{{ tc.name }}</div>
      {% if tc.has_mastery_gate %}
      <div class="roadmap-gate">Gate</div>
      {% endif %}
    </div>
    {% endfor %}
  </div>

  {% if plateau_status and plateau_status != 'none' %}
  <div style="margin-top: 12px; padding: 12px; background: var(--surface); border: 1px solid var(--border); border-radius: 8px;">
    <span class="subtitle">
      {% if plateau_status == 'approaching' %}
        Plateau approaching — the system will adjust if needed
      {% elif plateau_status == 'active' %}
        Working through a plateau — this is normal. The system is trying different approaches.
      {% elif plateau_status == 'resolving' %}
        Plateau resolving — progress resuming
      {% endif %}
    </span>
  </div>
  {% endif %}
</div>
```

- [ ] **Step 4: Create session history fragment**

```html
<!-- templates/progress/session_history.html -->
<div id="session-history-section" class="session-history">
  <h2 style="margin-bottom: 16px;">Session History</h2>

  {% if sessions %}
  <div class="session-list">
    {% for session in sessions %}
    <div class="session-item">
      <span class="session-template">{{ session.template_short }}</span>
      <span class="session-date">{{ session.date_formatted }}</span>
      <span class="session-summary">{{ session.summary }}</span>
      {% if session.accuracy is not none %}
      <span class="session-accuracy {{ 'positive' if session.accuracy >= 0.8 else 'neutral' if session.accuracy >= 0.6 else 'negative' }}"
            style="color: {{ 'var(--mastered)' if session.accuracy >= 0.8 else 'var(--familiar)' if session.accuracy >= 0.6 else 'var(--attempted)' }}">
        {{ (session.accuracy * 100) | round(0) | int }}%
      </span>
      {% endif %}
    </div>
    {% endfor %}
  </div>
  {% else %}
  <p class="subtitle">No sessions yet. Start training to see your history here.</p>
  {% endif %}
</div>
```

- [ ] **Step 5: Create coverage chart fragment**

```html
<!-- templates/progress/coverage_chart.html -->
<div id="coverage-chart-section">
  <h2 style="margin-bottom: 16px;">Knowledge Coverage Over Time</h2>

  <div class="coverage-chart" data-ignore-morph id="coverage-d3"
       data-signals:coverage_data='{{ coverage_data | tojson }}'
       data-effect="renderCoverageChart($coverage_data)">
  </div>

  <!-- Coverage breakdown by mastery category -->
  <div class="quality-stats" style="margin-top: 12px;">
    <div class="quality-stat approved">
      <span class="quality-stat-count">{{ coverage.mastered }}</span>
      <span class="quality-stat-label">Mastered</span>
    </div>
    <div class="quality-stat" style="color: var(--proficient);">
      <span class="quality-stat-count" style="color: var(--proficient);">{{ coverage.proficient }}</span>
      <span class="quality-stat-label">Proficient</span>
    </div>
    <div class="quality-stat" style="color: var(--familiar);">
      <span class="quality-stat-count" style="color: var(--familiar);">{{ coverage.familiar }}</span>
      <span class="quality-stat-label">Familiar</span>
    </div>
    <div class="quality-stat unreviewed">
      <span class="quality-stat-count">{{ coverage.not_started }}</span>
      <span class="quality-stat-label">Not Started</span>
    </div>
  </div>
</div>
```

- [ ] **Step 6: Commit**

```bash
git commit -m "feat: progress mode templates — dashboard, metrics cards, roadmap, session history, coverage chart"
```

---

### Task 12: Progress Mode Routes — Dashboard, Metrics, Roadmap

**Files:**
- Create: `learn-anything-app/app/routes/progress.py`
- Test: `learn-anything-app/tests/integration/test_routes/test_progress.py`

- [ ] **Step 1: Write failing test for progress routes**

```python
# tests/integration/test_routes/test_progress.py
import pytest
from httpx import AsyncClient, ASGITransport
from app.main import app


@pytest.fixture
async def client():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as c:
        yield c


@pytest.mark.asyncio
async def test_progress_page_renders(client):
    resp = await client.get("/progress/jazz-piano")
    assert resp.status_code == 200
    assert "Progress" in resp.text


@pytest.mark.asyncio
async def test_progress_identity(client):
    resp = await client.get("/progress/jazz-piano/identity")
    assert resp.status_code == 200


@pytest.mark.asyncio
async def test_progress_metrics(client):
    resp = await client.get("/progress/jazz-piano/metrics")
    assert resp.status_code == 200


@pytest.mark.asyncio
async def test_progress_secondary_metrics(client):
    resp = await client.get("/progress/jazz-piano/secondary-metrics")
    assert resp.status_code == 200


@pytest.mark.asyncio
async def test_progress_roadmap(client):
    resp = await client.get("/progress/jazz-piano/roadmap")
    assert resp.status_code == 200


@pytest.mark.asyncio
async def test_progress_coverage_chart(client):
    resp = await client.get("/progress/jazz-piano/coverage-chart")
    assert resp.status_code == 200


@pytest.mark.asyncio
async def test_progress_session_history(client):
    resp = await client.get("/progress/jazz-piano/session-history")
    assert resp.status_code == 200
```

- [ ] **Step 2: Run test — should fail**

Run: `cd learn-anything-app && uv run pytest tests/integration/test_routes/test_progress.py -v`
Expected: FAIL

- [ ] **Step 3: Implement progress routes**

```python
# app/routes/progress.py
import json
from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse
from app.templating import templates

router = APIRouter(prefix="/progress", tags=["progress"])


@router.get("/{skill_slug}")
async def progress_page(request: Request, skill_slug: str):
    """Render the Progress mode page shell."""
    return templates.TemplateResponse(
        request,
        "progress/index.html",
        {
            "skill_slug": skill_slug,
            "skill_name": skill_slug.replace("-", " ").title(),
        },
    )


@router.get("/{skill_slug}/identity")
async def identity_fragment(request: Request, skill_slug: str):
    """Return the identity frame hero text."""
    # In production: read from learning_plan.motivation_architecture.identity_frame
    identity = f"You're becoming a jazz pianist"
    from markupsafe import escape
    sub = f"Learning {escape(skill_slug.replace('-', ' '))}"
    return DatastarResponse(SSE.patch_elements(
        f'<div class="identity-hero" id="identity-text">'
        f'<div class="identity-text">{escape(identity)}</div>'
        f'<div class="identity-sub">{sub}</div>'
        f'</div>'
    ))


@router.get("/{skill_slug}/metrics")
async def metrics_fragment(request: Request, skill_slug: str):
    """Return primary metrics cards."""
    # In production: call compute_progress_metrics_pg or compute_progress_metrics_json
    # For now, use placeholder data
    from app.services.metrics import ProgressMetrics

    metrics = ProgressMetrics(
        delayed_retention_rate=0.82,
        transfer_task_success=None,
        mastery_transitions_forward=12,
        mastery_transitions_backward=2,
        mastery_transitions_net=10,
        calibration_accuracy=0.75,
        curriculum_velocity=1.2,
        total_vertices=35,
        coverage_by_category={
            "mastered": 5,
            "proficient": 8,
            "familiar": 10,
            "attempted": 6,
            "not_started": 6,
        },
        coverage_percentage=0.42,
        identity_frame="You're becoming a jazz pianist",
        sessions_completed=8,
        current_task_class="TC2: Basic Chord Voicings",
        plateau_status=None,
    )

    html = templates.get_template("progress/metrics.html").render({"metrics": metrics})
    return DatastarResponse(SSE.patch_elements(html))


@router.get("/{skill_slug}/secondary-metrics")
async def secondary_metrics_fragment(request: Request, skill_slug: str):
    """Return secondary (effort) metrics — less prominent."""
    # In production: query from DB
    return DatastarResponse(SSE.patch_elements(
        '<div class="secondary-metrics" id="secondary-metrics">'
        '<div class="secondary-metric">'
        '<span class="sec-value">8</span>'
        '<span>sessions completed</span>'
        '</div>'
        '<div class="secondary-metric">'
        '<span class="sec-value">6.2</span>'
        '<span>hours practiced</span>'
        '</div>'
        '<div class="secondary-metric">'
        '<span class="sec-value">145</span>'
        '<span>cards reviewed</span>'
        '</div>'
        '</div>'
    ))


@router.get("/{skill_slug}/roadmap")
async def roadmap_fragment(request: Request, skill_slug: str):
    """Return curriculum roadmap fragment."""
    # In production: read from learning_plan.curriculum.task_classes + progress
    task_classes = [
        {"name": "TC1: Music Fundamentals", "status": "completed", "has_mastery_gate": True},
        {"name": "TC2: Basic Voicings", "status": "current", "has_mastery_gate": True},
        {"name": "TC3: ii-V-I Progressions", "status": "upcoming", "has_mastery_gate": True},
        {"name": "TC4: Standards", "status": "upcoming", "has_mastery_gate": False},
        {"name": "TC5: Improvisation", "status": "upcoming", "has_mastery_gate": True},
    ]

    html = templates.get_template("progress/roadmap.html").render({
        "task_classes": task_classes,
        "plateau_status": None,
        "skill_slug": skill_slug,
    })
    return DatastarResponse(SSE.patch_elements(html))


@router.get("/{skill_slug}/coverage-chart")
async def coverage_chart_fragment(request: Request, skill_slug: str):
    """Return coverage chart fragment with D3 data."""
    # In production: compute from mastery transition log over time
    coverage_data = [
        {"date": "2026-03-01", "coverage": 0.0},
        {"date": "2026-03-08", "coverage": 0.08},
        {"date": "2026-03-15", "coverage": 0.18},
        {"date": "2026-03-22", "coverage": 0.30},
        {"date": "2026-03-29", "coverage": 0.42},
    ]
    coverage = {"mastered": 5, "proficient": 8, "familiar": 10, "attempted": 6, "not_started": 6}

    html = templates.get_template("progress/coverage_chart.html").render({
        "coverage_data": coverage_data,
        "coverage": coverage,
        "skill_slug": skill_slug,
    })
    return DatastarResponse(SSE.patch_elements(html))


@router.get("/{skill_slug}/session-history")
async def session_history_fragment(request: Request, skill_slug: str):
    """Return session history list fragment."""
    # In production: query TrainingSession model, most recent first
    sessions = [
        {
            "template_short": "B",
            "date_formatted": "Mar 29",
            "summary": "Retrieval practice on shell voicings. Strong recall on root position, inversions need work.",
            "accuracy": 0.82,
        },
        {
            "template_short": "A",
            "date_formatted": "Mar 27",
            "summary": "Introduced dominant 7th voicings. Connected to blues progression context.",
            "accuracy": 0.70,
        },
        {
            "template_short": "C",
            "date_formatted": "Mar 25",
            "summary": "Drill session on major 7th shell voicings across all 12 keys.",
            "accuracy": 0.88,
        },
        {
            "template_short": "E",
            "date_formatted": "Mar 22",
            "summary": "Mastery gate for TC1. Passed all three components. Advanced to TC2.",
            "accuracy": 0.91,
        },
    ]

    html = templates.get_template("progress/session_history.html").render(
        {"sessions": sessions, "skill_slug": skill_slug}
    )
    return DatastarResponse(SSE.patch_elements(html))
```

- [ ] **Step 4: Register route in main.py**

Add to `app/main.py`:
```python
from app.routes.progress import router as progress_router
app.include_router(progress_router)
```

- [ ] **Step 5: Run test — should pass**

Run: `cd learn-anything-app && uv run pytest tests/integration/test_routes/test_progress.py -v`
Expected: PASS

- [ ] **Step 6: Commit**

```bash
git commit -m "feat: progress mode routes — dashboard, metrics, roadmap, coverage chart, session history"
```

---

### Task 13: Alembic Migration for Progress Models

**Files:**
- Modify: `learn-anything-app/alembic/env.py`

Add the new progress models to the migration's model imports so Alembic auto-detects them.

- [ ] **Step 1: Update alembic/env.py imports**

Add to the import block in `alembic/env.py`:
```python
from app.models.progress import TrainingSession, SessionTopic, MaterialFeedback  # noqa
```

- [ ] **Step 2: Generate migration**

Run: `cd learn-anything-app && uv run alembic revision --autogenerate -m "add training_sessions, session_topics, material_feedback"`
Expected: Creates migration file in `alembic/versions/`

- [ ] **Step 3: Verify migration SQL**

Run: `cd learn-anything-app && uv run alembic upgrade head --sql`
Expected: Shows CREATE TABLE statements for `training_sessions`, `session_topics`, `material_feedback`.

- [ ] **Step 4: Commit**

```bash
git commit -m "feat: Alembic migration for training sessions, session topics, material feedback"
```

---

### Task 14: Wire LLM Streaming to Train Mode (Agent SDK Integration)

**Files:**
- Modify: `learn-anything-app/app/routes/train.py`
- Modify: `learn-anything-app/app/services/training.py`

Connect the train route's SSE chat stream to Plan 3's `LLMProvider` (with rate limiting, error recovery, etc.) for live LLM responses. Content-push directives in the LLM response are extracted and sent as separate SSE events to update the content panel.

**Important:** Do NOT create a separate `LLMProvider` class. Plan 3 already provides the full implementation with rate limiting, retries, and error recovery. Import and use it directly.

- [ ] **Step 1: Import Plan 3's LLM provider**

In `app/routes/train.py`, add this import (do NOT create a new LLMProvider class):
```python
from app.llm.dependencies import get_llm_provider
```

The `LLMProvider` from Plan 3 yields `LLMStreamEvent` objects (with a `.text` attribute) rather than raw dicts. The `stream_chat_response` function in `app/services/training.py` already handles this (see the `hasattr(event, 'text')` check).

- [ ] **Step 2: Update train route to use real LLM streaming with datastar-py SDK**

Replace the placeholder echo in `send_message` in `app/routes/train.py`:

```python
# In the send_message function, replace the "No active LLM session" else block:

import asyncio
import time
from markupsafe import escape
from datastar_py import ServerSentEventGenerator as SSE
from datastar_py.enums import ElementPatchMode
from app.llm.dependencies import get_llm_provider
from app.services.training import (
    build_system_prompt,
    _find_all_json_objects,
)

        state = get_session(session_id)
        if state is None:
            response_text = "Session not found. Please start a new session."
            yield from SSE.patch_elements(
                f'<div class="chat-bubble assistant" id="{bubble_id}">{response_text}</div>',
                selector=f"#{bubble_id}",
                mode=ElementPatchMode.INNER,
            )
        else:
            # Build system prompt with session context
            learner_context = {}  # In production: load from DB
            system = build_system_prompt(state, learner_context)

            # Stream from Plan 3's LLM provider (has rate limiting + error recovery)
            llm = get_llm_provider()

            full_response = ""
            token_batch = ""
            token_count = 0
            last_flush = time.monotonic()
            BATCH_SIZE = 8  # Flush every 8 tokens
            BATCH_TIMEOUT = 0.1  # Or every 100ms

            state.add_message("user", user_input)
            messages = [
                {"role": m["role"], "content": m["content"]}
                for m in state.messages
            ]

            async for event in llm.stream(messages, system=system):
                token = event.text if hasattr(event, 'text') else event.get("text", "")
                full_response += token
                token_batch += token
                token_count += 1

                now = time.monotonic()
                if token_count >= BATCH_SIZE or (now - last_flush) >= BATCH_TIMEOUT:
                    # Flush batch: send full accumulated text to replace bubble inner HTML
                    safe_response = str(escape(full_response))
                    yield from SSE.patch_elements(
                        safe_response,
                        selector=f"#{bubble_id}",
                        mode=ElementPatchMode.INNER,
                    )
                    token_batch = ""
                    token_count = 0
                    last_flush = now

            # Final flush for any remaining tokens
            if token_batch:
                safe_response = str(escape(full_response))
                yield from SSE.patch_elements(
                    safe_response,
                    selector=f"#{bubble_id}",
                    mode=ElementPatchMode.INNER,
                )

            state.add_message("assistant", full_response)

            # Extract content-push directives using brace-counting parser
            for directive in _find_all_json_objects(full_response, "content_push"):
                try:
                    tab = directive["content_push"]["tab"]
                    state.active_content_tab = tab
                    # Push content fragment update
                    # In production: render the appropriate content template
                    yield from SSE.patch_elements(
                        f"<div>Content update: {tab}</div>",
                        selector="#content-body",
                        mode=ElementPatchMode.INNER,
                    )
                except KeyError:
                    pass

            # Extract assessment directives using brace-counting parser
            for directive in _find_all_json_objects(full_response, "assessment"):
                try:
                    a = directive["assessment"]
                    state.record_assessment(
                        vertex_id=a["vertex_id"],
                        accuracy=a["accuracy"],
                        bloom=a["bloom_level"],
                    )
                except KeyError:
                    pass
```

- [ ] **Step 3: Verify SSE streaming works**

Run the app locally with an API key configured:
```bash
LA_ANTHROPIC_API_KEY=sk-ant-... cd learn-anything-app && uv run uvicorn app.main:app --reload
```
Open `/train/test-skill` in browser. Type a message. Verify:
- User bubble appears immediately
- Assistant bubble fills with streaming tokens (batched, not per-token)
- Content panel updates if the LLM includes a content-push directive

- [ ] **Step 4: Commit**

```bash
git commit -m "feat: wire Plan 3 LLMProvider to train mode with datastar-py SSE and batched streaming"
```

---

### Task 15: Full Integration Test — All Three Modes

**Files:**
- No new files — run existing tests plus manual verification

- [ ] **Step 1: Run full test suite**

Run: `cd learn-anything-app && uv run pytest tests/ -v --tb=short`

Expected: All tests pass. Count should include:
- Progress models (4)
- Training service (4)
- Metrics service (5)
- Train routes (5)
- Materials routes (8)
- Progress routes (7)
- Plus all tests from Plans 1-4

- [ ] **Step 2: Visual verification checklist**

Start the app and verify each mode:

**Train Mode:**
- [ ] Split panel renders at 30/70 ratio
- [ ] Divider is draggable, ratio persists across reload
- [ ] Double-click divider resets to 30/70
- [ ] Chat input accepts text, sends on Enter
- [ ] Voice mic button visible (active in Chrome/Edge, disabled in unsupported browsers)
- [ ] Session template badge shows in chat header
- [ ] Content tabs switch correctly
- [ ] At mobile width: panels stack, tab toggle appears

**Materials Mode:**
- [ ] Material cards render in grid
- [ ] Filter buttons filter the grid
- [ ] Search input filters by query
- [ ] Thumbs up button marks card as approved (green border)
- [ ] Flag button opens modal
- [ ] Flag modal has submit, regenerate, expand, dismiss options
- [ ] Quality stats bar shows counts
- [ ] Batch action buttons respond

**Progress Mode:**
- [ ] Identity hero text renders
- [ ] Primary metric cards show retention rate, transitions, coverage, velocity
- [ ] Secondary metrics row shows effort metrics (less prominent)
- [ ] Curriculum roadmap renders with completed/current/upcoming nodes
- [ ] Session history shows recent sessions with template badges
- [ ] Coverage chart container renders (D3 initialization in future plan)
- [ ] Decay indicators use fading opacity, not red

**Mobile (all modes):**
- [ ] At 768px breakpoint, layouts switch to single column
- [ ] Train mode shows panel toggle tabs
- [ ] Materials grid goes to single column
- [ ] Progress metrics stack in 2-column grid
- [ ] Nebula gradient background visible

- [ ] **Step 3: Commit**

```bash
git commit -m "feat: Plan 5 complete — Train, Materials, Progress modes with SSE, feedback, metrics"
```
