# uDOS Reboot Splash Template

Version: 1.0.0 | Created: 2026-01-07

---
type: splash
trigger: reboot
animation: slide
duration: 1500
version: 1.0.0
---

## Splash Content

```text
╔══════════════════════════════════════════════════════════════════╗
║                                                                  ║
║                      ↻ System Reboot ↻                          ║
║                                                                  ║
║                  uDOS is restarting...                          ║
║                                                                  ║
╚══════════════════════════════════════════════════════════════════╝
```

## Reboot Sequence

```upy
# Reboot sequence messages
messages = [
    "Saving workspace state...",
    "Clearing session cache...",
    "Reinitializing core services...",
    "Reloading configuration...",
    "uDOS {{version}} restarted successfully."
]

# Display sequence with progress
total = len(messages)
for i, msg in enumerate(messages):
    progress = int((i + 1) / total * 100)
    PRINT f"[{progress:3d}%] {msg}"
    WAIT 200
```

## Post-Reboot Status

```text
Reboot Complete:
  ✓ Memory banks loaded
  ✓ Workspace restored
  ✓ Configuration applied
  ✓ Ready for commands

Session preserved. Type HISTORY to see recent commands.
```

## Variables

| Variable | Description | Default |
| -------- | ----------- | ------- |
| `{{version}}` | Current uDOS version | v1.0.0.58 |
| `{{session_id}}` | Current session ID | auto |
| `{{reboot_reason}}` | Why reboot was triggered | user |

## Customization Notes

Edit this template to customize your reboot experience.

- Modify reboot messages
- Add post-reboot checks
- Change progress indicator style
- Adjust timing

Location: `core/data/templates/reboot.splash.udos.md`
