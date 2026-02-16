from pydantic import BaseModel, Field


class ToolDecision(BaseModel):
    """LLM decision for routing user input."""

    action: str = Field(description="translate or respond")
    text: str = Field(description="Text to translate or respond to")
    source_lang: str | None = Field(default=None, description="Source language code")
    target_lang: str | None = Field(default=None, description="Target language code")


class AgentResponse(BaseModel):
    """Simple response payload for non-translation replies."""

    message: str = Field(description="Response text")


class LanguageDetection(BaseModel):
    """LLM-detected language with confidence."""

    language: str = Field(description="Language code: en, ru, uk, sk, or other")
    confidence: str = Field(description="Confidence level: high, medium, low")


class Translation(BaseModel):
    """Translation request/response model

    Note that the languages may be the same; if so, only the text
    accuracy is corrected

    If it is a request, then translated field is None"""

    source: str = Field(..., description="Original text in source language")
    translated: str | None = Field(
        ..., description="Translated text in target language"
    )
    from_lang: str | None = Field(
        None, description="Source language code (e.g., 'en', 'es', 'fr')"
    )
    to_lang: str | None = Field(
        None, description="Target language code (e.g., 'en', 'es', 'fr')"
    )
