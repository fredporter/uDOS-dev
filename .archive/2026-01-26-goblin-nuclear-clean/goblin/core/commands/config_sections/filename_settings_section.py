"""
Filename Settings Configuration Section

Manages filename standards and file organization settings
"""

from .base_section import BaseConfigSection
from dev.goblin.core.uDOS_main import get_config


class FilenameSettingsSection(BaseConfigSection):
    """Manages filename standards and organization."""
    
    def __init__(self, config_manager, input_manager, output_formatter, logger=None, parent_handler=None):
        super().__init__(config_manager, input_manager, output_formatter, logger)
        self.parent_handler = parent_handler
    
    def handle(self):
        """Manage Filename Standard and organization settings (v1.2.23)."""
        self.clear_screen()
        try:
            config = get_config()
            
            output = []
            output.append(self.output_formatter.format_panel(
                "📝 File Organization & Naming",
                "Control how files are named and organized automatically."
            ))
            
            # Current settings
            filename_format = config.get('filename_format', 'dated')
            auto_organize = config.get('auto_organize', True)
            duplicate_detection = config.get('duplicate_detection', True)
            date_organization = config.get('date_organization', 'monthly')
            
            output.append(f"\nCurrent Settings:")
            output.append(f"  Default format: {filename_format}")
            output.append(f"  Auto-organize: {'✅ Enabled' if auto_organize else '❌ Disabled'}")
            output.append(f"  Duplicate detection: {'✅ Enabled' if duplicate_detection else '❌ Disabled'}")
            output.append(f"  Date organization: {date_organization}")
            
            output.append(f"\n📝 Filename Formats:")
            output.append(f"  • dated:   20251213-myfile.txt")
            output.append(f"  • timed:   20251213-164500UTC-script.upy")
            output.append(f"  • located: 20251213-164500UTC-AA340-mission.upy")
            
            action = self.input_manager.prompt_choice(
                message="Choose an action:",
                choices=[
                    "Set Default Format",
                    "Toggle Auto-organize",
                    "Toggle Duplicate Detection",
                    "Set Date Organization",
                    "Back to Main Menu"
                ],
                default="Back to Main Menu"
            )
            
            # Handle back to main menu
            if action == "Back to Main Menu":
                return None  # Signal to return to main CONFIG menu

            if action == "Set Default Format":
                new_format = self.input_manager.prompt_choice(
                    message="Select default filename format:",
                    choices=["dated", "timed", "located", "instance"],
                    default=filename_format
                )
                config.set('filename_format', new_format)
                output.append(f"\n✅ Default filename format set to: {new_format}")
                
            elif action == "Toggle Auto-organize":
                new_value = not auto_organize
                config.set('auto_organize', new_value)
                output.append(f"\n✅ Auto-organize: {'Enabled' if new_value else 'Disabled'}")
                
            elif action == "Toggle Duplicate Detection":
                new_value = not duplicate_detection
                config.set('duplicate_detection', new_value)
                output.append(f"\n✅ Duplicate detection: {'Enabled' if new_value else 'Disabled'}")
                
            elif action == "Set Date Organization":
                new_org = self.input_manager.prompt_choice(
                    message="Select date organization:",
                    choices=["daily", "weekly", "monthly", "yearly"],
                    default=date_organization
                )
                config.set('date_organization', new_org)
                output.append(f"\n✅ Date organization set to: {new_org}")
            
            return "\n".join(output)
            
        except Exception as e:
            return self.format_error("Filename settings management failed", e)
