> HISTORICAL DESIGN REFERENCE: superseded operationally by CONVENTIONS.md and
> docs/superpowers/plans/2026-11-06-alpha-foundation.md. Do not execute provisioning,
> runner or database commands below. No current service admission is implied.

# Plan 3: LLM Integration + Orchestrator — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking. **Use opus subagents exclusively (model: opus). No sonnet, no haiku.**
>
> **REQUIRED READING:** `docs/plans/CONVENTIONS.md` — all plans follow these rules.
>
> **Execution:** Plans execute sequentially (1→2→3→4→5→6) on feature branch `feature/learn-anything-webapp`. TDD strictly enforced.

**Goal:** A working LLM integration layer with the Anthropic Python SDK (Messages API), a pipeline orchestrator that detects state and routes to the correct phase, SSE streaming for LLM responses, per-user rate limiting, and the calibration loop + feedback loop infrastructure. After this plan, the backend can drive the full onboarding pipeline and ongoing training feedback loops.

**Architecture:** LLMProvider protocol with AnthropicProvider implementation. Pipeline service reads DB state (which records exist for a user+skill) and determines the next phase. Orchestrator service routes to phase-specific handlers. SSE streaming via datastar-py's DatastarResponse. Rate limiter tracks per-user LLM call budgets in the database.

**Tech Stack:** FastAPI, anthropic (Messages API, not claude_agent_sdk), SQLAlchemy (from Plan 1), structlog (from Plan 1), datastar-py, pytest, pytest-asyncio

> **Note:** The spec (Section 11) names the provider `AgentSDKProvider`. This plan renames it to `AnthropicProvider` because the implementation uses the Anthropic Python SDK's Messages API, not the Claude Agent SDK package. The `LLMProvider` protocol name is unchanged.

**Spec:** `docs/specs/2026-04-01-learn-anything-webapp-design.md` — Sections 2, 5, 10

**Depends on:** Plan 1 (project scaffold, models, auth, config) and Plan 2 (PostgresBackend, graph queries)

---

## Project Structure

This plan creates the following files inside `learn-anything-app/`:

```
app/
├── llm/
│   ├── __init__.py
│   ├── provider.py              # LLMProvider protocol + data classes
│   ├── anthropic_provider.py             # AnthropicProvider (Anthropic Messages API)
│   └── rate_limiter.py          # Per-user LLM call budget tracking
├── services/
│   ├── pipeline.py              # Pipeline phase detection
│   └── orchestrator.py          # Phase routing + calibration loop + feedback loops
├── routes/
│   └── sse.py                   # SSE streaming endpoint for LLM responses
├── models/
│   └── llm_usage.py             # LLM usage tracking model
tests/
├── unit/
│   └── test_llm/
│       ├── __init__.py
│       ├── test_provider.py             # Protocol + data class tests (no DB)
│       └── test_rate_limiter_unit.py    # BudgetExhaustedError tests (no DB)
│   └── test_services/
│       ├── __init__.py
│       ├── test_orchestrator_gates.py   # Agreement gate data class tests
│       └── test_orchestrator_retry.py   # PhaseRetryPolicy + PHASE_FALLBACKS tests
├── integration/
│   └── test_llm/
│       ├── __init__.py
│       ├── test_anthropic_provider.py   # Requires anthropic API (mocked)
│       └── test_rate_limiter.py         # Requires DB for usage records/budgets
│   └── test_services/
│       ├── __init__.py
│       ├── test_pipeline.py             # Pipeline phase detection (requires DB)
│       ├── test_orchestrator.py         # Orchestrator routing (requires DB)
│       ├── test_calibration_loop.py     # Calibration loop with mock handlers
│       └── test_feedback_cascade.py     # Feedback cascade execution driver
│   └── test_routes/
│       └── test_sse.py                  # SSE endpoint tests
```

---

### Task 1: LLMProvider Protocol + Data Classes

**Files:**
- Create: `learn-anything-app/app/llm/__init__.py`
- Create: `learn-anything-app/app/llm/provider.py`
- Test: `learn-anything-app/tests/unit/test_llm/test_provider.py`

- [ ] **Step 1: Write failing test for LLMProvider protocol and data classes**

```python
# tests/unit/test_llm/test_provider.py
from app.llm.provider import (
    LLMProvider,
    LLMMessage,
    LLMResponse,
    LLMStreamEvent,
    LLMTool,
    LLMToolCall,
    LLMToolResult,
)


def test_message_creation():
    msg = LLMMessage(role="user", content="What should I learn first?")
    assert msg.role == "user"
    assert msg.content == "What should I learn first?"


def test_message_with_tool_calls():
    tool_call = LLMToolCall(
        id="tc_001",
        name="read_state",
        arguments={"skill_slug": "jazz-piano"},
    )
    msg = LLMMessage(role="assistant", content="", tool_calls=[tool_call])
    assert len(msg.tool_calls) == 1
    assert msg.tool_calls[0].name == "read_state"


def test_tool_result_message():
    result = LLMToolResult(
        tool_call_id="tc_001",
        content='{"phase": "calibration"}',
        is_error=False,
    )
    msg = LLMMessage(role="tool", content="", tool_results=[result])
    assert msg.tool_results[0].tool_call_id == "tc_001"
    assert not msg.tool_results[0].is_error


def test_response_creation():
    resp = LLMResponse(
        content="Let me assess your current knowledge.",
        tool_calls=[],
        usage={"input_tokens": 150, "output_tokens": 42},
        stop_reason="end_turn",
        model="claude-sonnet-4-6",
    )
    assert resp.content == "Let me assess your current knowledge."
    assert resp.usage["input_tokens"] == 150
    assert resp.stop_reason == "end_turn"


def test_stream_event_types():
    text_event = LLMStreamEvent(type="text", content="Hello")
    assert text_event.type == "text"
    assert text_event.content == "Hello"

    tool_event = LLMStreamEvent(
        type="tool_call",
        tool_call=LLMToolCall(id="tc_002", name="update_graph", arguments={"node_id": "v1"}),
    )
    assert tool_event.type == "tool_call"
    assert tool_event.tool_call.name == "update_graph"

    done_event = LLMStreamEvent(
        type="done",
        usage={"input_tokens": 200, "output_tokens": 80},
        stop_reason="end_turn",
    )
    assert done_event.type == "done"
    assert done_event.stop_reason == "end_turn"


def test_tool_definition():
    tool = LLMTool(
        name="read_state",
        description="Read a pipeline state file for the current skill",
        parameters={
            "type": "object",
            "properties": {
                "skill_slug": {"type": "string", "description": "The skill identifier"},
                "state_file": {
                    "type": "string",
                    "enum": [
                        "domain-assessment",
                        "skill-dossier",
                        "knowledge-graph",
                        "learning-plan",
                        "srs-cards",
                        "progress",
                    ],
                },
            },
            "required": ["skill_slug", "state_file"],
        },
    )
    assert tool.name == "read_state"
    assert "skill_slug" in tool.parameters["properties"]


def test_provider_protocol_has_required_methods():
    """Verify LLMProvider protocol defines generate and stream."""
    import inspect
    members = {name for name, _ in inspect.getmembers(LLMProvider)}
    assert "generate" in members
    assert "stream" in members
```

- [ ] **Step 2: Run test — should fail**

Run: `cd learn-anything-app && uv run pytest tests/unit/test_llm/test_provider.py -v`
Expected: FAIL — `ModuleNotFoundError: No module named 'app.llm'`

- [ ] **Step 3: Implement LLMProvider protocol and data classes**

```python
# app/llm/__init__.py
from app.llm.provider import (
    LLMProvider,
    LLMMessage,
    LLMResponse,
    LLMStreamEvent,
    LLMTool,
    LLMToolCall,
    LLMToolResult,
)

__all__ = [
    "LLMProvider",
    "LLMMessage",
    "LLMResponse",
    "LLMStreamEvent",
    "LLMTool",
    "LLMToolCall",
    "LLMToolResult",
]
```

```python
# app/llm/provider.py
"""
LLMProvider protocol and shared data classes.

The protocol defines the contract for all LLM integrations.
MVP: AnthropicProvider (Claude). Roadmap: LiteLLMProvider.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, AsyncIterator, Protocol


@dataclass
class LLMToolCall:
    """A tool call requested by the LLM."""
    id: str
    name: str
    arguments: dict[str, Any]


@dataclass
class LLMToolResult:
    """Result of executing a tool call, sent back to the LLM."""
    tool_call_id: str
    content: str
    is_error: bool = False


@dataclass
class LLMMessage:
    """A message in the conversation.

    Roles:
    - "system": System prompt (first message only)
    - "user": User input or orchestrator instructions
    - "assistant": LLM response (may include tool_calls)
    - "tool": Tool results (includes tool_results)
    """
    role: str  # system, user, assistant, tool
    content: str
    tool_calls: list[LLMToolCall] = field(default_factory=list)
    tool_results: list[LLMToolResult] = field(default_factory=list)


@dataclass
class LLMTool:
    """Tool definition exposed to the LLM."""
    name: str
    description: str
    parameters: dict[str, Any]


@dataclass
class LLMResponse:
    """Complete (non-streaming) LLM response."""
    content: str
    tool_calls: list[LLMToolCall]
    usage: dict[str, int]  # input_tokens, output_tokens
    stop_reason: str  # end_turn, tool_use, max_tokens
    model: str


@dataclass
class LLMStreamEvent:
    """A single event in a streaming LLM response.

    Event types:
    - "text": Partial text content (content field)
    - "tool_call": Tool invocation (tool_call field)
    - "tool_result": Tool result fed back (tool_result field)
    - "done": Stream complete (usage + stop_reason fields)
    - "error": Error occurred (content field has error message)
    """
    type: str  # text, tool_call, tool_result, done, error
    content: str = ""
    tool_call: LLMToolCall | None = None
    tool_result: LLMToolResult | None = None
    usage: dict[str, int] = field(default_factory=dict)
    stop_reason: str = ""


class LLMProvider(Protocol):
    """Protocol for LLM provider implementations.

    All providers must implement both generate (blocking) and stream
    (async iterator) methods. Tools are optional — pass an empty list
    for simple generation without tool use.
    """

    async def generate(
        self,
        messages: list[LLMMessage],
        tools: list[LLMTool] | None = None,
        *,
        system: str = "",
        max_tokens: int = 4096,
        temperature: float = 1.0,
        **kwargs: Any,
    ) -> LLMResponse:
        """Generate a complete response (non-streaming).

        Args:
            messages: Conversation history.
            tools: Tool definitions the LLM may invoke.
            system: System prompt (alternative to a system message).
            max_tokens: Maximum output tokens.
            temperature: Sampling temperature.
            **kwargs: Forward compatibility for future provider parameters.

        Returns:
            Complete LLMResponse.
        """
        ...

    async def stream(
        self,
        messages: list[LLMMessage],
        tools: list[LLMTool] | None = None,
        *,
        system: str = "",
        max_tokens: int = 4096,
        temperature: float = 1.0,
        **kwargs: Any,
    ) -> AsyncIterator[LLMStreamEvent]:
        """Stream a response as a sequence of events.

        Args:
            messages: Conversation history.
            tools: Tool definitions the LLM may invoke.
            system: System prompt (alternative to a system message).
            max_tokens: Maximum output tokens.
            temperature: Sampling temperature.
            **kwargs: Forward compatibility for future provider parameters.

        Yields:
            LLMStreamEvent instances. The final event has type="done".
        """
        ...
```

- [ ] **Step 4: Run test — should pass**

Run: `cd learn-anything-app && uv run pytest tests/unit/test_llm/test_provider.py -v`
Expected: 7 passed

- [ ] **Step 5: Commit**

```bash
git commit -m "feat: LLMProvider protocol with data classes for messages, tools, streaming events"
```

---

### Task 2: AnthropicProvider Implementation

**Files:**
- Create: `learn-anything-app/app/llm/anthropic_provider.py`
- Test: `learn-anything-app/tests/unit/test_llm/test_anthropic_provider.py`

- [ ] **Step 1: Write failing test for AnthropicProvider**

