import pytest

from dekomposit.tui.models import ChatMode, LanguagePair, MessageKind
from dekomposit.tui.services import AgentService


class FakeAgent:
    def __init__(self, response: str = "ok", should_fail: bool = False) -> None:
        self.response = response
        self.should_fail = should_fail
        self.last_prompt: str | None = None

    async def chat(self, text: str) -> str:
        self.last_prompt = text
        if self.should_fail:
            raise RuntimeError("boom")
        return self.response


@pytest.mark.unit
@pytest.mark.asyncio
async def test_normal_mode_sends_raw_user_text() -> None:
    fake_agent = FakeAgent(response="hello")
    service = AgentService(agent=fake_agent)

    reply = await service.ask(
        text="hello",
        mode=ChatMode.NORMAL,
        pair=LanguagePair("en", "ru"),
    )

    assert fake_agent.last_prompt == "hello"
    assert reply.text == "hello"
    assert reply.kind == MessageKind.PLAIN


@pytest.mark.unit
@pytest.mark.asyncio
async def test_translation_mode_uses_strict_prompt_and_parses_tag() -> None:
    fake_agent = FakeAgent(response="<translated>привет</translated>")
    service = AgentService(agent=fake_agent)

    reply = await service.ask(
        text="hello",
        mode=ChatMode.TRANSLATION,
        pair=LanguagePair("en", "ru"),
    )

    assert fake_agent.last_prompt is not None
    assert "strict translation mode" in fake_agent.last_prompt
    assert "from en to ru" in fake_agent.last_prompt
    assert "hello" in fake_agent.last_prompt
    assert reply.text == "привет"
    assert reply.kind == MessageKind.TRANSLATED


@pytest.mark.unit
@pytest.mark.asyncio
async def test_service_returns_oops_fallback_on_error() -> None:
    fake_agent = FakeAgent(should_fail=True)
    service = AgentService(agent=fake_agent)

    reply = await service.ask(
        text="hello",
        mode=ChatMode.NORMAL,
        pair=LanguagePair("en", "ru"),
    )

    assert "Oops" in reply.text
    assert reply.kind == MessageKind.ERROR
