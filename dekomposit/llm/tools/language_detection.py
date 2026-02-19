import logging
from typing import Any

from dekomposit.llm.tools.base import BaseTool
from dekomposit.llm.types import LanguageDetection
from dekomposit.llm.utils import detect_language_local


logger = logging.getLogger(__name__)


class LanguageDetectionTool(BaseTool):
    """Tool for detecting language of text using LLM with local fallback."""

    def __init__(
        self,
        detection_prompt: str | None = None,
        supported_languages: tuple[str, ...] = ("en", "ru", "uk", "sk", "other"),
    ) -> None:
        super().__init__(
            name="detect_language",
            description=(
                "Detect language of text and return code + confidence. "
                "Primary: LLM, fallback: local heuristic."
            ),
        )
        self._detection_prompt = detection_prompt
        self._supported_languages = supported_languages

    def set_prompt(self, prompt: str) -> None:
        self._detection_prompt = prompt

    def _default_prompt(self) -> str:
        languages = "\n".join(f"- {code}" for code in self._supported_languages)
        return (
            "Detect the language of the following text. "
            "Return a language code and confidence.\n"
            f"Supported codes:\n{languages}"
        )

    async def __call__(self, text: str) -> dict[str, Any]:
        from dekomposit.llm.base_client import Client

        if not text or not text.strip():
            return {"language": "unknown", "confidence": "none", "error": "Empty text"}

        client = Client()
        prompt = self._detection_prompt or self._default_prompt()
        messages = [
            {"role": "system", "content": prompt},
            {"role": "user", "content": text},
        ]

        try:
            response = await client.request(
                messages=messages, return_format=LanguageDetection
            )
            parsed = response.choices[0].message.parsed
            if parsed and parsed.language:
                return {
                    "language": parsed.language,
                    "confidence": parsed.confidence,
                    "source": "llm",
                }
        except Exception as exc:
            logger.warning(
                "LLM language detection failed, using local fallback: %s", exc
            )

        fallback = detect_language_local(text)
        if fallback:
            return {
                "language": fallback,
                "confidence": "low",
                "source": "heuristic",
            }

        return {
            "language": "other",
            "confidence": "none",
            "source": "heuristic",
        }

    def get_schema(self) -> dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "text": {
                    "type": "string",
                    "description": "Text to detect language for",
                }
            },
            "required": ["text"],
        }
