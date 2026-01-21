"""
uDOS v1.2.27 - Setup Handler

Handles first-time setup wizard and settings display:
- Interactive story-style setup wizard (SETUP)
- Settings display and viewing (SETUP --show, SETUP <key>)
- Basic setting modification (SETUP <key> <value>)
- Location and timezone detection
- User profile configuration

Extracted from configuration_handler.py (v1.2.27 refactor)
"""

import json
from pathlib import Path
from .base_handler import BaseCommandHandler
from dev.goblin.core.uDOS_main import get_config


class SetupHandler(BaseCommandHandler):
    """Handles first-time setup wizard and settings display."""

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    def handle_setup(self, params, grid, parser):
        """
        Interactive story-style setup wizard.

        Usage:
            SETUP                 - Run interactive setup wizard
            SETUP --show          - Display all current settings
            SETUP <key>           - Show specific setting
            SETUP <key> <value>   - Set setting value

        The interactive wizard will guide you through:
            - User profile (name, location, timezone)
            - System preferences (theme, editor, offline mode)
            - Optional world map location
        """
        # Check for --show flag or no params runs wizard
        if not params:
            return self._run_interactive_setup()
        elif params[0] == '--show' or params[0].upper() == 'SHOW':
            return self._show_all_settings()
        elif len(params) == 1:
            return self._show_setting(params[0])
        elif len(params) == 2:
            return self._set_setting(params[0], params[1])
        else:
            return ("❌ Invalid setup command\n\n"
                   "Usage:\n"
                   "  SETUP                  - Run interactive setup wizard\n"
                   "  SETUP --show           - Display all settings\n"
                   "  SETUP <key>           - Show specific setting\n"
                   "  SETUP <key> <value>   - Set setting value")

    def _run_interactive_setup(self):
        """Run interactive story-style setup wizard."""
        try:
            from dev.goblin.core.commands.handler_utils import HandlerUtils
            config = HandlerUtils.get_config()

            output = []
            output.append("")
            output.append(self.formatter.box_top())
            output.append(self.formatter.box_line("🎮 Welcome to uDOS Interactive Setup Wizard!", align="center"))
            output.append(self.formatter.box_bottom())
            output.append("")
            output.append("This wizard will help you configure your uDOS environment.")
            output.append("")

            # Get current values
            current_username = config.get_user('USER_PROFILE.NAME', '')
            current_location = config.get_user('USER_PROFILE.LOCATION', '')
            current_timezone = config.get_user('USER_PROFILE.TIMEZONE', 'UTC')
            current_theme = config.get_env('THEME', 'dungeon')

            changes_made = False

            # Username
            output.append("┌─────────────────────────────────────────────────────────┐")
            output.append("│ Step 1: User Profile                                    │")
            output.append("└─────────────────────────────────────────────────────────┘")
            output.append("")

            if not current_username or current_username == 'user':
                if self.input_manager:
                    username = self.input_manager.prompt_user(
                        message="What should we call you?",
                        default="Explorer",
                        required=True
                    )
                    config.set_user('USER_PROFILE.NAME', username)
                    output.append(f"✅ Username set to: {username}")
                    changes_made = True
                else:
                    output.append(f"Current username: {current_username}")
                    output.append("💡 To change: SETUP username <new_name>")
            else:
                output.append(f"✅ Username: {current_username}")

            output.append("")

            # Location & Timezone
            output.append("┌─────────────────────────────────────────────────────────┐")
            output.append("│ Step 2: Location & Time                                 │")
            output.append("└─────────────────────────────────────────────────────────┘")
            output.append("")

            # Auto-detect timezone
            try:
                from dev.goblin.core.utils.system_info import get_system_timezone
                detected_tz, detected_city = get_system_timezone()
                output.append(f"📍 Detected: {detected_city} ({detected_tz})")

                if not current_location or current_location == 'Unknown':
                    if self.input_manager:
                        # Load cities from cities.json
                        cities_data = self._load_cities_list()

                        if cities_data:
                            # Offer to use detected or select from list
                            use_detected = self.input_manager.prompt_choice(
                                message="Use detected location?",
                                choices=["Yes", "No, select from list"],
                                default="Yes"
                            )

                            if use_detected == "Yes":
                                # Find full city info from cities.json
                                city_info = next((c for c in cities_data if c['name'] == detected_city), None)
                                if city_info:
                                    config.set_user('USER_PROFILE.LOCATION', city_info['name'])
                                    config.set_user('USER_PROFILE.TIMEZONE', city_info['timezone']['name'])
                                else:
                                    config.set_user('USER_PROFILE.LOCATION', detected_city)
                                    config.set_user('USER_PROFILE.TIMEZONE', detected_tz)
                                output.append(f"✅ Location set to: {detected_city}")
                                output.append(f"✅ Timezone set to: {detected_tz}")
                                changes_made = True
                            else:
                                # Show cities selection
                                city_names = [f"{c['name']}, {c['country']}" for c in cities_data]
                                selected = self.input_manager.prompt_choice(
                                    message="Select your location:",
                                    choices=city_names[:20],  # Show first 20 cities
                                    default=city_names[0] if city_names else ""
                                )

                                if selected:
                                    # Extract city name
                                    city_name = selected.split(',')[0].strip()
                                    city_info = next((c for c in cities_data if c['name'] == city_name), None)

                                    if city_info:
                                        config.set_user('USER_PROFILE.LOCATION', city_info['name'])
                                        config.set_user('USER_PROFILE.TIMEZONE', city_info['timezone']['name'])
                                        output.append(f"✅ Location set to: {city_info['name']}, {city_info['country']}")
                                        output.append(f"✅ Timezone set to: {city_info['timezone']['name']}")
                                        changes_made = True
                        else:
                            # Fallback to manual entry if cities.json not available
                            use_detected = self.input_manager.prompt_choice(
                                message="Use detected location?",
                                choices=["Yes", "No, enter manually"],
                                default="Yes"
                            )

                            if use_detected == "Yes":
                                config.set_user('USER_PROFILE.LOCATION', detected_city)
                                config.set_user('USER_PROFILE.TIMEZONE', detected_tz)
                                output.append(f"✅ Location set to: {detected_city}")
                                output.append(f"✅ Timezone set to: {detected_tz}")
                                changes_made = True
                            else:
                                location = self.input_manager.prompt_user(
                                    message="Enter your location (city, country):",
                                    default=detected_city,
                                    required=False
                                )
                                if location:
                                    config.set_user('USER_PROFILE.LOCATION', location)
                                    config.set_user('USER_PROFILE.TIMEZONE', detected_tz)
                                    output.append(f"✅ Location set to: {location}")
                                    changes_made = True
                    else:
                        output.append(f"Current location: {current_location}")
                        output.append("💡 To change: SETUP location <city>")
                else:
                    output.append(f"✅ Location: {current_location}")
                    output.append(f"✅ Timezone: {current_timezone}")
            except:
                output.append(f"Location: {current_location}")
                output.append(f"Timezone: {current_timezone}")

            output.append("")

            # Theme selection
            output.append("┌─────────────────────────────────────────────────────────┐")
            output.append("│ Step 3: Visual Theme                                    │")
            output.append("└─────────────────────────────────────────────────────────┘")
            output.append("")
            output.append(f"Current theme: {current_theme}")
            output.append("")
            output.append("💡 Available themes: dungeon, cyberpunk, foundation")
            output.append("💡 To change theme: THEME <name>")
            output.append("")

            # Summary
            output.append("")
            output.append(self.formatter.box_top())
            if changes_made:
                output.append(self.formatter.box_line("✅ Setup Complete - Configuration Saved!", align="center"))
            else:
                output.append(self.formatter.box_line("✅ Setup Complete - Configuration Verified!", align="center"))
            output.append(self.formatter.box_bottom())
            output.append("")
            output.append("📝 Quick reference:")
            output.append("   • View all settings: SETUP --show")
            output.append("   • Interactive config: CONFIG")
            output.append("   • Change theme: THEME <name>")
            output.append("   • Edit settings: SETUP <key> <value>")
            output.append("")

            return "\n".join(output)

        except Exception as e:
            return f"❌ Setup wizard error: {e}\n\n💡 Try: SETUP --show to view current settings"

    def _show_all_settings(self):
        """Display all current settings organized by category."""
        output = []
        output.append("⚙️ uDOS SYSTEM SETTINGS")
        output.append("=" * 60)

        # Get user data from ConfigManager (v2.0)
        config = get_config()

        # System Location
        output.append("")
        output.append("🌌 SYSTEM LOCATION:")
        output.append("-" * 40)
        # Read from USER_PROFILE and LOCATION_DATA (authoritative as of v1.2.21)
        galaxy = config.get_user('USER_PROFILE.GALAXY', 'Milky Way')
        planet = config.get_user('USER_PROFILE.PLANET', 'Earth')
        city = config.get_user('USER_PROFILE.LOCATION', 'Not set')  # City name
        tile_code = config.get_user('USER_PROFILE.TILE', 'N/A')  # TILE code
        full_tile = tile_code if tile_code != 'N/A' else 'N/A'

        output.append(f"  Galaxy: {galaxy}")
        output.append(f"  Planet: {planet}")
        output.append(f"  City: {city}")
        output.append(f"  TILE Code: {full_tile}")

        # User Profile
        output.append("")
        output.append("👤 USER PROFILE:")
        output.append("-" * 40)
        user_name = config.get_user('USER_PROFILE.NAME', 'Not set')
        location = config.get_user('USER_PROFILE.LOCATION', 'Not set')
        timezone = config.get_user('USER_PROFILE.TIMEZONE', 'UTC')
        password = config.get_user('USER_PROFILE.PASSWORD', '')
        password_display = '●●●●●●' if password else 'Not set'

        output.append(f"  Username: {user_name}")
        output.append(f"  Password: {password_display}")
        output.append(f"  Location: {location}")
        output.append(f"  Timezone: {timezone}")

        # Theme & Display
        output.append("")
        output.append("🎨 THEME & DISPLAY:")
        output.append("-" * 40)
        theme_name = config.get_env('THEME', 'dungeon')
        color_palette = config.get_user('system_settings.interface.color_palette', 'polaroid')

        output.append(f"  Theme: {theme_name}")
        output.append(f"  Color Palette: {color_palette}")

        if self.viewport:
            output.append(f"  Viewport: {self.viewport.width}×{self.viewport.height}")
            output.append(f"  Device: {getattr(self.viewport, 'device_type', 'TERMINAL')}")

        # Connection & Services
        output.append("")
        output.append("🌐 CONNECTION & SERVICES:")
        output.append("-" * 40)

        # Handle connection object safely (might be boolean or ConnectionMonitor)
        if self.connection and hasattr(self.connection, 'get_mode'):
            connection_mode = self.connection.get_mode()
            internet_available = self.connection.is_online()
        else:
            connection_mode = 'OFFLINE'
            internet_available = False

        output.append(f"  Connection: {connection_mode}")
        output.append(f"  Internet: {'✓ Available' if internet_available else '✗ Offline'}")

        # Check for cloud extension API
        try:
            from extensions.cloud.poke_commands import get_tunnel_status
            tunnel_status = get_tunnel_status()
            if tunnel_status:
                output.append(f"  Cloud Tunnel: {tunnel_status}")
        except:
            pass

        # Development & Tools
        output.append("")
        output.append("🔧 DEVELOPMENT & TOOLS:")
        output.append("-" * 40)
        debug_mode = getattr(self.logger, 'debug_enabled', False) if self.logger else False
        dev_mode = config.get('DEV_MODE', False)
        cli_editor = config.get_env('CLI_EDITOR', 'micro')

        output.append(f"  Debug Mode: {'✓ Enabled' if debug_mode else '✗ Disabled'}")
        output.append(f"  Dev Mode: {'✓ Enabled' if dev_mode else '✗ Disabled'}")
        output.append(f"  CLI Editor: {cli_editor} (fallback: nano)")
        output.append(f"  Auto-save: ✓ Enabled")

        output.append("")
        output.append("=" * 60)
        output.append("💡 Use: SETUP <key> <value> to modify settings")
        output.append("💡 Use: CONFIG for interactive menu")
        output.append("💡 Use: WIZARD to reconfigure system")

        return "\n".join(output)

    def _show_setting(self, key):
        """Show a specific setting value."""
        key_upper = key.upper()

        # Special case: SHOW (from default params) means show all settings
        if key_upper == 'SHOW':
            return self._show_all_settings()

        # Special case: EDIT means launch interactive editor
        elif key_upper == 'EDIT':
            # Delegate to CONFIG handler
            return "💡 Use: CONFIG for interactive menu"

        # Special case: RESET means reset to defaults
        elif key_upper == 'RESET':
            return self._reset_configs()

        # Check different setting categories
        if key_upper == 'THEME':
            if self.theme:
                return f"Current theme: {getattr(self.theme, 'name', 'Default')}"
            else:
                return "Theme not loaded"

        elif key_upper in ['GRID', 'VIEWPORT']:
            if self.viewport:
                return (f"Grid settings:\n"
                       f"  Terminal: {self.viewport.width}×{self.viewport.height}\n"
                       f"  Grid: {getattr(self.viewport, 'grid_width', '?')}×{getattr(self.viewport, 'grid_height', '?')}\n"
                       f"  Device: {getattr(self.viewport, 'device_type', 'UNKNOWN')}")
            else:
                return "Grid not initialized"

        elif key_upper == 'USER':
            # Get user data from ConfigManager (v1.5.0)
            config = get_config()
            user_name = config.get_user('USER_PROFILE.NAME', 'Not set')
            location = config.get_user('USER_PROFILE.LOCATION', 'Not set')
            timezone = config.get_user('USER_PROFILE.TIMEZONE', 'UTC')
            password = config.get_user('USER_PROFILE.PASSWORD', '')

            password_display = '●●●●●●' if password else 'Not set'

            return (f"User settings:\n"
                   f"  Username: {user_name}\n"
                   f"  Password: {password_display}\n"
                   f"  Location: {location}\n"
                   f"  Timezone: {timezone}")

        elif key_upper == 'DEBUG':
            debug_enabled = getattr(self.logger, 'debug_enabled', False) if self.logger else False
            return f"Debug mode: {'Enabled' if debug_enabled else 'Disabled'}"

        else:
            return f"❌ Unknown setting: {key}\n\nAvailable settings: THEME, GRID, USER, DEBUG"

    def _set_setting(self, key, value):
        """Set a specific setting value."""
        key_upper = key.upper()
        value_upper = value.upper()

        if key_upper == 'THEME':
            # Delegate to THEME handler
            return "💡 Use: THEME <name> to change theme"

        elif key_upper == 'DEBUG':
            if value_upper in ['TRUE', 'ON', '1', 'ENABLED']:
                if self.logger:
                    self.logger.debug_enabled = True
                    return "✅ Debug mode enabled"
                else:
                    return "❌ Logger not available"
            elif value_upper in ['FALSE', 'OFF', '0', 'DISABLED']:
                if self.logger:
                    self.logger.debug_enabled = False
                    return "✅ Debug mode disabled"
                else:
                    return "❌ Logger not available"
            else:
                return "❌ Invalid debug value. Use: TRUE/FALSE or ON/OFF"

        else:
            return f"❌ Setting '{key}' cannot be modified directly\n\nModifiable settings: THEME, DEBUG"

    def _load_cities_list(self):
        """Load cities from cities.json for location selection."""
        try:
            from dev.goblin.core.utils.paths import PATHS
            cities_path = PATHS.CORE_DATA_GEOGRAPHY_CITIES
            if cities_path.exists():
                with open(cities_path, 'r') as f:
                    data = json.load(f)
                    return data.get('cities', [])
        except Exception:
            pass
        return None

    def _reset_configs(self):
        """Reset configurations to defaults."""
        # This would require default config templates
        return ("⚠️  CONFIG RESET not implemented\n\n"
               "To reset configurations:\n"
               "1. Backup current configs: CONFIG BACKUP\n"
               "2. Restore from templates in core/data/templates/\n"
               "3. Or reinstall uDOS")
