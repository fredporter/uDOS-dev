# uDOS Startup Splash Template
# Version: 1.0.0 | Created: 2026-01-07

---
type: splash
trigger: startup
animation: fade
duration: 2000
version: 1.0.0
---

## Splash Content

```text
╔══════════════════════════════════════════════════════════════════╗
║                                                                  ║
║     ██╗   ██╗██████╗  ██████╗ ███████╗                          ║
║     ██║   ██║██╔══██╗██╔═══██╗██╔════╝                          ║
║     ██║   ██║██║  ██║██║   ██║███████╗                          ║
║     ██║   ██║██║  ██║██║   ██║╚════██║                          ║
║     ╚██████╔╝██████╔╝╚██████╔╝███████║                          ║
║      ╚═════╝ ╚═════╝  ╚═════╝ ╚══════╝                          ║
║                                                                  ║
║              Universal Data Operating System                     ║
║                                                                  ║
╚══════════════════════════════════════════════════════════════════╝
```

## System Messages

```upy
# Startup sequence messages
messages = [
    "Initializing offline-first knowledge system...",
    "Loading memory banks...",
    "Preparing workspace at {{workspace_path}}...",
    "uDOS {{version}} ready."
]

# Display sequence
for msg in messages:
    PRINT msg
    WAIT 300
```

## Post-Startup Tips

```text
Quick Start:
  • HELP          - View all commands
  • GUIDE         - Browse knowledge bank
  • MEMORY        - Check memory status
  • BACKUP        - Create workspace snapshot
  
Type any command to begin. Press F1 for contextual help.
```

## Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `{{version}}` | Current uDOS version | v1.0.0.58 |
| `{{workspace_path}}` | User workspace location | memory/ |
| `{{user_name}}` | Current user | Operator |
| `{{timestamp}}` | Current date/time | auto |

## Customization Notes

Edit this template to customize your startup experience:
- Change ASCII art logo
- Modify startup messages
- Add custom tips for your workflow
- Adjust animation timing

Location: `core/data/templates/startup.splash.udos.md`
