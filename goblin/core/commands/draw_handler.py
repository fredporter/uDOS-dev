"""
DRAW Command Handler - 24×24 Tile/Sprite Editor

Interactive editor for creating teletext-style character art.
Supports both TUI (terminal) and Desktop (web) modes.

Commands:
- DRAW NEW              - Create new blank tile
- DRAW EDIT [file]      - Open tile editor
- DRAW LOAD <file>      - Load tile from JSON
- DRAW SAVE [file]      - Save current tile
- DRAW EXPORT <format>  - Export (ascii|ansi|json)
- DRAW LIST             - List saved tiles
- DRAW VIEW <file>      - View tile without editing
- DRAW MAP <cmd>        - Map tile editing (v1.3.1+)

Part of uDOS v1.3.1 - Editor Suite
"""

import json
from pathlib import Path
from typing import Dict, Any, List, Optional
from dev.goblin.core.commands.base_handler import BaseCommandHandler


class DrawHandler(BaseCommandHandler):
    """Handler for DRAW (tile editor) commands."""
    
    def __init__(self, components: Dict[str, Any]):
        """Initialize draw handler with system components."""
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
        
        # Editor instance (lazy loaded)
        self._tile_editor = None
    
    @property
    def tile_editor(self):
        """Lazy load tile editor."""
        if self._tile_editor is None:
            from dev.goblin.core.ui.tile_editor import TileEditor
            self._tile_editor = TileEditor(self.config)
        return self._tile_editor
    
    @property
    def tiles_dir(self) -> Path:
        """Get tiles directory."""
        if self.config:
            return Path(self.config.project_root) / "memory" / "drafts" / "tiles"
        return Path.cwd() / "memory" / "drafts" / "tiles"
    
    def handle(self, args: List[str]) -> str:
        """Handle DRAW commands."""
        if not args:
            return self._show_help()
        
        command = args[0].upper()
        params = args[1:] if len(args) > 1 else []
        
        if command == 'NEW':
            return self._handle_new()
        elif command in ('EDIT', 'OPEN'):
            return self._handle_edit(params)
        elif command == 'LOAD':
            return self._handle_load(params)
        elif command == 'SAVE':
            return self._handle_save(params)
        elif command == 'EXPORT':
            return self._handle_export(params)
        elif command == 'LIST':
            return self._handle_list()
        elif command == 'VIEW':
            return self._handle_view(params)
        elif command == 'MAP':
            return self._handle_map(params)
        elif command == 'HELP':
            return self._show_help()
        else:
            return f"❌ Unknown DRAW command: {command}\nUse DRAW HELP for available commands."
    
    def _handle_new(self) -> str:
        """Create new blank tile."""
        from dev.goblin.core.ui.tile_editor import TileEditor
        self._tile_editor = TileEditor(self.config)
        
        output = []
        output.append("╔════════════════════════════════════════════════════════════════╗")
        output.append("║  24×24 Tile Editor - New Tile                                  ║")
        output.append("╚════════════════════════════════════════════════════════════════╝")
        output.append("")
        output.append(self.tile_editor.get_static_view())
        output.append("")
        output.append("─" * 66)
        output.append("Controls: DRAW SAVE <name> to save | DRAW EXPORT <fmt> to export")
        
        return '\n'.join(output)
    
    def _handle_edit(self, params: List[str]) -> str:
        """Open tile editor, optionally loading file."""
        if params:
            success, msg = self.tile_editor.load_tile(params[0])
            if not success:
                return msg
            title = f"Editing: {params[0]}"
        else:
            title = "New Tile"
        
        output = []
        output.append("╔════════════════════════════════════════════════════════════════╗")
        output.append(f"║  24×24 Tile Editor - {title:<43} ║")
        output.append("╚════════════════════════════════════════════════════════════════╝")
        output.append("")
        output.append(self.tile_editor.get_static_view())
        output.append("")
        output.append("─" * 66)
        output.append("Movement: 8↑ 2↓ 4← 6→ | Edit: Space=place, Del=clear | 7/9=undo/redo")
        
        return '\n'.join(output)
    
    def _handle_load(self, params: List[str]) -> str:
        """Load tile from file."""
        if not params:
            return "❌ Usage: DRAW LOAD <filename>"
        
        success, msg = self.tile_editor.load_tile(params[0])
        if success:
            output = []
            output.append(f"✅ {msg}")
            output.append("")
            output.append(self.tile_editor.get_static_view())
            return '\n'.join(output)
        return msg
    
    def _handle_save(self, params: List[str]) -> str:
        """Save tile to file."""
        filename = params[0] if params else None
        success, msg = self.tile_editor.save_tile(filename)
        return msg
    
    def _handle_export(self, params: List[str]) -> str:
        """Export tile to format."""
        if not params:
            return "❌ Usage: DRAW EXPORT <format>\n   Formats: ascii, ansi, json"
        
        fmt = params[0].lower()
        
        if fmt == 'ascii':
            output = []
            output.append("ASCII Export:")
            output.append("─" * 26)
            output.append(self.tile_editor.export_ascii())
            return '\n'.join(output)
        elif fmt == 'ansi':
            output = []
            output.append("ANSI Export (with colors):")
            output.append("─" * 26)
            output.append(self.tile_editor.export_ansi())
            return '\n'.join(output)
        elif fmt == 'json':
            data = {
                'version': '1.0',
                'type': 'tile',
                'size': self.tile_editor.GRID_SIZE,
                'grid': [[cell.to_dict() for cell in row] for row in self.tile_editor.grid]
            }
            return json.dumps(data, indent=2)
        else:
            return f"❌ Unknown format: {fmt}\n   Supported: ascii, ansi, json"
    
    def _handle_list(self) -> str:
        """List saved tiles."""
        if not self.tiles_dir.exists():
            return "No tiles directory found. Use DRAW NEW to create your first tile."
        
        tiles = list(self.tiles_dir.glob("*.json"))
        
        if not tiles:
            return "No saved tiles found. Use DRAW NEW to create one."
        
        output = []
        output.append("╔════════════════════════════════════════════════════════════════╗")
        output.append("║  Saved Tiles                                                   ║")
        output.append("╚════════════════════════════════════════════════════════════════╝")
        output.append("")
        output.append(f"  {'Name':<35} {'Size':>10}")
        output.append("  " + "─" * 47)
        
        for tile in sorted(tiles):
            size = tile.stat().st_size
            output.append(f"  {tile.stem:<35} {size:>10,} bytes")
        
        output.append("")
        output.append(f"  Total: {len(tiles)} tiles in {self.tiles_dir}")
        output.append("")
        output.append("Use: DRAW EDIT <name> to open, DRAW VIEW <name> to preview")
        
        return '\n'.join(output)
    
    def _handle_view(self, params: List[str]) -> str:
        """View tile without opening editor."""
        if not params:
            return "❌ Usage: DRAW VIEW <filename>"
        
        success, msg = self.tile_editor.load_tile(params[0])
        if not success:
            return msg
        
        output = []
        output.append(f"Preview: {params[0]}")
        output.append("═" * 26)
        output.append(self.tile_editor.export_ansi())
        output.append("═" * 26)
        
        return '\n'.join(output)
    
    def _handle_map(self, params: List[str]) -> str:
        """Handle MAP subcommands for terrain/map tile editing."""
        if not params:
            return self._show_map_help()
        
        subcmd = params[0].upper()
        subparams = params[1:] if len(params) > 1 else []
        
        # Import map tile library
        try:
            from dev.goblin.core.ui.map_tiles import get_tile_library, get_data_manager, MapTile
        except ImportError:
            return "❌ Map tile library not available (v1.3.1+ required)"
        
        if subcmd == 'LIBRARY':
            return self._map_library(subparams)
        elif subcmd == 'TERRAIN':
            return self._map_terrain(subparams)
        elif subcmd == 'MARKERS':
            return self._map_markers()
        elif subcmd == 'NETWORK':
            return self._map_network()
        elif subcmd == 'CREATE':
            return self._map_create(subparams)
        elif subcmd == 'CACHE':
            return self._map_cache(subparams)
        elif subcmd == 'HELP':
            return self._show_map_help()
        else:
            return f"❌ Unknown MAP command: {subcmd}\nUse DRAW MAP HELP for options."
    
    def _map_library(self, params: List[str]) -> str:
        """Show map tile library."""
        from dev.goblin.core.ui.map_tiles import get_tile_library
        
        library = get_tile_library()
        category = params[0].lower() if params else None
        
        tiles = library.list_tiles(category)
        
        output = []
        output.append("╔════════════════════════════════════════════════════════════════╗")
        output.append("║  Map Tile Library                                              ║")
        output.append("╚════════════════════════════════════════════════════════════════╝")
        output.append("")
        
        if category:
            output.append(f"Category: {category.upper()}")
            output.append("─" * 50)
        
        # Group by category
        categories = {}
        for tile in tiles:
            if tile.category not in categories:
                categories[tile.category] = []
            categories[tile.category].append(tile)
        
        for cat, cat_tiles in sorted(categories.items()):
            output.append(f"\n{cat.upper()} ({len(cat_tiles)} tiles):")
            output.append("  " + "─" * 48)
            for tile in cat_tiles[:10]:  # Limit display
                char = tile.data[0][0] if tile.data else ' '
                output.append(f"  {char}  {tile.id:<25} {tile.name}")
            if len(cat_tiles) > 10:
                output.append(f"  ... and {len(cat_tiles) - 10} more")
        
        output.append("")
        output.append(f"Total: {len(tiles)} tiles in {len(categories)} categories")
        output.append("Use: DRAW MAP TERRAIN <type> | DRAW MAP MARKERS | DRAW MAP NETWORK")
        
        return '\n'.join(output)
    
    def _map_terrain(self, params: List[str]) -> str:
        """Show terrain tiles or specific terrain type."""
        from dev.goblin.core.ui.map_tiles import get_tile_library, TERRAIN_PATTERNS
        
        output = []
        output.append("╔════════════════════════════════════════════════════════════════╗")
        output.append("║  Terrain Tiles                                                 ║")
        output.append("╚════════════════════════════════════════════════════════════════╝")
        output.append("")
        output.append(f"  {'Symbol':<8} {'Type':<12} {'Color':<10} Variants")
        output.append("  " + "─" * 52)
        
        for name, pattern in TERRAIN_PATTERNS.items():
            char = pattern['char']
            color = pattern.get('color', 'white')
            variants = ' '.join(pattern.get('variants', []))
            output.append(f"  {char:<8} {name:<12} {color:<10} {variants}")
        
        output.append("")
        output.append("Terrain types for map rendering. Use GEO VIEW to see the map.")
        
        return '\n'.join(output)
    
    def _map_markers(self) -> str:
        """Show marker tiles."""
        from dev.goblin.core.ui.map_tiles import MARKER_PATTERNS
        
        output = []
        output.append("╔════════════════════════════════════════════════════════════════╗")
        output.append("║  Map Marker Tiles                                              ║")
        output.append("╚════════════════════════════════════════════════════════════════╝")
        output.append("")
        output.append(f"  {'Symbol':<8} {'Type':<12} {'Color':<10}")
        output.append("  " + "─" * 32)
        
        for name, pattern in MARKER_PATTERNS.items():
            char = pattern['char']
            color = pattern.get('color', 'white')
            output.append(f"  {char:<8} {name:<12} {color:<10}")
        
        output.append("")
        output.append("Use GEO MARKER ADD <tile> <name> to place markers on map.")
        
        return '\n'.join(output)
    
    def _map_network(self) -> str:
        """Show network device tiles."""
        from dev.goblin.core.ui.map_tiles import NETWORK_PATTERNS
        
        output = []
        output.append("╔════════════════════════════════════════════════════════════════╗")
        output.append("║  Network Device Tiles                                          ║")
        output.append("╚════════════════════════════════════════════════════════════════╝")
        output.append("")
        output.append(f"  {'Symbol':<8} {'Type':<15} {'Color':<10}")
        output.append("  " + "─" * 35)
        
        for name, pattern in NETWORK_PATTERNS.items():
            char = pattern['char']
            color = pattern.get('color', 'white')
            output.append(f"  {char:<8} {name:<15} {color:<10}")
        
        output.append("")
        output.append("Network devices from MeshCore. Use GEO DEVICES to see active devices.")
        
        return '\n'.join(output)
    
    def _map_create(self, params: List[str]) -> str:
        """Create custom map tile."""
        from dev.goblin.core.ui.map_tiles import get_tile_library, MapTile
        
        if len(params) < 3:
            return "❌ Usage: DRAW MAP CREATE <id> <category> <char> [name]"
        
        tile_id = params[0]
        category = params[1].lower()
        char = params[2]
        name = params[3] if len(params) > 3 else tile_id.replace('_', ' ').title()
        
        library = get_tile_library()
        
        # Create tile
        tile = MapTile(
            id=tile_id,
            name=name,
            category=category,
            size=(1, 1),
            data=[[char]],
            metadata={'custom': True}
        )
        
        # Add and save
        if library.add_tile(tile, save=True):
            return f"✅ Created tile: {tile_id} ({char}) in category '{category}'"
        else:
            return f"❌ Failed to create tile: {tile_id}"
    
    def _map_cache(self, params: List[str]) -> str:
        """Show or manage geography data cache."""
        from dev.goblin.core.ui.map_tiles import get_data_manager
        
        manager = get_data_manager()
        
        if params and params[0].upper() == 'CLEAR':
            manager.clear_cache()
            return "✅ Geography data cache cleared"
        
        stats = manager.get_stats()
        
        output = []
        output.append("╔════════════════════════════════════════════════════════════════╗")
        output.append("║  Geography Data Cache                                          ║")
        output.append("╚════════════════════════════════════════════════════════════════╝")
        output.append("")
        output.append(f"  Cache Size:     {stats['cache_size']}/{stats['max_cache_size']} layers")
        output.append(f"  Cache Hits:     {stats['cache_hits']}")
        output.append(f"  Cache Misses:   {stats['cache_misses']}")
        output.append(f"  Layers Loaded:  {stats['layers_loaded']}")
        output.append(f"  Bytes Cached:   {stats['bytes_cached']:,}")
        output.append("")
        output.append("Use: DRAW MAP CACHE CLEAR to clear cache")
        
        return '\n'.join(output)
    
    def _show_map_help(self) -> str:
        """Show MAP subcommand help."""
        return """
╔════════════════════════════════════════════════════════════════╗
║  DRAW MAP - Map Tile Editor (v1.3.1)                           ║
╚════════════════════════════════════════════════════════════════╝

MAP COMMANDS:
  DRAW MAP LIBRARY [cat]   Show tile library (optional category filter)
  DRAW MAP TERRAIN         Show terrain tile patterns
  DRAW MAP MARKERS         Show map marker symbols
  DRAW MAP NETWORK         Show network device symbols
  DRAW MAP CREATE          Create custom map tile
  DRAW MAP CACHE           Show geography data cache stats
  DRAW MAP CACHE CLEAR     Clear the data cache
  DRAW MAP HELP            Show this help

TILE CATEGORIES:
  terrain   Ocean, land, mountain, forest, urban, etc.
  marker    City, capital, port, airport, landmark, etc.
  network   Node, gateway, sensor, repeater, etc.
  feature   River, lake, road, bridge, building, etc.

CREATE CUSTOM TILE:
  DRAW MAP CREATE <id> <category> <char> [name]
  
  Example: DRAW MAP CREATE custom_base marker ⊗ "Custom Base"

INTEGRATION:
  - Use GEO VIEW to display the map with terrain
  - Use GEO MARKER ADD to place markers
  - Use GEO DEVICES to show network overlays
  - Use MESH MAP to toggle MeshCore integration

FILES:
  System tiles: core/data/geography/tiles/
  User tiles:   memory/drafts/tiles/map/
"""
    
    def _show_help(self) -> str:
        """Show DRAW command help."""
        return """
╔════════════════════════════════════════════════════════════════╗
║  DRAW - 24×24 Tile Editor                                      ║
╚════════════════════════════════════════════════════════════════╝

COMMANDS:
  DRAW NEW                 Create new blank 24×24 tile
  DRAW EDIT [file]         Open tile editor
  DRAW LOAD <file>         Load tile from JSON file
  DRAW SAVE [file]         Save current tile to JSON
  DRAW EXPORT <format>     Export tile (ascii|ansi|json)
  DRAW LIST                List all saved tiles
  DRAW VIEW <file>         Preview tile without editing
  DRAW MAP <cmd>           Map tile commands (v1.3.1)
  DRAW HELP                Show this help

MAP COMMANDS (v1.3.1):
  DRAW MAP LIBRARY         Show map tile library
  DRAW MAP TERRAIN         Show terrain patterns
  DRAW MAP MARKERS         Show map markers
  DRAW MAP NETWORK         Show network device symbols
  DRAW MAP CREATE          Create custom map tile
  DRAW MAP CACHE           Manage data cache
  DRAW MAP HELP            Map commands help

KEYBOARD CONTROLS (in editor):
  Movement:   8=↑  2=↓  4=←  6=→  (numpad or arrows)
  Edit:       Space=place character  Del/0=clear cell
  Characters: [/]=prev/next char  Tab=change palette
  Tools:      P=pencil  L=line  R=rect  F=fill  E=eraser
  Colors:     1-8=foreground colors
  Undo/Redo:  7=undo  9=redo
  File:       Ctrl+S=save
  Exit:       Q or Esc

PALETTES:
  Block:   ░▒▓█ and box drawing characters
  ASCII:   Common ASCII art characters (!@#$%^&*...)
  Mosaic:  Teletext 2×3 pixel block characters
  Symbol:  Unicode symbols and shapes (★●◆♦...)

FORMATS:
  ascii    Plain text characters only
  ansi     Text with ANSI color codes
  json     Full data with colors and metadata

FILES:
  Tiles saved in: memory/drafts/tiles/
  Format: JSON with cell data (char, fg, bg per cell)

EXAMPLES:
  DRAW NEW                 Start with blank canvas
  DRAW EDIT logo           Open logo.json for editing
  DRAW EXPORT ascii        Export as plain ASCII art
  DRAW VIEW icon           Preview icon.json
  DRAW MAP TERRAIN         Show terrain tile patterns
  DRAW MAP CREATE camp marker ⌂ "Base Camp"
"""


def create_draw_handler(components: Dict[str, Any]) -> DrawHandler:
    """Factory function to create draw handler."""
    return DrawHandler(components)
