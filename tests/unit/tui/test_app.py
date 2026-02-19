from dataclasses import dataclass

import pytest
from textual.widgets import Input

from dekomposit.tui.app import DekompositTuiApp
from dekomposit.tui.models import ChatMode, LanguagePair, MessageKind
from dekomposit.tui.services import ServiceReply


@dataclass(slots=True)
class ServiceCall:
    text: str
    mode: ChatMode
    pair: LanguagePair


class FakeService:
    def __init__(self, reply: ServiceReply | None = None) -> None:
        self.reply = reply or ServiceReply(text="ok", kind=MessageKind.PLAIN)
        self.calls: list[ServiceCall] = []

    async def ask(self, text: str, mode: ChatMode, pair: LanguagePair) -> ServiceReply:
        self.calls.append(ServiceCall(text=text, mode=mode, pair=pair))
        return self.reply


@pytest.mark.unit
@pytest.mark.asyncio
async def test_tab_toggles_mode_and_ctrl_w_swaps_pair() -> None:
    fake_service = FakeService()
    app = DekompositTuiApp(service=fake_service)

    async with app.run_test() as pilot:
        assert app.mode == ChatMode.NORMAL
        assert app.pair.label == "en-ru"

        await pilot.press("tab")
        await pilot.pause()
        assert app.mode == ChatMode.TRANSLATION

        await pilot.press("ctrl+w")
        await pilot.pause()
        assert app.pair.label == "ru-en"


@pytest.mark.unit
@pytest.mark.asyncio
async def test_inline_pair_command_updates_pair_and_sends_remaining_text() -> None:
    fake_service = FakeService(
        reply=ServiceReply(
            text="<translated>привет</translated>", kind=MessageKind.TRANSLATED
        )
    )
    app = DekompositTuiApp(service=fake_service)

    async with app.run_test() as pilot:
        input_widget = app.query_one("#chat-input", Input)
        input_widget.value = "/ruuk hello"

        await pilot.press("enter")
        await pilot.pause()

        assert app.pair.label == "ru-uk"
        assert len(fake_service.calls) == 1
        call = fake_service.calls[0]
        assert call.text == "hello"
        assert call.mode == ChatMode.NORMAL
        assert call.pair.label == "ru-uk"
