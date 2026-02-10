# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

**dekomposit** (formerly NovaMova) is a language learning service with two interfaces:
1. **Telegram AI agent** (primary) - Personal language coach in Telegram
2. **Web platform** - Extended features like reading, vocabulary management

The project uses LLMs to provide conversational language learning experiences.

## Dual Platform Architecture

### Telegram Bot
- Primary user interface
- Built with aiogram (async Telegram bot framework)
- Conversational AI agent (personality defined in `dekomposit/llm/prompting/SOUL.md`)
- Commands: /start, /translate, /vocab, /daily, /level, /settings, /help
- Inline mode support
- Shares backend services with web platform

### Web Platform
- Secondary interface for richer experiences
- FastAPI backend
- HTML/CSS/JS frontend (htmx)
- Features: reading section, vocabulary dashboard, account management
- Shares service layer with Telegram bot

## Development Commands

### Environment Setup
```bash
# Activate virtual environment
source .venv/bin/activate  # Linux/Mac
.venv\Scripts\activate     # Windows

# Install dependencies (if needed)
pip install -r requirements.txt  # when requirements.txt exists
```

### Development
```bash
# Python 3.14 is used for this project

# Check code with static analysis tools (if configured)
mypy dekomposit/
ruff check dekomposit/
```

## Architecture

### Core Components

**dekomposit/config.py**
- Configuration management using `python-dotenv`
- LLM settings (model, server, API keys, temperature, max_tokens)
- Constants for application configuration

**dekomposit/llm/base_client.py**
- `Client` class: AsyncOpenAI wrapper for LLM interactions
- Handles API calls to OpenAI-compatible endpoints (OpenAI, Gemini via OpenAI API)
- Uses structured output parsing with Pydantic models via `chat.completions.parse()`
- Logs token usage for each request

**dekomposit/llm/prompting/SOUL.md**
- Defines the Telegram bot's personality and behavior
- "You are a personal coacher who helps me learn languages."
- This file guides the AI agent's conversational tone and teaching approach

### Environment Configuration

The `.env` file contains:
- `CURRENT_API_KEY`: Key name to use (e.g., "OPENAI_API_KEY", "GEMINI_API_KEY")
- `LLM_MODEL`: Model identifier (default: "gemini-flash-lite-latest")
- `LLM_SERVER`: API endpoint URL (OpenAI or Gemini with OpenAI compatibility)
- `LLM_TEMPERATURE`: Temperature setting (default: 0.2)
- `LLM_MAX_TOKENS`: Max output tokens (default: 1024)
- `TELEGRAM_BOT_TOKEN`: Bot token from @BotFather
- API keys for various providers

### Key Design Patterns

1. **Async-First**: All LLM calls and bot handlers use async/await
2. **Structured Output**: Pydantic models enforce response schema via OpenAI's structured output feature
3. **Conversational AI**: Bot acts as a personal language coach with personality
4. **Shared Services**: Telegram bot and web platform share the same backend logic

## Important Notes

- The project uses OpenAI SDK with custom base URLs to support multiple providers (OpenAI, Gemini)
- Gemini models accessed via OpenAI-compatible endpoint: `https://generativelanguage.googleapis.com/v1beta/openai/`
- Python 3.14 is the target version
- Telegram bot is built with aiogram (async framework)
- Backend uses FastAPI with PostgreSQL + SQLAlchemy (not yet fully implemented)

## Project Status

Early development phase. Core LLM client and CLI implemented.

**Completed:**
- AsyncOpenAI client wrapper
- Bot personality definition

**In Progress:**
- Telegram bot implementation (aiogram)
- Backend API (FastAPI)
- Database layer (PostgreSQL + SQLAlchemy)
- Prompt engineering for language learning

**Planned:**
See `docs/tech_requirements.md` for full feature roadmap including:
- Translation with phrase decomposition
- Vocabulary storage and tracking
- Interactive dialogues (Telegram chat + web UI)
- Reading section with inline translation (web only)
- Daily vocabulary packs with push notifications (Telegram)
- Community features (Trusted Authors)
- Premium tier (Dekomposer Pack)

### Better Project Understanding
For detailed feature specifications and platform distribution (Telegram vs Web), see:
- `docs/tech_requirements.md` - Complete technical requirements
- `dekomposit/llm/prompting/SOUL.md` - Bot personality definition
