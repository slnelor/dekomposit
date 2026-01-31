# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

**dekomposit** (formerly NovaMova) is a language learning service that helps users gain vocabulary through translation, dialogues, and reading. The project decomposes translations into natural phrase chunks to improve readability and learning outcomes.

## Development Commands

### Environment Setup
```bash
# Activate virtual environment
source .venv/bin/activate  # Linux/Mac
.venv\Scripts\activate     # Windows

# Install dependencies (if needed)
pip install -r requirements.txt  # when requirements.txt exists
```

### Running Tests and Evaluation
```bash
# Run LLM evaluation with BERT scoring
python -m dekomposit.llm.evaluation

# Or run specific evaluation functions:
# - geval_test_llm() - Uses DeepEval GEval metrics for translation quality
# - bert_test_llm() - Uses BERTScore for semantic similarity
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
- Constants for translation formatting (tags, placeholders)

**dekomposit/llm/base_client.py**
- `Client` class: AsyncOpenAI wrapper for LLM interactions
- Handles API calls to OpenAI-compatible endpoints (OpenAI, Gemini via OpenAI API)
- Uses structured output parsing with Pydantic models via `chat.completions.parse()`
- Logs token usage for each request

**dekomposit/llm/types.py**
- `TranslationPhrase`: Basic source-target phrase pair
- `PhraseDetailed`: Extended with definitions, parts of speech, synonyms, antonyms, examples
- `Translation`: Container for list of phrase pairs
- `Language`: Enum of supported languages (EN, ES, FR, DE, IT, PT, PL, UK, SK, RU, CS, ZH, JA)

**dekomposit/llm/prompts.py**
- `TranslationPrompt`: Generates prompts for translation tasks
- Auto-detects translation direction (source ↔ target)
- Corrects grammar, spelling, and punctuation errors in input
- Includes 11 annotated examples showing proper phrase chunking (idioms, phrasal verbs, punctuation handling)

**dekomposit/llm/features.py**
- `translate()`: Main async function to translate text
- Takes text, source_lang, target_lang and returns `Translation` object
- Uses Client + TranslationPrompt for LLM interaction

**dekomposit/llm/evaluation.py**
- Evaluation framework using DeepEval and BERTScore
- `bert_evaluate()`: Semantic similarity scoring
- `geval_test_llm()`: Translation correctness and JSON structure compliance
- Contains test examples in Ukrainian-English pairs

### Translation Philosophy

The translation system decomposes input into **natural phrase chunks** (1+ words):
- Idioms kept together as single units (e.g., "kick the bucket" → "Il est mort")
- Phrasal verbs preserved (e.g., "give up" → "abandonner")
- Punctuation attached to adjacent words, never standalone
- Grammar/spelling errors automatically corrected
- Special characters preserved in position

### Environment Configuration

The `.env` file contains:
- `CURRENT_API_KEY`: Key name to use (e.g., "OPENAI_API_KEY", "GEMINI_API_KEY")
- `LLM_MODEL`: Model identifier (default: "gemini-flash-lite-latest")
- `LLM_SERVER`: API endpoint URL (OpenAI or Gemini with OpenAI compatibility)
- `LLM_TEMPERATURE`: Temperature setting (default: 0.2)
- `LLM_MAX_TOKENS`: Max output tokens (default: 1024)
- API keys for various providers

### Key Design Patterns

1. **Async-First**: All LLM calls use async/await
2. **Structured Output**: Pydantic models enforce response schema via OpenAI's structured output feature
3. **Prompt Engineering**: Few-shot examples with annotations guide model behavior
4. **Error Correction**: Input mistakes auto-corrected in translation
5. **Language Agnostic**: Auto-detects translation direction

## Important Notes

- The project uses OpenAI SDK with custom base URLs to support multiple providers (OpenAI, Gemini)
- Gemini models accessed via OpenAI-compatible endpoint: `https://generativelanguage.googleapis.com/v1beta/openai/`
- All translation outputs must follow strict phrase chunking rules (no standalone punctuation)
- Python 3.14 is the target version
- Backend will eventually be FastAPI with PostgreSQL + SQLAlchemy (not yet implemented)

## Project Status

Early development phase. Core translation feature implemented with evaluation framework. See `docs/tech_requirements.md` for full feature roadmap including:
- Vocabulary storage
- Dialogues generation
- Reading section with inline translation
- Community features
- Multiple learning method

### Better project understanding
If you need more information of project explanation look up
in @/home/mikhail/ForPython/Afono_Wanders/docs/tech_requirements.md

