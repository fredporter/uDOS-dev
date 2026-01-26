# Error Handling System

**File:** `core/utils/error_helper.py`
**Version:** v1.2.28+

## Overview

Centralized error handling system that provides consistent, helpful error messages with recovery suggestions for DEV MODE, OK FIX, and system diagnostics.

## Functions

### `format_system_error(error, context="", show_traceback=True)`

Format a general system error with full recovery options.

**Returns:**
```
💀 CATASTROPHIC FAILURE
══════════════════════════════════════════════════════════════════════
📍 Context: [context]
❌ Error: ExceptionType: error message

🔍 Stack Trace:
----------------------------------------------------------------------
[traceback]
----------------------------------------------------------------------

🛠️  Recovery Options:
   1. DEV MODE      - Enter development mode for diagnostics
   2. OK FIX        - Use AI assistant to analyze and fix
   3. DEBUG STATUS  - Check system health and logs
   4. REPAIR        - Run automated system repair

💡 Tip: Type 'DEV MODE' to enable advanced debugging tools
══════════════════════════════════════════════════════════════════════
```

### `format_command_error(error, command, show_traceback=False)`

Format a command execution error (simpler, no traceback by default).

### `format_startup_error(error, component)`

Format startup/initialization errors with environment checks.

**Returns:**
```
🚨 STARTUP FAILURE
══════════════════════════════════════════════════════════════════════
❌ Failed to initialize: [component]
   Error: ExceptionType: error message

🛠️  Try:
   • Check virtual environment: source .venv/bin/activate
   • Verify dependencies: pip install -r requirements.txt
   • Run system repair: python uDOS.py (then type REPAIR)
   • Check logs: memory/logs/auto/
══════════════════════════════════════════════════════════════════════
```

### `format_extension_error(error, extension_name, action="load")`

Format extension-specific errors with extension recovery commands.

**Returns:**
```
⚠️  EXTENSION ERROR: [extension_name]
══════════════════════════════════════════════════════════════════════
❌ Failed to [action]: ExceptionType
   error message

🛠️  Recovery:
   • Check extension status: POKE STATUS [extension_name]
   • View extension info: POKE INFO [extension_name]
   • Reinstall: POKE UNINSTALL [extension_name] && POKE INSTALL [extension_name]
   • Get AI help: OK FIX
══════════════════════════════════════════════════════════════════════
```

### `suggest_dev_mode_help()`

Returns a short message suggesting DEV MODE/OK FIX.

### `@wrap_with_error_handling` decorator

Automatically wrap any function with error handling:

```python
from core.utils.error_helper import wrap_with_error_handling

@wrap_with_error_handling
def risky_operation():
    # Your code here
    pass
```

## Usage Examples

### Main Loop Error Handler

```python
from core.utils.error_helper import format_command_error

try:
    result = command_handler.execute(cmd)
except Exception as e:
    error_msg = format_command_error(e, command=cmd, show_traceback=True)
    print(error_msg)
```

### Startup Error Handler

```python
from core.utils.error_helper import format_startup_error

try:
    component = initialize_system()
except Exception as e:
    error_msg = format_startup_error(e, component="Config Manager")
    print(error_msg)
    sys.exit(1)
```

### Extension Error Handler

```python
from core.utils.error_helper import format_extension_error

try:
    server_manager.start_server(extension_name)
except Exception as e:
    return format_extension_error(e, extension_name, action="start")
```

## Integration Status

### ✅ Integrated Files

- `core/uDOS_main.py` - Main loop and startup errors
- `core/commands/output_handler.py` - POKE command errors

### 🔄 To Integrate

- `core/commands/*_handler.py` - All command handlers
- `extensions/server_manager.py` - Server management
- `core/services/*` - Service initialization
- `extensions/play/commands/*` - Play extension handlers

## Recovery Flow

1. **User encounters error** → System displays formatted error with suggestions
2. **User types "DEV MODE"** → Enters development mode with advanced tools
3. **User types "OK FIX"** → AI assistant analyzes error and suggests fix
4. **User types "DEBUG STATUS"** → System health diagnostics displayed
5. **User types "REPAIR"** → Automated system repair attempts fix

## Best Practices

1. **Always use error_helper** for exception handling in core/commands/
2. **Include context** when calling format functions
3. **Show tracebacks** for system errors, hide for user errors
4. **Test error paths** to ensure helpful messages appear
5. **Update integration list** when adding to new files

## Related Commands

- `DEV MODE` - Enter development mode (see `dev/README.md`)
- `OK FIX` - AI-powered error analysis (see `wiki/OK-Assistant-Guide.md`)
- `DEBUG STATUS` - System diagnostics
- `REPAIR` - Automated system repair
- `STATUS --health` - System health check
