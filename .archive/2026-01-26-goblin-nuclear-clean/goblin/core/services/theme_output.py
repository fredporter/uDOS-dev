"""
Theme Output Formatter
======================

Centralized display formatting using ThemeOverlay.
Use for user-facing prints only; do not wrap logs.
"""

from typing import Literal
from dev.goblin.core.services.theme_overlay import apply_theme

MessageType = Literal["error", "warning", "success", "status"]


def format_for_display(message: str, message_type: MessageType = "status") -> str:
    """
    Format a message for display with the active theme overlay.
    Returns original message when overlay is disabled.
    """
    return apply_theme(message or "", message_type)


def themed_print(
    message: str,
    message_type: MessageType = "status",
    end: str = "\n",
    flush: bool = False,
):
    """Print a themed display message (wrapper around print)."""
    print(format_for_display(message, message_type), end=end, flush=flush)
