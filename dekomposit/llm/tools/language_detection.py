import json
import logging
from typing import Any

from dekomposit.llm.tools.base import BaseTool
from dekomposit.llm.types import LanguageDetection


logging.basicConfig(
    datefmt="%d/%m/%Y %H:%M",
    format="%(asctime)s %(name)-12s %(levelname)-8s %(message)s",
)
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


class LanguageDetectionTool(BaseTool):
    """Tool for detecting language of text using LLM.

    Uses structured output to return language code and confidence.
    """

    def __init__(self, detection_prompt: str | None = None) -> None:
        """Initialize language detection tool.

        Args:
            detection_prompt: Optional custom prompt for detection.
        """
        super().__init__(
            name="detect_language",
            description="Detect language of text. Returns language code (en, ru, uk, sk) and confidence.",
        )
        self._detection_prompt = detection_prompt

    def set_prompt(self, prompt: str) -> None:
        """Set the detection prompt."""
        self._detection_prompt = prompt

    async def __call__(self, text: str) -> dict[str, Any]:
        """Detect language of the given text.

        Args:
            text: Text to detect language for

        Returns:
            Dict with language code and confidence
            Example: {"language": "uk", "confidence": "high"}
        """
        from dekomposit.llm.base_client import Client

        if not text or not text.strip():
            return {"language": "unknown", "confidence": "none", "error": "Empty text"}

        client = Client()

        default_prompt = """Detect the language of the following text. Return only the language code:
- en - English
- ru - Russian
- uk - Ukrainian
- sk - Slovak
- other - unknown

Be precise:
- Ukrainian uses letters і, ї, є, ґ
- Russian uses ъ, ы, э, ё
- Slovak uses diacritics like č, š, ž, ľ, ť, ň, ď"""

        prompt = self._detection_prompt or default_prompt

        messages = [
            {"role": "system", "content": prompt},
            {"role": "user", "content": text},
        ]

        try:
            response = await client.request(
                messages=messages,
                return_format=LanguageDetection,
            )

            parsed = response.choices[0].message.parsed

            if parsed:
                logger.debug(f"Detected language: {parsed.language} (confidence: {parsed.confidence})")
                return {
                    "language": parsed.language,
                    "confidence": parsed.confidence,
                }

            return {"language": "unknown", "confidence": "none", "error": "No response"}

        except Exception as e:
            logger.error(f"Language detection failed: {e}")
            return {"language": "unknown", "confidence": "none", "error": str(e)}

    def get_schema(self) -> dict[str, Any]:
        """Return OpenAI function calling schema."""
        return {
            "type": "object",
            "properties": {
                "text": {
                    "type": "string",
                    "description": "Text to detect language for"
                }
            },
            "required": ["text"],
        }
