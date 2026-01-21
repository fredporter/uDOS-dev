"""
uDOS Configuration Manager
Alpha v1.0.0.65

Unified configuration management with TinyCore compliance.
Single source of truth for user/system variables.

Config Hierarchy (highest to lowest priority):
1. Environment variables ($UDOS_*)
2. Session overrides (runtime)
3. User config (memory/config/udos.md)
4. System defaults

Storage:
- User config: memory/config/udos.md (markdown, user-editable)
- Credentials: core/security/.keys/ (encrypted)
- Defaults: core/data/defaults/config.json

Variable Syntax:
- $USER_NAME, $THEME, $MY_VAR_1, etc.
- System vars: $SYS_VERSION, $SYS_DEVICE (read-only)
"""

import os
import re
import json
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, Optional, List
from dataclasses import dataclass, field

from dev.goblin.core.services.logging_manager import get_logger

logger = get_logger("config-manager")


@dataclass
class VariableDefinition:
    """Definition for a configuration variable."""

    name: str
    type: str = "string"  # string, int, bool, list
    default: Any = ""
    description: str = ""
    editable: bool = True
    form_type: str = "text"  # text, select, radio, checkbox
    form_options: List[str] = field(default_factory=list)
    validation: Dict[str, Any] = field(default_factory=dict)


# Built-in variable definitions
BUILTIN_VARIABLES: Dict[str, VariableDefinition] = {
    # Profile
    "USER_NAME": VariableDefinition(
        name="USER_NAME",
        default="survivor",
        description="Your display name",
        form_type="text",
        validation={"minLength": 1, "maxLength": 50},
    ),
    "USER_EMAIL": VariableDefinition(
        name="USER_EMAIL",
        default="",
        description="Email address (optional)",
        form_type="text",
        validation={"pattern": r"^[a-zA-Z0-9._%+-]*@?[a-zA-Z0-9.-]*\.?[a-zA-Z]{0,}$"},
    ),
    "USER_LOCATION": VariableDefinition(
        name="USER_LOCATION", default="", description="Your location", form_type="text"
    ),
    "USER_TIMEZONE": VariableDefinition(
        name="USER_TIMEZONE",
        default="UTC",
        description="Your timezone",
        form_type="select",
        form_options=[
            "UTC",
            "America/New_York",
            "America/Los_Angeles",
            "Europe/London",
            "Europe/Paris",
            "Asia/Tokyo",
            "Australia/Sydney",
        ],
    ),
    # Security
    "AUTH_ENABLED": VariableDefinition(
        name="AUTH_ENABLED",
        type="bool",
        default=False,
        description="Enable authentication",
        form_type="checkbox",
    ),
    "AUTH_METHOD": VariableDefinition(
        name="AUTH_METHOD",
        default="none",
        description="Authentication method",
        form_type="radio",
        form_options=["none", "pin", "password"],
    ),
    "SESSION_TIMEOUT": VariableDefinition(
        name="SESSION_TIMEOUT",
        type="int",
        default=0,
        description="Auto-lock timeout (minutes, 0=never)",
        form_type="text",
        validation={"minimum": 0, "maximum": 1440},
    ),
    # Preferences
    "THEME": VariableDefinition(
        name="THEME",
        default="foundation",
        description="UI theme",
        form_type="select",
        form_options=["foundation", "galaxy", "survival", "retro"],
    ),
    "SOUND_ENABLED": VariableDefinition(
        name="SOUND_ENABLED",
        type="bool",
        default=True,
        description="Enable sound effects",
        form_type="checkbox",
    ),
    "TIPS_ENABLED": VariableDefinition(
        name="TIPS_ENABLED",
        type="bool",
        default=True,
        description="Show helpful tips",
        form_type="checkbox",
    ),
    "AUTO_SAVE": VariableDefinition(
        name="AUTO_SAVE",
        type="bool",
        default=True,
        description="Auto-save documents",
        form_type="checkbox",
    ),
    "COLOR_MODE": VariableDefinition(
        name="COLOR_MODE",
        default="auto",
        description="Color scheme",
        form_type="radio",
        form_options=["light", "dark", "auto"],
    ),
    # Project
    "PROJECT_NAME": VariableDefinition(
        name="PROJECT_NAME", default="", description="Current project name"
    ),
    "PROJECT_DESCRIPTION": VariableDefinition(
        name="PROJECT_DESCRIPTION", default="", description="Project description"
    ),
    "PROJECT_START": VariableDefinition(
        name="PROJECT_START", default="", description="Project start date"
    ),
}


