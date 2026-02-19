import logging
from dataclasses import dataclass

from dekomposit.llm.agent import Agent
from dekomposit.tui.formatting import parse_assistant_text
from dekomposit.tui.models import ChatMode, LanguagePair, MessageKind


logger = logging.getLogger(__name__)


TRANSLATION_MODE_TEMPLATE = """You are in strict translation mode.
Translate the user text from {source_lang} to {target_lang}.

Rules:
1) Reply only with the translated text.
2) Do not add explanations, comments, or transliteration.
3) Return exactly one XML-like wrapper and nothing else:
<translated>{{translation}}</translated>

User text:
{text}
"""


def build_translation_prompt(text: str, pair: LanguagePair) -> str:
    return TRANSLATION_MODE_TEMPLATE.format(
        source_lang=pair.source_lang,
        target_lang=pair.target_lang,
        text=text,
    )


@dataclass(frozen=True, slots=True)
class ServiceReply:
    text: str
    kind: MessageKind


class AgentService:
    def __init__(
        self,
        agent: Agent | None = None,
        error_message: str = "Oops... I hit an error. Please try again.",
    ) -> None:
        self._agent = agent or Agent()
        self._error_message = error_message

    async def ask(
        self,
        text: str,
        mode: ChatMode,
        pair: LanguagePair,
    ) -> ServiceReply:
        user_text = text.strip()
        if not user_text:
            return ServiceReply(text="", kind=MessageKind.PLAIN)

        prompt = (
            user_text
            if mode is ChatMode.NORMAL
            else build_translation_prompt(user_text, pair)
        )
        default_kind = (
            MessageKind.TRANSLATED
            if mode is ChatMode.TRANSLATION
            else MessageKind.PLAIN
        )

        try:
            raw_reply = await self._agent.chat(prompt)
        except Exception:
            logger.exception("Agent request failed")
            return ServiceReply(text=self._error_message, kind=MessageKind.ERROR)

        parsed = parse_assistant_text(raw_reply, default_kind=default_kind)
        if not parsed.text:
            return ServiceReply(text=self._error_message, kind=MessageKind.ERROR)

        return ServiceReply(text=parsed.text, kind=parsed.kind)
