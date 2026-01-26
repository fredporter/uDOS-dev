"""
FHS-Compliant Path Helpers

Provides system and user path helpers following TinyCore/Linux standards.

System paths: /opt/udos/ (read-only)
User paths: ~/.udos/ (read-write)

TinyCore-specific:
- User home: /home/tc/ (not ~)
- Persistence: mydata.tgz (requires explicit save)
- System: /opt/ mounts from TCZ extensions
"""

from pathlib import Path
import os
import platform


def is_tinycore() -> bool:
    """
    Detect if running on Tiny Core Linux.

    Checks:
    1. /etc/os-release contains 'Tiny Core'
    2. /home/tc exists (default TinyCore user)
    3. tce-load command available

    Returns:
        True if running on Tiny Core Linux
    """
    # Check /etc/os-release
    os_release = Path("/etc/os-release")
    if os_release.exists():
        try:
            content = os_release.read_text()
            if "Tiny Core" in content or "tinycore" in content.lower():
                return True
        except Exception:
            pass

    # Check for TinyCore user home
    if Path("/home/tc").exists():
        return True

    # Check for tce-load command
    tce_load = Path("/usr/bin/tce-load")
    if tce_load.exists():
        return True

    return False


def get_tinycore_user_home() -> Path:
    """
    Get TinyCore user home directory.

    Returns /home/tc for TinyCore, otherwise standard home.
    """
    if is_tinycore():
        tc_home = Path("/home/tc")
        if tc_home.exists():
            return tc_home
    return Path.home()


def get_system_path(subpath: str = "") -> Path:
    """
    Get system path (read-only).

    In production: /opt/udos/
    In development: Project root

    Args:
        subpath: Optional subdirectory path

    Returns:
        Path to system directory

    Example:
        >>> get_system_path('core')
        PosixPath('/opt/udos/core')
    """
    # Check if running from installed system
    system_base = Path("/opt/udos")

    if system_base.exists():
        # Production install
        base = system_base
    else:
        # Development mode - find project root
        current = Path(__file__).resolve()

        # Walk up to find project root (contains core/ directory)
        while current.parent != current:
            if (current / "core").exists():
                base = current
                break
            current = current.parent
        else:
            # Fallback: use current file's grandparent
            base = Path(__file__).parent.parent.parent

    return base / subpath if subpath else base


def get_user_path(subpath: str = "") -> Path:
    """
    Get user workspace path (read-write).

    Location: ~/.udos/memory/ (or /home/tc/.udos/memory/ on TinyCore)

    Creates directory if it doesn't exist.

    Args:
        subpath: Optional subdirectory path (e.g., 'logs', 'sandbox/scripts')

    Returns:
        Path to user directory

    Example:
        >>> get_user_path('logs')
        PosixPath('/home/user/.udos/memory/logs')
    """
    home = get_tinycore_user_home() if is_tinycore() else Path.home()
    base = home / ".udos" / "memory"
    path = base / subpath if subpath else base

    # Create directory if needed (with appropriate permissions)
    path.mkdir(mode=0o755, parents=True, exist_ok=True)

    return path


def get_config_path(subpath: str = "") -> Path:
    """
    Get user configuration path.

    Location: ~/.udos/config/ (or /home/tc/.udos/config/ on TinyCore)

    Creates directory with restricted permissions (700).

    Args:
        subpath: Optional subdirectory path

    Returns:
        Path to config directory

    Example:
        >>> get_config_path('user.json')
        PosixPath('/home/user/.udos/config/user.json')
    """
    home = get_tinycore_user_home() if is_tinycore() else Path.home()
    base = home / ".udos" / "config"
    path = base / subpath if subpath else base

    # Create directory with restricted permissions
    if not path.exists():
        path.mkdir(mode=0o700, parents=True, exist_ok=True)

    return path


