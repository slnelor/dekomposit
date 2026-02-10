# dekomposit

> **Gain new lexicon -> revise -> repeat.**

A language learning AI agent on Telegram and a web platform. Learn vocabulary through conversational AI coaching, interactive exercises, and immersive reading.

## Why dekomposit?

Traditional language learning focuses on single methods. Dekomposit combines listening, reading, speaking, and writing into one service. The Telegram bot acts as a personal language coach you can talk to anytime, while the web platform provides a richer experience for reading and vocabulary management.

## Platforms

### Telegram AI Agent (primary)
- Conversational language coach available 24/7
- Daily vocabulary packs pushed to your chat
- Interactive dialogue exercises in conversation
- Vocabulary quizzes and streak tracking
- Inline mode for quick translations in any Telegram chat

### Web Platform
- Reading section with inline translation (Trusted Authors library)
- Vocabulary dashboard with filters, search, and export
- Extended learning sessions with progress tracking
- Account management and settings

## Features

### Core
- **Conversational AI Coach** - Personal language learning assistant in Telegram with customizable personality
- **Vocabulary Storage** - Track your learned words with intelligent practice scheduling
- **Interactive Dialogues** - Practice conversations with AI-generated dialogue exercises tailored to your level
- **Reading Section** (web) - Community-powered reading library with inline translation
- **Learning Method** - Structured practice: memorize -> read/listen -> write -> repeat -> test
- **Daily Vocabulary Packs** - 10-20 new words every day based on current events or your learning gaps

### Premium (Dekomposer Pack)
- 1,000 requests to paid LLM methods
- Access to Episodes
- Interactive dialogues with advanced tasks
- 10,000 symbol input limit (vs. 1,000 free)
- High-quality audio (TTS)
- More/longer examples

## Project Status

**Early Development** - Core LLM client and CLI implemented.

### Completed
- AsyncOpenAI client wrapper with structured output
- Bot personality definition (SOUL.md)
- Multi-provider LLM support (OpenAI, Gemini)

### In Progress
- Telegram bot (aiogram)
- FastAPI backend
- PostgreSQL + SQLAlchemy
- Prompt engineering for language learning

### Planned
- User authentication & profiles
- Vocabulary storage and tracking
- Translation with phrase decomposition
- Interactive dialogues
- Reading section with Trusted Authors
- Daily word packs with push notifications
- Episodes
- Anki/Quizlet export

## Tech Stack

- **Language**: Python 3.14
- **Telegram Bot**: aiogram (async)
- **Web Backend**: FastAPI
- **Database**: PostgreSQL + SQLAlchemy
- **LLM**: OpenAI SDK (Gemini, ChatGPT via OpenAI-compatible API)
- **APIs**: ReversoAPI (fallback)
- **Web Frontend**: HTML, CSS, JavaScript (htmx)

## Architecture

```
dekomposit/
├── config.py              # Environment & LLM settings
└── llm/
    ├── base_client.py     # AsyncOpenAI wrapper
    └── prompting/
        └── SOUL.md        # Bot personality definition
```

## Setup

```bash
# Clone repository
git clone <repo-url>
cd Afono_Wanders

# Create virtual environment
python3.14 -m venv .venv
source .venv/bin/activate  # Linux/Mac
# .venv\Scripts\activate   # Windows

# Install dependencies
pip install -r requirements.txt

# Configure environment
cp .env.example .env
# Edit .env with your API keys and Telegram bot token
```

## Documentation

- [Technical Requirements](docs/tech_requirements.md) - Full feature specifications
- [Agent Instructions](AGENTS.md) - Guidelines for AI coding assistants
- [Claude Context](CLAUDE.md) - Project context for Claude Code

## License

[Add your license here]
