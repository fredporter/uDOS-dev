# uDOS Command Handlers (v1.2.25)

**Status:** 📘 CURRENT DOCUMENTATION (Beta v1.2.x)  
**Note:** Alpha v1.0.0.0+ uses same architecture  
**Last Updated:** 2025-12-30

## Modular Handler Architecture

**71 Module Handlers** - All commands route through parent module handlers.

## Critical Rules ⚠️

### ✅ ALWAYS:
1. **Add to existing handlers** - Check if a handler exists before creating new
2. **Use parent-child pattern** - Aliases route to parent (LOCATE → TILE)
3. **Keep methods private** - Use `_handle_*()` pattern for implementations
4. **Inherit from BaseCommandHandler** - Provides logging, config, viewport
5. **Test routing** - Verify command routes through `core/uDOS_commands.py`

### ❌ NEVER:
1. **Create `cmd_*.py` files** - DEPRECATED pattern (archived v1.2.25)
2. **Hardcode paths** - Use `Config.get_path()` or constants
3. **Duplicate logic** - Import and reuse existing code
4. **Bypass router** - All commands MUST route through main router
5. **Mix concerns** - File operations in display handler, etc.

## Handler Structure

```python
# core/commands/example_handler.py
from core.commands.base_handler import BaseCommandHandler

class ExampleHandler(BaseCommandHandler):
    """Handles EXAMPLE domain commands (EXAMPLE, ALIAS1, ALIAS2)."""
    
    def handle(self, command, params, grid, parser):
        """Main entry point - routes to private methods.
        
        Args:
            command: Command name (e.g., "EXAMPLE", "ALIAS1")
            params: Command parameters
            grid: Grid instance (optional)
            parser: Parser instance (optional)
            
        Returns:
            Command result or None
        """
        if command == "EXAMPLE":
            return self._handle_example(params)
        elif command == "ALIAS1":
            return self._handle_alias1(params)
        elif command == "ALIAS2":
            return self._handle_alias2(params)
        
        return f"Unknown command: {command}"
    
    def _handle_example(self, params):
        """Handle EXAMPLE command - single responsibility."""
        # Implementation here
        pass
```

## Router Registration

```python
# core/uDOS_commands.py
from core.commands.example_handler import ExampleHandler

class CommandHandler:
    def __init__(self, **kwargs):
        # ... other handlers ...
        self.example_handler = ExampleHandler(**handler_kwargs)
    
    def handle_command(self, command, params):
        module = command.split()[0].upper()
        
        # Parent-child relationships
        if module in ["EXAMPLE", "ALIAS1", "ALIAS2"]:
            return self.example_handler.handle(module, params, grid, parser)
```

## Current Handlers (71 modules)

### Core System
- `system_handler.py` - STATUS, REPAIR, REBOOT, VERSION
- `config_handler.py` - CONFIG commands
- `environment_handler.py` - ENV commands
- `variable_handler.py` - Variable management
- `output_handler.py` - Output formatting

### File Operations
- `file_handler.py` - FILE, NEW, DELETE, COPY, MOVE, RENAME
- `backup_handler.py` - BACKUP commands (v1.1.16)
- `undo_handler.py` - UNDO, REDO (v1.1.16)
- `archive_handler.py` - ARCHIVE commands (v1.1.16)
- `repair_handler.py` - REPAIR, RECOVER (with soft-delete)

### Display & Graphics
- `display_handler.py` - BLANK, CLEAR, SPLASH, DASH
- `color_handler.py` - COLOR, PALETTE
- `diagram_handler.py` - DIAGRAM commands
- `sprite_handler.py` - SPRITE commands
- `panel_handler.py` - PANEL commands

### Navigation & Grid
- `tile_handler.py` - TILE, LOCATE
- `map_handler.py` - MAP commands
- `grid_handler.py` - GRID commands

### Memory System
- `memory_commands.py` - MEMORY tier 4 (PUBLIC)
- `private_commands.py` - PRIVATE tier (tier 3)
- `shared_commands.py` - SHARED tier (tier 2)
- `community_commands.py` - COMMUNITY tier (tier 1)

### Knowledge & Guides
- `guide_handler.py` - GUIDE commands (v2.0 interactive)
- `help_handler.py` - HELP commands

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
- `tree_handler.py` - TREE commands
- `peek_handler.py` - PEEK commands
- `time_handler.py` - TIME, DATE (v1.2.22)
- `json_handler.py` - JSON viewer (v1.2.22)
- `build_handler.py` - BUILD commands
- `clone_handler.py` - CLONE commands
- `device_handler.py` - DEVICE commands (v1.2.25)
- `inbox_handler.py` - INBOX commands

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
