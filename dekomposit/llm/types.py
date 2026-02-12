from pydantic import BaseModel, Field


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