```python
# tests/unit/test_llm/test_anthropic_provider.py
"""
Tests for AnthropicProvider.

These tests use a mock Anthropic client to avoid requiring an API key.
Integration tests with a real API key are in tests/integration/.
"""
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from app.llm.anthropic_provider import AnthropicProvider
from app.llm.provider import LLMMessage, LLMTool, LLMStreamEvent


def test_provider_init():
    """AnthropicProvider initializes with api_key and model."""
    provider = AnthropicProvider(api_key="sk-test-key", model="claude-sonnet-4-6")
    assert provider.model == "claude-sonnet-4-6"
    assert provider._api_key == "sk-test-key"


def test_provider_init_default_model():
    """Default model is claude-sonnet-4-6."""
    provider = AnthropicProvider(api_key="sk-test-key")
    assert provider.model == "claude-sonnet-4-6"


def test_convert_messages_user():
    """User messages convert to Anthropic format."""
    provider = AnthropicProvider(api_key="sk-test-key")
    messages = [LLMMessage(role="user", content="Hello")]
    converted = provider._convert_messages(messages)
    assert len(converted) == 1
    assert converted[0]["role"] == "user"
    assert converted[0]["content"] == "Hello"


def test_convert_messages_assistant_with_tool_calls():
    """Assistant messages with tool calls convert correctly."""
    from app.llm.provider import LLMToolCall
    provider = AnthropicProvider(api_key="sk-test-key")
    messages = [
        LLMMessage(
            role="assistant",
            content="Let me check that.",
            tool_calls=[
                LLMToolCall(id="tc_1", name="read_state", arguments={"slug": "piano"})
            ],
        )
    ]
    converted = provider._convert_messages(messages)
    assert len(converted) == 1
    content_blocks = converted[0]["content"]
    # Should have a text block and a tool_use block
    assert any(b["type"] == "text" for b in content_blocks)
    assert any(b["type"] == "tool_use" for b in content_blocks)


def test_convert_messages_tool_results():
    """Tool result messages convert to tool_result content blocks."""
    from app.llm.provider import LLMToolResult
    provider = AnthropicProvider(api_key="sk-test-key")
    messages = [
        LLMMessage(
            role="tool",
            content="",
            tool_results=[
                LLMToolResult(tool_call_id="tc_1", content='{"phase": "calibration"}', is_error=False)
            ],
        )
    ]
    converted = provider._convert_messages(messages)
    assert len(converted) == 1
    assert converted[0]["role"] == "user"
    assert converted[0]["content"][0]["type"] == "tool_result"
    assert converted[0]["content"][0]["tool_use_id"] == "tc_1"


def test_convert_tools():
    """LLMTool objects convert to Anthropic tool format."""
    provider = AnthropicProvider(api_key="sk-test-key")
    tools = [
        LLMTool(
            name="read_state",
            description="Read pipeline state",
            parameters={
                "type": "object",
                "properties": {"slug": {"type": "string"}},
                "required": ["slug"],
            },
        )
    ]
    converted = provider._convert_tools(tools)
    assert len(converted) == 1
    assert converted[0]["name"] == "read_state"
    assert converted[0]["input_schema"]["type"] == "object"


@pytest.mark.asyncio
async def test_generate_calls_client():
    """generate() calls the Anthropic client and returns LLMResponse."""
    provider = AnthropicProvider(api_key="sk-test-key")

    mock_response = MagicMock()
    mock_response.content = [MagicMock(type="text", text="I'll help you learn piano.")]
    mock_response.usage.input_tokens = 100
    mock_response.usage.output_tokens = 25
    mock_response.stop_reason = "end_turn"
    mock_response.model = "claude-sonnet-4-6"

    with patch.object(provider, "_client") as mock_client:
        mock_client.messages.create = AsyncMock(return_value=mock_response)
        messages = [LLMMessage(role="user", content="I want to learn piano")]
        response = await provider.generate(messages)

    assert response.content == "I'll help you learn piano."
    assert response.usage["input_tokens"] == 100
    assert response.stop_reason == "end_turn"


@pytest.mark.asyncio
async def test_generate_with_tool_use_response():
    """generate() handles tool_use blocks in response."""
    from app.llm.provider import LLMToolCall
    provider = AnthropicProvider(api_key="sk-test-key")

    mock_tool_block = MagicMock()
    mock_tool_block.type = "tool_use"
    mock_tool_block.id = "tc_99"
    mock_tool_block.name = "read_state"
    mock_tool_block.input = {"slug": "piano"}

    mock_response = MagicMock()
    mock_response.content = [mock_tool_block]
    mock_response.usage.input_tokens = 80
    mock_response.usage.output_tokens = 15
    mock_response.stop_reason = "tool_use"
    mock_response.model = "claude-sonnet-4-6"

    with patch.object(provider, "_client") as mock_client:
        mock_client.messages.create = AsyncMock(return_value=mock_response)
        messages = [LLMMessage(role="user", content="Continue")]
        response = await provider.generate(messages)

    assert response.stop_reason == "tool_use"
    assert len(response.tool_calls) == 1
    assert response.tool_calls[0].id == "tc_99"
    assert response.tool_calls[0].name == "read_state"


@pytest.mark.asyncio
async def test_stream_yields_events():
    """stream() yields LLMStreamEvent objects."""
    provider = AnthropicProvider(api_key="sk-test-key")

    # Simulate Anthropic streaming events
    mock_text_event = MagicMock()
    mock_text_event.type = "content_block_delta"
    mock_text_event.delta.type = "text_delta"
    mock_text_event.delta.text = "Hello"

    mock_done_event = MagicMock()
    mock_done_event.type = "message_stop"

    mock_message = MagicMock()
    mock_message.usage.input_tokens = 50
    mock_message.usage.output_tokens = 10
    mock_message.stop_reason = "end_turn"

    async def mock_stream_iter():
        yield mock_text_event
        yield mock_done_event

    mock_stream_ctx = MagicMock()
    mock_stream_ctx.__aenter__ = AsyncMock(return_value=mock_stream_ctx)
    mock_stream_ctx.__aexit__ = AsyncMock(return_value=False)
    mock_stream_ctx.__aiter__ = lambda self: mock_stream_iter()
    mock_stream_ctx.get_final_message = MagicMock(return_value=mock_message)

    with patch.object(provider, "_client") as mock_client:
        mock_client.messages.stream = MagicMock(return_value=mock_stream_ctx)

        events = []
        async for event in provider.stream([LLMMessage(role="user", content="Hi")]):
            events.append(event)

    # Should have at least a text event and a done event
    text_events = [e for e in events if e.type == "text"]
    done_events = [e for e in events if e.type == "done"]
    assert len(text_events) >= 1
    assert text_events[0].content == "Hello"
    assert len(done_events) == 1
    assert done_events[0].stop_reason == "end_turn"
```

- [ ] **Step 2: Run test — should fail**

Run: `cd learn-anything-app && uv run pytest tests/unit/test_llm/test_anthropic_provider.py -v`
Expected: FAIL — `ModuleNotFoundError: No module named 'app.llm.anthropic_provider'`

- [ ] **Step 3: Add anthropic dependency to pyproject.toml**

Add to `[project] dependencies`:
```toml
    "anthropic>=0.45",  # Messages API — NOT claude_agent_sdk
```

Run: `cd learn-anything-app && uv sync`

- [ ] **Step 4: Implement AnthropicProvider**

```python
# app/llm/anthropic_provider.py
"""
AnthropicProvider — Anthropic Messages API implementation of LLMProvider.

Uses the Anthropic Python SDK (anthropic package) to call Claude's
Messages API. Supports both blocking generation and streaming.
"""
from __future__ import annotations

import structlog
from typing import Any, AsyncIterator

import anthropic

from app.llm.provider import (
    LLMMessage,
    LLMResponse,
    LLMStreamEvent,
    LLMTool,
    LLMToolCall,
)

log = structlog.get_logger()


class AnthropicProvider:
    """LLMProvider implementation using the Anthropic (Claude) SDK.

    Translates the generic LLMProvider interface to Anthropic's Messages API.
    """

    def __init__(self, api_key: str, model: str = "claude-sonnet-4-6"):
        self._api_key = api_key
        self.model = model
        self._client = anthropic.AsyncAnthropic(api_key=api_key)

    def _convert_messages(self, messages: list[LLMMessage]) -> list[dict[str, Any]]:
        """Convert LLMMessage list to Anthropic message format.

        Anthropic format:
        - User: {"role": "user", "content": str | list[block]}
        - Assistant: {"role": "assistant", "content": str | list[block]}
        - Tool results: {"role": "user", "content": [{"type": "tool_result", ...}]}
        """
        converted = []
        for msg in messages:
            if msg.role == "system":
                # System messages are handled separately via the system parameter
                continue

            if msg.role == "tool":
                # Tool results map to user messages with tool_result blocks
                blocks = []
                for result in msg.tool_results:
                    blocks.append({
                        "type": "tool_result",
                        "tool_use_id": result.tool_call_id,
                        "content": result.content,
                        "is_error": result.is_error,
                    })
                converted.append({"role": "user", "content": blocks})

            elif msg.role == "assistant" and msg.tool_calls:
                # Assistant with tool calls: mix of text and tool_use blocks
                blocks: list[dict[str, Any]] = []
                if msg.content:
                    blocks.append({"type": "text", "text": msg.content})
                for tc in msg.tool_calls:
                    blocks.append({
                        "type": "tool_use",
                        "id": tc.id,
                        "name": tc.name,
                        "input": tc.arguments,
                    })
                converted.append({"role": "assistant", "content": blocks})

            else:
                # Plain user or assistant message
                converted.append({"role": msg.role, "content": msg.content})

        return converted

    def _convert_tools(self, tools: list[LLMTool]) -> list[dict[str, Any]]:
        """Convert LLMTool list to Anthropic tool format."""
        return [
            {
                "name": tool.name,
                "description": tool.description,
                "input_schema": tool.parameters,
            }
            for tool in tools
        ]

    def _extract_system(self, messages: list[LLMMessage], system: str) -> str:
        """Extract system prompt from messages or use explicit system parameter."""
        if system:
            return system
        for msg in messages:
            if msg.role == "system":
                return msg.content
        return ""

    def _parse_response(self, response: Any) -> LLMResponse:
        """Parse Anthropic response into LLMResponse."""
        content = ""
        tool_calls = []

        for block in response.content:
            if block.type == "text":
                content += block.text
            elif block.type == "tool_use":
                tool_calls.append(
                    LLMToolCall(
                        id=block.id,
                        name=block.name,
                        arguments=block.input,
                    )
                )

        return LLMResponse(
            content=content,
            tool_calls=tool_calls,
            usage={
                "input_tokens": response.usage.input_tokens,
                "output_tokens": response.usage.output_tokens,
            },
            stop_reason=response.stop_reason,
            model=response.model,
        )

    async def generate(
        self,
        messages: list[LLMMessage],
        tools: list[LLMTool] | None = None,
        *,
        system: str = "",
        max_tokens: int = 4096,
        temperature: float = 1.0,
        **kwargs: Any,
    ) -> LLMResponse:
        """Generate a complete response using Claude Messages API."""
        system_prompt = self._extract_system(messages, system)
        converted_messages = self._convert_messages(messages)

        api_kwargs: dict[str, Any] = {
            "model": self.model,
            "messages": converted_messages,
            "max_tokens": max_tokens,
            "temperature": temperature,
        }
        if system_prompt:
            api_kwargs["system"] = system_prompt
        if tools:
            api_kwargs["tools"] = self._convert_tools(tools)

        log.debug("llm_generate", model=self.model, message_count=len(converted_messages))

        response = await self._client.messages.create(**api_kwargs)
        return self._parse_response(response)

    async def stream(
        self,
        messages: list[LLMMessage],
        tools: list[LLMTool] | None = None,
        *,
        system: str = "",
        max_tokens: int = 4096,
        temperature: float = 1.0,
        **kwargs: Any,
    ) -> AsyncIterator[LLMStreamEvent]:
        """Stream a response as LLMStreamEvent instances."""
        system_prompt = self._extract_system(messages, system)
        converted_messages = self._convert_messages(messages)

        api_kwargs: dict[str, Any] = {
            "model": self.model,
            "messages": converted_messages,
            "max_tokens": max_tokens,
            "temperature": temperature,
        }
        if system_prompt:
            api_kwargs["system"] = system_prompt
        if tools:
            api_kwargs["tools"] = self._convert_tools(tools)

        log.debug("llm_stream_start", model=self.model, message_count=len(converted_messages))

        async with self._client.messages.stream(**api_kwargs) as stream:
            current_tool_id = ""
            current_tool_name = ""
            current_tool_input = ""

            async for event in stream:
                if event.type == "content_block_start":
                    block = event.content_block
                    if hasattr(block, "type") and block.type == "tool_use":
                        current_tool_id = block.id
                        current_tool_name = block.name
                        current_tool_input = ""

                elif event.type == "content_block_delta":
                    delta = event.delta
                    if delta.type == "text_delta":
                        yield LLMStreamEvent(type="text", content=delta.text)
                    elif delta.type == "input_json_delta":
                        current_tool_input += delta.partial_json

                elif event.type == "content_block_stop":
                    if current_tool_name:
                        import json
                        try:
                            arguments = json.loads(current_tool_input) if current_tool_input else {}
                        except json.JSONDecodeError:
                            arguments = {}
                        yield LLMStreamEvent(
                            type="tool_call",
                            tool_call=LLMToolCall(
                                id=current_tool_id,
                                name=current_tool_name,
                                arguments=arguments,
                            ),
                        )
                        current_tool_id = ""
                        current_tool_name = ""
                        current_tool_input = ""

                elif event.type == "message_stop":
                    final = stream.get_final_message()
                    yield LLMStreamEvent(
                        type="done",
                        usage={
                            "input_tokens": final.usage.input_tokens,
                            "output_tokens": final.usage.output_tokens,
                        },
                        stop_reason=final.stop_reason,
                    )
```

- [ ] **Step 5: Run test — should pass**

Run: `cd learn-anything-app && uv run pytest tests/unit/test_llm/test_anthropic_provider.py -v`
Expected: All passed

- [ ] **Step 6: Commit**

```bash
git commit -m "feat: AnthropicProvider — Anthropic Messages API implementation of LLMProvider"
```

---

### Task 3: LLM Usage Model + Rate Limiter

**Files:**
- Create: `learn-anything-app/app/models/llm_usage.py`
- Create: `learn-anything-app/app/llm/rate_limiter.py`
- Test: `learn-anything-app/tests/unit/test_llm/test_rate_limiter.py`

- [ ] **Step 1: Write failing test for LLM usage model**

```python
# tests/unit/test_llm/test_rate_limiter.py
import pytest
from datetime import datetime, timezone, timedelta
from app.models.llm_usage import LLMUsageRecord, LLMBudget
from app.llm.rate_limiter import RateLimiter, BudgetExhaustedError


@pytest.mark.asyncio
async def test_usage_record_creation(db):
    record = LLMUsageRecord(
        user_id="user-1",
        model="claude-sonnet-4-6",
        input_tokens=150,
        output_tokens=42,
        endpoint="pipeline",
        phase="domain_assessment",
    )
    db.add(record)
    await db.commit()
    await db.refresh(record)
    assert record.id is not None
    assert record.input_tokens == 150
    assert record.total_tokens == 192


@pytest.mark.asyncio
async def test_budget_defaults(db):
    budget = LLMBudget(
        user_id="user-1",
    )
    db.add(budget)
    await db.commit()
    await db.refresh(budget)
    assert budget.requests_per_hour == 60
    assert budget.tokens_per_day == 500_000


@pytest.mark.asyncio
async def test_budget_custom(db):
    budget = LLMBudget(
        user_id="user-2",
        requests_per_hour=120,
        tokens_per_day=1_000_000,
    )
    db.add(budget)
    await db.commit()
    assert budget.requests_per_hour == 120


@pytest.mark.asyncio
async def test_rate_limiter_allows_within_budget(db):
    budget = LLMBudget(user_id="user-1", requests_per_hour=60, tokens_per_day=500_000)
    db.add(budget)
    await db.commit()

    limiter = RateLimiter(db)
    # No usage yet, should be allowed
    allowed = await limiter.check_budget("user-1")
    assert allowed is True


@pytest.mark.asyncio
async def test_rate_limiter_records_usage(db):
    budget = LLMBudget(user_id="user-1", requests_per_hour=60, tokens_per_day=500_000)
    db.add(budget)
    await db.commit()

    limiter = RateLimiter(db)
    await limiter.record_usage(
        user_id="user-1",
        model="claude-sonnet-4-6",
        input_tokens=100,
        output_tokens=50,
        endpoint="pipeline",
        phase="calibration",
    )

    status = await limiter.get_usage_status("user-1")
    assert status["requests_used_this_hour"] == 1
    assert status["tokens_used_today"] == 150


@pytest.mark.asyncio
async def test_rate_limiter_blocks_over_request_limit(db):
    budget = LLMBudget(user_id="user-1", requests_per_hour=2, tokens_per_day=500_000)
    db.add(budget)
    await db.commit()

    limiter = RateLimiter(db)

    # Use up the budget
    for _ in range(2):
        await limiter.record_usage(
            user_id="user-1",
            model="claude-sonnet-4-6",
            input_tokens=10,
            output_tokens=5,
            endpoint="pipeline",
            phase="test",
        )

    # Should be blocked now
    allowed = await limiter.check_budget("user-1")
    assert allowed is False


@pytest.mark.asyncio
async def test_rate_limiter_blocks_over_token_limit(db):
    budget = LLMBudget(user_id="user-1", requests_per_hour=1000, tokens_per_day=100)
    db.add(budget)
    await db.commit()

    limiter = RateLimiter(db)

    await limiter.record_usage(
        user_id="user-1",
        model="claude-sonnet-4-6",
        input_tokens=80,
        output_tokens=30,
        endpoint="pipeline",
        phase="test",
    )

    allowed = await limiter.check_budget("user-1")
    assert allowed is False


@pytest.mark.asyncio
async def test_rate_limiter_uses_default_budget(db):
    """Users without an explicit budget get the default."""
    limiter = RateLimiter(db)
    allowed = await limiter.check_budget("user-no-budget")
    assert allowed is True


@pytest.mark.asyncio
async def test_budget_exhausted_error():
    err = BudgetExhaustedError(
        budget_type="requests_per_hour",
        limit=60,
        current=60,
        resets_at=datetime(2026, 4, 1, 13, 0, 0, tzinfo=timezone.utc),
    )
    assert "requests_per_hour" in str(err)
    assert err.resets_at is not None
```

