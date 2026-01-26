"""
API Command Filter - Enforces dev/user mode boundaries

Blocks dev-only commands from API access.
Ensures Tauri app can only execute user-safe commands.
"""

import json
import re
from pathlib import Path
from typing import Tuple, Optional
from enum import Enum

from dev.goblin.core.services.logging_manager import get_logger

logger = get_logger("api-filter")


class AccessLevel(Enum):
    """Command access levels."""

    USER = "user"  # Safe for API/Tauri
    WIZARD = "wizard"  # Requires Wizard auth
    DEV = "dev"  # TUI only


class CommandFilter:
    """
    Filters commands based on access level.

    Ensures API only executes user-safe commands.
    Dev commands are blocked with helpful error messages.
    """

    def __init__(self):
        self._load_access_config()

    def _load_access_config(self):
        """Load command access configuration."""
        config_path = Path(__file__).parent.parent / "data" / "command_access.json"

        try:
            with open(config_path, "r") as f:
                self.config = json.load(f)
        except Exception as e:
            logger.error(f"[ERROR] Failed to load command_access.json: {e}")
            # Fallback to restrictive defaults
            self.config = {
                "commands": {"user": [], "wizard": [], "dev": []},
                "api_blocked_patterns": ["*"],
            }

        # Compile blocked patterns for faster matching
        self._blocked_patterns = []
        for pattern in self.config.get("api_blocked_patterns", []):
            # Convert simple wildcard to regex
            regex = pattern.replace("*", ".*")
            self._blocked_patterns.append(re.compile(f"^{regex}$", re.IGNORECASE))

    def get_access_level(self, command: str) -> AccessLevel:
        """
        Determine access level for a command.

        Args:
            command: Command string (e.g., "FILE READ", "BUILD TCZ")

        Returns:
            AccessLevel enum value
        """
        cmd_upper = command.upper().strip()
        cmd_base = cmd_upper.split()[0] if cmd_upper else ""

        # Check dev commands first (most restrictive)
        for dev_cmd in self.config["commands"].get("dev", []):
            if cmd_upper.startswith(dev_cmd.upper()):
                return AccessLevel.DEV

        # Check wizard commands
        for wizard_cmd in self.config["commands"].get("wizard", []):
            if cmd_upper.startswith(wizard_cmd.upper()):
                return AccessLevel.WIZARD

        # Check user commands
        for user_cmd in self.config["commands"].get("user", []):
            if cmd_upper.startswith(user_cmd.upper()):
                return AccessLevel.USER

        # Default to dev (restrictive) for unknown commands
        return AccessLevel.DEV

    def is_api_allowed(self, command: str) -> Tuple[bool, Optional[str]]:
        """
        Check if command is allowed via API.

        Args:
            command: Command string

        Returns:
            Tuple of (allowed, error_message)
        """
        cmd_upper = command.upper().strip()

        # Check against blocked patterns
        for pattern in self._blocked_patterns:
            if pattern.match(cmd_upper):
                return (
                    False,
                    f"Command '{command}' is dev-only. Use TUI for this operation.",
                )

        # Check access level
        level = self.get_access_level(command)

        if level == AccessLevel.DEV:
            return (
                False,
                f"Command '{command}' requires dev mode. Use TUI with Vibe CLI.",
            )

        return True, None

    def is_wizard_required(self, command: str) -> bool:
        """Check if command requires Wizard Server auth."""
        return self.get_access_level(command) == AccessLevel.WIZARD

    def get_user_commands(self) -> list:
        """Get list of user-safe commands."""
        return self.config["commands"].get("user", [])

    def get_blocked_message(self, command: str) -> str:
        """Get user-friendly message for blocked command."""
        cmd_base = command.upper().split()[0] if command else "UNKNOWN"

        messages = {
            "BUILD": "Package building is a dev operation. Run BUILD in TUI.",
            "DEPLOY": "Deployment requires dev mode. Use TUI with Vibe CLI.",
            "INSTALL": "System installation requires TUI access.",
            "REPAIR": "Git repair operations require TUI. Run: REPAIR in terminal.",
            "CLEAN": "Cleanup operations require TUI access.",
            "TIDY": "Workspace organization requires TUI access.",
            "BACKUP": "Backup operations require TUI access.",
            "RESTORE": "Restore operations require TUI access.",
            "GIT": "Git operations require TUI with Vibe CLI.",
            "VIBE": "Vibe CLI is TUI-only.",
            "CONFIG": "Configuration changes require TUI access.",
            "KEY": "Key management requires TUI access.",
            "SANDBOX": "Sandbox operations require TUI access.",
            "REBOOT": "System reboot requires TUI access.",
        }

        return messages.get(cmd_base, f"'{command}' is a dev-only command. Use TUI.")


# Singleton instance
_filter_instance = None


def get_command_filter() -> CommandFilter:
    """Get singleton CommandFilter instance."""
    global _filter_instance
    if _filter_instance is None:
        _filter_instance = CommandFilter()
    return _filter_instance


def check_api_command(command: str) -> Tuple[bool, Optional[str]]:
    """
    Convenience function to check if command is API-allowed.

    Args:
        command: Command string

    Returns:
        Tuple of (allowed, error_message)
    """
    return get_command_filter().is_api_allowed(command)
