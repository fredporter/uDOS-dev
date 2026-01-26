"""
24×24 Tile Editor - TUI (Teletext Mode)

Interactive terminal-based tile/sprite editor for creating and editing
24×24 character art using teletext mosaic characters and ASCII.

Part of uDOS v1.2.31 - Editor Suite

Features:
- 24×24 grid editing (576 cells)
- Teletext mosaic characters (2×3 pixel blocks)
- ASCII character palette
- 8-color teletext palette (WST standard)
- Numpad navigation (8/2/4/6 for movement)
- Undo/Redo (7/9 keys)
- Copy/paste regions
- Save/load to JSON
- Export to various formats (ASCII, HTML, PNG)

Keyboard Controls:
  Movement:   8=↑  2=↓  4=←  6=→  (numpad)
  Edit:       Space=place char, Del=clear cell
  Colors:     F1-F8=foreground, Shift+F1-F8=background
  Palette:    [/]=prev/next char
  Tools:      P=pencil, L=line, R=rect, F=fill
  Undo/Redo:  7=undo, 9=redo
  File:       Ctrl+S=save, Ctrl+O=open
  Exit:       Esc or Q
"""

import json
import copy
import os
import sys
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass, field
from enum import Enum
from datetime import datetime

# Try to import termios for raw input (Unix only)
try:
    import termios
    import tty
    TERMIOS_AVAILABLE = True
except ImportError:
    TERMIOS_AVAILABLE = False


class TeletextColor(Enum):
    """WST teletext color palette."""
    BLACK = ('blk', '\033[30m', '\033[40m', '#000000')
    RED = ('red', '\033[31m', '\033[41m', '#FF0000')
    GREEN = ('grn', '\033[32m', '\033[42m', '#00FF00')
    YELLOW = ('yel', '\033[33m', '\033[43m', '#FFFF00')
    BLUE = ('blu', '\033[34m', '\033[44m', '#0000FF')
    MAGENTA = ('mag', '\033[35m', '\033[45m', '#FF00FF')
    CYAN = ('cyn', '\033[36m', '\033[46m', '#00FFFF')
    WHITE = ('wht', '\033[37m', '\033[47m', '#FFFFFF')
    
    @property
    def code(self) -> str:
        return self.value[0]
    
    @property
    def fg_ansi(self) -> str:
        return self.value[1]
    
    @property
    def bg_ansi(self) -> str:
        return self.value[2]
    
    @property
    def hex_color(self) -> str:
        return self.value[3]


class EditTool(Enum):
    """Available editing tools."""
    PENCIL = "pencil"   # Single cell edit
    LINE = "line"       # Draw line between two points
    RECT = "rect"       # Draw rectangle
    FILL = "fill"       # Flood fill
    ERASER = "eraser"   # Clear cells
    SELECT = "select"   # Select region


@dataclass
class Cell:
    """Single cell in the tile grid."""
    char: str = ' '
    fg_color: TeletextColor = TeletextColor.WHITE
    bg_color: TeletextColor = TeletextColor.BLACK
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'char': self.char,
            'fg': self.fg_color.name,
            'bg': self.bg_color.name
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Cell':
        return cls(
            char=data.get('char', ' '),
            fg_color=TeletextColor[data.get('fg', 'WHITE')],
            bg_color=TeletextColor[data.get('bg', 'BLACK')]
        )


@dataclass
class TileState:
    """Complete tile state for undo/redo."""
    grid: List[List[Cell]]
    cursor_x: int
    cursor_y: int
    timestamp: str


