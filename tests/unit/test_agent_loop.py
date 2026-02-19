from types import SimpleNamespace
from typing import Any, cast

import pytest

from dekomposit.llm.agent import Agent
from dekomposit.llm.tools.base import BaseTool

from tests.conftest import make_chat_response, make_tool_call


class EchoTool(BaseTool):
    def __init__(self) -> None:
        super().__init__(name="echo_tool", description="Echo input text")

    async def __call__(self, text: str) -> dict[str, str]:
        return {"echo": text}


class FakeClient:
    def __init__(
        self,
        responses: list[SimpleNamespace],
        stream_chunks: list[str] | None = None,
    ) -> None:
        self._responses = responses
        self._index = 0
        self._stream_chunks = stream_chunks or ["stream-ok"]

    async def request_with_tools(self, messages, tools=None):
        if self._index >= len(self._responses):
            raise RuntimeError("No more fake responses configured")
        response = self._responses[self._index]
        self._index += 1
        return response

    async def request(self, messages, return_format, **kwargs):
        text = messages[-1]["content"]
        decision = SimpleNamespace(
            action="respond",
            text=text,
            source_lang=None,
            target_lang=None,
        )
        return SimpleNamespace(
            choices=[SimpleNamespace(message=SimpleNamespace(parsed=decision))]
        )

    async def stream(self, messages, **kwargs):
        for chunk in self._stream_chunks:
            yield chunk


@pytest.mark.unit
@pytest.mark.asyncio
async def test_handle_message_returns_direct_response() -> None:
    agent = Agent()
    agent.registry.clear()
    agent.client = cast(Any, FakeClient([make_chat_response("Hi there", [])]))

    result = await agent.handle_message("hello")

    assert result is not None
    assert result["type"] == "response"
    assert result["message"] == "Hi there"
    assert result["tool_calls"] == []
    assert agent.memory.conversation_history[-2]["role"] == "user"
    assert agent.memory.conversation_history[-1]["role"] == "assistant"


@pytest.mark.unit
@pytest.mark.asyncio
async def test_handle_message_executes_tool_and_continues_loop() -> None:
    agent = Agent()
    agent.registry.clear()
    agent.registry.register(EchoTool())

    tool_call = make_tool_call("echo_tool", '{"text": "ping"}', "echo_1")
    agent.client = cast(
        Any,
        FakeClient(
            [
                make_chat_response("[TOOL CALL]", [tool_call]),
                make_chat_response("Tool completed", []),
            ]
        ),
    )

    result = await agent.handle_message("use tool")

    assert result is not None
    assert result["type"] == "response"
    assert result["message"] == "Tool completed"
    assert len(result["tool_calls"]) == 1
    assert result["tool_calls"][0]["tool_name"] == "echo_tool"
    assert result["tool_calls"][0]["arguments"] == {"text": "ping"}
    assert result["tool_calls"][0]["result"] == {"echo": "ping"}


@pytest.mark.unit
@pytest.mark.asyncio
async def test_handle_message_handles_unknown_tool_gracefully() -> None:
    agent = Agent()
    agent.registry.clear()

    tool_call = make_tool_call("missing_tool", '{"x": 1}', "missing_1")
    agent.client = cast(
        Any,
        FakeClient(
            [
                make_chat_response("[TOOL CALL]", [tool_call]),
                make_chat_response("Recovered", []),
            ]
        ),
    )

    result = await agent.handle_message("trigger")

    assert result is not None
    assert result["type"] == "response"
    assert result["message"] == "Recovered"
    assert "Tool not found" in result["tool_calls"][0]["result"]["error"]


@pytest.mark.unit
@pytest.mark.asyncio
async def test_execute_tools_respects_max_iterations() -> None:
    agent = Agent()
    agent.registry.clear()
    agent.registry.register(EchoTool())

    tool_call = make_tool_call("echo_tool", '{"text": "loop"}', "loop_1")
    agent.client = cast(
        Any,
        FakeClient(
            [
                make_chat_response("[TOOL CALL]", [tool_call]),
                make_chat_response("[TOOL CALL]", [tool_call]),
            ]
        ),
    )

    result = await agent.execute_tools("loop", max_iterations=2)

    assert result["type"] == "error"
    assert "Maximum iterations reached" in result["message"]
    assert len(result["tool_calls"]) == 2


@pytest.mark.unit
@pytest.mark.asyncio
async def test_chat_returns_rendered_response() -> None:
    agent = Agent()
    agent.registry.clear()
    agent.client = cast(Any, FakeClient([make_chat_response("stream-ok", [])]))

    message = await agent.chat("hello")

    assert message == "stream-ok"