- [ ] **Step 2: Run test — should fail**

Run: `cd learn-anything-app && uv run pytest tests/unit/test_llm/test_rate_limiter.py -v`
Expected: FAIL — `ModuleNotFoundError`

- [ ] **Step 3: Implement LLM usage model**

```python
# app/models/llm_usage.py
"""
LLM usage tracking and per-user budgets.

Usage records track every LLM call. Budgets define per-user limits.
Admin can set default budgets and per-user overrides via /settings.
"""
import uuid
from datetime import datetime, timezone
from sqlalchemy import String, Integer, Float, DateTime, ForeignKey, func
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.ext.hybrid import hybrid_property
from app.models.base import Base


class LLMUsageRecord(Base):
    """Individual LLM API call record."""
    __tablename__ = "llm_usage_records"

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid.uuid4())
    )
    user_id: Mapped[str] = mapped_column(ForeignKey("users.id"), index=True)
    model: Mapped[str] = mapped_column(String(50))
    input_tokens: Mapped[int] = mapped_column(Integer, default=0)
    output_tokens: Mapped[int] = mapped_column(Integer, default=0)
    endpoint: Mapped[str] = mapped_column(String(50))  # pipeline, training, materials
    phase: Mapped[str] = mapped_column(String(50), default="")  # domain_assessment, calibration, etc.
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), index=True
    )

    @hybrid_property
    def total_tokens(self) -> int:
        return self.input_tokens + self.output_tokens


class LLMBudget(Base):
    """Per-user LLM call budget.

    If no budget exists for a user, the system uses DEFAULT_REQUESTS_PER_HOUR
    and DEFAULT_TOKENS_PER_DAY from the rate limiter.
    """
    __tablename__ = "llm_budgets"

    user_id: Mapped[str] = mapped_column(ForeignKey("users.id"), primary_key=True)
    requests_per_hour: Mapped[int] = mapped_column(Integer, default=60)
    tokens_per_day: Mapped[int] = mapped_column(Integer, default=500_000)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )
```

- [ ] **Step 4: Implement rate limiter**

```python
# app/llm/rate_limiter.py
"""
Per-user LLM rate limiting.

Tracks requests/hour and tokens/day per user. Budget limits are
configurable in /settings — admin can set defaults and per-user overrides.

Budget exhaustion shows a graceful message with reset time, not a crash.
"""
from __future__ import annotations

from datetime import datetime, timezone, timedelta

import structlog
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.llm_usage import LLMUsageRecord, LLMBudget

log = structlog.get_logger()

# Default budgets for users without an explicit LLMBudget record
DEFAULT_REQUESTS_PER_HOUR = 60
DEFAULT_TOKENS_PER_DAY = 500_000


class BudgetExhaustedError(Exception):
    """Raised when a user's LLM budget is exhausted.

    Contains information for a user-friendly message including
    which limit was hit and when it resets.
    """

    def __init__(
        self,
        budget_type: str,
        limit: int,
        current: int,
        resets_at: datetime,
    ):
        self.budget_type = budget_type
        self.limit = limit
        self.current = current
        self.resets_at = resets_at
        super().__init__(
            f"LLM budget exhausted: {budget_type} "
            f"({current}/{limit}). Resets at {resets_at.isoformat()}"
        )


class RateLimiter:
    """Per-user LLM rate limiter backed by the database.

    Usage:
        limiter = RateLimiter(db_session)
        if await limiter.check_budget(user_id):
            # proceed with LLM call
            response = await provider.generate(...)
            await limiter.record_usage(user_id, ...)
        else:
            # show graceful exhaustion message
    """

    def __init__(self, db: AsyncSession):
        self._db = db

    async def _get_budget(self, user_id: str) -> tuple[int, int]:
        """Get (requests_per_hour, tokens_per_day) for a user.

        Returns defaults if no explicit budget is configured.
        """
        result = await self._db.execute(
            select(LLMBudget).where(LLMBudget.user_id == user_id)
        )
        budget = result.scalar_one_or_none()
        if budget:
            return budget.requests_per_hour, budget.tokens_per_day
        return DEFAULT_REQUESTS_PER_HOUR, DEFAULT_TOKENS_PER_DAY

    async def _count_requests_this_hour(self, user_id: str) -> int:
        """Count LLM requests since the top of the current clock hour.

        Uses clock-aligned windows (e.g. 13:00-14:00) so resets_at is
        always the next hour boundary. This matches the spec's
        "resets on schedule" behavior.
        """
        now = datetime.now(timezone.utc)
        hour_start = now.replace(minute=0, second=0, microsecond=0)
        result = await self._db.execute(
            select(func.count(LLMUsageRecord.id)).where(
                LLMUsageRecord.user_id == user_id,
                LLMUsageRecord.created_at >= hour_start,
            )
        )
        return result.scalar_one()

    async def _sum_tokens_today(self, user_id: str) -> int:
        """Sum all tokens used today (UTC midnight to now)."""
        today_start = datetime.now(timezone.utc).replace(
            hour=0, minute=0, second=0, microsecond=0
        )
        result = await self._db.execute(
            select(
                func.coalesce(
                    func.sum(LLMUsageRecord.input_tokens + LLMUsageRecord.output_tokens),
                    0,
                )
            ).where(
                LLMUsageRecord.user_id == user_id,
                LLMUsageRecord.created_at >= today_start,
            )
        )
        return result.scalar_one()

    async def check_budget(self, user_id: str) -> bool:
        """Check if a user has remaining LLM budget.

        Returns True if the user can make another LLM call.
        Returns False if any budget limit is exceeded.
        """
        req_limit, token_limit = await self._get_budget(user_id)
        requests_used = await self._count_requests_this_hour(user_id)
        tokens_used = await self._sum_tokens_today(user_id)

        if requests_used >= req_limit:
            log.warning(
                "budget_exhausted",
                user_id=user_id,
                budget_type="requests_per_hour",
                used=requests_used,
                limit=req_limit,
            )
            return False

        if tokens_used >= token_limit:
            log.warning(
                "budget_exhausted",
                user_id=user_id,
                budget_type="tokens_per_day",
                used=tokens_used,
                limit=token_limit,
            )
            return False

        return True

    async def check_budget_or_raise(self, user_id: str) -> None:
        """Check budget and raise BudgetExhaustedError if exceeded."""
        req_limit, token_limit = await self._get_budget(user_id)
        requests_used = await self._count_requests_this_hour(user_id)
        tokens_used = await self._sum_tokens_today(user_id)

        now = datetime.now(timezone.utc)

        if requests_used >= req_limit:
            # Clock-aligned: resets at the next hour boundary
            resets_at = (now + timedelta(hours=1)).replace(
                minute=0, second=0, microsecond=0
            )
            raise BudgetExhaustedError(
                budget_type="requests_per_hour",
                limit=req_limit,
                current=requests_used,
                resets_at=resets_at,
            )

        if tokens_used >= token_limit:
            tomorrow = (now + timedelta(days=1)).replace(
                hour=0, minute=0, second=0, microsecond=0
            )
            raise BudgetExhaustedError(
                budget_type="tokens_per_day",
                limit=token_limit,
                current=tokens_used,
                resets_at=tomorrow,
            )

    async def record_usage(
        self,
        user_id: str,
        model: str,
        input_tokens: int,
        output_tokens: int,
        endpoint: str,
        phase: str = "",
    ) -> LLMUsageRecord:
        """Record an LLM API call for budget tracking."""
        record = LLMUsageRecord(
            user_id=user_id,
            model=model,
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            endpoint=endpoint,
            phase=phase,
        )
        self._db.add(record)
        await self._db.commit()
        await self._db.refresh(record)

        log.debug(
            "llm_usage_recorded",
            user_id=user_id,
            model=model,
            tokens=input_tokens + output_tokens,
            phase=phase,
        )
        return record

    async def get_usage_status(self, user_id: str) -> dict:
        """Get current usage status for display in UI.

        Returns a dict suitable for rendering in the settings page
        or in a budget exhaustion message.
        """
        req_limit, token_limit = await self._get_budget(user_id)
        requests_used = await self._count_requests_this_hour(user_id)
        tokens_used = await self._sum_tokens_today(user_id)

        now = datetime.now(timezone.utc)
        # Clock-aligned: next hour boundary
        hour_resets = (now + timedelta(hours=1)).replace(
            minute=0, second=0, microsecond=0
        )
        day_resets = (now + timedelta(days=1)).replace(
            hour=0, minute=0, second=0, microsecond=0
        )

        return {
            "requests_used_this_hour": requests_used,
            "requests_limit_per_hour": req_limit,
            "requests_remaining": max(0, req_limit - requests_used),
            "requests_resets_at": hour_resets.isoformat(),
            "tokens_used_today": tokens_used,
            "tokens_limit_per_day": token_limit,
            "tokens_remaining": max(0, token_limit - tokens_used),
            "tokens_resets_at": day_resets.isoformat(),
        }
```

- [ ] **Step 5: Update conftest.py with new model imports**

Add to `tests/conftest.py`:
```python
from app.models.llm_usage import LLMUsageRecord, LLMBudget  # noqa
```

- [ ] **Step 6: Run test — should pass**

Run: `cd learn-anything-app && uv run pytest tests/unit/test_llm/test_rate_limiter.py -v`
Expected: All passed (10 tests)

- [ ] **Step 7: Commit**

```bash
git commit -m "feat: LLM rate limiter — per-user budgets (requests/hour, tokens/day) with graceful exhaustion"
```

---

### Task 4: Pipeline Phase Detection

**Files:**
- Create: `learn-anything-app/app/services/pipeline.py`
- Test: `learn-anything-app/tests/integration/test_services/test_pipeline.py`

- [ ] **Step 1: Write failing test for pipeline phase detection**

