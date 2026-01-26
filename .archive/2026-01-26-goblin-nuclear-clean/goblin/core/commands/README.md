# uDOS Command Handlers - Empty Framework (v1.0.0.65+)

**Status:** 🧪 FRAMEWORK ONLY (All handlers removed 2026-01-26)  
**Last Updated:** 2026-01-26  
**Purpose:** Trial/experimental command development

## Framework Status

All 80 concrete handlers have been removed to keep Goblin as an **experimental testing ground**.

### What's Remaining

**Framework Files:**

- `base_handler.py` - Base class for all command handlers
- `handler_utils.py` - Shared utilities for handlers
- `__init__.py` - Module initialization
- `config_sections/` - Configuration structures

### What Was Removed

**80 Handlers** spanning:

- Core Gameplay (18) — missions, workflows, tasks, resources
- User Interface (13) — display, themes, TUI, input
- Data & Knowledge (15) — memory, guides, archives, overlays
- Creativity & Content (12) — make, sprites, music, voice
- System & Integration (13) — files, time, devices, email
- Network & Cloud (8) — mesh, QR, audio, cloud
- Utilities (5) — colors, variables, environment

**For complete inventory, see:** [GOBLIN-COMMAND-MANIFEST.md](GOBLIN-COMMAND-MANIFEST.md)

---

## Adding New Commands (Trial/Experimental)

### 1. Create Handler File

```python
# dev/goblin/core/commands/my_new_handler.py
from .base_handler import BaseCommandHandler

class MyNewCommandHandler(BaseCommandHandler):
    """Handler for MY_NEW commands (trial feature)."""

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        # Initialize state

    def handle(self, command, params, grid, parser):
        """Route MY_NEW commands."""
        if command == "STATUS":
            return self._handle_status(params)
        return f"Unknown MY_NEW command: {command}"

    def _handle_status(self, params):
        """Handle MY_NEW STATUS command."""
        return "✅ My new command is working!"
```

### 2. Register in Router

Edit `dev/goblin/core/uDOS_commands.py`:

```python
# In __init__:
from dev.goblin.core.commands.my_new_handler import MyNewCommandHandler
self.my_new_handler = MyNewCommandHandler(**handler_kwargs)

# In execute_ucode():
elif module == "MY_NEW":
    return self.my_new_handler.handle(command, params, grid, parser)
```

### 3. Test

```
$ MYNEW STATUS
✅ My new command is working!
```

---

## Guidelines for Trial Commands

### ✅ DO:

1. **Use this space to experiment** - Try new UI paradigms, features, workflows
2. **Keep it focused** - One handler per logical command domain
3. **Test against Goblin only** - Don't affect Core or Wizard
4. **Document your intent** - Why is this being trialed?
5. **Create handler docstrings** - Purpose, examples, status

### ❌ DON'T:

1. **Don't duplicate Core/Wizard logic** - Refer to GOBLIN-COMMAND-MANIFEST.md
2. **Don't use hardcoded paths** - Use config/PATHS
3. **Don't bypass the router** - All commands route through `uDOS_commands.py`
4. **Don't leave broken handlers** - Test before committing
5. **Don't commit to long-term** - Goblin is for experimentation

---

## Handler Base Class

All new handlers should extend `BaseCommandHandler`:

```python
from .base_handler import BaseCommandHandler

class MyHandler(BaseCommandHandler):
    """Your handler docstring."""

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        # Access these from parent:
        # - self.viewport: Viewport instance
        # - self.logger: Logger instance
        # - self.config: Configuration
        # - self.theme: Theme name
        # - self.connection: ConnectionManager
```

**Inherited Methods:**

- `self.get_message(key, **kwargs)` - Get themed messages
- `self.logger.info()`, `logger.error()` - Logging
- `self.viewport.render()` - Display output

---

## Removed Handlers Reference

**See [GOBLIN-COMMAND-MANIFEST.md](GOBLIN-COMMAND-MANIFEST.md) for:**

- Complete list of all 80 removed handlers
- Their original purposes
- Which moved to Core vs Wizard
- Architectural decisions

---

## Next Steps

1. **To add a trial command:** Follow the "Adding New Commands" section above
2. **To graduate a command:** Document it in GOBLIN-COMMAND-MANIFEST.md first
3. **To review past commands:** See GOBLIN-COMMAND-MANIFEST.md for history
   class CommandHandler:
   def **init**(self, \*\*kwargs): # ... other handlers ...
   def handle_command(self, command, params):
   module = command.split()[0].upper()

````

## Current Handlers (71 modules)

- `config_handler.py` - CONFIG commands
- `environment_handler.py` - ENV commands
- `variable_handler.py` - Variable management

### File Operations

- `file_handler.py` - FILE, NEW, DELETE, COPY, MOVE, RENAME
- `diagram_handler.py` - DIAGRAM commands
- `sprite_handler.py` - SPRITE commands

