"""
FeedRenderer - Display feed content in TUI

Provides two main display modes:
- TICKER: Single-line horizontal scrolling
- SCROLL: Full-page vertical scrolling with typed effect

Can render to any terminal output.
"""

from enum import Enum
from typing import Optional, Callable, List, Any
from datetime import datetime
import time
import sys
import threading

from .feed_item import FeedItem


class DisplayMode(Enum):
    """Feed display modes"""

    TICKER = "ticker"  # Single line, horizontal scroll
    SCROLL = "scroll"  # Full page, vertical scroll
    PANEL = "panel"  # Fixed area, rotating items
    STATIC = "static"  # Single item, no animation


class FeedSpeed(Enum):
    """Predefined display speeds"""

    VERY_SLOW = 0.15  # Seconds per character
    SLOW = 0.08
    MEDIUM = 0.04
    FAST = 0.02
    VERY_FAST = 0.01
    INSTANT = 0.0


class FeedRenderer:
    """
    Renders feed content to terminal display.

    Supports ticker (horizontal scroll) and scroll (vertical typed)
    display modes with configurable speed and styling.
    """

    def __init__(self, width: int = 80, height: int = 24):
        self.width = width
        self.height = height
        self.mode: DisplayMode = DisplayMode.TICKER
        self.speed: float = FeedSpeed.MEDIUM.value
        self.running: bool = False
        self.paused: bool = False

        # Styling
        self.separator = " ••• "
        self.ticker_prefix = "▶ "
        self.scroll_prefix = "│ "

        # Callbacks
        self._on_update: Optional[Callable[[str], None]] = None
        self._on_item_shown: Optional[Callable[[FeedItem], None]] = None

        # State
        self._current_text = ""
        self._scroll_position = 0
        self._thread: Optional[threading.Thread] = None
        self._items: List[FeedItem] = []

    def set_mode(self, mode: DisplayMode) -> None:
        """Set display mode"""
        self.mode = mode

    def set_speed(self, speed: float | FeedSpeed) -> None:
        """Set display speed (seconds per character)"""
        if isinstance(speed, FeedSpeed):
            self.speed = speed.value
        else:
            self.speed = max(0.0, min(1.0, speed))

    def set_speed_by_name(self, name: str) -> bool:
        """Set speed by name (very_slow, slow, medium, fast, very_fast, instant)"""
        speed_map = {
            "very_slow": FeedSpeed.VERY_SLOW,
            "slow": FeedSpeed.SLOW,
            "medium": FeedSpeed.MEDIUM,
            "fast": FeedSpeed.FAST,
            "very_fast": FeedSpeed.VERY_FAST,
            "instant": FeedSpeed.INSTANT,
        }
        if name.lower() in speed_map:
            self.set_speed(speed_map[name.lower()])
            return True
        return False

    def on_update(self, callback: Callable[[str], None]) -> None:
        """Register callback for display updates"""
        self._on_update = callback

    def on_item_shown(self, callback: Callable[[FeedItem], None]) -> None:
        """Register callback when an item is fully displayed"""
        self._on_item_shown = callback

    def set_items(self, items: List[FeedItem]) -> None:
        """Set items to display"""
        self._items = items

    # TICKER MODE - Single line horizontal scroll

    def render_ticker_frame(self, text: str, position: int) -> str:
        """
        Render a single frame of ticker display.

        Args:
            text: Full ticker text
            position: Current scroll position

        Returns:
            String of width characters for display
        """
        display_width = self.width - len(self.ticker_prefix)

        # Create looping text
        full_text = text + self.separator
        text_len = len(full_text)

        if text_len == 0:
            return self.ticker_prefix + " " * display_width

        # Calculate visible portion
        pos = position % text_len
        visible = ""

        for i in range(display_width):
            char_pos = (pos + i) % text_len
            visible += full_text[char_pos]

        return self.ticker_prefix + visible

    def start_ticker(
        self, text: str, callback: Optional[Callable[[str], None]] = None
    ) -> None:
        """
        Start ticker animation in background thread.

        Args:
            text: Text to scroll
            callback: Called with each frame (or uses default output)
        """
        self.running = True
        self.paused = False
        self._current_text = text
        self._scroll_position = 0

        output_fn = callback or self._on_update or self._default_output

        def ticker_loop():
            while self.running:
                if not self.paused:
                    frame = self.render_ticker_frame(
                        self._current_text, self._scroll_position
                    )
                    output_fn(frame)
                    self._scroll_position += 1

                time.sleep(self.speed)

        self._thread = threading.Thread(target=ticker_loop, daemon=True)
        self._thread.start()

    def update_ticker_text(self, text: str) -> None:
        """Update ticker text while running"""
        self._current_text = text

    # SCROLL MODE - Full page vertical scroll with typed effect

    def render_scroll_line(self, text: str, typed_length: int) -> str:
        """
        Render a partially typed line for scroll effect.

        Args:
            text: Full line text
            typed_length: Characters typed so far

        Returns:
            Line with typing cursor
        """
        if typed_length >= len(text):
            return self.scroll_prefix + text

        visible = text[:typed_length]
        cursor = "▌" if typed_length < len(text) else ""
        return self.scroll_prefix + visible + cursor

    def type_line(
        self, text: str, callback: Optional[Callable[[str], None]] = None
    ) -> None:
        """
        Display a single line with typing effect.

        Args:
            text: Line to type
            callback: Called with each frame
        """
        output_fn = callback or self._on_update or self._default_output

        for i in range(len(text) + 1):
            if not self.running or self.paused:
                while self.paused and self.running:
                    time.sleep(0.1)
                if not self.running:
                    return

            frame = self.render_scroll_line(text, i)
            output_fn(frame)

            if self.speed > 0:
                time.sleep(self.speed)

        # Brief pause at end of line
        time.sleep(self.speed * 5)

    def start_scroll(
        self,
        lines: List[str],
        callback: Optional[Callable[[str], None]] = None,
        loop: bool = True,
    ) -> None:
        """
        Start scrolling text display.

        Args:
            lines: Lines to display
            callback: Called with each frame
            loop: Whether to loop continuously
        """
        self.running = True
        self.paused = False

        output_fn = callback or self._on_update or self._default_output

        def scroll_loop():
            while self.running:
                for line in lines:
                    if not self.running:
                        break
                    self.type_line(line, output_fn)

                if not loop:
                    self.running = False
                    break

                # Pause between loops
                time.sleep(1.0)

        self._thread = threading.Thread(target=scroll_loop, daemon=True)
        self._thread.start()

    # PANEL MODE - Fixed area with rotating items

    def render_panel(self, items: List[FeedItem], panel_height: int = 5) -> List[str]:
        """
        Render items in a fixed panel area.

        Args:
            items: Items to display
            panel_height: Lines available

        Returns:
            List of lines for panel
        """
        lines = []
        lines.append("┌" + "─" * (self.width - 2) + "┐")

        for i in range(panel_height - 2):
            if i < len(items):
                item = items[i]
                text = item.ticker_text[: self.width - 4]
                padding = " " * (self.width - 4 - len(text))
                lines.append(f"│ {text}{padding} │")
            else:
                lines.append("│" + " " * (self.width - 2) + "│")

        lines.append("└" + "─" * (self.width - 2) + "┘")
        return lines

    # Control methods

    def pause(self) -> None:
        """Pause display"""
        self.paused = True

    def resume(self) -> None:
        """Resume display"""
        self.paused = False

    def stop(self) -> None:
        """Stop display"""
        self.running = False
        if self._thread and self._thread.is_alive():
            self._thread.join(timeout=1.0)

    def is_running(self) -> bool:
        """Check if display is running"""
        return self.running

    # Output methods

    def _default_output(self, text: str) -> None:
        """Default output to stdout with carriage return"""
        sys.stdout.write(f"\r{text}")
        sys.stdout.flush()

    def render_to_string(self, items: List[FeedItem]) -> str:
        """
        Render items to string based on current mode.

        Returns single-shot render, not animated.
        """
        if self.mode == DisplayMode.TICKER:
            text = self.separator.join(item.ticker_text for item in items)
            return self.render_ticker_frame(text, 0)

        elif self.mode == DisplayMode.SCROLL:
            lines = [item.ticker_text for item in items]
            return "\n".join(self.scroll_prefix + line for line in lines)

        elif self.mode == DisplayMode.PANEL:
            panel = self.render_panel(items)
            return "\n".join(panel)

        elif self.mode == DisplayMode.STATIC:
            if items:
                return items[0].ticker_text
            return ""

        return ""

    def get_status(self) -> dict:
        """Get renderer status"""
        return {
            "mode": self.mode.value,
            "speed": self.speed,
            "running": self.running,
            "paused": self.paused,
            "width": self.width,
            "height": self.height,
        }


# Convenience functions for quick rendering


def ticker(text: str, width: int = 80, speed: str = "medium") -> FeedRenderer:
    """Create and start a ticker renderer"""
    renderer = FeedRenderer(width=width)
    renderer.set_mode(DisplayMode.TICKER)
    renderer.set_speed_by_name(speed)
    renderer.start_ticker(text)
    return renderer


def scroll(lines: List[str], width: int = 80, speed: str = "medium") -> FeedRenderer:
    """Create and start a scroll renderer"""
    renderer = FeedRenderer(width=width)
    renderer.set_mode(DisplayMode.SCROLL)
    renderer.set_speed_by_name(speed)
    renderer.start_scroll(lines)
    return renderer