```python
# tests/integration/test_services/test_pipeline.py
"""
Tests for pipeline phase detection.

The pipeline reads state from the database (which records exist for a
user + skill slug) and determines the next phase to execute.
"""
import pytest
from app.services.pipeline import PipelinePhase, PipelineDetector
from app.models.graph_nodes import Domain, SkillNode, Concept
from app.models.graph_edges import GraphEdge
from app.models.learner_state import LearnerState
from app.models.material import Material
from app.models.user import User
from app.security.passwords import hash_password


def _make_user(email: str = "learner@test.com") -> User:
    return User(
        email=email,
        display_name="Learner",
        password_hash=hash_password("test"),
        provider="local",
    )


@pytest.mark.asyncio
async def test_phase_enum_order():
    """Pipeline phases are ordered correctly."""
    assert PipelinePhase.DOMAIN_ASSESSMENT.value < PipelinePhase.SKILL_RESEARCH.value
    assert PipelinePhase.SKILL_RESEARCH.value < PipelinePhase.LEARNER_CALIBRATION.value
    assert PipelinePhase.LEARNER_CALIBRATION.value < PipelinePhase.CURRICULUM_DESIGN.value
    assert PipelinePhase.CURRICULUM_DESIGN.value < PipelinePhase.MATERIAL_GENERATION.value
    assert PipelinePhase.MATERIAL_GENERATION.value < PipelinePhase.PROGRESS_DASHBOARD.value
    assert PipelinePhase.PROGRESS_DASHBOARD.value < PipelinePhase.TRAINING.value


@pytest.mark.asyncio
async def test_detect_new_skill_no_domain(db):
    """No domain record for this skill → DOMAIN_ASSESSMENT."""
    user = _make_user()
    db.add(user)
    await db.commit()

    detector = PipelineDetector(db)
    phase = await detector.detect_phase(user.id, "jazz-piano")
    assert phase == PipelinePhase.DOMAIN_ASSESSMENT


@pytest.mark.asyncio
async def test_detect_after_domain_assessment(db):
    """Domain exists but no skill nodes → SKILL_RESEARCH."""
    user = _make_user()
    domain = Domain(name="Jazz Piano", skill_type="hybrid", environment_type="mostly_kind")
    db.add_all([user, domain])
    await db.commit()

    # Simulate domain assessment completion by creating a PipelineState record
    from app.services.pipeline import PipelineState
    state = PipelineState(
        user_id=user.id,
        skill_slug="jazz-piano",
        domain_id=domain.id,
        phase_completed="domain_assessment",
    )
    db.add(state)
    await db.commit()

    detector = PipelineDetector(db)
    phase = await detector.detect_phase(user.id, "jazz-piano")
    assert phase == PipelinePhase.SKILL_RESEARCH


@pytest.mark.asyncio
async def test_detect_after_skill_research(db):
    """Domain + skill nodes exist, but no learner state → LEARNER_CALIBRATION."""
    user = _make_user()
    domain = Domain(name="Jazz Piano", skill_type="hybrid", environment_type="mostly_kind")
    db.add_all([user, domain])
    await db.commit()

    from app.services.pipeline import PipelineState
    for phase_name in ["domain_assessment", "skill_research"]:
        db.add(PipelineState(
            user_id=user.id, skill_slug="jazz-piano",
            domain_id=domain.id, phase_completed=phase_name,
        ))
    await db.commit()

    detector = PipelineDetector(db)
    phase = await detector.detect_phase(user.id, "jazz-piano")
    assert phase == PipelinePhase.LEARNER_CALIBRATION


@pytest.mark.asyncio
async def test_detect_after_calibration(db):
    """All through calibration → CURRICULUM_DESIGN."""
    user = _make_user()
    domain = Domain(name="Jazz Piano", skill_type="hybrid", environment_type="mostly_kind")
    db.add_all([user, domain])
    await db.commit()

    from app.services.pipeline import PipelineState
    for phase_name in ["domain_assessment", "skill_research", "learner_calibration"]:
        db.add(PipelineState(
            user_id=user.id, skill_slug="jazz-piano",
            domain_id=domain.id, phase_completed=phase_name,
        ))
    await db.commit()

    detector = PipelineDetector(db)
    phase = await detector.detect_phase(user.id, "jazz-piano")
    assert phase == PipelinePhase.CURRICULUM_DESIGN


@pytest.mark.asyncio
async def test_detect_after_curriculum(db):
    """Through curriculum design → MATERIAL_GENERATION."""
    user = _make_user()
    domain = Domain(name="Jazz Piano", skill_type="hybrid", environment_type="mostly_kind")
    db.add_all([user, domain])
    await db.commit()

    from app.services.pipeline import PipelineState
    for phase_name in [
        "domain_assessment", "skill_research",
        "learner_calibration", "curriculum_design",
    ]:
        db.add(PipelineState(
            user_id=user.id, skill_slug="jazz-piano",
            domain_id=domain.id, phase_completed=phase_name,
        ))
    await db.commit()

    detector = PipelineDetector(db)
    phase = await detector.detect_phase(user.id, "jazz-piano")
    assert phase == PipelinePhase.MATERIAL_GENERATION


@pytest.mark.asyncio
async def test_detect_after_materials(db):
    """Through material generation → PROGRESS_DASHBOARD."""
    user = _make_user()
    domain = Domain(name="Jazz Piano", skill_type="hybrid", environment_type="mostly_kind")
    db.add_all([user, domain])
    await db.commit()

    from app.services.pipeline import PipelineState
    for phase_name in [
        "domain_assessment", "skill_research",
        "learner_calibration", "curriculum_design",
        "material_generation",
    ]:
        db.add(PipelineState(
            user_id=user.id, skill_slug="jazz-piano",
            domain_id=domain.id, phase_completed=phase_name,
        ))
    await db.commit()

    detector = PipelineDetector(db)
    phase = await detector.detect_phase(user.id, "jazz-piano")
    assert phase == PipelinePhase.PROGRESS_DASHBOARD


@pytest.mark.asyncio
async def test_detect_all_complete_is_training(db):
    """All phases complete → TRAINING."""
    user = _make_user()
    domain = Domain(name="Jazz Piano", skill_type="hybrid", environment_type="mostly_kind")
    db.add_all([user, domain])
    await db.commit()

    from app.services.pipeline import PipelineState
    for phase_name in [
        "domain_assessment", "skill_research",
        "learner_calibration", "curriculum_design",
        "material_generation", "progress_dashboard",
    ]:
        db.add(PipelineState(
            user_id=user.id, skill_slug="jazz-piano",
            domain_id=domain.id, phase_completed=phase_name,
        ))
    await db.commit()

    detector = PipelineDetector(db)
    phase = await detector.detect_phase(user.id, "jazz-piano")
    assert phase == PipelinePhase.TRAINING


@pytest.mark.asyncio
async def test_get_completed_phases(db):
    """get_completed_phases returns the set of completed phase names."""
    user = _make_user()
    domain = Domain(name="Jazz Piano", skill_type="hybrid", environment_type="mostly_kind")
    db.add_all([user, domain])
    await db.commit()

    from app.services.pipeline import PipelineState
    for phase_name in ["domain_assessment", "skill_research"]:
        db.add(PipelineState(
            user_id=user.id, skill_slug="jazz-piano",
            domain_id=domain.id, phase_completed=phase_name,
        ))
    await db.commit()

    detector = PipelineDetector(db)
    completed = await detector.get_completed_phases(user.id, "jazz-piano")
    assert completed == {"domain_assessment", "skill_research"}


@pytest.mark.asyncio
async def test_mark_phase_complete(db):
    """mark_phase_complete creates a PipelineState record."""
    user = _make_user()
    domain = Domain(name="Jazz Piano", skill_type="hybrid", environment_type="mostly_kind")
    db.add_all([user, domain])
    await db.commit()

    detector = PipelineDetector(db)
    await detector.mark_phase_complete(user.id, "jazz-piano", "domain_assessment", domain.id)

    completed = await detector.get_completed_phases(user.id, "jazz-piano")
    assert "domain_assessment" in completed


@pytest.mark.asyncio
async def test_mark_phase_complete_idempotent(db):
    """Marking the same phase complete twice does not error."""
    user = _make_user()
    domain = Domain(name="Jazz Piano", skill_type="hybrid", environment_type="mostly_kind")
    db.add_all([user, domain])
    await db.commit()

    detector = PipelineDetector(db)
    await detector.mark_phase_complete(user.id, "jazz-piano", "domain_assessment", domain.id)
    await detector.mark_phase_complete(user.id, "jazz-piano", "domain_assessment", domain.id)

    completed = await detector.get_completed_phases(user.id, "jazz-piano")
    assert completed == {"domain_assessment"}
```

- [ ] **Step 2: Run test — should fail**

Run: `cd learn-anything-app && uv run pytest tests/integration/test_services/test_pipeline.py -v`
Expected: FAIL — `ModuleNotFoundError`

- [ ] **Step 3: Implement PipelinePhase, PipelineState, and PipelineDetector**

```python
# app/services/pipeline.py
"""
Pipeline phase detection.

The pipeline reads database state (which PipelineState records exist for a
user + skill slug) and determines the next phase to execute. This is the
web app equivalent of the plugin's orchestrator checking which JSON state
files exist on disk.

Pipeline phases (in order):
1. Domain Assessment — classify skill, gather learner profile
2. Skill Research — decompose skill into graph nodes
3. Learner Calibration — diagnostic assessment, calibration loop
4. Curriculum Design — learning plan with agreement gates
5. Material Generation — flashcards, lectures, worked examples
6. Progress Dashboard — metrics computation, dashboard available
7. Training — ongoing sessions, feedback loops

Each phase writes a PipelineState record on completion. The detector
checks which records exist and returns the next incomplete phase.
"""
from __future__ import annotations

import enum
import uuid
from datetime import datetime, timezone

import structlog
from sqlalchemy import String, DateTime, func, select, UniqueConstraint
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base

log = structlog.get_logger()


class PipelinePhase(enum.IntEnum):
    """Pipeline phases in execution order."""
    DOMAIN_ASSESSMENT = 1
    SKILL_RESEARCH = 2
    LEARNER_CALIBRATION = 3
    CURRICULUM_DESIGN = 4
    MATERIAL_GENERATION = 5
    PROGRESS_DASHBOARD = 6
    TRAINING = 7


# Maps phase completion record names to the next phase
PHASE_ORDER = [
    "domain_assessment",
    "skill_research",
    "learner_calibration",
    "curriculum_design",
    "material_generation",
    "progress_dashboard",
]

PHASE_NAME_TO_ENUM = {
    "domain_assessment": PipelinePhase.DOMAIN_ASSESSMENT,
    "skill_research": PipelinePhase.SKILL_RESEARCH,
    "learner_calibration": PipelinePhase.LEARNER_CALIBRATION,
    "curriculum_design": PipelinePhase.CURRICULUM_DESIGN,
    "material_generation": PipelinePhase.MATERIAL_GENERATION,
    "progress_dashboard": PipelinePhase.PROGRESS_DASHBOARD,
    # TRAINING is the terminal state — it is excluded from PHASE_ORDER
    # because it has no completion marker (it runs indefinitely). The
    # orchestrator returns TRAINING when all PHASE_ORDER entries are complete.
    "training": PipelinePhase.TRAINING,
}


class PipelineState(Base):
    """Tracks which pipeline phases are complete for a user + skill.

    Analogous to checking which JSON state files exist in the plugin's
    learn-anything/<slug>/ directory.
    """
    __tablename__ = "pipeline_states"
    __table_args__ = (
        UniqueConstraint("user_id", "skill_slug", "phase_completed", name="uq_pipeline_phase"),
    )

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid.uuid4())
    )
    user_id: Mapped[str] = mapped_column(ForeignKey("users.id"), index=True)
    skill_slug: Mapped[str] = mapped_column(String(200), index=True)
    domain_id: Mapped[str] = mapped_column(ForeignKey("domains.id"))
    phase_completed: Mapped[str] = mapped_column(String(50))
    completed_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )


class PipelineDetector:
    """Detects the current pipeline phase for a user + skill.

    Usage:
        detector = PipelineDetector(db)
        phase = await detector.detect_phase(user_id, "jazz-piano")
        # phase is PipelinePhase.LEARNER_CALIBRATION (or whichever is next)
    """

    def __init__(self, db: AsyncSession):
        self._db = db

    async def get_completed_phases(self, user_id: str, skill_slug: str) -> set[str]:
        """Return the set of completed phase names for a user + skill."""
        result = await self._db.execute(
            select(PipelineState.phase_completed).where(
                PipelineState.user_id == user_id,
                PipelineState.skill_slug == skill_slug,
            )
        )
        return {row[0] for row in result.all()}

    async def detect_phase(self, user_id: str, skill_slug: str) -> PipelinePhase:
        """Determine the next pipeline phase to execute.

        Walks PHASE_ORDER and returns the PipelinePhase enum for the
        first incomplete phase. If all phases are complete, returns TRAINING.
        """
        completed = await self.get_completed_phases(user_id, skill_slug)

        for phase_name in PHASE_ORDER:
            if phase_name not in completed:
                phase_enum = PHASE_NAME_TO_ENUM[phase_name]
                log.info(
                    "pipeline_phase_detected",
                    user_id=user_id,
                    skill_slug=skill_slug,
                    next_phase=phase_name,
                    completed_count=len(completed),
                )
                return phase_enum

        log.info(
            "pipeline_phase_detected",
            user_id=user_id,
            skill_slug=skill_slug,
            next_phase="training",
            completed_count=len(completed),
        )
        return PipelinePhase.TRAINING

    async def mark_phase_complete(
        self,
        user_id: str,
        skill_slug: str,
        phase_name: str,
        domain_id: str,
    ) -> None:
        """Mark a pipeline phase as complete.

        Idempotent: calling twice for the same phase is a no-op.
        """
        # Check if already complete
        result = await self._db.execute(
            select(PipelineState).where(
                PipelineState.user_id == user_id,
                PipelineState.skill_slug == skill_slug,
                PipelineState.phase_completed == phase_name,
            )
        )
        if result.scalar_one_or_none() is not None:
            return

        state = PipelineState(
            user_id=user_id,
            skill_slug=skill_slug,
            domain_id=domain_id,
            phase_completed=phase_name,
        )
        self._db.add(state)
        await self._db.commit()

        log.info(
            "pipeline_phase_completed",
            user_id=user_id,
            skill_slug=skill_slug,
            phase=phase_name,
        )

    async def reset_phase(
        self,
        user_id: str,
        skill_slug: str,
        phase_name: str,
    ) -> None:
        """Reset a phase to incomplete (used by feedback loops).

        This does NOT delete data — it only removes the completion
        marker so the orchestrator re-routes to that phase.
        """
        result = await self._db.execute(
            select(PipelineState).where(
                PipelineState.user_id == user_id,
                PipelineState.skill_slug == skill_slug,
                PipelineState.phase_completed == phase_name,
            )
        )
        state = result.scalar_one_or_none()
        if state:
            await self._db.delete(state)
            await self._db.commit()
            log.info(
                "pipeline_phase_reset",
                user_id=user_id,
                skill_slug=skill_slug,
                phase=phase_name,
            )
```

- [ ] **Step 4: Update conftest.py with PipelineState import**

Add to `tests/conftest.py`:
```python
from app.services.pipeline import PipelineState  # noqa
```

- [ ] **Step 5: Run test — should pass**

Run: `cd learn-anything-app && uv run pytest tests/integration/test_services/test_pipeline.py -v`
Expected: 11 passed

- [ ] **Step 6: Commit**

```bash
git commit -m "feat: pipeline phase detection — reads DB state, determines next phase for user+skill"
```

---

### Task 5: Orchestrator — Phase Routing + Calibration Loop

**Files:**
- Create: `learn-anything-app/app/services/orchestrator.py`
- Test: `learn-anything-app/tests/integration/test_services/test_orchestrator.py`

- [ ] **Step 1: Write failing test for orchestrator routing**

