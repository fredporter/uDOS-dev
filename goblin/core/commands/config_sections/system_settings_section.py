"""
System Settings Configuration Section

Manages system settings (theme, palette, debug mode, viewport, editor)
"""

from pathlib import Path
from .base_section import BaseConfigSection
from dev.goblin.core.uDOS_main import get_config


class SystemSettingsSection(BaseConfigSection):
    """Manages system settings."""
    
    def __init__(self, config_manager, input_manager, output_formatter, logger=None, viewport=None):
        """Initialize with optional viewport for viewport config."""
        super().__init__(config_manager, input_manager, output_formatter, logger)
        self.viewport = viewport
    
    def handle(self):
        """Interactive system settings management (v2.0: Enhanced with palettes, dev mode)."""
        self.clear_screen()
        try:
            config = get_config()

            # Get current settings
            current_theme = config.get_env('THEME', 'dungeon')
            current_palette = config.get_user('system_settings.interface.color_palette', 'polaroid')
            debug_mode = getattr(self.logger, 'debug_enabled', False) if self.logger else False
            dev_mode = config.get('DEV_MODE', False)
            cli_editor = config.get_env('CLI_EDITOR', 'micro')

            # Show current settings
            output = []
            output.append(self.output_formatter.format_panel(
                "System Settings",
                f"Theme: {current_theme}\n"
                f"Color Palette: {current_palette}\n"
                f"Debug Mode: {'Enabled' if debug_mode else 'Disabled'}\n"
                f"Dev Mode: {'Enabled' if dev_mode else 'Disabled'}\n"
                f"CLI Editor: {cli_editor}"
            ))

            # Ask what to update
            action = self.input_manager.prompt_choice(
                message="What would you like to change?",
                choices=[
                    "Change Theme",
                    "Select Color Palette",
                    "Toggle Debug Mode",
                    "Toggle Dev Mode",
                    "Set CLI Editor (micro/nano/vim)",
                    "Back to Main Menu"
                ],
                default="Back to Main Menu"
            )

            if action == "Back to Main Menu":
                return None

            if action == "Change Theme":
                themes_dir = Path('dev/goblin/core/data/themes')
                available_themes = []
                if themes_dir.exists():
                    available_themes = [f.stem for f in themes_dir.glob('*.json')]

                if not available_themes:
                    output.append("\n❌ No themes found in dev/goblin/core/data/themes/")
                else:
                    new_theme = self.input_manager.prompt_choice(
                        message="Select a theme:",
                        choices=available_themes,
                        default=current_theme if current_theme in available_themes else available_themes[0]
                    )
                    config.set_env('THEME', new_theme)
                    output.append(f"\n✅ Theme changed to: {new_theme}")
                    output.append("⚠️ Restart uDOS to apply theme changes")

            elif action == "Select Color Palette":
                palettes = ["polaroid", "concrete", "brutalist", "terminal", "cyberpunk", "sepia", "mono", "earth"]
                new_palette = self.input_manager.prompt_choice(
                    message="Select color palette:",
                    choices=palettes,
                    default=current_palette if current_palette in palettes else "polaroid"
                )
                config.set_user('system_settings.interface.color_palette', new_palette)
                output.append(f"\n✅ Color palette set to: {new_palette}")

            elif action == "Toggle Debug Mode":
                if self.logger:
                    self.logger.debug_enabled = not debug_mode
                    output.append(f"\n✅ Debug mode {'enabled' if self.logger.debug_enabled else 'disabled'}")

            elif action == "Toggle Dev Mode":
                new_dev_mode = not dev_mode
                config.set('DEV_MODE', new_dev_mode)
                output.append(f"\n✅ Dev Mode {'enabled' if new_dev_mode else 'disabled'}")

            elif action == "Set CLI Editor (micro/nano/vim)":
                from dev.goblin.core.services.editor_manager import EditorManager
                editor_mgr = EditorManager()
                available = editor_mgr.detect_available_editors()

                if available['CLI']:
                    new_editor = self.input_manager.prompt_choice(
                        message="Select CLI editor:",
                        choices=available['CLI'],
                        default='micro' if 'micro' in available['CLI'] else available['CLI'][0]
                    )
                    config.set_env('CLI_EDITOR', new_editor)
                    output.append(f"\n✅ CLI editor set to: {new_editor}")

            return "\n".join(output)

        except Exception as e:
            return self.format_error("System settings management failed", e)
