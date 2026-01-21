"""
uDOS v1.5.0 - Configuration Handler

Handles configuration management operations:
- Settings display and modification
- Theme switching and configuration
- Configuration file management
- User preferences
- Advanced theme management (v1.0.13+)
- Unified configuration via ConfigManager (v1.5.0+)

v2.0.0 Refactoring: Modular config sections
"""

import json
import shutil
from pathlib import Path
from .base_handler import BaseCommandHandler
from dev.goblin.core.services.theme.theme_manager import ThemeManager
from dev.goblin.core.services.theme.theme_builder import ThemeBuilder
from dev.goblin.core.uDOS_main import get_config  # v1.5.0 Unified configuration
from dev.goblin.core.utils.paths import PATHS

# Import modular config sections
from .config_sections import (
    APIKeysSection,
    UserProfileSection,
    SystemSettingsSection,
    TaskSettingsSection,
    FilenameSettingsSection,
    VersionControlSection,
    InputDeviceSection,
    UPYSettingsSection,
    GameplaySettingsSection,
)


class ConfigurationHandler(BaseCommandHandler):
    """Handles configuration and settings management operations."""

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self._theme_manager = None
        self._theme_builder = None

    @property
    def theme_manager(self):
        """Lazy-load ThemeManager service."""
        if self._theme_manager is None:
            self._theme_manager = ThemeManager()
        return self._theme_manager

    @property
    def theme_builder(self):
        """Lazy-load ThemeBuilder service."""
        if self._theme_builder is None:
            self._theme_builder = ThemeBuilder(theme_manager=self.theme_manager)
        return self._theme_builder

    # SETUP command extracted to setup_handler.py (v1.2.27 refactor)
    # Use: SETUP for interactive wizard or SETUP --show for settings display

    def _set_theme(self, theme_name):
        """Set the current theme - kept for SETUP command compatibility."""
        try:
            # Load theme data
            theme_file = Path(f"dev/goblin/core/data/themes/{theme_name.lower()}.json")
            if not theme_file.exists():
                return f"❌ Theme '{theme_name}' not found\n\nUse: THEME LIST to see available themes"

            with open(theme_file, "r") as f:
                theme_data = json.load(f)

            # Apply theme through theme manager
            if self.theme and hasattr(self.theme, "load_theme"):
                self.theme.load_theme(theme_name.lower())
                return f"✅ Theme changed to '{theme_name}'"
            else:
                return "❌ Theme manager not available"

        except Exception as e:
            return f"❌ Failed to set theme: {str(e)}"

    # THEME command extracted to theme_handler.py (v1.2.26 refactor)
    # Use: THEME <subcommand> instead of CONFIG THEME

    def handle_config(self, params, grid, parser):
        """
        Manage configuration files and system settings (Smart Mode v1.0.29).

        Smart Mode (no arguments):
            CONFIG               - Interactive menu for all config operations

        Explicit Mode (backward compatible):
            CONFIG BACKUP        - Backup all configs
            CONFIG RESTORE       - Restore from backup
            CONFIG RESET         - Reset to defaults
            CONFIG VALIDATE      - Validate all configs
            CONFIG VIEWPORT      - Show viewport information
            CONFIG VIEWPORT <w> <h> - Set custom viewport (in cells)
            CONFIG GET <key>     - Get configuration value
            CONFIG SET <key> <value> - Set configuration value

        Manages configuration files in core/data/ directory.
        """
        # SMART MODE: No params → Interactive menu (only in terminal)
        if not params:
            # Check if running in interactive mode (has input_manager)
            if not hasattr(self, "input_manager") or self.input_manager is None:
                # Non-interactive (API mode) - show help instead
                return (
                    "❌ Unknown config command\n\n"
                    "Available commands:\n"
                    "  CONFIG           - Interactive menu (smart mode)\n"
                    "  CONFIG BACKUP    - Backup configurations\n"
                    "  CONFIG RESTORE   - Restore from backup\n"
                    "  CONFIG RESET     - Reset to defaults\n"
                    "  CONFIG VALIDATE  - Validate configurations\n"
                    "  CONFIG VIEWPORT  - Manage viewport settings\n"
                    "  CONFIG GET <key> - Get configuration value\n"
                    "  CONFIG SET <key> <value> - Set configuration value"
                )
            return self._config_interactive_menu()

        # EXPLICIT MODE: Backward compatible command routing
        command = params[0].upper()

        if command == "BACKUP":
            return self._backup_configs()
        elif command == "RESTORE":
            return self._restore_configs()
        elif command == "RESET":
            return self._reset_configs()
        elif command == "VALIDATE":
            return self._validate_configs()
        elif command == "CHECK":
            return self._check_folder_structure()
        elif command == "FIX":
            return self._fix_folder_structure()
        elif command == "VIEWPORT":
            if len(params) == 1:
                return self._show_viewport_config()
            elif len(params) == 3:
                try:
                    width = int(params[1])
                    height = int(params[2])
                    return self._set_viewport_config(width, height)
                except ValueError:
                    return "❌ Invalid viewport dimensions. Use: CONFIG VIEWPORT <width> <height>"
            else:
                return (
                    "❌ Invalid viewport command\n\n"
                    "Usage:\n"
                    "  CONFIG VIEWPORT        - Show current viewport\n"
                    "  CONFIG VIEWPORT <w> <h> - Set custom viewport in cells"
                )
        elif command == "GET":
            if len(params) < 2:
                return "❌ Usage: CONFIG GET <key>"
            return self._get_config_value(params[1])
        elif command == "SET":
            if len(params) < 3:
                return "❌ Usage: CONFIG SET <key> <value>"
            return self._set_config_value(params[1], " ".join(params[2:]))
        else:
            return (
                "❌ Unknown config command\n\n"
                "Available commands:\n"
                "  CONFIG           - Interactive menu (smart mode)\n"
                "  CONFIG BACKUP    - Backup configurations\n"
                "  CONFIG RESTORE   - Restore from backup\n"
                "  CONFIG RESET     - Reset to defaults\n"
                "  CONFIG VALIDATE  - Validate configurations\n"
                "  CONFIG VIEWPORT  - Manage viewport settings\n"
                "  CONFIG GET <key> - Get configuration value\n"
                "  CONFIG SET <key> <value> - Set configuration value"
            )

    def _clear_screen(self):
        """Clear terminal for cleaner menu navigation."""
        import os

        os.system("clear" if os.name != "nt" else "cls")

    def _show_config_status(self):
        """Show current configuration status with v1.5.0 features."""
        self._clear_screen()
        config_dir = Path("core/data")
        if not config_dir.exists():
            return self.get_message("ERROR_CONFIG_DIR_NOT_FOUND", path=config_dir)

        config_files = [
            "commands.json",
            "extensions.json",
            "font-system.json",  # v2.0.0: Includes color palette
            "fonts.json",
            "locations.json",  # v2.0.0: TILE code system
        ]

        # Get current settings
        user_role = (
            self.config_manager.get("USER_ROLE", "user")
            if hasattr(self, "config_manager")
            else "user"
        )
        theme = (
            self.config_manager.get("THEME", "dungeon")
            if hasattr(self, "config_manager")
            else "dungeon"
        )
        auto_save = (
            self.config_manager.get("AUTO_SAVE", "true")
            if hasattr(self, "config_manager")
            else "true"
        )

        output = []
        output.append("⚙️  uDOS CONFIGURATION STATUS")
        output.append("═" * 60)
        output.append("")
        output.append("📊 SYSTEM SETTINGS")
        output.append("─" * 60)
        output.append(f"  User Role:        {user_role}")
        output.append(f"  Theme:            {theme}")
        output.append(f"  Auto-save:        {auto_save}")
        output.append("")
        output.append("📁 CONFIGURATION FILES")
        output.append("─" * 60)

        total_size = 0
        valid_count = 0

        for config_file in config_files:
            file_path = config_dir / config_file
            if file_path.exists():
                size = file_path.stat().st_size
                total_size += size

                # Validate JSON
                try:
                    with open(file_path, "r") as f:
                        json.load(f)
                    status = "✅ Valid"
                    valid_count += 1
                except:
                    status = "❌ Invalid JSON"

                size_str = f"{size:,} bytes" if size < 1024 else f"{size//1024} KB"
                output.append(
                    f"  {config_file.ljust(20)} {size_str.rjust(10)} {status}"
                )
            else:
                output.append(
                    f"  {config_file.ljust(20)} {'Missing'.rjust(10)} ❌ Not found"
                )

        output.append("")
        output.append(
            f"Total: {len(config_files)} files, {valid_count} valid, {total_size:,} bytes"
        )
        output.append("")
        output.append("💡 Use: CONFIG VALIDATE for detailed validation")
        output.append("💡 Use: CONFIG BACKUP to save current state")

        return "\n".join(output)

    def _backup_configs(self):
        """Backup all configuration files."""
        try:
            config_dir = Path("core/data")
            backup_dir = Path("memory/system/backup")
            backup_dir.mkdir(parents=True, exist_ok=True)

            backed_up = []
            for config_file in config_dir.glob("*.json"):
                backup_file = backup_dir / config_file.name
                shutil.copy2(config_file, backup_file)
                backed_up.append(config_file.name)

            if backed_up:
                return (
                    f"✅ Backed up {len(backed_up)} configuration files\n\n"
                    f"Backup location: {backup_dir}\n"
                    f"Files: {', '.join(backed_up)}"
                )
            else:
                return "❌ No configuration files found to backup"

        except Exception as e:
            return f"❌ Failed to backup configs: {str(e)}"

    def _restore_configs(self):
        """Restore configuration files from backup."""
        try:
            backup_dir = Path("memory/system/backup")
            if not backup_dir.exists():
                return "❌ No backup directory found\n\nUse: CONFIG BACKUP first"

            config_dir = Path("core/data")
            restored = []

            for backup_file in backup_dir.glob("*.json"):
                target_file = config_dir / backup_file.name
                shutil.copy2(backup_file, target_file)
                restored.append(backup_file.name)

            if restored:
                return (
                    f"✅ Restored {len(restored)} configuration files\n\n"
                    f"Files: {', '.join(restored)}\n\n"
                    "💡 Use: REBOOT to apply changes"
                )
            else:
                return "❌ No backup files found to restore"

        except Exception as e:
            return f"❌ Failed to restore configs: {str(e)}"

        """Validate all configuration files."""
        config_dir = Path("core/data")
        if not config_dir.exists():
            return "❌ Configuration directory not found"

        output = []
        output.append("🔍 CONFIGURATION VALIDATION")
        output.append("=" * 50)

        valid_count = 0
        total_count = 0

        for config_file in config_dir.glob("*.json"):
            total_count += 1
            try:
                with open(config_file, "r") as f:
                    data = json.load(f)

                # Basic validation
                if isinstance(data, dict) and data:
                    output.append(
                        f"  ✅ {config_file.name}: Valid JSON with {len(data)} keys"
                    )
                    valid_count += 1
                else:
                    output.append(
                        f"  ⚠️  {config_file.name}: Valid JSON but empty or invalid structure"
                    )

            except json.JSONDecodeError as e:
                output.append(f"  ❌ {config_file.name}: JSON Error - {str(e)}")
            except Exception as e:
                output.append(f"  ❌ {config_file.name}: Error - {str(e)}")

        output.append("")
        if valid_count == total_count:
            output.append(f"✅ All {total_count} configuration files are valid")
        else:
            output.append(
                f"⚠️  {valid_count}/{total_count} configuration files are valid"
            )
            output.append("💡 Use: CONFIG RESTORE to restore from backup")

        return "\n".join(output)

    def _show_viewport_config(self):
        """Show current viewport configuration."""
        try:
            from dev.goblin.core.services.viewport_manager import ViewportManager

            viewport = ViewportManager()
            summary = viewport.get_viewport_summary()
            chart = viewport.get_size_comparison_chart()

            output = [
                "📐 Viewport Configuration",
                "=" * 50,
                summary,
                "",
                chart,
                "",
                "💡 Use: CONFIG VIEWPORT <width> <height> to set custom dimensions",
                "💡 Use: REBOOT to refresh auto-detection",
            ]

            return "\n".join(output)

        except ImportError:
            return "❌ Viewport manager not available"
        except Exception as e:
            return f"❌ Error reading viewport config: {str(e)}"

    def _set_viewport_config(self, width_cells: int, height_cells: int):
        """Set custom viewport configuration."""
        try:
            from dev.goblin.core.services.viewport_manager import ViewportManager

            # Validate dimensions
            if width_cells < 10 or height_cells < 5:
                return "❌ Viewport too small. Minimum: 10×5 cells"

            if width_cells > 1000 or height_cells > 1000:
                return "❌ Viewport too large. Maximum: 1000×1000 cells"

            viewport = ViewportManager()
            viewport_info = viewport.set_custom_viewport(width_cells, height_cells)

            tier = viewport_info["screen_tier"]

            output = [
                "✅ Viewport configuration updated",
                "",
                f"📐 Custom Viewport: {width_cells}×{height_cells} cells",
                f"📏 Pixel Dimensions: {tier['width_pixels']}×{tier['height_pixels']}px",
                f"📺 Nearest Tier: {tier['label']} (Tier {tier['tier']})",
                f"📊 Aspect Ratio: {tier['aspect']}",
                "",
                "💾 Settings saved to core/data/viewport.json",
                "💡 Use: REBOOT to apply changes fully",
                "💡 Use: CONFIG VIEWPORT to view current settings",
            ]

            return "\n".join(output)

        except ImportError:
            return "❌ Viewport manager not available"
        except Exception as e:
            return f"❌ Error setting viewport config: {str(e)}"

    # ======================================================================
    # SMART MODE (v1.0.29) - Interactive Configuration
    # ======================================================================

    def _config_interactive_menu(self):
        """
        Smart mode: Interactive configuration menu with navigation loop.
        Shows all config options and prompts user for action.
        """
        while True:
            try:
                self._clear_screen()

                # Present menu choices
                choices = [
                    "View Configuration Status",
                    "API Keys & Credentials",
                    "User Profile Settings",
                    "System Settings (Theme, Viewport, Debug)",
                    "Task & Project Management",
                    "File Organization & Naming",
                    "Backup & Version History",
                    "Keyboard & Mouse Settings",
                    "Scripting & Performance",
                    "Gameplay Features",
                    "Quick Setup (View/Edit All Settings)",
                    "Backup/Restore Configuration",
                    "Validate All Configurations",
                    "Exit CONFIG",
                ]

                choice = self.input_manager.prompt_choice(
                    message="What would you like to configure?",
                    choices=choices,
                    default="View Configuration Status",
                )

                # Handle exit
                if choice == "Exit CONFIG":
                    return "✓ Configuration complete."

                # Execute submenu and handle result
                result = None
                if choice == "View Configuration Status":
                    result = self._show_config_status()

                elif choice == "API Keys & Credentials":
                    section = APIKeysSection(
                        get_config(),
                        self.input_manager,
                        self.output_formatter,
                        self.logger,
                    )
                    result = section.handle()

                elif choice == "User Profile Settings":
                    section = UserProfileSection(
                        get_config(),
                        self.input_manager,
                        self.output_formatter,
                        self.logger,
                    )
                    result = section.handle()

                elif choice == "System Settings (Theme, Viewport, Debug)":
                    section = SystemSettingsSection(
                        get_config(),
                        self.input_manager,
                        self.output_formatter,
                        self.logger,
                        self.viewport,
                    )
                    result = section.handle()

                elif choice == "Task & Project Management":
                    section = TaskSettingsSection(
                        get_config(),
                        self.input_manager,
                        self.output_formatter,
                        self.logger,
                        self,
                    )
                    result = section.handle()

                elif choice == "File Organization & Naming":
                    section = FilenameSettingsSection(
                        get_config(),
                        self.input_manager,
                        self.output_formatter,
                        self.logger,
                        self,
                    )
                    result = section.handle()

                elif choice == "Backup & Version History":
                    section = VersionControlSection(
                        get_config(),
                        self.input_manager,
                        self.output_formatter,
                        self.logger,
                        self,
                    )
                    result = section.handle()

                elif choice == "Keyboard & Mouse Settings":
                    section = InputDeviceSection(
                        get_config(),
                        self.input_manager,
                        self.output_formatter,
                        self.logger,
                        self,
                    )
                    result = section.handle()

                elif choice == "Scripting & Performance":
                    section = UPYSettingsSection(
                        get_config(),
                        self.input_manager,
                        self.output_formatter,
                        self.logger,
                        self,
                    )
                    result = section.handle()

                elif choice == "Gameplay Features":
                    section = GameplaySettingsSection(
                        get_config(),
                        self.input_manager,
                        self.output_formatter,
                        self.logger,
                        self,
                    )
                    result = section.handle()

                elif choice == "Quick Setup (View/Edit All Settings)":
                    result = self._show_all_settings()

                elif choice == "Backup/Restore Configuration":
                    result = self._manage_backup_restore_interactive()

                elif choice == "Validate All Configurations":
                    result = self._validate_configs()

                # Show result and wait for user to continue
                if result:
                    print(result)
                    print("\n" + "═" * 60)
                    print("\n  ╔════════════════════════════════════╗")
                    print("  ║  [◄ BACK]  ENTER: Menu  |  X: Exit ║")
                    print("  ╚════════════════════════════════════╝")

                    # Get single keypress
                    import sys
                    import termios
                    import tty

                    try:
                        fd = sys.stdin.fileno()
                        old_settings = termios.tcgetattr(fd)
                        try:
                            tty.setraw(fd)
                            ch = sys.stdin.read(1)
                            if ch == "\x1b":  # ESC sequence
                                sys.stdin.read(2)  # Consume escape sequence
                                ch = "enter"
                            elif ch == "\r" or ch == "\n":
                                ch = "enter"
                        finally:
                            termios.tcsetattr(fd, termios.TCSADRAIN, old_settings)
                            print()  # New line after keypress
                    except Exception:
                        ch = input().strip().lower() or "enter"

                    if ch.lower() == "x":
                        return "✓ Configuration complete."
                    continue  # Return to menu

            except KeyboardInterrupt:
                return "\n✓ Configuration cancelled."
            except Exception as e:
                print(
                    self.output_formatter.format_error(
                        "Configuration menu failed", error_details=str(e)
                    )
                )
                input("\n⏎ Press ENTER to continue...")
                continue

    # _manage_api_keys_interactive extracted to config_sections/ (v1.2.29 Phase 2)

    # _manage_user_profile_interactive extracted to config_sections/ (v1.2.29 Phase 2)

    # _manage_system_settings_interactive extracted to config_sections/ (v1.2.29 Phase 2)

    # _manage_backup_restore_interactive extracted to config_sections/ (v1.2.29 Phase 2)

    def _get_config_value(self, key: str):
        """Get a configuration value by key (v1.5.0: Uses ConfigManager)."""
        try:
            config = get_config()

            # Try ConfigManager first for known keys
            # Check ENV keys first, then user config
            if key.upper() in config.ENV_KEYS:
                value = config.get_env(key.upper())
            else:
                value = config.get_user(key)

            if value is not None:
                return self.output_formatter.format_panel(
                    f"Configuration: {key}", str(value)
                )

            # Fallback to story_manager for legacy/unknown keys
            if "." in key:
                value = self.story_manager.get_field(key, default="Not found")
            else:
                value = self.story_manager.get_field(
                    f"CONFIG.{key}", default="Not found"
                )

            return self.output_formatter.format_panel(
                f"Configuration: {key}", str(value)
            )

        except Exception as e:
            return self.output_formatter.format_error(
                f"Failed to get config: {key}", error_details=str(e)
            )

    def _set_config_value(self, key: str, value: str):
        """Set a configuration value by key (v1.5.0: Uses ConfigManager)."""
        try:
            config = get_config()

            # Try ConfigManager first for known keys
            try:
                # Route to appropriate method based on key type
                if key.upper() in config.ENV_KEYS:
                    config.set_env(key.upper(), value)
                else:
                    config.set_user(key, value)
                return self.output_formatter.format_panel(
                    f"Configuration Updated: {key}",
                    f"New value: {value}\n📝 Changes saved to .env and user.json",
                )
            except KeyError:
                # Fallback to story_manager for legacy/unknown keys
                if "." in key:
                    self.story_manager.set_field(key, value, auto_save=True)
                else:
                    self.story_manager.set_field(f"CONFIG.{key}", value, auto_save=True)

            return self.output_formatter.format_success(
                f"Configuration updated: {key} = {value}"
            )

        except Exception as e:
            return self.output_formatter.format_error(
                f"Failed to set config: {key}", error_details=str(e)
            )

    def _check_folder_structure(self):
        """Check v1.2.12 folder structure and report issues."""
        from pathlib import Path

        output = []
        output.append("═" * 70)
        output.append("📁 CONFIG CHECK - Folder Structure Validation (v1.2.12)")
        output.append("═" * 70)
        output.append("")

        root = Path.cwd()

        # Define required v1.2.x structure
        required_folders = [
            ("memory/ucode/scripts", "User .upy scripts"),
            ("memory/ucode/tests", "Test suites"),
            ("memory/ucode/sandbox", "Experimental scripts"),
            ("memory/ucode/stdlib", "Standard library"),
            ("memory/ucode/examples", "Example scripts"),
            (str(PATHS.MEMORY_UCODE_ADVENTURES), "Adventure scripts"),
            (str(PATHS.MEMORY_WORKFLOWS_MISSIONS), "Mission scripts"),
            (str(PATHS.MEMORY_WORKFLOWS_CHECKPOINTS), "State snapshots"),
            (str(PATHS.MEMORY_WORKFLOWS_STATE), "Current execution state"),
            ("memory/workflows/extensions", "Gameplay integration"),
            ("memory/system/user", "User settings"),
            ("memory/system/themes", "Custom themes"),
            ("memory/bank", "Banking/transactions"),
            ("memory/shared", "Shared/community content"),
            ("memory/docs", "User documentation"),
            ("memory/drafts", "Draft content"),
        ]

        missing = []
        present = []

        for folder, description in required_folders:
            folder_path = root / folder
            if folder_path.exists():
                present.append((folder, description))
            else:
                missing.append((folder, description))

        # Report results
        output.append(f"✅ Present: {len(present)}/{len(required_folders)}")
        if missing:
            output.append(f"❌ Missing: {len(missing)}/{len(required_folders)}")
            output.append("")
            output.append("Missing folders:")
            for folder, description in missing:
                output.append(f"  ❌ {folder}/")
                output.append(f"     {description}")
            output.append("")
            output.append("💡 Run 'CONFIG FIX' to create missing folders")
        else:
            output.append("")
            output.append("✅ All required folders present!")

        output.append("")
        return "\n".join(output)

    def _fix_folder_structure(self):
        """Create missing v1.2.12 folders with .gitkeep files."""
        from pathlib import Path

        output = []
        output.append("═" * 70)
        output.append("🔧 CONFIG FIX - Creating Missing Folders (v1.2.12)")
        output.append("═" * 70)
        output.append("")

        root = Path.cwd()

        # Define required v1.2.x structure
        required_folders = [
            "memory/ucode/scripts",
            "memory/ucode/tests",
            "memory/ucode/sandbox",
            "memory/ucode/stdlib",
            "memory/ucode/examples",
            str(PATHS.MEMORY_UCODE_ADVENTURES),
            str(PATHS.MEMORY_WORKFLOWS_MISSIONS),
            str(PATHS.MEMORY_WORKFLOWS_CHECKPOINTS),
            str(PATHS.MEMORY_WORKFLOWS_STATE),
            "memory/workflows/extensions",
            "memory/system/user",
            "memory/system/themes",
            "memory/bank",
            "memory/shared",
            "memory/docs",
            "memory/drafts",
        ]

        created = []
        existed = []

        for folder in required_folders:
            folder_path = root / folder
            if folder_path.exists():
                existed.append(folder)
            else:
                try:
                    folder_path.mkdir(parents=True, exist_ok=True)

                    # Add .gitkeep to keep folders in git
                    gitkeep = folder_path / ".gitkeep"
                    gitkeep.touch()

                    created.append(folder)
                    output.append(f"✅ Created: {folder}/")
                except Exception as e:
                    output.append(f"❌ Failed to create {folder}/: {e}")

        output.append("")
        output.append(f"✅ Created: {len(created)} new folders")
        output.append(f"✓  Existed: {len(existed)} folders")
        output.append("")

        if created:
            output.append("Created folders:")
            for folder in created:
                output.append(f"  ✅ {folder}/")

        output.append("")
        output.append("✅ Folder structure fixed!")
        output.append("")
        return "\n".join(output)

    # ======================================================================
    # v1.2.23+ Configuration Handlers
    # ======================================================================

    # _manage_task_settings_interactive extracted to config_sections/ (v1.2.29 Phase 2)

    # _manage_filename_settings_interactive extracted to config_sections/ (v1.2.29 Phase 2)

    # _manage_version_control_interactive extracted to config_sections/ (v1.2.29 Phase 2)

    # _manage_input_device_settings_interactive extracted to config_sections/ (v1.2.29 Phase 2)

    # _manage_upy_settings_interactive extracted to config_sections/ (v1.2.29 Phase 2)

    # _manage_gameplay_settings_interactive extracted to config_sections/ (v1.2.29 Phase 2)
