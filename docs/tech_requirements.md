# dekomposit Technical Requirements

## Product statement

`dekomposit` is a personal AI language teacher (inspired by OpenClaw).

This repository defines and implements the **AI Agent core only**.
Web-platform requirements are out of scope for this codebase.

## Naming rationale

Why `dekomposit`?

- decomposition is the learning strategy
- "decompose + it" -> `dekomposit`

## Core goals

The agent should:

1. Teach language through conversation, not just static translation.
2. Decompose user input into understandable learning units.
3. Adapt over time to user mistakes, preferences, and interests.
4. Use tools when appropriate (translation, memory, future drill tools).
5. Keep responses structured enough for downstream clients (e.g., Telegram).

## Functional requirements

### 1) Conversational teaching mode

- The agent must provide natural coaching dialogue.
- It should ask follow-up questions and suggest short practice tasks.
- Tone and depth must adapt to user style (short vs detailed, chill vs focused).

### 2) Translation mode

- The agent must detect when user asks for translation.
- Supported language codes currently: `en`, `ru`, `uk`, `sk`.
- If source language is missing, agent should detect it.
- Translation output should use a stable, parseable format preset.

### 3) Decomposition-first output

For translation-oriented interactions, target output structure should evolve toward:

- translated result
- decomposition into meaningful chunks (phrase-first, not random tokens)
- short definitions/glosses for key chunks
- context examples when useful

Note: current implementation provides the formatted translation core; richer decomposition layers are planned.

### 4) User memory and personalization

- Track conversation history.
- Track free-form memory notes selected by the agent.
- Rebuild system prompt context from memory state.

### 5) Tool-enabled agent loop

- The model must be able to call tools through OpenAI-style function calling.
- Tool results must be injected back into conversation state for iterative reasoning.
- Loop stops on final response or iteration limit.

## Non-functional requirements

### Architecture

- Python 3.12+
- async-first design
- modular components: client, agent, registry, tools, prompts, memory, formatting

### Reliability

- log token usage per LLM request
- handle tool errors without crashing the full interaction
- return safe fallback message when processing fails

### Extensibility

- tools auto-discovered from `dekomposit/llm/tools/`
- prompts loaded from markdown files
- formatting presets loaded from JSON

### Portability

- support OpenAI-compatible endpoints (OpenAI, Gemini-compatible gateway, others)

## Environment requirements

Minimum expected variables:

- `CURRENT_API_KEY`
- provider key named by `CURRENT_API_KEY` (e.g., `GEMINI_API_KEY`)
- `CURRENT_LLM`
- `CURRENT_PROVIDER`
- `LLM_TEMPERATURE`
- `LLM_MAX_TOKENS`

Adaptive MT translation requires:

- `GOOGLE_CLOUD_PROJECT`
- `ADAPTIVE_MT_LOCATION` (default `us-central1`)
- `ADAPTIVE_MT_DATASET_ID` or full dataset name
- authentication via ADC or `GOOGLE_OAUTH_ACCESS_TOKEN`

## Delivery boundaries

In this repository:

- AI-agent runtime logic
- prompts and memory behavior
- language tooling and formatting

Not in this repository:

- web backend/frontend
- web user accounts and dashboards
- web reading/vocabulary UI

## Acceptance criteria for current phase

1. Agent can receive text and produce either:
   - direct conversational response, or
   - formatted translation response.
2. Agent can execute at least one working production tool (`adaptive_translation`).
3. Agent keeps in-session memory and adapts prompt context.
4. Tool-calling loop supports multi-step tool interactions.
5. Documentation consistently states AI-agent-only scope.
