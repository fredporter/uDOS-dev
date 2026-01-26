"""
uDOS Graphics Utilities
=======================
Provides terminal graphics utilities including spinners and status indicators
using Unicode block characters.

⚠️ DEPRECATION NOTICE:
   ProgressBar class moved to core.ui.progress_indicators.ProgressBar
   This module provides a compatibility shim. Please update imports.

Version: 1.0.24 (Phase 2 Consolidation)
"""

import sys
import time
import threading
import warnings
from typing import Optional, Callable


class Spinner:
    """
    Animated spinner for long-running operations.

    Usage:
        with Spinner("Loading..."):
            # do work
            pass
    """

    FRAMES = ["⠋", "⠙", "⠹", "⠸", "⠼", "⠴", "⠦", "⠧", "⠇", "⠏"]  # Braille dots
    FRAMES_ALT = ["◐", "◓", "◑", "◒"]  # Circle rotation
    FRAMES_DOTS = ["⣾", "⣽", "⣻", "⢿", "⡿", "⣟", "⣯", "⣷"]  # Braille blocks
    FRAMES_SIMPLE = ["|", "/", "-", "\\"]  # Classic

    def __init__(self, message: str = "Working", style: str = "braille"):
        """
        Initialize spinner.

        Args:
            message: Message to display next to spinner
            style: Animation style ('braille', 'circle', 'dots', 'simple')
        """
        self.message = message
        self.running = False
        self.thread: Optional[threading.Thread] = None

        # Select frame style
        if style == "circle":
            self.frames = self.FRAMES_ALT
        elif style == "dots":
            self.frames = self.FRAMES_DOTS
        elif style == "simple":
            self.frames = self.FRAMES_SIMPLE
        else:
            self.frames = self.FRAMES

    def _spin(self):
        """Internal spinner loop."""
        idx = 0
        while self.running:
            frame = self.frames[idx % len(self.frames)]
            sys.stdout.write(f"\r{frame} {self.message}")
            sys.stdout.flush()
            idx += 1
            time.sleep(0.1)

    def start(self):
        """Start the spinner animation."""
        self.running = True
        self.thread = threading.Thread(target=self._spin, daemon=True)
        self.thread.start()

    def stop(self, final_message: Optional[str] = None):
        """
        Stop the spinner animation.

        Args:
            final_message: Optional message to display when done (e.g., "✅ Done")
        """
        self.running = False
        if self.thread:
            self.thread.join()

        if final_message:
            sys.stdout.write(f"\r{final_message}\n")
        else:
            sys.stdout.write("\r" + " " * (len(self.message) + 3) + "\r")
        sys.stdout.flush()

    def __enter__(self):
        """Context manager entry."""
        self.start()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        if exc_type is None:
            self.stop("✅ Done")
        else:
            self.stop("❌ Failed")
        return False


class ProgressBar:
    """
    ⚠️ DEPRECATED: Use core.ui.progress_indicators.ProgressBar instead

    This is a compatibility shim that will be removed in a future version.

    Migration:
        from dev.goblin.core.ui.progress_indicators import ProgressBar

    Changes:
        - update() no longer takes 'message' parameter
        - finish() method removed (automatic on completion)
    """

    def __init__(
        self, total: int, width: int = 40, title: str = "", show_percent: bool = True
    ):
        """Initialize progress bar (deprecated)."""
        warnings.warn(
            "core.output.graphics.ProgressBar is deprecated and will be removed. "
            "Use core.ui.progress_indicators.ProgressBar instead.",
            DeprecationWarning,
            stacklevel=2,
        )

        # Import the canonical implementation
        from dev.goblin.core.ui.progress_indicators import ProgressBar as _ProgressBar

        self._impl = _ProgressBar(total=total, width=width, title=title)
        self.total = total
        self.width = width
        self.title = title
        self.show_percent = show_percent
        self.current = 0

    def update(self, current: int, message: str = ""):
        """Update progress bar (message parameter ignored)."""
        self.current = current
        self._impl.update(current=current)

        # If message provided, append it manually for backward compatibility
        if message:
            sys.stdout.write(f" {message}")
            sys.stdout.flush()

    def finish(self, message: str = "✅ Complete"):
        """Finish the progress bar."""
        self.update(self.total)
        if message:
            sys.stdout.write(f" {message}")
        sys.stdout.write("\n")
        sys.stdout.flush()


def make_progress_bar(value: int, max_value: int, width: int = 10) -> str:
    """
    Create a static progress bar string.

    Args:
        value: Current value
        max_value: Maximum value
        width: Width in characters

    Returns:
        Progress bar string using block characters

    Example:
        >>> make_progress_bar(7, 10, 10)
        '███████░░░'
    """
    if max_value == 0:
        return "░" * width
    filled = int((value / max_value) * width)
    return "█" * filled + "░" * (width - filled)


def make_percentage_bar(percent: float, width: int = 20) -> str:
    """
    Create a percentage bar (0-100).

    Args:
        percent: Percentage (0-100)
        width: Width in characters

    Returns:
        Progress bar string

    Example:
        >>> make_percentage_bar(75.5, 20)
        '███████████████░░░░░'
    """
    filled = int((percent / 100) * width)
    return "█" * filled + "░" * (width - filled)


