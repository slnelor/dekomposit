import pytest

from dekomposit.llm.agent import Agent
from dekomposit.llm.tools.language_detection import LanguageDetectionTool

from tests.conftest import live_llm_available


pytestmark = [
    pytest.mark.live,
    pytest.mark.skipif(
        not live_llm_available(), reason="Live LLM key is not configured"
    ),
]


@pytest.mark.asyncio
async def test_live_agent_chat_returns_non_empty_response() -> None:
    agent = Agent()

    reply = await agent.chat("Reply with exactly one short greeting in English.")

    assert isinstance(reply, str)
    assert reply.strip()


@pytest.mark.asyncio
async def test_live_language_detection_tool_returns_structured_result() -> None:
    tool = LanguageDetectionTool()

    result = await tool("Hello, how are you today?")

    assert "language" in result
    assert "confidence" in result
    assert result["language"] != "unknown"
