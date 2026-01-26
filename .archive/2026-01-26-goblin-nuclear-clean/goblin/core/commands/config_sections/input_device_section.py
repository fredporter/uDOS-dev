"""
Input Device Configuration Section

Manages input device settings (keyboard shortcuts, mouse clicks, keypad navigation)
"""

from .base_section import BaseConfigSection
from dev.goblin.core.uDOS_main import get_config


class InputDeviceSection(BaseConfigSection):
    """Manages input device settings."""
    
    def __init__(self, config_manager, input_manager, output_formatter, logger=None, parent_handler=None):
        super().__init__(config_manager, input_manager, output_formatter, logger)
        self.parent_handler = parent_handler
    
    def handle(self):
        """Manage Input Device settings (v1.2.25)."""
        self.clear_screen()
        try:
            config = get_config()
            
            output = []
            output.append(self.output_formatter.format_panel(
                "🎮 Keyboard & Mouse Settings",
                "Choose how you want to control uDOS (keyboard shortcuts, mouse clicks)."
            ))
            
            # Current settings
            input_mode = config.get('input_mode', 'hybrid')
            mouse_enabled = config.get('mouse_enabled', True)
            keypad_navigation = config.get('keypad_navigation', True)
            page_size = config.get('selector_page_size', 9)
            
            output.append(f"\nCurrent Settings:")
            output.append(f"  Input mode: {input_mode}")
            output.append(f"  Mouse support: {'✅ Enabled' if mouse_enabled else '❌ Disabled'}")
            output.append(f"  Keypad navigation: {'✅ Enabled' if keypad_navigation else '❌ Disabled'}")
            output.append(f"  Selector page size: {page_size} items")
            
            output.append(f"\n🎮 Input Modes:")
            output.append(f"  • keypad: Numpad navigation only (8↑ 2↓ 4← 6→)")
            output.append(f"  • full_keyboard: Full keyboard support")
            output.append(f"  • hybrid: Both keypad and full keyboard")
            
            action = self.input_manager.prompt_choice(
                message="Choose an action:",
                choices=[
                    "Set Input Mode",
                    "Toggle Mouse Support",
                    "Toggle Keypad Navigation",
                    "Set Page Size",
                    "Detect Capabilities",
                    "Back to Main Menu"
                ],
                default="Back to Main Menu"
            )
            
            # Handle back to main menu
            if action == "Back to Main Menu":
                return None

            if action == "Set Input Mode":
                new_mode = self.input_manager.prompt_choice(
                    message="Select input mode:",
                    choices=["keypad", "full_keyboard", "hybrid"],
                    default=input_mode
                )
                config.set('input_mode', new_mode)
                output.append(f"\n✅ Input mode set to: {new_mode}")
                
            elif action == "Toggle Mouse Support":
                new_value = not mouse_enabled
                config.set('mouse_enabled', new_value)
                output.append(f"\n✅ Mouse support: {'Enabled' if new_value else 'Disabled'}")
                output.append(f"💡 Use: REBOOT to apply changes")
                
            elif action == "Toggle Keypad Navigation":
                new_value = not keypad_navigation
                config.set('keypad_navigation', new_value)
                output.append(f"\n✅ Keypad navigation: {'Enabled' if new_value else 'Disabled'}")
                output.append(f"💡 Use: REBOOT to apply changes")
                
            elif action == "Set Page Size":
                new_size = self.input_manager.prompt_user(
                    message="Enter page size (1-20):",
                    default=str(page_size),
                    required=True
                )
                try:
                    new_size_int = int(new_size)
                    if 1 <= new_size_int <= 20:
                        config.set('selector_page_size', new_size_int)
                        output.append(f"\n✅ Selector page size set to: {new_size_int}")
                    else:
                        output.append(f"\n❌ Invalid value. Must be between 1 and 20.")
                except ValueError:
                    output.append(f"\n❌ Invalid number: {new_size}")
                    
            elif action == "Detect Capabilities":
                try:
                    from dev.goblin.core.services.device_manager import DeviceManager
                    dm = DeviceManager()
                    dm.scan_hardware()
                    
                    output.append(f"\n🔍 Detected Capabilities:")
                    output.append(f"  Terminal: {dm.get_info('terminal')['type']}")
                    output.append(f"  Mouse: {'✅ Available' if dm.has_mouse() else '❌ Not available'}")
                    output.append(f"  Input mode: {dm.get_input_mode()}")
                    output.append(f"\n💡 Settings will be auto-configured on next boot")
                except ImportError:
                    output.append(f"\n❌ Device Manager not available (v1.2.25+ required)")
            
            return "\n".join(output)
            
        except Exception as e:
            return self.format_error("Input device settings management failed", e)
