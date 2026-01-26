"""
Goblin Commands Module - Empty Framework

This module contains the command handler framework for Goblin.
All concrete handlers have been removed as of 2026-01-26.

Framework files remaining:
- base_handler.py: Base class for all command handlers
- handler_utils.py: Shared utilities for handlers

To add new commands:
1. Create a new handler file (e.g., my_handler.py)
2. Extend BaseCommandHandler from base_handler.py
3. Import and register in dev/goblin/core/uDOS_commands.py

For reference, see GOBLIN-COMMAND-MANIFEST.md for complete
inventory of previously removed handlers and their purposes.
"""

from .base_handler import BaseCommandHandler

__all__ = ["BaseCommandHandler"]
