"""
User Configuration Manager for uDOS v1.0.0.39+

TinyCore-compliant user config with schema validation.
Single source of truth for TUI and Tauri user profiles.

Design Philosophy:
- Use TinyCore-compliant paths everywhere (not just on TC)
- Workspace-relative paths work on all platforms
- No platform detection needed
- Test on macOS = test for TinyCore

Features:
- JSON Schema validation
- Graceful migration from old formats
- Lazy loading (no circular imports)
- Same path structure everywhere

Author: GitHub Copilot
Version: 1.0.0.39
Date: 2026-01-05
"""

import json
import os
import time
from pathlib import Path
from typing import Dict, Any, Optional
from datetime import datetime


class UserConfigManager:
    """
    Manages user configuration with schema validation.

    Uses TinyCore-compliant paths everywhere (workspace-relative).
    No platform detection - same structure on all systems.

    Handles:
    - Config file location (workspace-relative)
    - Schema validation
    - Migration from old formats
    - Default value generation
    """

    SCHEMA_VERSION = "1.0.0"

    def __init__(self, config_path: Optional[Path] = None):
        """
        Initialize user config manager.

        Args:
            config_path: Optional override for config file location
        """
        if config_path:
            self.config_path = Path(config_path)
        else:
            self.config_path = self._detect_config_path()

        self._schema = None
        self._config = None

    @property
    def schema(self) -> Dict[str, Any]:
        """Lazy-load JSON schema."""
        if self._schema is None:
            schema_path = Path(__file__).parent.parent / "config" / "user_schema.json"
            if schema_path.exists():
                with open(schema_path) as f:
                    self._schema = json.load(f)
            else:
                # Fallback: minimal schema if file missing
                self._schema = {"type": "object", "properties": {}, "required": []}
        return self._schema

    def _detect_config_path(self) -> Path:
        """
        Get config path using workspace-relative structure.

        Uses TinyCore-compliant paths everywhere:
        - Development/macOS/Linux: ./memory/bank/user/user.json
        - TinyCore deployment: /opt/udos/memory/bank/user/user.json

        Same structure, different root. No detection needed.

        Returns:
            Path to user config file
        """
        from dev.goblin.core.utils.paths import PATHS

        base = PATHS.MEMORY_BANK / "user"
        base.mkdir(parents=True, exist_ok=True)
        return base / "user.json"

    def load(self) -> Dict[str, Any]:
        """
        Load user config with validation and migration.

        Returns:
            User config dictionary
        """
        if self._config is not None:
            return self._config

        if not self.config_path.exists():
            # No config exists - return defaults
            self._config = self._get_defaults()
            return self._config

        try:
            with open(self.config_path) as f:
                raw_config = json.load(f)

            # Migrate from old format if needed
            self._config = self._migrate_config(raw_config)

            # Validate against schema
            self._validate_config(self._config)

            return self._config

        except (json.JSONDecodeError, FileNotFoundError) as e:
            print(f"⚠️  Config load error: {e}")
            self._config = self._get_defaults()
            return self._config

    def save(self, config: Optional[Dict[str, Any]] = None) -> bool:
        """
        Save user config to file.

        Args:
            config: Config dict to save (uses cached if None)

        Returns:
            True if saved successfully
        """
        if config is not None:
            self._config = config

        if self._config is None:
            return False

        try:
            # Validate before saving
            self._validate_config(self._config)

            # Ensure directory exists
            self.config_path.parent.mkdir(parents=True, exist_ok=True)

            # Write with pretty formatting
            with open(self.config_path, "w") as f:
                json.dump(self._config, f, indent=2)

            return True

        except Exception as e:
            print(f"❌ Config save error: {e}")
            return False

    def update(self, updates: Dict[str, Any]) -> bool:
        """
        Update config fields (deep merge).

        Args:
            updates: Dictionary of updates to apply

        Returns:
            True if updated successfully
        """
        if self._config is None:
            self.load()

        self._deep_merge(self._config, updates)
        return self.save()

    def get(self, key: str, default: Any = None) -> Any:
        """
        Get config value by dot-notation key.

        Args:
            key: Dot-notation key (e.g., 'user_profile.username')
            default: Default value if key not found

        Returns:
            Config value or default
        """
        if self._config is None:
            self.load()

        keys = key.split(".")
        value = self._config

        for k in keys:
            if isinstance(value, dict) and k in value:
                value = value[k]
            else:
                return default

        return value

    def _get_defaults(self) -> Dict[str, Any]:
        """
        Generate default config from schema.

        Returns:
            Default config dictionary
        """
        # Auto-detect timezone and city
        timezone, city = self._detect_timezone()

        return {
            "version": self.SCHEMA_VERSION,
            "user_profile": {
                "username": os.getenv("USER", "user"),
                "timezone": timezone,
                "password_hash": "",
                "preferred_mode": "standard",
            },
            "project": {"name": "", "description": "", "start_date": ""},
            "location_data": {
                "city": city,
                "country": "",
                "latitude": 0,
                "longitude": 0,
                "tile_code": "",
                "map_position": {"x": 0, "y": 0},
                "current_layer": "surface",
            },
            "spatial_data": {
                "planet": "Earth",
                "planet_id": "earth",
                "galaxy": "Milky Way",
                "galaxy_id": "milky_way",
            },
            "session_data": {
                "current_session": f"session_{int(time.time())}",
                "session_count": 0,
                "last_login": datetime.now().isoformat(),
                "viewport": {},
            },
            "system_settings": {
                "interface": {
                    "theme": "dungeon",
                    "show_hints": True,
                    "animation_speed": "normal",
                },
                "workspace_preference": "memory",
                "auto_save": True,
                "backup_on_edit": False,
            },
        }

    def _migrate_config(self, old_config: Dict[str, Any]) -> Dict[str, Any]:
        """
        Migrate old config format to new schema.

        Args:
            old_config: Config in old format

        Returns:
            Config in new schema format
        """
        # Check if already in new format
        if "version" in old_config and old_config["version"] == self.SCHEMA_VERSION:
            return old_config

        # Start with defaults
        new_config = self._get_defaults()

        # Migrate USER_PROFILE → user_profile
        if "USER_PROFILE" in old_config:
            up = old_config["USER_PROFILE"]
            new_config["user_profile"]["username"] = up.get("NAME", "user")
            new_config["user_profile"]["timezone"] = up.get("TIMEZONE", "UTC")
            new_config["user_profile"]["preferred_mode"] = up.get(
                "PREFERRED_MODE", "standard"
            ).lower()

        # Migrate PROJECT
        if "PROJECT" in old_config:
            proj = old_config["PROJECT"]
            new_config["project"]["name"] = proj.get("NAME", "")
            new_config["project"]["description"] = proj.get("DESCRIPTION", "")
            new_config["project"]["start_date"] = proj.get("START_DATE", "")

        # Migrate LOCATION_DATA → location_data
        if "LOCATION_DATA" in old_config:
            loc = old_config["LOCATION_DATA"]
            new_config["location_data"]["city"] = loc.get("CITY", "")
            new_config["location_data"]["country"] = loc.get("COUNTRY", "")
            new_config["location_data"]["latitude"] = loc.get("LATITUDE", 0)
            new_config["location_data"]["longitude"] = loc.get("LONGITUDE", 0)
            new_config["location_data"]["tile_code"] = loc.get("TILE_CODE", "")
            new_config["location_data"]["map_position"] = loc.get(
                "MAP_POSITION", {"x": 0, "y": 0}
            )
            new_config["location_data"]["current_layer"] = loc.get(
                "CURRENT_LAYER", "surface"
            ).lower()

        # Migrate SPATIAL_DATA → spatial_data
        if "SPATIAL_DATA" in old_config:
            spatial = old_config["SPATIAL_DATA"]
            new_config["spatial_data"]["planet"] = spatial.get("PLANET", "Earth")
            new_config["spatial_data"]["planet_id"] = spatial.get("PLANET_ID", "earth")
            new_config["spatial_data"]["galaxy"] = spatial.get("GALAXY", "Milky Way")
            new_config["spatial_data"]["galaxy_id"] = spatial.get(
                "GALAXY_ID", "milky_way"
            )

        # Migrate SESSION_DATA → session_data
        if "SESSION_DATA" in old_config:
            sess = old_config["SESSION_DATA"]
            new_config["session_data"]["current_session"] = sess.get(
                "CURRENT_SESSION", f"session_{int(time.time())}"
            )
            new_config["session_data"]["session_count"] = sess.get("SESSION_COUNT", 0)
            new_config["session_data"]["last_login"] = sess.get(
                "LAST_LOGIN", datetime.now().isoformat()
            )
            new_config["session_data"]["viewport"] = sess.get("VIEWPORT", {})

        # Migrate system_settings
        if "system_settings" in old_config:
            sys_settings = old_config["system_settings"]
            if "interface" in sys_settings:
                new_config["system_settings"]["interface"]["theme"] = sys_settings[
                    "interface"
                ].get("theme", "dungeon")
            if "workspace_preference" in sys_settings:
                new_config["system_settings"]["workspace_preference"] = sys_settings[
                    "workspace_preference"
                ]

        return new_config

    def _validate_config(self, config: Dict[str, Any]) -> bool:
        """
        Validate config against schema.

        Args:
            config: Config to validate

        Returns:
            True if valid

        Raises:
            ValueError: If validation fails
        """
        # Basic validation (full jsonschema validation would require dependency)
        required = [
            "version",
            "user_profile",
            "location_data",
            "spatial_data",
            "system_settings",
        ]
        for key in required:
            if key not in config:
                raise ValueError(f"Missing required field: {key}")

        # Check user_profile required fields
        if "username" not in config["user_profile"]:
            raise ValueError("Missing user_profile.username")
        if "timezone" not in config["user_profile"]:
            raise ValueError("Missing user_profile.timezone")

        return True

    def _deep_merge(self, base: Dict[str, Any], updates: Dict[str, Any]) -> None:
        """
        Deep merge updates into base dictionary (in-place).

        Args:
            base: Base dictionary to merge into
            updates: Updates to apply
        """
        for key, value in updates.items():
            if key in base and isinstance(base[key], dict) and isinstance(value, dict):
                self._deep_merge(base[key], value)
            else:
                base[key] = value

    def _detect_timezone(self) -> tuple:
        """
        Detect system timezone and city.

        Returns:
            (timezone, city) tuple
        """
        try:
            from dev.goblin.core.utils.system_info import get_system_timezone

            return get_system_timezone()
        except:
            return ("UTC", "")


# Singleton instance
_user_config_manager = None


def get_user_config() -> UserConfigManager:
    """
    Get singleton UserConfigManager instance.

    Returns:
        UserConfigManager instance
    """
    global _user_config_manager
    if _user_config_manager is None:
        _user_config_manager = UserConfigManager()
    return _user_config_manager
