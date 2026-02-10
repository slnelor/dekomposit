# AGENTS.md - Navigation Guide for AI Agents

_This file explains the prompting system structure and how to use it._

## Overview

This directory contains the core personality and behavior definitions for the language learning AI agent. These files work together to create a consistent, personalized coaching experience.

## File Structure

### 🎭 SOUL.md
**Purpose:** Defines the core personality, communication style, and teaching approach.

**What's inside:**
- Core identity (who you are)
- Communication style rules (direct, opinionated, constructive)
- Banned phrases (no corporate speak)
- Teaching methodology (Socratic Method)
- Tone guidelines (humor, calling out mistakes, swearing)
- Examples of good vs bad responses

**Customization:** Contains `{custom_personality['SOUL.md']}` placeholder for user-specific personality traits.

**When to use:** This is your primary behavioral guide. Read it at initialization to understand how to communicate.

---

### 🧠 MEMORY.md
**Purpose:** Stores conversation history and context from previous interactions.

**What's inside:**
- Memory from past conversations
- User preferences and learning patterns
- Context that persists across sessions

**Customization:** Contains `{custom_personality['MEMORY.md']}` placeholder for user-specific memories.

**When to use:** Reference this to maintain continuity and personalization across conversations.

---

### 🛠️ TOOLS.md
**Purpose:** Documentation about available tools and external resources.

**What's inside:**
- Available tools and APIs
- External documentation references
- Integration guidelines

**When to use:** Reference this when you need to know what tools are available or how to access external resources.

---

### 📋 AGENTS.md (this file)
**Purpose:** Navigation and documentation for the AI agent system.

**What's inside:**
- File structure explanation
- How files work together
- Usage guidelines

**When to use:** When you need to understand the prompting system architecture.

---

## How It Works Together

```
┌─────────────┐
│   SOUL.md   │  ← Load first: Get your personality
└──────┬──────┘
       │
       ▼
┌─────────────┐
│  MEMORY.md  │  ← Load second: Get conversation context
└──────┬──────┘
       │
       ▼
┌─────────────┐
│  TOOLS.md   │  ← Load third: Know your available tools
└──────┬──────┘
       │
       ▼
┌─────────────┐
│ Start Chat  │  ← Now interact with user
└─────────────┘
```

## Custom Personality System

Both SOUL.md and MEMORY.md contain placeholders in the format:
```
{custom_personality['FILENAME.md']}
```

**Purpose:** These placeholders allow per-user customization of the agent.

**How it works:**
1. Base personality and memory are defined in the files
2. When an agent is instantiated for a specific user, the `custom_personality` dict is populated
3. User-specific traits/memories are injected via these placeholders
4. Result: Same base agent + personalized modifications per user

**Example use case:**
- User A prefers formal language → inject formal tone in `custom_personality['SOUL.md']`
- User B is learning Spanish → inject Spanish context in `custom_personality['MEMORY.md']`

## Guidelines for AI Agents

### On Initialization:
1. **Load SOUL.md first** - Understand your personality and communication rules
2. **Load MEMORY.md second** - Get context from previous conversations
3. **Load TOOLS.md third** - Know what tools and resources are available
4. **Apply all** - Combine personality, memory, and tools for consistent behavior

### During Conversation:
1. **Follow SOUL.md rules** - Stay in character, use the defined communication style
2. **Reference MEMORY.md** - Use past context to provide continuity
3. **Be adaptive** - Custom personality traits override base traits when present

### When in Doubt:
- SOUL.md defines WHO you are
- MEMORY.md defines WHAT you know about this user
- TOOLS.md defines WHAT you can do
- Together they create a personalized, capable coaching experience

## File Maintenance

**SOUL.md:**
- Core personality is stable (rarely changes)
- Custom personality section updated per-user needs
- Examples should be expanded as edge cases are discovered

**MEMORY.md:**
- Grows over time with conversation history
- Should be pruned periodically to avoid context bloat
- Important patterns/preferences should be summarized

**TOOLS.md:**
- Updated when new tools/APIs are added or removed
- Should document integration patterns and usage examples
- Keep tool descriptions current with actual capabilities

**AGENTS.md:**
- Updated when new files are added to the system
- Keep this as the single source of truth for navigation

---

## Quick Reference

| File | Purpose | When to Load | Frequency |
|------|---------|--------------|-----------|
| SOUL.md | Personality & behavior | Initialization | Once per session |
| MEMORY.md | Conversation context | Initialization | Once per session |
| TOOLS.md | Available tools & APIs | Initialization | Once per session |
| AGENTS.md | System documentation | As needed | Reference only |

---

_Last updated: 2026-02-10_
