# dekomposit Architecture (AI Agent Only)

## Scope

This repository contains the language-teaching **AI Agent core**.

- In scope: LLM client, agent orchestration, prompts, memory, tools, formatting
- Out of scope: web platform, web backend, web UI

## High-level design

```text
User text
   |
   v
Agent.handle_message()
   |
   v
Agent.execute_tools()  <-- iterative tool loop (LLM can call tools)
   |
   +--> ToolRegistry.get_tool_schemas()
   +--> Client.request_with_tools(...)
   +--> execute tool calls (if any)
   +--> append tool results back into message history
   '--> final assistant response
```

The agent is async-first and centered around a loop where the model can observe tool results and decide next actions.

## Main modules

### `dekomposit/config.py`

Loads environment variables and defines LLM defaults:

- default model and server
- selected API key name (`CURRENT_API_KEY`)
- generation config (`temperature`, `max_tokens`)

### `dekomposit/llm/base_client.py`

Async wrapper around `AsyncOpenAI`:

- `request()` for structured responses (`chat.completions.parse`)
- `request_with_tools()` for function/tool calling
- `stream()` for streaming responses
- request token-usage logging

### `dekomposit/llm/agent.py`

Core orchestrator:

- initializes client, tool registry, format registry, prompt registry, user memory
- loads and composes base prompt (`SOUL.md` + `MEMORY.md`)
- runs tool loop in `execute_tools()`
- exposes `handle_message()`, `chat()`, and `stream_chat()`

### `dekomposit/llm/memory.py`

In-memory user profile model:

- learning gaps
- preferred topics
- speaking/teaching style
- conversation history and mistake counters

### `dekomposit/llm/prompts/`

Prompt files discovered by `PromptRegistry`:

- `routing.md`: decide translate vs respond
- `detection.md`: detect language code

### `dekomposit/llm/base_prompts/`

Persistent personality and context templates:

- `SOUL.md`: agent voice and teaching behavior
- `MEMORY.md`: placeholders for learned user profile

### `dekomposit/llm/tools/`

Tool interface and concrete tool implementations:

- `BaseTool`: common async callable interface + JSON schema
- `ToolRegistry`: auto-discovers tools and exposes schemas
- `AdaptiveTranslationTool`: Google Cloud Adaptive MT translation
- `MemoryTool`: allows model-driven memory updates
- `ReversoAPI`: skeleton placeholder (not implemented)

### `dekomposit/llm/formatting/`

Formatting presets loaded from JSON:

- active preset selection
- template rendering for normalized translation output

## Runtime flow details

1. `Agent.handle_message(text)` adds user text to memory.
2. `execute_tools()` sends system+user messages to model with available tool schemas.
3. If model emits tool calls, agent executes each tool and appends tool outputs as `role=tool` messages.
4. Loop repeats until model emits a final text response or max-iteration limit is reached.
5. Agent stores final assistant text in memory and rebuilds system prompt context.

## Key design choices

- **Async-first**: all external I/O and model calls are async.
- **Provider-flexible**: OpenAI-compatible API surface (Gemini/OpenAI/custom).
- **Prompt-as-files**: behavior changes without code edits.
- **Tool auto-discovery**: extensible capabilities via `tools/`.
- **Structured output**: Pydantic models for reliable routing and parsing.

## Planned architectural evolution

- durable memory persistence (database-backed)
- production Telegram adapter around current agent core
- deeper teaching tools (exercise generation, correction loops, progress scoring)
- stronger tool safety/validation and observability
