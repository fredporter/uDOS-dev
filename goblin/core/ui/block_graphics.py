#!/usr/bin/env python3
"""
uDOS v1.3.3 - Block Graphics Generator

Python-side block graphics generation for:
- Converting ASCII panels to block characters
- Generating JSON for Tauri rendering
- NES-style mosaic pattern creation

Version: 1.3.3
Author: Fred Porter
Date: December 2025
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, List, Optional, Any, Tuple
import json


class BlockChar(Enum):
    """Unicode block characters for 2×3 pixel rendering."""
    EMPTY = ' '
    FULL = '█'
    UPPER_HALF = '▀'
    LOWER_HALF = '▄'
    LEFT_HALF = '▌'
    RIGHT_HALF = '▐'
    
    # Quadrants
    UPPER_LEFT = '▘'
    UPPER_RIGHT = '▝'
    LOWER_LEFT = '▖'
    LOWER_RIGHT = '▗'
    
    # Three-quarter blocks
    MISS_UPPER_LEFT = '▟'
    MISS_UPPER_RIGHT = '▙'
    MISS_LOWER_LEFT = '▜'
    MISS_LOWER_RIGHT = '▛'
    
    # Shades
    LIGHT_SHADE = '░'
    MEDIUM_SHADE = '▒'
    DARK_SHADE = '▓'


# Box drawing to block character mapping
BOX_TO_BLOCK: Dict[str, str] = {
    # Single line
    '┌': '▛', '┐': '▜', '└': '▙', '┘': '▟',
    '─': '▀', '│': '▌',
    '├': '▌', '┤': '▐', '┬': '▀', '┴': '▄',
    '┼': '█',
    
    # Double line
    '╔': '▛', '╗': '▜', '╚': '▙', '╝': '▟',
    '═': '▀', '║': '▌',
    '╠': '▌', '╣': '▐', '╦': '▀', '╩': '▄',
    '╬': '█',
    
    # Rounded corners
    '╭': '▛', '╮': '▜', '╰': '▙', '╯': '▟',
    
    # Heavy line
    '┏': '▛', '┓': '▜', '┗': '▙', '┛': '▟',
    '━': '▀', '┃': '▌',
    '┣': '▌', '┫': '▐', '┳': '▀', '┻': '▄',
    '╋': '█',
}


# NES-style color palette
NES_PALETTE = {
    'black': '#232323',
    'white': '#eeeeee',
    'red': '#e26f5f',
    'green': '#6fce84',
    'blue': '#5c9dd5',
    'yellow': '#f5e052',
    'cyan': '#64c8d4',
    'purple': '#b78fd5',
    'border': '#4a4a4a',
    'background': '#1a1a1a',
    'highlight': '#3a3a3a',
    'text': '#cccccc',
}


@dataclass
class BlockCell:
    """A single cell in block graphics."""
    char: str
    color: str = 'text'
    background: str = 'background'
    
    def to_dict(self) -> Dict[str, str]:
        """Convert to dictionary for JSON serialization."""
        return {
            'char': self.char,
            'color': self.color,
            'bg': self.background,
        }


@dataclass
class BlockFrame:
    """A frame of block graphics (2D grid of cells)."""
    width: int
    height: int
    cells: List[List[BlockCell]] = field(default_factory=list)
    
    def __post_init__(self):
        if not self.cells:
            self.cells = [
                [BlockCell(' ') for _ in range(self.width)]
                for _ in range(self.height)
            ]
    
    def set_cell(self, x: int, y: int, char: str, color: str = 'text') -> None:
        """Set a cell value."""
        if 0 <= x < self.width and 0 <= y < self.height:
            self.cells[y][x] = BlockCell(char, color)
    
    def get_cell(self, x: int, y: int) -> Optional[BlockCell]:
        """Get a cell value."""
        if 0 <= x < self.width and 0 <= y < self.height:
            return self.cells[y][x]
        return None
    
    def render_text(self) -> str:
        """Render frame as plain text."""
        lines = []
        for row in self.cells:
            lines.append(''.join(cell.char for cell in row))
        return '\n'.join(lines)
    
    def to_json(self) -> str:
        """Convert to JSON for Tauri."""
        data = {
            'width': self.width,
            'height': self.height,
            'cells': [[cell.to_dict() for cell in row] for row in self.cells],
        }
        return json.dumps(data)


class BlockGraphicsGenerator:
    """
    Generate block graphics from ASCII panels.
    
    Converts standard ASCII panels to NES-style block graphics
    suitable for rendering in Tauri.
    """
    
    def __init__(self):
        """Initialize the generator."""
        self.palette = NES_PALETTE.copy()
    
    def ascii_to_blocks(self, ascii_content: str) -> str:
        """
        Convert ASCII content to block characters.
        
        Args:
            ascii_content: ASCII art or panel content
            
        Returns:
            Block character string
        """
        lines = ascii_content.split('\n')
        result = []
        
        for line in lines:
            block_line = ''
            for char in line:
                block_line += self._char_to_block(char)
            result.append(block_line)
        
        return '\n'.join(result)
    
    def _char_to_block(self, char: str) -> str:
        """Convert single character to block equivalent."""
        # Check box drawing first
        if char in BOX_TO_BLOCK:
            return BOX_TO_BLOCK[char]
        
        # Already a block character
        block_chars = [bc.value for bc in BlockChar]
        if char in block_chars:
            return char
        
        # Special characters
        special = {
            '+': '█',
            '-': '▀',
            '|': '▌',
            '*': '█',
            '#': '▓',
            '=': '▀',
            ':': '▌',
        }
        return special.get(char, char)
    
    def ascii_to_frame(self, ascii_content: str) -> BlockFrame:
        """
        Convert ASCII content to BlockFrame.
        
        Args:
            ascii_content: ASCII art or panel content
            
        Returns:
            BlockFrame with colorized cells
        """
        lines = ascii_content.split('\n')
        height = len(lines)
        width = max(len(line) for line in lines) if lines else 0
        
        frame = BlockFrame(width, height)
        
        for y, line in enumerate(lines):
            for x, char in enumerate(line):
                block_char = self._char_to_block(char)
                color = self._get_char_color(char, block_char)
                frame.set_cell(x, y, block_char, color)
        
        return frame
    
    def _get_char_color(self, original: str, block: str) -> str:
        """Determine color for a character."""
        # Box drawing = border
        if original in BOX_TO_BLOCK:
            return 'border'
        
        # Status indicators
        if original in ['✅', '●']:
            return 'green'
        if original in ['⚠️', '◐']:
            return 'yellow'
        if original in ['❌', '◑']:
            return 'red'
        if original in ['ℹ️', '○']:
            return 'blue'
        
        # Block shades
        if block in ['█', '▓']:
            return 'white'
        if block in ['▀', '▄', '▌', '▐']:
            return 'highlight'
        
        return 'text'
    
    def generate_panel_json(self, 
                           panel_type: str,
                           data: Dict[str, Any],
                           width: int = 40) -> str:
        """
        Generate JSON for a specific panel type.
        
        Args:
            panel_type: Type of panel (status, progress, list, etc.)
            data: Panel data
            width: Panel width
            
        Returns:
            JSON string for Tauri rendering
        """
        if panel_type == 'status':
            ascii_content = self._build_status_panel(data, width)
        elif panel_type == 'progress':
            ascii_content = self._build_progress_panel(data, width)
        elif panel_type == 'list':
            ascii_content = self._build_list_panel(data, width)
        elif panel_type == 'alert':
            ascii_content = self._build_alert_panel(data, width)
        else:
            ascii_content = str(data)
        
        frame = self.ascii_to_frame(ascii_content)
        return frame.to_json()
    
    def _build_status_panel(self, data: Dict[str, Any], width: int) -> str:
        """Build ASCII status panel."""
        title = data.get('title', 'Status')
        items = data.get('items', {})
        
        lines = []
        
        # Top border with title
        title_text = f' {title} '
        left_pad = (width - len(title_text) - 2) // 2
        right_pad = width - len(title_text) - left_pad - 2
        lines.append('┌' + '─' * left_pad + title_text + '─' * right_pad + '┐')
        
        # Padding
        lines.append('│' + ' ' * (width - 2) + '│')
        
        # Content
        if items:
            max_key_len = max(len(k) for k in items.keys())
            for key, value in items.items():
                line = f' {key:<{max_key_len}} : {value}'
                lines.append('│' + line.ljust(width - 2) + '│')
        
        # Padding
        lines.append('│' + ' ' * (width - 2) + '│')
        
        # Bottom border
        lines.append('└' + '─' * (width - 2) + '┘')
        
        return '\n'.join(lines)
    
    def _build_progress_panel(self, data: Dict[str, Any], width: int) -> str:
        """Build ASCII progress panel."""
        title = data.get('title', 'Progress')
        value = data.get('value', 0)
        max_val = data.get('max', 100)
        
        bar_width = width - 12
        ratio = min(1.0, max(0.0, value / max_val)) if max_val > 0 else 0
        filled = int(bar_width * ratio)
        empty = bar_width - filled
        
        bar = '█' * filled + '░' * empty
        percent = f'{ratio * 100:.0f}%'
        
        lines = []
        lines.append('┌' + '─' * (width - 2) + '┐')
        lines.append('│' + f' {title}'.ljust(width - 2) + '│')
        lines.append('│' + f' [{bar}] {percent}'.ljust(width - 2) + '│')
        lines.append('└' + '─' * (width - 2) + '┘')
        
        return '\n'.join(lines)
    
    def _build_list_panel(self, data: Dict[str, Any], width: int) -> str:
        """Build ASCII list panel."""
        title = data.get('title', 'List')
        items = data.get('items', [])
        bullet = data.get('bullet', '•')
        
        lines = []
        
        # Top border with title
        title_text = f' {title} '
        left_pad = (width - len(title_text) - 2) // 2
        right_pad = width - len(title_text) - left_pad - 2
        lines.append('┌' + '─' * left_pad + title_text + '─' * right_pad + '┐')
        
        # Padding
        lines.append('│' + ' ' * (width - 2) + '│')
        
        # Items
        for item in items[:10]:  # Max 10 items
            line = f' {bullet} {item}'
            if len(line) > width - 2:
                line = line[:width - 5] + '...'
            lines.append('│' + line.ljust(width - 2) + '│')
        
        if len(items) > 10:
            lines.append('│' + f'   ... and {len(items) - 10} more'.ljust(width - 2) + '│')
        
        # Padding
        lines.append('│' + ' ' * (width - 2) + '│')
        
        # Bottom border
        lines.append('└' + '─' * (width - 2) + '┘')
        
        return '\n'.join(lines)
    
    def _build_alert_panel(self, data: Dict[str, Any], width: int) -> str:
        """Build ASCII alert panel."""
        message = data.get('message', '')
        alert_type = data.get('type', 'info')
        
        icons = {'info': 'ℹ️', 'warning': '⚠️', 'error': '❌', 'success': '✅'}
        titles = {'info': 'Info', 'warning': 'Warning', 'error': 'Error', 'success': 'Success'}
        
        icon = icons.get(alert_type, 'ℹ️')
        title = titles.get(alert_type, 'Notice')
        
        lines = []
        
        # Top border with title
        title_text = f' {title} '
        left_pad = (width - len(title_text) - 2) // 2
        right_pad = width - len(title_text) - left_pad - 2
        lines.append('╔' + '═' * left_pad + title_text + '═' * right_pad + '╗')
        
        # Padding
        lines.append('║' + ' ' * (width - 2) + '║')
        
        # Message (wrapped)
        msg_width = width - 6
        words = message.split()
        current_line = f' {icon} '
        
        for word in words:
            if len(current_line) + len(word) + 1 > msg_width:
                lines.append('║' + current_line.ljust(width - 2) + '║')
                current_line = '   ' + word
            else:
                current_line += ' ' + word if current_line.strip() else word
        
        if current_line.strip():
            lines.append('║' + current_line.ljust(width - 2) + '║')
        
        # Padding
        lines.append('║' + ' ' * (width - 2) + '║')
        
        # Bottom border
        lines.append('╚' + '═' * (width - 2) + '╝')
        
        return '\n'.join(lines)


def generate_tauri_dashboard_json(dashboard_data: Dict[str, Any]) -> str:
    """
    Generate complete dashboard JSON for Tauri.
    
    Args:
        dashboard_data: Dashboard configuration with panels
        
    Returns:
        JSON string for Tauri rendering
    """
    generator = BlockGraphicsGenerator()
    
    panels = []
    for panel_config in dashboard_data.get('panels', []):
        panel_type = panel_config.get('type', 'status')
        panel_data = panel_config.get('data', {})
        width = panel_config.get('width', 40)
        
        panel_json = generator.generate_panel_json(panel_type, panel_data, width)
        panels.append({
            'id': panel_config.get('id', ''),
            'position': panel_config.get('position', 0),
            'frame': json.loads(panel_json),
        })
    
    return json.dumps({
        'version': '1.3.3',
        'layout': dashboard_data.get('layout', 'grid'),
        'columns': dashboard_data.get('columns', 2),
        'panels': panels,
    }, indent=2)


# =============================================================================
# Module singleton
# =============================================================================

_generator: Optional[BlockGraphicsGenerator] = None


def get_block_generator() -> BlockGraphicsGenerator:
    """Get the block graphics generator singleton."""
    global _generator
    if _generator is None:
        _generator = BlockGraphicsGenerator()
    return _generator


# =============================================================================
# Test
# =============================================================================

if __name__ == "__main__":
    print("=" * 60)
    print("Block Graphics Generator Test")
    print("=" * 60)
    
    generator = BlockGraphicsGenerator()
    
    # Test ASCII to blocks
    ascii_panel = """
┌──────────── Status ────────────┐
│                                │
│ Version : 1.3.3                │
│ Mode    : Offline              │
│                                │
└────────────────────────────────┘
"""
    
    print("\nOriginal ASCII:")
    print(ascii_panel)
    
    print("\nBlock Graphics:")
    blocks = generator.ascii_to_blocks(ascii_panel)
    print(blocks)
    
    # Test JSON generation
    print("\nJSON Output (status panel):")
    json_output = generator.generate_panel_json('status', {
        'title': 'System',
        'items': {'Version': '1.3.3', 'Mode': 'Offline', 'Role': 'Ghost'},
    }, width=35)
    
    data = json.loads(json_output)
    print(f"Frame size: {data['width']}x{data['height']}")
    print(f"First line chars: {''.join(c['char'] for c in data['cells'][0][:20])}...")
    
    # Test progress panel
    print("\nProgress Panel (ASCII):")
    progress = generator._build_progress_panel({
        'title': 'Download',
        'value': 73,
        'max': 100,
    }, width=40)
    print(progress)
    
    print("\nProgress Panel (Blocks):")
    print(generator.ascii_to_blocks(progress))
    
    print("\n" + "=" * 60)
    print("✅ Block Graphics Generator working!")