class CharacterPalette:
    """Character palette for tile editing."""
    
    # Teletext mosaic characters (2×3 pixel blocks)
    MOSAIC_CHARS = [
        ' ', '🬀', '🬁', '🬂', '🬃', '🬄', '🬅', '🬆',
        '🬇', '🬈', '🬉', '🬊', '🬋', '🬌', '🬍', '🬎',
        '🬏', '🬐', '🬑', '🬒', '🬓', '▌', '🬔', '🬕',
        '🬖', '🬗', '🬘', '🬙', '🬚', '🬛', '🬜', '🬝',
        '🬞', '🬟', '🬠', '🬡', '🬢', '🬣', '🬤', '🬥',
        '🬦', '🬧', '▐', '🬨', '🬩', '🬪', '🬫', '🬬',
        '🬭', '🬮', '🬯', '🬰', '🬱', '🬲', '🬳', '🬴',
        '🬵', '🬶', '🬷', '🬸', '🬹', '🬺', '🬻', '█'
    ]
    
    # ASCII block characters
    BLOCK_CHARS = [
        ' ', '░', '▒', '▓', '█',
        '▀', '▄', '▌', '▐',
        '┌', '┐', '└', '┘',
        '─', '│', '┬', '┴',
        '├', '┤', '┼',
        '╔', '╗', '╚', '╝',
        '═', '║', '╬',
    ]
    
    # Common ASCII art characters
    ASCII_CHARS = [
        ' ', '.', ':', '-', '=', '+', '*', '#',
        '@', 'O', '0', 'X', '/', '\\', '|', '_',
        '(', ')', '[', ']', '{', '}', '<', '>',
    ]
    
    # Symbols and special characters
    SYMBOL_CHARS = [
        '●', '○', '◉', '◎', '◐', '◑', '◒', '◓',
        '★', '☆', '♠', '♣', '♥', '♦',
        '▲', '▼', '◀', '▶', '△', '▽', '◁', '▷',
        '⊚', '⊕', '⊗', '⊙', '⊘',
    ]
    
    def __init__(self):
        self.palettes = {
            'mosaic': self.MOSAIC_CHARS,
            'block': self.BLOCK_CHARS,
            'ascii': self.ASCII_CHARS,
            'symbol': self.SYMBOL_CHARS,
        }
        self.current_palette = 'block'
        self.current_index = 0
    
    @property
    def current_chars(self) -> List[str]:
        return self.palettes[self.current_palette]
    
    @property
    def current_char(self) -> str:
        return self.current_chars[self.current_index]
    
    def next_char(self):
        self.current_index = (self.current_index + 1) % len(self.current_chars)
    
    def prev_char(self):
        self.current_index = (self.current_index - 1) % len(self.current_chars)
    
    def next_palette(self):
        names = list(self.palettes.keys())
        idx = names.index(self.current_palette)
        self.current_palette = names[(idx + 1) % len(names)]
        self.current_index = 0
    
    def set_char(self, char: str):
        """Set specific character."""
        for name, chars in self.palettes.items():
            if char in chars:
                self.current_palette = name
                self.current_index = chars.index(char)
                return


