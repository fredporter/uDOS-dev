# Goblin - MODE Experimental Playground

**Version:** v0.2.0.0 (Nuclear Clean - 2026-01-26)  
**Port:** 8767  
**Status:** Experimental MODE testing only

---

## Purpose

Goblin is the **experimental MODE playground** for uDOS. Test new rendering modes, ANSI patterns, and terminal features before promoting to Core.

### Current MODEs

1. **Teletext** - Retro teletext patterns, ANSI art, 80x30 grids
2. **Terminal** - Terminal emulation, escape codes, color schemes

When a MODE is stable and tested, it graduates to `/core/runtime/modes/`.

---

## Architecture

```
/dev/goblin/
├── goblin_server.py         # FastAPI server (port 8767)
├── modes/
│   ├── teletext/           # Teletext MODE experiments
│   └── terminal/           # Terminal MODE experiments
├── routes/
│   ├── mode_routes.py      # /api/v0/modes/*
│   └── dashboard_routes.py # Dashboard API
├── dashboard/              # Svelte + Tailwind UI
│   ├── src/
│   │   ├── routes/
│   │   │   ├── +layout.svelte  # Top nav + bottom bar
│   │   │   ├── +page.svelte    # Home
│   │   │   ├── Teletext.svelte
│   │   │   └── Terminal.svelte
│   │   └── lib/
│   │       ├── components/
│   │       └── styles/
│   ├── static/
│   └── package.json
├── config/
│   └── goblin.json         # Local config (gitignored)
└── tests/
    ├── test_teletext.py
    └── test_terminal.py
```

---

## Quick Start

### Interactive Mode (Recommended)

```bash
# Launch server + TUI + auto-open dashboard
./dev/bin/Launch-Goblin-Dev.command
```

**What happens:**

1. ✅ Server starts on port 8767 (background)
2. ✅ Dashboard auto-opens at http://localhost:5174
3. ✅ Interactive `goblin>` prompt for testing
4. Type `help` for commands, `exit` to quit

See [TUI-GUIDE.md](TUI-GUIDE.md) for full documentation.

### Manual Mode

```bash
# Install dependencies
cd /Users/fredbook/Code/uDOS/dev/goblin/dashboard
npm install

# Start server (in one terminal)
cd /Users/fredbook/Code/uDOS/dev/goblin
source ../../.venv/bin/activate
python goblin_server.py

# Start dashboard (in another terminal)
cd /Users/fredbook/Code/uDOS/dev/goblin/dashboard
npm run dev
```

**URLs:**

- Server: http://localhost:8767
- Dashboard: http://localhost:5174

---

## MODEs

### Teletext MODE

**Features:**

- ANSI pattern rendering
- Teletext-style grids (80x30)
- Color palettes (Commodore 64, BBC Micro, etc.)
- Frame-by-frame animation

**Routes:**

- `GET /api/v0/modes/teletext/patterns` - List available patterns
- `GET /api/v0/modes/teletext/render?pattern=chevrons` - Render pattern
- `GET /api/v0/modes/teletext/animate?pattern=raster` - Animated frames

### Terminal MODE

**Features:**

- ANSI escape code testing
- Color scheme experiments
- Terminal emulation patterns
- Text effects (bold, italic, underline)

**Routes:**

- `GET /api/v0/modes/terminal/schemes` - List color schemes
- `GET /api/v0/modes/terminal/render?text=test` - Render with effects
- `GET /api/v0/modes/terminal/test` - Terminal capability tests

---

## Development

### Adding a New MODE

1. Create mode directory: `modes/new_mode/`
2. Implement renderer: `modes/new_mode/renderer.py`
3. Add routes: `routes/mode_routes.py`
4. Add dashboard page: `dashboard/src/routes/NewMode.svelte`
5. Test: `tests/test_new_mode.py`

### Promoting to Core

When MODE is stable:

1. Move to `/core/runtime/modes/`
2. Update Core imports
3. Add to Core version
4. Archive Goblin experiments

---

## Size Target

**< 100MB total** (compared to old 580MB)

- No duplicate `/core/` (import from main Core)
- Minimal Svelte deps (Tailwind only, no heavy libs)
- No Notion sync, no screwdriver, no meshcore
- MODE experiments only

---

## References

- [Wizard Dashboard](../../wizard/dashboard/) - Structure reference
- [Core Runtime](../../core/) - Import services from here
- [Teletext Patterns](../../wizard/services/teletext_patterns.py) - Production patterns

---

**Last Updated:** 2026-01-26  
**Nuclear Clean:** Old Goblin archived to `.archive/2026-01-26-goblin-nuclear-clean/`
