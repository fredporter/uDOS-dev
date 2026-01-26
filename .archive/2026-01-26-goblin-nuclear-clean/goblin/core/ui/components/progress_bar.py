"""
Unified Progress Bar (TUI)
==========================

Canonical text progress bar with block characters.
Authoritative source: use this module across core.
"""

from dataclasses import dataclass

FULL_BLOCK = "█"
EMPTY_BLOCK = "░"


@dataclass
class ProgressBar:
    total: int
    width: int = 30

    def render(self, current: int) -> str:
        """Render a progress bar for current progress."""
        if self.total <= 0:
            return f"[{EMPTY_BLOCK * self.width}] 0%"
        pct = max(0.0, min(1.0, float(current) / float(self.total)))
        filled = int(round(pct * self.width))
        bar = FULL_BLOCK * filled + EMPTY_BLOCK * (self.width - filled)
        percent_text = int(round(pct * 100))
        return f"[{bar}] {percent_text}%"