### Memory System

- `memory_commands.py` - MEMORY tier 4 (PUBLIC)
- `private_commands.py` - PRIVATE tier (tier 3)
- `shared_commands.py` - SHARED tier (tier 2)
- `community_commands.py` - COMMUNITY tier (tier 1)

### Knowledge & Guides

- `guide_handler.py` - GUIDE commands (v2.0 interactive)

### AI & Assistant

- `assistant_handler.py` - ASK, ANALYZE
- `ok_handler.py` - OK commands (v1.2.21)

### Workflows & Automation

- `workflow_handler.py` - WORKFLOW, RUN commands
- `mission_handler.py` - MISSION commands
- `checklist_handler.py` - CHECKLIST commands

### User Interface

- `tui_handler.py` - TUI commands (v1.2.15)
- `keypad_demo_handler.py` - KEYPAD demo (v1.2.25)
- `mouse_handler.py` - MOUSE commands (v1.2.25)
- `selector_handler.py` - SELECT commands (v1.2.25)

### Extensions

- `extension_handler.py` - EXTENSION management
- `sandbox_handler.py` - SANDBOX commands

### Utilities

- `peek_handler.py` - PEEK commands
- `time_handler.py` - TIME, DATE (v1.2.22)
- `json_handler.py` - JSON viewer (v1.2.22)
- `build_handler.py` - BUILD commands
- `clone_handler.py` - CLONE commands
- `device_handler.py` - DEVICE commands (v1.2.25)
- `inbox_handler.py` - INBOX commands

### Delegated to Core/Wizard

- HELP, MAP, PANEL → Refer to `core/commands/*` handlers for canonical implementations
- TIDY, CLEAN, BACKUP, COMPOST → Managed by `core/commands/maintenance_handler.py`
- REPAIR → Managed by `core/commands/repair_handler.py`
- SHAKEDOWN → Managed by `core/commands/shakedown_handler.py`
- DEV MODE → Managed by Wizard Server (`core/commands/dev_mode_handler.py`)
- TREE → Managed via Wizard/Core MEMORY tooling (`core/commands/memory_commands.py`)

## Adding a New Command

### 1. Identify Parent Handler

Check if a handler already exists for your command domain:

- File operations? → `file_handler.py`
- Display/graphics? → `display_handler.py`
- Navigation? → `tile_handler.py`
- Memory? → `memory_commands.py`

### 2. Add Method to Handler

```python
# core/commands/parent_handler.py
def _handle_newcmd(self, params):
    """Handle NEWCMD command."""
    # Implementation
    return result
```

### 3. Update Handle Method

```python
def handle(self, command, params, grid, parser):
    if command == "NEWCMD":
        return self._handle_newcmd(params)
    # ... existing commands ...
```

### 4. Register in Router

```python
# core/uDOS_commands.py
elif module in ["PARENT", "EXISTING1", "NEWCMD"]:
    return self.parent_handler.handle(module, params, grid, parser)
```

### 5. Add to commands.json

```json
{
  "NEWCMD": {
    "syntax": "NEWCMD <args>",
    "description": "Does something useful",
    "category": "parent-domain"
  }
}
```

### 6. Test Routing

```python
# Test that command routes correctly
from core.config import Config
from core.uDOS_commands import CommandHandler

config = Config()
handler = CommandHandler(config=config)
result = handler.handle_command("NEWCMD", {})
assert result is not None
```

## Deprecated Patterns

### ❌ Standalone Command Files (Archived v1.2.25)

```python
# core/commands/cmd_mycommand.py  # WRONG - Don't create these
def cmd_mycommand(params):
    pass
```

**Why deprecated:**

- Creates file bloat (one file per command)
- No inheritance from BaseCommandHandler
- Harder to maintain and test
- Bypasses modular routing system

**Migration path:**
All `cmd_*.py` files have been archived to `core/commands/.archive/`.
Use parent handler pattern instead.

## Testing

```bash
# Run command routing tests
pytest memory/ucode/tests/test_routing.py

# Validate modular system
source .venv/bin/activate
python << 'EOF'
from core.config import Config
from core.uDOS_commands import CommandHandler

config = Config()
handler = CommandHandler(config=config)

# Test your command
result = handler.handle_command("MYCOMMAND", {})
print(f"✅ MYCOMMAND routed: {result}")
EOF
```

## Resources

- **Router Map**: See `core/uDOS_commands.py` for complete routing table
- **Base Handler**: `core/commands/base_handler.py` - Base class for all handlers
- **Commands Reference**: `core/data/commands.json` - All 97 commands documented
- **Copilot Instructions**: `.github/copilot-instructions.md` - Development guidelines

---

**Remember**: Keep core lean (16MB minimal), use existing handlers, test routing!
````
