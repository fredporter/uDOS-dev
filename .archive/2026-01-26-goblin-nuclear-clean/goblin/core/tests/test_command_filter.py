"""
Tests for command filter - Dev Mode boundary enforcement
"""

import pytest
from dev.goblin.core.security.command_filter import (
    CommandFilter,
    AccessLevel,
    check_api_command,
    get_command_filter,
)


class TestCommandFilter:
    """Test command filtering for API access."""

    def test_user_commands_allowed(self):
        """User-safe commands should be allowed via API."""
        cf = CommandFilter()

        # These should be allowed
        user_commands = ["HELP", "VERSION", "STATUS", "FILE LIST", "KNOWLEDGE"]

        for cmd in user_commands:
            allowed, _ = cf.is_api_allowed(cmd)
            assert allowed, f"User command '{cmd}' should be allowed"

    def test_dev_commands_blocked(self):
        """Dev-only commands should be blocked via API."""
        cf = CommandFilter()

        # These should be blocked
        dev_commands = ["BUILD TCZ", "DEPLOY CORE", "REPAIR GIT", "CLEAN ALL"]

        for cmd in dev_commands:
            allowed, error = cf.is_api_allowed(cmd)
            assert not allowed, f"Dev command '{cmd}' should be blocked"
            assert error is not None, f"Should have error message for '{cmd}'"

    def test_access_level_detection(self):
        """Test access level detection."""
        cf = CommandFilter()

        # User level
        assert cf.get_access_level("HELP") == AccessLevel.USER
        assert cf.get_access_level("VERSION") == AccessLevel.USER

        # Wizard level
        assert cf.get_access_level("AI ASK") == AccessLevel.WIZARD
        assert cf.get_access_level("SCRAPE") == AccessLevel.WIZARD

        # Dev level
        assert cf.get_access_level("BUILD") == AccessLevel.DEV
        assert cf.get_access_level("REPAIR") == AccessLevel.DEV

    def test_wizard_commands_need_auth(self):
        """Wizard commands should require Wizard Server auth."""
        cf = CommandFilter()

        assert cf.is_wizard_required("AI ASK question")
        assert cf.is_wizard_required("CHAT hello")
        assert cf.is_wizard_required("SCRAPE url")

    def test_case_insensitive(self):
        """Commands should be case-insensitive."""
        cf = CommandFilter()

        allowed1, _ = cf.is_api_allowed("help")
        allowed2, _ = cf.is_api_allowed("HELP")
        allowed3, _ = cf.is_api_allowed("Help")

        assert allowed1 == allowed2 == allowed3

    def test_singleton_instance(self):
        """get_command_filter should return singleton."""
        cf1 = get_command_filter()
        cf2 = get_command_filter()

        assert cf1 is cf2

    def test_convenience_function(self):
        """check_api_command convenience function."""
        allowed, error = check_api_command("HELP")
        assert allowed
        assert error is None

        allowed, error = check_api_command("BUILD TCZ")
        assert not allowed
        assert error is not None

    def test_blocked_message(self):
        """Test user-friendly blocked messages."""
        cf = CommandFilter()

        msg = cf.get_blocked_message("BUILD TCZ")
        assert "TUI" in msg

        msg = cf.get_blocked_message("GIT STATUS")
        assert "Vibe CLI" in msg or "TUI" in msg


class TestBlockedPatterns:
    """Test pattern-based blocking."""

    def test_wildcard_patterns(self):
        """Wildcard patterns should block correctly."""
        cf = CommandFilter()

        # BUILD * pattern
        allowed, _ = cf.is_api_allowed("BUILD TCZ")
        assert not allowed

        allowed, _ = cf.is_api_allowed("BUILD EXTENSION")
        assert not allowed

    def test_partial_match_not_blocked(self):
        """Partial matches shouldn't incorrectly block."""
        cf = CommandFilter()

        # "INSTALL" pattern shouldn't block "INSTALLINFO" if that existed
        # (testing pattern matching accuracy)
        allowed, _ = cf.is_api_allowed("FILE LIST")  # Should be allowed
        assert allowed


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