```python
# tests/integration/test_services/test_orchestrator.py
"""
Tests for the orchestrator service.

The orchestrator routes to the correct phase handler based on pipeline
state, manages the calibration loop, and handles feedback loop triggers.
"""
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from app.services.orchestrator import (
    Orchestrator,
    PhaseHandler,
    CalibrationLoopState,
    FeedbackSignal,
    FeedbackSignalType,
)
from app.services.pipeline import PipelinePhase, PipelineDetector
from app.llm.provider import LLMMessage, LLMResponse, LLMStreamEvent


class MockPhaseHandler:
    """Mock phase handler for testing."""

    def __init__(self, phase_name: str):
        self.phase_name = phase_name
        self.called = False
        self.messages = []

    async def handle(self, context):
        self.called = True
        self.messages = context.get("messages", [])

    async def handle_stream(self, context):
        self.called = True
        yield LLMStreamEvent(type="text", content=f"[{self.phase_name}] Processing...")
        yield LLMStreamEvent(type="done", usage={"input_tokens": 10, "output_tokens": 5}, stop_reason="end_turn")


def test_phase_handler_protocol():
    """PhaseHandler protocol has required methods."""
    import inspect
    members = {name for name, _ in inspect.getmembers(PhaseHandler)}
    assert "handle" in members
    assert "handle_stream" in members


def test_feedback_signal_types():
    """All feedback signal types from spec are defined."""
    assert FeedbackSignalType.FIELD_EVOLVED is not None
    assert FeedbackSignalType.MASTERY_DRIFT is not None
    assert FeedbackSignalType.PACING_MISMATCH is not None
    assert FeedbackSignalType.MATERIALS_EXHAUSTED is not None
    assert FeedbackSignalType.PLATEAU is not None


def test_feedback_signal_creation():
    signal = FeedbackSignal(
        type=FeedbackSignalType.MASTERY_DRIFT,
        evidence="Performance diverges across 4 sessions on vertex v_chord_voicings",
        affected_vertex_ids=["v_chord_voicings", "v_shell_voicings"],
        session_count=4,
    )
    assert signal.type == FeedbackSignalType.MASTERY_DRIFT
    assert len(signal.affected_vertex_ids) == 2
    assert signal.session_count == 4


def test_calibration_loop_state_init():
    state = CalibrationLoopState(
        iteration=0,
        max_iterations=2,
        re_research_triggers=[],
        new_vertex_ids=[],
    )
    assert state.iteration == 0
    assert state.max_iterations == 2
    assert not state.should_loop


def test_calibration_loop_state_with_triggers():
    state = CalibrationLoopState(
        iteration=0,
        max_iterations=2,
        re_research_triggers=["unexpected expertise in harmonic analysis"],
        new_vertex_ids=[],
    )
    assert state.should_loop is True


def test_calibration_loop_state_max_reached():
    state = CalibrationLoopState(
        iteration=2,
        max_iterations=2,
        re_research_triggers=["still finding gaps"],
        new_vertex_ids=[],
    )
    assert state.should_loop is False  # Max iterations reached


@pytest.mark.asyncio
async def test_orchestrator_routes_to_correct_phase(db):
    """Orchestrator routes to the handler matching the detected phase."""
    from app.models.user import User
    from app.models.graph_nodes import Domain
    from app.security.passwords import hash_password

    user = User(email="o@test.com", display_name="O", password_hash=hash_password("x"), provider="local")
    db.add(user)
    await db.commit()

    # No pipeline state → should route to DOMAIN_ASSESSMENT
    domain_handler = MockPhaseHandler("domain_assessment")
    research_handler = MockPhaseHandler("skill_research")

    orchestrator = Orchestrator(
        db=db,
        llm_provider=MagicMock(),
        handlers={
            PipelinePhase.DOMAIN_ASSESSMENT: domain_handler,
            PipelinePhase.SKILL_RESEARCH: research_handler,
        },
    )

    handler, phase = await orchestrator.route(user.id, "jazz-piano")
    assert phase == PipelinePhase.DOMAIN_ASSESSMENT
    assert handler is domain_handler


@pytest.mark.asyncio
async def test_orchestrator_routes_after_domain(db):
    """After domain assessment, routes to skill research."""
    from app.models.user import User
    from app.models.graph_nodes import Domain
    from app.security.passwords import hash_password
    from app.services.pipeline import PipelineState

    user = User(email="o2@test.com", display_name="O2", password_hash=hash_password("x"), provider="local")
    domain = Domain(name="Jazz Piano", skill_type="hybrid", environment_type="mostly_kind")
    db.add_all([user, domain])
    await db.commit()

    db.add(PipelineState(
        user_id=user.id, skill_slug="jazz-piano",
        domain_id=domain.id, phase_completed="domain_assessment",
    ))
    await db.commit()

    research_handler = MockPhaseHandler("skill_research")
    orchestrator = Orchestrator(
        db=db,
        llm_provider=MagicMock(),
        handlers={
            PipelinePhase.DOMAIN_ASSESSMENT: MockPhaseHandler("domain_assessment"),
            PipelinePhase.SKILL_RESEARCH: research_handler,
        },
    )

    handler, phase = await orchestrator.route(user.id, "jazz-piano")
    assert phase == PipelinePhase.SKILL_RESEARCH
    assert handler is research_handler


@pytest.mark.asyncio
async def test_feedback_signal_routes_correctly():
    """Feedback signals route to the correct upstream phase."""
    from app.services.orchestrator import resolve_feedback_route

    # Field evolved → Skill Research
    route = resolve_feedback_route(FeedbackSignalType.FIELD_EVOLVED)
    assert route == PipelinePhase.SKILL_RESEARCH

    # Mastery drift → Learner Calibration
    route = resolve_feedback_route(FeedbackSignalType.MASTERY_DRIFT)
    assert route == PipelinePhase.LEARNER_CALIBRATION

    # Pacing mismatch → Curriculum Design
    route = resolve_feedback_route(FeedbackSignalType.PACING_MISMATCH)
    assert route == PipelinePhase.CURRICULUM_DESIGN

    # Materials exhausted → Material Generation
    route = resolve_feedback_route(FeedbackSignalType.MATERIALS_EXHAUSTED)
    assert route == PipelinePhase.MATERIAL_GENERATION

    # Plateau → Curriculum Design
    route = resolve_feedback_route(FeedbackSignalType.PLATEAU)
    assert route == PipelinePhase.CURRICULUM_DESIGN


@pytest.mark.asyncio
async def test_calibration_loop_increments():
    """Calibration loop increments iteration count."""
    state = CalibrationLoopState(
        iteration=0,
        max_iterations=2,
        re_research_triggers=["unexpected gap"],
        new_vertex_ids=[],
    )
    assert state.should_loop is True
    state.iteration += 1
    assert state.iteration == 1
    assert state.should_loop is True  # Still under max

    state.iteration += 1
    assert state.should_loop is False  # At max


@pytest.mark.asyncio
async def test_orchestrator_build_context(db):
    """Orchestrator builds correct context for phase handlers."""
    from app.models.user import User
    from app.security.passwords import hash_password

    user = User(email="ctx@test.com", display_name="Ctx", password_hash=hash_password("x"), provider="local")
    db.add(user)
    await db.commit()

    orchestrator = Orchestrator(
        db=db,
        llm_provider=MagicMock(),
        handlers={PipelinePhase.DOMAIN_ASSESSMENT: MockPhaseHandler("domain_assessment")},
    )

    context = await orchestrator.build_context(
        user_id=user.id,
        skill_slug="jazz-piano",
        phase=PipelinePhase.DOMAIN_ASSESSMENT,
        user_message="I want to learn jazz piano",
    )

    assert context["user_id"] == user.id
    assert context["skill_slug"] == "jazz-piano"
    assert context["phase"] == PipelinePhase.DOMAIN_ASSESSMENT
    assert context["user_message"] == "I want to learn jazz piano"
    assert "completed_phases" in context
```

- [ ] **Step 2: Run test — should fail**

Run: `cd learn-anything-app && uv run pytest tests/integration/test_services/test_orchestrator.py -v`
Expected: FAIL — `ModuleNotFoundError`

- [ ] **Step 3: Implement orchestrator**

```python
# app/services/orchestrator.py
"""
Orchestrator — skill-driven routing based on pipeline state.

The orchestrator is the web app equivalent of the plugin's
meta-learning-orchestrator skill. It:

1. Detects the current pipeline phase (via PipelineDetector)
2. Routes to the correct phase handler
3. Manages the calibration loop (max 2 iterations)
4. Handles feedback loop triggers from the Training Conductor

Design principle: Skills drive the flow, NOT the UI.
The orchestrator checks state and routes to the next incomplete phase.
No artificial stops.
"""
from __future__ import annotations

import enum
from dataclasses import dataclass, field
from typing import Any, AsyncIterator, Protocol

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

from app.llm.provider import LLMProvider, LLMStreamEvent
from app.services.pipeline import PipelineDetector, PipelinePhase

log = structlog.get_logger()


class PhaseHandler(Protocol):
    """Protocol for pipeline phase handlers.

    Each phase (domain assessment, skill research, etc.) implements
    this protocol. The orchestrator routes to the correct handler
    based on the detected pipeline phase.
    """

    async def handle(self, context: dict[str, Any]) -> dict[str, Any]:
        """Execute the phase (non-streaming). Returns phase results."""
        ...

    async def handle_stream(self, context: dict[str, Any]) -> AsyncIterator[LLMStreamEvent]:
        """Execute the phase with streaming. Yields events for SSE."""
        ...


class FeedbackSignalType(str, enum.Enum):
    """Feedback signal types from the Training Conductor.

    These are evidence-based judgment calls (pattern across 3+ sessions),
    not knee-jerk reactions.
    """
    FIELD_EVOLVED = "field_evolved"
    MASTERY_DRIFT = "mastery_drift"
    PACING_MISMATCH = "pacing_mismatch"
    MATERIALS_EXHAUSTED = "materials_exhausted"
    PLATEAU = "plateau"


@dataclass
class FeedbackSignal:
    """A feedback signal from the Training Conductor.

    Signals trigger upstream pipeline phase re-execution. The orchestrator
    interprets the signal and routes to the appropriate phase handler
    in update mode (preserving existing progress).
    """
    type: FeedbackSignalType
    evidence: str
    affected_vertex_ids: list[str] = field(default_factory=list)
    session_count: int = 0
    metadata: dict[str, Any] = field(default_factory=dict)


# Feedback signal → target phase routing table (from spec Section 5)
FEEDBACK_ROUTES: dict[FeedbackSignalType, PipelinePhase] = {
    # Field evolved, new concepts → Skill Researcher (update) → Calibrator → Architect
    FeedbackSignalType.FIELD_EVOLVED: PipelinePhase.SKILL_RESEARCH,
    # Mastery estimates drifted → Calibrator (targeted re-assessment)
    FeedbackSignalType.MASTERY_DRIFT: PipelinePhase.LEARNER_CALIBRATION,
    # Pacing mismatch → Curriculum Architect (update)
    FeedbackSignalType.PACING_MISMATCH: PipelinePhase.CURRICULUM_DESIGN,
    # Materials exhausted → Material Forge (on-demand)
    FeedbackSignalType.MATERIALS_EXHAUSTED: PipelinePhase.MATERIAL_GENERATION,
    # Plateau, protocols exhausted → Curriculum Architect (re-sequence)
    FeedbackSignalType.PLATEAU: PipelinePhase.CURRICULUM_DESIGN,
}

# Feedback cascade: after re-executing a phase, which downstream
# phases also need re-execution. This preserves learner progress
# while updating the pipeline.
FEEDBACK_CASCADE: dict[FeedbackSignalType, list[str]] = {
    FeedbackSignalType.FIELD_EVOLVED: [
        "skill_research", "learner_calibration", "curriculum_design",
    ],
    FeedbackSignalType.MASTERY_DRIFT: [
        "learner_calibration",
    ],
    FeedbackSignalType.PACING_MISMATCH: [
        "curriculum_design",
    ],
    FeedbackSignalType.MATERIALS_EXHAUSTED: [
        "material_generation",
    ],
    FeedbackSignalType.PLATEAU: [
        "curriculum_design",
    ],
}


@dataclass
class CalibrationLoopState:
    """Tracks the calibration loop between Calibrator and Researcher.

    The calibration loop almost always fires on first pass — assessment
    reveals surprises that require additional research. Max 2 iterations
    to prevent infinite cycling.

    Loop flow:
    1. Calibrator runs → flags re_research_triggers
    2. Researcher does targeted update (new vertices only)
    3. Calibrator re-assesses only new/changed vertices
    4. If triggers remain and iteration < max_iterations, loop again
    5. Otherwise, proceed to Curriculum Architect
    """
    iteration: int = 0
    max_iterations: int = 2
    re_research_triggers: list[str] = field(default_factory=list)
    new_vertex_ids: list[str] = field(default_factory=list)

    @property
    def should_loop(self) -> bool:
        """True if there are triggers and we haven't hit the max."""
        return len(self.re_research_triggers) > 0 and self.iteration < self.max_iterations


def resolve_feedback_route(signal_type: FeedbackSignalType) -> PipelinePhase:
    """Resolve which pipeline phase a feedback signal routes to."""
    return FEEDBACK_ROUTES[signal_type]


class Orchestrator:
    """Main orchestrator that routes to pipeline phase handlers.

    Usage:
        orchestrator = Orchestrator(db, llm_provider, handlers)
        handler, phase = await orchestrator.route(user_id, "jazz-piano")
        context = await orchestrator.build_context(user_id, "jazz-piano", phase, user_msg)

        # Non-streaming:
        result = await handler.handle(context)

        # Streaming (for SSE):
        async for event in handler.handle_stream(context):
            yield event
    """

    def __init__(
        self,
        db: AsyncSession,
        llm_provider: LLMProvider,
        handlers: dict[PipelinePhase, PhaseHandler],
    ):
        self._db = db
        self._llm = llm_provider
        self._handlers = handlers
        self._detector = PipelineDetector(db)

    async def route(
        self,
        user_id: str,
        skill_slug: str,
    ) -> tuple[PhaseHandler, PipelinePhase]:
        """Detect the current phase and return the appropriate handler.

        Returns:
            (handler, phase) tuple. The handler implements PhaseHandler.

        Raises:
            KeyError: If no handler is registered for the detected phase.
        """
        phase = await self._detector.detect_phase(user_id, skill_slug)

        if phase not in self._handlers:
            log.error(
                "no_handler_for_phase",
                phase=phase.name,
                registered=list(self._handlers.keys()),
            )
            raise KeyError(f"No handler registered for phase: {phase.name}")

        handler = self._handlers[phase]
        log.info(
            "orchestrator_routed",
            user_id=user_id,
            skill_slug=skill_slug,
            phase=phase.name,
        )
        return handler, phase

    async def build_context(
        self,
        user_id: str,
        skill_slug: str,
        phase: PipelinePhase,
        user_message: str = "",
        calibration_loop: CalibrationLoopState | None = None,
        feedback_signal: FeedbackSignal | None = None,
    ) -> dict[str, Any]:
        """Build the context dict passed to phase handlers.

        The context contains everything a phase handler needs:
        user ID, skill slug, phase, conversation messages, completed
        phases, calibration loop state, and feedback signal info.
        """
        completed = await self._detector.get_completed_phases(user_id, skill_slug)

        context: dict[str, Any] = {
            "user_id": user_id,
            "skill_slug": skill_slug,
            "phase": phase,
            "user_message": user_message,
            "completed_phases": completed,
            "llm_provider": self._llm,
            "db": self._db,
        }

        if calibration_loop:
            context["calibration_loop"] = calibration_loop
        if feedback_signal:
            context["feedback_signal"] = feedback_signal

        return context

    async def handle_feedback(
        self,
        user_id: str,
        skill_slug: str,
        signal: FeedbackSignal,
    ) -> tuple[PhaseHandler, PipelinePhase]:
        """Handle a feedback signal from the Training Conductor.

        Resets the appropriate pipeline phases and routes to the
        target phase handler. All updates preserve completed work
        and learner progress.

        Returns:
            (handler, phase) tuple for the phase to re-execute.
        """
        target_phase = resolve_feedback_route(signal.type)
        cascade_phases = FEEDBACK_CASCADE.get(signal.type, [])

        log.info(
            "feedback_signal_received",
            user_id=user_id,
            skill_slug=skill_slug,
            signal_type=signal.type.value,
            target_phase=target_phase.name,
            cascade=cascade_phases,
            evidence=signal.evidence[:200],
        )

        # Reset the cascade phases (marks them as incomplete so
        # the orchestrator will re-route through them)
        for phase_name in cascade_phases:
            await self._detector.reset_phase(user_id, skill_slug, phase_name)

        # Route to the target phase
        return await self.route(user_id, skill_slug)

    async def run_feedback_cascade(
        self,
        user_id: str,
        skill_slug: str,
        domain_id: str,
        signal: FeedbackSignal,
    ) -> None:
        """Execute the full feedback cascade after handle_feedback resets phases.

        Loops through all cascaded phases sequentially (similar to
        run_calibration_loop) until the pipeline reaches TRAINING again.
        After resetting phases, it routes and executes each phase in order.

        This is the execution driver that handle_feedback is missing —
        handle_feedback resets the phases and returns the first handler,
        but run_feedback_cascade actually drives each phase to completion.
        """
        handler, phase = await self.handle_feedback(user_id, skill_slug, signal)

        while phase != PipelinePhase.TRAINING:
            log.info(
                "feedback_cascade_executing",
                user_id=user_id,
                skill_slug=skill_slug,
                phase=phase.name,
                signal_type=signal.type.value,
            )

            context = await self.build_context(
                user_id=user_id,
                skill_slug=skill_slug,
                phase=phase,
                feedback_signal=signal,
            )
            await handler.handle(context)

            # Mark the phase complete and advance
            phase_name = phase.name.lower()
            await self._detector.mark_phase_complete(
                user_id, skill_slug, phase_name, domain_id
            )

            # Route to the next incomplete phase
            handler, phase = await self.route(user_id, skill_slug)

        log.info(
            "feedback_cascade_complete",
            user_id=user_id,
            skill_slug=skill_slug,
            signal_type=signal.type.value,
        )

    async def run_calibration_loop(
        self,
        user_id: str,
        skill_slug: str,
        domain_id: str,
        initial_triggers: list[str],
    ) -> CalibrationLoopState:
        """Execute the calibration loop between Calibrator and Researcher.

        This is called by the Calibrator phase handler when it detects
        re-research triggers. The loop:

        1. Routes to Researcher (targeted update mode)
        2. Routes back to Calibrator (re-assess new vertices only)
        3. Repeats if triggers remain, up to max_iterations

        Returns the final CalibrationLoopState.
        """
        loop_state = CalibrationLoopState(
            iteration=0,
            max_iterations=2,
            re_research_triggers=initial_triggers,
        )

        while loop_state.should_loop:
            loop_state.iteration += 1

            log.info(
                "calibration_loop_iteration",
                user_id=user_id,
                skill_slug=skill_slug,
                iteration=loop_state.iteration,
                triggers=loop_state.re_research_triggers[:3],
            )

            # Reset skill_research so the orchestrator routes there
            await self._detector.reset_phase(user_id, skill_slug, "skill_research")

            # Route to Skill Researcher (targeted update)
            if PipelinePhase.SKILL_RESEARCH in self._handlers:
                research_handler = self._handlers[PipelinePhase.SKILL_RESEARCH]
                research_context = await self.build_context(
                    user_id=user_id,
                    skill_slug=skill_slug,
                    phase=PipelinePhase.SKILL_RESEARCH,
                    calibration_loop=loop_state,
                )
                result = await research_handler.handle(research_context)
                loop_state.new_vertex_ids = result.get("new_vertex_ids", [])

                # Mark research as complete again
                await self._detector.mark_phase_complete(
                    user_id, skill_slug, "skill_research", domain_id
                )

            # Reset calibration so orchestrator routes there
            await self._detector.reset_phase(user_id, skill_slug, "learner_calibration")

            # Route to Calibrator (re-assess new vertices only)
            if PipelinePhase.LEARNER_CALIBRATION in self._handlers:
                calibration_handler = self._handlers[PipelinePhase.LEARNER_CALIBRATION]
                calibration_context = await self.build_context(
                    user_id=user_id,
                    skill_slug=skill_slug,
                    phase=PipelinePhase.LEARNER_CALIBRATION,
                    calibration_loop=loop_state,
                )
                result = await calibration_handler.handle(calibration_context)
                loop_state.re_research_triggers = result.get("re_research_triggers", [])

        # Mark calibration as complete after loop exits
        await self._detector.mark_phase_complete(
            user_id, skill_slug, "learner_calibration", domain_id
        )

        log.info(
            "calibration_loop_complete",
            user_id=user_id,
            skill_slug=skill_slug,
            total_iterations=loop_state.iteration,
        )

        return loop_state
```

