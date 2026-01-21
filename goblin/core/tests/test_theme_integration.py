"""
Theme Integration Tests
=======================

Verifies theme bootstrap and display formatting integration.
"""

import os
import io
import sys
import contextlib
import pytest

from dev.goblin.core.services.theme_bootstrap import init_theme_from_config
from dev.goblin.core.services.theme_overlay import get_active_theme, set_active_theme
from dev.goblin.core.services.theme_output import format_for_display, themed_print


def test_bootstrap_from_env(monkeypatch):
    """Init theme from THEME_OVERLAY env."""
    monkeypatch.setenv("THEME_OVERLAY", "dungeon-adventure")
    # Ensure active theme resets
    set_active_theme("default")
    active = init_theme_from_config()
    assert active == "dungeon-adventure"
    overlay = get_active_theme()
    assert overlay is not None
    assert overlay.theme_id == "dungeon-adventure"


def test_bootstrap_fallback_theme_env(monkeypatch):
    """Fallback to THEME if THEME_OVERLAY not set."""
    monkeypatch.delenv("THEME_OVERLAY", raising=False)
    monkeypatch.setenv("THEME", "dungeon-adventure")
    set_active_theme("default")
    active = init_theme_from_config()
    assert active == "dungeon-adventure"


def test_format_for_display_applies_overlay():
    """format_for_display should apply overlay when active."""
    set_active_theme("dungeon-adventure")
    original = "Error in sandbox"
    themed = format_for_display(original, "error")
    assert themed != original
    assert "⚔️" in themed
    assert "dungeon" in themed.lower()


def test_themed_print_outputs_overlay():
    """themed_print should print themed content to stdout."""
    set_active_theme("dungeon-adventure")
    buf = io.StringIO()
    with contextlib.redirect_stdout(buf):
        themed_print("Plugin loaded successfully", "success")
    output = buf.getvalue().strip()
    assert output
    assert "💎" in output
    assert "enchantment" in output.lower() or "plugin" in output.lower()


def test_disable_overlay_results_in_original():
    """When overlay disabled, output should match original input apart from templates."""
    set_active_theme("default")
    original = "System ready"
    themed = format_for_display(original, "status")
    assert themed == original
