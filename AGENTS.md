# AGENTS.md

This file provides guidance for agentic coding assistants working in the **dekomposit** repository.

## Project Overview

**dekomposit** is a language learning service with dual interfaces:

1. **Telegram AI Agent** (primary) - Conversational language coach in Telegram
2. **Web Platform** - Extended features (reading, vocabulary dashboard)

The core uses LLMs (OpenAI, Gemini) to provide personalized language learning experiences.

- **Language**: Python 3.12
- **Architecture**: Async-first with Pydantic models, OpenAI SDK with custom base URLs
- **Telegram Bot**: aiogram (async framework)
- **Web Stack**: FastAPI + PostgreSQL + SQLAlchemy + htmx frontend

## Environment Setup

```bash
# Activate virtual environment (ALWAYS do this first)
source .venv/bin/activate  # Linux/Mac
.venv\Scripts\activate     # Windows

# Environment variables are in .env (git-ignored)
# Key variables: CURRENT_API_KEY, CURRENT_LLM, CURRENT_PROVIDER,
#                LLM_TEMPERATURE, LLM_MAX_TOKENS, TELEGRAM_BOT_TOKEN
```

## Development Commands

### Code Quality Tools

```bash
# Type checking (if mypy configured)
mypy dekomposit/

# Linting (if ruff configured)
ruff check dekomposit/

# Format checking
ruff format --check dekomposit/
```

**Note**: No pyproject.toml, setup.py, or tool configs found. Tools may need manual configuration.

## Code Style Guidelines

### 1. Import Organization

**Order**: Standard library → Third-party → Local modules

```python
# Standard library
import os
import logging
from functools import lru_cache

# Third-party
from openai import AsyncOpenAI
from pydantic import BaseModel, Field
from aiogram import Bot, Dispatcher, Router
from aiogram.types import Message

# Local
from dekomposit.config import DEFAULT_LLM
from dekomposit.llm.base_client import Client
```

**Style**:
- Avoid wildcard imports (`from module import *`)
- Use absolute imports for clarity
- Group related imports together

### 2. Type Annotations

**Required**: Always use type hints for function parameters and return values.

```python
# Good
async def handle_message(message: Message, user_id: int) -> None:
    ...

def process_data(items: list[str]) -> dict[str, int]:
    ...

# Modern union syntax
def __init__(self, model: str | None = None, provider: str | None = None) -> None:
    ...
```

**Guidelines**:
- Use `str | None` instead of `Optional[str]` (Python 3.10+ syntax)
- Use `list[str]` instead of `List[str]` when possible
- Use `type[BaseModel]` for class types
- Add return type hints even for `None` returns

### 3. Async/Await Patterns

**Philosophy**: This project is async-first. All LLM interactions and bot handlers must be async.

```python
# Correct: async function with proper await
async def call_llm(prompt: str) -> str:
    client = Client()
    response = await client.request(...)
    return response.choices[0].message.content

# Correct: gathering multiple async tasks
tasks = [process_item(item) for item in items]
completed = await asyncio.gather(*tasks)

# Correct: aiogram message handler
@router.message(Command("start"))
async def cmd_start(message: Message) -> None:
    await message.answer("Welcome!")
```

**Rules**:
- Use `async def` for any function that calls LLM APIs or bot methods
- Use `await` for all async calls (never mix sync/async incorrectly)
- Use `asyncio.gather()` for parallel execution
- Run async functions with `asyncio.run()` from sync contexts
- All aiogram handlers must be async

### 4. Pydantic Models

**Structured Output**: Use Pydantic models for LLM response schemas.

```python
class VocabularyEntry(BaseModel):
    word: str = Field(description="The vocabulary word")
    translation: str = Field(description="Translation of the word")
    example: str = Field(description="Example sentence using the word")
    difficulty: int = Field(description="Difficulty level 1-5", ge=1, le=5)
```

**Guidelines**:
- Use `Field()` with detailed descriptions (helps LLM structured output)
- Use `list[Type]` instead of `List[Type]` in Python 3.9+
- Use `str | None` for optional fields or `Optional[str]`
- Use StrEnum for string enumerations

### 5. Logging

**Standard**: Use Python's logging module, not print statements.

```python
import logging

logging.basicConfig(
    datefmt="%d/%m/%Y %H:%M",
    format="%(asctime)s %(name)-12s %(levelname)-8s %(message)s",
)
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

# Usage
logger.info(f"LLMCALL {response.id}\tTOKENS USED: {usage.total_tokens}")
```

### 6. Naming Conventions

- **Classes**: `PascalCase` (e.g., `TranslationBot`, `Client`)
- **Functions/Methods**: `snake_case` (e.g., `translate()`, `get_response()`)
- **Constants**: `UPPER_SNAKE_CASE` (e.g., `DEFAULT_LLM`, `MAX_TOKENS`)
- **Private attributes**: Prefix with `_` (e.g., `self._api_key`)
- **Module names**: `snake_case` (e.g., `base_client.py`, `handlers.py`)