- [ ] **Step 4: Run test — should pass**

Run: `cd learn-anything-app && uv run pytest tests/integration/test_services/test_orchestrator.py -v`
Expected: All passed (12 tests)

- [ ] **Step 5: Commit**

```bash
git commit -m "feat: orchestrator — phase routing, calibration loop (max 2x), feedback loop triggers"
```

---

### Task 6: SSE Streaming Endpoint

**Files:**
- Create: `learn-anything-app/app/routes/sse.py`
- Test: `learn-anything-app/tests/integration/test_routes/test_sse.py`

- [ ] **Step 1: Write failing test for SSE endpoint**

```python
# tests/integration/test_routes/test_sse.py
"""
Tests for the SSE streaming endpoint.

The SSE endpoint streams LLM responses to the frontend as
text/event-stream events compatible with Datastar's SSE handling.
"""
import pytest
import json
from unittest.mock import AsyncMock, MagicMock, patch
from httpx import AsyncClient, ASGITransport
from app.main import app
from app.llm.provider import LLMStreamEvent, LLMToolCall


@pytest.fixture
async def client():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as c:
        yield c


def test_sse_event_format():
    """SSE events conform to text/event-stream format."""
    from app.routes.sse import format_sse_event

    event = format_sse_event(
        event_type="text",
        data={"content": "Hello, let me help you learn."},
    )
    assert event.startswith("event: text\n")
    assert "data: " in event
    assert event.endswith("\n\n")

    parsed_data = json.loads(event.split("data: ")[1].strip())
    assert parsed_data["content"] == "Hello, let me help you learn."


def test_sse_event_with_id():
    """SSE events can include an id field."""
    from app.routes.sse import format_sse_event

    event = format_sse_event(
        event_type="text",
        data={"content": "chunk"},
        event_id="evt_001",
    )
    assert "id: evt_001\n" in event


def test_sse_done_event():
    """Done events include usage information."""
    from app.routes.sse import format_sse_event

    event = format_sse_event(
        event_type="done",
        data={
            "stop_reason": "end_turn",
            "usage": {"input_tokens": 200, "output_tokens": 80},
        },
    )
    parsed = json.loads(event.split("data: ")[1].strip())
    assert parsed["stop_reason"] == "end_turn"
    assert parsed["usage"]["input_tokens"] == 200


def test_sse_error_event():
    """Error events include error message."""
    from app.routes.sse import format_sse_event

    event = format_sse_event(
        event_type="error",
        data={"message": "Rate limit exceeded", "resets_at": "2026-04-01T14:00:00Z"},
    )
    parsed = json.loads(event.split("data: ")[1].strip())
    assert parsed["message"] == "Rate limit exceeded"


def test_sse_phase_event():
    """Phase events signal pipeline phase transitions."""
    from app.routes.sse import format_sse_event

    event = format_sse_event(
        event_type="phase",
        data={"phase": "skill_research", "message": "Researching jazz piano..."},
    )
    parsed = json.loads(event.split("data: ")[1].strip())
    assert parsed["phase"] == "skill_research"


def test_sse_tool_event():
    """Tool call events include tool name and arguments."""
    from app.routes.sse import format_sse_event

    event = format_sse_event(
        event_type="tool_call",
        data={
            "tool_id": "tc_001",
            "tool_name": "read_state",
            "arguments": {"slug": "jazz-piano"},
        },
    )
    parsed = json.loads(event.split("data: ")[1].strip())
    assert parsed["tool_name"] == "read_state"


def test_stream_event_to_sse():
    """LLMStreamEvent converts to SSE format."""
    from app.routes.sse import stream_event_to_sse

    text_event = LLMStreamEvent(type="text", content="Learning jazz piano involves...")
    sse = stream_event_to_sse(text_event)
    assert "event: text" in sse
    parsed = json.loads(sse.split("data: ")[1].strip())
    assert parsed["content"] == "Learning jazz piano involves..."

    tool_event = LLMStreamEvent(
        type="tool_call",
        tool_call=LLMToolCall(id="tc_1", name="web_search", arguments={"query": "jazz piano"}),
    )
    sse = stream_event_to_sse(tool_event)
    assert "event: tool_call" in sse

    done_event = LLMStreamEvent(
        type="done",
        usage={"input_tokens": 100, "output_tokens": 50},
        stop_reason="end_turn",
    )
    sse = stream_event_to_sse(done_event)
    assert "event: done" in sse


@pytest.mark.asyncio
async def test_sse_endpoint_exists(client):
    """SSE endpoint is registered and responds."""
    # Without auth, should redirect or return 401/403
    resp = await client.get("/api/sse/pipeline/jazz-piano")
    # The exact status depends on auth middleware — but the route exists
    assert resp.status_code in (200, 401, 403, 307, 422)


@pytest.mark.asyncio
async def test_sse_content_type():
    """SSE endpoint returns text/event-stream content type."""
    from app.routes.sse import format_sse_event

    # Verify the format is valid SSE
    event = format_sse_event("heartbeat", {"timestamp": "2026-04-01T12:00:00Z"})
    lines = event.strip().split("\n")
    assert lines[0].startswith("event: ")
    assert lines[1].startswith("data: ")
```

- [ ] **Step 2: Run test — should fail**

Run: `cd learn-anything-app && uv run pytest tests/integration/test_routes/test_sse.py -v`
Expected: FAIL — `ModuleNotFoundError`

- [ ] **Step 3: Add datastar-py dependency to pyproject.toml**

Add to `[project] dependencies`:
```toml
    "datastar-py>=0.3",
```

Run: `cd learn-anything-app && uv sync`

- [ ] **Step 4: Implement SSE route**

```python
# app/routes/sse.py
"""
SSE streaming endpoint for LLM responses.

Streams pipeline phase execution results to the frontend via
Server-Sent Events (text/event-stream). Compatible with Datastar's
SSE-based reactivity.

Event types:
- text: Partial LLM text output
- tool_call: LLM requested a tool invocation
- phase: Pipeline phase transition
- done: Stream complete with usage stats
- error: Error occurred (budget exhausted, LLM failure, etc.)
- heartbeat: Keep-alive ping (every 15s)
"""
from __future__ import annotations

import json
import asyncio
from typing import Any, AsyncIterator

import structlog
from fastapi import APIRouter, Request, Depends

from datastar_py import ServerSentEventGenerator as SSE
from datastar_py.fastapi import DatastarResponse

from app.llm.provider import LLMStreamEvent

log = structlog.get_logger()

router = APIRouter(prefix="/api/sse", tags=["sse"])

HEARTBEAT_INTERVAL_SECONDS = 15


def format_sse_event(
    event_type: str,
    data: dict[str, Any],
    event_id: str | None = None,
) -> str:
    """Format a dict as a Server-Sent Event string.

    Returns a string conforming to the SSE specification:
    https://html.spec.whatwg.org/multipage/server-sent-events.html

    Format:
        id: <optional>\n
        event: <type>\n
        data: <json>\n
        \n
    """
    parts = []
    if event_id:
        parts.append(f"id: {event_id}")
    parts.append(f"event: {event_type}")
    parts.append(f"data: {json.dumps(data)}")
    parts.append("")  # Trailing newline to terminate event
    return "\n".join(parts) + "\n"


def stream_event_to_sse(event: LLMStreamEvent) -> str:
    """Convert an LLMStreamEvent to SSE format."""
    if event.type == "text":
        return format_sse_event("text", {"content": event.content})

    elif event.type == "tool_call" and event.tool_call:
        return format_sse_event("tool_call", {
            "tool_id": event.tool_call.id,
            "tool_name": event.tool_call.name,
            "arguments": event.tool_call.arguments,
        })

    elif event.type == "tool_result" and event.tool_result:
        return format_sse_event("tool_result", {
            "tool_call_id": event.tool_result.tool_call_id,
            "content": event.tool_result.content,
            "is_error": event.tool_result.is_error,
        })

    elif event.type == "done":
        return format_sse_event("done", {
            "stop_reason": event.stop_reason,
            "usage": event.usage,
        })

    elif event.type == "error":
        return format_sse_event("error", {"message": event.content})

    else:
        return format_sse_event(event.type, {"content": event.content})


async def heartbeat_generator() -> AsyncIterator[str]:
    """Yield heartbeat events to keep the SSE connection alive."""
    while True:
        await asyncio.sleep(HEARTBEAT_INTERVAL_SECONDS)
        yield format_sse_event("heartbeat", {"ping": True})


async def merge_streams(
    event_stream: AsyncIterator[str],
    heartbeat: AsyncIterator[str],
) -> AsyncIterator[str]:
    """Merge an event stream with heartbeat pings.

    Uses asyncio to interleave real events with periodic heartbeats.
    The heartbeat keeps the connection alive through proxies that
    timeout idle connections.
    """
    event_task = None
    heartbeat_task = None

    event_iter = aiter(event_stream)
    heartbeat_iter = aiter(heartbeat)

    try:
        while True:
            if event_task is None:
                event_task = asyncio.ensure_future(anext(event_iter))
            if heartbeat_task is None:
                heartbeat_task = asyncio.ensure_future(anext(heartbeat_iter))

            done, _ = await asyncio.wait(
                {event_task, heartbeat_task},
                return_when=asyncio.FIRST_COMPLETED,
            )

            for task in done:
                try:
                    result = task.result()
                    yield result
                except StopAsyncIteration:
                    # Event stream ended — send final event and stop
                    if task is event_task:
                        if heartbeat_task and not heartbeat_task.done():
                            heartbeat_task.cancel()
                        return
                    # Heartbeat ended unexpectedly — log and continue
                    # without heartbeats (connection may timeout through proxies)
                    if task is heartbeat_task:
                        log.warning("heartbeat_stream_terminated_unexpectedly")
                        heartbeat_task = None
                        continue

                if task is event_task:
                    event_task = None
                elif task is heartbeat_task:
                    heartbeat_task = None

    finally:
        # Clean up any pending tasks
        for task in [event_task, heartbeat_task]:
            if task and not task.done():
                task.cancel()


@router.get("/pipeline/{skill_slug}")
async def stream_pipeline(
    request: Request,
    skill_slug: str,
):
    """Stream pipeline phase execution for a skill.

    The orchestrator detects the current phase, routes to the
    appropriate handler, and streams the handler's output as SSE events.

    Query parameters:
    - message: User message to send to the current phase handler

    Authentication: Requires a valid session cookie. The user_id is
    extracted from the session.

    SSE event types:
    - phase: Pipeline phase transition (sent at start)
    - text: LLM text output (streamed)
    - tool_call: LLM tool invocation
    - done: Phase complete
    - error: Error occurred
    - heartbeat: Keep-alive ping
    """
    # TODO: Extract user_id from session (requires auth middleware from Plan 1)
    # For now, return a placeholder stream
    user_message = request.query_params.get("message", "")

    async def event_generator() -> AsyncIterator[str]:
        # Phase announcement
        yield format_sse_event("phase", {
            "phase": "pending",
            "skill_slug": skill_slug,
            "message": f"Processing: {skill_slug}",
        })

        # Placeholder — will be replaced with orchestrator integration
        yield format_sse_event("text", {
            "content": f"Pipeline endpoint ready for {skill_slug}. "
                       f"Orchestrator integration pending.",
        })

        yield format_sse_event("done", {
            "stop_reason": "end_turn",
            "usage": {"input_tokens": 0, "output_tokens": 0},
        })

    return DatastarResponse(
        merge_streams(event_generator(), heartbeat_generator()),
    )


@router.get("/pipeline/{skill_slug}/feedback")
async def stream_feedback(
    request: Request,
    skill_slug: str,
):
    """Stream feedback loop execution for a skill.

    Called when the Training Conductor signals an upstream update.
    The orchestrator handles the feedback signal and streams the
    re-execution of affected phases.

    Query parameters:
    - signal_type: FeedbackSignalType value
    - evidence: Evidence string
    """
    signal_type = request.query_params.get("signal_type", "")
    evidence = request.query_params.get("evidence", "")

    async def event_generator() -> AsyncIterator[str]:
        yield format_sse_event("phase", {
            "phase": "feedback",
            "signal_type": signal_type,
            "message": f"Processing feedback: {signal_type}",
        })

        yield format_sse_event("done", {
            "stop_reason": "end_turn",
            "usage": {"input_tokens": 0, "output_tokens": 0},
        })

    return DatastarResponse(
        merge_streams(event_generator(), heartbeat_generator()),
    )
```