class TaskProgress:
    """
    Multi-task progress tracker.

    Usage:
        tasks = TaskProgress(["Task 1", "Task 2", "Task 3"])
        tasks.start_task(0)
        # ... do work ...
        tasks.complete_task(0)
        tasks.start_task(1)
        # ... do work ...
        tasks.complete_task(1)
    """

    def __init__(self, task_names: list[str]):
        """
        Initialize task tracker.

        Args:
            task_names: List of task names
        """
        self.tasks = task_names
        self.status = [
            "⚪" for _ in task_names
        ]  # ⚪ = pending, 🔵 = active, ✅ = done, ❌ = failed

    def start_task(self, idx: int):
        """Mark task as started."""
        self.status[idx] = "🔵"
        self._display()

    def complete_task(self, idx: int, success: bool = True):
        """Mark task as completed."""
        self.status[idx] = "✅" if success else "❌"
        self._display()

    def fail_task(self, idx: int):
        """Mark task as failed."""
        self.complete_task(idx, success=False)

    def _display(self):
        """Display current status."""
        sys.stdout.write("\r")
        for status, task in zip(self.status, self.tasks):
            sys.stdout.write(f"{status} {task}  ")
        sys.stdout.flush()

    def finish(self):
        """Finish and move to new line."""
        sys.stdout.write("\n")
        sys.stdout.flush()


# Color utilities (ANSI escape codes)
class Colors:
    """ANSI color codes for terminal output."""

    RESET = "\033[0m"
    BOLD = "\033[1m"
    DIM = "\033[2m"

    # Regular colors
    BLACK = "\033[30m"
    RED = "\033[31m"
    GREEN = "\033[32m"
    YELLOW = "\033[33m"
    BLUE = "\033[34m"
    MAGENTA = "\033[35m"
    CYAN = "\033[36m"
    WHITE = "\033[37m"

    # Bright colors
    BRIGHT_BLACK = "\033[90m"
    BRIGHT_RED = "\033[91m"
    BRIGHT_GREEN = "\033[92m"
    BRIGHT_YELLOW = "\033[93m"
    BRIGHT_BLUE = "\033[94m"
    BRIGHT_MAGENTA = "\033[95m"
    BRIGHT_CYAN = "\033[96m"
    BRIGHT_WHITE = "\033[97m"

    @staticmethod
    def color(text: str, color: str) -> str:
        """Wrap text in color codes."""
        return f"{color}{text}{Colors.RESET}"


# Box drawing utilities
# DEPRECATED: Use core.ui.components.BoxChars instead
# This implementation will be archived in v1.0.3.0
# See: core/ui/components/box_drawing.py
# Archive: .archive/2026-01-14/graphics_box_chars.py
import warnings


class BoxChars:
    """
    Unicode box drawing characters.

    ⚠️  DEPRECATED: Use core.ui.components.BoxChars instead

    This class is kept for backward compatibility but will be removed.
    Migrate to the consolidated box drawing module:

        from dev.goblin.core.ui.components import BoxChars

    See: core/ui/components/box_drawing.py
    """

    # Single line
    H = "─"  # Horizontal
    V = "│"  # Vertical
    TL = "┌"  # Top-left
    TR = "┐"  # Top-right
    BL = "└"  # Bottom-left
    BR = "┘"  # Bottom-right
    VR = "├"  # Vertical-right
    VL = "┤"  # Vertical-left
    HU = "┴"  # Horizontal-up
    HD = "┬"  # Horizontal-down
    CROSS = "┼"  # Cross

    # Double line
    DH = "═"  # Double horizontal
    DV = "║"  # Double vertical
    DTL = "╔"  # Double top-left
    DTR = "╗"  # Double top-right
    DBL = "╚"  # Double bottom-left
    DBR = "╝"  # Double bottom-right
    DVR = "╠"  # Double vertical-right
    DVL = "╣"  # Double vertical-left
    DHU = "╩"  # Double horizontal-up
    DHD = "╦"  # Double horizontal-down
    DCROSS = "╬"  # Double cross

    @staticmethod
    def box(width: int, height: int, title: str = "", double: bool = True) -> str:
        """
        Create a box with optional title.

        Args:
            width: Box width
            height: Box height
            title: Optional title
            double: Use double lines if True

        Returns:
            Multi-line box string
        """
        if double:
            tl, tr, bl, br = BoxChars.DTL, BoxChars.DTR, BoxChars.DBL, BoxChars.DBR
            h, v = BoxChars.DH, BoxChars.DV
        else:
            tl, tr, bl, br = BoxChars.TL, BoxChars.TR, BoxChars.BL, BoxChars.BR
            h, v = BoxChars.H, BoxChars.V

        lines = []

        # Top line with title
        if title:
            title_padded = f" {title} "
            padding = width - len(title_padded) - 2
            left_pad = padding // 2
            right_pad = padding - left_pad
            lines.append(f"{tl}{h * left_pad}{title_padded}{h * right_pad}{tr}")
        else:
            lines.append(f"{tl}{h * (width - 2)}{tr}")

        # Middle lines
        for _ in range(height - 2):
            lines.append(f"{v}{' ' * (width - 2)}{v}")

        # Bottom line
        lines.append(f"{bl}{h * (width - 2)}{br}")

        return "\n".join(lines)


