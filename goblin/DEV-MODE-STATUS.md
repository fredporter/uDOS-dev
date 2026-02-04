# Goblin Dev Server — Dev Mode Status Check

**Date:** 2026-02-04  
**Purpose:** Container testing + vibe CLI integration for local dev workflows  
**Current Status:** ✅ Dev workflow endpoints wired; needs validation pass

---

## 🎯 Purpose (Clarified)

Goblin is **NOT production code**. It's the **dev mode testing server** for:

1. **Container Development** — Test containers locally before packaging
2. **Vibe CLI Integration** — Full vibe CLI capacity for development
3. **MODE Testing** — Experimental renderers (Teletext, Terminal) before Core promotion
4. **Local Workflows** — Dev Mode endpoints for rapid iteration

**Relationship to v1.3:**
- ✅ Supports v1.3 dev workflows
- ✅ Tests v1.3 containers locally
- ✅ Provides vibe CLI endpoints for TUI integration
- ❌ NOT part of v1.3 production refactor
- ❌ Gets replaced by production Wizard routes when MODEs graduate

---

## ✅ Current Working Status

### Infrastructure
- ✅ FastAPI server structure (port 8767)
- ✅ Launch scripts: `dev/bin/Launch-Goblin-Dev.command`
- ✅ Dashboard framework (Svelte)
- ✅ MODE routes defined (Teletext, Terminal)
- ✅ Services architecture

### Routes Registered
```python
# After import fixes:
✅ /                              # Root info
✅ /health                        # Health check
✅ /api/v0/modes/                 # MODE list
✅ /api/v0/modes/teletext/*       # Teletext patterns/render/animate
✅ /api/v0/modes/terminal/*       # Terminal schemes/render/test
✅ /api/dev/                      # Dev index (Round 7 kickoff)
✅ /api/dev/binders/*             # Binder dev endpoints
✅ /api/dev/screwdriver/*         # Screwdriver flash pack endpoints
✅ /api/dev/meshcore/*            # MeshCore device manager + pairing
✅ /api/dev/containers/*          # Container test/status
✅ /api/dev/vibe/*                # Vibe proxy + context
✅ /api/dev/logs/*                # Log tail + list
✅ /api/dev/vault/sync            # Vault sync
```

---

## ⚠️ Current Issues (Being Fixed)

### 1. Import Path Issues
**Problem:** Relative imports failing between modules  
**Status:** ✅ FIXED (added goblin dir to sys.path)  
**Files Modified:**
- [goblin_server.py](goblin_server.py) — Added `sys.path.insert(0, str(Path(__file__).parent))`
- [routes/mode_routes.py](routes/mode_routes.py) — Changed to absolute imports from goblin dir

### 2. Server Startup
**Problem:** Console blocking server launch  
**Status:** ✅ FIXED  
**Solution:** Console is now optional. Set `GOBLIN_CONSOLE=1` to enable interactive prompt; default is off.

### 3. Route Testing
**Problem:** Endpoints not re-verified after wiring  
**Status:** ⚠️ PENDING  
**Next:** Run curl validation pass for dev endpoints

---

## 🎯 Integration with v1.3 Dev Workflows

### Vibe CLI Integration
From [VIBE-CLI-ROADMAP-ALIGNMENT.md](../../VIBE-CLI-ROADMAP-ALIGNMENT.md):

**Goblin Should Provide:**
```bash
# Container testing endpoints
POST /api/dev/containers/test/{name}
GET  /api/dev/containers/status/{name}
GET  /api/dev/containers

# Vibe CLI proxy endpoints  
POST /api/dev/vibe/chat
POST /api/dev/vibe/context-inject
GET  /api/dev/vibe/history

# MODE testing (existing)
GET  /api/v0/modes/teletext/*
GET  /api/v0/modes/terminal/*

# Dev workflow helpers
GET  /api/dev/logs/tail
GET  /api/dev/logs/list
POST /api/dev/vault/sync
```

