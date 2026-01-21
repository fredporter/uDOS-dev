"""
Version Control Configuration Section

Manages version control and archive settings (max versions, retention, auto-archive)
"""

from pathlib import Path
from .base_section import BaseConfigSection
from dev.goblin.core.uDOS_main import get_config


class VersionControlSection(BaseConfigSection):
    """Manages version control and archive settings."""
    
    def __init__(self, config_manager, input_manager, output_formatter, logger=None, parent_handler=None):
        super().__init__(config_manager, input_manager, output_formatter, logger)
        self.parent_handler = parent_handler
    
    def handle(self):
        """Manage Version Control and Archive settings (v1.2.23)."""
        self.clear_screen()
        try:
            config = get_config()
            
            output = []
            output.append(self.output_formatter.format_panel(
                "🔄 Backup & Version History",
                "Keep backups of your files and undo changes when needed."
            ))
            
            # Current settings
            max_versions = config.get('max_versions_per_file', 10)
            retention_days = config.get('version_retention_days', 90)
            auto_archive = config.get('auto_archive', True)
            archive_completed = config.get('archive_completed_tasks', True)
            
            output.append(f"\nCurrent Settings:")
            output.append(f"  Max versions per file: {max_versions}")
            output.append(f"  Retention period: {retention_days} days")
            output.append(f"  Auto-archive: {'✅ Enabled' if auto_archive else '❌ Disabled'}")
            output.append(f"  Archive completed tasks: {'✅ Enabled' if archive_completed else '❌ Disabled'}")
            
            output.append(f"\n📁 Archive Locations:")
            output.append(f"  • File versions: .archive/versions/")
            output.append(f"  • Completed work: .archive/completed/")
            output.append(f"  • Backups: .archive/backups/")
            
            action = self.input_manager.prompt_choice(
                message="Choose an action:",
                choices=[
                    "Set Max Versions",
                    "Set Retention Period",
                    "Toggle Auto-archive",
                    "Toggle Archive Completed Tasks",
                    "View Archive Usage",
                    "Back to Main Menu"
                ],
                default="Back to Main Menu"
            )
            
            # Handle back to main menu
            if action == "Back to Main Menu":
                return None

            if action == "Set Max Versions":
                new_max = self.input_manager.prompt_user(
                    message="Enter max versions per file (1-100):",
                    default=str(max_versions),
                    required=True
                )
                try:
                    new_max_int = int(new_max)
                    if 1 <= new_max_int <= 100:
                        config.set('max_versions_per_file', new_max_int)
                        output.append(f"\n✅ Max versions set to: {new_max_int}")
                    else:
                        output.append(f"\n❌ Invalid value. Must be between 1 and 100.")
                except ValueError:
                    output.append(f"\n❌ Invalid number: {new_max}")
                    
            elif action == "Set Retention Period":
                new_days = self.input_manager.prompt_user(
                    message="Enter retention period in days (7-365):",
                    default=str(retention_days),
                    required=True
                )
                try:
                    new_days_int = int(new_days)
                    if 7 <= new_days_int <= 365:
                        config.set('version_retention_days', new_days_int)
                        output.append(f"\n✅ Retention period set to: {new_days_int} days")
                    else:
                        output.append(f"\n❌ Invalid value. Must be between 7 and 365.")
                except ValueError:
                    output.append(f"\n❌ Invalid number: {new_days}")
                    
            elif action == "Toggle Auto-archive":
                new_value = not auto_archive
                config.set('auto_archive', new_value)
                output.append(f"\n✅ Auto-archive: {'Enabled' if new_value else 'Disabled'}")
                
            elif action == "Toggle Archive Completed Tasks":
                new_value = not archive_completed
                config.set('archive_completed_tasks', new_value)
                output.append(f"\n✅ Archive completed tasks: {'Enabled' if new_value else 'Disabled'}")
                
            elif action == "View Archive Usage":
                archive_dir = Path('.archive')
                if archive_dir.exists():
                    total_size = sum(f.stat().st_size for f in archive_dir.rglob('*') if f.is_file())
                    file_count = sum(1 for f in archive_dir.rglob('*') if f.is_file())
                    output.append(f"\n📊 Archive Statistics:")
                    output.append(f"  Total files: {file_count:,}")
                    output.append(f"  Total size: {total_size / 1024 / 1024:.1f} MB")
                    output.append(f"\n💡 Use: CLEAN to manage archive space")
                else:
                    output.append(f"\n❌ No .archive folder found")
            
            return "\n".join(output)
            
        except Exception as e:
            return self.format_error("Version control settings management failed", e)
