# uDOS Build Tools

## 🔧 Development Mode (What You Want!)

**Use this for daily work:**
```bash
# Just double-click in Finder (from project root):
./Launch-Tauri-Dev.command
```

**What you get:**
- ✅ Full access to your local uDOS folder (`/Users/fredbook/Code/uDOS/`)
- ✅ All 71+ commands work (routes to backend API)
- ✅ Can read/write `/memory/`, `/core/`, user files
- ✅ Hot reload during development
- ✅ Debug console available
- ✅ Python API server + Tauri dev window

**How it works:**
1. Starts Python API server (port 5001)
2. Launches `npm run tauri dev`
3. Tauri runs as development window (NOT packaged app)
4. Full filesystem access to your working directory

---

## 📦 Distribution Mode (Archived - For Later)

**DMG building archived in:** `dev/.archive/dmg-build-2025-12-17/`

**Why it's archived:**
- Packaged DMG creates self-contained app in `/Applications/`
- App is sandboxed and can't access your uDOS working folder
- Great for distributing to users, NOT for development
- You don't need this right now!

**When to use DMG:**
- When you want to give uDOS to someone else
- When you need a standalone installer
- When ready for beta testing / release

**Files archived:**
- `build-macos-app.sh` - DMG builder script
- `sync_version.py` - Version syncing tool
- `uDOS_1.2.25_aarch64.dmg` - Last built DMG
- `RELEASE-PROCESS.md` - Release documentation

**To build DMG later:**
```bash
cd dev/.archive/dmg-build-2025-12-17/
./build-macos-app.sh
```

---

## Quick Reference

### Start Development
```bash
./Launch-Tauri-Dev.command
```

### Build DMG (Later)
```bash
cd dev/.archive/dmg-build-2025-12-17/
./build-macos-app.sh
```

### Clean Build Cache
```bash
cd extensions/tauri
cargo clean
rm -rf node_modules
npm install
```

---

## Troubleshooting

### "Virtual environment not found"
```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

### "Flask not installed"
```bash
source .venv/bin/activate
pip install -r requirements.txt
```

### "npm not found"
Install Node.js from: https://nodejs.org/

### Port 5001 already in use
```bash
# Find and kill the process
lsof -ti:5001 | xargs kill -9
```

---

## Architecture Notes

**Why dev mode is different:**
- **Development:** Tauri runs as window, full folder access
- **Production:** Packaged DMG, sandboxed, isolated
- **Your use case:** Local development = dev mode
- **DMG building:** For distribution only

**Key insight:**
> "It's essentially a new OS running in a Tauri window over the top of macOS, so it needs access to the uDOS working folder"
> 
> That's exactly what dev mode gives you! 🎉
- Part of the dev workflow, not the app itself
- Can be excluded from minimal distributions
