"""
Theme Overlay System - Test Suite
==================================

Tests for theme_overlay.py functionality including:
- Theme loading and configuration
- Variable replacement
- Message template formatting
- Case preservation
- Edge cases

Run with: pytest core/tests/test_theme_overlay.py -v
"""

import pytest
from pathlib import Path
from dev.goblin.core.services.theme_overlay import (
    ThemeOverlay,
    get_available_themes,
    get_theme_metadata,
    set_active_theme,
    get_active_theme,
    apply_theme,
)


class TestThemeLoading:
    """Test theme configuration loading."""

    def test_default_theme_no_overlay(self):
        """Default theme should not apply any overlay."""
        overlay = ThemeOverlay("default")
        message = "Error in sandbox"
        assert overlay.apply(message) == message

    def test_theme_loading_dungeon_adventure(self):
        """Test loading dungeon-adventure theme."""
        overlay = ThemeOverlay("dungeon-adventure")
        assert overlay.theme_id == "dungeon-adventure"
        assert len(overlay.variables) > 0
        assert len(overlay.messages) > 0
        assert "Sandbox" in overlay.variables
        assert overlay.variables["Sandbox"] == "Dungeon"

    def test_theme_metadata(self):
        """Test theme metadata extraction."""
        overlay = ThemeOverlay("dungeon-adventure")
        info = overlay.get_theme_info()
        assert info["theme_id"] == "dungeon-adventure"
        assert info["theme_name"] == "Dungeon Adventure"
        assert "variables_count" in info
        assert "templates_count" in info

    def test_nonexistent_theme_falls_back(self):
        """Non-existent theme should fall back to default."""
        overlay = ThemeOverlay("nonexistent-theme-12345")
        message = "Test message"
        # Should return original message
        assert overlay.apply(message) == message


class TestVariableReplacement:
    """Test system variable → theme vocabulary replacement."""

    def test_simple_replacement(self):
        """Test basic word replacement."""
        overlay = ThemeOverlay("dungeon-adventure")
        message = "Error in sandbox"
        result = overlay._replace_variables(message)
        assert "dungeon" in result.lower()
        assert "sandbox" not in result.lower()

    def test_multiple_replacements(self):
        """Test multiple variables in one message."""
        overlay = ThemeOverlay("dungeon-adventure")
        message = "Plugin loaded in sandbox"
        result = overlay._replace_variables(message)
        assert "enchantment" in result.lower()
        assert "dungeon" in result.lower()

    def test_case_preservation_upper(self):
        """Test uppercase preservation."""
        overlay = ThemeOverlay("dungeon-adventure")
        message = "ERROR IN SANDBOX"
        result = overlay._replace_variables(message)
        # Should preserve uppercase
        assert result.isupper()

    def test_case_preservation_title(self):
        """Test title case preservation."""
        overlay = ThemeOverlay("dungeon-adventure")
        message = "Error In Sandbox"
        result = overlay._replace_variables(message)
        # Check that words start with capitals
        words = result.split()
        assert all(w[0].isupper() for w in words if w)

    def test_word_boundary_matching(self):
        """Test that replacements respect word boundaries."""
        overlay = ThemeOverlay("dungeon-adventure")
        # Should not replace partial matches
        message = "sandboxed environment"
        result = overlay._replace_variables(message)
        # "sandboxed" should not be replaced (not exact word match)
        assert "sandboxed" in result.lower()

    def test_longest_match_first(self):
        """Test that longer phrases are replaced before shorter ones."""
        overlay = ThemeOverlay("dungeon-adventure")
        # "Syntax Error" should be replaced as a whole, not just "Error"
        message = "Syntax Error detected"
        result = overlay._replace_variables(message)
        assert "cursed incantation" in result.lower()


class TestMessageTemplates:
    """Test message template formatting."""

    def test_error_template(self):
        """Test error message template formatting."""
        overlay = ThemeOverlay("dungeon-adventure")
        message = "File not found"
        result = overlay.apply(message, "error")
        assert "⚔️" in result  # Should have emoji prefix
        assert "CURSED INCANTATION" in result.upper() or "TRAP" in result.upper()

    def test_success_template(self):
        """Test success message template formatting."""
        overlay = ThemeOverlay("dungeon-adventure")
        message = "Operation completed"
        result = overlay.apply(message, "success")
        assert "💎" in result  # Should have treasure emoji
        assert "TREASURE" in result.upper() or "FOUND" in result.upper()

    def test_warning_template(self):
        """Test warning message template formatting."""
        overlay = ThemeOverlay("dungeon-adventure")
        message = "Low memory"
        result = overlay.apply(message, "warning")
        assert "🧙" in result  # Should have wizard emoji
        assert "EERIE" in result.upper() or "FEELING" in result.upper()

    def test_status_template(self):
        """Test status message template formatting."""
        overlay = ThemeOverlay("dungeon-adventure")
        message = "System ready"
        result = overlay.apply(message, "status")
        assert "🧙" in result  # Should have wizard emoji


