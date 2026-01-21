"""
Command Restrictions - Mobile Console Command Enforcement
=========================================================

Enforces command restrictions for mobile console devices.
Integrates with the pairing manager and command dispatcher.

Restriction Levels:
  - FULL: All commands allowed (device owner)
  - RESTRICTED: Whitelist of safe commands (mobile console)
  - READONLY: View-only commands (guest)

Security:
  - Mobile consoles cannot modify files
  - Mobile consoles cannot access settings
  - Mobile consoles cannot run scripts
  - All file access sandboxed
"""

from typing import Dict, Any, Optional, List, Tuple, Set
from enum import Enum
from dataclasses import dataclass
from pathlib import Path

from dev.goblin.core.services.logging_manager import get_logger

logger = get_logger("command-restrictions")


class RestrictionLevel(Enum):
    """Command restriction levels."""

    FULL = "full"  # Device owner - all commands
    RESTRICTED = "restricted"  # Mobile console - safe commands only
    READONLY = "readonly"  # Guest - view only


@dataclass
class CommandContext:
    """Context for command authorization."""

    device_id: str
    device_role: str
    session_token: Optional[str]
    transport: str  # mesh, qr, audio, local
    command: str
    params: List[str]


class CommandRestrictions:
    """
    Enforces command restrictions based on device role and transport.

    Used by the command dispatcher to check if a command is allowed
    before execution.
    """

    # Commands safe for mobile console (read-only, informational)
    SAFE_COMMANDS: Set[str] = {
        # Information
        "HELP",
        "VERSION",
        "STATUS",
        "TIME",
        "DATE",
        # Navigation
        "VIEW",
        "LIST",
        "READ",
        "SEARCH",
        "FIND",
        # Knowledge
        "KNOWLEDGE",
        "GUIDE",
        "TUTORIAL",
        "WIKI",
        "K",  # Alias for KNOWLEDGE
        # Workflow (read-only)
        "WORKFLOW",
        "TASK",  # View only
        # Display
        "GRID",
        "LOCATE",
        "MAP",
        # System info
        "DEVICE",
        "NETWORK",
    }

    # Commands that require parameters to be safe
    CONDITIONAL_COMMANDS: Dict[str, List[str]] = {
        "FILE": ["LIST", "VIEW", "READ"],  # FILE EDIT/WRITE not allowed
        "PLUGIN": ["LIST", "STATUS", "INFO"],  # PLUGIN INSTALL not allowed
        "PAIR": ["STATUS", "LIST"],  # PAIR NEW/REVOKE not allowed
        "AUDIO": ["TEST", "DEVICES"],  # AUDIO TRANSMIT not allowed
    }

    # Commands never allowed for mobile
    BLOCKED_COMMANDS: Set[str] = {
        # File modification
        "EDIT",
        "WRITE",
        "NEW",
        "DELETE",
        "COPY",
        "MOVE",
        "RENAME",
        # System modification
        "CONFIG",
        "SETTINGS",
        "INSTALL",
        "UNINSTALL",
        # Scripting
        "RUN",
        "EXEC",
        "SCRIPT",
        "UCODE",
        # Security sensitive
        "KEY",
        "SECRET",
        "TOKEN",
        "EXPORT",
        "IMPORT",
        # Administrative
        "ADMIN",
        "WIZARD",
        "DEBUG",
        "EVAL",
        # Transport commands
        "TRANSMIT",
        "SEND",  # Can receive but not transmit
    }

    # Sandbox paths for mobile file access
    SANDBOX_PATHS: List[str] = [
        "memory/sandbox",
        "memory/workflows",
        "knowledge",
        "wiki",
    ]

    def __init__(self, pairing_manager=None):
        """
        Initialize command restrictions.

        Args:
            pairing_manager: Optional MobilePairingManager instance
        """
        self.pairing_manager = pairing_manager

    def get_restriction_level(self, device_role: str) -> RestrictionLevel:
        """Get restriction level for device role."""
        if device_role == "device_owner":
            return RestrictionLevel.FULL
        elif device_role == "mobile_console":
            return RestrictionLevel.RESTRICTED
        elif device_role == "guest":
            return RestrictionLevel.READONLY
        else:
            return RestrictionLevel.READONLY  # Default to most restrictive

    def authorize(self, context: CommandContext) -> Tuple[bool, str]:
        """
        Authorize a command for execution.

        Args:
            context: Command context with device info

        Returns:
            Tuple of (authorized, message)
        """
        cmd = context.command.upper()
        params = [p.upper() for p in context.params] if context.params else []

        level = self.get_restriction_level(context.device_role)

        # Full access - allow everything
        if level == RestrictionLevel.FULL:
            return True, "Full access"

        # Check blocked commands first
        if cmd in self.BLOCKED_COMMANDS:
            logger.warning(
                f"[RESTRICT] Blocked command '{cmd}' for {context.device_id}"
            )
            return False, f"Command '{cmd}' not allowed for {context.device_role}"

        # Check safe commands
        if cmd in self.SAFE_COMMANDS:
            return True, "Safe command"

        # Check conditional commands
        if cmd in self.CONDITIONAL_COMMANDS:
            allowed_subcommands = self.CONDITIONAL_COMMANDS[cmd]
            if params and params[0] in allowed_subcommands:
                return True, f"Allowed subcommand: {cmd} {params[0]}"
            else:
                subcmd = params[0] if params else "(none)"
                return False, f"Subcommand '{subcmd}' not allowed for {cmd}"

        # Default: block unknown commands for restricted users
        if level == RestrictionLevel.RESTRICTED:
            logger.info(
                f"[RESTRICT] Unknown command '{cmd}' blocked for mobile console"
            )
            return False, f"Command '{cmd}' not recognized as safe"

        # Readonly - only allow view commands
        if level == RestrictionLevel.READONLY:
            if cmd in {"VIEW", "READ", "LIST", "HELP"}:
                return True, "Read-only command"
            return False, "Read-only access"

        return False, "Authorization failed"

    def validate_file_access(
        self, context: CommandContext, filepath: str
    ) -> Tuple[bool, str]:
        """
        Validate file access for mobile console.

        Args:
            context: Command context
            filepath: Path being accessed

        Returns:
            Tuple of (allowed, message)
        """
        level = self.get_restriction_level(context.device_role)

        # Full access - allow all files
        if level == RestrictionLevel.FULL:
            return True, "Full file access"

        # Check sandbox paths
        filepath_lower = filepath.lower().replace("\\", "/")

        for sandbox in self.SANDBOX_PATHS:
            if sandbox in filepath_lower:
                return True, f"Sandbox access: {sandbox}"

        # Block access outside sandbox
        logger.warning(
            f"[RESTRICT] File access denied: {filepath} for {context.device_id}"
        )
        return False, "File access outside sandbox not allowed"

    def get_allowed_commands(self, device_role: str) -> List[str]:
        """Get list of allowed commands for a device role."""
        level = self.get_restriction_level(device_role)

        if level == RestrictionLevel.FULL:
            return ["*"]  # All commands

        commands = list(self.SAFE_COMMANDS)

        # Add conditional commands with allowed subcommands
        for cmd, subs in self.CONDITIONAL_COMMANDS.items():
            for sub in subs:
                commands.append(f"{cmd} {sub}")

        return sorted(commands)

    def get_blocked_commands(self, device_role: str) -> List[str]:
        """Get list of blocked commands for a device role."""
        level = self.get_restriction_level(device_role)

        if level == RestrictionLevel.FULL:
            return []

        return sorted(self.BLOCKED_COMMANDS)


# Singleton instance
_restrictions: Optional[CommandRestrictions] = None


def get_command_restrictions(pairing_manager=None) -> CommandRestrictions:
    """Get command restrictions singleton."""
    global _restrictions
    if _restrictions is None:
        _restrictions = CommandRestrictions(pairing_manager)
    return _restrictions
