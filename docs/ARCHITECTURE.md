# dekomposit - Project Architecture

## Overview

**dekomposit** is a language learning service with dual interfaces:
- **Telegram AI Agent** - Conversational language coach
- **Web Platform** - Extended features (reading, vocabulary dashboard)

The core uses LLMs (OpenAI, Gemini) to provide personalized language learning experiences.

---

## Directory Structure

```
dekomposit/
├── config.py                    # Environment & configuration
├── __init__.py
└── llm/                        # Core LLM functionality
    ├── __init__.py
    ├── agent.py                # Main Agent class
    ├── base_client.py          # LLM client wrapper
    ├── types.py                # Pydantic models
    ├── base_prompts/           # Bot personality & memory
    │   ├── SOUL.md             # Bot personality definition
    │   └── MEMORY.md           # Session memory
    ├── tools/                  # Agent capabilities
    │   ├── __init__.py
    │   ├── base.py             # BaseTool abstract class
    │   ├── registry.py         # ToolRegistry (auto-discovery)
    │   ├── adaptive_translation.py  # Google Cloud Adaptive MT
    │   └── reverso_api.py      # Reverso Context API (skeleton)
    ├── utils/
    │   ├── __init__.py
    │   └── language_detection.py  # Heuristic language detection
    └── datasets/                # Translation dataset tools
        ├── __init__.py
        ├── translation_data_gen.py
        ├── deduplicate.py
        ├── generate_cli.py
        ├── review_pairs.py
        ├── automl/              # Source TSVs for Adaptive MT
        ├── review_state/       # Review session state
        └── *.json              # Generated datasets
```

---

## File Details

### `config.py` - Configuration Management

**Purpose**: Central configuration for the entire application.

| Constant/Variable | Type | Description |
|-------------------|------|-------------|
| `SECTION_PLACEHOLDER` | str | Marker for section headers |
| `TRANSLATION_TAG_START` | str | XML tag for formatted translations |
| `TRANSLATION_TAG_END` | str | XML tag closing |
| `DEFAULT_LLM` | str | Default LLM model (gemini-flash-lite-latest) |
| `DEFAULT_SERVER` | str | OpenAI-compatible API endpoint |
| `CURRENT_API_KEY` | str | Environment variable name for API key |
| `LLM_CONFIG` | dict | LLM settings (temperature, max_tokens) |

---

### `llm/base_client.py` - LLM Client Wrapper

**Purpose**: Async wrapper around OpenAI SDK with structured output support.

#### Class: `Client`

| Method | Signature | Description |
|--------|-----------|-------------|
| `client()` | `() -> AsyncOpenAI` | Cached AsyncOpenAI singleton |
| `request()` | `(messages, return_format, ...) -> Response` | Non-streaming request with structured output parsing |
| `stream()` | `(messages, ...) -> AsyncGenerator[str]` | Streaming chat completions |

**Key Features**:
- Supports any OpenAI-compatible API (Gemini, OpenAI, custom endpoints)
- Uses `chat.completions.parse()` for Pydantic structured output
- Logs token usage for every request

---

### `llm/types.py` - Data Models

**Purpose**: Pydantic models for type safety and structured output.

#### Models

| Class | Fields | Description |
|-------|--------|-------------|
| `ToolDecision` | `action`, `text`, `source_lang`, `target_lang` | LLM routing decision |
| `AgentResponse` | `message` | Simple chat response |
| `Translation` | `source`, `translated`, `from_lang`, `to_lang` | Translation request/response |

---

### `llm/agent.py` - Main Agent

**Purpose**: Core agent class handling message routing and tool execution.

#### Class: `Agent`

| Method | Signature | Description |
|--------|-----------|-------------|
| `__init__()` | `(model?, server?)` | Initialize client, registry, prompts |
| `_load_base_prompts()` | `() -> dict[str, str]` | Load SOUL.md and MEMORY.md |
| `_build_base_prompt()` | `(prompts) -> str` | Aggregate system prompt |
| `_build_routing_prompt()` | `() -> str` | Build dynamic routing prompt with available tools |
| `handle_message()` | `(text) -> dict \| None` | Main entry: route and process message |
| `chat()` | `(text) -> str` | Non-streaming chat entrypoint |
| `stream_chat()` | `(text) -> AsyncGenerator[str]` | Streaming chat entrypoint |
| `format_translation()` | `(result) -> str` | Format translation with XML tags |
| `_decide_action()` | `(text) -> ToolDecision` | Use LLM to decide translate/respond |
| `_handle_translation()` | `(decision) -> dict \| None` | Execute translation via tool registry |
| `_handle_response()` | `(decision) -> dict` | Generate chat response (non-streaming) |
| `_handle_response_stream()` | `(decision) -> AsyncGenerator[str]` | Generate chat response (streaming) |

**Key Attributes**:
- `client`: LLM client instance
- `registry`: ToolRegistry with auto-discovered tools
- `base_prompt`: Aggregated SOUL + MEMORY
- `routing_prompt`: Dynamic prompt including available tools

---

### `llm/tools/base.py` - Tool Interface

**Purpose**: Abstract base class for all agent tools.

#### Class: `BaseTool`

| Method | Signature | Description |
|--------|-----------|-------------|
| `__init__()` | `(name, description)` | Initialize tool metadata |
| `__call__()` | `(*args, **kwargs) -> Any` | Execute tool (abstract) |
| `validate_input()` | `(*args, **kwargs) -> bool` | Validate parameters before execution |
| `__repr__()` | `() -> str` | Debug representation |
| `__str__()` | `() -> str` | Human-readable description |

**Purpose**: All tools inherit from this to provide a consistent interface.

