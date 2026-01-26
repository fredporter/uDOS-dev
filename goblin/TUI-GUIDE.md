# Goblin Interactive TUI

**Version:** v0.2.0.0  
**Added:** 2026-01-26

---

## Overview

Interactive command prompt for Goblin MODE playground with auto-launching dashboard.

---

## Features

1. **Auto-start server in background**
2. **Auto-open dashboard in browser**
3. **Interactive `goblin>` prompt**
4. **Quick MODE testing commands**
5. **Clean shutdown handling**

---

## Launch

```bash
# From anywhere in uDOS repo
./dev/bin/Launch-Goblin-Dev.command

# Or directly
cd dev/goblin
./bin/launch-goblin-server.sh
```

**What happens:**

1. Server starts on port 8767 (background)
2. Dashboard opens at http://localhost:5174
3. TUI prompt appears: `goblin>`
4. Use commands to test MODEs
5. Type `exit` to quit (offers to stop server)

---

## Commands

| Command    | Description                       |
| ---------- | --------------------------------- |
| `help`     | Show available commands           |
| `status`   | Check server health               |
| `modes`    | List available MODEs              |
| `dash`     | (Re)open dashboard in browser     |
| `teletext` | Quick teletext render test        |
| `terminal` | Quick terminal render test        |
| `logs`     | Show recent server logs           |
| `exit`     | Exit TUI (prompts to stop server) |

---

## Example Session

```bash
$ ./dev/bin/Launch-Goblin-Dev.command

╔═══════════════════════════════════════════════════════════════╗
║              🧪 Goblin MODE Playground - TUI                  ║
╚═══════════════════════════════════════════════════════════════╝
Version: v0.2.0.0 | Port: 8767 | Experimental

Available Commands:
  help     - Show this help
  status   - Check server status
  modes    - List available MODEs
  dash     - Open dashboard in browser
  teletext - Quick teletext test
  terminal - Quick terminal test
  logs     - Show recent server logs
  exit     - Exit TUI

goblin> status
✅ Server online
   Version: 0.2.0.0
   Status: ok

goblin> teletext
Testing Teletext MODE...

▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓
 ▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓
▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓

✅ Teletext MODE working

goblin> dash
Opening dashboard...
URL: http://localhost:5174
✅ Browser launched

goblin> exit

Stop Goblin server? [Y/n] y
✅ Server stopped
```

---

## Launcher Behavior

### Launch-Goblin-Dev.command

**Old:**

- Start server (foreground, blocks terminal)
- User must Ctrl+C to stop
- No dashboard auto-open

**New:**

- Start server (background)
- Auto-open dashboard
- Launch interactive TUI
- Type `exit` to quit cleanly
- Prompts to stop server on exit

---

## Dashboard Auto-Open

Both launchers now auto-open the dashboard:

### Server Launcher

```bash
./dev/goblin/bin/launch-goblin-server.sh
# → Server starts in background
# → TUI launches
# → Type 'dash' to open browser
```

### Dashboard Launcher

```bash
./dev/goblin/bin/launch-goblin-dashboard.sh
# → npm run dev starts
# → Browser opens after 3 seconds
```

---

## File Structure

```
dev/goblin/
├── goblin_tui.py              # Interactive TUI
├── bin/
│   ├── launch-goblin-server.sh   # Server + TUI launcher
│   └── launch-goblin-dashboard.sh # Dashboard + auto-open
```

---

## Implementation Details

### Background Server Launch

```bash
# Start server in background
python goblin_server.py > /dev/null 2>&1 &
SERVER_PID=$!

# Launch TUI (foreground)
python goblin_tui.py

# When TUI exits, kill server
kill $SERVER_PID 2>/dev/null
```

### Auto-Open Dashboard

```python
import webbrowser
webbrowser.open("http://localhost:5174")
```

### Prompt Loop

```python
while self.running:
    command = input(f"\n{MAGENTA}{BOLD}goblin>{NC} ").strip().lower()
    self.handle_command(command)
```

---

## See Also

- [Goblin README](../../dev/goblin/README.md)
- [Goblin Quick Reference](../../dev/goblin/QUICK-REFERENCE.md)
- [MODE Specifications](../../docs/specs/)

---

**Status:** Production Ready  
**Last Updated:** 2026-01-26
