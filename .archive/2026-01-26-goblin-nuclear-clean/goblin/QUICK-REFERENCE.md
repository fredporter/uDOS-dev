# Goblin Dev Server Quick Reference

**Port:** 8767 (localhost only)  
**Version:** v0.1.0.0 (unstable)  
**Purpose:** Experimental development features

---

## 🚀 Quick Start

```bash
# 1. Configure (first time only)
cp dev/goblin/config/goblin.example.json dev/goblin/config/goblin.json
# Edit goblin.json with your API keys

# 2. Launch server
./bin/Launch-Goblin-Dev.command

# 3. Test endpoints
curl http://localhost:8767/health
```

---

## 📡 API Endpoints

### Notion Sync

```bash
# Webhook (incoming from Notion)
POST http://localhost:8767/api/v0/notion/webhook

# Get sync status
GET http://localhost:8767/api/v0/notion/sync/status

# Get mappings
GET http://localhost:8767/api/v0/notion/maps

# Publish to Notion
POST http://localhost:8767/api/v0/notion/publish
```

### TS Markdown Runtime

```bash
# Parse markdown
POST http://localhost:8767/api/v0/runtime/parse
Body: {"markdown": "..."}

# Execute block
POST http://localhost:8767/api/v0/runtime/execute
Body: {"block_type": "state", "content": "...", "state": {...}}

# Get state
GET http://localhost:8767/api/v0/runtime/state

# Set state
PUT http://localhost:8767/api/v0/runtime/state
Body: {"state": {...}}
```

### Task Scheduler

```bash
# Schedule task
POST http://localhost:8767/api/v0/tasks/schedule
Body: {
  "name": "Research Topic X",
  "type": "research",
  "cadence": "once",
  "priority": "high"
}

# View queue
GET http://localhost:8767/api/v0/tasks/queue

# Execution history
GET http://localhost:8767/api/v0/tasks/runs
```

### Binder Compiler

```bash
# Compile binder
POST http://localhost:8767/api/v0/binder/compile
Body: {
  "binder_id": "my-binder",
  "formats": ["markdown", "pdf", "json"]
}

# Get chapters
GET http://localhost:8767/api/v0/binder/chapters?binder_id=my-binder
```

---

## ⚙️ Configuration

**File:** `dev/goblin/config/goblin.json` (gitignored)

**Example:**

```json
{
  "server": {
    "host": "127.0.0.1",
    "port": 8767,
    "debug": true
  },
  "notion": {
    "webhook_secret_keychain_id": "notion-webhook-secret",
    "api_token_keychain_id": "notion-api-token",
    "publish_mode": "on_demand"
  },
  "runtime": {
    "max_state_size_bytes": 1048576,
    "execution_timeout_ms": 5000
  },
  "scheduler": {
    "organic_mode": true,
    "daily_quota_calls": 200
  },
  "providers": {
    "ollama": {
      "base_url": "http://localhost:11434"
    },
    "openrouter": {
      "api_key_keychain_id": "openrouter-api-key"
    }
  }
}
```

---

## 🧪 Runtime Block Examples

### State Block

```markdown
\`\`\`state
$name = "Fred"
$coins = 10
$has_key = false
\`\`\`
```

### Set Block

```markdown
\`\`\`set
set $coins 50
inc $coins 10
dec $coins 5
toggle $has_key
\`\`\`
```

### Form Block

```markdown
\`\`\`form
fields:

- name: username
  type: text
  required: true
- name: email
  type: email
  required: true
  \`\`\`
```

### Panel Block (with interpolation)

```markdown
\`\`\`panel

# Welcome, $name!

You have $coins coins.
Key status: $has_key
\`\`\`
```

---

## 🔄 Organic Cron Phases

1. **Plant** — Expand project into tasks
2. **Sprout** — Execute initial drafts
3. **Prune** — Remove low-quality outputs
4. **Trellis** — Guide refinement passes
5. **Harvest** — Collect completed work
6. **Compost** — Extract learnings

---

## 📋 Promotion Checklist

When feature is ready for production:

- [ ] Tests (unit + integration)
- [ ] Documentation (user-facing + API)
- [ ] Version API (`/api/v0/*` → `/api/v1/*`)
- [ ] Security review
- [ ] Performance testing
- [ ] Production config
- [ ] Monitoring setup
- [ ] Deploy to Wizard or new Extension
- [ ] Migration plan
- [ ] Deprecate in Goblin

---

## 🆚 Wizard vs Goblin

| Aspect   | Wizard (8765)      | Goblin (8767)  |
| -------- | ------------------ | -------------- |
| Status   | Production stable  | Experimental   |
| API      | `/api/v1/*`        | `/api/v0/*`    |
| Access   | Public (with auth) | Localhost only |
| Breaking | Never              | Expected       |
| Config   | Versioned          | Gitignored     |

---

## 📚 Documentation

- **Architecture:** `/dev/goblin/README.md`
- **AGENTS.md:** Sections 3.3.1-3.3.2
- **Roadmap:** `/docs/roadmap.md`
- **Step 1 Summary:** `/docs/devlog/2026-01-15-step-1-complete.md`

---

_Last Updated: 2026-01-15_  
_Goblin Dev Server v0.1.0.0_