class ConfigManager:
    """
    Unified configuration manager for uDOS.

    Reads config from memory/config/udos.md (markdown format).
    Falls back to defaults if not found.
    """

    # Regex to match $VAR: value lines in markdown
    VAR_PATTERN = re.compile(r"^\$([A-Z_][A-Z0-9_]*)\s*:\s*(.*)$", re.MULTILINE)

    def __init__(self, root_path: Optional[Path] = None):
        """Initialize config manager."""
        self.root_path = root_path or Path(__file__).parent.parent.parent
        self.config_file = self.root_path / "memory" / "config" / "udos.md"
        self.defaults_file = (
            self.root_path / "core" / "data" / "defaults" / "config.json"
        )

        # In-memory caches
        self._user_config: Dict[str, Any] = {}
        self._session_vars: Dict[str, Any] = {}
        self._defaults: Dict[str, Any] = {}
        self._loaded = False

        # Variable definitions
        self.variables = BUILTIN_VARIABLES.copy()

    def load(self) -> bool:
        """Load configuration from files."""
        try:
            # Load defaults
            self._load_defaults()

            # Load user config from udos.md
            self._load_user_config()

            self._loaded = True
            logger.info(f"[LOCAL] Config loaded: {len(self._user_config)} user vars")
            return True

        except Exception as e:
            logger.error(f"[LOCAL] Failed to load config: {e}")
            self._loaded = True  # Mark loaded to use defaults
            return False

    def _load_defaults(self):
        """Load default values from definitions and optional JSON file."""
        # Start with builtin defaults
        self._defaults = {name: var.default for name, var in self.variables.items()}

        # Override with JSON defaults if exists
        if self.defaults_file.exists():
            try:
                with open(self.defaults_file, "r") as f:
                    json_defaults = json.load(f)
                    self._defaults.update(json_defaults)
            except Exception as e:
                logger.warning(f"Could not load defaults JSON: {e}")

    def _load_user_config(self):
        """Load user config from udos.md markdown file."""
        if not self.config_file.exists():
            logger.info(f"[LOCAL] No user config found, using defaults")
            return

        try:
            content = self.config_file.read_text()

            # Parse $VAR: value lines
            for match in self.VAR_PATTERN.finditer(content):
                var_name = match.group(1)
                raw_value = match.group(2).strip()

                # Type conversion based on variable definition
                value = self._parse_value(var_name, raw_value)
                self._user_config[var_name] = value

            logger.debug(f"Loaded {len(self._user_config)} vars from udos.md")

        except Exception as e:
            logger.error(f"Failed to parse udos.md: {e}")

    def _parse_value(self, var_name: str, raw_value: str) -> Any:
        """Parse raw string value to appropriate type."""
        # Get type from definition
        var_def = self.variables.get(var_name)
        var_type = var_def.type if var_def else "string"

        if not raw_value:
            return var_def.default if var_def else ""

        if var_type == "bool":
            return raw_value.lower() in ("true", "yes", "1", "on")
        elif var_type == "int":
            try:
                return int(raw_value)
            except ValueError:
                return var_def.default if var_def else 0
        elif var_type == "list":
            # Comma-separated list
            return [item.strip() for item in raw_value.split(",") if item.strip()]
        else:
            return raw_value

    def get(self, var_name: str, default: Any = None) -> Any:
        """
        Get configuration value with hierarchy resolution.

        Priority: ENV > Session > User Config > Defaults
        """
        if not self._loaded:
            self.load()

        # Remove $ prefix if present
        if var_name.startswith("$"):
            var_name = var_name[1:]

        # 1. Check environment variable
        env_key = f"UDOS_{var_name}"
        if env_key in os.environ:
            return self._parse_value(var_name, os.environ[env_key])

        # 2. Check session overrides
        if var_name in self._session_vars:
            return self._session_vars[var_name]

        # 3. Check user config
        if var_name in self._user_config:
            return self._user_config[var_name]

        # 4. Check defaults
        if var_name in self._defaults:
            return self._defaults[var_name]

        # 5. Return provided default or None
        return default

    def set(self, var_name: str, value: Any, persist: bool = True) -> bool:
        """
        Set configuration value.

        Args:
            var_name: Variable name (with or without $ prefix)
            value: Value to set
            persist: If True, save to udos.md; if False, session-only
        """
        # Remove $ prefix if present
        if var_name.startswith("$"):
            var_name = var_name[1:]

        # Check if variable is editable
        var_def = self.variables.get(var_name)
        if var_def and not var_def.editable:
            logger.warning(f"Cannot modify read-only variable: {var_name}")
            return False

        if persist:
            self._user_config[var_name] = value
            return self._save_user_config()
        else:
            self._session_vars[var_name] = value
            return True

    def _save_user_config(self) -> bool:
        """Save user config back to udos.md."""
        try:
            # Ensure directory exists
            self.config_file.parent.mkdir(parents=True, exist_ok=True)

            # If file exists, update in place; otherwise create new
            if self.config_file.exists():
                content = self.config_file.read_text()
                content = self._update_markdown_vars(content)
            else:
                content = self._generate_new_config()

            self.config_file.write_text(content)
            logger.info(f"[LOCAL] Saved config to {self.config_file}")
            return True

        except Exception as e:
            logger.error(f"Failed to save config: {e}")
            return False

    def _update_markdown_vars(self, content: str) -> str:
        """Update variable values in existing markdown content."""
        for var_name, value in self._user_config.items():
            # Convert value to string
            if isinstance(value, bool):
                str_value = "true" if value else "false"
            elif isinstance(value, list):
                str_value = ", ".join(str(v) for v in value)
            else:
                str_value = str(value)

            # Pattern to match this specific variable
            pattern = re.compile(rf"^\$({re.escape(var_name)})\s*:\s*.*$", re.MULTILINE)
            replacement = f"${var_name}: {str_value}"

            if pattern.search(content):
                content = pattern.sub(replacement, content)
            else:
                # Variable not in file - add to Custom Variables section
                custom_marker = "## Custom Variables"
                if custom_marker in content:
                    content = content.replace(
                        custom_marker, f"{custom_marker}\n\n${var_name}: {str_value}"
                    )

        # Update timestamp
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        content = re.sub(
            r"\*Last modified:.*\*", f"*Last modified: {timestamp}*", content
        )

        return content

    def _generate_new_config(self) -> str:
        """Generate new udos.md from template."""
        template = self._get_template()

        # Replace variable placeholders with values
        for var_name, value in self._user_config.items():
            if isinstance(value, bool):
                str_value = "true" if value else "false"
            elif isinstance(value, list):
                str_value = ", ".join(str(v) for v in value)
            else:
                str_value = str(value)

            template = re.sub(
                rf"\${re.escape(var_name)}:\s*\S*",
                f"${var_name}: {str_value}",
                template,
            )

        return template

    def _get_template(self) -> str:
        """Get the udos.md template content."""
        return """# uDOS Configuration

Your personal settings file. Edit this directly or use `STORY SETUP`.

---

## Profile

$USER_NAME: survivor
$USER_EMAIL: 
$USER_LOCATION: 
$USER_TIMEZONE: UTC

## Security

$AUTH_ENABLED: false
$AUTH_METHOD: none
$SESSION_TIMEOUT: 0

## Preferences

$THEME: foundation
$SOUND_ENABLED: true
$TIPS_ENABLED: true
$AUTO_SAVE: true
$COLOR_MODE: auto

## Project

$PROJECT_NAME: 
$PROJECT_DESCRIPTION: 
$PROJECT_START: 

## Custom Variables

$MY_VAR_1: 
$MY_VAR_2: 
$MY_VAR_3: 

---

*Last modified: {timestamp}*
*uDOS Alpha v1.0.0.65*
""".format(
            timestamp=datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        )

    def get_all(self) -> Dict[str, Any]:
        """Get all configuration values."""
        if not self._loaded:
            self.load()

        result = {}

        # Start with defaults
        result.update(self._defaults)

        # Override with user config
        result.update(self._user_config)

        # Override with session vars
        result.update(self._session_vars)

        # Add system variables
        result["SYS_VERSION"] = self._get_system_version()
        result["SYS_DEVICE"] = (
            os.uname().nodename if hasattr(os, "uname") else "unknown"
        )
        result["SYS_MODE"] = os.environ.get("UDOS_MODE", "PROD")
        result["SYS_REALM"] = os.environ.get("UDOS_REALM", "USER_MESH")
        result["SYS_TIMESTAMP"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        return result

    def _get_system_version(self) -> str:
        """Get uDOS version from version.json."""
        version_file = self.root_path / "core" / "version.json"
        try:
            if version_file.exists():
                with open(version_file) as f:
                    data = json.load(f)
                    return data.get("version", "1.0.0.0")
        except Exception:
            pass
        return "1.0.0.0"

    def get_form_definition(self, section: str = "all") -> Dict[str, Any]:
        """
        Get form definition for variables (for gtx-form integration).

        Args:
            section: "profile", "security", "preferences", "project", or "all"

        Returns:
            Form definition compatible with gtx-form
        """
        sections = {
            "profile": ["USER_NAME", "USER_EMAIL", "USER_LOCATION", "USER_TIMEZONE"],
            "security": ["AUTH_ENABLED", "AUTH_METHOD", "SESSION_TIMEOUT"],
            "preferences": [
                "THEME",
                "SOUND_ENABLED",
                "TIPS_ENABLED",
                "AUTO_SAVE",
                "COLOR_MODE",
            ],
            "project": ["PROJECT_NAME", "PROJECT_DESCRIPTION", "PROJECT_START"],
        }

        if section == "all":
            var_names = []
            for names in sections.values():
                var_names.extend(names)
        else:
            var_names = sections.get(section, [])

        form_fields = []
        for var_name in var_names:
            var_def = self.variables.get(var_name)
            if not var_def:
                continue

            form_fields.append(
                {
                    "name": var_name,
                    "type": var_def.form_type,
                    "label": var_def.description,
                    "value": self.get(var_name),
                    "options": var_def.form_options if var_def.form_options else None,
                    "validation": var_def.validation if var_def.validation else None,
                }
            )

        return {"section": section, "fields": form_fields}

    def define_custom_variable(
        self,
        name: str,
        var_type: str = "string",
        default: Any = "",
        description: str = "",
    ) -> bool:
        """
        Define a new custom variable.

        Args:
            name: Variable name (will be prefixed with MY_ if not already)
            var_type: "string", "int", "bool", "list"
            default: Default value
            description: Human-readable description
        """
        # Ensure MY_ prefix for user variables
        if not name.startswith("MY_") and not name.startswith("$MY_"):
            name = f"MY_{name}"

        name = name.lstrip("$").upper()

        self.variables[name] = VariableDefinition(
            name=name,
            type=var_type,
            default=default,
            description=description,
            editable=True,
            form_type="text",
        )

        logger.info(f"[LOCAL] Defined custom variable: ${name}")
        return True

    def resolve_template(self, template: str) -> str:
        """
        Resolve $VAR references in a template string.

        Example: "Hello $USER_NAME!" → "Hello survivor!"
        """

        def replace_var(match):
            var_name = match.group(1)
            return str(self.get(var_name, f"${var_name}"))

        return re.sub(r"\$([A-Z_][A-Z0-9_]*)", replace_var, template)


# Global config instance
_config: Optional[ConfigManager] = None


def get_config() -> ConfigManager:
    """Get the global ConfigManager instance."""
    global _config
    if _config is None:
        _config = ConfigManager()
        _config.load()
    return _config


def get_var(var_name: str, default: Any = None) -> Any:
    """Convenience function to get a config variable."""
    return get_config().get(var_name, default)


def set_var(var_name: str, value: Any, persist: bool = True) -> bool:
    """Convenience function to set a config variable."""
    return get_config().set(var_name, value, persist)