class TileEditor:
    """24×24 Tile Editor for terminal (TUI mode)."""
    
    GRID_SIZE = 24
    
    # ANSI escape codes
    RESET = '\033[0m'
    CLEAR_SCREEN = '\033[2J'
    CURSOR_HOME = '\033[H'
    HIDE_CURSOR = '\033[?25l'
    SHOW_CURSOR = '\033[?25h'
    
    def __init__(self, config=None):
        self.config = config
        self.project_root = Path(config.project_root) if config else Path.cwd()
        
        # Grid state
        self.grid: List[List[Cell]] = self._create_empty_grid()
        
        # Cursor position
        self.cursor_x = 0
        self.cursor_y = 0
        
        # Edit state
        self.current_tool = EditTool.PENCIL
        self.fg_color = TeletextColor.WHITE
        self.bg_color = TeletextColor.BLACK
        self.palette = CharacterPalette()
        
        # Undo/Redo stacks
        self.undo_stack: List[TileState] = []
        self.redo_stack: List[TileState] = []
        
        # Selection
        self.selection_start: Optional[Tuple[int, int]] = None
        self.selection_end: Optional[Tuple[int, int]] = None
        self.clipboard: Optional[List[List[Cell]]] = None
        
        # File info
        self.current_file: Optional[str] = None
        self.modified = False
        
        # UI state
        self.running = False
        self.message = ""
        self.show_grid_lines = True
        self.show_status = True
    
    def _create_empty_grid(self) -> List[List[Cell]]:
        """Create empty 24×24 grid."""
        return [[Cell() for _ in range(self.GRID_SIZE)] for _ in range(self.GRID_SIZE)]
    
    def _save_state(self):
        """Save current state for undo."""
        state = TileState(
            grid=[[copy.deepcopy(cell) for cell in row] for row in self.grid],
            cursor_x=self.cursor_x,
            cursor_y=self.cursor_y,
            timestamp=datetime.now().isoformat()
        )
        self.undo_stack.append(state)
        self.redo_stack.clear()  # Clear redo on new edit
        
        # Limit undo stack size
        if len(self.undo_stack) > 100:
            self.undo_stack.pop(0)
    
    def undo(self) -> bool:
        """Undo last action."""
        if not self.undo_stack:
            self.message = "Nothing to undo"
            return False
        
        # Save current state to redo
        current = TileState(
            grid=[[copy.deepcopy(cell) for cell in row] for row in self.grid],
            cursor_x=self.cursor_x,
            cursor_y=self.cursor_y,
            timestamp=datetime.now().isoformat()
        )
        self.redo_stack.append(current)
        
        # Restore previous state
        state = self.undo_stack.pop()
        self.grid = state.grid
        self.cursor_x = state.cursor_x
        self.cursor_y = state.cursor_y
        
        self.message = "Undo"
        return True
    
    def redo(self) -> bool:
        """Redo undone action."""
        if not self.redo_stack:
            self.message = "Nothing to redo"
            return False
        
        # Save current state to undo
        current = TileState(
            grid=[[copy.deepcopy(cell) for cell in row] for row in self.grid],
            cursor_x=self.cursor_x,
            cursor_y=self.cursor_y,
            timestamp=datetime.now().isoformat()
        )
        self.undo_stack.append(current)
        
        # Restore redo state
        state = self.redo_stack.pop()
        self.grid = state.grid
        self.cursor_x = state.cursor_x
        self.cursor_y = state.cursor_y
        
        self.message = "Redo"
        return True
    
    def move_cursor(self, dx: int, dy: int):
        """Move cursor with wrapping."""
        self.cursor_x = (self.cursor_x + dx) % self.GRID_SIZE
        self.cursor_y = (self.cursor_y + dy) % self.GRID_SIZE
    
    def place_char(self, char: str = None):
        """Place character at cursor position."""
        self._save_state()
        
        cell = self.grid[self.cursor_y][self.cursor_x]
        cell.char = char if char else self.palette.current_char
        cell.fg_color = self.fg_color
        cell.bg_color = self.bg_color
        
        self.modified = True
    
    def clear_cell(self):
        """Clear cell at cursor position."""
        self._save_state()
        
        cell = self.grid[self.cursor_y][self.cursor_x]
        cell.char = ' '
        cell.fg_color = TeletextColor.WHITE
        cell.bg_color = TeletextColor.BLACK
        
        self.modified = True
    
    def flood_fill(self, start_x: int, start_y: int, new_char: str = None,
                   new_fg: TeletextColor = None, new_bg: TeletextColor = None):
        """Flood fill from point."""
        self._save_state()
        
        target_cell = self.grid[start_y][start_x]
        target_char = target_cell.char
        target_fg = target_cell.fg_color
        target_bg = target_cell.bg_color
        
        fill_char = new_char if new_char else self.palette.current_char
        fill_fg = new_fg if new_fg else self.fg_color
        fill_bg = new_bg if new_bg else self.bg_color
        
        # Don't fill if target is same as fill
        if target_char == fill_char and target_fg == fill_fg and target_bg == fill_bg:
            return
        
        # BFS flood fill
        stack = [(start_x, start_y)]
        visited = set()
        
        while stack:
            x, y = stack.pop()
            
            if (x, y) in visited:
                continue
            if x < 0 or x >= self.GRID_SIZE or y < 0 or y >= self.GRID_SIZE:
                continue
            
            cell = self.grid[y][x]
            if cell.char != target_char or cell.fg_color != target_fg or cell.bg_color != target_bg:
                continue
            
            visited.add((x, y))
            cell.char = fill_char
            cell.fg_color = fill_fg
            cell.bg_color = fill_bg
            
            stack.extend([(x+1, y), (x-1, y), (x, y+1), (x, y-1)])
        
        self.modified = True
        self.message = f"Filled {len(visited)} cells"
    
    def draw_line(self, x1: int, y1: int, x2: int, y2: int):
        """Draw line using Bresenham's algorithm."""
        self._save_state()
        
        dx = abs(x2 - x1)
        dy = abs(y2 - y1)
        sx = 1 if x1 < x2 else -1
        sy = 1 if y1 < y2 else -1
        err = dx - dy
        
        x, y = x1, y1
        count = 0
        
        while True:
            if 0 <= x < self.GRID_SIZE and 0 <= y < self.GRID_SIZE:
                cell = self.grid[y][x]
                cell.char = self.palette.current_char
                cell.fg_color = self.fg_color
                cell.bg_color = self.bg_color
                count += 1
            
            if x == x2 and y == y2:
                break
            
            e2 = 2 * err
            if e2 > -dy:
                err -= dy
                x += sx
            if e2 < dx:
                err += dx
                y += sy
        
        self.modified = True
        self.message = f"Line: {count} cells"
    
    def draw_rect(self, x1: int, y1: int, x2: int, y2: int, filled: bool = False):
        """Draw rectangle."""
        self._save_state()
        
        min_x, max_x = min(x1, x2), max(x1, x2)
        min_y, max_y = min(y1, y2), max(y1, y2)
        count = 0
        
        for y in range(min_y, max_y + 1):
            for x in range(min_x, max_x + 1):
                if 0 <= x < self.GRID_SIZE and 0 <= y < self.GRID_SIZE:
                    # Only draw borders if not filled
                    if filled or x == min_x or x == max_x or y == min_y or y == max_y:
                        cell = self.grid[y][x]
                        cell.char = self.palette.current_char
                        cell.fg_color = self.fg_color
                        cell.bg_color = self.bg_color
                        count += 1
        
        self.modified = True
        self.message = f"Rect: {count} cells"
    
    def save_tile(self, filepath: str = None) -> Tuple[bool, str]:
        """Save tile to JSON file."""
        try:
            save_path = filepath or self.current_file
            if not save_path:
                return False, "No filename specified"
            
            # Resolve path
            if not os.path.isabs(save_path):
                save_path = self.project_root / "memory" / "drafts" / "tiles" / save_path
            
            # Ensure directory exists
            Path(save_path).parent.mkdir(parents=True, exist_ok=True)
            
            # Build data
            data = {
                'version': '1.0',
                'size': self.GRID_SIZE,
                'created': datetime.now().isoformat(),
                'grid': [[cell.to_dict() for cell in row] for row in self.grid]
            }
            
            # Save
            with open(save_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2)
            
            self.current_file = str(save_path)
            self.modified = False
            
            return True, f"Saved: {save_path}"
        
        except Exception as e:
            return False, f"Error saving: {e}"
    
    def load_tile(self, filepath: str) -> Tuple[bool, str]:
        """Load tile from JSON file."""
        try:
            # Resolve path
            if not os.path.isabs(filepath):
                filepath = self.project_root / "memory" / "drafts" / "tiles" / filepath
            
            with open(filepath, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            # Validate
            if data.get('size', 0) != self.GRID_SIZE:
                return False, f"Wrong grid size (expected {self.GRID_SIZE})"
            
            # Load grid
            self._save_state()  # Allow undo of load
            
            for y, row_data in enumerate(data.get('grid', [])):
                for x, cell_data in enumerate(row_data):
                    if y < self.GRID_SIZE and x < self.GRID_SIZE:
                        self.grid[y][x] = Cell.from_dict(cell_data)
            
            self.current_file = str(filepath)
            self.modified = False
            
            return True, f"Loaded: {filepath}"
        
        except FileNotFoundError:
            return False, f"File not found: {filepath}"
        except json.JSONDecodeError as e:
            return False, f"Invalid JSON: {e}"
        except Exception as e:
            return False, f"Error loading: {e}"
    
    def export_ascii(self) -> str:
        """Export tile as plain ASCII text."""
        lines = []
        for row in self.grid:
            line = ''.join(cell.char for cell in row)
            lines.append(line)
        return '\n'.join(lines)
    
    def export_ansi(self) -> str:
        """Export tile with ANSI colors."""
        lines = []
        for row in self.grid:
            line_parts = []
            for cell in row:
                line_parts.append(f"{cell.fg_color.fg_ansi}{cell.bg_color.bg_ansi}{cell.char}{self.RESET}")
            lines.append(''.join(line_parts))
        return '\n'.join(lines)
    
    def render(self) -> str:
        """Render editor view for terminal."""
        output = []
        
        # Header
        output.append(f"{'─' * 50}")
        output.append(f"  24×24 TILE EDITOR {'- ' + Path(self.current_file).name if self.current_file else '- [Untitled]'}")
        output.append(f"  Tool: {self.current_tool.value} | Char: [{self.palette.current_char}] | FG: {self.fg_color.code} | BG: {self.bg_color.code}")
        output.append(f"{'─' * 50}")
        
        # Grid with border
        output.append("  ┌" + "─" * (self.GRID_SIZE + 2) + "┐")
        
        for y, row in enumerate(self.grid):
            line_parts = [" "]
            
            for x, cell in enumerate(row):
                # Highlight cursor
                if x == self.cursor_x and y == self.cursor_y:
                    # Invert colors for cursor
                    line_parts.append(f"\033[7m{cell.char}\033[27m")
                else:
                    line_parts.append(f"{cell.fg_color.fg_ansi}{cell.bg_color.bg_ansi}{cell.char}{self.RESET}")
            
            output.append("  │" + ''.join(line_parts) + " │")
        
        output.append("  └" + "─" * (self.GRID_SIZE + 2) + "┘")
        
        # Status bar
        output.append(f"  Pos: ({self.cursor_x:2d},{self.cursor_y:2d}) | Undo: {len(self.undo_stack)} | Modified: {'*' if self.modified else '-'}")
        
        # Message
        if self.message:
            output.append(f"  {self.message}")
        
        # Help
        output.append("")
        output.append("  8/2/4/6=move | Space=place | Del=clear | [/]=char | 7=undo | 9=redo")
        output.append("  P=pencil | L=line | R=rect | F=fill | Tab=palette | Q=quit")
        
        return '\n'.join(output)
    
    def get_static_view(self) -> str:
        """Get static view for non-interactive display."""
        return self.render()
    
    def handle_key(self, key: str) -> bool:
        """Handle keyboard input. Returns False to exit."""
        self.message = ""
        
        # Movement (numpad style)
        if key == '8' or key == 'up':
            self.move_cursor(0, -1)
        elif key == '2' or key == 'down':
            self.move_cursor(0, 1)
        elif key == '4' or key == 'left':
            self.move_cursor(-1, 0)
        elif key == '6' or key == 'right':
            self.move_cursor(1, 0)
        
        # Undo/Redo
        elif key == '7':
            self.undo()
        elif key == '9':
            self.redo()
        
        # Place/Clear
        elif key == ' ':
            self.place_char()
        elif key == 'delete' or key == 'backspace' or key == '0':
            self.clear_cell()
        
        # Character selection
        elif key == '[' or key == '-':
            self.palette.prev_char()
            self.message = f"Char: {self.palette.current_char}"
        elif key == ']' or key == '=':
            self.palette.next_char()
            self.message = f"Char: {self.palette.current_char}"
        elif key == '\t':
            self.palette.next_palette()
            self.message = f"Palette: {self.palette.current_palette}"
        
        # Tools
        elif key.lower() == 'p':
            self.current_tool = EditTool.PENCIL
            self.message = "Tool: Pencil"
        elif key.lower() == 'l':
            self.current_tool = EditTool.LINE
            self.message = "Tool: Line (mark start with Enter, end with Space)"
        elif key.lower() == 'r':
            self.current_tool = EditTool.RECT
            self.message = "Tool: Rectangle (mark start with Enter, end with Space)"
        elif key.lower() == 'f':
            self.flood_fill(self.cursor_x, self.cursor_y)
        elif key.lower() == 'e':
            self.current_tool = EditTool.ERASER
            self.message = "Tool: Eraser"
        
        # Colors (1-8 for foreground)
        elif key in '12345678':
            colors = list(TeletextColor)
            self.fg_color = colors[int(key) - 1]
            self.message = f"FG: {self.fg_color.code}"
        
        # Exit
        elif key.lower() == 'q' or key == 'escape':
            return False
        
        return True


# Convenience function for command handler
def create_tile_editor(config=None) -> TileEditor:
    """Create a new tile editor instance."""
    return TileEditor(config)


def get_tile_editor_help() -> str:
    """Get help text for tile editor."""
    return """
24×24 TILE EDITOR
═════════════════

A terminal-based tile/sprite editor for creating 24×24 character art.

COMMANDS:
  TILE EDIT [file]          Open editor (optionally load file)
  TILE NEW                  Create new blank tile
  TILE LOAD <file>          Load tile from JSON
  TILE SAVE [file]          Save current tile
  TILE EXPORT <format>      Export (ascii|ansi|html)
  TILE LIST                 List saved tiles

KEYBOARD CONTROLS:
  Movement:   8=↑  2=↓  4=←  6=→  (or arrow keys)
  Edit:       Space=place  Del/0=clear
  Characters: [/]=prev/next char  Tab=change palette
  Tools:      P=pencil  L=line  R=rect  F=fill  E=eraser
  Colors:     1-8=foreground colors
  Undo/Redo:  7=undo  9=redo
  File:       Ctrl+S=save
  Exit:       Q or Esc

PALETTES:
  - Block:  ░▒▓█ and box drawing
  - ASCII:  Common ASCII art characters
  - Mosaic: Teletext 2×3 mosaic characters
  - Symbol: Unicode symbols and shapes

FILES:
  Tiles are saved as JSON in memory/drafts/tiles/
"""
