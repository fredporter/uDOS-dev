#!/usr/bin/env python3
"""
uDOS v1.3.3 - ASCII Panel Templates

Standard panel templates for dashboards with:
- Box styles (single, double, rounded, heavy, teletext)
- Header/footer support
- Content alignment
- Color/ANSI support
- Tauri block graphics compatibility

Version: 1.3.3
Author: Fred Porter
Date: December 2025
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import List, Optional, Dict, Any, Tuple

# IMPORT from consolidated module (v1.0.0)
# See: core/ui/components/box_drawing.py
from dev.goblin.core.ui.components.box_drawing import BoxStyle, BoxChars, BOX_CHARS


class Alignment(Enum):
    """Text alignment."""

    LEFT = "left"
    CENTER = "center"
    RIGHT = "right"


class PanelType(Enum):
    """Standard panel types."""

    STATUS = "status"  # System status display
    INFO = "info"  # Information panel
    MENU = "menu"  # Menu/options panel
    LOG = "log"  # Log/output panel
    STATS = "stats"  # Statistics display
    PROGRESS = "progress"  # Progress bars
    LIST = "list"  # List items
    GRAPH = "graph"  # Simple ASCII graphs
    HEADER = "header"  # Title/header panel
    FOOTER = "footer"  # Footer/status bar
    ALERT = "alert"  # Alert/warning panel
    CUSTOM = "custom"  # User-defined


@dataclass
class PanelStyle:
    """Panel styling configuration."""

    box_style: BoxStyle = BoxStyle.SINGLE
    title_align: Alignment = Alignment.CENTER
    content_align: Alignment = Alignment.LEFT
    padding: int = 1  # Inner padding
    margin: int = 0  # Outer margin
    title_style: str = ""  # ANSI codes for title
    border_style: str = ""  # ANSI codes for border
    content_style: str = ""  # ANSI codes for content
    fill_char: str = " "  # Background fill
    min_width: int = 10
    max_width: int = 80
    min_height: int = 3
    max_height: int = 40


@dataclass
class Panel:
    """A renderable panel."""

    title: str = ""
    content: List[str] = field(default_factory=list)
    width: int = 40
    height: int = 10
    panel_type: PanelType = PanelType.INFO
    style: PanelStyle = field(default_factory=PanelStyle)
    footer: str = ""
    data: Dict[str, Any] = field(default_factory=dict)

    def render(self) -> List[str]:
        """Render panel to list of strings."""
        return render_panel(self)

    def render_str(self) -> str:
        """Render panel to single string."""
        return "\n".join(self.render())


def render_panel(panel: Panel) -> List[str]:
    """Render a panel to list of strings."""
    chars = BOX_CHARS[panel.style.box_style]
    style = panel.style

    # Calculate inner dimensions
    inner_width = panel.width - 2 - (style.padding * 2)
    inner_height = (
        panel.height - 2 - (style.padding * 2 if panel.title else style.padding)
    )

    lines = []

    # Top border with title
    if panel.title:
        title_text = f" {panel.title} "
        if len(title_text) > inner_width:
            title_text = title_text[: inner_width - 3] + "..."

        if style.title_align == Alignment.CENTER:
            left_pad = (panel.width - 2 - len(title_text)) // 2
        elif style.title_align == Alignment.RIGHT:
            left_pad = panel.width - 2 - len(title_text) - 1
        else:
            left_pad = 1

        right_pad = panel.width - 2 - left_pad - len(title_text)
        top_line = (
            chars.top_left
            + chars.horizontal * left_pad
            + title_text
            + chars.horizontal * right_pad
            + chars.top_right
        )
    else:
        top_line = (
            chars.top_left + chars.horizontal * (panel.width - 2) + chars.top_right
        )

    lines.append(top_line)

    # Top padding
    for _ in range(style.padding):
        lines.append(
            chars.vertical + style.fill_char * (panel.width - 2) + chars.vertical
        )

    # Content lines
    content_lines = panel.content[:inner_height] if panel.content else []

    for i in range(inner_height):
        if i < len(content_lines):
            text = content_lines[i]
            # Truncate if needed
            if len(text) > inner_width:
                text = text[: inner_width - 3] + "..."

            # Align content
            if style.content_align == Alignment.CENTER:
                text = text.center(inner_width)
            elif style.content_align == Alignment.RIGHT:
                text = text.rjust(inner_width)
            else:
                text = text.ljust(inner_width)
        else:
            text = style.fill_char * inner_width

        # Add padding
        padded = (
            style.fill_char * style.padding + text + style.fill_char * style.padding
        )
        lines.append(chars.vertical + padded + chars.vertical)

    # Bottom padding
    for _ in range(style.padding):
        lines.append(
            chars.vertical + style.fill_char * (panel.width - 2) + chars.vertical
        )

    # Bottom border with footer
    if panel.footer:
        footer_text = f" {panel.footer} "
        if len(footer_text) > panel.width - 4:
            footer_text = footer_text[: panel.width - 7] + "..."

        left_pad = (panel.width - 2 - len(footer_text)) // 2
        right_pad = panel.width - 2 - left_pad - len(footer_text)
        bottom_line = (
            chars.bottom_left
            + chars.horizontal * left_pad
            + footer_text
            + chars.horizontal * right_pad
            + chars.bottom_right
        )
    else:
        bottom_line = (
            chars.bottom_left
            + chars.horizontal * (panel.width - 2)
            + chars.bottom_right
        )

    lines.append(bottom_line)

    return lines


def render_panels_horizontal(panels: List[Panel], gap: int = 1) -> List[str]:
    """Render multiple panels side by side."""
    if not panels:
        return []

    # Render all panels
    rendered = [p.render() for p in panels]

    # Find max height
    max_height = max(len(r) for r in rendered)

    # Pad shorter panels
    for i, r in enumerate(rendered):
        while len(r) < max_height:
            r.append(" " * panels[i].width)

    # Combine horizontally
    gap_str = " " * gap
    combined = []
    for row in range(max_height):
        line_parts = [rendered[i][row] for i in range(len(panels))]
        combined.append(gap_str.join(line_parts))

    return combined


def render_panels_vertical(panels: List[Panel], gap: int = 0) -> List[str]:
    """Render multiple panels stacked vertically."""
    lines = []
    for i, panel in enumerate(panels):
        if i > 0:
            lines.extend([""] * gap)
        lines.extend(panel.render())
    return lines


def render_panels_grid(
    panels: List[Panel], columns: int = 2, h_gap: int = 1, v_gap: int = 0
) -> List[str]:
    """Render panels in a grid layout."""
    if not panels:
        return []

    lines = []
    for row_start in range(0, len(panels), columns):
        row_panels = panels[row_start : row_start + columns]
        row_lines = render_panels_horizontal(row_panels, h_gap)
        if lines:
            lines.extend([""] * v_gap)
        lines.extend(row_lines)

    return lines


# =============================================================================
# Standard Panel Templates
# =============================================================================


def create_status_panel(
    title: str,
    items: Dict[str, str],
    width: int = 40,
    style: BoxStyle = BoxStyle.SINGLE,
) -> Panel:
    """Create a status panel with key-value pairs."""
    content = []
    max_key_len = max(len(k) for k in items.keys()) if items else 0

    for key, value in items.items():
        content.append(f"{key:<{max_key_len}} : {value}")

    return Panel(
        title=title,
        content=content,
        width=width,
        height=len(content) + 4,
        panel_type=PanelType.STATUS,
        style=PanelStyle(box_style=style),
    )


def create_progress_panel(
    title: str,
    progress: float,
    width: int = 40,
    bar_char: str = "█",
    empty_char: str = "░",
    style: BoxStyle = BoxStyle.SINGLE,
) -> Panel:
    """Create a progress bar panel."""
    bar_width = width - 10
    filled = int(bar_width * min(1.0, max(0.0, progress)))
    empty = bar_width - filled

    bar = bar_char * filled + empty_char * empty
    percent = f"{progress * 100:.0f}%"

    content = [f"[{bar}] {percent}"]

    return Panel(
        title=title,
        content=content,
        width=width,
        height=5,
        panel_type=PanelType.PROGRESS,
        style=PanelStyle(box_style=style, content_align=Alignment.CENTER),
    )


def create_menu_panel(
    title: str,
    options: List[str],
    selected: int = -1,
    width: int = 30,
    style: BoxStyle = BoxStyle.SINGLE,
) -> Panel:
    """Create a menu panel with selectable options."""
    content = []
    for i, option in enumerate(options):
        prefix = "► " if i == selected else "  "
        content.append(f"{prefix}{option}")

    return Panel(
        title=title,
        content=content,
        width=width,
        height=len(content) + 4,
        panel_type=PanelType.MENU,
        style=PanelStyle(box_style=style),
    )


def create_list_panel(
    title: str,
    items: List[str],
    bullet: str = "•",
    width: int = 40,
    max_items: int = 10,
    style: BoxStyle = BoxStyle.SINGLE,
) -> Panel:
    """Create a bulleted list panel."""
    content = []
    display_items = items[:max_items]

    for item in display_items:
        content.append(f" {bullet} {item}")

    if len(items) > max_items:
        content.append(f"   ... and {len(items) - max_items} more")

    return Panel(
        title=title,
        content=content,
        width=width,
        height=len(content) + 4,
        panel_type=PanelType.LIST,
        style=PanelStyle(box_style=style),
    )


def create_stats_panel(
    title: str,
    stats: Dict[str, Tuple[float, float]],  # name -> (current, max)
    width: int = 40,
    bar_width: int = 15,
    style: BoxStyle = BoxStyle.SINGLE,
) -> Panel:
    """Create a stats panel with mini progress bars."""
    content = []
    max_name_len = max(len(k) for k in stats.keys()) if stats else 0

    for name, (current, maximum) in stats.items():
        ratio = current / maximum if maximum > 0 else 0
        filled = int(bar_width * min(1.0, max(0.0, ratio)))
        bar = "█" * filled + "░" * (bar_width - filled)
        content.append(f"{name:<{max_name_len}} [{bar}] {current:.0f}/{maximum:.0f}")

    return Panel(
        title=title,
        content=content,
        width=width,
        height=len(content) + 4,
        panel_type=PanelType.STATS,
        style=PanelStyle(box_style=style),
    )


def create_log_panel(
    title: str,
    logs: List[str],
    width: int = 60,
    height: int = 15,
    style: BoxStyle = BoxStyle.SINGLE,
) -> Panel:
    """Create a log/output panel."""
    # Show most recent logs that fit
    max_lines = height - 4
    display_logs = logs[-max_lines:] if len(logs) > max_lines else logs

    return Panel(
        title=title,
        content=display_logs,
        width=width,
        height=height,
        panel_type=PanelType.LOG,
        style=PanelStyle(box_style=style),
    )


def create_alert_panel(
    message: str,
    alert_type: str = "info",  # info, warning, error, success
    width: int = 50,
    style: BoxStyle = BoxStyle.DOUBLE,
) -> Panel:
    """Create an alert/notification panel."""
    icons = {"info": "ℹ️", "warning": "⚠️", "error": "❌", "success": "✅"}

    titles = {
        "info": "Information",
        "warning": "Warning",
        "error": "Error",
        "success": "Success",
    }

    icon = icons.get(alert_type, "ℹ️")
    title = titles.get(alert_type, "Notice")

    # Wrap message
    content = []
    words = message.split()
    line = f"{icon} "
    max_line_len = width - 6

    for word in words:
        if len(line) + len(word) + 1 > max_line_len:
            content.append(line)
            line = "  " + word
        else:
            line += " " + word if line.strip() else word
    if line.strip():
        content.append(line)

    return Panel(
        title=title,
        content=content,
        width=width,
        height=len(content) + 4,
        panel_type=PanelType.ALERT,
        style=PanelStyle(box_style=style, content_align=Alignment.CENTER),
    )


def create_header_panel(
    title: str, subtitle: str = "", width: int = 60, style: BoxStyle = BoxStyle.DOUBLE
) -> Panel:
    """Create a header/title panel."""
    content = [title.center(width - 4)]
    if subtitle:
        content.append(subtitle.center(width - 4))

    return Panel(
        title="",
        content=content,
        width=width,
        height=len(content) + 2,
        panel_type=PanelType.HEADER,
        style=PanelStyle(box_style=style, content_align=Alignment.CENTER, padding=0),
    )


def create_footer_panel(
    left: str = "",
    center: str = "",
    right: str = "",
    width: int = 60,
    style: BoxStyle = BoxStyle.SINGLE,
) -> Panel:
    """Create a footer/status bar panel."""
    # Calculate spacing
    total_len = len(left) + len(center) + len(right)
    inner_width = width - 4

    if total_len > inner_width:
        # Truncate
        available = inner_width - len(center) - 4
        left = left[: available // 2]
        right = right[: available // 2]

    gap = (inner_width - total_len) // 2
    content = [left + " " * gap + center + " " * gap + right]

    return Panel(
        title="",
        content=content,
        width=width,
        height=3,
        panel_type=PanelType.FOOTER,
        style=PanelStyle(box_style=style, padding=0),
    )


# =============================================================================
# Dashboard Layout Templates
# =============================================================================


@dataclass
class DashboardLayout:
    """Dashboard layout configuration."""

    name: str
    description: str
    panels: List[Dict[str, Any]]  # Panel configs with positions
    width: int = 80
    height: int = 24


# Standard dashboard layouts
DASHBOARD_LAYOUTS = {
    "status": DashboardLayout(
        name="Status Dashboard",
        description="System status overview",
        panels=[
            {"type": "header", "title": "uDOS Status", "row": 0, "col": 0, "width": 80},
            {"type": "status", "title": "System", "row": 1, "col": 0, "width": 40},
            {"type": "stats", "title": "Resources", "row": 1, "col": 1, "width": 40},
            {
                "type": "log",
                "title": "Recent Activity",
                "row": 2,
                "col": 0,
                "width": 80,
                "height": 10,
            },
        ],
    ),
    "profile": DashboardLayout(
        name="Profile Dashboard",
        description="User profile and achievements",
        panels=[
            {"type": "header", "title": "Profile", "row": 0, "col": 0, "width": 80},
            {"type": "status", "title": "User Info", "row": 1, "col": 0, "width": 40},
            {"type": "stats", "title": "XP/HP/Barter", "row": 1, "col": 1, "width": 40},
            {"type": "list", "title": "Achievements", "row": 2, "col": 0, "width": 40},
            {
                "type": "list",
                "title": "Recent Activity",
                "row": 2,
                "col": 1,
                "width": 40,
            },
        ],
    ),
    "network": DashboardLayout(
        name="Network Dashboard",
        description="MeshCore and connectivity status",
        panels=[
            {
                "type": "header",
                "title": "Network Status",
                "row": 0,
                "col": 0,
                "width": 80,
            },
            {"type": "status", "title": "MeshCore", "row": 1, "col": 0, "width": 40},
            {"type": "status", "title": "Web/Cloud", "row": 1, "col": 1, "width": 40},
            {
                "type": "list",
                "title": "Connected Devices",
                "row": 2,
                "col": 0,
                "width": 80,
            },
        ],
    ),
    "minimal": DashboardLayout(
        name="Minimal Dashboard",
        description="Clean, minimal status view",
        panels=[
            {"type": "status", "title": "Status", "row": 0, "col": 0, "width": 60},
        ],
    ),
}


def get_layout(name: str) -> Optional[DashboardLayout]:
    """Get a dashboard layout by name."""
    return DASHBOARD_LAYOUTS.get(name)


def list_layouts() -> List[str]:
    """List available dashboard layouts."""
    return list(DASHBOARD_LAYOUTS.keys())


# =============================================================================
# Block Graphics Conversion (for Tauri)
# =============================================================================

# Teletext/block character mappings for 2x3 pixel blocks
BLOCK_CHARS = {
    # 6-bit pattern -> unicode block character
    0b000000: " ",  # empty
    0b111111: "█",  # full block
    0b110000: "▀",  # upper half
    0b001111: "▄",  # lower half
    0b100100: "▌",  # left half
    0b011011: "▐",  # right half
    0b100000: "▘",  # upper left
    0b010000: "▝",  # upper right
    0b000100: "▖",  # lower left
    0b000010: "▗",  # lower right
    0b110100: "▛",  # upper left + upper right + lower left
    0b110010: "▜",  # upper left + upper right + lower right
    0b101100: "▙",  # upper left + lower left + lower right
    0b011100: "▟",  # upper right + lower left + lower right
}


def ascii_to_block(ascii_art: List[str]) -> List[str]:
    """Convert ASCII art to block graphics (2x3 pixel blocks)."""
    # This is a simplified conversion - full implementation would
    # analyze character patterns and map to appropriate block chars
    result = []
    for line in ascii_art:
        block_line = ""
        for char in line:
            if char in "█▓▒░":
                block_line += char
            elif char in "┌┐└┘├┤┬┴┼─│":
                # Map box drawing to blocks
                block_line += {
                    "┌": "▛",
                    "┐": "▜",
                    "└": "▙",
                    "┘": "▟",
                    "├": "▌",
                    "┤": "▐",
                    "┬": "▀",
                    "┴": "▄",
                    "┼": "█",
                    "─": "▀",
                    "│": "▌",
                }.get(char, char)
            else:
                block_line += char
        result.append(block_line)
    return result


# =============================================================================
# Module exports
# =============================================================================

__all__ = [
    # Enums
    "BoxStyle",
    "Alignment",
    "PanelType",
    # Data classes
    "BoxChars",
    "PanelStyle",
    "Panel",
    "DashboardLayout",
    # Constants
    "BOX_CHARS",
    "DASHBOARD_LAYOUTS",
    # Render functions
    "render_panel",
    "render_panels_horizontal",
    "render_panels_vertical",
    "render_panels_grid",
    # Template creators
    "create_status_panel",
    "create_progress_panel",
    "create_menu_panel",
    "create_list_panel",
    "create_stats_panel",
    "create_log_panel",
    "create_alert_panel",
    "create_header_panel",
    "create_footer_panel",
    # Layout functions
    "get_layout",
    "list_layouts",
    # Block graphics
    "ascii_to_block",
]


# =============================================================================
# Test
# =============================================================================

if __name__ == "__main__":
    print("=" * 60)
    print("Panel Templates Test")
    print("=" * 60)

    # Test status panel
    status = create_status_panel(
        "System Status",
        {
            "Version": "1.3.3",
            "Role": "Ghost (4)",
            "Network": "MeshCore",
            "Uptime": "2h 34m",
        },
    )
    print("\n".join(status.render()))

    print()

    # Test progress panel
    progress = create_progress_panel("Download Progress", 0.73)
    print("\n".join(progress.render()))

    print()

    # Test stats panel
    stats = create_stats_panel(
        "Resources", {"XP": (1250, 2000), "HP": (85, 100), "Barter": (150, 500)}
    )
    print("\n".join(stats.render()))

    print()

    # Test menu panel
    menu = create_menu_panel(
        "Options", ["Profile", "Network", "Settings", "Help", "Exit"], selected=2
    )
    print("\n".join(menu.render()))

    print()

    # Test alert panel
    alert = create_alert_panel(
        "Your session will expire in 5 minutes. Save your work.", alert_type="warning"
    )
    print("\n".join(alert.render()))

    print()

    # Test horizontal layout
    p1 = create_status_panel("Left", {"A": "1", "B": "2"}, width=25)
    p2 = create_status_panel("Right", {"C": "3", "D": "4"}, width=25)
    print("\n".join(render_panels_horizontal([p1, p2])))

    print()
    print("=" * 60)
    print("✅ Panel Templates working!")
