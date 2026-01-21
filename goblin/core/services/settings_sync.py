"""
uDOS Unified Settings Service
Synchronizes configuration between TUI, Tauri, and API environments

Version: 1.2.30
Date: 2025-12-27
"""

import json
import os
from pathlib import Path
from typing import Dict, Any, Optional, List
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


class SettingsSync:
    """
    Unified settings manager that synchronizes between:
    - core/config.py (.env + user.json)
    - extensions/tauri/config/user-preferences.json
    - API server runtime state
    """

    def __init__(self, project_root: Optional[Path] = None):
        """Initialize settings sync service."""
        if project_root is None:
            project_root = Path(__file__).parent.parent.parent

        self.project_root = project_root

        # Core configuration paths
        self.core_user_json = project_root / "memory" / "bank" / "user" / "user.json"
        self.core_env_file = project_root / ".env"

        # Tauri configuration paths (uCode Markdown App)
        self.tauri_prefs_json = (
            project_root / "app" / "config" / "user-preferences.json"
        )

        # Runtime state
        self._settings_cache: Dict[str, Any] = {}
        self._last_sync: Optional[datetime] = None

    # =========================================================================
    # UNIFIED SETTINGS MODEL
    # =========================================================================

    def get_unified_settings(self) -> Dict[str, Any]:
        """
        Get unified settings from all sources.

        Returns:
            Dict with structure:
            {
                "user": {...},           # User profile (name, email, location)
                "system": {...},         # System config (.env)
                "ui": {...},             # UI preferences (theme, scale, input)
                "workspace": {...},      # File/folder settings
                "extensions": {...}      # Extension-specific settings
            }
        """
        settings = {
            "user": self._load_user_profile(),
            "system": self._load_system_config(),
            "ui": self._load_ui_preferences(),
            "workspace": self._load_workspace_config(),
            "extensions": self._load_extension_config(),
        }

        self._settings_cache = settings
        self._last_sync = datetime.now()

        return settings

    def _load_user_profile(self) -> Dict[str, Any]:
        """Load user profile from memory/bank/user/user.json."""
        if not self.core_user_json.exists():
            return self._get_default_user_profile()

        try:
            with open(self.core_user_json, "r") as f:
                data = json.load(f)
                # Extract user profile fields
                return {
                    "name": data.get("user", {}).get("name", "User"),
                    "email": data.get("variables", {})
                    .get("USER-EMAIL", {})
                    .get("default", ""),
                    "location": data.get("variables", {})
                    .get("USER-LOCATION", {})
                    .get("default", "AA340"),
                    "skill_level": data.get("variables", {})
                    .get("USER-SKILL-LEVEL", {})
                    .get("default", "beginner"),
                    "preferences": data.get("variables", {})
                    .get("USER-PREFERENCES", {})
                    .get("default", {}),
                }
        except Exception as e:
            logger.error(f"Failed to load user profile: {e}")
            return self._get_default_user_profile()

    def _load_system_config(self) -> Dict[str, Any]:
        """Load system configuration from .env."""
        if not self.core_env_file.exists():
            return self._get_default_system_config()

        try:
            from dotenv import dotenv_values

            env_vars = dotenv_values(self.core_env_file)

            return {
                "api_keys": {
                    "gemini": bool(env_vars.get("GEMINI_API_KEY")),
                    "openai": bool(env_vars.get("OPENAI_API_KEY")),
                    "anthropic": bool(env_vars.get("ANTHROPIC_API_KEY")),
                    "mistral": bool(env_vars.get("MISTRAL_API_KEY")),
                },
                "installation_id": env_vars.get("UDOS_INSTALLATION_ID", ""),
                "default_workspace": env_vars.get("DEFAULT_WORKSPACE", "knowledge"),
                "theme": env_vars.get("THEME", "system7"),
                "editor": {
                    "cli": env_vars.get("CLI_EDITOR", "micro"),
                    "web": env_vars.get("WEB_EDITOR", "typo"),
                },
                "server": {
                    "auto_start": env_vars.get("AUTO_START_SERVER", "false").lower()
                    == "true",
                    "port": int(env_vars.get("HTTP_SERVER_PORT", "5001")),
                },
            }
        except Exception as e:
            logger.error(f"Failed to load system config: {e}")
            return self._get_default_system_config()

    def _load_ui_preferences(self) -> Dict[str, Any]:
        """Load UI preferences from Tauri config."""
        if not self.tauri_prefs_json.exists():
            return self._get_default_ui_preferences()

        try:
            with open(self.tauri_prefs_json, "r") as f:
                tauri_prefs = json.load(f)

                return {
                    "theme": tauri_prefs.get("global", {}).get("theme", "system7"),
                    "scale": tauri_prefs.get("global", {}).get("scale", "2x"),
                    "toasts": {
                        "enabled": tauri_prefs.get("global", {}).get(
                            "showToasts", True
                        ),
                        "position": tauri_prefs.get("global", {}).get(
                            "toastPosition", "bottom-left"
                        ),
                    },
                    "input": tauri_prefs.get("input", {}),
                    "overlays": tauri_prefs.get("overlays", {}),
                    "fonts": tauri_prefs.get("fonts", {}),
                    "windows": tauri_prefs.get("windows", {}),
                }
        except Exception as e:
            logger.error(f"Failed to load UI preferences: {e}")
            return self._get_default_ui_preferences()

    def _load_workspace_config(self) -> Dict[str, Any]:
        """Load workspace/file picker configuration."""
        tauri_prefs = {}
        if self.tauri_prefs_json.exists():
            try:
                with open(self.tauri_prefs_json, "r") as f:
                    tauri_prefs = json.load(f)
            except Exception:
                pass

        return {
            "default_workspace": tauri_prefs.get("filepicker", {}).get(
                "defaultWorkspace", "knowledge"
            ),
            "recent_files_max": tauri_prefs.get("filepicker", {}).get(
                "recentFilesMax", 10
            ),
            "filter_extensions": tauri_prefs.get("filepicker", {}).get(
                "filterExtensions", [".md", ".json", ".upy"]
            ),
            "show_hidden": tauri_prefs.get("filepicker", {}).get("showHidden", False),
            "sort_by": tauri_prefs.get("filepicker", {}).get("sortBy", "name"),
        }

    def _load_extension_config(self) -> Dict[str, Any]:
        """Load extension-specific configuration."""
        return {
            "tauri": {"enabled": True, "port": 3000, "auto_launch": False},
            "api": {"enabled": True, "port": 5001, "cors_enabled": True},
            "web": {
                "dashboard": {"enabled": True, "port": 5050},
                "teletext": {"enabled": True, "port": 5051},
            },
            "cloud": {"enabled": False, "sync_interval": 300},
            "meshcore": {"enabled": False, "discovery": True},
        }

    # =========================================================================
    # DEFAULT SETTINGS
    # =========================================================================

    def _get_default_user_profile(self) -> Dict[str, Any]:
        """Get default user profile."""
        return {
            "name": "User",
            "email": "",
            "location": "AA340",  # Sydney default
            "skill_level": "beginner",
            "preferences": {"auto_save": True, "show_tips": True, "color_mode": "auto"},
        }

    def _get_default_system_config(self) -> Dict[str, Any]:
        """Get default system configuration."""
        return {
            "api_keys": {
                "gemini": False,
                "openai": False,
                "anthropic": False,
                "mistral": False,
            },
            "installation_id": "",
            "default_workspace": "knowledge",
            "theme": "system7",
            "editor": {"cli": "micro", "web": "typo"},
            "server": {"auto_start": False, "port": 5001},
        }

    def _get_default_ui_preferences(self) -> Dict[str, Any]:
        """Get default UI preferences."""
        return {
            "theme": "system7",
            "scale": "2x",
            "toasts": {"enabled": True, "position": "bottom-left"},
            "input": {
                "autoSelectByMode": True,
                "defaultVariant": "command",
                "historySize": 50,
                "predictionsEnabled": True,
            },
            "overlays": {},
            "fonts": {},
            "windows": {},
        }

    # =========================================================================
    # SAVE & SYNC
    # =========================================================================

    def save_settings(self, settings: Dict[str, Any]) -> bool:
        """
        Save unified settings to all configuration files.

        Args:
            settings: Unified settings dict

        Returns:
            True if all saves succeeded
        """
        success = True

        # Save user profile
        if not self._save_user_profile(settings.get("user", {})):
            success = False

        # Save system config (.env)
        if not self._save_system_config(settings.get("system", {})):
            success = False

        # Save UI preferences (Tauri)
        if not self._save_ui_preferences(settings.get("ui", {})):
            success = False

        # Update cache
        if success:
            self._settings_cache = settings
            self._last_sync = datetime.now()

        return success

    def _save_user_profile(self, user_data: Dict[str, Any]) -> bool:
        """Save user profile to core user.json."""
        try:
            # Load existing user.json
            if self.core_user_json.exists():
                with open(self.core_user_json, "r") as f:
                    data = json.load(f)
            else:
                data = {"variables": {}}

            # Update user fields
            if "user" not in data:
                data["user"] = {}
            data["user"]["name"] = user_data.get("name", "User")

            # Update variables
            vars_dict = data.get("variables", {})
            if "USER-EMAIL" in vars_dict:
                vars_dict["USER-EMAIL"]["default"] = user_data.get("email", "")
            if "USER-LOCATION" in vars_dict:
                vars_dict["USER-LOCATION"]["default"] = user_data.get(
                    "location", "AA340"
                )
            if "USER-SKILL-LEVEL" in vars_dict:
                vars_dict["USER-SKILL-LEVEL"]["default"] = user_data.get(
                    "skill_level", "beginner"
                )

            # Save
            self.core_user_json.parent.mkdir(parents=True, exist_ok=True)
            with open(self.core_user_json, "w") as f:
                json.dump(data, f, indent=2)

            return True
        except Exception as e:
            logger.error(f"Failed to save user profile: {e}")
            return False

    def _save_system_config(self, system_data: Dict[str, Any]) -> bool:
        """Save system config to .env (non-sensitive fields only)."""
        try:
            # Read existing .env
            env_lines = []
            if self.core_env_file.exists():
                with open(self.core_env_file, "r") as f:
                    env_lines = f.readlines()

            # Update specific fields (not API keys - those are sensitive)
            updates = {
                "DEFAULT_WORKSPACE": system_data.get("default_workspace", "knowledge"),
                "THEME": system_data.get("theme", "system7"),
                "CLI_EDITOR": system_data.get("editor", {}).get("cli", "micro"),
                "WEB_EDITOR": system_data.get("editor", {}).get("web", "typo"),
                "HTTP_SERVER_PORT": str(
                    system_data.get("server", {}).get("port", 5001)
                ),
                "AUTO_START_SERVER": (
                    "true"
                    if system_data.get("server", {}).get("auto_start")
                    else "false"
                ),
            }

            # Update or append
            for key, value in updates.items():
                found = False
                for i, line in enumerate(env_lines):
                    if line.startswith(f"{key}="):
                        env_lines[i] = f"{key}={value}\n"
                        found = True
                        break
                if not found:
                    env_lines.append(f"{key}={value}\n")

            # Save
            with open(self.core_env_file, "w") as f:
                f.writelines(env_lines)

            return True
        except Exception as e:
            logger.error(f"Failed to save system config: {e}")
            return False

    def _save_ui_preferences(self, ui_data: Dict[str, Any]) -> bool:
        """Save UI preferences to Tauri config."""
        try:
            # Load existing Tauri prefs
            if self.tauri_prefs_json.exists():
                with open(self.tauri_prefs_json, "r") as f:
                    tauri_prefs = json.load(f)
            else:
                tauri_prefs = {"version": "1.0.0"}

            # Update fields
            tauri_prefs["global"] = {
                "theme": ui_data.get("theme", "system7"),
                "scale": ui_data.get("scale", "2x"),
                "showToasts": ui_data.get("toasts", {}).get("enabled", True),
                "toastPosition": ui_data.get("toasts", {}).get(
                    "position", "bottom-left"
                ),
            }

            if "input" in ui_data:
                tauri_prefs["input"] = ui_data["input"]
            if "overlays" in ui_data:
                tauri_prefs["overlays"] = ui_data["overlays"]
            if "fonts" in ui_data:
                tauri_prefs["fonts"] = ui_data["fonts"]
            if "windows" in ui_data:
                tauri_prefs["windows"] = ui_data["windows"]

            # Save
            self.tauri_prefs_json.parent.mkdir(parents=True, exist_ok=True)
            with open(self.tauri_prefs_json, "w") as f:
                json.dump(tauri_prefs, f, indent=2)

            return True
        except Exception as e:
            logger.error(f"Failed to save UI preferences: {e}")
            return False

    # =========================================================================
    # CONVENIENCE METHODS
    # =========================================================================

    def get_user_name(self) -> str:
        """Get user name from settings."""
        settings = self.get_unified_settings()
        return settings["user"]["name"]

    def get_user_location(self) -> str:
        """Get user location TILE code."""
        settings = self.get_unified_settings()
        return settings["user"]["location"]

    def get_theme(self) -> str:
        """Get active theme."""
        settings = self.get_unified_settings()
        return settings["ui"]["theme"]

    def get_workspace_root(self) -> str:
        """Get default workspace folder."""
        settings = self.get_unified_settings()
        return settings["workspace"]["default_workspace"]

    def is_api_key_configured(self, provider: str) -> bool:
        """Check if an API key is configured."""
        settings = self.get_unified_settings()
        return settings["system"]["api_keys"].get(provider, False)


# Singleton instance
_settings_sync: Optional[SettingsSync] = None


def get_settings_sync(project_root: Optional[Path] = None) -> SettingsSync:
    """Get singleton SettingsSync instance."""
    global _settings_sync
    if _settings_sync is None:
        _settings_sync = SettingsSync(project_root)
    return _settings_sync