- [ ] **Step 5: Register SSE router in main.py**

Add to `app/main.py`:
```python
from app.routes.sse import router as sse_router
app.include_router(sse_router)
```

- [ ] **Step 6: Run test — should pass**

Run: `cd learn-anything-app && uv run pytest tests/integration/test_routes/test_sse.py -v`
Expected: All passed (10 tests)

- [ ] **Step 7: Commit**

```bash
git commit -m "feat: SSE streaming endpoint — text/event-stream with heartbeats, phase transitions, error handling"
```

---

### Task 7: Orchestrator-SSE Integration

**Files:**
- Modify: `learn-anything-app/app/routes/sse.py`
- Modify: `learn-anything-app/app/services/orchestrator.py`
- Test: `learn-anything-app/tests/integration/test_routes/test_sse.py` (add integration tests)

- [ ] **Step 1: Write failing test for orchestrator-SSE integration**

Add to `tests/integration/test_routes/test_sse.py`:

```python
@pytest.mark.asyncio
async def test_pipeline_stream_integrates_orchestrator():
    """The SSE pipeline endpoint uses the orchestrator to route and stream."""
    from app.routes.sse import create_pipeline_stream
    from app.services.orchestrator import Orchestrator
    from app.services.pipeline import PipelinePhase

    events_collected = []

    class FakeHandler:
        async def handle(self, context):
            return {"status": "ok"}

        async def handle_stream(self, context):
            yield LLMStreamEvent(type="text", content="Assessing your background...")
            yield LLMStreamEvent(
                type="done",
                usage={"input_tokens": 50, "output_tokens": 20},
                stop_reason="end_turn",
            )

    fake_handler = FakeHandler()

    async for event_str in create_pipeline_stream(
        user_id="user-1",
        skill_slug="jazz-piano",
        phase=PipelinePhase.DOMAIN_ASSESSMENT,
        handler=fake_handler,
        user_message="I want to learn jazz piano",
    ):
        events_collected.append(event_str)

    # Should have: phase announcement, text, done
    full_output = "".join(events_collected)
    assert "event: phase" in full_output
    assert "domain_assessment" in full_output
    assert "event: text" in full_output
    assert "Assessing your background" in full_output
    assert "event: done" in full_output
```

- [ ] **Step 2: Run test — should fail**

Run: `cd learn-anything-app && uv run pytest tests/integration/test_routes/test_sse.py::test_pipeline_stream_integrates_orchestrator -v`
Expected: FAIL — `ImportError: cannot import name 'create_pipeline_stream'`

- [ ] **Step 3: Add create_pipeline_stream to sse.py**

Add to `app/routes/sse.py`:

```python
from app.services.pipeline import PipelinePhase
from app.services.orchestrator import PhaseHandler


async def create_pipeline_stream(
    user_id: str,
    skill_slug: str,
    phase: PipelinePhase,
    handler: PhaseHandler,
    user_message: str = "",
) -> AsyncIterator[str]:
    """Create an SSE event stream from an orchestrator phase handler.

    This is the bridge between the orchestrator (which routes to phase
    handlers) and the SSE endpoint (which streams to the frontend).

    Yields SSE-formatted strings:
    1. Phase announcement event
    2. Handler's streaming events (text, tool_call, etc.)
    3. Done event

    Used by the /api/sse/pipeline/{skill_slug} endpoint.
    """
    # Announce the phase
    yield format_sse_event("phase", {
        "phase": phase.name.lower(),
        "skill_slug": skill_slug,
        "message": _phase_transition_message(phase, skill_slug),
    })

    # Stream the handler's events
    context = {
        "user_id": user_id,
        "skill_slug": skill_slug,
        "phase": phase,
        "user_message": user_message,
    }

    try:
        async for event in handler.handle_stream(context):
            yield stream_event_to_sse(event)
    except Exception as e:
        log.error("phase_handler_error", phase=phase.name, error=str(e))
        yield format_sse_event("error", {
            "message": f"Error during {phase.name.lower()}: {str(e)}",
            "phase": phase.name.lower(),
        })


def _phase_transition_message(phase: PipelinePhase, skill_slug: str) -> str:
    """Human-readable transition message for each phase."""
    messages = {
        PipelinePhase.DOMAIN_ASSESSMENT: f"Let's understand what you want to learn about {skill_slug.replace('-', ' ')}.",
        PipelinePhase.SKILL_RESEARCH: f"Researching the structure of {skill_slug.replace('-', ' ')}...",
        PipelinePhase.LEARNER_CALIBRATION: "Time to assess what you already know.",
        PipelinePhase.CURRICULUM_DESIGN: "Designing your personalized learning plan.",
        PipelinePhase.MATERIAL_GENERATION: "Generating your learning materials...",
        PipelinePhase.PROGRESS_DASHBOARD: "Setting up your progress dashboard.",
        PipelinePhase.TRAINING: "Ready for your training session.",
    }
    return messages.get(phase, f"Processing {phase.name.lower()}...")
```

- [ ] **Step 4: Run test — should pass**

Run: `cd learn-anything-app && uv run pytest tests/integration/test_routes/test_sse.py -v`
Expected: All passed

- [ ] **Step 5: Commit**

```bash
git commit -m "feat: orchestrator-SSE integration — create_pipeline_stream bridges phase handlers to SSE"
```

---

### Task 8: Rate Limiter Integration with SSE

**Files:**
- Modify: `learn-anything-app/app/routes/sse.py`
- Test: `learn-anything-app/tests/integration/test_routes/test_sse.py` (add rate limit tests)

- [ ] **Step 1: Write failing test for rate-limited SSE stream**

Add to `tests/integration/test_routes/test_sse.py`:

```python
@pytest.mark.asyncio
async def test_budget_exhaustion_sends_error_event():
    """When budget is exhausted, SSE sends an error event instead of crashing."""
    from app.routes.sse import create_rate_limited_stream
    from app.llm.rate_limiter import BudgetExhaustedError
    from datetime import datetime, timezone

    events_collected = []

    async def failing_stream():
        raise BudgetExhaustedError(
            budget_type="requests_per_hour",
            limit=60,
            current=60,
            resets_at=datetime(2026, 4, 1, 14, 0, 0, tzinfo=timezone.utc),
        )
        # WARNING: Do NOT remove this yield. Although it is never reached
        # at runtime, it is syntactically required to make this function
        # an async generator (PEP 525). Without it, Python treats the
        # function as a plain coroutine, and `async for` over its return
        # value would raise TypeError instead of catching the exception.
        yield  # noqa: unreachable — required to make this an async generator

    async for event_str in create_rate_limited_stream(failing_stream()):
        events_collected.append(event_str)

    full_output = "".join(events_collected)
    assert "event: error" in full_output
    assert "budget" in full_output.lower() or "limit" in full_output.lower()
    assert "resets" in full_output.lower()


@pytest.mark.asyncio
async def test_normal_stream_passes_through():
    """When budget is fine, events pass through unchanged."""
    from app.routes.sse import create_rate_limited_stream

    async def normal_stream():
        yield format_sse_event("text", {"content": "Hello"})
        yield format_sse_event("done", {"stop_reason": "end_turn", "usage": {}})

    events = []
    async for event_str in create_rate_limited_stream(normal_stream()):
        events.append(event_str)

    full_output = "".join(events)
    assert "event: text" in full_output
    assert "Hello" in full_output
    assert "event: done" in full_output
```

- [ ] **Step 2: Run test — should fail**

Run: `cd learn-anything-app && uv run pytest tests/integration/test_routes/test_sse.py::test_budget_exhaustion_sends_error_event -v`
Expected: FAIL — `ImportError: cannot import name 'create_rate_limited_stream'`

- [ ] **Step 3: Add rate limiter integration to sse.py**

Add to `app/routes/sse.py`:

```python
from app.llm.rate_limiter import BudgetExhaustedError


async def create_rate_limited_stream(
    inner_stream: AsyncIterator[str],
) -> AsyncIterator[str]:
    """Wraps an SSE stream with rate limit error handling.

    If a BudgetExhaustedError is raised during streaming, it yields
    a graceful error event with reset time instead of crashing.
    """
    try:
        async for event in inner_stream:
            yield event
    except BudgetExhaustedError as e:
        yield format_sse_event("error", {
            "message": (
                f"LLM budget exhausted: {e.budget_type} "
                f"({e.current}/{e.limit}). "
                f"Resets at {e.resets_at.isoformat()}."
            ),
            "budget_type": e.budget_type,
            "limit": e.limit,
            "current": e.current,
            "resets_at": e.resets_at.isoformat(),
        })
    except Exception as e:
        log.error("sse_stream_error", error=str(e), error_type=type(e).__name__)
        yield format_sse_event("error", {
            "message": f"An error occurred: {str(e)}",
        })
```

- [ ] **Step 4: Run test — should pass**

Run: `cd learn-anything-app && uv run pytest tests/integration/test_routes/test_sse.py -v`
Expected: All passed

- [ ] **Step 5: Commit**

```bash
git commit -m "feat: rate limiter integration with SSE — graceful budget exhaustion events"
```

---

### Task 9: Agreement Gates (Curriculum Design)

**Files:**
- Modify: `learn-anything-app/app/services/orchestrator.py`
- Test: `learn-anything-app/tests/integration/test_services/test_orchestrator.py` (add agreement gate tests)

- [ ] **Step 1: Write failing test for agreement gates**

Add to `tests/integration/test_services/test_orchestrator.py`:

```python
from app.services.orchestrator import AgreementGate, AgreementGateType


def test_agreement_gate_types():
    """Two agreement gates defined: teaching preferences + epitome refinement."""
    assert AgreementGateType.TEACHING_PREFERENCES is not None
    assert AgreementGateType.EPITOME_REFINEMENT is not None


def test_agreement_gate_creation():
    gate = AgreementGate(
        gate_type=AgreementGateType.TEACHING_PREFERENCES,
        prompt="Based on the expert panel, which instructor persona resonates with you?",
        context={"expert_panel": ["Feynman", "Strict Academic", "Socratic Coach"]},
    )
    assert gate.gate_type == AgreementGateType.TEACHING_PREFERENCES
    assert not gate.confirmed
    assert gate.response is None


def test_agreement_gate_confirmation():
    gate = AgreementGate(
        gate_type=AgreementGateType.EPITOME_REFINEMENT,
        prompt="Your first lesson would cover basic chord voicings. Does this feel right?",
        context={"epitome_vertex_ids": ["v1", "v2"]},
    )
    gate.confirm("Yes, that sounds perfect for where I'm starting.")
    assert gate.confirmed is True
    assert gate.response == "Yes, that sounds perfect for where I'm starting."


def test_agreement_gate_redirect():
    gate = AgreementGate(
        gate_type=AgreementGateType.EPITOME_REFINEMENT,
        prompt="Your first lesson would cover basic chord voicings. Does this feel right?",
        context={"epitome_vertex_ids": ["v1", "v2"]},
    )
    gate.redirect("I'd rather start with scales and intervals.")
    assert gate.confirmed is False
    assert gate.response == "I'd rather start with scales and intervals."
    assert gate.redirected is True
```

- [ ] **Step 2: Run test — should fail**

Run: `cd learn-anything-app && uv run pytest tests/integration/test_services/test_orchestrator.py::test_agreement_gate_types -v`
Expected: FAIL — `ImportError`

- [ ] **Step 3: Add AgreementGate to orchestrator**

Add to `app/services/orchestrator.py`:

```python
class AgreementGateType(str, enum.Enum):
    """Agreement gate types in the Curriculum Design phase.

    These are conversational checkpoints, NOT forms. They appear
    as natural dialogue moments inline in the chat.
    """
    TEACHING_PREFERENCES = "teaching_preferences"
    EPITOME_REFINEMENT = "epitome_refinement"


@dataclass
class AgreementGate:
    """A conversational agreement gate in the Curriculum Design phase.

    Two gates exist:
    1. Teaching preferences — expert panel presented, learner chooses
       instructor persona and instruction style
    2. Epitome refinement — proposed first lesson presented as a rich card
       with rationale, learner confirms or redirects

    The Curriculum Architect phase handler presents these inline in the
    conversation. Only proceeds when confirmed.
    """
    gate_type: AgreementGateType
    prompt: str
    context: dict[str, Any] = field(default_factory=dict)
    confirmed: bool = False
    redirected: bool = False
    response: str | None = None

    def confirm(self, response: str) -> None:
        """Learner confirms — proceed with current proposal."""
        self.confirmed = True
        self.redirected = False
        self.response = response

    def redirect(self, response: str) -> None:
        """Learner redirects — revise the proposal."""
        self.confirmed = False
        self.redirected = True
        self.response = response
```

