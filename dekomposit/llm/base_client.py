import logging
from functools import lru_cache
from typing import Any, AsyncGenerator, cast

from openai import AsyncOpenAI
from pydantic import BaseModel

from dekomposit.config import get_settings


logger = logging.getLogger(__name__)


class Client:
    """AsyncOpenAI wrapper for dekomposit."""

    def __init__(self, model: str | None = None, provider: str | None = None) -> None:
        settings = get_settings()

        if provider:
            resolved_provider = provider.strip().lower()
            endpoint = settings.endpoint_for(resolved_provider)
        else:
            resolved_provider = settings.current_provider
            endpoint = settings.current_endpoint

        self.model = model or settings.current_llm
        self.provider = resolved_provider
        self.endpoint = endpoint
        self.temperature = settings.llm_temperature
        self.max_tokens = settings.llm_max_tokens
        self.api_key_name = settings.current_api_key
        self.api_key = settings.selected_api_key

    @staticmethod
    @lru_cache
    def _client_for(api_key: str, endpoint: str) -> AsyncOpenAI:
        return AsyncOpenAI(api_key=api_key, base_url=endpoint)

    def _client(self) -> AsyncOpenAI:
        if not self.api_key:
            raise ValueError(f"Missing API key value for env var '{self.api_key_name}'")
        return self._client_for(self.api_key, self.endpoint)

    async def request(
        self,
        messages: list[dict[str, Any]],
        return_format: type[BaseModel],
        model: str | None = None,
        temperature: float | None = None,
        timeout: float = 30.0,
    ) -> Any:
        """Wrapper around `chat.completions.parse`."""
        model = model or self.model
        temperature = self.temperature if temperature is None else temperature
        completions = cast(Any, self._client().chat.completions)

        response = await completions.parse(
            model=model,
            messages=messages,
            response_format=return_format,
            temperature=temperature,
            max_tokens=self.max_tokens,
            timeout=timeout,
        )

        usage = cast(Any, response.usage)
        if usage:
            logger.info(
                "LLMCALL %s\tTOKENS USED: %s (input); %s (output); %s (total)",
                response.id,
                usage.prompt_tokens,
                usage.completion_tokens,
                usage.total_tokens,
            )
        return response

    async def request_with_tools(
        self,
        messages: list[dict[str, Any]],
        tools: list[dict[str, Any]] | None = None,
        model: str | None = None,
        temperature: float | None = None,
        timeout: float = 30.0,
    ) -> Any:
        """Wrapper around `chat.completions.create` with tools."""
        model = model or self.model
        temperature = self.temperature if temperature is None else temperature
        completions = cast(Any, self._client().chat.completions)

        response = await completions.create(
            model=model,
            messages=messages,
            tools=tools,
            temperature=temperature,
            max_tokens=self.max_tokens,
            timeout=timeout,
        )

        usage = cast(Any, response.usage)
        if usage:
            logger.info(
                "LLMCALL %s\tTOKENS USED: %s (input); %s (output); %s (total)",
                response.id,
                usage.prompt_tokens,
                usage.completion_tokens,
                usage.total_tokens,
            )
        return response

    async def stream(
        self,
        messages: list[dict[str, Any]],
        model: str | None = None,
        temperature: float | None = None,
        timeout: float = 30.0,
    ) -> AsyncGenerator[str, None]:
        """Stream chat completions without structured output."""
        model = model or self.model
        temperature = self.temperature if temperature is None else temperature
        completions = cast(Any, self._client().chat.completions)

        stream = await completions.create(
            model=model,
            messages=messages,
            temperature=temperature,
            max_tokens=self.max_tokens,
            stream=True,
            timeout=timeout,
        )

        async for chunk in stream:
            if chunk.choices and chunk.choices[0].delta.content:
                yield chunk.choices[0].delta.content