---

### `llm/tools/registry.py` - Tool Management

**Purpose**: Central registry with auto-discovery of tools.

#### Class: `ToolRegistry`

| Method | Signature | Description |
|--------|-----------|-------------|
| `__init__()` | `(auto_discover?)` | Initialize and optionally auto-discover |
| `_auto_discover()` | `() -> None` | Scan tools/ for BaseTool subclasses |
| `register()` | `(tool: BaseTool)` | Register tool instance |
| `register_factory()` | `(name, factory)` | Register class/callable factory |
| `get()` | `(name) -> BaseTool \| None` | Get tool by name (create from factory if needed) |
| `has()` | `(name) -> bool` | Check if tool exists |
| `list_tools()` | `() -> list[str]` | List all available tool names |
| `get_tool_schemas()` | `() -> list[dict]` | OpenAI-compatible tool schemas |
| `execute()` | `(name, *args, **kwargs) -> Any` | Execute tool by name |
| `clear()` | `() -> None` | Clear all registered tools |

**Auto-Discovery**: Scans `dekomposit/llm/tools/` for modules containing subclasses of `BaseTool` (excluding `BaseTool` itself).

---

### `llm/tools/adaptive_translation.py` - Google Cloud Adaptive MT

**Purpose**: Translate using custom Adaptive MT datasets.

#### Class: `AdaptiveTranslationTool`

| Method | Signature | Description |
|--------|-----------|-------------|
| `__init__()` | `(project_id?, location?, dataset_id?, dataset_name?)` | Initialize with GCP config |
| `__call__()` | `(text, source_lang?, target_lang?, ...) -> dict` | Execute translation |
| `validate_input()` | `(text, project_id, location, dataset_id, dataset_name) -> bool` | Validate parameters |
| `_resolve_dataset_name()` | `(project_id, location, dataset_id, dataset_name) -> str \| None` | Build dataset resource name |
| `_get_access_token()` | `(access_token?, allow_env?) -> str` | Get OAuth token (ADC or gcloud) |

**Key Features**:
- Uses Google Cloud Adaptive MT API
- Supports single text or batch translation
- Automatic token refresh on 401
- Falls back to gcloud CLI if ADC unavailable

---

### `llm/tools/reverso_api.py` - Reverso Context API (Skeleton)

**Purpose**: Placeholder for Reverso Context integration.

#### Class: `ReversoAPI`

| Method | Signature | Description |
|--------|-----------|-------------|
| `__init__()` | `()` | Initialize tool |
| `__call__()` | `(text, source_lang, target_lang, ...) -> dict` | Get translation + examples (NOT IMPLEMENTED) |
| `validate_input()` | `(text, source_lang, target_lang) -> bool` | Validate input |

**Status**: Skeleton - raises `NotImplementedError`.

---

### `llm/utils/language_detection.py` - Language Detection

**Purpose**: Heuristic language detection for en/ru/uk/sk.

#### Function: `detect_language_local()`

| Parameter | Type | Description |
|-----------|------|-------------|
| `text` | str | Input text |

| Returns | Type | Description |
|---------|------|-------------|
| | str \| None | Language code ('en', 'ru', 'uk', 'sk') or None |

**Algorithm**:
- Cyrillic detection → ru/uk based on specific characters
- Slovak diacritics detection
- Latin alphabet → en

---

### `llm/base_prompts/` - Bot Personality

**Files**:

| File | Purpose |
|------|---------|
| `SOUL.md` | Bot personality, tone, teaching approach |
| `MEMORY.md` | Session context and memory management |

**Loading**: Agent reads all `.md` files and aggregates them into the system prompt.

---

## Data Flow

```
User Message
     │
     ▼
┌─────────────────┐
│   Agent.chat()  │
└────────┬────────┘
         │
         ▼
┌──────────────────────┐
│ _decide_action()     │ ◄── Routing prompt (dynamic)
│ (ToolDecision)       │
└────────┬─────────────┘
         │
    ┌────┴────┐
    │         │
    ▼         ▼
"translate" "respond"
    │         │
    ▼         ▼
_handle_   _handle_response()
translation   │
    │         │
    ▼         ▼
ToolRegistry.get()
("adaptive_translation")
    │
    ▼
AdaptiveTranslationTool
(Google Cloud Adaptive MT)
```

---

## Adding a New Tool

1. Create `llm/tools/my_tool.py`:

```python
from dekomposit.llm.tools.base import BaseTool

class MyTool(BaseTool):
    def __init__(self):
        super().__init__(
            name="my_tool",
            description="What this tool does"
        )
    
    async def __call__(self, *args, **kwargs):
        # Implementation
        pass
```

2. Auto-discovery picks it up automatically:

```python
agent = Agent()
print(agent.registry.list_tools())
# ['adaptivetranslationtool', 'reversoapi', 'mytool']
```

---

## Configuration

Environment variables (in `.env`):

| Variable | Default | Description |
|----------|---------|-------------|
| `CURRENT_API_KEY` | GEMINI_API_KEY | API key env var name |
| `LLM_MODEL` | gemini-flash-lite-latest | Model name |
| `LLM_SERVER` | https://generativelanguage.googleapis.com/v1beta/openai/ | API endpoint |
| `LLM_TEMPERATURE` | 1.0 | Sampling temperature |
| `LLM_MAX_TOKENS` | 1024 | Max response tokens |
| `GOOGLE_CLOUD_PROJECT` | - | GCP project for Adaptive MT |
| `ADAPTIVE_MT_LOCATION` | us-central1 | GCP location |
| `ADAPTIVE_MT_DATASET_ID` | - | Default dataset ID |
