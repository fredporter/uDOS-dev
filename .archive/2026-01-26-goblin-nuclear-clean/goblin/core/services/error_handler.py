"""
uDOS Error Handler Service - v1.0.23 Phase 8
Consolidated error handling with boundary validation

Features:
- Smart error messages with context and suggestions
- Data architecture boundary violation detection
- Similar command suggestions using fuzzy matching
- User-friendly error explanations and fix recommendations
- Enhanced error formatting for all error types

This module consolidates:
  - core/services/error_handler.py (boundary validation)
  - core/utils/error_handler.py (generic error handling)

Author: uDOS Development Team
Version: 1.1.0
"""

from typing import List, Optional, Dict, Any
from pathlib import Path
import difflib

from dev.goblin.core.utils.path_validator import is_writable_path, detect_boundary_violation


class ErrorContext:
    """Context information for errors"""

    def __init__(
        self,
        error_type: str,
        message: str,
        command: Optional[str] = None,
        args: Optional[List[str]] = None,
        suggestions: Optional[List[str]] = None,
        fix_steps: Optional[List[str]] = None,
    ):
        """Initialize error context"""
        self.error_type = error_type
        self.message = message
        self.command = command
        self.args = args or []
        self.suggestions = suggestions or []
        self.fix_steps = fix_steps or []


