# dekomposit

> **Gain new lexicon → revise → repeat.**

A language learning service with an unusual approach: learn vocabulary through multiple methods—from handwriting to short animations and interactive dialogues.

## 🎯 Why dekomposit?

Traditional language learning focuses on single methods. Dekomposit combines listening, reading, speaking, and writing into one platform, making vocabulary acquisition more effective through diverse, reinforcing experiences.

## ✨ Features

### Core Features
- **🔤 Smart Translation** - Decomposes translations into natural phrase chunks (idioms, phrasal verbs preserved)
  - Auto-corrects grammar/spelling mistakes
  - Provides definitions, examples, and pixel-art illustrations
  - Multiple translation methods (ReversoContext, ChatGPT, etc.)
  
- **📚 Vocabulary Storage** - Personal vocabulary tracker with intelligent example generation based on your level

- **💬 Dialogues** - AI-generated conversational practice tailored to your vocabulary and proficiency
  - Interactive tasks: correct mistakes, fill gaps, chat with AI
  - Sentence-by-sentence translation

- **📖 Reading Section** - Community-powered reading library
  - Books, articles, stories from Trusted Authors
  - Inline translation with hover/click
  - Reading progress tracking

- **🎓 Learning Method** - Structured practice system
  1. Memorize units with translations/images
  2. Read/listen to texts with those units
  3. Write your own examples
  4. Take optional challenges

- **📦 Today's Pack of Memorizing** - Daily 10-20 new words based on current events or your learning gaps

### Premium (Dekomposer Pack)
- 1,000 requests to paid LLM methods
- Access to Episodes (short movies)
- Interactive dialogues with advanced tasks
- 10,000 symbol input limit (vs. 1,000 free)
- High-quality audio (TTS)
- More/longer examples

## 🚀 Project Status

**Early Development** - Core translation feature implemented (0/17 features complete)

### Completed ✅
- LLM-powered phrase-by-phrase translation
- Multi-language support (13 languages)
- Pydantic-based structured output
- Evaluation framework (BERTScore + DeepEval)

### In Progress 🚧
- FastAPI backend
- PostgreSQL + SQLAlchemy
- User authentication & profiles
- Vocabulary storage

### Planned 📋
- Reading section with Trusted Authors
- Interactive dialogues
- Episodes (short movies)
- Daily word packs
- Anki/Quizlet export
- Browser extension
- Mobile app & Telegram bot

## 🛠️ Tech Stack

- **Backend**: FastAPI
- **Database**: PostgreSQL + SQLAlchemy
- **LLM**: OpenAI SDK (Gemini, ChatGPT via OpenAI API)
- **APIs**: ReversoAPI (fallback)
- **Frontend**: HTML, CSS, JavaScript (htmx planned)
- **Language**: Python 3.14
- **Evaluation**: DeepEval, BERTScore

## 🏗️ Architecture

```
dekomposit/
├── config.py           # Environment & LLM settings
└── llm/
    ├── base_client.py  # AsyncOpenAI wrapper
    ├── features.py     # translate() and future features
    ├── prompts.py      # Translation prompt engineering
    ├── types.py        # Pydantic models (Translation, Language)
    └── evaluation.py   # Quality testing suite
```

## 🔧 Setup

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
# Edit .env with your API keys
```

## 📊 Development

```bash
# Run translation evaluation
python -m dekomposit.llm.evaluation

# Test translation in Python
from dekomposit.llm.features import translate
import asyncio

result = asyncio.run(translate(
    "Привіт, світ!",
    source_lang="ukrainian",
    target_lang="english"
))
print(result)
```

## 📄 Documentation

- [Technical Requirements](docs/tech_requirements.md) - Full feature specifications
- [Agent Instructions](AGENTS.md) - Guidelines for AI coding assistants
- [Claude Context](CLAUDE.md) - Project context for Claude Code

## 🤝 Contributing

Contributions welcome! See [docs/tech_requirements.md](docs/tech_requirements.md) for feature roadmap.

## 📜 License

[Add your license here]

---

**Note**: Project is in active development. Features and documentation are subject to change.