# Goblin Quick Reference

**Version:** v0.2.0.0 (Nuclear Clean)  
**Purpose:** MODE experimental playground

---

## Launch

```bash
# Terminal 1: Start server (console optional)
cd /Users/fredbook/Code/uDOS/dev/goblin
source ../../.venv/bin/activate
GOBLIN_CONSOLE=1 python goblin_server.py

# Terminal 2: Start dashboard
cd /Users/fredbook/Code/uDOS/dev/goblin/dashboard
npm install  # First time only
npm run dev
```

**URLs:**

- Server: http://localhost:8767
- Dashboard: http://localhost:5174

---

## API Endpoints

### Teletext MODE

```bash
# List patterns
curl http://localhost:8767/api/v0/modes/teletext/patterns

# Render frame
curl "http://localhost:8767/api/v0/modes/teletext/render?pattern=chevrons&width=80"

# Animate
curl "http://localhost:8767/api/v0/modes/teletext/animate?pattern=raster&frames=10"
```

### Terminal MODE

```bash
# List schemes
curl http://localhost:8767/api/v0/modes/terminal/schemes

# Render text
curl "http://localhost:8767/api/v0/modes/terminal/render?text=hello&fg=green&style=bold"

# Run tests
curl http://localhost:8767/api/v0/modes/terminal/test

# Apply scheme
curl "http://localhost:8767/api/v0/modes/terminal/scheme?text=hello&scheme=solarized"
```

---

## Binder + Screwdriver Endpoints (Migrated)

Binder and Screwdriver dev endpoints have moved to Wizard:

- Binder API: `http://localhost:8765/api/binder/*`
- Screwdriver API: `http://localhost:8765/api/sonic/screwdriver/*`

See `docs/BINDER-SONIC-ENDPOINTS.md` for the updated examples.

---

## MeshCore Device Manager (Round 7)

```bash
# List devices
curl http://localhost:8767/api/dev/meshcore/devices

# Register a device
curl -X POST http://localhost:8767/api/dev/meshcore/devices \
  -H "Content-Type: application/json" \
  -d '{"device_id":"D1","device_type":"node"}'

# Create pairing
curl -X POST http://localhost:8767/api/dev/meshcore/pairings \
  -H "Content-Type: application/json" \
  -d '{"source_id":"D1","target_id":"D2","method":"pin"}'

# Confirm pairing
curl -X POST http://localhost:8767/api/dev/meshcore/pairings/pair-XXXX/confirm
```

---

## Dev Workflow Endpoints (Round 7)

```bash
# Container test
curl -X POST http://localhost:8767/api/dev/containers/test/meshcore \
  -H "Content-Type: application/json" \
  -d '{"validate_only":true}'

# Vibe chat (requires Ollama)
curl -X POST http://localhost:8767/api/dev/vibe/chat \
  -H "Content-Type: application/json" \
  -d '{"prompt":"summarize recent changes","with_context":true}'

# Tail logs
curl http://localhost:8767/api/dev/logs/tail?lines=200

# Vault sync (dry run)
curl -X POST http://localhost:8767/api/dev/vault/sync \
  -H "Content-Type: application/json" \
  -d '{"source":"memory/bank","target":"vault/notes","dry_run":true}'
```

---

## Container Testing Automation

```bash
# Run all container tests + write report to vault/07_LOGS/
python dev/bin/test-containers.py

# Test a single container and write a custom report path
python dev/bin/test-containers.py --container meshcore --out /tmp/container_report.json

# Fail the process if any container reports errors
python dev/bin/test-containers.py --strict
```

---

## Structure

```
/dev/goblin/
├── goblin_server.py         # FastAPI server (8767)
├── modes/
│   ├── teletext_mode.py     # Teletext renderer
│   └── terminal_mode.py     # Terminal renderer
├── routes/
│   └── mode_routes.py       # /api/v0/modes/*
├── dashboard/               # Svelte app (5174)
│   ├── src/routes/
│   │   ├── +layout.svelte   # Top nav + bottom bar
│   │   ├── +page.svelte     # Home
│   │   ├── teletext/        # Teletext MODE
│   │   └── terminal/        # Terminal MODE
│   └── package.json
└── bin/
    ├── launch-goblin-server.sh
    └── launch-goblin-dashboard.sh
```

---

## Development

### Adding a New Pattern (Teletext)

1. Add to `wizard/services/teletext_patterns.py`
2. Update `PatternName` enum
3. Test via Goblin API
4. When stable, promote to Core

### Adding a New Scheme (Terminal)

1. Add to `modes/terminal_mode.py` schemes dict
2. Update `list_schemes()` method
3. Test via dashboard
4. Document in README

---

## Promotion Path

When MODE is stable:

1. Move to `/core/runtime/modes/`
2. Update Core imports
3. Add tests to Core test suite
4. Archive Goblin experiments

---

## Size

**Target:** < 100MB (vs old 580MB)

- No duplicate Core
- Minimal Svelte deps
- MODE experiments only

---

_Last Updated: 2026-02-04_
