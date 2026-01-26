---
id: ai-system
provider: all
version: 1.0.0
created: 2026-01-06
author: uDOS Dev Mode
tags: [ai, system, prompts, config]
---

# uDOS AI System - Unified Prompts

## Overview

This document defines the unified AI prompt system for uDOS, supporting
multiple AI providers (Gemini, Mistral) across TUI and Tauri interfaces.

## Provider Configuration

| Provider | Model | Free Tier | Use Case |
|----------|-------|-----------|----------|
| Gemini | gemini-2.0-flash | ✅ | Image gen, text, Tauri |
| Mistral | open-mistral-nemo | ✅ | Code fix, TUI commands |

## Prompt Files

| File | Provider | Purpose |
|------|----------|---------|
| [vibe-cli.md](vibe-cli.md) | Mistral | TUI dev commands, OK FIX |
| [gemini-image.md](gemini-image.md) | Gemini | Image generation styles |
| [okfix.md](okfix.md) | Mistral | Code analysis prompts |

## API Keys Configuration

Location: `wizard/config/ai_keys.json`

```json
{
  "GEMINI_API_KEY": "your-gemini-key",
  "MISTRAL_API_KEY": "your-mistral-key"
}
```

Or via environment variables:

```bash
export GEMINI_API_KEY="your-gemini-key"
export MISTRAL_API_KEY="your-mistral-key"
```

---

## Architecture

### TUI Flow

```
User Input
    ↓
SmartPrompt Parser
    ↓
uDOS_commands.py (Router)
    ↓
OkFixHandler (Mistral)
    ↓
DevstralClient → Mistral API
    ↓
Formatted Output (Vibe Style)
```

### Tauri Flow

```
SketchPad/AIPanel
    ↓
ai.ts (Frontend Service)
    ↓
API Server (/ai/generate)
    ↓
GeminiClient → Gemini API
    ↓
JSON Response (SVG/Image)
```

---

## Logging Integration

### Log Categories for AI

| Category | File Pattern | Purpose |
|----------|--------------|---------|
| `command-okfix` | command-okfix-*.log | OK FIX operations |
| `api-ai` | api-ai-*.log | AI API requests |
| `system-ai` | system-ai-*.log | AI system events |

### Context Injection

AI prompts can include log context:

```python
# Read recent logs for context
recent_errors = read_log('error', lines=20)
recent_commands = read_log('session-commands', lines=10)

# Inject into prompt
prompt = f"""
Recent errors:
{recent_errors}

Recent commands:
{recent_commands}

User question: {user_input}
"""
```

---

## Prompt Template Format

All prompts use YAML frontmatter + markdown body:

```yaml
---
id: prompt-name
provider: gemini|mistral|all
model: specific-model (optional)
version: 1.0.0
created: YYYY-MM-DD
author: author-name
tags: [tag1, tag2]
---

# Prompt Title

## System Prompt
The main system prompt text...

## Variables
- {{variable1}}: Description
- {{variable2}}: Description

## Examples
...
```

---

## Variable Substitution

Common variables:

| Variable | Description |
|----------|-------------|
| `{{code}}` | Source code to analyze |
| `{{language}}` | Programming language |
| `{{file_path}}` | Path to file |
| `{{error}}` | Error message |
| `{{logs}}` | Log content |
| `{{context}}` | Additional context |
| `{{style}}` | Image style name |
| `{{input}}` | User input text |

---

## Security Notes

1. **Never include API keys in prompts**
2. **Sanitize user input before injection**
3. **Log prompts without sensitive data**
4. **Realm A (device mesh) = local AI only (future)**
5. **Realm B (Wizard) = cloud AI allowed**

---

## Extending Prompts

To add a new prompt:

1. Create `core/data/prompts/ai/new-prompt.md`
2. Use YAML frontmatter format
3. Register in prompt loader (future)
4. Test with both TUI and Tauri

---

## Future: Prompt API

Planned API endpoint for Typo access:

```
GET /api/prompts           - List all prompts
GET /api/prompts/:id       - Get specific prompt
POST /api/prompts/:id/run  - Execute prompt
PUT /api/prompts/:id       - Update prompt (user workspace)
```

---

*Part of uDOS Alpha v1.0.2.0+*
