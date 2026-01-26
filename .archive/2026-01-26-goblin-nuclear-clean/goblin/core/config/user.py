"""
User Directory and Configuration Management

Initializes ~/.udos/ structure with correct permissions.
"""

from pathlib import Path
import json
import os
import stat
from typing import Dict, Any

from .paths import get_user_path, get_config_path, get_credentials_path


def init_user_directory() -> None:
    """
    Initialize ~/.udos/ directory structure with correct permissions.

    Creates:
        ~/.udos/config/          (700) - User configuration
        ~/.udos/memory/          (755) - User workspace
        ~/.udos/memory/sandbox/  (755) - User scripts/extensions
        ~/.udos/memory/logs/     (755) - Log files
        ~/.udos/memory/.cache/   (755) - Cache data
        ~/.udos/memory/.backups/ (755) - Local backups
        ~/.udos/.credentials/    (700) - Encrypted credentials

    Safe to call multiple times.
    """
    udos_home = Path.home() / ".udos"

    # Create directory structure with permissions
    dirs_with_perms = {
        # Config (private)
        "config": 0o700,
        # Workspace (standard)
        "memory": 0o755,
        "memory/sandbox": 0o755,
        "memory/sandbox/scripts": 0o755,
        "memory/sandbox/workflows": 0o755,
        "memory/sandbox/extensions": 0o755,
        "memory/knowledge": 0o755,
        "memory/knowledge/private": 0o755,
        "memory/knowledge/p2p": 0o755,
        "memory/knowledge/groups": 0o755,
        "memory/logs": 0o755,
        "memory/.cache": 0o755,
        "memory/.backups": 0o755,
        # Credentials (strict)
        ".credentials": 0o700,
    }

    for subdir, mode in dirs_with_perms.items():
        path = udos_home / subdir
        path.mkdir(mode=mode, parents=True, exist_ok=True)

        # Ensure permissions are correct even if dir existed
        os.chmod(path, mode)

    # Create default config files if they don't exist
    # Get username, handling non-interactive environments (e.g., GitHub Actions)
    try:
        username = os.getlogin() if hasattr(os, "getlogin") else "user"
    except (OSError, AttributeError):
        # Fallback for non-interactive environments
        username = os.environ.get("USER", os.environ.get("USERNAME", "user"))
    
    default_configs = {
        "config/user.json": {
            "username": username,
            "device_name": os.uname().nodename if hasattr(os, "uname") else "device",
            "created": None,  # Will be set by system
            "version": "1.0.0.0",
        },
        "config/devices.json": {
            "paired_devices": [],
            "trusted_devices": [],
        },
        "config/extensions.json": {
            "enabled_extensions": [],
            "extension_settings": {},
        },
        "config/permissions.json": {
            "granted_permissions": {},
        },
    }

    for config_file, default_content in default_configs.items():
        config_path = udos_home / config_file

        if not config_path.exists():
            config_path.write_text(json.dumps(default_content, indent=2))
            os.chmod(config_path, 0o600)  # Private config files


def get_user_config() -> Dict[str, Any]:
    """
    Load user configuration.

    Returns:
        User configuration dictionary
    """
    config_file = get_config_path("user.json")

    if not config_file.exists():
        # Initialize if needed
        init_user_directory()

    try:
        return json.loads(config_file.read_text())
    except (json.JSONDecodeError, FileNotFoundError):
        # Return default config
        return {
            "username": "user",
            "device_name": "device",
            "version": "1.0.0.0",
        }


def save_user_config(config: Dict[str, Any]) -> None:
    """
    Save user configuration.

    Args:
        config: Configuration dictionary
    """
    config_file = get_config_path("user.json")

    # Write with restricted permissions
    config_file.write_text(json.dumps(config, indent=2))
    os.chmod(config_file, 0o600)


def get_device_config() -> Dict[str, Any]:
    """Load paired devices configuration."""
    config_file = get_config_path("devices.json")

    if not config_file.exists():
        init_user_directory()

    try:
        return json.loads(config_file.read_text())
    except (json.JSONDecodeError, FileNotFoundError):
        return {"paired_devices": [], "trusted_devices": []}


def save_device_config(config: Dict[str, Any]) -> None:
    """Save device configuration."""
    config_file = get_config_path("devices.json")
    config_file.write_text(json.dumps(config, indent=2))
    os.chmod(config_file, 0o600)
