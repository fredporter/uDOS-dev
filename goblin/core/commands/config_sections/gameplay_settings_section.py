"""
Gameplay Settings Configuration Section

Manages gameplay systems settings (checkpoints, XP, inventory, barter)
"""

from .base_section import BaseConfigSection
from dev.goblin.core.uDOS_main import get_config


class GameplaySettingsSection(BaseConfigSection):
    """Manages gameplay systems settings."""
    
    def __init__(self, config_manager, input_manager, output_formatter, logger=None, parent_handler=None):
        super().__init__(config_manager, input_manager, output_formatter, logger)
        self.parent_handler = parent_handler
    
    def handle(self):
        """Manage Gameplay systems settings (v1.2.24)."""
        self.clear_screen()
        try:
            config = get_config()
            
            output = []
            output.append(self.output_formatter.format_panel(
                "🎮 Gameplay Features",
                "Enable or disable game-like features (checkpoints, inventory, experience points)."
            ))
            
            # Current settings
            checkpoint_auto_save = config.get('checkpoint_auto_save', True)
            xp_tracking = config.get('xp_tracking', True)
            inventory_limit = config.get('inventory_item_limit', 100)
            barter_enabled = config.get('barter_enabled', True)
            
            output.append(f"\nCurrent Settings:")
            output.append(f"  Checkpoint auto-save: {'✅ Enabled' if checkpoint_auto_save else '❌ Disabled'}")
            output.append(f"  XP tracking: {'✅ Enabled' if xp_tracking else '❌ Disabled'}")
            output.append(f"  Inventory limit: {inventory_limit} items")
            output.append(f"  Barter system: {'✅ Enabled' if barter_enabled else '❌ Disabled'}")
            
            output.append(f"\n🎮 Core Gameplay Commands:")
            output.append(f"  • CHECKPOINT - Save/restore mission progress")
            output.append(f"  • XP - Experience points and leveling")
            output.append(f"  • ITEM - Basic inventory management")
            output.append(f"  • BARTER - Value exchange system")
            
            action = self.input_manager.prompt_choice(
                message="Choose an action:",
                choices=[
                    "Toggle Checkpoint Auto-save",
                    "Toggle XP Tracking",
                    "Set Inventory Limit",
                    "Toggle Barter System",
                    "View Storage Locations",
                    "Back to Main Menu"
                ],
                default="Back to Main Menu"
            )
            
            # Handle back to main menu
            if action == "Back to Main Menu":
                return None

            if action == "Toggle Checkpoint Auto-save":
                new_value = not checkpoint_auto_save
                config.set('checkpoint_auto_save', new_value)
                output.append(f"\n✅ Checkpoint auto-save: {'Enabled' if new_value else 'Disabled'}")
                
            elif action == "Toggle XP Tracking":
                new_value = not xp_tracking
                config.set('xp_tracking', new_value)
                output.append(f"\n✅ XP tracking: {'Enabled' if new_value else 'Disabled'}")
                
            elif action == "Set Inventory Limit":
                new_limit = self.input_manager.prompt_user(
                    message="Enter inventory limit (10-1000):",
                    default=str(inventory_limit),
                    required=True
                )
                try:
                    new_limit_int = int(new_limit)
                    if 10 <= new_limit_int <= 1000:
                        config.set('inventory_item_limit', new_limit_int)
                        output.append(f"\n✅ Inventory limit set to: {new_limit_int} items")
                    else:
                        output.append(f"\n❌ Invalid value. Must be between 10 and 1000.")
                except ValueError:
                    output.append(f"\n❌ Invalid number: {new_limit}")
                    
            elif action == "Toggle Barter System":
                new_value = not barter_enabled
                config.set('barter_enabled', new_value)
                output.append(f"\n✅ Barter system: {'Enabled' if new_value else 'Disabled'}")
                
            elif action == "View Storage Locations":
                output.append(f"\n📁 Storage Locations:")
                output.append(f"  • Checkpoints: memory/workflows/checkpoints/")
                output.append(f"  • XP Profile: memory/bank/user/profile.json")
                output.append(f"  • Inventory: Active sprite/character data")
                output.append(f"  • Barter Log: memory/bank/barter/")
                output.append(f"\n💡 Use respective commands to manage data")
            
            return "\n".join(output)
            
        except Exception as e:
            return self.format_error("Gameplay settings management failed", e)
