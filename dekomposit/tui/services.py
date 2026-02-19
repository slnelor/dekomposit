import logging
from html import unescape
from dataclasses import dataclass
from typing import Any

from dekomposit.llm.agent import Agent
from dekomposit.llm.tools.adaptive_translation import AdaptiveTranslationTool
from dekomposit.tui.formatting import parse_assistant_text
from dekomposit.tui.models import ChatMode, LanguagePair, MessageKind


logger = logging.getLogger(__name__)


def extract_translation_text(payload: dict[str, Any]) -> str | None:
    """Extract translated text from Adaptive MT response payload."""
    response = payload.get("response")
    if not isinstance(response, dict):
        return None

    translations = response.get("translations")
    if not isinstance(translations, list):
        return None

    for entry in translations:
        if not isinstance(entry, dict):
            continue

        candidate = entry.get("translatedText") or entry.get("translation")
        if isinstance(candidate, str) and candidate.strip():
            return unescape(candidate.strip())

    return None


@dataclass(frozen=True, slots=True)
class ServiceReply:
    text: str
    kind: MessageKind


class AgentService:
    def __init__(
        self,
        agent: Agent | None = None,
        translation_tool: AdaptiveTranslationTool | None = None,
        error_message: str = "Oops... I hit an error. Please try again.",
    ) -> None:
        self._agent = agent or Agent()
        self._translation_tool = translation_tool or AdaptiveTranslationTool()
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

        if mode is ChatMode.TRANSLATION:
            return await self._translate_strict(text=user_text, pair=pair)

        try:
            raw_reply = await self._agent.chat(user_text)
        except Exception:
            logger.exception("Agent request failed")
            return ServiceReply(text=self._error_message, kind=MessageKind.ERROR)

        parsed = parse_assistant_text(raw_reply, default_kind=MessageKind.PLAIN)
        if not parsed.text:
            return ServiceReply(text=self._error_message, kind=MessageKind.ERROR)

        return ServiceReply(text=parsed.text, kind=parsed.kind)

    async def _translate_strict(self, text: str, pair: LanguagePair) -> ServiceReply:
        try:
            payload = await self._translation_tool(
                text=text,
                source_lang=pair.source_lang,
                target_lang=pair.target_lang,
            )
        except Exception:
            logger.exception(
                "Strict translation failed for pair %s",
                pair.label,
            )
            return ServiceReply(text=self._error_message, kind=MessageKind.ERROR)

        translated = extract_translation_text(payload)
        if not translated:
            return ServiceReply(text=self._error_message, kind=MessageKind.ERROR)

        return ServiceReply(text=translated, kind=MessageKind.TRANSLATED)
