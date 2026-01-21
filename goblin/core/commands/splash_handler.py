"""
SPLASH Command Handler
Configure and display system splash screens

Commands:
- SPLASH: Display startup splash
- SPLASH SHOW: Show splash with current config
- SPLASH CONFIG: Edit splash configuration
- SPLASH REBOOT: Show reboot splash
- SPLASH TEST: Test current splash configuration
- SPLASH RESET: Reset to default configuration
"""

from .base_handler import BaseCommandHandler
from pathlib import Path
import json


class SplashCommandHandler(BaseCommandHandler):
    """Handle SPLASH command for splash screen configuration."""

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.splash_config_path = Path("memory/system/splash.upy")
        self.user_config_path = Path("memory/system/user/USER.json")

    def handle(self, command, params, grid, parser=None):
        """Route SPLASH subcommands."""
        if not params:
            return self._show_splash()

        subcommand = params[0].upper()

        if subcommand == "SHOW":
            return self._show_splash()
        elif subcommand == "CONFIG":
            return self._edit_config()
        elif subcommand == "REBOOT":
            return self._show_reboot_splash()
        elif subcommand == "TEST":
            return self._test_splash()
        elif subcommand == "RESET":
            return self._reset_config()
        elif subcommand == "STATUS":
            return self._show_status()
        else:
            return self._show_help()

    def _load_splash_config(self):
        """Load splash configuration from uPY file."""
        try:
            if self.splash_config_path.exists():
                # Execute uPY file to get configuration
                from dev.goblin.core.runtime.upy_executor import UPyExecutor

                executor = UPyExecutor()
                result = executor.execute_file(str(self.splash_config_path))

                if isinstance(result, dict) and "config" in result:
                    return result["config"]
                elif isinstance(result, dict):
                    return result

        except Exception as e:
            print(f"Warning: Could not load splash config: {e}")

        # Return defaults if loading fails
        return self._get_default_config()

    def _get_default_config(self):
        """Get default splash configuration."""
        return {
            "enabled": True,
            "duration": 3,
            "style": "block",
            "logo_char": "U",
            "logo_size": "90x30",
            "logo_zoom": "2:2",
            "color_scheme": "rainbow",
            "background_bars": True,
            "title": "uDOS SURVIVAL OS",
            "version": "v2.5.0",
            "message": "SYSTEM STARTING...",
            "animation_enabled": True,
            "animation_speed": 100,
            "progress_bar": True,
            "tui_fallback": True,
            "tui_style": "simple",
        }

    def _show_splash(self):
        """Display startup splash."""
        config = self._load_splash_config()

        # Try Tauri IPC first
        tauri_result = self._show_tauri_splash(config)
        if tauri_result:
            return tauri_result

        # Fallback to TUI
        if config.get("tui_fallback", True):
            return self._show_tui_splash(config)

        return "❌ Splash display not available"

    def _show_tauri_splash(self, config):
        """Display splash in Tauri/web interface."""
        try:
            # Return command for Tauri extension
            return {
                "output": "",
                "tauri_command": {"type": "splash_show", "config": config},
            }
        except Exception:
            return None

    def _show_tui_splash(self, config):
        """Display splash in terminal (TUI fallback)."""
        output = []

        # Border
        output.append("═" * 70)
        output.append("")

        # Logo/Title
        if "tui_blocks" in config:
            for line in config["tui_blocks"]:
                output.append(line.center(70))
            output.append("")

        # Version and message
        output.append(config.get("version", "v2.5.0").center(70))
        output.append("")
        output.append(config.get("message", "SYSTEM STARTING...").center(70))
        output.append("")

        # Progress simulation
        if config.get("progress_bar", True):
            progress = "▓" * 20
            output.append(f"[{progress}] 100%".center(70))

        output.append("")
        output.append("═" * 70)

        return "\n".join(output)

    def _show_reboot_splash(self):
        """Display reboot splash."""
        config = self._load_splash_config()

        if not config.get("reboot_enabled", True):
            return "ℹ️ Reboot splash disabled in configuration"

        # Try Tauri IPC
        try:
            return {
                "output": "",
                "tauri_command": {"type": "splash_reboot", "config": config},
            }
        except Exception:
            pass

        # TUI fallback
        return self._show_tui_reboot_splash(config)

    def _show_tui_reboot_splash(self, config):
        """Show reboot splash in terminal."""
        output = []
        output.append("═" * 70)
        output.append("")
        output.append(config.get("reboot_message", "SYSTEM REBOOTING").center(70))
        output.append("")

        if config.get("reboot_countdown", True):
            for i in range(3, 0, -1):
                output.append(f"{i}...".center(70))

        output.append("")
        output.append("═" * 70)

        return "\n".join(output)

    def _edit_config(self):
        """Edit splash configuration."""
        if not self.splash_config_path.exists():
            return (
                f"❌ Splash configuration not found\n\n"
                f"Expected: {self.splash_config_path}\n\n"
                f"💡 Run 'SPLASH RESET' to create default configuration"
            )

        return {
            "output": f"📝 Opening splash configuration...\n{self.splash_config_path}",
            "tauri_command": {
                "type": "open_file",
                "path": str(self.splash_config_path),
                "mode": "edit",
            },
        }

    def _test_splash(self):
        """Test current splash configuration."""
        output = []
        output.append("═" * 70)
        output.append("🧪 SPLASH TEST - Configuration Validation")
        output.append("═" * 70)
        output.append("")

        config = self._load_splash_config()

        output.append("📋 Current Configuration:")
        output.append(f"  • Enabled: {config.get('enabled', False)}")
        output.append(f"  • Duration: {config.get('duration', 3)}s")
        output.append(f"  • Style: {config.get('style', 'block')}")
        output.append(f"  • Logo: {config.get('logo_char', 'U')}")
        output.append(f"  • Animation: {config.get('animation_enabled', True)}")
        output.append(f"  • TUI Fallback: {config.get('tui_fallback', True)}")
        output.append("")

        # Test display
        output.append("🎨 Preview:")
        output.append("")
        output.append(self._show_tui_splash(config))

        return "\n".join(output)

    def _reset_config(self):
        """Reset splash configuration to defaults."""
        try:
            # Create default configuration file
            default_content = open(__file__).read().split('"""')[2]  # Get template

            self.splash_config_path.parent.mkdir(parents=True, exist_ok=True)

            # Write minimal default if template not available
            if not default_content or len(default_content) < 100:
                from pathlib import Path

                template_path = (
                    Path(__file__).parent.parent.parent / "memory/system/splash.upy"
                )
                if template_path.exists():
                    with open(template_path, "r") as f:
                        default_content = f.read()

            with open(self.splash_config_path, "w") as f:
                if default_content:
                    f.write(default_content)
                else:
                    # Write basic config
                    f.write("# splash.upy - System Splash Configuration\n")
                    f.write("from udos_core import *\n\n")
                    f.write("splash_enabled = True\n")
                    f.write("splash_duration = 3\n")
                    f.write("logo_char = 'U'\n")

            return (
                f"✅ Splash configuration reset to defaults\n"
                f"   Config: {self.splash_config_path}\n\n"
                f"💡 Run 'SPLASH CONFIG' to customize"
            )

        except Exception as e:
            return f"❌ Error resetting configuration: {e}"

    def _show_status(self):
        """Show splash configuration status."""
        output = []
        output.append("═" * 70)
        output.append("📊 SPLASH STATUS")
        output.append("═" * 70)
        output.append("")

        config = self._load_splash_config()

        output.append(f"📁 Configuration File: {self.splash_config_path}")
        output.append(
            f"   Exists: {'✅' if self.splash_config_path.exists() else '❌'}"
        )
        output.append("")

        output.append("⚙️ Settings:")
        output.append(
            f"  • Status: {'✅ Enabled' if config.get('enabled') else '❌ Disabled'}"
        )
        output.append(f"  • Style: {config.get('style', 'block')}")
        output.append(f"  • Duration: {config.get('duration', 3)}s")
        output.append(
            f"  • TUI Fallback: {'✅' if config.get('tui_fallback') else '❌'}"
        )
        output.append("")

        output.append("💡 Commands:")
        output.append("   SPLASH SHOW    - Display splash")
        output.append("   SPLASH CONFIG  - Edit configuration")
        output.append("   SPLASH TEST    - Preview current settings")
        output.append("   SPLASH RESET   - Reset to defaults")

        return "\n".join(output)

    def _show_help(self):
        """Show SPLASH command help."""
        return """
═══════════════════════════════════════════════════════════════
📺 SPLASH - Configurable System Splash Screens
═══════════════════════════════════════════════════════════════

COMMANDS:
  SPLASH              Display startup splash
  SPLASH SHOW         Show splash with current config
  SPLASH CONFIG       Edit splash configuration (uPY)
  SPLASH REBOOT       Show reboot splash
  SPLASH TEST         Preview current configuration
  SPLASH RESET        Reset to default configuration
  SPLASH STATUS       Show configuration status

CONFIGURATION:
  Location: memory/system/splash.upy
  Format: uPY (Python-based configuration)
  
  Key Settings:
    • splash_enabled - Enable/disable splash
    • splash_duration - Display time (seconds)
    • splash_style - Visual style (block/rainbow/minimal)
    • logo_char - Character for block display
    • color_scheme - Color palette
    • tui_fallback - Enable terminal fallback

CUSTOMIZATION:
  Edit memory/system/splash.upy to customize:
  - Logo character and size
  - Colors and animation
  - Text content
  - TUI fallback behavior

EXAMPLES:
  SPLASH                  # Show startup splash
  SPLASH TEST             # Preview configuration
  SPLASH CONFIG           # Edit splash.upy
  SPLASH REBOOT           # Reboot animation

INTEGRATION:
  - Tauri: Uses C64-style splash viewport
  - Terminal: Fallback ASCII block display
  - uPY: Full Python configuration support
"""


def register_command():
    """Register SPLASH command (for backward compatibility)."""
    return SplashCommandHandler


# Module-level handler instance
handler = SplashCommandHandler()
