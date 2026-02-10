from pydantic import BaseModel, Field


class Translation(BaseModel):
    """Translation request/response model"""

    source: str = Field(..., description="Original sentence in source language")
    translated: str = Field(..., description="Translated sentence in target language")
    from_lang: str | None = Field(None, description="Source language code (e.g., 'en', 'es', 'fr')")
    to_lang: str | None = Field(None, description="Target language code (e.g., 'en', 'es', 'fr')")
