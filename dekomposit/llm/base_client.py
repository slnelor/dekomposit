import os
import logging
from functools import lru_cache
from typing import AsyncGenerator

from openai import AsyncOpenAI
from pydantic import BaseModel

from dekomposit.config import DEFAULT_LLM, DEFAULT_SERVER, CURRENT_API_KEY, LLM_CONFIG


logging.basicConfig(
    datefmt="%d/%m/%Y %H:%M",
    format="%(asctime)s %(name)-12s %(levelname)-8s %(message)s",
)
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

LLM_SERVER = os.getenv("LLM_SERVER", DEFAULT_SERVER)
if LLM_SERVER.lower() in ["none", "null"]:
    LLM_SERVER = None

LLM_MODEL = os.getenv("LLM_MODEL", DEFAULT_LLM)


class Client:
    """An AsyncOpenAI wrapper for dekomposit"""

    def __init__(
        self,
        model: str | None = None,
        server: str | None = None,
    ) -> None:
        self.model = model or LLM_MODEL
        self.server = server or LLM_SERVER

    @staticmethod
    @lru_cache
    def client() -> AsyncOpenAI:
        return AsyncOpenAI(api_key=LLM_CONFIG[CURRENT_API_KEY], base_url=LLM_SERVER)

    async def request(
        self,
        messages: list[dict],
        return_format: type[BaseModel],
        model: str | None = None,
        temperature: float | None = None,
        timeout: float = 30.0,
    ):
        """A method wrapper around openai.chat.completions.parse"""
        model = model or self.model
        temperature = temperature if temperature is not None else LLM_CONFIG["temperature"]

        response = await self.client().chat.completions.parse(
            model=model,
            messages=messages,
            response_format=return_format,
            temperature=temperature,
            timeout=timeout,
        )

        usage = response.usage
        logger.info(
            f"LLMCALL {response.id}\tTOKENS USED: {usage.prompt_tokens} (input); "
            f"{usage.completion_tokens} (output); {usage.total_tokens} (total)"
        )

        return response

    async def request_with_tools(
        self,
        messages: list[dict],
        tools: list[dict] | None = None,
        model: str | None = None,
        temperature: float | None = None,
        timeout: float = 30.0,
    ):
        """A method wrapper around openai.chat.completions with tool calling.
        
        Args:
            messages: Chat messages
            tools: OpenAI tool definitions
            model: Model to use
            temperature: Sampling temperature
            timeout: Request timeout
            
        Returns:
            ChatCompletion response with tool_calls
        """
        model = model or self.model
        temperature = temperature if temperature is not None else LLM_CONFIG["temperature"]

        response = await self.client().chat.completions.create(
            model=model,
            messages=messages,
            tools=tools,
            temperature=temperature,
            timeout=timeout,
        )

        usage = response.usage
        logger.info(
            f"LLMCALL {response.id}\tTOKENS USED: {usage.prompt_tokens} (input); "
            f"{usage.completion_tokens} (output); {usage.total_tokens} (total)"
        )

        return response

    async def stream(
        self,
        messages: list[dict],
        model: str | None = None,
        temperature: float | None = None,
        timeout: float = 30.0,
    ) -> AsyncGenerator[str, None]:
        """Stream chat completions without structured output."""
        model = model or self.model
        temperature = temperature if temperature is not None else LLM_CONFIG["temperature"]

        stream = await self.client().chat.completions.create(
            model=model,
            messages=messages,
            temperature=temperature,
            stream=True,
            timeout=timeout,
        )

        async for chunk in stream:
            if chunk.choices and chunk.choices[0].delta.content:
                yield chunk.choices[0].delta.content
