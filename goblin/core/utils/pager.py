"""
uDOS Unified Pager (v1.2.30)

Merges functionality from:
- core/ui/pager.py (Enhanced Pager with scroll-while-prompting)
- core/utils/pager.py (Simple Pager with block graphics)

Provides:
- Scroll-while-prompting (keep output visible during command entry)
- Block graphics progress bar
- Visual scroll indicators (▲ ▼)
- Search functionality
- Page-by-page navigation
- Configurable viewport
- Raw terminal input support

Author: uDOS Development Team
Version: 1.2.30
"""

import sys
import shutil

try:
    import termios
    import tty

    TERMINAL_AVAILABLE = True
except (ImportError, OSError):
    # No terminal available (API mode, Windows, etc.)
    TERMINAL_AVAILABLE = False
    termios = None
    tty = None
from dataclasses import dataclass, field
from typing import List, Optional, Tuple
from enum import Enum


class ScrollDirection(Enum):
    """Scroll movement direction"""

    UP = "up"
    DOWN = "down"
    PAGE_UP = "page_up"
    PAGE_DOWN = "page_down"
    TOP = "top"
    BOTTOM = "bottom"


@dataclass
class PagerState:
    """Current pager state"""

    lines: List[str] = field(default_factory=list)
    offset: int = 0
    viewport_height: int = 20
    viewport_width: int = 80
    preserve_scroll: bool = True
    show_indicators: bool = True

    @property
    def total_lines(self) -> int:
        return len(self.lines)

    @property
    def max_offset(self) -> int:
        return max(0, self.total_lines - self.viewport_height)

    @property
    def scroll_percentage(self) -> float:
        """Current scroll position as percentage (0.0 - 1.0)"""
        if self.total_lines <= self.viewport_height:
            return 1.0
        return self.offset / self.max_offset if self.max_offset > 0 else 0.0

    @property
    def scroll_percentage_viewed(self) -> float:
        """Percentage of content viewed (0.0 - 1.0)"""
        if self.total_lines <= self.viewport_height:
            return 1.0
        visible_end = min(self.offset + self.viewport_height, self.total_lines)
        return visible_end / self.total_lines

    @property
    def current_page(self) -> int:
        """Current page number (1-indexed)"""
        if self.viewport_height <= 0:
            return 1
        return (self.offset // self.viewport_height) + 1

    @property
    def total_pages(self) -> int:
        """Total number of pages"""
        if self.viewport_height <= 0:
            return 1
        return max(
            1, (self.total_lines + self.viewport_height - 1) // self.viewport_height
        )

    @property
    def at_top(self) -> bool:
        return self.offset == 0

    @property
    def at_bottom(self) -> bool:
        return self.offset >= self.max_offset


class UnifiedPager:
    """
    Unified terminal pager combining enhanced and simple pager features.

    Features:
    - Navigate large outputs with space/arrows/numpad
    - Keep output visible while typing new command
    - Visual scroll indicators (▲ ▼) and progress bar
    - Preserve scroll position option
    - Search functionality
    - Block graphics progress display
    """

    # Block graphics characters (use unified progress bar constants)
    from dev.goblin.core.ui.components.progress_bar import FULL_BLOCK, EMPTY_BLOCK

    def __init__(self, preserve_scroll: bool = True, show_indicators: bool = True):
        """
        Initialize unified pager.

        Args:
            preserve_scroll: Keep scroll position between updates
            show_indicators: Show scroll indicators
        """
        self.state = PagerState(
            preserve_scroll=preserve_scroll, show_indicators=show_indicators
        )
        self.command_buffer = ""
        self.in_command_mode = False
        self._detect_terminal_size()

    def _detect_terminal_size(self):
        """Auto-detect terminal dimensions"""
        try:
            size = shutil.get_terminal_size()
            self.state.viewport_width = size.columns
            self.state.viewport_height = max(10, size.lines - 3)  # Reserve for prompt
        except Exception:
            self.state.viewport_width = 80
            self.state.viewport_height = 20

    def set_content(self, content: str | List[str], reset_scroll: bool = None):
        """
        Set new content to display.

        Args:
            content: Text string or list of lines
            reset_scroll: Override preserve_scroll setting
        """
        if isinstance(content, str):
            self.state.lines = content.split("\n")
        else:
            self.state.lines = list(content)

        # Reset scroll if requested or not preserving
        if reset_scroll is True or (
            reset_scroll is None and not self.state.preserve_scroll
        ):
            self.state.offset = 0
        else:
            # Clamp offset to new content
            self.state.offset = min(self.state.offset, self.state.max_offset)

    def scroll(self, direction: ScrollDirection) -> bool:
        """
        Scroll in specified direction.

        Returns:
            True if scrolled, False if already at limit
        """
        old_offset = self.state.offset

        if direction == ScrollDirection.UP:
            self.state.offset = max(0, self.state.offset - 1)
        elif direction == ScrollDirection.DOWN:
            self.state.offset = min(self.state.max_offset, self.state.offset + 1)
        elif direction == ScrollDirection.PAGE_UP:
            self.state.offset = max(0, self.state.offset - self.state.viewport_height)
        elif direction == ScrollDirection.PAGE_DOWN:
            self.state.offset = min(
                self.state.max_offset, self.state.offset + self.state.viewport_height
            )
        elif direction == ScrollDirection.TOP:
            self.state.offset = 0
        elif direction == ScrollDirection.BOTTOM:
            self.state.offset = self.state.max_offset

        return old_offset != self.state.offset

    def get_viewport(self) -> List[str]:
        """Get current viewport of visible lines"""
        start = self.state.offset
        end = start + self.state.viewport_height
        return self.state.lines[start:end]

    def _draw_progress_bar(self, width: int = None) -> str:
        """
        Draw block graphics progress bar.

        Args:
            width: Bar width (auto-calculated if None)

        Returns:
            Formatted progress bar string
        """
        if width is None:
            # Reserve space for page info
            info_text = f" {self.state.current_page}/{self.state.total_pages} "
            width = max(10, self.state.viewport_width - len(info_text) - 4)

        # Calculate filled blocks
        progress = self.state.scroll_percentage_viewed
        filled = int(width * progress)
        empty = width - filled

        bar = self.FULL_BLOCK * filled + self.EMPTY_BLOCK * empty
        return f"{bar} {self.state.current_page}/{self.state.total_pages}"

    def _draw_scroll_indicator_top(self) -> str:
        """Draw top scroll indicator"""
        if not self.state.at_top:
            return "▲ (More above - Press 8 or PgUp)"
        return "─" * min(60, self.state.viewport_width)

    def _draw_scroll_indicator_bottom(self) -> str:
        """Draw bottom scroll indicator"""
        if not self.state.at_bottom:
            pct = int(self.state.scroll_percentage_viewed * 100)
            return f"▼ ({pct}% viewed - Press 2 or PgDn)"
        return "─" * min(60, self.state.viewport_width)

    def render(self, style: str = "indicators") -> str:
        """
        Render current viewport.

        Args:
            style: "indicators" (▲▼), "progress" (block bar), "minimal" (no decorations)

        Returns:
            Formatted output string
        """
        lines = []

        if style == "indicators" and self.state.show_indicators:
            lines.append(self._draw_scroll_indicator_top())
        elif style == "progress":
            lines.append(self._draw_progress_bar())

        # Add viewport content
        lines.extend(self.get_viewport())

        if style == "indicators" and self.state.show_indicators:
            lines.append(self._draw_scroll_indicator_bottom())
        elif style == "progress":
            lines.append(self._draw_progress_bar())

        return "\n".join(lines)

    def handle_key(self, key: str) -> str:
        """
        Handle keypress for paging control.

        Args:
            key: Key character or code

        Returns:
            Action: "scrolled", "limit", "passthrough", "exit", "skip"
        """
        # Map keys to scroll actions
        scroll_keys = {
            "8": ScrollDirection.UP,  # Numpad 8
            "2": ScrollDirection.DOWN,  # Numpad 2
            "k": ScrollDirection.UP,  # Vim up
            "j": ScrollDirection.DOWN,  # Vim down
            "g": ScrollDirection.TOP,  # Go to top
            "G": ScrollDirection.BOTTOM,  # Go to bottom
            " ": ScrollDirection.PAGE_DOWN,  # Space = page down
        }

        # Check for escape sequences
        if key == "\x1b[A" or key == "up":  # Up arrow
            direction = ScrollDirection.UP
        elif key == "\x1b[B" or key == "down":  # Down arrow
            direction = ScrollDirection.DOWN
        elif key == "\x1b[5~":  # Page Up
            direction = ScrollDirection.PAGE_UP
        elif key == "\x1b[6~":  # Page Down
            direction = ScrollDirection.PAGE_DOWN
        elif key == "\x1b" or key == "esc":  # Escape
            return "exit"
        elif key == "c":  # Skip to command
            return "skip"
        elif key in ("\r", "\n", "enter"):  # Enter
            if self.state.at_bottom:
                return "exit"
            direction = ScrollDirection.PAGE_DOWN
        elif key in scroll_keys:
            direction = scroll_keys[key]
        else:
            return "passthrough"

        # Attempt scroll
        return "scrolled" if self.scroll(direction) else "limit"

    def is_paging_needed(self) -> bool:
        """Check if content requires paging"""
        return self.state.total_lines > self.state.viewport_height

    def get_status_line(self) -> str:
        """Get status line showing scroll position"""
        if not self.is_paging_needed():
            return ""

        current = self.state.offset + 1
        visible_end = min(
            self.state.offset + self.state.viewport_height, self.state.total_lines
        )
        total = self.state.total_lines
        pct = int(self.state.scroll_percentage * 100)

        return f"Lines {current}-{visible_end} of {total} ({pct}%)"

    def search(self, query: str, forward: bool = True) -> bool:
        """
        Search for text and scroll to first match.

        Args:
            query: Search string
            forward: Search forward or backward

        Returns:
            True if found
        """
        current = self.state.offset
        lines = self.state.lines
        query_lower = query.lower()

        if forward:
            for i in range(current, len(lines)):
                if query_lower in lines[i].lower():
                    self.state.offset = max(0, i - self.state.viewport_height // 2)
                    return True
        else:
            for i in range(current, -1, -1):
                if query_lower in lines[i].lower():
                    self.state.offset = max(0, i - self.state.viewport_height // 2)
                    return True

        return False

    def clear(self):
        """Clear pager content"""
        self.state.lines = []
        self.state.offset = 0

    def auto_scroll_to_bottom(self):
        """Scroll to show latest content"""
        self.state.offset = self.state.max_offset

    # ─── Interactive Paging (from SimplePager) ──────────────────────

    def _get_key_raw(self) -> str:
        """
        Get a single keypress (raw terminal mode).

        Returns:
            Key code: 'up', 'down', 'esc', 'enter', 'c', or character
        """
        try:
            fd = sys.stdin.fileno()
            old_settings = termios.tcgetattr(fd)
            try:
                tty.setraw(fd)
                ch = sys.stdin.read(1)

                if ch == "\x1b":  # ESC
                    ch2 = sys.stdin.read(1)
                    if ch2 == "[":
                        ch3 = sys.stdin.read(1)
                        if ch3 == "A":
                            return "up"
                        elif ch3 == "B":
                            return "down"
                        elif ch3 == "C":
                            return "down"  # Right = next
                        elif ch3 == "D":
                            return "up"  # Left = prev
                        elif ch3 == "5":
                            sys.stdin.read(1)  # Read the ~
                            return "page_up"
                        elif ch3 == "6":
                            sys.stdin.read(1)  # Read the ~
                            return "page_down"
                    return "esc"
                elif ch in ("\r", "\n"):
                    return "enter"
                return ch
            finally:
                termios.tcsetattr(fd, termios.TCSADRAIN, old_settings)
        except Exception:
            return input().strip().lower() or "enter"

    def page_interactive(self, text: str = None, title: str = None) -> None:
        """
        Display content with interactive page-by-page navigation.

        Args:
            text: Text to display (uses current content if None)
            title: Optional title for each page
        """
        if text is not None:
            self.set_content(text, reset_scroll=True)

        if not self.is_paging_needed():
            print("\n".join(self.state.lines))
            return

        # ANSI colors
        CYAN = "\033[36m"
        YELLOW = "\033[33m"
        GREEN = "\033[32m"
        RESET = "\033[0m"

        while True:
            # Show title
            if title:
                print(f"{CYAN}╔{'═' * (len(title) + 2)}╗{RESET}")
                print(f"{CYAN}║ {title} ║{RESET}")
                print(f"{CYAN}╚{'═' * (len(title) + 2)}╝{RESET}")
                print()

            # Show viewport
            for line in self.get_viewport():
                print(line)

            # Show progress bar
            progress_bar = self._draw_progress_bar()
            at_end = self.state.at_bottom

            if at_end:
                hint = "[ENTER=OK|ESC]"
            else:
                hint = "[↓/ENTER|↑|c=skip|ESC]"

            print(f"{YELLOW}\n{progress_bar} {hint}{RESET}")
            print(f"{GREEN}►{RESET}", end=" ", flush=True)

            # Get input
            try:
                key = self._get_key_raw()
                action = self.handle_key(key)

                if action in ("exit", "skip"):
                    print()
                    break
                elif action == "limit" and at_end and key == "enter":
                    print()
                    break

            except (KeyboardInterrupt, EOFError):
                print(f"{YELLOW}\n⚠️  Cancelled{RESET}")
                break


# ─── Convenience Functions ──────────────────────────────────────────


def page_output(text: str, title: str = None, viewport_height: int = None) -> str:
    """
    Convenience function to page text output.

    Args:
        text: Text to page
        title: Optional title
        viewport_height: Override viewport height

    Returns:
        Empty string if paged successfully, full text if no terminal available
    """
    if not TERMINAL_AVAILABLE:
        # No terminal - return text directly for API/non-interactive mode
        return text

    try:
        pager = UnifiedPager()
        if viewport_height:
            pager.state.viewport_height = viewport_height
        pager.page_interactive(text, title=title)
        return ""  # Successfully paged
    except (OSError, IOError):
        # Terminal error - return text directly
        return text


def page_lines(lines: List[str], title: str = None) -> None:
    """Page a list of lines"""
    page_output("\n".join(lines), title=title)


# ─── Backwards Compatibility Aliases ────────────────────────────────

# For code using old SimplePager
SimplePager = UnifiedPager

# For code using old Pager
Pager = UnifiedPager


# ─── Test ───────────────────────────────────────────────────────────

if __name__ == "__main__":
    # Generate sample content
    lines = [
        f"Line {i + 1}: Sample content for pager demonstration." for i in range(100)
    ]

    print("Testing UnifiedPager with 100 lines...\n")
    page_output("\n".join(lines), title="Sample Content")
