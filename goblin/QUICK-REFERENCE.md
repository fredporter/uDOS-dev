# Goblin Quick Reference

**Version:** v0.2.0.0 (Nuclear Clean)  
**Purpose:** MODE experimental playground

---

## Launch

```bash
# Terminal 1: Start server
cd /Users/fredbook/Code/uDOS/dev/goblin
source ../../.venv/bin/activate
python goblin_server.py

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

_Last Updated: 2026-01-26_