class TestEndToEnd:
    """Test complete theme overlay workflow."""

    def test_full_overlay_pipeline(self):
        """Test variable replacement + template formatting together."""
        overlay = ThemeOverlay("dungeon-adventure")
        message = "Plugin loaded in sandbox"
        result = overlay.apply(message, "success")

        # Should have template formatting
        assert "💎" in result
        # Should have variable replacement
        assert "enchantment" in result.lower()
        assert "dungeon" in result.lower()
        # Should not have original words
        assert "plugin" not in result.lower()
        assert "sandbox" not in result.lower()

    def test_error_with_system_vars(self):
        """Test error message with system variable replacement."""
        overlay = ThemeOverlay("dungeon-adventure")
        message = "Syntax Error in config file"
        result = overlay.apply(message, "error")

        # Should have error formatting
        assert "⚔️" in result
        # Should replace "Syntax Error" and "config"
        assert "cursed" in result.lower() or "trap" in result.lower()
        assert "dungeon settings" in result.lower() or "settings" in result.lower()


class TestUtilityFunctions:
    """Test module-level utility functions."""

    def test_get_available_themes(self):
        """Test listing available themes."""
        themes = get_available_themes()
        assert isinstance(themes, list)
        # Should have at least dungeon-adventure
        assert "dungeon-adventure" in themes

    def test_get_theme_metadata(self):
        """Test getting theme metadata without loading full overlay."""
        metadata = get_theme_metadata("dungeon-adventure")
        assert metadata is not None
        assert metadata["theme_name"] == "Dungeon Adventure"
        assert "emoji_set" in metadata
        assert "style" in metadata

    def test_get_theme_metadata_nonexistent(self):
        """Test getting metadata for non-existent theme."""
        metadata = get_theme_metadata("nonexistent-theme-xyz")
        assert metadata is None

    def test_set_active_theme(self):
        """Test setting global active theme."""
        success = set_active_theme("dungeon-adventure")
        assert success is True

        active = get_active_theme()
        assert active is not None
        assert active.theme_id == "dungeon-adventure"

    def test_apply_theme_convenience(self):
        """Test convenience function for applying active theme."""
        set_active_theme("dungeon-adventure")
        message = "Error in sandbox"
        result = apply_theme(message, "error")

        assert "⚔️" in result
        assert "dungeon" in result.lower()


class TestMultipleThemes:
    """Test behavior across different themes."""

    def test_stranger_things_theme(self):
        """Test stranger-things theme if available."""
        themes = get_available_themes()
        if "stranger-things" not in themes:
            pytest.skip("stranger-things theme not available")

        overlay = ThemeOverlay("stranger-things")
        message = "Error in sandbox"
        result = overlay.apply(message, "error")

        # Should be themed differently than dungeon
        assert result != message  # Should be modified
        # Should have stranger-things vocabulary (campaigns, demogorgon, etc.)
        assert (
            "campaign" in result.lower()
            or "demogorgon" in result.lower()
            or "breach" in result.lower()
        )

    def test_switching_themes(self):
        """Test switching between themes."""
        # Start with dungeon
        overlay1 = ThemeOverlay("dungeon-adventure")
        message = "Error in sandbox"
        result1 = overlay1.apply(message, "error")

        # Switch to default
        overlay2 = ThemeOverlay("default")
        result2 = overlay2.apply(message, "error")

        # Results should be different
        assert result1 != result2
        assert result2 == message  # Default returns original


class TestEdgeCases:
    """Test edge cases and error handling."""

    def test_empty_message(self):
        """Test applying theme to empty message."""
        overlay = ThemeOverlay("dungeon-adventure")
        result = overlay.apply("")
        # Empty message should return empty (no template applied)
        assert result == ""

    def test_message_with_no_variables(self):
        """Test message that doesn't contain any system variables."""
        overlay = ThemeOverlay("dungeon-adventure")
        message = "Hello world"
        result = overlay.apply(message, "status")
        # Should still apply template formatting
        assert "🧙" in result

    def test_invalid_message_type(self):
        """Test applying non-existent message type."""
        overlay = ThemeOverlay("dungeon-adventure")
        message = "Test message"
        result = overlay.apply(message, "nonexistent-type")
        # Should return message with variable replacements but no template
        assert result is not None

    def test_special_characters_in_message(self):
        """Test messages with special characters."""
        overlay = ThemeOverlay("dungeon-adventure")
        message = "Error: File 'test.txt' not found!"
        result = overlay.apply(message, "error")
        # Should handle special characters gracefully
        assert "'" in result
        assert "!" in result

    def test_unicode_in_message(self):
        """Test messages with unicode characters."""
        overlay = ThemeOverlay("dungeon-adventure")
        message = "Folder '📁 Documents' created"
        result = overlay.apply(message, "success")
        # Should preserve unicode
        assert "📁" in result


class TestListMethods:
    """Test methods that return theme information."""

    def test_list_variables(self):
        """Test getting all variable mappings."""
        overlay = ThemeOverlay("dungeon-adventure")
        variables = overlay.list_variables()
        assert isinstance(variables, dict)
        assert "Sandbox" in variables
        assert len(variables) > 10  # Should have many mappings

    def test_list_templates(self):
        """Test getting all message templates."""
        overlay = ThemeOverlay("dungeon-adventure")
        templates = overlay.list_templates()
        assert isinstance(templates, dict)
        assert "error" in templates
        assert "success" in templates
        assert "warning" in templates
        assert "status" in templates


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
