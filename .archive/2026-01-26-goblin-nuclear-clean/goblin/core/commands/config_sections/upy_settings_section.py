"""
uPY Settings Configuration Section

Manages uPY scripting and execution settings (execution modes, display modes, performance)
"""

from .base_section import BaseConfigSection
from dev.goblin.core.uDOS_main import get_config


class UPYSettingsSection(BaseConfigSection):
    """Manages uPY scripting and execution settings."""
    
    def __init__(self, config_manager, input_manager, output_formatter, logger=None, parent_handler=None):
        super().__init__(config_manager, input_manager, output_formatter, logger)
        self.parent_handler = parent_handler
    
    def handle(self):
        """Manage uPY scripting and execution settings (v1.2.24)."""
        self.clear_screen()
        try:
            config = get_config()
            
            output = []
            output.append(self.output_formatter.format_panel(
                "⚡ Scripting & Performance",
                "Control how scripts run and optimize performance."
            ))
            
            # Current settings
            execution_mode = config.get('upy_execution_mode', 'python_first')
            display_mode = config.get('upy_display_mode', 'symbolic')
            auto_convert = config.get('upy_auto_convert', True)
            
            output.append(f"\nCurrent Settings:")
            output.append(f"  Execution mode: {execution_mode}")
            output.append(f"  Display mode: {display_mode}")
            output.append(f"  Auto-convert: {'✅ Enabled' if auto_convert else '❌ Disabled'}")
            
            output.append(f"\n⚡ Execution Modes:")
            output.append(f"  • python_first: Native Python (925K ops/sec)")
            output.append(f"  • runtime_parser: Line-by-line interpretation (9K ops/sec)")
            output.append(f"  • hybrid: Python for production, parser for debug")
            
            output.append(f"\n📝 Display Modes:")
            output.append(f"  • pythonic: Raw Python code")
            output.append(f"  • symbolic: uCODE bracket syntax COMMAND[ args ]")
            output.append(f"  • typo: Beautiful typography (requires extension)")
            
            action = self.input_manager.prompt_choice(
                message="Choose an action:",
                choices=[
                    "Set Execution Mode",
                    "Set Display Mode",
                    "Toggle Auto-convert",
                    "View Performance Stats",
                    "Back to Main Menu"
                ],
                default="Back to Main Menu"
            )
            
            # Handle back to main menu
            if action == "Back to Main Menu":
                return None

            if action == "Set Execution Mode":
                new_mode = self.input_manager.prompt_choice(
                    message="Select execution mode:",
                    choices=["python_first", "runtime_parser", "hybrid"],
                    default=execution_mode
                )
                config.set('upy_execution_mode', new_mode)
                output.append(f"\n✅ Execution mode set to: {new_mode}")
                if new_mode == "python_first":
                    output.append(f"⚡ ~925,078 ops/sec (100x faster)")
                elif new_mode == "runtime_parser":
                    output.append(f"🐢 ~9,000 ops/sec (sandbox/debug mode)")
                    
            elif action == "Set Display Mode":
                new_mode = self.input_manager.prompt_choice(
                    message="Select display mode:",
                    choices=["pythonic", "symbolic", "typo"],
                    default=display_mode
                )
                config.set('upy_display_mode', new_mode)
                output.append(f"\n✅ Display mode set to: {new_mode}")
                
            elif action == "Toggle Auto-convert":
                new_value = not auto_convert
                config.set('upy_auto_convert', new_value)
                output.append(f"\n✅ Auto-convert: {'Enabled' if new_value else 'Disabled'}")
                
            elif action == "View Performance Stats":
                output.append(f"\n📊 Performance Comparison:")
                output.append(f"  Python-First:    925,078 ops/sec (100x faster)")
                output.append(f"  Runtime Parser:    9,000 ops/sec (sandbox mode)")
                output.append(f"\n💡 Use python_first for production scripts")
                output.append(f"💡 Use runtime_parser for learning/debugging")
            
            return "\n".join(output)
            
        except Exception as e:
            return self.format_error("uPY settings management failed", e)