def get_credentials_path(subpath: str = "") -> Path:
    """
    Get credentials storage path.

    Location: ~/.udos/.credentials/ (or /home/tc/.udos/.credentials/ on TinyCore)

    Creates directory with strict permissions (700).

    Args:
        subpath: Optional subdirectory path

    Returns:
        Path to credentials directory

    Example:
        >>> get_credentials_path('keys.enc')
        PosixPath('/home/user/.udos/.credentials/keys.enc')
    """
    home = get_tinycore_user_home() if is_tinycore() else Path.home()
    base = home / ".udos" / ".credentials"
    path = base / subpath if subpath else base

    # Create directory with strict permissions
    if not path.exists():
        path.mkdir(mode=0o700, parents=True, exist_ok=True)

    return path


def get_temp_path(subpath: str = "") -> Path:
    """
    Get temporary session directory.

    Location: /tmp/udos-$USER/

    Cleaned up on exit.

    Args:
        subpath: Optional subdirectory path

    Returns:
        Path to temp directory
    """
    import getpass

    base = Path("/tmp") / f"udos-{getpass.getuser()}"
    path = base / subpath if subpath else base

    path.mkdir(mode=0o755, parents=True, exist_ok=True)

    return path


def setup_tinycore_user() -> dict:
    """
    Initialize uDOS directories for TinyCore user.

    Creates:
    - /home/tc/.udos/memory/
    - /home/tc/.udos/config/
    - /home/tc/.udos/.credentials/
    - /home/tc/.udos/logs/

    Also adds .udos to /opt/.filetool.lst for mydata.tgz persistence.

    Returns:
        dict with created paths and persistence status
    """
    result = {
        "is_tinycore": is_tinycore(),
        "paths_created": [],
        "persistence_configured": False,
        "errors": [],
    }

    if not is_tinycore():
        result["message"] = "Not running on TinyCore, using standard paths"
        # Still create directories for non-TinyCore
        try:
            get_user_path()
            get_config_path()
            get_credentials_path()
            result["paths_created"] = [
                "~/.udos/memory",
                "~/.udos/config",
                "~/.udos/.credentials",
            ]
        except Exception as e:
            result["errors"].append(str(e))
        return result

    # TinyCore-specific setup
    tc_home = Path("/home/tc")

    try:
        # Create uDOS directories
        udos_base = tc_home / ".udos"
        for subdir in ["memory", "config", ".credentials", "logs"]:
            path = udos_base / subdir
            path.mkdir(
                mode=0o700 if subdir in [".credentials", "config"] else 0o755,
                parents=True,
                exist_ok=True,
            )
            result["paths_created"].append(str(path))

        # Configure persistence via filetool.lst
        filetool_lst = Path("/opt/.filetool.lst")
        udos_entry = "/home/tc/.udos"

        if filetool_lst.exists():
            content = filetool_lst.read_text()
            if udos_entry not in content:
                try:
                    # Append to filetool.lst (requires root on TinyCore)
                    with open(filetool_lst, "a") as f:
                        f.write(f"\n{udos_entry}\n")
                    result["persistence_configured"] = True
                except PermissionError:
                    result["errors"].append(
                        f"Cannot write to {filetool_lst} - run as root or add manually: {udos_entry}"
                    )
            else:
                result["persistence_configured"] = True
        else:
            result["errors"].append(
                f"{filetool_lst} not found - manual persistence setup needed"
            )

        result["message"] = "TinyCore user setup complete"

    except Exception as e:
        result["errors"].append(f"Setup failed: {str(e)}")

    return result


def get_platform_info() -> dict:
    """
    Get platform information for diagnostics.

    Returns:
        dict with platform details
    """
    return {
        "system": platform.system(),
        "release": platform.release(),
        "machine": platform.machine(),
        "is_tinycore": is_tinycore(),
        "user_home": str(get_tinycore_user_home() if is_tinycore() else Path.home()),
        "udos_base": str(
            (get_tinycore_user_home() if is_tinycore() else Path.home()) / ".udos"
        ),
    }
