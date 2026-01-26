#!/usr/bin/env python3
"""
uDOS Grid Renderer - Text-based grid display system for Layers 600-650

Provides foundation for MeshCore networking (Layer 600-619) and Sonic Screwdriver
firmware provisioning (Layer 650) visualizations using 12-character column system.

Features:
- 12-character base column width with 1-space gutters
- 4 viewport tiers: Compact (40), Standard (80), Wide (120), Ultra (160)
- Text symbol library for devices, signal, status, and routing
- Grid cell formatting with TILE+device notation
- Template-based rendering for complex layouts

Version: v1.2.14
Author: Fred Porter
Date: December 7, 2025
"""

from enum import Enum
from typing import List, Dict, Tuple, Optional, Union
from dataclasses import dataclass
from dev.goblin.core.ui.components.box_drawing import (
    render_section,
    render_box as draw_box,
    BoxStyle,
    get_box_chars,
)
from dev.goblin.core.ui.components.progress_bar import FULL_BLOCK, EMPTY_BLOCK


# Grid Constants
COLUMN_WIDTH = 12  # Base column width in characters
GUTTER_WIDTH = 1  # Space between columns


class ViewportTier(Enum):
    """Viewport size tiers with column capacity."""

    COMPACT = (40, 3)  # (total_width, num_columns)
    STANDARD = (80, 6)
    WIDE = (120, 9)
    ULTRA = (160, 12)

    @property
    def width(self) -> int:
        """Total viewport width in characters."""
        return self.value[0]

    @property
    def columns(self) -> int:
        """Number of grid columns that fit."""
        return self.value[1]

    @classmethod
    def from_width(cls, width: int) -> "ViewportTier":
        """Auto-detect viewport tier from terminal width."""
        if width < 60:
            return cls.COMPACT
        elif width < 100:
            return cls.STANDARD
        elif width < 140:
            return cls.WIDE
        else:
            return cls.ULTRA


# Text Symbol Library
class Symbols:
    """Unicode symbols for grid rendering."""

    # Device Types
    NODE = "⊚"  # U+229A - Primary node/hub
    GATEWAY = "⊕"  # U+2295 - Gateway/router
    SENSOR = "⊗"  # U+2297 - Sensor/monitor
    REPEATER = "⊙"  # U+2299 - Repeater/relay
    END_DEVICE = "⊘"  # U+2298 - End device/client

    # Signal Strength (Block characters)
    SIGNAL_100 = "█"  # U+2588 - Full block (100%)
    SIGNAL_75 = "▓"  # U+2593 - Dark shade (75%)
    SIGNAL_50 = "▒"  # U+2592 - Medium shade (50%)
    SIGNAL_25 = "░"  # U+2591 - Light shade (25%)
    SIGNAL_00 = " "  # Empty/no signal

    # Status Indicators
    ONLINE = "●"  # U+25CF - Active/online
    OFFLINE = "○"  # U+25CB - Inactive/offline
    CONNECTING = "◐"  # U+25D0 - Transitioning
    ERROR = "◑"  # U+25D1 - Error/warning

    # Box Drawing (Light)
    H_LINE = "─"  # U+2500 - Horizontal line
    V_LINE = "│"  # U+2502 - Vertical line
    TL_CORNER = "┌"  # U+250C - Top-left corner
    TR_CORNER = "┐"  # U+2510 - Top-right corner
    BL_CORNER = "└"  # U+2514 - Bottom-left corner
    BR_CORNER = "┘"  # U+2518 - Bottom-right corner
    T_LEFT = "├"  # U+251C - T junction left
    T_RIGHT = "┤"  # U+2524 - T junction right
    T_TOP = "┬"  # U+252C - T junction top
    T_BOTTOM = "┴"  # U+2534 - T junction bottom
    CROSS = "┼"  # U+253C - Cross junction

    # Box Drawing (Double)
    H_LINE_DBL = "═"  # U+2550 - Double horizontal
    V_LINE_DBL = "║"  # U+2551 - Double vertical
    TL_CORNER_DBL = "╔"  # U+2554
    TR_CORNER_DBL = "╗"  # U+2557
    BL_CORNER_DBL = "╚"  # U+255A
    BR_CORNER_DBL = "╝"  # U+255D

    # Box Drawing (Heavy)
    H_LINE_HVY = "━"  # U+2501 - Heavy horizontal
    V_LINE_HVY = "┃"  # U+2503 - Heavy vertical

    # Firmware Status
    CHECK = "✓"  # U+2713 - Success/current
    CROSS = "✗"  # U+2717 - Failure/outdated
    WARNING = "⚠"  # U+26A0 - Warning/previous

    @classmethod
    def signal_bar(cls, percentage: int, length: int = 10) -> str:
        """Generate signal strength bar."""
        if percentage < 0 or percentage > 100:
            raise ValueError(f"Percentage must be 0-100, got {percentage}")

        filled = int((percentage / 100) * length)
        empty = length - filled

        return cls.SIGNAL_100 * filled + cls.SIGNAL_25 * empty

    @classmethod
    def signal_gradient(cls, percentage: int) -> str:
        """Get appropriate signal block for percentage."""
        if percentage >= 88:
            return cls.SIGNAL_100
        elif percentage >= 63:
            return cls.SIGNAL_75
        elif percentage >= 38:
            return cls.SIGNAL_50
        elif percentage > 0:
            return cls.SIGNAL_25
        else:
            return cls.SIGNAL_00


