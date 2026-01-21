"""
uDOS v1.2.26 - Theme Handler

Extracted from ConfigurationHandler as part of handler refactoring.
Handles all theme-related commands:
- THEME (show current)
- THEME LIST/LIST DETAILED
- THEME <name> (switch)
- THEME PREVIEW <name>
- THEME CREATE/CREATE INTERACTIVE/CREATE FROM <template>
- THEME COPY <source> <new_name>
- THEME EXPORT/IMPORT
- THEME VALIDATE/DETAILS/STATS
- THEME TEMPLATES
- THEME BACKUP/RESTORE

Enhanced in v1.0.13 with theme builder and templates.
"""

import json
from pathlib import Path
from .base_handler import BaseCommandHandler
from dev.goblin.core.services.theme.theme_manager import ThemeManager
from dev.goblin.core.services.theme.theme_builder import ThemeBuilder


class ThemeHandler(BaseCommandHandler):
    """Handles theme management operations."""

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

    def handle_command(self, params):
        """Main command entry point."""
        if not params:
            return self.format_error("No command provided")
        
        cmd = params[0].upper()
        
        if cmd == 'THEME':
            return self.handle_theme(params[1:], None, None)
        else:
            return self.format_error(f"Unknown command: {cmd}")

    def handle_theme(self, params, grid, parser):
        """
        Manage color themes (Enhanced in v1.0.13).

        Usage:
            THEME                    - Show current theme
            THEME LIST               - List all available themes
            THEME LIST DETAILED      - List themes with full details
            THEME <name>             - Switch to theme
            THEME PREVIEW <name>     - Preview theme without applying
            THEME CREATE             - Create new theme (interactive wizard)
            THEME CREATE INTERACTIVE - Create theme with step-by-step wizard
            THEME CREATE FROM <template> - Create from template
            THEME COPY <source> <new_name> - Copy existing theme
            THEME EXPORT <name> [path] - Export theme to .udostheme file
            THEME IMPORT <path> [name] - Import theme from .udostheme file
            THEME VALIDATE <name>    - Validate theme structure
            THEME DETAILS <name>     - Show detailed theme information
            THEME STATS              - Show theme statistics
            THEME TEMPLATES          - List available templates
            THEME BACKUP             - Backup current theme
            THEME RESTORE            - Restore from backup

        Available themes are in data/themes/ directory.
        """
        if not params:
            return self._show_current_theme()

        command = params[0].upper()

        # New v1.0.13 commands
        if command == 'PREVIEW':
            if len(params) < 2:
                return "❌ Usage: THEME PREVIEW <name>"
            return self._preview_theme(params[1])

        elif command == 'CREATE':
            if len(params) == 1:
                return self._create_theme_interactive()
            elif params[1].upper() == 'INTERACTIVE':
                return self._create_theme_interactive()
            elif params[1].upper() == 'FROM':
                if len(params) < 3:
                    return "❌ Usage: THEME CREATE FROM <template>"
                return self._create_theme_from_template(params[2])
            else:
                return "❌ Unknown CREATE option. Use: INTERACTIVE or FROM <template>"

        elif command == 'COPY':
            if len(params) < 3:
                return "❌ Usage: THEME COPY <source> <new_name>"
            return self._copy_theme(params[1], params[2])

        elif command == 'EXPORT':
            if len(params) < 2:
                return "❌ Usage: THEME EXPORT <name> [path]"
            output_path = params[2] if len(params) > 2 else f"{params[1]}.udostheme"
            return self._export_theme(params[1], output_path)

        elif command == 'IMPORT':
            if len(params) < 2:
                return "❌ Usage: THEME IMPORT <path> [name]"
            theme_name = params[2] if len(params) > 2 else None
            return self._import_theme(params[1], theme_name)

        elif command == 'VALIDATE':
            if len(params) < 2:
                return "❌ Usage: THEME VALIDATE <name>"
            return self._validate_theme(params[1])

        elif command == 'DETAILS':
            if len(params) < 2:
                return "❌ Usage: THEME DETAILS <name>"
            return self._show_theme_details(params[1])

        elif command == 'STATS':
            return self._show_theme_stats()

        elif command == 'TEMPLATES':
            return self._list_templates()

        # Existing commands
        elif command == 'LIST':
            detailed = len(params) > 1 and params[1].upper() == 'DETAILED'
            return self._list_themes(detailed)
        elif command == 'BACKUP':
            return self._backup_theme()
        elif command == 'RESTORE':
            return self._restore_theme()
        else:
            # Assume it's a theme name
            return self._switch_theme(params[0])

    def _show_current_theme(self):
        """Show current theme information."""
        if not self.theme:
            return "❌ Theme system not initialized"

        try:
            theme_name = getattr(self.theme, 'name', 'Unknown')
            theme_version = getattr(self.theme, 'version', 'Unknown')

            output = []
            output.append(f"🎨 CURRENT THEME: {theme_name.upper()}")
            output.append("=" * 50)
            output.append(f"Name: {theme_name}")
            output.append(f"Version: {theme_version}")

            # Show color preview if available
            if hasattr(self.theme, 'colors'):
                output.append("")
                output.append("Color preview:")
                # Add basic color samples
                colors = ['red', 'green', 'yellow', 'blue', 'purple', 'cyan']
                preview_line = ""
                for color in colors:
                    if hasattr(self.theme, color):
                        ansi_code = getattr(self.theme, color, '')
                        if ansi_code:
                            preview_line += f"{ansi_code}██\033[0m "
                if preview_line:
                    output.append(f"  {preview_line}")

            output.append("")
            output.append("💡 Use: THEME LIST to see all available themes")
            output.append("💡 Use: THEME <name> to switch themes")

            return "\n".join(output)

        except Exception as e:
            return f"❌ Failed to show theme info: {str(e)}"

    def _list_themes(self, detailed=False):
        """List all available themes (enhanced in v1.0.13)."""
        return self.theme_manager.list_json_themes(detailed=detailed)

    def _switch_theme(self, theme_name):
        """Switch to a different theme."""
        try:
            theme_file = Path(f'dev/goblin/core/data/themes/{theme_name.lower()}.json')
            if not theme_file.exists():
                return f"❌ Theme '{theme_name}' not found\n\nUse: THEME LIST to see available themes"

            # Load theme data to validate
            with open(theme_file, 'r') as f:
                theme_data = json.load(f)

            # Apply theme
            if self.theme and hasattr(self.theme, 'load_theme'):
                self.theme.load_theme(theme_name.lower())
                return f"✅ Switched to theme: {theme_name}"
            else:
                return "❌ Theme manager not available"

        except Exception as e:
            return f"❌ Failed to switch theme: {str(e)}"

    # ==================== New v1.0.13 Theme Methods ====================

    def _preview_theme(self, theme_name):
        """Preview a theme without applying it."""
        try:
            return self.theme_manager.preview_json_theme(theme_name)
        except Exception as e:
            return f"❌ Failed to preview theme: {str(e)}"

    def _create_theme_interactive(self):
        """Create theme using interactive wizard."""
        try:
            print("\n🎨 Starting interactive theme creation wizard...")
            print("This will guide you through creating a custom theme.\n")

            theme_data = self.theme_builder.create_theme_interactive()

            if not theme_data:
                return "❌ Theme creation cancelled"

            # Validate and fix
            fixed_data, warnings = self.theme_builder.validate_and_fix(theme_data)

            if warnings:
                print("\n⚠️  Auto-fixed issues:")
                for warning in warnings:
                    print(f"  - {warning}")

            # Save theme
            theme_name = fixed_data.get("THEME_NAME", "custom_theme").lower()
            if self.theme_builder.save_theme(fixed_data, theme_name):
                return f"\n✅ Theme '{theme_name}' created successfully!\n" \
                       f"💡 Use: THEME PREVIEW {theme_name} to preview\n" \
                       f"💡 Use: THEME {theme_name} to activate"
            else:
                return "❌ Failed to save theme"

        except Exception as e:
            return f"❌ Failed to create theme: {str(e)}"

    def _create_theme_from_template(self, template_name):
        """Create theme from a template."""
        try:
            print(f"\n🎨 Creating theme from template: {template_name}\n")

            # Get basic customizations
            theme_name = input("Theme Name (e.g., MY_THEME): ").strip().upper()
            if not theme_name:
                return "❌ Theme name is required"

            display_name = input("Display Name: ").strip()
            description = input("Description: ").strip()

            customizations = {
                "THEME_NAME": theme_name,
                "NAME": display_name or theme_name.title(),
                "DESCRIPTION": description or f"Theme based on {template_name}",
            }

            # Create from template
            theme_data = self.theme_builder.create_from_template(template_name, customizations)

            # Validate and fix
            fixed_data, warnings = self.theme_builder.validate_and_fix(theme_data)

            # Save theme
            if self.theme_builder.save_theme(fixed_data, theme_name.lower()):
                return f"\n✅ Theme '{theme_name}' created from template!\n" \
                       f"💡 Use: THEME PREVIEW {theme_name.lower()} to preview\n" \
                       f"💡 Use: THEME {theme_name.lower()} to activate"
            else:
                return "❌ Failed to save theme"

        except Exception as e:
            return f"❌ Failed to create theme from template: {str(e)}"

    def _copy_theme(self, source_name, new_name):
        """Copy an existing theme."""
        try:
            print(f"\n🎨 Copying theme '{source_name}' to '{new_name}'...\n")

            # Optional modifications
            modify = input("Apply modifications? (y/n): ").strip().lower()
            modifications = None

            if modify == 'y':
                print("\nEnter modifications (press Enter to skip):")
                description = input("  New description: ").strip()
                icon = input("  New icon: ").strip()

                modifications = {}
                if description:
                    modifications["DESCRIPTION"] = description
                if icon:
                    modifications["ICON"] = icon

            # Copy theme
            new_theme = self.theme_builder.copy_theme(source_name, new_name, modifications)

            if not new_theme:
                return f"❌ Failed to copy theme '{source_name}'"

            # Save copied theme
            if self.theme_builder.save_theme(new_theme, new_name.lower()):
                return f"\n✅ Theme copied successfully as '{new_name}'!\n" \
                       f"💡 Use: THEME PREVIEW {new_name.lower()} to preview\n" \
                       f"💡 Use: THEME {new_name.lower()} to activate"
            else:
                return "❌ Failed to save copied theme"

        except Exception as e:
            return f"❌ Failed to copy theme: {str(e)}"

    def _export_theme(self, theme_name, output_path):
        """Export theme to .udostheme file."""
        try:
            if self.theme_manager.export_json_theme(theme_name, output_path):
                return f"✅ Theme '{theme_name}' exported successfully"
            else:
                return f"❌ Failed to export theme '{theme_name}'"
        except Exception as e:
            return f"❌ Export failed: {str(e)}"

    def _import_theme(self, import_path, theme_name):
        """Import theme from .udostheme file."""
        try:
            if self.theme_manager.import_json_theme(import_path, theme_name):
                imported_name = theme_name or Path(import_path).stem
                return f"✅ Theme imported successfully as '{imported_name}'\n" \
                       f"💡 Use: THEME PREVIEW {imported_name} to preview\n" \
                       f"💡 Use: THEME {imported_name} to activate"
            else:
                return "❌ Failed to import theme"
        except Exception as e:
            return f"❌ Import failed: {str(e)}"

    def _validate_theme(self, theme_name):
        """Validate theme structure."""
        try:
            theme_data = self.theme_manager.load_json_theme(theme_name)
            if not theme_data:
                return f"❌ Theme '{theme_name}' not found"

            is_valid, errors = self.theme_manager.validate_json_theme(theme_data)

            output = []
            output.append(f"\n🔍 VALIDATION RESULTS: {theme_name}")
            output.append("=" * 60)

            if is_valid:
                output.append("✅ Theme is VALID")
                output.append("\nAll required fields and sections present.")
            else:
                output.append("❌ Theme is INVALID")
                output.append(f"\nFound {len(errors)} error(s):")
                for error in errors:
                    output.append(f"  • {error}")

            output.append("")
            return "\n".join(output)

        except Exception as e:
            return f"❌ Validation failed: {str(e)}"

    def _show_theme_details(self, theme_name):
        """Show detailed theme information."""
        try:
            metadata = self.theme_manager.get_json_theme_metadata(theme_name)
            if not metadata:
                return f"❌ Theme '{theme_name}' not found"

            theme_data = self.theme_manager.load_json_theme(theme_name)

            output = []
            output.append(f"\n{metadata.icon} {metadata.name.upper()}")
            output.append("=" * 60)
            output.append(f"Version: {metadata.version}")
            output.append(f"Style: {metadata.style}")
            output.append(f"Description: {metadata.description}")

            if metadata.author:
                output.append(f"Author: {metadata.author}")
            if metadata.created:
                output.append(f"Created: {metadata.created}")

            # Show sections
            output.append("\nSections:")
            sections = ["CORE_SYSTEM", "CORE_USER", "TERMINOLOGY", "MESSAGE_STYLES",
                       "CHARACTER_TYPES", "OBJECT_TYPES", "LOCATION_TRACKING"]
            for section in sections:
                has_section = "✓" if section in theme_data else "✗"
                output.append(f"  {has_section} {section}")

            # Validation
            is_valid, errors = self.theme_manager.validate_json_theme(theme_data)
            output.append(f"\nValidation: {'✅ VALID' if is_valid else '❌ INVALID'}")

            output.append("\n💡 Use: THEME PREVIEW " + theme_name + " to see preview")
            output.append("")

            return "\n".join(output)

        except Exception as e:
            return f"❌ Failed to show details: {str(e)}"

    def _show_theme_stats(self):
        """Show theme statistics."""
        try:
            return self.theme_manager.get_json_theme_stats()
        except Exception as e:
            return f"❌ Failed to show stats: {str(e)}"

    def _list_templates(self):
        """List available theme templates."""
        try:
            return self.theme_builder.list_templates()
        except Exception as e:
            return f"❌ Failed to list templates: {str(e)}"

    # ==================== End v1.0.13 Methods ====================

    def _backup_theme(self):
        """Backup current theme configuration."""
        try:
            backup_dir = Path('memory/bank/system')
            backup_dir.mkdir(parents=True, exist_ok=True)

            current_theme = getattr(self.theme, 'name', 'default') if self.theme else 'default'
            backup_file = backup_dir / f'theme_backup_{current_theme}.json'

            # Create backup data
            backup_data = {
                'theme_name': current_theme,
                'backup_timestamp': Path().cwd().name,  # Simple timestamp
                'settings': {
                    'debug_mode': getattr(self.logger, 'debug_enabled', False) if self.logger else False
                }
            }

            success, error = self.save_json_file(backup_file, backup_data)
            if success:
                return f"✅ Theme backup saved to: {backup_file}"
            else:
                return f"❌ Failed to backup theme: {error}"

        except Exception as e:
            return f"❌ Failed to backup theme: {str(e)}"

    def _restore_theme(self):
        """Restore theme from backup."""
        try:
            backup_dir = Path('memory/bank/system')
            if not backup_dir.exists():
                return "❌ No backup directory found"

            backup_files = list(backup_dir.glob('theme_backup_*.json'))
            if not backup_files:
                return "❌ No theme backups found"

            # Use most recent backup
            latest_backup = max(backup_files, key=lambda f: f.stat().st_mtime)

            backup_data, error = self.load_json_file(latest_backup)
            if not backup_data:
                return f"❌ Failed to load backup: {error}"

            theme_name = backup_data.get('theme_name', 'default')

            # Restore theme
            if self.theme and hasattr(self.theme, 'load_theme'):
                self.theme.load_theme(theme_name)
                return f"✅ Restored theme: {theme_name} from backup"
            else:
                return "❌ Theme manager not available"

        except Exception as e:
            return f"❌ Failed to restore theme: {str(e)}"