class EnhancedErrorHandler:
    """Enhanced error handling with contextual messages and boundary validation"""

    def __init__(self, logger=None, available_commands: Optional[List[str]] = None):
        """Initialize error handler"""
        self.logger = logger
        self.available_commands = available_commands or []
        self.error_history: List[ErrorContext] = []

    # ========================================================================
    # Boundary Validation Methods (Phase 5: Consolidated from services version)
    # ========================================================================

    def validate_write_operation(
        self, path: str, command: str = None, root: str = None
    ) -> Optional[str]:
        """
        Validate a write operation respects data boundaries.

        Args:
            path: Path to write to
            command: Command attempting the write
            root: Project root

        Returns:
            Error message if invalid, None if valid
        """
        if not is_writable_path(path, root):
            error = f"Cannot write to read-only system directory"
            if command:
                error = f"{command}: {error}"
            return error

        return None

    def check_boundary_violation(
        self, source: str, dest: str, root: str = None
    ) -> Optional[str]:
        """
        Check for cross-boundary violations.

        Args:
            source: Source path
            dest: Destination path
            root: Project root

        Returns:
            Error message if violation detected, None if valid
        """
        return detect_boundary_violation(source, dest, root)

    # ========================================================================
    # Enhanced Error Formatting Methods (Phase 5: From utils version)
    # ========================================================================

    def file_not_found(
        self, filepath: str, available_files: Optional[List[str]] = None
    ) -> str:
        """Enhanced file not found error"""
        suggestions = []

        # Find similar files
        if available_files:
            similar = self._find_similar_strings(filepath, available_files, n=3)
            if similar:
                suggestions.extend([f"  • {f}" for f in similar[:3]])

        output = [
            "┌─────────────────────────────────────────────────────────────────┐",
            "│  ❌ FILE NOT FOUND                                             │",
            "├─────────────────────────────────────────────────────────────────┤",
            f"│  File: {filepath:<55} │",
            "│                                                                 │",
        ]

        if suggestions:
            output.append(
                "│  Did you mean:                                                  │"
            )
            for sugg in suggestions:
                output.append(f"│  {sugg:<61} │")
            output.append(
                "│                                                                 │"
            )

        output.extend(
            [
                "│  Suggestions:                                                   │",
                "│    • Check spelling and case sensitivity                       │",
                "│    • Use fuzzy matching: LOAD wat_pur → water-purification.md │",
                "│    • List files: LIST or ls                                    │",
                "│    • Use file picker: LOAD (no args)                           │",
                "│                                                                 │",
                "│  Common locations:                                              │",
                "│    knowledge/    - Guides and learning content                │",
                "│    data/         - Data files                                  │",
                "│    memory/       - User memory tiers                           │",
                "└─────────────────────────────────────────────────────────────────┘",
            ]
        )

        return "\n".join(output)

    def command_not_found(
        self, command: str, available_commands: Optional[List[str]] = None
    ) -> str:
        """Enhanced command not found error"""
        # Find similar commands
        commands = available_commands or self.available_commands
        similar = self._find_similar_strings(command, commands, n=3)

        output = [
            "┌─────────────────────────────────────────────────────────────────┐",
            "│  ❌ COMMAND NOT FOUND                                          │",
            "├─────────────────────────────────────────────────────────────────┤",
            f"│  Command: {command:<53} │",
            "│                                                                 │",
        ]

        if similar:
            output.append(
                "│  Did you mean:                                                  │"
            )
            for cmd in similar:
                output.append(f"│    • {cmd:<57} │")
            output.append(
                "│                                                                 │"
            )

        output.extend(
            [
                "│  Try:                                                           │",
                "│    • HELP               List all available commands            │",
                "│    • HELP <topic>       Get help on specific topic             │",
                "│    • ?                  Quick help (alias)                     │",
                "│    • DOCS               Browse documentation                   │",
                "│                                                                 │",
                "│  Common commands:                                               │",
                "│    DOCS, LEARN, MEMORY, LOAD, SAVE, EDIT, LIST                │",
                "└─────────────────────────────────────────────────────────────────┘",
            ]
        )

        return "\n".join(output)

    def permission_denied(
        self, resource: str, required_tier: str, current_tier: str
    ) -> str:
        """Enhanced permission denied error"""
        output = [
            "┌─────────────────────────────────────────────────────────────────┐",
            "│  ❌ PERMISSION DENIED                                          │",
            "├─────────────────────────────────────────────────────────────────┤",
            f"│  Resource: {resource:<52} │",
            f"│  Required tier: {required_tier:<47} │",
            f"│  Current tier: {current_tier:<48} │",
            "│                                                                 │",
            "│  How to fix:                                                    │",
        ]

        # Context-specific fixes
        if required_tier.lower() == "private":
            output.extend(
                [
                    "│    1. This is in the PRIVATE tier (encrypted)                 │",
                    "│    2. Only you can access your PRIVATE memory                 │",
                    "│    3. Make sure you're logged in as the correct user          │",
                ]
            )
        elif required_tier.lower() == "admin":
            output.extend(
                [
                    "│    1. This requires ADMIN privileges                          │",
                    "│    2. Contact system administrator to upgrade access          │",
                    "│    3. Or use a lower-privilege alternative if available       │",
                ]
            )
        elif required_tier.lower() == "shared":
            output.extend(
                [
                    "│    1. This is in the SHARED tier (team access)                │",
                    "│    2. Ask team admin to grant you access                      │",
                    "│    3. Or move to COMMUNITY/PUBLIC tier if appropriate         │",
                ]
            )
        else:
            output.extend(
                [
                    "│    1. Check file/directory permissions                        │",
                    "│    2. Contact system administrator if needed                  │",
                    "│    3. Use appropriate memory tier for your access level       │",
                ]
            )

        output.extend(
            [
                "│                                                                 │",
                "│  Memory tier guide:                                             │",
                "│    🔒 PRIVATE    - You only                                    │",
                "│    🔐 SHARED     - Team members                                │",
                "│    👥 COMMUNITY  - Group access                                │",
                "│    🌍 PUBLIC     - Everyone                                    │",
                "└─────────────────────────────────────────────────────────────────┘",
            ]
        )

        return "\n".join(output)

    def invalid_argument(
        self,
        param_name: str,
        provided_value: str,
        valid_values: Optional[List[str]] = None,
        expected: Optional[str] = None,
    ) -> str:
        """Enhanced invalid argument error"""
        # Find similar valid values
        suggestions = []
        if valid_values:
            similar = self._find_similar_strings(provided_value, valid_values, n=3)
            if similar:
                suggestions = similar[:3]

        output = [
            "┌─────────────────────────────────────────────────────────────────┐",
            "│  ❌ INVALID ARGUMENT                                           │",
            "├─────────────────────────────────────────────────────────────────┤",
            f"│  Parameter: {param_name:<51} │",
            f"│  Provided: {provided_value:<52} │",
        ]

        if expected:
            output.append(f"│  Expected: {expected:<52} │")

        output.append(
            "│                                                                 │"
        )

        if suggestions:
            output.append(
                "│  Did you mean:                                                  │"
            )
            for sugg in suggestions:
                output.append(f"│    • {sugg:<57} │")
            output.append(
                "│                                                                 │"
            )

        if valid_values:
            output.append(
                "│  Valid values:                                                  │"
            )
            for val in valid_values[:5]:  # Show max 5
                output.append(f"│    • {val:<57} │")
            if len(valid_values) > 5:
                output.append(f"│    ... and {len(valid_values) - 5} more{' ':<39} │")
            output.append(
                "│                                                                 │"
            )

        output.extend(
            [
                "│  Try:                                                           │",
                "│    • Check spelling and case sensitivity                       │",
                "│    • Use --help flag for valid options                         │",
                "│    • Use tab completion if available                           │",
                "└─────────────────────────────────────────────────────────────────┘",
            ]
        )

        return "\n".join(output)

    def syntax_error(
        self,
        command: str,
        invalid_syntax: str,
        expected_format: Optional[str] = None,
        example: Optional[str] = None,
    ) -> str:
        """Enhanced syntax error"""
        output = [
            "┌─────────────────────────────────────────────────────────────────┐",
            "│  ❌ SYNTAX ERROR                                               │",
            "├─────────────────────────────────────────────────────────────────┤",
            f"│  Command: {command:<53} │",
            f"│  Invalid syntax: {invalid_syntax:<46} │",
        ]

        if expected_format:
            output.extend(
                [
                    "│                                                                 │",
                    "│  Expected format:                                               │",
                    f"│    {expected_format:<61} │",
                ]
            )

        if example:
            output.extend(
                [
                    "│                                                                 │",
                    "│  Example:                                                       │",
                    f"│    {example:<61} │",
                ]
            )

        output.extend(
            [
                "│                                                                 │",
                "│  uCODE syntax:                                                  │",
                "│    [MODULE|COMMAND*PARAM1*PARAM2]                              │",
                "│                                                                 │",
                "│  Common examples:                                               │",
                "│    [FILE|LOAD*README.md]                                       │",
                "│    [MEMORY|SAVE*notes.txt*PRIVATE]                             │",
                "│    [DOCS|SEARCH*git*manual]                                    │",
                "│                                                                 │",
                "│  See also:                                                      │",
                "│    DOCS --handbook syntax    Syntax guide                     │",
                "│    LEARN ucode              uCODE tutorial                    │",
                "└─────────────────────────────────────────────────────────────────┘",
            ]
        )

        return "\n".join(output)

    def timeout_error(
        self, operation: str, timeout_seconds: int, suggestion: Optional[str] = None
    ) -> str:
        """Enhanced timeout error"""
        output = [
            "┌─────────────────────────────────────────────────────────────────┐",
            "│  ⏱️  OPERATION TIMEOUT                                         │",
            "├─────────────────────────────────────────────────────────────────┤",
            f"│  Operation: {operation:<51} │",
            f"│  Timeout: {timeout_seconds}s{' '*(55-len(str(timeout_seconds)))} │",
            "│                                                                 │",
            "│  This operation took too long to complete.                      │",
            "│                                                                 │",
        ]

        if suggestion:
            output.extend(
                [
                    "│  Suggestion:                                                    │",
                    f"│    {suggestion:<61} │",
                    "│                                                                 │",
                ]
            )

        output.extend(
            [
                "│  Possible causes:                                               │",
                "│    • Network connectivity issues                                │",
                "│    • Large file/dataset processing                              │",
                "│    • System resource constraints                                │",
                "│                                                                 │",
                "│  Try:                                                           │",
                "│    • Check network connection (if online operation)             │",
                "│    • Break into smaller operations                              │",
                "│    • Increase timeout: --timeout=<seconds>                     │",
                "│    • Use background mode: --background                         │",
                "│                                                                 │",
                "│  Performance tips:                                              │",
                "│    • Use caching for repeated operations                        │",
                "│    • Process files in chunks                                    │",
                "│    • Enable lazy loading                                        │",
                "└─────────────────────────────────────────────────────────────────┘",
            ]
        )

        return "\n".join(output)

    def format_exception(
        self, exception: Exception, context: Optional[Dict] = None
    ) -> str:
        """Format exception with context"""
        exc_type = type(exception).__name__
        exc_message = str(exception)

        output = [
            "┌─────────────────────────────────────────────────────────────────┐",
            f"│  ❌ {exc_type:<60} │",
            "├─────────────────────────────────────────────────────────────────┤",
            f"│  {exc_message:<61} │",
        ]

        if context:
            output.append(
                "│                                                                 │"
            )
            output.append(
                "│  Context:                                                       │"
            )
            for key, value in context.items():
                output.append(f"│    {key}: {str(value):<53} │")

        output.extend(
            [
                "│                                                                 │",
                "│  This is an unexpected error. Please report if persistent.      │",
                "│                                                                 │",
                "│  Debug steps:                                                   │",
                "│    1. Check error log: LOG --errors                            │",
                "│    2. Try with --verbose flag for more details                 │",
                "│    3. Report to GitHub: github.com/fredporter/uDOS-dev/issues      │",
                "└─────────────────────────────────────────────────────────────────┘",
            ]
        )

        return "\n".join(output)

    # ========================================================================
    # Utility Methods
    # ========================================================================

    def _find_similar_strings(
        self, target: str, candidates: List[str], n: int = 3
    ) -> List[str]:
        """Find similar strings using difflib"""
        if not candidates:
            return []

        # Use lower cutoff for better fuzzy matching
        matches = difflib.get_close_matches(target, candidates, n=n, cutoff=0.5)

        # If no matches, try case-insensitive matching
        if not matches:
            candidates_lower = [c.lower() for c in candidates]
            matches_lower = difflib.get_close_matches(
                target.lower(), candidates_lower, n=n, cutoff=0.5
            )
            # Map back to original case
            matches = [candidates[candidates_lower.index(m)] for m in matches_lower]

        return matches

    def _find_similar_files(
        self, target: str, search_paths: List[str], n: int = 3
    ) -> List[str]:
        """Find similar filenames in search paths"""
        candidates = []
        target_name = Path(target).name.lower()

        for search_path in search_paths:
            path = Path(search_path)
            if path.is_dir():
                for file in path.rglob("*"):
                    if file.is_file():
                        candidates.append(str(file))

        # Find similar based on filename
        similar = []
        for candidate in candidates:
            candidate_name = Path(candidate).name.lower()
            ratio = difflib.SequenceMatcher(None, target_name, candidate_name).ratio()
            if ratio > 0.6:
                similar.append((ratio, candidate))

        # Sort by similarity and return top n
        similar.sort(reverse=True)
        return [f for _, f in similar[:n]]


# Convenience function
def get_error_handler(
    logger=None, available_commands: Optional[List[str]] = None
) -> EnhancedErrorHandler:
    """Get error handler instance"""
    return EnhancedErrorHandler(logger=logger, available_commands=available_commands)
