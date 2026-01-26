#!/usr/bin/env python3
"""
Theme Overlay Demo
==================

Demonstrates the ThemeOverlay system with all 7 themes.

Usage:
    python demo_theme_overlay.py
"""

import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from dev.goblin.core.services.theme_overlay import (
    ThemeOverlay,
    get_available_themes,
    get_theme_metadata,
)


def print_separator(char="=", length=70):
    """Print a visual separator."""
    print(char * length)


def demo_theme(theme_id: str):
    """Demonstrate a specific theme."""
    print_separator()
    print(f"  THEME: {theme_id}")
    print_separator()

    # Load theme
    overlay = ThemeOverlay(theme_id)
    info = overlay.get_theme_info()

    # Show metadata
    print(f"\n📋 Metadata:")
    print(f"   Name: {info.get('theme_name', 'N/A')}")
    print(f"   Style: {info.get('style', 'N/A')}")
    print(f"   Emojis: {' '.join(info.get('emoji_set', []))}")
    print(f"   Variables: {info['variables_count']}")
    print(f"   Templates: {info['templates_count']}")

    # Demo messages
    print(f"\n💬 Example Messages:")

    test_messages = [
        ("Error in sandbox", "error"),
        ("Plugin loaded successfully", "success"),
        ("Warning: Low memory", "warning"),
        ("System ready", "status"),
    ]

    for message, msg_type in test_messages:
        themed = overlay.apply(message, msg_type)
        print(f"\n   Original: {message}")
        print(f"   Themed:   {themed}")

    print()


def main():
    """Run theme overlay demo."""
    print("\n")
    print_separator("*")
    print("  🎨 uDOS Theme Overlay System Demo")
    print_separator("*")
    print()

    # Get all available themes
    themes = get_available_themes()
    print(f"📚 Available Themes ({len(themes)}):\n")

    for theme_id in themes:
        metadata = get_theme_metadata(theme_id)
        if metadata:
            name = metadata.get("theme_name", theme_id)
            style = metadata.get("style", "N/A")
            print(f"   • {name:40s} - {style}")

    print()

    # Demo each theme
    for theme_id in themes:
        demo_theme(theme_id)

    print_separator("*")
    print("  ✅ Demo Complete!")
    print_separator("*")
    print()


if __name__ == "__main__":
    main()
