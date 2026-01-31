import os
from dotenv import load_dotenv

load_dotenv()

SECTION_PLACEHOLDER = "###"  # Add in the beginning of the section
TRANSLATION_TAG_START = "<translation>"
TRANSLATION_TAG_END = "</translation>"

DEFAULT_LLM = "gemini-flash-lite-latest"
DEFAULT_SERVER = "https://generativelanguage.googleapis.com/v1beta/openai/"
CURRENT_API_KEY = os.getenv("CURRENT_API_KEY", "GEMINI_API_KEY")

LLM_CONFIG = {
    "temperature": float(os.getenv("LLM_TEMPERATURE", 0.2)),
    "max_tokens": int(os.getenv("LLM_MAX_TOKENS", 1024)),
    CURRENT_API_KEY: os.getenv(CURRENT_API_KEY),
}
