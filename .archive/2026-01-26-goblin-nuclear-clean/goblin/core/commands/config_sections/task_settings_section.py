"""
Task Settings Configuration Section

Manages task management system settings (auto-save, priorities, location tracking)
"""

from pathlib import Path
from .base_section import BaseConfigSection
from dev.goblin.core.uDOS_main import get_config


class TaskSettingsSection(BaseConfigSection):
    """Manages task management system settings."""
    
    def __init__(self, config_manager, input_manager, output_formatter, logger=None, parent_handler=None):
        """
        Initialize task settings section.
        
        Args:
            parent_handler: Parent configuration handler (for compatibility)
        """
        super().__init__(config_manager, input_manager, output_formatter, logger)
        self.parent_handler = parent_handler
    
    def handle(self):
        """Manage Task Management system settings (v1.2.23)."""
        self.clear_screen()
        try:
            config = get_config()
            
            output = []
            output.append(self.output_formatter.format_panel(
                "📋 Task & Project Management",
                "Manage tasks, projects, and track your progress."
            ))
            
            # Current settings
            task_auto_save = config.get('task_auto_save', True)
            task_default_priority = config.get('task_default_priority', 'medium')
            project_location_tracking = config.get('project_location_tracking', True)
            
            output.append(f"\nCurrent Settings:")
            output.append(f"  Auto-save tasks: {'✅ Enabled' if task_auto_save else '❌ Disabled'}")
            output.append(f"  Default priority: {task_default_priority}")
            output.append(f"  Location tracking: {'✅ Enabled' if project_location_tracking else '❌ Disabled'}")
            
            action = self.input_manager.prompt_choice(
                message="Choose an action:",
                choices=[
                    "Toggle Auto-save",
                    "Set Default Priority",
                    "Toggle Location Tracking",
                    "View Unified Tasks File",
                    "Back to Main Menu"
                ],
                default="Back to Main Menu"
            )
            
            # Handle back to main menu
            if action == "Back to Main Menu":
                return None  # Signal to return to main CONFIG menu

            if action == "Toggle Auto-save":
                new_value = not task_auto_save
                config.set('task_auto_save', new_value)
                output.append(f"\n✅ Task auto-save: {'Enabled' if new_value else 'Disabled'}")
                
            elif action == "Set Default Priority":
                new_priority = self.input_manager.prompt_choice(
                    message="Select default priority:",
                    choices=["low", "medium", "high", "urgent"],
                    default=task_default_priority
                )
                config.set('task_default_priority', new_priority)
                output.append(f"\n✅ Default priority set to: {new_priority}")
                
            elif action == "Toggle Location Tracking":
                new_value = not project_location_tracking
                config.set('project_location_tracking', new_value)
                output.append(f"\n✅ Project location tracking: {'Enabled' if new_value else 'Disabled'}")
                
            elif action == "View Unified Tasks File":
                tasks_file = Path('memory/bank/user/unified_tasks.json')
                if tasks_file.exists():
                    output.append(f"\n📁 Location: {tasks_file}")
                    output.append(f"📏 Size: {tasks_file.stat().st_size:,} bytes")
                    output.append(f"\n💡 Use: TASK LIST to view all tasks")
                else:
                    output.append(f"\n❌ Tasks file not found: {tasks_file}")
                    output.append(f"💡 Use: TASK CREATE to initialize task system")
            
            return "\n".join(output)
            
        except Exception as e:
            return self.format_error("Task settings management failed", e)
