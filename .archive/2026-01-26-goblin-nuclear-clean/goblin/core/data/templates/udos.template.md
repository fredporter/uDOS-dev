# uDOS System Template
# 
# This template defines system messages, terminology, and response patterns.
# Edit this file to customize how uDOS communicates with you.
#
# Variables use {{variable_name}} syntax and are replaced at runtime.
# Sections are marked with ## headers and can be extended.
#
# Version: 1.0.0
# Last Updated: 2026-01-06

---

## Identity

**name:** Default System
**style:** Standard uDOS
**icon:** 💻
**description:** Clean, straightforward uDOS system responses

---

## Prompt

**base:** >
**continuation:** ...
**script:** #
**debug:** ?

---

## Terminology

These define the canonical names for system commands. Override to create themed variants.

| Key | Default | Description |
|-----|---------|-------------|
| CMD_CATALOG | CATALOG | List available items |
| CMD_LOAD | LOAD | Load a file or resource |
| CMD_SAVE | SAVE | Save current state |
| CMD_RUN | RUN | Execute a script |
| CMD_CLS | CLS | Clear screen |
| CMD_HELP | HELP | Show help |
| CMD_MAP | MAP | Display map |
| CMD_EDIT | EDIT | Edit a file |
| CMD_EXIT | EXIT | Exit session |
| CMD_REBOOT | REBOOT | Restart system |
| CMD_REPAIR | REPAIR | Run diagnostics |

---

## Messages

### Errors

**ERROR_CRASH:**
```
ERROR: Command '{{command}}' failed unexpectedly
```

**ERROR_INVALID_FORMAT:**
```
ERROR: Invalid format '{{input}}' - {{error}}
```

**ERROR_UNKNOWN_MODULE:**
```
ERROR: Unknown module '{{module}}'
```

**ERROR_UNKNOWN_COMMAND:**
```
ERROR: Unknown command '{{command}}'
```

**ERROR_FILE_NOT_FOUND:**
```
ERROR: File not found '{{filename}}'
```

**ERROR_PERMISSION:**
```
ERROR: Permission denied for '{{path}}'
```

**ERROR_GENERIC:**
```
ERROR: {{error}}
```

### Information

**INFO_EXIT:**
```
Goodbye! uDOS session terminated.
```

**INFO_HELP_INTRO:**
```
Available commands:
```

**INFO_REPAIR_RUNNING:**
```
Running system diagnostics...
```

**INFO_VERSION:**
```
uDOS {{version}} - {{component}}
```

**INFO_LOCATION:**
```
Current location: {{tile}}
```

### Success

**SUCCESS_GENERIC:**
```
Operation completed successfully
```

**SUCCESS_REPAIR:**
```
System repair completed successfully
```

**SUCCESS_SAVE:**
```
Saved '{{filename}}' ({{bytes}} bytes)
```

**SUCCESS_LOAD:**
```
Loaded '{{filename}}'
```

### Progress

**PROGRESS_START:**
```
Starting {{operation}}...
```

**PROGRESS_COMPLETE:**
```
{{operation}} complete
```

---

## Response Patterns

### Greetings

**startup:**
```
uDOS {{version}} initialized
Type HELP for commands
```

**morning:**
```
Good morning. System ready.
```

**evening:**
```
Good evening. System ready.
```

### Confirmations

**confirm_delete:**
```
Delete '{{target}}'? (Y/N)
```

**confirm_overwrite:**
```
File '{{filename}}' exists. Overwrite? (Y/N)
```

**confirm_exit:**
```
Exit uDOS? (Y/N)
```

---

## Command Help

### HELP Text

Override these to customize command descriptions.

**help_catalog:**
```
CATALOG [path]
  List files and directories
  
  Options:
    path - Directory to list (default: current)
```

**help_load:**
```
LOAD <filename>
  Load a file into the system
  
  Arguments:
    filename - File to load
```

**help_save:**
```
SAVE <filename>
  Save current state to file
  
  Arguments:
    filename - Destination file
```

---

## Status Indicators

| Status | Symbol | Meaning |
|--------|--------|---------|
| OK | ✅ | Success |
| ERROR | ❌ | Failure |
| WARNING | ⚠️ | Caution |
| INFO | ℹ️ | Information |
| PROGRESS | ⏳ | In progress |
| PENDING | 📋 | Queued |
| MESH | 📡 | Network activity |
| LOCAL | 💻 | Local operation |

---

## Log Tags

These tags prefix log entries for filtering.

| Tag | Context | Example |
|-----|---------|---------|
| [LOCAL] | Local device operation | [LOCAL] File saved |
| [MESH] | MeshCore P2P | [MESH] Peer connected |
| [BT-PRIV] | Bluetooth Private | [BT-PRIV] Transfer complete |
| [NFC] | NFC contact | [NFC] Tag read |
| [QR] | QR relay | [QR] Code scanned |
| [WIZ] | Wizard Server | [WIZ] Query sent |
| [ERROR] | Error condition | [ERROR] Connection failed |

---

## Customization Notes

### Adding New Messages

1. Add a new `**MESSAGE_NAME:**` entry under the appropriate section
2. Use `{{variable}}` syntax for dynamic content
3. Keep messages concise (one line preferred)

### Creating Themed Variants

To create a themed variant (e.g., retro, survival, space):

1. Copy this file to `memory/templates/mytheme.udos.md`
2. Update the Identity section
3. Modify messages to match your theme
4. Load with: `CONFIG TEMPLATE mytheme`

### Future Expansion

This template system will expand to support:
- Role-based response variations
- Gameplay integration
- Dynamic message selection
- Context-aware responses

---

*Template Version: 1.0.0*
*Compatible with: uDOS Alpha v1.0.0.57+*
