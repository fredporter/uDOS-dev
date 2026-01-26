# Goblin Dev Server

**Status:** Development v0.1.0.0 (experimental, unstable)  
**Port:** 8767  
**Scope:** Local development only (localhost)

---

## Purpose

Goblin is the **experimental development server** for uDOS. Features are built here first, then promoted to:

- `/core/` — Core runtime
- `/extensions/` — Public extensions
- `/wizard/` — Production server

Goblin is **intentionally unstable**. Breaking changes are expected and encouraged.

---

## Goblin vs Wizard

| Aspect         | Wizard Server                            | Goblin Dev Server                             |
| -------------- | ---------------------------------------- | --------------------------------------------- |
| **Port**       | 8765                                     | 8767                                          |
| **Status**     | Production v1.1.0.0                      | Development v0.1.0.0                          |
| **Stability**  | Stable, frozen                           | Unstable, experimental                        |
| **Access**     | Public (auth required)                   | Local-only (localhost)                        |
| **Config**     | `/wizard/config/wizard.json` (committed) | `/dev/goblin/config/goblin.json` (gitignored) |
| **Purpose**    | Always-on services                       | Feature development                           |
| **API Prefix** | `/api/v1/*`                              | `/api/v0/*`                                   |

---

## Features (Experimental)

### Notion Sync

- Webhook handlers
- SQLite mapping tables
- Publish mode + limited live sync
- Conflict resolution

### TS Markdown Runtime

- Parse runtime blocks (`state`, `set`, `form`, `if/else`, `nav`)
- Execute with sandboxed state
- SQLite data binding
- Variable interpolation

### Task Scheduler

- Organic cron model (Plant → Sprout → Prune → Trellis → Harvest → Compost)
- Project/mission management
- Provider rotation (Ollama → OpenRouter escalation)
- Quota-aware pacing

### Binder Compiler

- Multi-chapter generation
- Format exports (Markdown, PDF, JSON)
- Knowledge synthesis

---

## Quick Start — Move 1 (Notion Integration)

**Entry Points:**

1. **[Move 1 Quick Start](./MOVE-1-QUICK-START.md)** — Setup & implementation phases
2. **[Block Mapper Implementation](./BLOCK-MAPPER-IMPLEMENTATION.md)** — Parse markdown ↔ Notion blocks
3. **[Notion-Compatible Block Spec](../../docs/specs/notion-compatible-blocks.md)** — Design

**Setup:**

1. Create Notion Internal Integration at https://www.notion.so/my-integrations
2. Grant integration page access (Read/Update/Insert/Delete)
3. Configure `dev/goblin/config/goblin.json` with API key + webhook secret
4. Launch Goblin server (see below)
5. Implement `BlockMapper` (Phase A)

**Launch Goblin:**

```bash
cd ~/uDOS
source .venv/bin/activate
python dev/goblin/goblin_server.py
# → Server running on http://localhost:8767
```

Or use launcher:

```bash
bin/Launch-Goblin-Dev.command
```

---

## Architecture

```
/dev/goblin/
  goblin_server.py          # Main server (port 8767)
  README.md                 # This file
  config/
    goblin.json             # Local config (gitignored)
    goblin.example.json     # Template
  services/
    notion_sync_service.py  # Notion webhooks + publish
    runtime_executor.py     # TS runtime integration
    task_scheduler.py       # Organic scheduling
    binder_compiler.py      # Chapter compilation
  routes/
    notion.py               # /api/v0/notion/*
    runtime.py              # /api/v0/runtime/*
    tasks.py                # /api/v0/tasks/*
    binder.py               # /api/v0/binder/*
```

---

## Configuration

### goblin.json (Local Only)

```json
{
  "server": {
    "host": "127.0.0.1",
    "port": 8767,
    "debug": true
  },
  "notion": {
    "webhook_secret": "your-webhook-secret",
    "sync_mode": "publish"
  },
  "runtime": {
    "max_state_size": 1048576,
    "timeout_ms": 5000
  },
  "scheduler": {
    "organic_mode": true,
    "daily_quota_calls": 200
  }
}
```

**Security:** Secrets stored in macOS Keychain, referenced by ID.

---

## Endpoints (Unstable - `/api/v0/*`)

### Notion Sync

