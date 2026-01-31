# AGENTS.md

This file provides guidance for agentic coding assistants working in the **dekomposit** repository.

## Project Overview

**dekomposit** is a language learning service that decomposes translations into natural phrase chunks to improve vocabulary acquisition. The project uses LLMs (OpenAI, Gemini) for translation and evaluation.

- **Language**: Python 3.14
- **Architecture**: Async-first with Pydantic models, OpenAI SDK with custom base URLs
- **Stack**: Will evolve to FastAPI + PostgreSQL + SQLAlchemy (currently core translation features)

## Environment Setup

```bash
# Activate virtual environment (ALWAYS do this first)
source .venv/bin/activate  # Linux/Mac
.venv\Scripts\activate     # Windows

# Environment variables are in .env (git-ignored)
# Key variables: CURRENT_API_KEY, LLM_MODEL, LLM_SERVER, LLM_TEMPERATURE, LLM_MAX_TOKENS
```

## Development Commands

### Running Tests & Evaluation

```bash
# Run LLM evaluation with DeepEval (GEval metrics)
python -m dekomposit.llm.evaluation

# Run specific evaluation functions in Python:
# >>> from dekomposit.llm.evaluation import geval_test_llm, bert_test_llm
# >>> import asyncio
# >>> asyncio.run(bert_test_llm())  # BERTScore semantic similarity
# >>> geval_test_llm()              # DeepEval GEval translation quality
```

**Note**: Currently no pytest test files exist. Tests are evaluation-based (see `dekomposit/llm/evaluation.py`).

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

# Local
from dekomposit.config import DEFAULT_LLM
from dekomposit.llm.types import Translation
```

**Style**:
- Avoid wildcard imports (`from module import *`)
- Use absolute imports for clarity: `from dekomposit.llm.features import translate`
- Group related imports together

### 2. Type Annotations

**Required**: Always use type hints for function parameters and return values.

```python
# Good
async def translate(
    text: str, *, source_lang: Language | str, target_lang: Language | str
) -> Translation:
    ...

def bert_evaluate(refs, candidates, lang="en") -> list[float]:
    ...

# Modern union syntax
def __init__(self, model: str | None = None, server: str | None = None) -> None:
    ...
```

**Guidelines**:
- Use `str | None` instead of `Optional[str]` (Python 3.10+ syntax)
- Use `list[str]` instead of `List[str]` when possible
- Use `type[BaseModel]` for class types
- Add return type hints even for `None` returns

### 3. Async/Await Patterns

**Philosophy**: This project is async-first. All LLM interactions must be async.

```python
# Correct: async function with proper await
async def translate(text: str, *, source_lang: str, target_lang: str) -> Translation:
    client = Client()
    response = await client.request(...)
    return response.choices[0].message.parsed

# Correct: gathering multiple async tasks
tasks = [translate(text, source_lang="uk", target_lang="en") for text in texts]
completed = await asyncio.gather(*tasks)
```

**Rules**:
- Use `async def` for any function that calls LLM APIs
- Use `await` for all async calls (never mix sync/async incorrectly)
- Use `asyncio.gather()` for parallel execution
- Run async functions with `asyncio.run()` from sync contexts

### 4. Pydantic Models

**Structured Output**: Use Pydantic models for LLM response schemas.

```python
class TranslationPhrase(BaseModel):
    phrase_source: str = Field(
        description="A natural phrase chunk 1+ words..."
    )
    phrase_translated: str = Field(
        description="Translation of phrase_source..."
    )

class Translation(BaseModel):
    translation: list[TranslationPhrase] = Field(
        description="List of natural phrase pairs..."
    )
```

**Guidelines**:
- Use `Field()` with detailed descriptions (helps LLM structured output)
- Use `list[Type]` instead of `List[Type]` in Python 3.9+
- Use `str | None` for optional fields or `Optional[str]`
- Use StrEnum for string enumerations (see `Language` class)

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

- **Classes**: `PascalCase` (e.g., `TranslationPrompt`, `Client`)
- **Functions/Methods**: `snake_case` (e.g., `translate()`, `get_prompt()`)
- **Constants**: `UPPER_SNAKE_CASE` (e.g., `DEFAULT_LLM`, `TRANSLATION_TAG_START`)
- **Private attributes**: Prefix with `_` (e.g., `self._instruction_prompt`)
- **Module names**: `snake_case` (e.g., `base_client.py`, `types.py`)

### 7. Error Handling

```python
# Validate inputs explicitly
if (source_lang not in Language) or (target_lang not in Language):
    raise ValueError(
        "Incorrect language. See all supported languages in dekomposit.llm.types.Language"
    )

# Handle environment variables gracefully
LLM_SERVER = os.getenv("LLM_SERVER", DEFAULT_SERVER)
if LLM_SERVER.lower() in ["none", "null"]:
    LLM_SERVER = None
```

**Rules**:
- Raise descriptive exceptions with helpful messages
- Provide defaults for environment variables via `os.getenv(key, default)`
- Validate inputs at function entry points

### 8. Docstrings

Use concise docstrings for non-obvious functions:

```python
async def translate(text: str, *, source_lang: Language | str, target_lang: Language | str) -> Translation:
    """Translate text between languages using LLM with phrase decomposition."""
    ...

def bert_evaluate(refs, candidates, lang="en"):
    """Evaluate candidate texts against reference texts using BERTScore."""
    ...
```

**Style**: Simple one-liner describing what the function does. No need for elaborate multi-line docstrings unless the function is complex.

## Project-Specific Rules

### Translation Philosophy

**Critical**: Translations must decompose into natural phrase chunks:
- Keep idioms together as single units (e.g., "kick the bucket" → one phrase)
- Preserve phrasal verbs (e.g., "give up" → one phrase)
- **NEVER create standalone punctuation entries** (e.g., `{"phrase_source": ".", "phrase_translated": "."}`). Always attach punctuation to adjacent words.
- Auto-correct grammar/spelling errors in input
- Preserve special characters in position

### LLM Configuration

- Use `python-dotenv` for environment management
- Support multiple providers via OpenAI-compatible endpoints
- Always log token usage for each LLM request
- Use structured output parsing with `chat.completions.parse()`

## File Organization

```
dekomposit/
├── config.py              # Environment config, constants
├── llm/
│   ├── __init__.py        # Empty
│   ├── types.py           # Pydantic models (TranslationPhrase, Translation, Language)
│   ├── base_client.py     # AsyncOpenAI wrapper (Client class)
│   ├── prompts.py         # Prompt engineering (TranslationPrompt)
│   ├── features.py        # Main translate() function
│   └── evaluation.py      # DeepEval + BERTScore evaluation
```

## Common Tasks

### Adding a new language

1. Add to `Language` enum in `dekomposit/llm/types.py`
2. Test with existing evaluation examples

### Adding a new feature function

1. Create async function in `dekomposit/llm/features.py`
2. Use `Client` class for LLM calls
3. Define Pydantic model for structured output
4. Add prompt class in `prompts.py` if needed

### Running evaluation

```bash
python -m dekomposit.llm.evaluation  # Runs geval_test_llm() by default
```

## References

- Full tech requirements: `docs/tech_requirements.md`
- Project context: `CLAUDE.md`
- Python version: **3.14**
