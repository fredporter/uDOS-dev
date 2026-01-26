"""
Path Constants for uDOS v1.0.0.44+

Centralized path management with Alpine Linux detection.
Use these constants instead of string literals.

Alpine Linux Path Strategy:
- Development: ./memory/, ./core/, etc. (workspace-relative)
- Alpine: /opt/udos/ (persistent), /tmp/udos/ (ephemeral)
- Detection via /etc/alpine-release or UDOS_ALPINE env var

Example:
    from dev.goblin.core.utils.paths import PATHS, is_alpine

    # ✅ Good - works everywhere
    user_file = PATHS.MEMORY_USER / "user.json"

    # Check platform
    if is_alpine():
        print("Running on Alpine Linux")
"""

from pathlib import Path
from typing import Dict, Optional
import os


def is_alpine() -> bool:
    """
    Detect if running on Alpine Linux.

    Detection methods:
    1. UDOS_ALPINE env var (for testing/override)
    2. /etc/alpine-release exists
    3. apk command exists (Alpine package manager)
    4. /etc/os-release contains 'Alpine'

    Returns:
        True if running on Alpine Linux
    """
    # Allow override via environment
    if os.environ.get("UDOS_ALPINE", "").lower() in ("1", "true", "yes"):
        return True

    # Check for Alpine release file
    if Path("/etc/alpine-release").exists():
        return True

    # Check for apk package manager
    import shutil

    if shutil.which("apk") is not None:
        return True

    # Check /etc/os-release
    try:
        os_release = Path("/etc/os-release")
        if os_release.exists():
            content = os_release.read_text().lower()
            if "alpine" in content:
                return True
    except:
        pass

    return False


def is_tinycore() -> bool:
    """
    DEPRECATED: Use is_alpine() instead.

    Detect if running on Tiny Core Linux.
    This function is kept for backwards compatibility but will be removed.
    All TinyCore logic now redirects to Alpine Linux detection.

    Returns:
        False (TinyCore is deprecated, use Alpine Linux)
    """
    # Check for actual TinyCore environment (for migration warning)
    try:
        os_release = Path("/etc/os-release")
        if os_release.exists():
            content = os_release.read_text().lower()
            if "tiny core" in content or "tinycore" in content:
                print(
                    "WARNING: TinyCore Linux detected. uDOS has migrated to Alpine Linux."
                )
                print("Please migrate to Alpine Linux for continued support.")
                return False
    except:
        pass

    # Check for TC package manager
    if Path("/usr/bin/tce-load").exists():
        print("WARNING: TinyCore tools detected. uDOS has migrated to Alpine Linux.")
        return False

    return False


def get_platform_info() -> Dict[str, str]:
    """
    Get platform information for logging/diagnostics.

    Returns:
        Dict with platform details
    """
    import platform

    return {
        "os": platform.system(),
        "os_version": platform.version(),
        "is_alpine": is_alpine(),
        "udos_root": str(_get_udos_root()),
        "python_version": platform.python_version(),
    }


def _get_udos_root() -> Path:
    """
    Get uDOS root directory.

    Priority:
    1. UDOS_ROOT environment variable
    2. Alpine: /opt/udos
    3. Development: Parent of core/ directory

    Returns:
        Path to uDOS root
    """
    # Environment override
    env_root = os.environ.get("UDOS_ROOT")
    if env_root:
        return Path(env_root)

    # Alpine deployment
    if is_alpine():
        alpine_root = Path("/opt/udos")
        if alpine_root.exists():
            return alpine_root

    # Development: relative to this file
    return Path(__file__).parent.parent.parent


def _get_ephemeral_root() -> Path:
    """
    Get ephemeral storage root (for temp files, caches).

    Alpine: /tmp/udos (RAM disk, cleared on reboot)
    Other: Standard temp or workspace .tmp/

    Returns:
        Path to ephemeral storage
    """
    if is_alpine():
        tmp = Path("/tmp/udos")
        tmp.mkdir(parents=True, exist_ok=True)
        return tmp

    # Development: use workspace .tmp/
    workspace_tmp = _get_udos_root() / ".tmp"
    workspace_tmp.mkdir(parents=True, exist_ok=True)
    return workspace_tmp