```
POST   /api/v0/notion/webhook           # Incoming Notion changes
GET    /api/v0/notion/sync/status       # Current sync state
GET    /api/v0/notion/maps              # Local ↔ Notion mappings
POST   /api/v0/notion/publish           # Publish local → Notion
```

### TS Runtime

```
POST   /api/v0/runtime/parse            # Parse .md to AST
POST   /api/v0/runtime/execute          # Execute runtime block
GET    /api/v0/runtime/state            # Get state
PUT    /api/v0/runtime/state            # Set state variables
```

### Task Scheduler

```
POST   /api/v0/tasks/schedule           # Schedule task
GET    /api/v0/tasks/queue              # View scheduled queue
GET    /api/v0/tasks/runs               # Execution history
```

### Binder Compiler

```
POST   /api/v0/binder/compile           # Compile binder outputs
GET    /api/v0/binder/chapters          # List chapters
```

---

## Development Workflow

### 1. Start Goblin Dev Server

```bash
cd ~/uDOS
source .venv/bin/activate
python dev/goblin/goblin_server.py
```

### 2. Test Features Locally

````bash
# Test Notion webhook
curl -X POST http://localhost:8767/api/v0/notion/webhook \
  -H "Content-Type: application/json" \
  -d '{"type": "page.created", "data": {...}}'

# Test runtime execution
curl -X POST http://localhost:8767/api/v0/runtime/execute \
  -H "Content-Type: application/json" \
  -d '{"markdown": "# Test\n```state\n$name = \"Fred\"\n```"}'
````

### 3. Promote to Production

When feature is stable:

1. Write tests
2. Create proper API versioning
3. Move to appropriate location:
   - Core functionality → `/core/`
   - Extension → `/extensions/`
   - Production service → `/wizard/`
4. Update version numbers
5. Document in AGENTS.md

---

## Promotion Checklist

Before moving feature from Goblin to production:

- [ ] Feature is stable (no known breaking bugs)
- [ ] Tests written (unit + integration)
- [ ] Documentation complete
- [ ] API versioned properly (`/api/v1/*`)
- [ ] Config schema defined
- [ ] Security reviewed
- [ ] Performance acceptable
- [ ] Error handling comprehensive
- [ ] Logging consistent with uDOS standards
- [ ] Version bumped appropriately

---

## Design Principles

1. **Break Fast** — Goblin is for experimentation
2. **Local Only** — Never expose to public
3. **Feature Flags** — Easy to enable/disable
4. **Clear Promotion Path** — Features graduate to production
5. **Isolated State** — Don't pollute production data
6. **Verbose Logging** — Debug everything
7. **No Assumptions** — All features optional

---

## Status & Roadmap

### Current (v0.1.0.0)

- ✅ Server structure
- 🔄 Notion sync service (in progress)
- 🔄 TS runtime executor (in progress)
- 📋 Task scheduler (planned)
- 📋 Binder compiler (planned)

### Next (v0.2.0.0)

- Complete Notion webhook handlers
- SQLite mapping table queries
- Runtime state management
- Basic task scheduling

### Future

- Provider rotation logic
- Organic cron implementation
- Multi-chapter binder compilation
- Cost tracking integration

---

## Logging

All Goblin logs go to:

- `memory/logs/goblin-YYYY-MM-DD.log`
- `memory/logs/goblin-debug-YYYY-MM-DD.log`

Use canonical logger:

```python
from core.services.logging_manager import get_logger

logger = get_logger('goblin-server')
logger.info('[GOBLIN] Feature tested successfully')
```

---

## FAQ

**Q: Why "Goblin"?**  
A: Wizard = stable production magic. Goblin = chaotic experimental workshop.

**Q: Can I run Wizard and Goblin simultaneously?**  
A: Yes! Different ports (8765 vs 8767), isolated configs.

**Q: What happens to features that don't graduate?**  
A: Archive to `.archive/goblin-experiments-YYYY-MM-DD/`

**Q: How do I know when to promote?**  
A: When you've used it successfully for 2+ weeks without issues.

**Q: Is Goblin ever in git?**  
A: Yes, but `config/goblin.json` is gitignored. Code is committed.

---

_Last Updated: 2026-01-15_  
_Goblin Dev Server v0.1.0.0_
