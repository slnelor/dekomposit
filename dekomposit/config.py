import json
import os
from functools import lru_cache

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    model_config = SettingsConfigDict(extra="ignore")

    section_placeholder: str = Field(default="###", alias="SECTION_PLACEHOLDER")
    current_llm: str = Field(default="gemini-flash-lite-latest", alias="CURRENT_LLM")
    current_provider: str = Field(default="gemini", alias="CURRENT_PROVIDER")
    current_api_key: str = Field(default="GEMINI_API_KEY", alias="CURRENT_API_KEY")

    llm_temperature: float = Field(default=1.0, alias="LLM_TEMPERATURE")
    llm_max_tokens: int = Field(default=1024, alias="LLM_MAX_TOKENS")

    provider_endpoints: dict[str, str] = Field(
        default_factory=lambda: {
            "gemini": "https://generativelanguage.googleapis.com/v1beta/openai/",
            "openai": "https://api.openai.com/v1",
            "openrouter": "https://openrouter.ai/api/v1",
        },
        alias="CURRENT_PROVIDER_ENDPOINTS",
    )

    google_cloud_project: str | None = Field(default=None, alias="GOOGLE_CLOUD_PROJECT")
    adaptive_mt_location: str = Field(
        default="us-central1", alias="ADAPTIVE_MT_LOCATION"
    )
    adaptive_mt_dataset_id: str | None = Field(
        default=None, alias="ADAPTIVE_MT_DATASET_ID"
    )
    adaptive_mt_dataset_name: str | None = Field(
        default=None, alias="ADAPTIVE_MT_DATASET_NAME"
    )

    @field_validator("provider_endpoints", mode="before")
    @classmethod
    def _parse_provider_endpoints(cls, value: object) -> object:
        if isinstance(value, str):
            try:
                parsed = json.loads(value)
            except json.JSONDecodeError as exc:
                raise ValueError(
                    "CURRENT_PROVIDER_ENDPOINTS must be valid JSON"
                ) from exc
            if not isinstance(parsed, dict):
                raise ValueError("CURRENT_PROVIDER_ENDPOINTS must decode to an object")
            return parsed
        return value

    @field_validator("current_provider")
    @classmethod
    def _normalize_provider(cls, value: str) -> str:
        return value.strip().lower()

    @field_validator("provider_endpoints")
    @classmethod
    def _normalize_endpoints(cls, value: dict[str, str]) -> dict[str, str]:
        normalized: dict[str, str] = {}
        for provider, endpoint in value.items():
            normalized[provider.strip().lower()] = endpoint.strip()
        return normalized

    @property
    def current_endpoint(self) -> str:
        endpoint = self.provider_endpoints.get(self.current_provider)
        if not endpoint:
            raise ValueError(
                f"No endpoint configured for provider '{self.current_provider}'. "
                "Set CURRENT_PROVIDER_ENDPOINTS with this provider key."
            )
        return endpoint

    @property
    def selected_api_key(self) -> str | None:
        return os.getenv(self.current_api_key)

    def endpoint_for(self, provider: str) -> str:
        key = provider.strip().lower()
        endpoint = self.provider_endpoints.get(key)
        if not endpoint:
            raise ValueError(
                f"No endpoint configured for provider '{key}'. "
                "Set CURRENT_PROVIDER_ENDPOINTS with this provider key."
            )
        return endpoint


@lru_cache
def get_settings() -> Settings:
    return Settings()