class PathConstants:
    """Centralized path constants for uDOS workspace"""

    # Root directories (computed on access for TinyCore support)
    @property
    def ROOT(self) -> Path:
        return _get_udos_root()

    @property
    def PROJECT_ROOT(self) -> Path:
        return self.ROOT

    @property
    def CORE(self) -> Path:
        return self.ROOT / "core"

    @property
    def EXTENSIONS(self) -> Path:
        return self.ROOT / "extensions"

    @property
    def KNOWLEDGE(self) -> Path:
        return self.ROOT / "knowledge"

    @property
    def MEMORY(self) -> Path:
        return self.ROOT / "memory"

    @property
    def DEV(self) -> Path:
        return self.ROOT / "dev"

    @property
    def WIKI(self) -> Path:
        return self.ROOT / "wiki"

    # Ephemeral storage (TinyCore: /tmp/udos, Dev: .tmp/)
    @property
    def EPHEMERAL(self) -> Path:
        return _get_ephemeral_root()

    @property
    def CACHE(self) -> Path:
        return self.EPHEMERAL / "cache"

    @property
    def TMP(self) -> Path:
        return self.EPHEMERAL / "tmp"

    # Core subdirectories
    @property
    def CORE_DATA(self) -> Path:
        return self.CORE / "data"

    @property
    def CORE_DATA_GEOGRAPHY(self) -> Path:
        return self.CORE_DATA / "geography"

    @property
    def CORE_DATA_GEOGRAPHY_CITIES(self) -> Path:
        return self.CORE_DATA_GEOGRAPHY / "cities.json"

    @property
    def CORE_DATA_GEOGRAPHY_CLIMATE(self) -> Path:
        return self.CORE_DATA_GEOGRAPHY / "climate.json"

    @property
    def CORE_DATA_GEOGRAPHY_TERRAIN(self) -> Path:
        return self.CORE_DATA_GEOGRAPHY / "terrain.json"

    @property
    def CORE_COMMANDS(self) -> Path:
        return self.CORE / "commands"

    @property
    def CORE_RUNTIME(self) -> Path:
        return self.CORE / "runtime"

    @property
    def CORE_SERVICES(self) -> Path:
        return self.CORE / "services"

    @property
    def CORE_UTILS(self) -> Path:
        return self.CORE / "utils"

    # Memory subdirectories
    @property
    def MEMORY_UCODE(self) -> Path:
        return self.MEMORY / "ucode"

    @property
    def MEMORY_UCODE_SCRIPTS(self) -> Path:
        return self.MEMORY_UCODE / "scripts"

    @property
    def MEMORY_UCODE_TESTS(self) -> Path:
        return self.MEMORY_UCODE / "tests"

    @property
    def MEMORY_UCODE_SANDBOX(self) -> Path:
        return self.MEMORY_UCODE / "sandbox"

    @property
    def MEMORY_UCODE_STDLIB(self) -> Path:
        return self.MEMORY_UCODE / "stdlib"

    @property
    def MEMORY_UCODE_EXAMPLES(self) -> Path:
        return self.MEMORY_UCODE / "examples"

    @property
    def MEMORY_UCODE_ADVENTURES(self) -> Path:
        return self.MEMORY_UCODE / "adventures"

    @property
    def MEMORY_WORKFLOWS(self) -> Path:
        return self.MEMORY / "workflows"

    @property
    def MEMORY_WORKFLOWS_MISSIONS(self) -> Path:
        return self.MEMORY_WORKFLOWS / "missions"

    @property
    def MEMORY_WORKFLOWS_CHECKPOINTS(self) -> Path:
        return self.MEMORY_WORKFLOWS / "checkpoints"

    @property
    def MEMORY_WORKFLOWS_STATE(self) -> Path:
        return self.MEMORY_WORKFLOWS / "state"

    @property
    def MEMORY_SYSTEM(self) -> Path:
        return self.MEMORY / "system"

    @property
    def MEMORY_SYSTEM_USER(self) -> Path:
        return self.MEMORY_SYSTEM / "user"

    @property
    def MEMORY_SYSTEM_THEMES(self) -> Path:
        return self.MEMORY_SYSTEM / "themes"

    @property
    def MEMORY_BANK(self) -> Path:
        return self.MEMORY / "bank"

    @property
    def MEMORY_BANK_USER(self) -> Path:
        return self.MEMORY_BANK / "user"

    @property
    def MEMORY_BANK_PRIVATE(self) -> Path:
        return self.MEMORY_BANK / "private"

    @property
    def MEMORY_BANK_BARTER(self) -> Path:
        return self.MEMORY_BANK / "barter"

    @property
    def MEMORY_SHARED(self) -> Path:
        return self.MEMORY / "shared"

    @property
    def MEMORY_SHARED_PUBLIC(self) -> Path:
        return self.MEMORY_SHARED / "public"

    @property
    def MEMORY_SHARED_GROUPS(self) -> Path:
        return self.MEMORY_SHARED / "groups"

    @property
    def MEMORY_SHARED_METADATA(self) -> Path:
        return self.MEMORY_SHARED / "metadata"

    @property
    def MEMORY_LOGS(self) -> Path:
        return self.MEMORY / "logs"

    @property
    def MEMORY_SESSIONS(self) -> Path:
        return self.MEMORY / "sessions"

    @property
    def MEMORY_MISSIONS(self) -> Path:
        return self.MEMORY / "missions"

    @property
    def MEMORY_CHECKLISTS(self) -> Path:
        return self.MEMORY / "checklists"

    @property
    def MEMORY_DOCS(self) -> Path:
        return self.MEMORY / "docs"

    @property
    def MEMORY_DRAFTS(self) -> Path:
        return self.MEMORY / "drafts"

    @property
    def MEMORY_DRAFTS_ASCII(self) -> Path:
        return self.MEMORY_DRAFTS / "ascii"

    @property
    def MEMORY_DRAFTS_SVG(self) -> Path:
        return self.MEMORY_DRAFTS / "svg"

    @property
    def MEMORY_DRAFTS_TELETEXT(self) -> Path:
        return self.MEMORY_DRAFTS / "teletext"

    # Deprecated paths (for migration/compatibility)
    @property
    def DEPRECATED_SANDBOX(self) -> Path:
        return self.ROOT / ".archive" / "deprecated-root" / "sandbox-legacy"

    # Common file paths
    @property
    def USER_PROFILE(self) -> Path:
        return self.MEMORY_SYSTEM_USER / "USER.UDT"

    @property
    def WORKFLOW_CONFIG(self) -> Path:
        return self.MEMORY_WORKFLOWS / "config.json"

    @property
    def WORKFLOW_STATE(self) -> Path:
        return self.MEMORY_WORKFLOWS / "state" / "current.json"

    @property
    def CHECKLIST_STATE(self) -> Path:
        return self.MEMORY_SYSTEM_USER / "checklist_state.json"

    @property
    def WEBHOOKS_CONFIG(self) -> Path:
        return self.MEMORY_SYSTEM / "webhooks.json"

    @property
    def KNOWLEDGE_GAPS_REPORT(self) -> Path:
        return self.MEMORY_SYSTEM / "knowledge-gaps-report.json"

    @property
    def KNOWLEDGE_QUALITY_REPORT(self) -> Path:
        return self.MEMORY_SYSTEM / "knowledge-quality-report.json"

    @property
    def KNOWLEDGE_QUALITY_HISTORY(self) -> Path:
        return self.MEMORY_SYSTEM / "knowledge-quality-history.json"

    @property
    def KNOWLEDGE_QUALITY_DASHBOARD(self) -> Path:
        return self.MEMORY_SYSTEM / "knowledge-quality-dashboard.html"

    @property
    def RESOURCE_STATE(self) -> Path:
        return self.MEMORY_BANK / "system" / "resource-state.json"

    def get_writable_dirs(self) -> set:
        """Get set of directories that are writable by users"""
        return {
            str(self.MEMORY),
            str(self.MEMORY_UCODE_SCRIPTS),
            str(self.MEMORY_UCODE_SANDBOX),
            str(self.MEMORY_WORKFLOWS),
            str(self.MEMORY_SYSTEM_USER),
            str(self.MEMORY_BANK),
            str(self.MEMORY_SHARED),
            str(self.MEMORY_LOGS),
            str(self.MEMORY_DRAFTS),
            str(self.EPHEMERAL),
        }

    def get_workspace_map(self) -> Dict[str, Dict[str, str]]:
        """Get workspace directory mapping for legacy compatibility"""
        return {
            "memory": {
                "path": str(self.MEMORY),
                "description": "User workspace (persistent)",
            },
            "ucode": {
                "path": str(self.MEMORY_UCODE),
                "description": "uPY scripts and tests",
            },
            "workflows": {
                "path": str(self.MEMORY_WORKFLOWS),
                "description": "Workflow automation",
            },
            "system": {
                "path": str(self.MEMORY_SYSTEM_USER),
                "description": "System configuration",
            },
            "ephemeral": {
                "path": str(self.EPHEMERAL),
                "description": "Temporary storage (cleared on reboot)",
            },
        }


# Global instance for easy importing
PATHS = PathConstants()