if __name__ == "__main__":
    # Demo
    print("🎨 uDOS Graphics Demo\n")

    # Spinner demo
    print("1. Spinner:")
    with Spinner("Loading resources", style="braille"):
        time.sleep(2)

    # Progress bar demo
    print("\n2. Progress Bar:")
    bar = ProgressBar(total=50, width=30, title="Processing")
    for i in range(50):
        bar.update(i + 1)
        time.sleep(0.05)
    bar.finish()

    # Static bars demo
    print("\n3. Static Bars:")
    print(f"  Disk:   {make_progress_bar(75, 100, 20)} 75%")
    print(f"  Memory: {make_progress_bar(45, 100, 20)} 45%")
    print(f"  CPU:    {make_progress_bar(90, 100, 20)} 90%")

    # Task tracker demo
    print("\n4. Task Tracker:")
    tasks = TaskProgress(["Download", "Extract", "Install", "Configure"])
    for i in range(4):
        tasks.start_task(i)
        time.sleep(0.5)
        tasks.complete_task(i)
    tasks.finish()

    # Box demo
    print("\n5. Box Drawing:")
    print(BoxChars.box(40, 5, "Sample Box", double=True))

    print("\n✅ Demo complete!")


class FontGraphicsHelper:
    """
    Helper class for font-based graphics using Synthwave DOS colors and retro fonts.
    Integrates with core/data/font-system.json
    """

    @staticmethod
    def get_block_char(block_type: str = "full", charset: str = "unicode") -> str:
        """
        Get block graphics character from font system.

        Args:
            block_type: Type of block (full, top_half, bottom_half, left_half, etc.)
            charset: Character set (unicode, petscii, teletext, ascii)

        Returns:
            Block character string
        """
        from dev.goblin.core.uDOS_settings import FontSystemManager

        font_sys = FontSystemManager.get_instance()
        blocks = font_sys.get_block_graphics(charset)

        # Map common block types
        block_map = {
            "full": blocks.get("full_block", "█"),
            "top_half": blocks.get("upper_half_block", "▀"),
            "bottom_half": blocks.get("lower_half_block", "▄"),
            "left_half": blocks.get("left_half_block", "▌"),
            "right_half": blocks.get("right_half_block", "▐"),
            "light_shade": blocks.get("light_shade", "░"),
            "medium_shade": blocks.get("medium_shade", "▒"),
            "dark_shade": blocks.get("dark_shade", "▓"),
        }

        return block_map.get(block_type, "█")

    @staticmethod
    def get_ansi_color(color_name: str, brightness: str = "bright") -> str:
        """
        Get ANSI escape code for Synthwave DOS color.

        Args:
            color_name: Color name (black, red, green, blue, cyan, magenta, orange, gray, white)
            brightness: bright or dark

        Returns:
            ANSI escape sequence
        """
        from dev.goblin.core.uDOS_settings import FontSystemManager

        font_sys = FontSystemManager.get_instance()
        palette = font_sys.get_color_palette()

        color_key = (
            f"{color_name}_{brightness}"
            if brightness in ["bright", "dark"]
            else color_name
        )
        color_data = palette.get(color_key, palette.get("white_bright", {}))

        return color_data.get("ansi", "\033[0m")

    @staticmethod
    def colorize(text: str, color: str, brightness: str = "bright") -> str:
        """
        Colorize text using Synthwave DOS colors.

        Args:
            text: Text to colorize
            color: Color name
            brightness: bright or dark

        Returns:
            ANSI-colored text string
        """
        ansi = FontGraphicsHelper.get_ansi_color(color, brightness)
        reset = "\033[0m"
        return f"{ansi}{text}{reset}"

    @staticmethod
    def make_retro_banner(text: str, width: int = 60, font: str = "chicago") -> str:
        """
        Create retro-styled banner using block characters.

        Args:
            text: Banner text
            width: Total width
            font: Font name (affects character selection)

        Returns:
            Multi-line banner string
        """
        border_char = FontGraphicsHelper.get_block_char("full")
        top_half = FontGraphicsHelper.get_block_char("top_half")
        bottom_half = FontGraphicsHelper.get_block_char("bottom_half")

        lines = []
        lines.append(border_char * width)
        lines.append(f"{border_char}{top_half * (width - 2)}{border_char}")

        # Center text
        padding = (width - 4 - len(text)) // 2
        text_line = (
            f"{border_char}  {' ' * padding}{text}{' ' * padding}  {border_char}"
        )
        if len(text_line) < width:
            text_line += " " * (width - len(text_line) - 1) + border_char
        lines.append(text_line)

        lines.append(f"{border_char}{bottom_half * (width - 2)}{border_char}")
        lines.append(border_char * width)

        return "\n".join(lines)
