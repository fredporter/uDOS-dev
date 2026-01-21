def print_splash_screen():
    """
    Prints the uDOS splash screen with rainbow gradient colors.
    Now uses modular SplashLoader for enhanced features.
    Falls back to simple terminal rendering if rich is unavailable.
    """
    try:
        from dev.goblin.core.services.splash_loader import get_splash_loader
        
        # Try to use modular splash loader first
        loader = get_splash_loader()
        splash_output = loader.render_static_splash()
        print(splash_output)
        return
    except Exception as loader_error:
        # Fall back to rich rendering
        pass
    
    try:
        from rich.console import Console
        from rich.panel import Panel
        from rich.text import Text
        from rich import box

        console = Console(force_terminal=True, force_interactive=False)

        # Rainbow gradient ASCII art (each line different color)
        # Using proper Unicode box-drawing characters (no line gaps)
        splash_lines = [
            "██╗   ██╗██████╗  ██████╗ ███████╗",
            "██║   ██║██╔══██╗██╔═══██╗██╔════╝",
            "██║   ██║██║  ██║██║   ██║███████╗",
            "██║   ██║██║  ██║██║   ██║╚════██║",
            "╚██████╔╝██████╔╝╚██████╔╝███████║",
            " ╚═════╝ ╚═════╝  ╚═════╝ ╚══════╝"
        ]

        # Rainbow gradient colors (vivid palette)
        colors = ["red", "yellow", "green", "cyan", "blue", "magenta"]

        # Build colored splash
        splash_text = Text()
        for i, line in enumerate(splash_lines):
            # No extra newline added - fixes line gaps
            splash_text.append(line, style=f"bold {colors[i % len(colors)]}")
            if i < len(splash_lines) - 1:  # Only add newline between lines, not after last
                splash_text.append("\n")

        # Subtitle with gradient
        subtitle = Text()
        subtitle.append("uDOS ", style="bold cyan")
        subtitle.append("v2.4.0", style="bold yellow")
        subtitle.append(" - ", style="white")
        subtitle.append("Offline-First Survival OS", style="bold green")

        # Commands help
        help_text = Text()
        help_text.append("💡 Type ", style="dim")
        help_text.append("HELP", style="bold cyan")
        help_text.append(" for commands | ", style="dim")
        help_text.append("CONFIG LIST", style="bold yellow")
        help_text.append(" for settings", style="dim")

        syntax_text = Text()
        syntax_text.append("📝 Syntax: ", style="dim")
        syntax_text.append("COMMAND [ options ]", style="bold green")
        syntax_text.append(" or ", style="dim")
        syntax_text.append("COMMAND [ param1 | param2 ]", style="bold magenta")
        
        # NES-style pointer hint
        pointer_text = Text()
        pointer_text.append("🎮 NES Mode: ", style="dim")
        pointer_text.append("LOADER PRESET nes", style="bold cyan")
        pointer_text.append(" for retro navigation", style="dim")

        # Create panel with colored border (using HEAVY box to prevent gaps)
        panel_content = Text.assemble(
            splash_text,
            "\n",
            subtitle,
            "\n",
            ("─" * 60, "dim"),
            "\n",
            help_text,
            "\n",
            syntax_text,
            "\n",
            pointer_text
        )

        panel = Panel(
            panel_content,
            border_style="bold cyan",
            box=box.HEAVY,  # Changed from DOUBLE to HEAVY for better rendering
            padding=(1, 2)
        )

        console.print(panel)
        print()  # Extra line for spacing
        return  # Success - exit early

    except ImportError:
        # Rich library not installed - use plain text fallback
        pass
    except Exception as e:
        # Rich rendering failed - use plain text fallback
        # Uncomment for debugging: print(f"DEBUG: Rich rendering failed: {e}")
        pass

    # Fallback to plain text (no line gaps)
    splash_text = r"""
██╗   ██╗██████╗  ██████╗ ███████╗
██║   ██║██╔══██╗██╔═══██╗██╔════╝
██║   ██║██║  ██║██║   ██║███████╗
██║   ██║██║  ██║██║   ██║╚════██║
╚██████╔╝██████╔╝╚██████╔╝███████║
 ╚═════╝ ╚═════╝  ╚═════╝ ╚══════╝
"""
    print(splash_text)
    print("uDOS v2.4.0 - Offline-First Survival OS")
    print("="*50)
    print("Type HELP for commands | CONFIG LIST for settings")
    print("Syntax: COMMAND [ options ] or COMMAND [ param1 | param2 ]")
    print("🎮 Try: LOADER PRESET nes for NES-style interface")
    print()


# DEPRECATED: print_viewport_measurement() removed in v1.2.25
# Use ViewportVisualizer.generate_educational_splash() instead
# Location: core/utils/viewport_viz.py
