"""
uDOS Configuration Management

Provides FHS-compliant path helpers and configuration utilities.

Note: The main Config class is in core/config.py (module) not this package.
To avoid circular imports, import Config directly:
    from dev.goblin.core.config import Config  # This works via importlib magic below
"""

from .paths import (
    get_system_path,
    get_user_path,
    get_config_path,
    get_credentials_path,
    get_temp_path,
    is_tinycore,
    get_tinycore_user_home,
    setup_tinycore_user,
    get_platform_info,
)
from .user import init_user_directory, get_user_config, save_user_config


def get_config():
    """
    Compatibility shim for old get_config() function.

    Returns Config() instance for backward compatibility.
    Deprecated - use Config() directly instead.
    """
    # Import here to avoid circular imports
    from dev.goblin.core.config import Config

    return Config()


def __getattr__(name):
    """
    Lazy import Config to avoid circular imports.

    When someone does `from dev.goblin.core.config import Config`, Python first
    tries this package's __init__.py. We use __getattr__ to lazily
    load Config from the sibling module.
    """
    if name == "Config":
        import importlib.util
        from pathlib import Path

        # Load core/config.py as a module
        config_module_path = Path(__file__).parent.parent / "config.py"
        spec = importlib.util.spec_from_file_location(
            "core._config_module", config_module_path
        )
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        return module.Config
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")


__all__ = [
    "Config",
    "get_config",  # Compatibility shim (deprecated)
    "get_system_path",
    "get_user_path",
    "get_config_path",
    "get_credentials_path",
    "get_temp_path",
    "is_tinycore",
    "get_tinycore_user_home",
    "setup_tinycore_user",
    "get_platform_info",
    "init_user_directory",
    "get_user_config",
    "save_user_config",
]
