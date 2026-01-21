"""
Editor Command Handler

Unified handler for TILE and JSON editor commands.
Routes to appropriate TUI or Web editors based on mode.

Part of uDOS v1.2.31 - Editor Suite
"""

import json
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple
from dev.goblin.core.commands.base_handler import BaseCommandHandler


class EditorHandler(BaseCommandHandler):
    """Handler for TILE and JSON editor commands."""
    
    def __init__(self, components: Dict[str, Any]):
        """Initialize editor handler."""
        super().__init__(
            theme=components.get('theme', 'default'),
            connection=components.get('connection'),
            viewport=components.get('viewport'),
            user_manager=components.get('user_manager'),
            history=components.get('history'),
            command_history=components.get('command_history'),
            logger=components.get('logger'),
            main_handler=components.get('main_handler')
        )
        
        self.components = components
        self.config = components.get('config')
        
        # Editor instances (lazy loaded)
        self._tile_editor = None
        self._json_viewer = None
    
    @property
    def tile_editor(self):
        """Lazy load tile editor."""
        if self._tile_editor is None:
            from dev.goblin.core.ui.tile_editor import TileEditor
            self._tile_editor = TileEditor(self.config)
        return self._tile_editor
    
    @property
    def json_viewer(self):
        """Lazy load JSON viewer."""
        if self._json_viewer is None:
            from dev.goblin.core.ui.json_viewer import JSONTreeViewer
            self._json_viewer = JSONTreeViewer(self.config)
        return self._json_viewer
    
    def handle(self, args: List[str]) -> str:
        """Route editor commands."""
        if not args:
            return self._show_help()
        
        cmd = args[0].upper()
        params = args[1:] if len(args) > 1 else []
        
        # TILE commands
        if cmd == 'TILE':
            return self._handle_tile(params)
        
        # JSON commands
        elif cmd == 'JSON':
            return self._handle_json(params)
        
        else:
            return f"❌ Unknown editor command: {cmd}"
    
    def _handle_tile(self, params: List[str]) -> str:
        """Handle TILE editor commands."""
        if not params:
            return self._tile_help()
        
        action = params[0].upper()
        args = params[1:] if len(params) > 1 else []
        
        if action == 'EDIT' or action == 'OPEN':
            return self._tile_edit(args)
        elif action == 'NEW':
            return self._tile_new()
        elif action == 'LOAD':
            return self._tile_load(args)
        elif action == 'SAVE':
            return self._tile_save(args)
        elif action == 'EXPORT':
            return self._tile_export(args)
        elif action == 'LIST':
            return self._tile_list()
        elif action == 'VIEW':
            return self._tile_view(args)
        elif action == 'HELP':
            return self._tile_help()
        else:
            return f"❌ Unknown TILE action: {action}"
    
    def _handle_json(self, params: List[str]) -> str:
        """Handle JSON viewer/editor commands."""
        if not params:
            return self._json_help()
        
        action = params[0].upper()
        args = params[1:] if len(params) > 1 else []
        
        if action == 'VIEW' or action == 'OPEN':
            return self._json_view(args)
        elif action == 'EDIT':
            return self._json_edit(args)
        elif action == 'LOAD':
            return self._json_load(args)
        elif action == 'SAVE':
            return self._json_save(args)
        elif action == 'PATH':
            return self._json_path(args)
        elif action == 'SEARCH':
            return self._json_search(args)
        elif action == 'VALIDATE':
            return self._json_validate(args)
        elif action == 'DIFF':
            return self._json_diff(args)
        elif action == 'HELP':
            return self._json_help()
        else:
            return f"❌ Unknown JSON action: {action}"
    
    # ===== TILE Editor Methods =====
    
    def _tile_new(self) -> str:
        """Create new blank tile."""
        from dev.goblin.core.ui.tile_editor import TileEditor
        self._tile_editor = TileEditor(self.config)
        return self._tile_editor.get_static_view()
    
    def _tile_edit(self, args: List[str]) -> str:
        """Open tile editor, optionally loading file."""
        if args:
            success, msg = self.tile_editor.load_tile(args[0])
            if not success:
                return msg
        
        return self.tile_editor.get_static_view()
    
    def _tile_load(self, args: List[str]) -> str:
        """Load tile from file."""
        if not args:
            return "❌ Usage: TILE LOAD <filename>"
        
        success, msg = self.tile_editor.load_tile(args[0])
        if success:
            return f"{msg}\n\n{self.tile_editor.get_static_view()}"
        return msg
    
    def _tile_save(self, args: List[str]) -> str:
        """Save tile to file."""
        filename = args[0] if args else None
        success, msg = self.tile_editor.save_tile(filename)
        return msg
    
    def _tile_export(self, args: List[str]) -> str:
        """Export tile to format."""
        if not args:
            return "❌ Usage: TILE EXPORT <format>\n   Formats: ascii, ansi, json"
        
        fmt = args[0].lower()
        
        if fmt == 'ascii':
            return self.tile_editor.export_ascii()
        elif fmt == 'ansi':
            return self.tile_editor.export_ansi()
        elif fmt == 'json':
            data = {
                'version': '1.0',
                'size': self.tile_editor.GRID_SIZE,
                'grid': [[cell.to_dict() for cell in row] for row in self.tile_editor.grid]
            }
            return json.dumps(data, indent=2)
        else:
            return f"❌ Unknown format: {fmt}"
    
    def _tile_list(self) -> str:
        """List saved tiles."""
        tiles_dir = Path(self.config.project_root) / "memory" / "drafts" / "tiles"
        
        if not tiles_dir.exists():
            return "No tiles directory found. Use TILE NEW to create your first tile."
        
        tiles = list(tiles_dir.glob("*.json"))
        
        if not tiles:
            return "No saved tiles found."
        
        lines = ["Saved Tiles:", "─" * 40]
        for tile in sorted(tiles):
            size = tile.stat().st_size
            lines.append(f"  {tile.name:30} ({size:,} bytes)")
        
        lines.append(f"\nTotal: {len(tiles)} tiles")
        return '\n'.join(lines)
    
    def _tile_view(self, args: List[str]) -> str:
        """View tile without opening editor."""
        if not args:
            return "❌ Usage: TILE VIEW <filename>"
        
        success, msg = self.tile_editor.load_tile(args[0])
        if not success:
            return msg
        
        return self.tile_editor.export_ansi()
    
    def _tile_help(self) -> str:
        """Show tile editor help."""
        from dev.goblin.core.ui.tile_editor import get_tile_editor_help
        return get_tile_editor_help()
    
    # ===== JSON Viewer Methods =====
    
    def _json_view(self, args: List[str]) -> str:
        """View JSON file."""
        if not args:
            return "❌ Usage: JSON VIEW <filename>"
        
        success, msg = self.json_viewer.load_file(args[0])
        if not success:
            return msg
        
        return f"{msg}\n\n{self.json_viewer.render()}"
    
    def _json_edit(self, args: List[str]) -> str:
        """Edit JSON file."""
        if not args:
            return "❌ Usage: JSON EDIT <filename>"
        
        success, msg = self.json_viewer.load_file(args[0])
        if not success:
            return msg
        
        return f"{msg}\n\n{self.json_viewer.render()}"
    
    def _json_load(self, args: List[str]) -> str:
        """Load JSON file or string."""
        if not args:
            return "❌ Usage: JSON LOAD <filename|json_string>"
        
        # Try as file first
        if Path(args[0]).suffix == '.json' or not args[0].startswith('{'):
            success, msg = self.json_viewer.load_file(args[0])
        else:
            # Try as JSON string
            success, msg = self.json_viewer.load_string(' '.join(args))
        
        if success:
            return f"{msg}\n\n{self.json_viewer.render()}"
        return msg
    
    def _json_save(self, args: List[str]) -> str:
        """Save JSON to file."""
        filename = args[0] if args else None
        success, msg = self.json_viewer.save(filename)
        return msg
    
    def _json_path(self, args: List[str]) -> str:
        """Get value at JSON path."""
        if len(args) < 2:
            return "❌ Usage: JSON PATH <filename> <path>\n   Example: JSON PATH config.json server.port"
        
        # Load file if needed
        success, msg = self.json_viewer.load_file(args[0])
        if not success:
            return msg
        
        # Get value at path
        path = args[1]
        try:
            value = self._get_value_at_path(self.json_viewer.current_data, path)
            return f"Value at {path}:\n{json.dumps(value, indent=2)}"
        except Exception as e:
            return f"❌ Error: {e}"
    
    def _get_value_at_path(self, data: Any, path: str) -> Any:
        """Navigate to value at dot/bracket path."""
        parts = []
        current = ""
        in_bracket = False
        
        for char in path:
            if char == '.' and not in_bracket:
                if current:
                    parts.append(current)
                    current = ""
            elif char == '[':
                if current:
                    parts.append(current)
                    current = ""
                in_bracket = True
            elif char == ']':
                if current:
                    parts.append(int(current))
                    current = ""
                in_bracket = False
            else:
                current += char
        
        if current:
            parts.append(current)
        
        obj = data
        for part in parts:
            if isinstance(part, int):
                obj = obj[part]
            else:
                obj = obj[part]
        
        return obj
    
    def _json_search(self, args: List[str]) -> str:
        """Search within loaded JSON."""
        if not args:
            return "❌ Usage: JSON SEARCH <query>"
        
        if not self.json_viewer.root:
            return "❌ No JSON loaded. Use JSON LOAD first."
        
        query = ' '.join(args)
        self.json_viewer.search(query)
        
        if self.json_viewer.search_matches:
            return f"Found {len(self.json_viewer.search_matches)} matches.\n\n{self.json_viewer.render()}"
        else:
            return f"No matches found for: {query}"
    
    def _json_validate(self, args: List[str]) -> str:
        """Validate JSON against schema."""
        if not args:
            return "❌ Usage: JSON VALIDATE <filename> [schema_file]"
        
        # Load file
        success, msg = self.json_viewer.load_file(args[0])
        if not success:
            return msg
        
        # Load schema if provided
        if len(args) > 1:
            success, msg = self.json_viewer.load_schema(args[1])
            if not success:
                return msg
        
        # Validate
        try:
            json.dumps(self.json_viewer.current_data)
            return "✅ JSON is valid"
        except Exception as e:
            return f"❌ Invalid JSON: {e}"
    
    def _json_diff(self, args: List[str]) -> str:
        """Show diff of current changes."""
        if not self.json_viewer.root:
            return "❌ No JSON loaded. Use JSON LOAD first."
        
        diff = self.json_viewer.get_diff()
        
        if not diff or diff == ["No changes"]:
            return "No changes detected."
        
        return '\n'.join(diff)
    
    def _json_help(self) -> str:
        """Show JSON viewer help."""
        from dev.goblin.core.ui.json_viewer import get_json_viewer_help
        return get_json_viewer_help()
    
    def _show_help(self) -> str:
        """Show general editor help."""
        return """
EDITOR COMMANDS
═══════════════

TILE EDITOR (24×24 Character Art):
  TILE NEW               Create new blank tile
  TILE EDIT [file]       Open tile editor
  TILE LOAD <file>       Load tile from JSON
  TILE SAVE [file]       Save current tile
  TILE EXPORT <format>   Export (ascii|ansi|json)
  TILE LIST              List saved tiles
  TILE VIEW <file>       View tile without editing

JSON VIEWER/EDITOR:
  JSON VIEW <file>       View JSON file in tree format
  JSON EDIT <file>       Edit JSON file
  JSON PATH <file> <p>   Get value at path
  JSON SEARCH <query>    Search within JSON
  JSON VALIDATE <file>   Validate JSON
  JSON DIFF              Show changes since load

See TILE HELP or JSON HELP for detailed information.
"""
