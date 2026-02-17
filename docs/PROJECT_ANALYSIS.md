# dekomposit Project Analysis

## One-line definition

`dekomposit` is an AI-agent core for a personal language teacher (inspired by OpenClaw), with decomposition-first learning logic.

## Product direction (confirmed)

- This repository is **AI Agent only**.
- Web platform work is intentionally excluded and should be developed in a separate repository.
- The name idea is: **decompose + it = dekomposit**.

## Current implementation maturity

Overall maturity: **early-to-mid prototype of the core runtime**.

### Strong parts

- Clean async LLM wrapper with structured output support
- Agentic loop with tool-calling and iterative observation
- File-based prompt architecture (`SOUL`, `MEMORY`, routing, detection)
- Extensible tool registry with auto-discovery
- Translation output formatting system
- Basic user memory model and adaptive prompt rebuilding

### Partial parts

- `MemoryTool` exists but needs explicit agent wiring for reliable runtime use
- `stream_chat()` path still follows older decision-based flow vs full tool-loop flow
- Some behavior paths coexist (new loop + legacy helper methods), needs consolidation

### Not implemented / placeholder

- Reverso integration (`reverso_api.py`) is skeleton only
- persistent memory storage (DB-backed profile/history)
- production transport layer (Telegram runtime integration in this repo)
- guardrails and validation policy for tool execution at scale

## Architectural observations

- The codebase is modular and ready for feature growth without major rewrites.
- Prompt files are a good lever for rapid behavior iteration.
- Tool abstractions are appropriate for adding teacher capabilities (quiz generation, targeted drills, correction tools).
- Memory signals are currently ephemeral; persistence is the biggest functional gap for a true personal teacher experience.

## Risks and constraints

- Dependency on external APIs (LLM provider, Google Adaptive MT) requires robust failure handling and fallback strategy.
- In-memory state limits long-term personalization between sessions.
- Mixed old/new control flows can increase maintenance burden if not unified.

## Recommended next milestones

1. **Unify execution path**
   - make `chat()` and `stream_chat()` both rely on one primary orchestration path
   - remove stale decision-only branches where redundant

2. **Stabilize memory model**
   - add persistence interface and storage-backed implementation
   - define retention and compaction for long user histories

3. **Harden tools**
   - finalize tool naming conventions and schema consistency
   - improve tool input validation and error normalization

4. **Ship Telegram adapter**
   - add production-ready integration layer that wraps the current agent core
   - keep transport concerns separated from language-teaching logic

5. **Learning-specific capabilities**
   - implement correction/exercise tools and progress tracking signals
   - add explicit decomposition outputs (phrase chunks, definitions, examples)

## Conclusion

The project already has a solid AI-agent backbone.
To become a true personal language teacher, the most important next steps are memory persistence, runtime unification, and production transport integration.
