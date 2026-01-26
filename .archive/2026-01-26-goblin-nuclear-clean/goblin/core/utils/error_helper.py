"""
Error Helper - Centralized error handling with dev mode prompts
Provides consistent error messages with suggestions for DEV MODE and OK FIX
"""

import traceback
from typing import Optional


def format_system_error(error: Exception, context: str = "", show_traceback: bool = True) -> str:
    """
    Format a system error with helpful recovery suggestions.
    
    Args:
        error: The exception that occurred
        context: Additional context about what was being attempted
        show_traceback: Whether to include full traceback
        
    Returns:
        Formatted error message with recovery suggestions
    """
    error_msg = "💀 CATASTROPHIC FAILURE\n"
    error_msg += "═" * 70 + "\n"
    
    if context:
        error_msg += f"📍 Context: {context}\n"
    
    error_msg += f"❌ Error: {type(error).__name__}: {str(error)}\n"
    
    if show_traceback:
        error_msg += "\n🔍 Stack Trace:\n"
        error_msg += "-" * 70 + "\n"
        tb = traceback.format_exc()
        error_msg += tb
        error_msg += "-" * 70 + "\n"
    
    error_msg += "\n🛠️  Recovery Options:\n"
    error_msg += "   1. DEV MODE      - Enter development mode for diagnostics\n"
    error_msg += "   2. OK FIX        - Use AI assistant to analyze and fix\n"
    error_msg += "   3. DEBUG STATUS  - Check system health and logs\n"
    error_msg += "   4. REPAIR        - Run automated system repair\n"
    error_msg += "\n💡 Tip: Type 'DEV MODE' to enable advanced debugging tools\n"
    error_msg += "═" * 70 + "\n"
    
    return error_msg


def format_command_error(error: Exception, command: str, show_traceback: bool = False) -> str:
    """
    Format a command execution error with recovery suggestions.
    Prompts for DEV MODE on code errors (SyntaxError, ImportError, etc.)
    
    Args:
        error: The exception that occurred
        command: The command that failed
        show_traceback: Whether to include full traceback
        
    Returns:
        Formatted error message with optional DEV MODE prompt
    """
    error_type = type(error).__name__
    
    # Auto-prompt for DEV MODE on code-related errors
    code_errors = ['SyntaxError', 'ImportError', 'ModuleNotFoundError', 
                   'AttributeError', 'NameError', 'IndentationError']
    
    error_msg = format_system_error(
        error,
        context=f"Command: {command}",
        show_traceback=show_traceback
    )
    
    # Add DEV MODE prompt for code errors
    if error_type in code_errors:
        error_msg += "\n⚠️  Code error detected - this may require system file repair\n"
        error_msg += "\n❓ Enter DEV MODE for advanced debugging and repair tools?\n"
        error_msg += "   Type 'DEV MODE' to enable, or press Enter to continue\n"
        error_msg += "   💡 In DEV MODE you can use 'OK FIX' for AI-assisted repair\n"
    
    return error_msg


def format_startup_error(error: Exception, component: str) -> str:
    """
    Format a startup/initialization error.
    
    Args:
        error: The exception that occurred
        component: The component that failed to initialize
        
    Returns:
        Formatted error message
    """
    error_msg = "🚨 STARTUP FAILURE\n"
    error_msg += "═" * 70 + "\n"
    error_msg += f"❌ Failed to initialize: {component}\n"
    error_msg += f"   Error: {type(error).__name__}: {str(error)}\n"
    error_msg += "\n🛠️  Try:\n"
    error_msg += "   • Check virtual environment: source .venv/bin/activate\n"
    error_msg += "   • Verify dependencies: pip install -r requirements.txt\n"
    error_msg += "   • Run system repair: python uDOS.py (then type REPAIR)\n"
    error_msg += "   • Check logs: memory/logs/auto/\n"
    error_msg += "═" * 70 + "\n"
    
    return error_msg


def format_extension_error(error: Exception, extension_name: str, action: str = "load") -> str:
    """
    Format an extension-related error.
    
    Args:
        error: The exception that occurred
        extension_name: Name of the extension
        action: What was being attempted (load, start, stop, etc.)
        
    Returns:
        Formatted error message
    """
    error_msg = f"⚠️  EXTENSION ERROR: {extension_name}\n"
    error_msg += "═" * 70 + "\n"
    error_msg += f"❌ Failed to {action}: {type(error).__name__}\n"
    error_msg += f"   {str(error)}\n"
    error_msg += "\n🛠️  Recovery:\n"
    error_msg += f"   • Check extension status: POKE STATUS {extension_name}\n"
    error_msg += f"   • View extension info: POKE INFO {extension_name}\n"
    error_msg += f"   • Reinstall: POKE UNINSTALL {extension_name} && POKE INSTALL {extension_name}\n"
    error_msg += "   • Get AI help: OK FIX\n"
    error_msg += "═" * 70 + "\n"
    
    return error_msg


def suggest_dev_mode_help() -> str:
    """Get helpful message about entering DEV MODE."""
    return (
        "\n💡 For advanced debugging:\n"
        "   • Type 'DEV MODE' to enable development tools\n"
        "   • Type 'OK FIX' to get AI-powered assistance\n"
        "   • Type 'DEBUG STATUS' to see system diagnostics\n"
    )


def wrap_with_error_handling(func):
    """
    Decorator to wrap functions with automatic error handling.
    
    Usage:
        @wrap_with_error_handling
        def my_function():
            # Your code here
    """
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except Exception as e:
            error_msg = format_system_error(
                e,
                context=f"Function: {func.__name__}",
                show_traceback=True
            )
            print(error_msg)
            return None
    
    wrapper.__name__ = func.__name__
    wrapper.__doc__ = func.__doc__
    return wrapper