### 7. Error Handling

```python
# Validate inputs explicitly
if not user_id:
    raise ValueError("user_id is required")

# Handle environment variables gracefully
provider = os.getenv("CURRENT_PROVIDER", "gemini")
model = os.getenv("CURRENT_LLM", "gemini-flash-lite-latest")
```

**Rules**:
- Raise descriptive exceptions with helpful messages
- Provide defaults for environment variables via `os.getenv(key, default)`
- Validate inputs at function entry points

### 8. Docstrings

Use concise docstrings for non-obvious functions:

```python
async def handle_vocab_save(message: Message, word: str) -> None:
    """Save a vocabulary word to the user's collection."""
    ...

def calculate_difficulty(word: str, user_level: str) -> int:
    """Estimate word difficulty based on user's proficiency level."""
    ...
```

**Style**: Simple one-liner describing what the function does. No need for elaborate multi-line docstrings unless the function is complex.

## Project-Specific Rules

### LLM Configuration

- Use `python-dotenv` for environment management
- Support multiple providers via OpenAI-compatible endpoints
- Always log token usage for each LLM request
- Use structured output parsing with `chat.completions.parse()`

### Telegram Bot Design

- Bot personality is defined in `dekomposit/llm/base_prompts/SOUL.md`
- Base prompt is the aggregation of `SOUL.md` + `MEMORY.md` via `Agent.get_base_prompts()`
- Use aiogram's `Router` for organizing handlers
- All handlers must be async
- Use `Message.answer()` for responses, not `Bot.send_message()` when possible
- Implement inline mode for translations in any chat
- Use callback queries for interactive elements (save to vocab, etc.)

### Platform-Specific Features

**Telegram-only**:
- Daily push notifications (vocabulary packs)
- Streak tracking and reminders
- Inline mode for quick translations
- Interactive dialogue in chat (bot plays one speaker, user the other)

**Web-only**:
- Reading section with inline translation
- Full vocabulary dashboard
- Trusted Authors paper library
- Account/settings management UI

**Shared**:
- Translation core
- Vocabulary storage (backend)
- Example generation
- Learning method logic

## File Organization

```
dekomposit/
├── config.py              # Environment config, constants
├── llm/
│   ├── __init__.py        # Empty
│   ├── base_client.py     # AsyncOpenAI wrapper (Client class)
│   └── base_prompts/
│       ├── SOUL.md        # Bot personality definition
│       └── MEMORY.md      # Session memory
├── bot/                   # (Planned) Telegram bot code
│   ├── handlers/          # Message/command handlers
│   ├── keyboards.py       # Inline keyboards
│   └── main.py            # Bot entry point
├── web/                   # (Planned) FastAPI web app
│   ├── api/               # API routes
│   ├── models.py          # SQLAlchemy models
│   └── main.py            # FastAPI app
└── services/              # (Planned) Shared business logic
    ├── translation.py     # Translation service
    ├── vocabulary.py      # Vocab CRUD
    └── user.py            # User management
```

## Common Tasks

### Updating bot personality

Edit `dekomposit/llm/base_prompts/SOUL.md` to change the conversational tone and teaching approach.

### Adaptive Translation datasets (Cloud Translation)

- Datasets are created and imported via the Cloud Translation API.
- Supported dataset location: `us-central1` only.
- Source TSVs live in `dekomposit/llm/datasets/automl/` and use `source<TAB>target` format.
- Workflow: upload TSVs to GCS, create datasets per direction, import TSVs, then call `adaptiveMtTranslate` with the dataset name.
- Tooling: `dekomposit/llm/tools/adaptive_translation.py` calls `adaptiveMtTranslate` using ADC or `GOOGLE_OAUTH_ACCESS_TOKEN`.
- Environment: `GOOGLE_CLOUD_PROJECT`, `ADAPTIVE_MT_LOCATION`, `ADAPTIVE_MT_DATASET_ID`, `ADAPTIVE_MT_DATASET_NAME`, `GOOGLE_APPLICATION_CREDENTIALS`.

### Agent tool routing

- Entry point: `Agent.handle_message()` in `dekomposit/llm/agent.py`.
- Tool selection: LLM returns a `ToolDecision` with `action`, `source_lang`, `target_lang`.
- Translation: uses `AdaptiveTranslationTool` with dataset `adaptive-<src>-<tgt>`; if dataset is missing, returns `None`.

## References

- Full tech requirements: `docs/tech_requirements.md`
- Bot personality: `dekomposit/llm/base_prompts/SOUL.md`
- Python version: **3.12**