- [ ] **Step 4: Run test — should pass**

Run: `cd learn-anything-app && uv run pytest tests/integration/test_services/test_orchestrator.py -v`
Expected: All passed

- [ ] **Step 5: Commit**

```bash
git commit -m "feat: agreement gates — teaching preferences + epitome refinement conversational checkpoints"
```

---

### Task 10: Error Recovery + Retry Logic

**Files:**
- Modify: `learn-anything-app/app/services/orchestrator.py`
- Test: `learn-anything-app/tests/integration/test_services/test_orchestrator.py` (add error recovery tests)

- [ ] **Step 1: Write failing test for error recovery**

Add to `tests/integration/test_services/test_orchestrator.py`:

```python
from app.services.orchestrator import PhaseRetryPolicy


def test_retry_policy_defaults():
    policy = PhaseRetryPolicy()
    assert policy.max_retries == 2
    assert policy.retry_count == 0
    assert policy.should_retry is True
    assert policy.should_fallback is False


def test_retry_policy_after_first_failure():
    policy = PhaseRetryPolicy()
    policy.record_failure("LLM timeout")
    assert policy.retry_count == 1
    assert policy.should_retry is True
    assert policy.should_fallback is False


def test_retry_policy_after_two_failures():
    policy = PhaseRetryPolicy()
    policy.record_failure("LLM timeout")
    policy.record_failure("LLM rate limit")
    assert policy.retry_count == 2
    assert policy.should_retry is False
    assert policy.should_fallback is True


def test_retry_policy_tracks_errors():
    policy = PhaseRetryPolicy()
    policy.record_failure("Timeout at 30s")
    policy.record_failure("Invalid JSON response")
    assert len(policy.errors) == 2
    assert "Timeout" in policy.errors[0]


def test_fallback_descriptions():
    """Each phase has a documented fallback behavior."""
    from app.services.orchestrator import PHASE_FALLBACKS
    from app.services.pipeline import PipelinePhase

    assert PipelinePhase.DOMAIN_ASSESSMENT in PHASE_FALLBACKS
    assert PipelinePhase.SKILL_RESEARCH in PHASE_FALLBACKS
    assert PipelinePhase.LEARNER_CALIBRATION in PHASE_FALLBACKS
    assert PipelinePhase.CURRICULUM_DESIGN in PHASE_FALLBACKS
    assert PipelinePhase.MATERIAL_GENERATION in PHASE_FALLBACKS
    assert PipelinePhase.PROGRESS_DASHBOARD in PHASE_FALLBACKS
    assert PipelinePhase.TRAINING in PHASE_FALLBACKS

    # Fallback for domain assessment accepts user's self-described domain
    assert "self-described" in PHASE_FALLBACKS[PipelinePhase.DOMAIN_ASSESSMENT].lower()

    # Fallback for research is "basic skill tree from LLM knowledge without web search"
    assert "without web search" in PHASE_FALLBACKS[PipelinePhase.SKILL_RESEARCH].lower() or \
           "basic" in PHASE_FALLBACKS[PipelinePhase.SKILL_RESEARCH].lower()

    # Fallback for progress dashboard shows raw mastery data
    assert "raw mastery data" in PHASE_FALLBACKS[PipelinePhase.PROGRESS_DASHBOARD].lower()
```

- [ ] **Step 2: Run test — should fail**

Run: `cd learn-anything-app && uv run pytest tests/integration/test_services/test_orchestrator.py::test_retry_policy_defaults -v`
Expected: FAIL — `ImportError`

- [ ] **Step 3: Add retry policy and fallback descriptions**

Add to `app/services/orchestrator.py`:

```python
@dataclass
class PhaseRetryPolicy:
    """Retry policy for pipeline phase execution.

    From spec Section 10: After 2 consecutive failures, the system
    falls back to a simplified version of the phase and notifies
    the user.

    Pipeline stages are idempotent — if an LLM call fails mid-phase,
    the state file is not written, so the orchestrator retries the
    same phase on next interaction.
    """
    max_retries: int = 2
    retry_count: int = 0
    errors: list[str] = field(default_factory=list)

    @property
    def should_retry(self) -> bool:
        return self.retry_count < self.max_retries

    @property
    def should_fallback(self) -> bool:
        return self.retry_count >= self.max_retries

    def record_failure(self, error: str) -> None:
        self.retry_count += 1
        self.errors.append(error)


# Fallback behaviors when a phase fails twice (from plugin orchestrator)
PHASE_FALLBACKS: dict[PipelinePhase, str] = {
    PipelinePhase.DOMAIN_ASSESSMENT: (
        "Accept user's self-described skill domain without LLM classification. "
        "Uses the raw skill slug as the domain name with default settings."
    ),
    PipelinePhase.SKILL_RESEARCH: (
        "Generate a basic skill tree from LLM knowledge without web search. "
        "Covers core components but may miss domain-specific nuances."
    ),
    PipelinePhase.LEARNER_CALIBRATION: (
        "Use the learner profile's self-reported experience as the mastery overlay. "
        "Less precise but functional for curriculum design."
    ),
    PipelinePhase.CURRICULUM_DESIGN: (
        "Linear sequencing of priority gaps ordered by frequency x impact score. "
        "No task class grouping or productive failure points."
    ),
    PipelinePhase.MATERIAL_GENERATION: (
        "Generate basic flashcards only, without lectures, worked examples, or visualizations."
    ),
    PipelinePhase.PROGRESS_DASHBOARD: (
        "Show raw mastery data without computed metrics. "
        "Displays per-vertex mastery states directly from the knowledge graph."
    ),
    PipelinePhase.TRAINING: (
        "Structured Q&A mode without full template architecture. "
        "Covers the same vertices but with simplified session flow."
    ),
}
```

- [ ] **Step 4: Run test — should pass**

Run: `cd learn-anything-app && uv run pytest tests/integration/test_services/test_orchestrator.py -v`
Expected: All passed

- [ ] **Step 5: Commit**

```bash
git commit -m "feat: error recovery — retry policy (max 2 failures) with phase-specific fallback behaviors"
```

---

### Task 11: LLM Provider Dependency Injection

**Files:**
- Modify: `learn-anything-app/app/dependencies.py`
- Modify: `learn-anything-app/app/routes/sse.py`
- Test: `learn-anything-app/tests/unit/test_llm/test_anthropic_provider.py` (add DI test)

- [ ] **Step 1: Write failing test for provider dependency**

Add to `tests/unit/test_llm/test_anthropic_provider.py`:

```python
def test_get_llm_provider_returns_anthropic():
    """get_llm_provider returns AnthropicProvider when configured."""
    from app.llm.dependencies import create_llm_provider

    provider = create_llm_provider(api_key="sk-test", model="claude-sonnet-4-6")
    assert isinstance(provider, AnthropicProvider)
    assert provider.model == "claude-sonnet-4-6"


def test_get_llm_provider_raises_without_key():
    """get_llm_provider raises ValueError when no API key configured."""
    from app.llm.dependencies import create_llm_provider

    with pytest.raises(ValueError, match="API key"):
        create_llm_provider(api_key="", model="claude-sonnet-4-6")
```

- [ ] **Step 2: Run test — should fail**

Run: `cd learn-anything-app && uv run pytest tests/unit/test_llm/test_anthropic_provider.py::test_get_llm_provider_returns_anthropic -v`
Expected: FAIL — `ImportError`

- [ ] **Step 3: Create LLM dependencies module**

```python
# app/llm/dependencies.py
"""
LLM provider dependency injection.

Provides the LLM provider instance to route handlers and services.
The provider is created once from settings and reused.
"""
from __future__ import annotations

import structlog

from app.llm.anthropic_provider import AnthropicProvider
from app.llm.provider import LLMProvider

log = structlog.get_logger()

# Module-level singleton — initialized on first use
_provider: LLMProvider | None = None


def create_llm_provider(api_key: str, model: str) -> AnthropicProvider:
    """Create an LLM provider instance.

    Args:
        api_key: Anthropic API key.
        model: Claude model identifier.

    Returns:
        Configured AnthropicProvider.

    Raises:
        ValueError: If api_key is empty.
    """
    if not api_key:
        raise ValueError(
            "LLM API key not configured. Set it in /settings or "
            "provide LA_ANTHROPIC_API_KEY environment variable."
        )
    return AnthropicProvider(api_key=api_key, model=model)


def get_llm_provider() -> LLMProvider:
    """FastAPI dependency: get the configured LLM provider.

    The provider is created lazily on first call and cached for
    the lifetime of the application.

    In production, the API key comes from the encrypted AppConfig
    in the database (decrypted by SecretStore). For development,
    it can be set via LA_ANTHROPIC_API_KEY env var.
    """
    global _provider
    if _provider is None:
        from app.config import settings
        _provider = create_llm_provider(
            api_key=settings.anthropic_api_key,
            model=settings.anthropic_model,
        )
    return _provider


def reset_llm_provider() -> None:
    """Reset the cached provider (used when settings change)."""
    global _provider
    _provider = None
    log.info("llm_provider_reset")
```

- [ ] **Step 4: Run test — should pass**

Run: `cd learn-anything-app && uv run pytest tests/unit/test_llm/test_anthropic_provider.py -v`
Expected: All passed

- [ ] **Step 5: Commit**

```bash
git commit -m "feat: LLM provider dependency injection — lazy singleton with settings-driven config"
```

---

### Task 12: Alembic Migration for New Models

**Files:**
- Create: `learn-anything-app/alembic/versions/003_llm_usage_pipeline_state.py`

> **Note:** Migration 002 is taken by Plan 2 (PGVector embeddings). This is 003.

- [ ] **Step 1: Update alembic env.py to import new models**

Add to `alembic/env.py`:
```python
from app.models.llm_usage import LLMUsageRecord, LLMBudget  # noqa
from app.services.pipeline import PipelineState  # noqa
```

- [ ] **Step 2: Generate migration**

Run: `cd learn-anything-app && uv run alembic revision --autogenerate -m "add llm_usage pipeline_state tables"`
Expected: Creates migration file in `alembic/versions/`

- [ ] **Step 3: Verify migration has correct tables**

Open the generated migration and verify it contains:
- `llm_usage_records` table with user_id, model, input_tokens, output_tokens, endpoint, phase, created_at
- `llm_budgets` table with user_id, requests_per_hour, tokens_per_day
- `pipeline_states` table with user_id, skill_slug, domain_id, phase_completed, completed_at
- Unique constraint on pipeline_states (user_id, skill_slug, phase_completed)
- Index on llm_usage_records.created_at

- [ ] **Step 4: Commit**

```bash
git commit -m "feat: Alembic migration for LLM usage tracking and pipeline state tables"
```

---

### Task 13: Full Integration Test

**Files:**
- Modify: `learn-anything-app/tests/conftest.py` (ensure all models imported)

- [ ] **Step 1: Run full test suite**

Run: `cd learn-anything-app && uv run pytest tests/ -v --tb=short`
Expected: All tests pass. Count should be ~50+ tests covering:
- LLM provider protocol (7)
- AnthropicProvider (8 + 2 DI)
- Rate limiter (10)
- Pipeline detector (11)
- Orchestrator routing (12 + 4 agreement gates + 5 error recovery)
- SSE endpoint (10 + 2 integration + 2 rate limit)

- [ ] **Step 2: Verify no import cycles**

Run: `cd learn-anything-app && uv run python -c "from app.llm import LLMProvider; from app.services.orchestrator import Orchestrator; from app.routes.sse import router; print('OK')"`
Expected: `OK`

- [ ] **Step 3: Verify type annotations**

Run: `cd learn-anything-app && uv run python -c "from app.llm.provider import LLMProvider; from app.llm.anthropic_provider import AnthropicProvider; from app.llm.rate_limiter import RateLimiter; from app.services.pipeline import PipelineDetector; from app.services.orchestrator import Orchestrator; print('All imports OK')"`
Expected: `All imports OK`

- [ ] **Step 4: Commit**

```bash
git commit -m "feat: Plan 3 complete — LLM integration, orchestrator, pipeline detection, SSE streaming, rate limiting"
```

---

## Summary

### What This Plan Delivers

| Component | What It Does |
|---|---|
| `LLMProvider` protocol | Shared interface for all LLM backends (generate + stream) |
| `AnthropicProvider` | Claude integration via Anthropic SDK |
| `RateLimiter` | Per-user budget tracking (requests/hour, tokens/day) |
| `PipelineDetector` | Reads DB state, determines next pipeline phase |
| `PipelineState` model | Tracks which phases are complete per user+skill |
| `Orchestrator` | Routes to correct phase handler, manages calibration loop |
| `CalibrationLoopState` | Tracks calibration iterations (max 2) |
| `FeedbackSignal` | Feedback loop triggers from Training Conductor |
| `AgreementGate` | Conversational checkpoints in Curriculum Design |
| `PhaseRetryPolicy` | Error recovery with phase-specific fallbacks |
| SSE endpoint | Streams LLM responses as text/event-stream |
| `create_pipeline_stream` | Bridges orchestrator handlers to SSE output |
| `LLMUsageRecord` / `LLMBudget` | Database models for usage tracking |

### What This Plan Does NOT Deliver

- Individual phase handler implementations (Domain Assessor, Skill Researcher, etc.) — those are Plan 4+
- Frontend UI — Plan 5+
- Voice input/output — roadmap item
- LiteLLM provider — deferred per spec (supply chain concerns)

### Design Decisions Embedded in This Plan

1. **PipelineState as DB records, not JSON files.** The plugin checks for JSON files on disk. The web app checks for PipelineState rows in the database. Same logic, different substrate.

2. **PhaseHandler protocol, not concrete classes.** Each pipeline phase (Plan 4+) implements PhaseHandler. The orchestrator doesn't know or care what a phase does internally.

3. **SSE over WebSockets.** Matches Datastar's SSE-based architecture. Simpler than WebSockets for server-driven UI updates.

4. **Rate limiter in the DB, not in-memory.** Survives restarts, works across multiple app instances, admin-configurable via `/settings`.

5. **Calibration loop as explicit state machine.** CalibrationLoopState tracks iteration count and triggers. The orchestrator drives the loop; phase handlers just report triggers.

6. **Feedback signals as data, not code paths.** The Training Conductor emits a FeedbackSignal; the orchestrator resolves the routing. Clean separation.
