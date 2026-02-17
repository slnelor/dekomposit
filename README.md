# dekomposit

> Your personal language teacher.

`dekomposit` is an AI language-teaching agent project (inspired by OpenClaw).

This repository is focused on the **AI Agent only**.
The web platform is intentionally out of scope and will live in a separate repository.

## Why the name?

From the idea: **decompose + it = dekomposit**.

The core learning principle is decomposition: break language into meaningful parts,
understand them, and rebuild fluency through practice.

## What this repo contains

- Async LLM client built on OpenAI SDK (works with OpenAI-compatible endpoints)
- Agent loop with tool-calling support
- Prompt system (`SOUL.md`, `MEMORY.md`, routing, language detection)
- User memory model (topics, learning gaps, style adaptation)
- Translation tooling, including Adaptive MT integration
- Translation output formatting presets

## Current status

This is an active AI-agent core project.

- Implemented: client, agent loop, tool registry, prompt registry, formatting, memory
- Partial: translation tools and language-routing behavior
- Planned next: production Telegram integration, persistence, richer teaching workflows

## Quick start

```bash
python3.12 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

Create `.env` in the project root and set at least:

```env
CURRENT_API_KEY=GEMINI_API_KEY
GEMINI_API_KEY=your_api_key_here
LLM_MODEL=gemini-flash-lite-latest
LLM_SERVER=https://generativelanguage.googleapis.com/v1beta/openai/
LLM_TEMPERATURE=1.0
LLM_MAX_TOKENS=1024
```

For Adaptive MT tool usage, also configure:

```env
GOOGLE_CLOUD_PROJECT=your-project-id
ADAPTIVE_MT_LOCATION=us-central1
ADAPTIVE_MT_DATASET_ID=adaptive-en-ru
```

## Repository map

```text
dekomposit/
├── config.py
└── llm/
    ├── agent.py
    ├── base_client.py
    ├── memory.py
    ├── types.py
    ├── base_prompts/
    ├── prompts/
    ├── tools/
    ├── formatting/
    └── datasets/
```

## Docs

- `docs/ARCHITECTURE.md` - AI-agent architecture and runtime flow
- `docs/PROJECT_ANALYSIS.md` - current project state and practical roadmap
- `docs/tech_requirements.md` - product and technical requirements for the agent

## Note

If you see older mentions of a web platform in historical notes/commits, treat them as legacy context.
The source of truth for this repository is: **AI Agent only**.
