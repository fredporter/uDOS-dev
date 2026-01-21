"""
uDOS Profile Handler
Alpha v1.0.0.65

Manages user profile and configuration via the ConfigManager.
Provides setup wizard, variable get/set, and form integration.

Commands:
    PROFILE                    - View current profile
    PROFILE SETUP             - Run interactive setup wizard
    PROFILE EDIT              - Open udos.md in editor
    PROFILE SET $VAR value    - Set a variable
    PROFILE GET $VAR          - Get a variable value
    PROFILE EXPORT            - Export profile to JSON
    PROFILE RESET             - Reset to defaults

The PROFILE command is the user-facing interface to udos.md.
"""

from pathlib import Path
from datetime import datetime
from typing import Dict, Any, Optional, List

from .base_handler import BaseCommandHandler
from dev.goblin.core.config import Config  # v1.1.0 Unified configuration
from dev.goblin.core.services.logging_manager import get_logger

logger = get_logger("profile-handler")


class ProfileHandler(BaseCommandHandler):
    """Handler for PROFILE commands (user configuration)."""

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.config = Config()
        self.root_path = Path(__file__).parent.parent.parent

    def handle(self, command: str, params: list, grid=None, parser=None) -> dict:
        """Route PROFILE commands to handlers."""

        if not params:
            return self._handle_show([], grid)

        subcommand = params[0].upper()
        sub_params = params[1:] if len(params) > 1 else []

        handlers = {
            "SETUP": self._handle_setup,
            "EDIT": self._handle_edit,
            "SET": self._handle_set,
            "GET": self._handle_get,
            "EXPORT": self._handle_export,
            "RESET": self._handle_reset,
            "HELP": self._handle_help,
        }

        handler = handlers.get(subcommand)
        if handler:
            return handler(sub_params, grid)

        # Check if first param is a variable name
        if params[0].startswith("$"):
            return self._handle_get(params, grid)

        return self._handle_help([], grid)

    def _handle_show(self, params: list, grid=None) -> dict:
        """Show current profile summary."""
        config = self.config.get_all()

        lines = [
            "👤 PROFILE",
            "",
            "─" * 40,
            "",
            "📋 User",
            f"   Name:     {config.get('USER_NAME', 'Not set')}",
            f"   Email:    {config.get('USER_EMAIL') or 'Not set'}",
            f"   Location: {config.get('USER_LOCATION') or 'Not set'}",
            f"   Timezone: {config.get('USER_TIMEZONE', 'UTC')}",
            "",
            "🔐 Security",
            f"   Auth:     {'Enabled' if config.get('AUTH_ENABLED') else 'Disabled'}",
            f"   Method:   {config.get('AUTH_METHOD', 'none')}",
            f"   Timeout:  {config.get('SESSION_TIMEOUT', 0)}m",
            "",
            "⚙️ Preferences",
            f"   Theme:    {config.get('THEME', 'foundation')}",
            f"   Sound:    {'On' if config.get('SOUND_ENABLED') else 'Off'}",
            f"   Tips:     {'On' if config.get('TIPS_ENABLED') else 'Off'}",
            f"   Autosave: {'On' if config.get('AUTO_SAVE') else 'Off'}",
            "",
            "📁 Project",
            f"   Name:     {config.get('PROJECT_NAME') or 'None'}",
            "",
            "─" * 40,
            "",
            "Commands:",
            "  PROFILE SETUP    Run setup wizard",
            "  PROFILE EDIT     Open udos.md",
            "  PROFILE SET $VAR value",
            "  PROFILE GET $VAR",
        ]

        return {"status": "success", "message": "\n".join(lines)}

    def _handle_setup(self, params: list, grid=None) -> dict:
        """Run interactive setup wizard."""
        if not self.input_manager:
            return {"status": "error", "message": "Setup requires interactive mode"}

        lines = ["🚀 PROFILE SETUP", "", "Let's configure your uDOS profile.", ""]

        # Step 1: Name
        current_name = get_var("USER_NAME", "survivor")
        new_name = self.input_manager.prompt_input(f"Your name [{current_name}]: ")
        if new_name:
            set_var("USER_NAME", new_name)
            lines.append(f"✅ Name: {new_name}")
        else:
            lines.append(f"✅ Name: {current_name} (unchanged)")

        # Step 2: Timezone
        timezones = [
            "UTC",
            "America/New_York",
            "America/Los_Angeles",
            "Europe/London",
            "Europe/Paris",
            "Asia/Tokyo",
            "Australia/Sydney",
        ]
        current_tz = get_var("USER_TIMEZONE", "UTC")

        tz_choice = self.input_manager.prompt_choice(
            "Select your timezone:", choices=timezones, default=current_tz
        )
        if tz_choice:
            set_var("USER_TIMEZONE", tz_choice)
            lines.append(f"✅ Timezone: {tz_choice}")

        # Step 3: Theme
        themes = ["foundation", "galaxy", "survival", "retro"]
        current_theme = get_var("THEME", "foundation")

        theme_choice = self.input_manager.prompt_choice(
            "Choose a theme:", choices=themes, default=current_theme
        )
        if theme_choice:
            set_var("THEME", theme_choice)
            lines.append(f"✅ Theme: {theme_choice}")

        # Step 4: Security
        security_choice = self.input_manager.prompt_choice(
            "Enable session security?",
            choices=["No security", "PIN code", "Password"],
            default="No security",
        )

        if "PIN" in security_choice:
            set_var("AUTH_ENABLED", True)
            set_var("AUTH_METHOD", "pin")
            # TODO: Prompt for PIN and store hash
            lines.append("✅ Security: PIN enabled")
        elif "Password" in security_choice:
            set_var("AUTH_ENABLED", True)
            set_var("AUTH_METHOD", "password")
            # TODO: Prompt for password and store hash
            lines.append("✅ Security: Password enabled")
        else:
            set_var("AUTH_ENABLED", False)
            set_var("AUTH_METHOD", "none")
            lines.append("✅ Security: Disabled")

        lines.extend(
            [
                "",
                "─" * 40,
                "",
                "✨ Setup complete!",
                "",
                "Your settings are saved in memory/config/udos.md",
                "Edit anytime with: PROFILE EDIT",
            ]
        )

        return {"status": "success", "message": "\n".join(lines)}

    def _handle_edit(self, params: list, grid=None) -> dict:
        """Open udos.md in editor."""
        config_file = self.root_path / "memory" / "config" / "udos.md"

        # Ensure file exists
        if not config_file.exists():
            # Create from template
            config_file.parent.mkdir(parents=True, exist_ok=True)
            self.config._save_user_config()

        # Return edit command
        return {
            "status": "success",
            "action": "edit",
            "file": str(config_file),
            "message": f"Opening {config_file}...",
        }

    def _handle_set(self, params: list, grid=None) -> dict:
        """Set a variable value."""
        if len(params) < 2:
            return {"status": "error", "message": "Usage: PROFILE SET $VAR value"}

        var_name = params[0].lstrip("$").upper()
        value = " ".join(params[1:])

        # Handle boolean values
        if value.lower() in ("true", "yes", "on", "1"):
            value = True
        elif value.lower() in ("false", "no", "off", "0"):
            value = False

        if set_var(var_name, value):
            return {"status": "success", "message": f"✅ ${var_name} = {value}"}
        else:
            return {"status": "error", "message": f"Failed to set ${var_name}"}

    def _handle_get(self, params: list, grid=None) -> dict:
        """Get a variable value."""
        if not params:
            return {"status": "error", "message": "Usage: PROFILE GET $VAR"}

        var_name = params[0].lstrip("$").upper()
        value = get_var(var_name)

        if value is not None:
            return {"status": "success", "message": f"${var_name} = {value}"}
        else:
            return {"status": "error", "message": f"${var_name} is not set"}

    def _handle_export(self, params: list, grid=None) -> dict:
        """Export profile to JSON."""
        import json

        export_file = (
            self.root_path
            / "memory"
            / "exports"
            / f"profile-{datetime.now().strftime('%Y%m%d-%H%M%S')}.json"
        )
        export_file.parent.mkdir(parents=True, exist_ok=True)

        config = self.config.get_all()

        # Remove system vars from export
        export_data = {k: v for k, v in config.items() if not k.startswith("SYS_")}

        export_file.write_text(json.dumps(export_data, indent=2))

        return {
            "status": "success",
            "message": f"✅ Profile exported to: {export_file.name}",
        }

    def _handle_reset(self, params: list, grid=None) -> dict:
        """Reset profile to defaults."""
        if self.input_manager:
            confirm = self.input_manager.prompt_confirm(
                "Reset all settings to defaults?"
            )
            if not confirm:
                return {"status": "cancelled", "message": "Reset cancelled"}

        # Delete config file
        config_file = self.root_path / "memory" / "config" / "udos.md"
        if config_file.exists():
            config_file.unlink()

        # Reload defaults
        self.config.load()

        return {"status": "success", "message": "✅ Profile reset to defaults"}

    def _handle_help(self, params: list, grid=None) -> dict:
        """Show help."""
        help_text = """
👤 PROFILE Command

View and manage your uDOS configuration.

Usage:
  PROFILE                    Show current profile
  PROFILE SETUP             Run interactive setup wizard
  PROFILE EDIT              Open udos.md in editor
  PROFILE SET $VAR value    Set a variable
  PROFILE GET $VAR          Get a variable value
  PROFILE EXPORT            Export profile to JSON
  PROFILE RESET             Reset to defaults

Variables:
  $USER_NAME        Your display name
  $USER_TIMEZONE    Your timezone (e.g., Australia/Sydney)
  $THEME            UI theme (foundation, galaxy, survival, retro)
  $AUTH_ENABLED     Enable session security (true/false)
  $AUTH_METHOD      Security method (none, pin, password)
  $PROJECT_NAME     Current project name
  $MY_VAR_1..5      Custom user variables

Examples:
  PROFILE SET $USER_NAME Fred
  PROFILE SET $THEME galaxy
  PROFILE SET $MY_VAR_1 my custom value
  PROFILE GET $THEME

Config File:
  Your settings are stored in memory/config/udos.md
  This is a markdown file you can edit directly.
"""
        return {"status": "success", "message": help_text}

    def get_form_definition(self, section: str = "all") -> Dict[str, Any]:
        """
        Get form definition for gtx-form integration.

        Used by API to provide form data to Tauri app.
        """
        return self.config.get_form_definition(section)
