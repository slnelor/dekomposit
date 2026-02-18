# Memory Architecture Concept

## Purpose

Define a memory system that keeps `dekomposit` personalized over long periods without bloating prompt context.

This design is local-first for OSS usage and compatible with a future multi-user product deployment.

## Design Principles

- Keep immutable behavior separate from mutable personalization.
- Use structured storage for stable facts and vector search for episodic recall.
- Retrieve memory on demand; do not inject all history every turn.
- Fail soft when memory backends are unavailable.
- Keep prompt composition deterministic and auditable.

## Memory Layers

### 1) Core prompt layer (immutable)

Source files:

- `dekomposit/llm/base_prompts/SOUL.md`
- base system/routing prompts

Role:

- define assistant identity, tone, and safety/behavior constraints
- never edited by the agent at runtime

### 2) Procedural layer (mutable)

Source:

- `custom_instructions` (agent-editable with validation)

Role:

- user-specific operating preferences and coaching style adjustments
- versioned and rollback-capable
- only mutable prompt component at runtime

### 3) Profile layer (regular DB)

Store type:

- relational database (SQLite/PostgreSQL depending on environment)

Role:

- source of truth for stable user attributes

Example fields:

- proficiency level
- goals
- preferred explanation style
- active learning gaps
- language preferences

### 4) Episodic layer (vector DB)

Store type:

- vector database (local-first in OSS; provider may differ by deployment)

Role:

- semantic recall of memory-worthy events from interactions

Episode examples:

- repeated mistakes and corrections
- explicit preferences stated in conversation
- session outcomes relevant to future coaching

Required metadata:

- `timestamp`
- `importance`
- `confidence`
- `event_type`
- `source_turn_id`

### 5) Knowledge layer (optional vector index)

Role:

- domain/reference knowledge retrieval (`KNOWLEDGE`) separate from personal memory
- merged into prompt only when relevant

## Runtime Flow

1. User message arrives.
2. Load profile + custom instructions.
3. Decide retrieval need (intent/personalization/confidence).
4. Retrieve top-k episodic memories (and optional knowledge snippets).
5. Compose prompt in fixed order:
   - immutable core
   - custom instructions
   - compact profile summary
   - episodic retrieval
   - knowledge retrieval
   - current user message
6. Generate assistant response.
7. Apply post-turn memory write policy:
   - update profile fields when appropriate
   - write episodic events if memory-worthy
   - version custom instruction edits (if any)

## Retrieval Policy

Retrieve memory only when it materially improves response quality.

Common triggers:

- user asks about prior preferences/decisions/history
- personalized correction or lesson adaptation is needed
- confidence is low without prior context

Retrieval controls:

- strict top-k
- score threshold
- dedupe by semantic similarity
- recency weighting (optional)
- token budget cap per section

## Write Policy

Do not persist every turn.

Persist only memory-worthy events, such as:

- durable user preferences
- repeated learning gaps/mistakes
- long-term goals and important updates

Each persisted item should include confidence and provenance metadata.

## Safety and Mutation Rules

- Agent cannot edit `SOUL.md` or immutable system prompts.
- Agent may propose/update only `custom_instructions`.
- Instruction updates must pass validation:
  - no safety/policy overrides
  - no secret leakage
  - bounded size and format
- All instruction edits are versioned and rollbackable.

## OSS vs Product Deployment

### OSS local mode (current target)

- single-tenant local runtime
- local DB + local vector DB
- encryption at rest when available

### Product mode (future)

- multi-tenant isolation
- per-user namespaces and access control
- managed key handling and tenant-aware observability

Schema should still keep `user_id` fields in OSS mode to simplify migration.

## Observability

Track at minimum:

- retrieval hit rate
- average retrieved token volume
- memory write count by type
- fallback/error rate for memory backends
- latency per retrieval stage

## Test Strategy

Minimum coverage for this architecture:

- prompt composition order is deterministic
- retrieval returns relevant snippets under budget
- write policy stores only memory-worthy events
- instruction mutation guardrails block unsafe edits
- system degrades gracefully when vector backend fails

## Implementation Note for `dekomposit`

Current in-memory `UserMemory` should evolve into repository interfaces:

- `ProfileStore`
- `EpisodeStore`
- `InstructionStore`
- `PromptComposer`

This keeps orchestration in `Agent` simple and allows backend replacement without changing core behavior.
