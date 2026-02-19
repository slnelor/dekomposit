import logging

from rich.text import Text
from textual import events, on
from textual.app import App, ComposeResult
from textual.binding import Binding
from textual.containers import Container, Horizontal, VerticalScroll
from textual.widgets import Input, Static

from dekomposit.tui.input_parser import parse_input
from dekomposit.tui.models import (
    ChatMessage,
    ChatMode,
    LanguagePair,
    MessageKind,
    MessageRole,
)
from dekomposit.tui.services import AgentService, ServiceReply


logger = logging.getLogger(__name__)


class ChatBubble(Static):
    def __init__(self, message: ChatMessage) -> None:
        classes = "bubble"
        body = Text()
        if message.kind == MessageKind.TRANSLATED and message.pair_label:
            body.append(f"[{message.pair_label}]\n", style="italic #8f946f")
            body.append(message.text)
        else:
            body.append(message.text)

        super().__init__(body, classes=classes)


class MessageRow(Container):
    def __init__(self, message: ChatMessage) -> None:
        super().__init__(
            classes=f"message-row role-{message.role.value} kind-{message.kind.value}"
        )
        self._message = message

    def compose(self) -> ComposeResult:
        yield ChatBubble(self._message)


class DekompositTuiApp(App[None]):
    CSS_PATH = "app.tcss"
    TITLE = "dekomposit"
    BINDINGS = [
        Binding("tab,ctrl+i", "toggle_mode", "Toggle mode", priority=True),
        Binding("ctrl+tab", "swap_pair", "Swap languages", priority=True),
        Binding("ctrl+w", "swap_pair", "Swap languages", show=False, priority=True),
        Binding("ctrl+l", "focus_input", "Focus input", show=False, priority=True),
    ]

    def __init__(self, service: AgentService | None = None) -> None:
        super().__init__()
        self._service = service or AgentService()
        self._mode = ChatMode.NORMAL
        self._pair = LanguagePair()
        self._pending = False
        self._status_text = "Ready."

    @property
    def mode(self) -> ChatMode:
        return self._mode

    @property
    def pair(self) -> LanguagePair:
        return self._pair

    def compose(self) -> ComposeResult:
        with Container(id="root"):
            with Horizontal(id="topbar"):
                yield Static("dekomposit", id="brand")
                with Horizontal(id="chips"):
                    yield Static(id="mode-indicator", classes="chip")
                    yield Static(id="pair-indicator", classes="chip")
            with Container(id="transcript-shell"):
                yield VerticalScroll(id="messages")
            with Container(id="composer"):
                yield Input(
                    placeholder='Tip Prompt "Give me today\'s reading practice"',
                    id="chat-input",
                    classes="-textual-compact",
                )
            with Horizontal(id="footer-bar"):
                yield Static(id="status-line")
                yield Static(
                    "Ctrl+Tab/Ctrl+W swap languages   Tab toggle mode",
                    id="hint-line",
                )

    def on_mount(self) -> None:
        self.query_one("#chat-input", Input).focus()
        self._refresh_chrome()

    def action_toggle_mode(self) -> None:
        self._mode = (
            ChatMode.TRANSLATION if self._mode == ChatMode.NORMAL else ChatMode.NORMAL
        )
        self._status_text = f"Mode set to {self._mode.value}."
        self._refresh_chrome()

    def action_swap_pair(self) -> None:
        self._pair = self._pair.swapped()
        self._status_text = f"Language pair: {self._pair.label}."
        self._refresh_chrome()

    def action_focus_input(self) -> None:
        self.query_one("#chat-input", Input).focus()

    def on_key(self, event: events.Key) -> None:
        if event.key in {"tab", "ctrl+i"}:
            self.action_toggle_mode()
            event.stop()

    @on(Input.Submitted, "#chat-input")
    def handle_input_submitted(self, event: Input.Submitted) -> None:
        raw_text = event.value
        event.input.value = ""

        parsed = parse_input(raw_text)
        if parsed.error:
            self._append_message(
                ChatMessage(
                    role=MessageRole.ASSISTANT,
                    text=f"Oops... {parsed.error}",
                    kind=MessageKind.ERROR,
                )
            )
            self._status_text = "Command failed."
            self._refresh_chrome()
            return

        if parsed.pair is not None:
            self._pair = parsed.pair
            self._status_text = f"Language pair: {self._pair.label}."

        text_to_send = parsed.text
        if not text_to_send:
            self._refresh_chrome()
            return

        if self._pending:
            self._append_message(
                ChatMessage(
                    role=MessageRole.ASSISTANT,
                    text="Oops... still processing the previous message.",
                    kind=MessageKind.ERROR,
                )
            )
            self._status_text = "Busy."
            self._refresh_chrome()
            return

        self._append_message(
            ChatMessage(
                role=MessageRole.USER,
                text=text_to_send,
            )
        )

        self._pending = True
        self._status_text = "Thinking..."
        self._refresh_chrome()
        self.run_worker(
            self._request_reply(
                text=text_to_send,
                mode=self._mode,
                pair=self._pair,
            ),
            exclusive=True,
            group="chat",
        )

    async def _request_reply(
        self,
        text: str,
        mode: ChatMode,
        pair: LanguagePair,
    ) -> None:
        try:
            reply = await self._service.ask(text=text, mode=mode, pair=pair)
            self._append_service_reply(reply=reply, pair=pair)
            self._status_text = "Ready."
        except Exception:
            logger.exception("Background chat worker failed")
            self._append_message(
                ChatMessage(
                    role=MessageRole.ASSISTANT,
                    text="Oops... something went wrong.",
                    kind=MessageKind.ERROR,
                )
            )
            self._status_text = "Failed."
        finally:
            self._pending = False
            self._refresh_chrome()

    def _append_service_reply(self, reply: ServiceReply, pair: LanguagePair) -> None:
        if not reply.text:
            return

        pair_label = pair.label if reply.kind == MessageKind.TRANSLATED else None
        self._append_message(
            ChatMessage(
                role=MessageRole.ASSISTANT,
                text=reply.text,
                kind=reply.kind,
                pair_label=pair_label,
            )
        )

    def _append_message(self, message: ChatMessage) -> None:
        transcript = self.query_one("#messages", VerticalScroll)
        transcript.mount(MessageRow(message))
        self.call_after_refresh(transcript.scroll_end, animate=False)

    def _refresh_chrome(self) -> None:
        mode_name = "TRANSLATION" if self._mode == ChatMode.TRANSLATION else "NORMAL"
        mode_indicator = self.query_one("#mode-indicator", Static)
        pair_indicator = self.query_one("#pair-indicator", Static)
        status_line = self.query_one("#status-line", Static)
        prompt = self.query_one("#chat-input", Input)

        mode_indicator.update(f"Mode: {mode_name}")
        pair_indicator.update(f"Pair: {self._pair.label}")
        status_line.update(self._status_text)

        if self._mode == ChatMode.TRANSLATION:
            prompt.placeholder = f"Translate ({self._pair.label})..."
        else:
            prompt.placeholder = 'Tip Prompt "Give me today\'s reading practice"'