### Container Testing Workflow
From [CONTAINER-SYSTEM-QUICK-REF.md](../../docs/CONTAINER-SYSTEM-QUICK-REF.md):

**Local Dev Pattern:**
1. Clone container to `/library/`
2. Test via Goblin dev endpoints
3. Iterate locally
4. Promote to Wizard when stable
5. Package for distribution

**Automation Helper:**
- `dev/bin/test-containers.py` runs the Goblin container tests and writes a JSON report to `vault/07_LOGS/`.

**Goblin's Role:**
- ✅ Provides test harness before Wizard integration
- ✅ Validates container startup/config
- ✅ Allows rapid iteration without restarting Wizard
- ✅ Logs detailed debug output

---

## 📋 Next Actions

### Immediate (Fix Current Server)
- [x] Fix import paths in goblin_server.py
- [x] Fix import paths in routes/mode_routes.py  
- [ ] Test server startup with uvicorn
- [ ] Verify all MODE endpoints respond
- [ ] Document working curl examples

### Round 7 Kickoff (Goblin Dev Server Experiments)
- [x] Add `/api/dev/binders/*` endpoints for binder workflows
- [x] Add binder compiler schema fallback + auto-create binder rows
- [x] Wire binder creation + compile to real data sources (filesystem + compiler sync)
- [x] Define Screwdriver flash-pack endpoints + payload schema
- [x] Define MeshCore device manager API + pairing flow

### Short-term (Dev Workflow Support)
- [x] Add `/api/dev/containers/` routes
- [x] Add `/api/dev/vibe/` proxy routes
- [x] Add `/api/dev/logs/` tail endpoint
- [x] Wire to Vibe service (Ollama)
- [x] Add container status checks
- [x] Add `/api/dev/vault/sync` endpoint
- [x] Add container testing automation script (`dev/bin/test-containers.py`)

### Integration (v1.3 Alignment)
- [ ] Document how Goblin supports v1.3 container dev
- [ ] Create dev workflow guide (local test → Wizard → package)
- [ ] Add Goblin endpoints to uCODE TUI discovery
- [ ] Link to vibe CLI roadmap items

---

## 🔗 Key References

**Dev Workflows:**
- [VIBE-CLI-ROADMAP-ALIGNMENT.md](../../VIBE-CLI-ROADMAP-ALIGNMENT.md) — Vibe integration plan
- [VIBE-CLI-INTEGRATION-SUMMARY.md](../../VIBE-CLI-INTEGRATION-SUMMARY.md) — What's working
- [CONTAINER-SYSTEM-QUICK-REF.md](../../docs/CONTAINER-SYSTEM-QUICK-REF.md) — Container testing

**Architecture:**
- [dev/README.md](../README.md) — Dev workshop overview
- [v1-3/docs/00-dev-brief.md](../../v1-3/docs/00-dev-brief.md) — v1.3 dev lanes
- [docs/ROADMAP-TODO.md](../../docs/ROADMAP-TODO.md) — Migration status

**Goblin Specific:**
- [README.md](README.md) — Goblin overview
- [QUICK-REFERENCE.md](QUICK-REFERENCE.md) — API reference
- [TUI-GUIDE.md](TUI-GUIDE.md) — Interactive console

---

## ✅ Validation Checklist

Once imports fixed and server running:

```bash
# 1. Server starts cleanly
cd /Users/fredbook/Code/uDOS/dev/goblin
python -m uvicorn goblin_server:app --host 127.0.0.1 --port 8767

# 2. Core endpoints respond
curl http://localhost:8767/
curl http://localhost:8767/health

# 3. MODE endpoints work
curl http://localhost:8767/api/v0/modes/teletext/patterns
curl http://localhost:8767/api/v0/modes/terminal/schemes

# 4. Dashboard accessible
open http://localhost:5174

# 5. Ready for dev workflow integration
echo "✅ Goblin ready for container testing + vibe CLI integration"
```

---

**Status:** Import fixes complete. Round 7 kickoff underway; dev workflow endpoints wired.  
**Next:** Verify live endpoints, then document dev workflows + migration plan.