@dataclass
class GridCell:
    """Single grid cell with TILE and optional device."""

    tile: str  # TILE code (e.g., "AA340")
    layer: int  # Layer number (600-650)
    device: Optional[str] = None  # Device ID (e.g., "D1")
    content: str = ""  # Cell content
    symbol: str = ""  # Device symbol (⊚⊕⊗⊙⊘)
    status: str = ""  # Status indicator (●○◐◑)
    value: str = ""  # Numeric/percentage value

    @property
    def full_code(self) -> str:
        """Generate full TILE+device code."""
        base = f"{self.tile}-{self.layer}"
        if self.device:
            return f"{base}-{self.device}"
        return base

    def __str__(self) -> str:
        """Render cell as 12-character string."""
        if not self.content:
            # Auto-generate from components
            parts = []
            if self.symbol:
                parts.append(self.symbol)
            if self.device:
                parts.append(self.device)
            if self.status:
                parts.append(self.status)
            if self.value:
                parts.append(self.value)

            self.content = " ".join(parts) if parts else self.tile

        # Pad or truncate to COLUMN_WIDTH
        if len(self.content) > COLUMN_WIDTH:
            return self.content[:COLUMN_WIDTH]
        else:
            return self.content.ljust(COLUMN_WIDTH)


class GridRenderer:
    """Text-based grid renderer for Layers 600-650."""

    def __init__(self, viewport: ViewportTier = ViewportTier.STANDARD):
        """
        Initialize grid renderer.

        Args:
            viewport: Viewport tier determining column count
        """
        self.viewport = viewport
        self.cells: List[List[GridCell]] = []
        self.header: Optional[str] = None
        self.footer: Optional[str] = None

    def set_viewport(self, tier: ViewportTier) -> None:
        """Change viewport tier."""
        self.viewport = tier

    def create_grid(self, rows: int, cols: Optional[int] = None) -> None:
        """
        Create empty grid structure.

        Args:
            rows: Number of grid rows
            cols: Number of columns (defaults to viewport columns)
        """
        if cols is None:
            cols = self.viewport.columns

        self.cells = []
        for _ in range(rows):
            row = []
            for _ in range(cols):
                row.append(GridCell(tile="", layer=600))
            self.cells.append(row)

    def set_cell(self, row: int, col: int, cell: GridCell) -> None:
        """Set cell at specific position."""
        if 0 <= row < len(self.cells) and 0 <= col < len(self.cells[0]):
            self.cells[row][col] = cell
        else:
            raise IndexError(f"Cell position ({row}, {col}) out of bounds")

    def get_cell(self, row: int, col: int) -> Optional[GridCell]:
        """Get cell at specific position."""
        if 0 <= row < len(self.cells) and 0 <= col < len(self.cells[0]):
            return self.cells[row][col]
        return None

    def render(self, border: bool = False) -> str:
        """
        Render grid as text string.

        Args:
            border: Add border around grid

        Returns:
            Formatted grid string
        """
        if not self.cells:
            return ""

        lines = []

        # Header (standardized)
        if self.header:
            # Compute content width based on current grid size
            width = (COLUMN_WIDTH * len(self.cells[0])) + (
                GUTTER_WIDTH * (len(self.cells[0]) - 1)
            )
            section = render_section(
                self.header, width=width, style=BoxStyle.SINGLE, align="center"
            )
            lines.extend(section.splitlines())

        # Border top
        if border:
            lines.append(self._render_border_top())

        # Grid rows
        for row in self.cells:
            line = self._render_row(row, border)
            lines.append(line)

        # Border bottom
        if border:
            lines.append(self._render_border_bottom())

        # Footer
        if self.footer:
            lines.append(self.footer)

        return "\n".join(lines)

    def _render_row(self, row: List[GridCell], border: bool = False) -> str:
        """Render single row with gutters."""
        cells_str = []
        for cell in row:
            cells_str.append(str(cell))

        # Join with gutters
        gutter = " " * GUTTER_WIDTH
        row_str = gutter.join(cells_str)

        # Add borders if requested
        if border:
            chars = get_box_chars(BoxStyle.SINGLE)
            return f"{chars.vertical} {row_str} {chars.vertical}"

        return row_str

    def _render_border_top(self) -> str:
        """Render top border."""
        width = (
            (COLUMN_WIDTH * len(self.cells[0]))
            + (GUTTER_WIDTH * (len(self.cells[0]) - 1))
            + 2
        )
        chars = get_box_chars(BoxStyle.SINGLE)
        return chars.top_left + (chars.horizontal * width) + chars.top_right

    def _render_border_bottom(self) -> str:
        """Render bottom border."""
        width = (
            (COLUMN_WIDTH * len(self.cells[0]))
            + (GUTTER_WIDTH * (len(self.cells[0]) - 1))
            + 2
        )
        chars = get_box_chars(BoxStyle.SINGLE)
        return chars.bottom_left + (chars.horizontal * width) + chars.bottom_right

    def render_box(
        self, title: str, content: List[str], double_border: bool = False
    ) -> str:
        """
        Render content in bordered box using canonical box_drawing helper.

        Args:
            title: Box title
            content: List of content lines
            double_border: Use double-line border

        Returns:
            Formatted box string
        """
        max_width = max(
            len(title), max(len(line) for line in content) if content else 0
        )
        width = max_width + 2
        style = BoxStyle.DOUBLE if double_border else BoxStyle.SINGLE
        box = draw_box(
            [title] + content, width=width, style=style, padding=0, align="left"
        )
        return box

    def render_progress_bar(
        self, percentage: int, width: int = 12, label: str = ""
    ) -> str:
        """
        Render progress bar.

        Args:
            percentage: 0-100 completion percentage
            width: Bar width in characters
            label: Optional label

        Returns:
            Formatted progress bar
        """
        pct = max(0, min(100, percentage))
        filled = int((pct / 100) * width)
        bar = FULL_BLOCK * filled + EMPTY_BLOCK * (width - filled)
        result = f"[{bar}]"

        if label:
            result = f"{label.ljust(25)} {result} {percentage}%"

        return result

    def auto_scale_to_terminal(self, terminal_width: int) -> None:
        """Auto-detect and set viewport tier from terminal width."""
        self.viewport = ViewportTier.from_width(terminal_width)


