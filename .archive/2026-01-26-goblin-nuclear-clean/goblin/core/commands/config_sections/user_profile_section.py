"""
User Profile Configuration Section

Manages user profile settings (username, password, location, timezone)
"""

from .base_section import BaseConfigSection
from dev.goblin.core.uDOS_main import get_config


class UserProfileSection(BaseConfigSection):
    """Manages user profile settings."""
    
    def handle(self):
        """Interactive user profile management (v1.5.0: Uses ConfigManager)."""
        self.clear_screen()
        try:
            # Get ConfigManager instance
            config = get_config()

            # Auto-detect system timezone and location
            from dev.goblin.core.utils.system_info import get_system_timezone
            detected_timezone, detected_city = get_system_timezone()

            # Get current profile from ConfigManager (user.json only - single source of truth)
            user_name = config.get_user('USER_PROFILE.NAME', '')
            password = config.get_user('USER_PROFILE.PASSWORD', '')
            location = config.get_user('USER_PROFILE.LOCATION', '')
            timezone = config.get_user('USER_PROFILE.TIMEZONE', '')

            # Use detected values as defaults if not set
            if not timezone or timezone == 'UTC':
                timezone = detected_timezone
            if not location or location == 'Unknown':
                location = detected_city

            # Show current profile
            output = []
            output.append(self.output_formatter.format_panel(
                "User Profile",
                f"Username: {user_name or 'Not set'}\n"
                f"Password: {'●●●●●●' if password else 'Not set (optional)'}\n"
                f"Location: {location or 'Not set'}\n"
                f"Timezone: {timezone}\n"
                f"\nℹ️  Detected: {detected_timezone} ({detected_city})"
            ))

            # Ask what to update
            action = self.input_manager.prompt_choice(
                message="What would you like to update?",
                choices=[
                    "Username",
                    "Password",
                    "Location",
                    "Timezone",
                    "Update All Fields",
                    "Back to Main Menu"
                ],
                default="Back to Main Menu"
            )

            # Handle back to main menu
            if action == "Back to Main Menu":
                return None  # Signal to return to main CONFIG menu

            if action == "Username":
                new_name = self.input_manager.prompt_user(
                    message="Enter username:",
                    default=user_name,
                    required=True
                )
                # Update via ConfigManager (user.json only - single source of truth)
                config.set_user('USER_PROFILE.NAME', new_name)
                output.append(f"\n✅ Username updated to: {new_name}")

            elif action == "Password":
                new_password = self.input_manager.prompt_user(
                    message="Enter password (leave blank for none):",
                    default="",
                    required=False
                )
                config.set_user('USER_PROFILE.PASSWORD', new_password if new_password else '')
                if new_password:
                    output.append("\n✅ Password updated")
                else:
                    output.append("\n✅ Password cleared")

            elif action == "Location":
                new_location = self.input_manager.prompt_user(
                    message=f"Enter location (detected: {detected_city}):",
                    default=location or detected_city,
                    required=False
                )
                config.set_user('USER_PROFILE.LOCATION', new_location)
                output.append(f"\n✅ Location updated to: {new_location}")

            elif action == "Timezone":
                new_timezone = self.input_manager.prompt_user(
                    message=f"Enter timezone (detected: {detected_timezone}):",
                    default=timezone or detected_timezone,
                    required=False
                )
                config.set_user('USER_PROFILE.TIMEZONE', new_timezone)
                output.append(f"\n✅ Timezone updated to: {new_timezone}")

            elif action == "Update All Fields":
                # Prompt for all fields with auto-detected defaults
                new_name = self.input_manager.prompt_user(
                    message="Username:",
                    default=user_name,
                    required=True
                )

                new_password = self.input_manager.prompt_user(
                    message="Password (leave blank for none):",
                    default="",
                    required=False
                )

                new_timezone = self.input_manager.prompt_user(
                    message=f"Timezone (detected: {detected_timezone}):",
                    default=timezone or detected_timezone,
                    required=False
                )

                new_location = self.input_manager.prompt_user(
                    message=f"Location (defaults to timezone city):",
                    default=location or detected_city,
                    required=False
                )

                # Save all fields via ConfigManager (user.json only - single source of truth)
                config.set_user('USER_PROFILE.NAME', new_name)
                if new_password:
                    config.set_user('USER_PROFILE.PASSWORD', new_password)
                config.set_user('USER_PROFILE.TIMEZONE', new_timezone)
                config.set_user('USER_PROFILE.LOCATION', new_location)

                output.append("\n✅ User profile updated")
                output.append("📝 Changes saved to user.json")

            return "\n".join(output)

        except Exception as e:
            return self.format_error("User profile management failed", e)
