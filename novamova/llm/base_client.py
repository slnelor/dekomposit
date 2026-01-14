import os
import logging
from functools import lru_cache

from openai import AsyncOpenAI
from pydantic import BaseModel

from novamova.config import DEFAULT_LLM, DEFAULT_SERVER, CURRENT_API_KEY, LLM_CONFIG


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
    """An AsyncOpenAI wrapper for novamova service"""

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
    ):
        """A method wrapper around openai.chat.completions.parse"""
        model = model or self.model

        response = await self.client().chat.completions.parse(
            model=model,
            messages=messages,
            response_format=return_format,
        )

        usage = response.usage
        logger.info(
            f"LLMCALL {response.id}\tTOKENS USED: {usage.prompt_tokens} (input); "
            f"{usage.completion_tokens} (output); {usage.total_tokens} (total)"
        )

        return response
