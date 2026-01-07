from openai import AsyncOpenAI

from novamova.config import cfg


DEFAULT_LLM = "gemini-flash-lite-latest"
DEFAULT_SERVER = "https://generativelanguage.googleapis.com/v1beta/openai/"

LLM_SERVER = cfg.get("LLM_SERVER", DEFAULT_SERVER)
LLM_MODEL = cfg.get("LLM_MODEL", DEFAULT_LLM)

client = AsyncOpenAI(api_key=cfg["LLMAPI_KEY"], base_url=LLM_SERVER)