def demo_grid_rendering():
    """Demonstration of grid rendering capabilities."""

    print("=" * 80)
    print("uDOS Grid Renderer Demo - v1.2.14")
    print("=" * 80)
    print()

    # Demo 1: Basic grid with devices
    print("Demo 1: MeshCore Device Grid (Standard Viewport)")
    print("-" * 80)

    renderer = GridRenderer(ViewportTier.STANDARD)
    renderer.create_grid(3, 6)

    # Row 1
    renderer.set_cell(
        0,
        0,
        GridCell(
            tile="AA340",
            layer=600,
            device="D1",
            symbol=Symbols.NODE,
            status=Symbols.ONLINE,
            value="82%",
        ),
    )
    renderer.set_cell(
        0,
        1,
        GridCell(
            tile="AB340",
            layer=600,
            device="D2",
            symbol=Symbols.GATEWAY,
            status=Symbols.ONLINE,
            value="76%",
        ),
    )
    renderer.set_cell(0, 2, GridCell(tile="AC340", layer=600, content="░░░░"))
    renderer.set_cell(
        0,
        3,
        GridCell(
            tile="AD340",
            layer=600,
            device="D3",
            symbol=Symbols.SENSOR,
            status=Symbols.ONLINE,
            value="91%",
        ),
    )

    # Row 2
    renderer.set_cell(
        1,
        0,
        GridCell(
            tile="AA341",
            layer=600,
            device="D4",
            symbol=Symbols.REPEATER,
            status=Symbols.OFFLINE,
            value="0%",
        ),
    )
    renderer.set_cell(
        1,
        4,
        GridCell(
            tile="AE341",
            layer=600,
            device="D5",
            symbol=Symbols.END_DEVICE,
            status=Symbols.ONLINE,
            value="68%",
        ),
    )

    renderer.header = "Layer 600 - MeshCore Network Topology"
    renderer.footer = f"Legend: {Symbols.NODE}=Node {Symbols.GATEWAY}=Gateway {Symbols.SENSOR}=Sensor {Symbols.REPEATER}=Repeater {Symbols.END_DEVICE}=End"

    print(renderer.render(border=True))
    print()

    # Demo 2: Signal heatmap
    print("Demo 2: Signal Strength Heatmap")
    print("-" * 80)

    renderer2 = GridRenderer(ViewportTier.STANDARD)
    renderer2.create_grid(4, 6)

    signal_data = [
        [100, 88, 66, 44, 22, 0],
        [88, 100, 88, 66, 44, 22],
        [66, 88, 100, 88, 66, 44],
        [44, 66, 88, 100, 88, 66],
    ]

    for row_idx, row_data in enumerate(signal_data):
        for col_idx, signal in enumerate(row_data):
            bar = Symbols.signal_bar(signal, 4)
            renderer2.set_cell(
                row_idx,
                col_idx,
                GridCell(
                    tile=f"{chr(65+col_idx)}{340+row_idx}", layer=600, content=bar
                ),
            )

    renderer2.header = "Signal Coverage Grid (100%-0%)"
    print(renderer2.render())
    print()

    # Demo 3: Progress indicator
    print("Demo 3: Firmware Flash Progress")
    print("-" * 80)

    renderer3 = GridRenderer()

    steps = [
        ("Verifying signature...", 100, Symbols.CHECK),
        ("Erasing Bank B...", 100, Symbols.CHECK),
        ("Writing firmware...", 76, ""),
        ("Validating...", 0, ""),
        ("Health check...", 0, ""),
    ]

    content_lines = []
    for label, pct, status in steps:
        if pct == 100:
            bar = renderer3.render_progress_bar(pct, 12)
            content_lines.append(f"{label.ljust(25)} {bar} {status}")
        elif pct > 0:
            bar = renderer3.render_progress_bar(pct, 12)
            content_lines.append(f"{label.ljust(25)} {bar}")
        else:
            content_lines.append(f"{label.ljust(25)} [{'░' * 12}]   0%")

    content_lines.append("")
    content_lines.append(f"Progress: 3/5 steps       Elapsed: 8.2s")

    print(renderer3.render_box("🔧 Flashing AA340-300-D1", content_lines))
    print()

    # Demo 4: Viewport tiers
    print("Demo 4: Viewport Tier Auto-Detection")
    print("-" * 80)

    for tier in ViewportTier:
        print(f"{tier.name:10} - Width: {tier.width:3} → Columns: {tier.columns:2}")

    print()


if __name__ == "__main__":
    demo_grid_rendering()
