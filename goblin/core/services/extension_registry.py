"""
uDOS Extension Service Registry - Alpha v1.0.0.0+
Provides clear separation and management for all extension services
"""

import json
from pathlib import Path
from typing import Dict, Optional, Any, List
from enum import Enum
from dataclasses import dataclass
import logging

logger = logging.getLogger(__name__)


def _get_extension_version(extension_name: str, fallback: str = "1.0.0.0") -> str:
    """Get version from extension/version.json."""
    # Map extension names to their version.json paths
    version_paths = {
        "tauri": Path(__file__).parent.parent.parent
        / "extensions"
        / "tauri"
        / "version.json",
        "api": Path(__file__).parent.parent.parent
        / "extensions"
        / "api"
        / "version.json",
        "cloud": Path(__file__).parent.parent.parent
        / "extensions"
        / "cloud"
        / "version.json",
        "assistant": Path(__file__).parent.parent.parent
        / "extensions"
        / "assistant"
        / "version.json",
        "web.dashboard": Path(__file__).parent.parent.parent
        / "extensions"
        / "web"
        / "dashboard"
        / "version.json",
        "web.teletext": Path(__file__).parent.parent.parent
        / "extensions"
        / "web"
        / "teletext"
        / "version.json",
    }

    version_file = version_paths.get(extension_name)
    if version_file and version_file.exists():
        try:
            with open(version_file, "r") as f:
                data = json.load(f)
                version = data.get("version")
                # Handle both string and dict formats
                if isinstance(version, dict):
                    return f"{version.get('major', 1)}.{version.get('minor', 0)}.{version.get('patch', 0)}.{version.get('build', 0)}"
                return str(version) if version else fallback
        except:
            pass
    return fallback


class ExtensionType(Enum):
    """Types of extensions"""

    TAURI = "tauri"
    API = "api"
    WEB = "web"
    CLOUD = "cloud"
    MESHCORE = "meshcore"
    ASSISTANT = "assistant"


class ExtensionStatus(Enum):
    """Extension status"""

    ONLINE = "online"
    OFFLINE = "offline"
    ERROR = "error"
    DISABLED = "disabled"


@dataclass
class ExtensionInfo:
    """Extension information"""

    type: ExtensionType
    name: str
    enabled: bool
    status: ExtensionStatus
    port: Optional[int] = None
    version: str = "1.0.0"
    description: str = ""
    config_path: Optional[Path] = None
    dependencies: List[str] = None

    def to_dict(self) -> dict:
        """Convert to dictionary"""
        return {
            "type": self.type.value,
            "name": self.name,
            "enabled": self.enabled,
            "status": self.status.value,
            "port": self.port,
            "version": self.version,
            "description": self.description,
            "config_path": str(self.config_path) if self.config_path else None,
            "dependencies": self.dependencies or [],
        }


