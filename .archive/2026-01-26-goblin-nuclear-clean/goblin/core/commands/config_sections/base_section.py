"""
Base Configuration Section

Base class for all configuration sections.
Provides common utilities and structure.
"""

import os
from typing import Optional


class BaseConfigSection:
    """Base class for configuration sections."""
    
    def __init__(self, config_manager, input_manager, output_formatter, logger=None):
        """
        Initialize config section.
        
        Args:
            config_manager: ConfigManager instance
            input_manager: InputManager instance for prompts
            output_formatter: OutputFormatter for display
            logger: Optional logger instance
        """
        self.config_manager = config_manager
        self.input_manager = input_manager
        self.output_formatter = output_formatter
        self.logger = logger
    
    def clear_screen(self):
        """Clear terminal screen."""
        os.system('clear' if os.name != 'nt' else 'cls')
    
    def handle(self) -> Optional[str]:
        """
        Handle the configuration section interactively.
        
        Returns:
            Output message or None to return to main menu
        """
        raise NotImplementedError("Subclasses must implement handle()")
    
    def format_error(self, message: str, error: Exception) -> str:
        """Format error message."""
        return self.output_formatter.format_error(
            message,
            error_details=str(error)
        )
