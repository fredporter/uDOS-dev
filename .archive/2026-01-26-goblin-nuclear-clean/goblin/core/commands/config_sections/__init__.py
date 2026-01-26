"""
Configuration Sections Package

Modular configuration management sections for uDOS CONFIG command.
Each section handles a specific configuration domain.
"""

from .api_keys_section import APIKeysSection
from .user_profile_section import UserProfileSection
from .system_settings_section import SystemSettingsSection
from .task_settings_section import TaskSettingsSection
from .filename_settings_section import FilenameSettingsSection
from .version_control_section import VersionControlSection
from .input_device_section import InputDeviceSection
from .upy_settings_section import UPYSettingsSection
from .gameplay_settings_section import GameplaySettingsSection

__all__ = [
    'APIKeysSection',
    'UserProfileSection',
    'SystemSettingsSection',
    'TaskSettingsSection',
    'FilenameSettingsSection',
    'VersionControlSection',
    'InputDeviceSection',
    'UPYSettingsSection',
    'GameplaySettingsSection',
]