class ExtensionRegistry:
    """
    Central registry for all uDOS extensions.

    Provides:
    - Extension discovery and registration
    - Status monitoring
    - Clear separation of concerns
    - Service coordination
    """

    def __init__(self, project_root: Optional[Path] = None):
        """Initialize extension registry."""
        if project_root is None:
            project_root = Path(__file__).parent.parent.parent

        self.project_root = project_root
        self.extensions_path = project_root / "extensions"

        self._extensions: Dict[str, ExtensionInfo] = {}
        self._initialize_extensions()

    def _initialize_extensions(self):
        """Initialize all extensions."""
        # Tauri Extension
        self._extensions["tauri"] = ExtensionInfo(
            type=ExtensionType.TAURI,
            name="Tauri Desktop App",
            enabled=True,
            status=ExtensionStatus.ONLINE,
            port=3000,
            version=_get_extension_version("tauri"),
            description="Desktop GUI application with System 7 interface",
            config_path=self.extensions_path
            / "tauri"
            / "config"
            / "user-preferences.json",
            dependencies=["api"],
        )

        # API Extension
        self._extensions["api"] = ExtensionInfo(
            type=ExtensionType.API,
            name="REST API Server",
            enabled=True,
            status=ExtensionStatus.ONLINE,
            port=5001,
            version=_get_extension_version("api"),
            description="REST API bridge for core services",
            config_path=self.project_root / ".env",
            dependencies=[],
        )

        # Web Extensions
        self._extensions["web.dashboard"] = ExtensionInfo(
            type=ExtensionType.WEB,
            name="Web Dashboard",
            enabled=True,
            status=ExtensionStatus.ONLINE,
            port=5050,
            version=_get_extension_version("web.dashboard"),
            description="Retro web dashboard for monitoring",
            config_path=self.extensions_path / "web" / "dashboard",
            dependencies=["api"],
        )

        self._extensions["web.teletext"] = ExtensionInfo(
            type=ExtensionType.WEB,
            name="Teletext Interface",
            enabled=True,
            status=ExtensionStatus.ONLINE,
            port=5051,
            version=_get_extension_version("web.teletext"),
            description="Broadcast TV style interface",
            config_path=self.extensions_path / "web" / "teletext",
            dependencies=["api"],
        )

        # Assistant Extension
        self._extensions["assistant"] = ExtensionInfo(
            type=ExtensionType.ASSISTANT,
            name="AI Assistant",
            enabled=True,
            status=ExtensionStatus.ONLINE,
            version=_get_extension_version("assistant"),
            description="Multi-provider AI assistant (Gemini, Claude, GPT-4, Mistral, Vibe)",
            config_path=self.extensions_path / "assistant",
            dependencies=[],
        )

        # Cloud Extension (Disabled)
        self._extensions["cloud"] = ExtensionInfo(
            type=ExtensionType.CLOUD,
            name="Cloud Services",
            enabled=False,
            status=ExtensionStatus.DISABLED,
            version="0.1.0",
            description="Cloud sync and storage (future)",
            config_path=self.extensions_path / "cloud",
            dependencies=["api"],
        )

        # Meshcore Extension (Disabled)
        self._extensions["meshcore"] = ExtensionInfo(
            type=ExtensionType.MESHCORE,
            name="Meshcore Network",
            enabled=False,
            status=ExtensionStatus.DISABLED,
            version="0.1.0",
            description="Peer-to-peer networking (future)",
            config_path=self.extensions_path / "meshcore",
            dependencies=["api"],
        )

    # =========================================================================
    # EXTENSION MANAGEMENT
    # =========================================================================

    def get_extension(self, extension_id: str) -> Optional[ExtensionInfo]:
        """Get extension info by ID."""
        return self._extensions.get(extension_id)

    def get_all_extensions(self) -> Dict[str, ExtensionInfo]:
        """Get all extensions."""
        return self._extensions.copy()

    def get_enabled_extensions(self) -> Dict[str, ExtensionInfo]:
        """Get only enabled extensions."""
        return {
            ext_id: info for ext_id, info in self._extensions.items() if info.enabled
        }

    def get_extensions_by_type(
        self, extension_type: ExtensionType
    ) -> Dict[str, ExtensionInfo]:
        """Get extensions by type."""
        return {
            ext_id: info
            for ext_id, info in self._extensions.items()
            if info.type == extension_type
        }

    def set_extension_status(self, extension_id: str, status: ExtensionStatus) -> bool:
        """Set extension status."""
        if extension_id in self._extensions:
            self._extensions[extension_id].status = status
            return True
        return False

    def enable_extension(self, extension_id: str) -> bool:
        """Enable extension."""
        if extension_id in self._extensions:
            self._extensions[extension_id].enabled = True
            if self._extensions[extension_id].status == ExtensionStatus.DISABLED:
                self._extensions[extension_id].status = ExtensionStatus.OFFLINE
            return True
        return False

    def disable_extension(self, extension_id: str) -> bool:
        """Disable extension."""
        if extension_id in self._extensions:
            self._extensions[extension_id].enabled = False
            self._extensions[extension_id].status = ExtensionStatus.DISABLED
            return True
        return False

    # =========================================================================
    # SERVICE SEPARATION
    # =========================================================================

    def get_service_boundaries(self) -> Dict[str, Any]:
        """
        Get clear service boundaries for all extensions.

        Returns:
            Dict mapping extension IDs to their responsibilities
        """
        return {
            "tauri": {
                "responsibilities": [
                    "Desktop GUI rendering",
                    "User interaction (clicks, keyboard)",
                    "Window management",
                    "System tray integration",
                    "Local file dialog access",
                ],
                "boundaries": [
                    "Does NOT access core Python directly",
                    "Does NOT modify user.json directly",
                    "Uses API server for all data",
                    "Settings synced via API",
                ],
            },
            "api": {
                "responsibilities": [
                    "REST API endpoints",
                    "WebSocket streaming",
                    "Service coordination",
                    "Bridge between core and frontends",
                    "Session management",
                ],
                "boundaries": [
                    "Does NOT render UI",
                    "Does NOT handle user input directly",
                    "Stateless (uses core services for state)",
                    "Port 5001 only",
                ],
            },
            "web.dashboard": {
                "responsibilities": [
                    "Dashboard visualization",
                    "Real-time monitoring",
                    "Status displays",
                    "Progress bars and metrics",
                ],
                "boundaries": [
                    "Read-only interface",
                    "Uses API for data",
                    "Port 5050 only",
                    "No command execution",
                ],
            },
            "web.teletext": {
                "responsibilities": [
                    "Teletext-style interface",
                    "Page-based navigation",
                    "Broadcast TV aesthetic",
                    "Command execution UI",
                ],
                "boundaries": [
                    "Uses API for commands",
                    "Port 5051 only",
                    "No direct file access",
                ],
            },
            "assistant": {
                "responsibilities": [
                    "AI provider management",
                    "Content generation",
                    "OK command handling",
                    "Multi-provider routing",
                ],
                "boundaries": [
                    "No UI rendering",
                    "Works through commands",
                    "API key management only",
                    "No file system access",
                ],
            },
            "cloud": {
                "responsibilities": [
                    "Cloud storage sync (future)",
                    "Cross-device settings sync",
                    "Backup management",
                    "Collaborative features",
                ],
                "boundaries": [
                    "Currently disabled",
                    "Will use API bridge",
                    "Separate authentication",
                    "Opt-in only",
                ],
            },
            "meshcore": {
                "responsibilities": [
                    "P2P networking (future)",
                    "Local discovery",
                    "Distributed computing",
                    "File sharing",
                ],
                "boundaries": [
                    "Currently disabled",
                    "Local network only",
                    "Separate security layer",
                    "Opt-in only",
                ],
            },
        }

    def get_data_flow(self) -> Dict[str, Any]:
        """
        Get data flow patterns between extensions.

        Returns:
            Dict describing how data flows through the system
        """
        return {
            "user_input": {
                "flow": "Tauri → API → Core → API → Tauri",
                "components": ["tauri", "api", "core"],
                "description": "User input goes through API, never directly to core",
            },
            "settings_sync": {
                "flow": "Tauri ← settings_sync → user.json/env",
                "components": ["tauri", "api", "settings_sync", "core"],
                "description": "Settings sync bidirectional through API",
            },
            "file_access": {
                "flow": "Tauri → API → file_picker_service → filesystem",
                "components": ["tauri", "api", "file_picker_service"],
                "description": "File access always through service layer",
            },
            "map_data": {
                "flow": "Tauri → API → map_data_bridge → core/data",
                "components": ["tauri", "api", "map_data_bridge", "core"],
                "description": "Map data served from core through bridge",
            },
            "dashboard": {
                "flow": "Web Dashboard → API → dashboard_service → memory/",
                "components": ["web.dashboard", "api", "dashboard_service"],
                "description": "Dashboard reads live data through service",
            },
        }

    # =========================================================================
    # PORT REGISTRY
    # =========================================================================

    def get_port_registry(self) -> Dict[int, str]:
        """Get all registered ports."""
        ports = {}
        for ext_id, info in self._extensions.items():
            if info.port:
                ports[info.port] = ext_id
        return ports

    def is_port_available(self, port: int) -> bool:
        """Check if port is available."""
        ports = self.get_port_registry()
        return port not in ports

    # =========================================================================
    # STATUS & HEALTH
    # =========================================================================

    def get_system_status(self) -> Dict[str, Any]:
        """Get overall system status."""
        extensions = {
            ext_id: info.to_dict() for ext_id, info in self._extensions.items()
        }

        enabled_count = sum(1 for info in self._extensions.values() if info.enabled)
        online_count = sum(
            1
            for info in self._extensions.values()
            if info.status == ExtensionStatus.ONLINE
        )

        return {
            "extensions": extensions,
            "summary": {
                "total": len(self._extensions),
                "enabled": enabled_count,
                "online": online_count,
                "offline": enabled_count - online_count,
            },
            "ports": self.get_port_registry(),
        }


# Singleton instance
_extension_registry: Optional[ExtensionRegistry] = None


def get_extension_registry(project_root: Optional[Path] = None) -> ExtensionRegistry:
    """Get singleton ExtensionRegistry instance."""
    global _extension_registry
    if _extension_registry is None:
        _extension_registry = ExtensionRegistry(project_root)
    return _extension_registry
