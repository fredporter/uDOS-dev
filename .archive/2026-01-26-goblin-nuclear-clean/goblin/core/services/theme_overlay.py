"""
Theme Overlay System - Display Layer
=====================================

Applies thematic vocabulary and formatting to system output AFTER
runtime execution and logging. Keeps debugging pure while providing
immersive user experience.

Architecture:
    Runtime/Execution → [System Output] → Theme Overlay → [Themed Output]

Usage:
    overlay = ThemeOverlay('dungeon-adventure')
    themed = overlay.apply('Error: File not found', 'error')
    # Returns: "⚔️ TRAP SPRUNG: Scroll not found"

Author: uDOS Team
Version: 1.0.0
Date: 2026-01-14
"""

import json
import re
from pathlib import Path
from typing import Dict, Optional, Any
from dev.goblin.core.services.logging_manager import get_logger

logger = get_logger("theme-overlay")


class ThemeOverlay:
    """
    Theme overlay system that applies thematic vocabulary and formatting
    to system messages without affecting core debugging/logging.
    """

    def __init__(self, theme_id: str = "default"):
        """
        Initialize theme overlay with specified theme.

        Args:
            theme_id: Theme identifier (e.g., 'dungeon-adventure')
        """
        self.theme_id = theme_id
        self.theme_path = Path(__file__).parent.parent / "data" / "themes" / theme_id
        self.variables: Dict[str, str] = {}
        self.messages: Dict[str, Any] = {}
        self.metadata: Dict[str, Any] = {}

        # Load theme if not default
        if theme_id != "default":
            self._load_theme()
        else:
            logger.debug("[LOCAL] Using default theme (no overlay)")

    def _load_theme(self) -> None:
        """Load theme configuration files from theme directory."""
        try:
            # Load variables mapping
            variables_file = self.theme_path / "variables.json"
            if variables_file.exists():
                with open(variables_file, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    # Handle both flat (str) and nested (dict) variable formats
                    raw_variables = data.get("variables", {})
                    self.variables = {}
                    for key, value in raw_variables.items():
                        if isinstance(value, dict):
                            # Nested format: extract theme_vocab
                            self.variables[value.get("system_var", key)] = value.get(
                                "theme_vocab", key
                            )
                        else:
                            # Flat format: use key-value directly
                            self.variables[key] = value
                    self.metadata = {
                        "theme_name": data.get("theme_name", ""),
                        "theme_id": data.get("theme_id", self.theme_id),
                        "style": data.get("style", ""),
                        "emoji_set": data.get("emoji_set", []),
                        "author": data.get("author", ""),
                        "tone": data.get("tone", ""),
                        "description": data.get("description", ""),
                    }
                logger.debug(
                    f"[LOCAL] Loaded {len(self.variables)} variable mappings from {variables_file}"
                )
            else:
                logger.warning(f"[LOCAL] Variables file not found: {variables_file}")

            # Load message templates
            messages_file = self.theme_path / "messages.json"
            if messages_file.exists():
                with open(messages_file, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    self.messages = data.get("templates", {})
                logger.debug(
                    f"[LOCAL] Loaded {len(self.messages)} message templates from {messages_file}"
                )
            else:
                logger.warning(f"[LOCAL] Messages file not found: {messages_file}")

        except Exception as e:
            logger.error(f"[LOCAL] Failed to load theme '{self.theme_id}': {e}")
            # Fall back to default (no overlay)
            self.variables = {}
            self.messages = {}
            self.metadata = {}

    def apply(self, message: str, message_type: str = "status") -> str:
        """
        Apply theme overlay to a system message.

        Args:
            message: Original system message
            message_type: Message category (error, warning, success, status, etc.)

        Returns:
            Themed message with variable replacements and formatting

        Examples:
            >>> overlay = ThemeOverlay('dungeon-adventure')
            >>> overlay.apply('Error in sandbox', 'error')
            '⚔️ TRAP SPRUNG: Trap in dungeon'

            >>> overlay.apply('Plugin loaded successfully', 'success')
            '💎 TREASURE FOUND: Enchantment loaded successfully'
        """
        # Handle empty messages first
        if not message or not message.strip():
            return message
        

        # If no theme loaded, return original message
        if not self.variables and not self.messages:
            return message

        # Step 1: Apply variable replacements
        themed_message = self._replace_variables(message)

        # Step 2: Apply message template formatting
        formatted_message = self._apply_template(themed_message, message_type)

        return formatted_message

    def _replace_variables(self, text: str) -> str:
        """
        Replace system variables with theme-specific vocabulary.

        Performs case-insensitive, word-boundary replacement of system
        terms with theme equivalents.

        Args:
            text: Original text with system variables

        Returns:
            Text with theme vocabulary substituted
        """
        if not self.variables:
            return text

        # Handle empty text
        if not text or not text.strip():
            return text

        result = text

        # Sort by length (longest first) to avoid partial replacements
        sorted_vars = sorted(
            self.variables.items(), key=lambda x: len(x[0]), reverse=True
        )

        for system_var, theme_var in sorted_vars:
            # Use word boundaries to avoid partial replacements
            # Case-insensitive matching, preserve original case style
            pattern = re.compile(r"\b" + re.escape(system_var) + r"\b", re.IGNORECASE)

            def replace_with_case(match):
                """Preserve case style of original text."""
                original = match.group(0)

                # All caps
                if original.isupper():
                    return theme_var.upper()
                # Title case
                elif original[0].isupper():
                    return (
                        theme_var.title() if not theme_var[0].isupper() else theme_var
                    )
                # Lower case
                else:
                    return theme_var.lower()

            result = pattern.sub(replace_with_case, result)

        return result

    def _apply_template(self, message: str, message_type: str) -> str:
        """
        Apply message template formatting based on message type.

        Args:
            message: Message with variables already replaced
            message_type: Message category (error, warning, success, status, etc.)

        Returns:
            Fully formatted themed message with prefix, verb, and formatting
        """
        # For unknown message types or empty messages, fall back to status or return as-is
        if not self.messages:
            return message

        # Default to 'status' template if message_type not found
        if message_type not in self.messages:
            if "status" in self.messages:
                message_type = "status"
            else:
                return message

        template = self.messages[message_type]

        # Extract template components
        prefix = template.get("prefix", "")
        verb = template.get("verb", "")
        format_str = template.get("format", "{message}")

        # Apply template formatting
        try:
            formatted = format_str.format(prefix=prefix, verb=verb, message=message)
            return formatted
        except KeyError as e:
            logger.warning(
                f"[LOCAL] Template formatting error for '{message_type}': {e}"
            )
            return message

    def get_theme_info(self) -> Dict[str, Any]:
        """
        Get theme metadata information.

        Returns:
            Dictionary with theme name, style, emoji set, and other metadata
        """
        return {
            "theme_id": self.theme_id,
            "theme_path": str(self.theme_path),
            "variables_count": len(self.variables),
            "templates_count": len(self.messages),
            **self.metadata,
        }

    def list_variables(self) -> Dict[str, str]:
        """
        Get all variable mappings for this theme.

        Returns:
            Dictionary of system_var → theme_var mappings
        """
        return self.variables.copy()

    def list_templates(self) -> Dict[str, Any]:
        """
        Get all message templates for this theme.

        Returns:
            Dictionary of message_type → template configuration
        """
        return self.messages.copy()


def get_available_themes() -> list[str]:
    """
    Get list of all available theme IDs.

    Returns:
        List of theme directory names
    """
    themes_dir = Path(__file__).parent.parent / "data" / "themes"

    if not themes_dir.exists():
        logger.warning(f"[LOCAL] Themes directory not found: {themes_dir}")
        return []

    # Return directories that have variables.json
    available = []
    for theme_dir in themes_dir.iterdir():
        if theme_dir.is_dir() and (theme_dir / "variables.json").exists():
            available.append(theme_dir.name)

    return sorted(available)


def get_theme_metadata(theme_id: str) -> Optional[Dict[str, Any]]:
    """
    Get metadata for a specific theme without loading full overlay.

    Args:
        theme_id: Theme identifier

    Returns:
        Theme metadata dictionary, or None if theme not found
    """
    theme_path = Path(__file__).parent.parent / "data" / "themes" / theme_id
    variables_file = theme_path / "variables.json"

    if not variables_file.exists():
        return None

    try:
        with open(variables_file, "r", encoding="utf-8") as f:
            data = json.load(f)
            return {
                "theme_name": data.get("theme_name", ""),
                "theme_id": data.get("theme_id", theme_id),
                "style": data.get("style", ""),
                "emoji_set": data.get("emoji_set", []),
                "author": data.get("author", ""),
                "tone": data.get("tone", ""),
                "description": data.get("description", ""),
                "version": data.get("version", "1.0.0"),
            }
    except Exception as e:
        logger.error(f"[LOCAL] Failed to read theme metadata for '{theme_id}': {e}")
        return None


# Module-level convenience functions

_current_overlay: Optional[ThemeOverlay] = None


def set_active_theme(theme_id: str) -> bool:
    """
    Set the active theme for the application.

    Args:
        theme_id: Theme identifier (or 'default' for no overlay)

    Returns:
        True if theme loaded successfully, False otherwise
    """
    global _current_overlay

    try:
        _current_overlay = ThemeOverlay(theme_id)
        logger.info(f"[LOCAL] Active theme set to '{theme_id}'")
        return True
    except Exception as e:
        logger.error(f"[LOCAL] Failed to set active theme '{theme_id}': {e}")
        return False


def get_active_theme() -> Optional[ThemeOverlay]:
    """
    Get the currently active theme overlay.

    Returns:
        Active ThemeOverlay instance, or None if no theme active
    """
    return _current_overlay


def apply_theme(message: str, message_type: str = "status") -> str:
    """
    Apply active theme to a message (convenience function).

    Args:
        message: Original system message
        message_type: Message category

    Returns:
        Themed message if theme active, otherwise original message
    """
    if _current_overlay:
        return _current_overlay.apply(message, message_type)
    return message
