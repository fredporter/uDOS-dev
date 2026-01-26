"""
State Manager - Unified state synchronization across TUI, Tauri, and Web interfaces.

Manages:
- User preferences and settings
- Interface state (active UI, current file, pager position)
- Installed systems and capabilities
- Default startup configuration
- Cross-interface synchronization via WebSocket

Author: uDOS Development Team
Version: 1.2.22
Date: December 22, 2025
"""

import json
import uuid
from pathlib import Path
from typing import Dict, Any, Optional, List, Callable
from datetime import datetime
from dataclasses import dataclass, asdict, field
import threading

from ..config.paths import get_user_path


@dataclass
class InterfaceState:
    """Current interface state snapshot."""

    active_interface: str = "TUI"  # TUI, Tauri, Web
    current_file: Optional[str] = None
    pager_position: int = 0
    pager_content: Optional[str] = None
    last_command: Optional[str] = None
    command_history_index: int = 0
    file_browser_workspace: str = "knowledge"
    file_browser_path: str = ""
    theme: str = "default"
    keypad_enabled: bool = False
    last_updated: str = field(default_factory=lambda: datetime.now().isoformat())


@dataclass
class SystemCapabilities:
    """Installed systems and extensions."""

    has_tauri: bool = False
    has_meshcore: bool = False
    has_gemini_api: bool = False
    has_web_server: bool = True
    extensions_loaded: List[str] = field(default_factory=list)
    tui_components: Dict[str, bool] = field(
        default_factory=lambda: {
            "keypad": True,
            "pager": True,
            "predictor": True,
            "file_browser": True,
            "debug_panel": True,
        }
    )


@dataclass
class UserConfiguration:
    """User configuration and preferences."""

    default_ui: str = "TUI"  # TUI, Tauri, Web
    startup_command: Optional[str] = None
    auto_launch_server: bool = False
    log_level: str = "INFO"
    preserve_scroll: bool = True
    auto_save_state: bool = True
    websocket_enabled: bool = True
    correlation_id_tracking: bool = True


class StateManager:
    """
    Singleton state manager for cross-interface synchronization.

    Features:
    - Single source of truth for user state
    - WebSocket broadcasting for live sync
    - Auto-save with debouncing (max 1 write/second)
    - Session recovery on startup
    - Thread-safe state updates
    """

    _instance: Optional["StateManager"] = None
    _lock = threading.Lock()

    def __new__(cls):
        """Singleton pattern implementation."""
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self):
        """Initialize state manager."""
        if hasattr(self, "_initialized"):
            return

        self._initialized = True
        self.state_file = get_user_path("bank/user/user-state.json")
        self.state_file.parent.mkdir(parents=True, exist_ok=True)

        # State components
        self.interface_state = InterfaceState()
        self.system_capabilities = SystemCapabilities()
        self.user_config = UserConfiguration()

        # WebSocket clients for broadcasting
        self._ws_clients: List[Any] = []
        self._broadcast_callbacks: List[Callable] = []

        # Debouncing
        self._pending_save = False
        self._last_save_time = datetime.now()
        self._save_lock = threading.Lock()

        # Session tracking
        self.session_id = f"session_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        self.correlation_id = str(uuid.uuid4())

        # Load persisted state
        self.load_state()

    def load_state(self) -> bool:
        """Load state from JSON file."""
        try:
            if self.state_file.exists():
                with open(self.state_file, "r") as f:
                    data = json.load(f)

                # Reconstruct state objects
                if "interface_state" in data:
                    self.interface_state = InterfaceState(**data["interface_state"])
                if "system_capabilities" in data:
                    self.system_capabilities = SystemCapabilities(
                        **data["system_capabilities"]
                    )
                if "user_config" in data:
                    self.user_config = UserConfiguration(**data["user_config"])

                return True
        except Exception as e:
            print(f"[StateManager] Failed to load state: {e}")

        return False

    def save_state(self, force: bool = False) -> bool:
        """
        Save state to JSON file with debouncing.

        Args:
            force: Skip debouncing and save immediately
        """
        with self._save_lock:
            now = datetime.now()

            # Debounce: max 1 write per second
            if not force:
                time_since_last = (now - self._last_save_time).total_seconds()
                if time_since_last < 1.0:
                    self._pending_save = True
                    return False

            try:
                # Update timestamp
                self.interface_state.last_updated = now.isoformat()

                # Serialize to JSON
                state_data = {
                    "session_id": self.session_id,
                    "interface_state": asdict(self.interface_state),
                    "system_capabilities": asdict(self.system_capabilities),
                    "user_config": asdict(self.user_config),
                    "last_saved": now.isoformat(),
                }

                # Write to file
                with open(self.state_file, "w") as f:
                    json.dump(state_data, f, indent=2)

                self._last_save_time = now
                self._pending_save = False
                return True

            except Exception as e:
                print(f"[StateManager] Failed to save state: {e}")
                return False

    def update_interface_state(self, **kwargs) -> None:
        """Update interface state and broadcast changes."""
        for key, value in kwargs.items():
            if hasattr(self.interface_state, key):
                setattr(self.interface_state, key, value)

        # Broadcast to WebSocket clients
        self.broadcast_state_change("interface_state", kwargs)

        # Auto-save if enabled
        if self.user_config.auto_save_state:
            self.save_state()

    def update_system_capabilities(self, **kwargs) -> None:
        """Update system capabilities."""
        for key, value in kwargs.items():
            if hasattr(self.system_capabilities, key):
                setattr(self.system_capabilities, key, value)

        self.broadcast_state_change("system_capabilities", kwargs)
        self.save_state()

    def update_user_config(self, **kwargs) -> None:
        """Update user configuration."""
        for key, value in kwargs.items():
            if hasattr(self.user_config, key):
                setattr(self.user_config, key, value)

        self.broadcast_state_change("user_config", kwargs)
        self.save_state()

    def register_ws_callback(self, callback: Callable) -> None:
        """Register callback for WebSocket broadcasting."""
        if callback not in self._broadcast_callbacks:
            self._broadcast_callbacks.append(callback)

    def unregister_ws_callback(self, callback: Callable) -> None:
        """Unregister WebSocket callback."""
        if callback in self._broadcast_callbacks:
            self._broadcast_callbacks.remove(callback)

    def broadcast_state_change(self, category: str, changes: Dict[str, Any]) -> None:
        """Broadcast state changes to all registered callbacks."""
        if not self.user_config.websocket_enabled:
            return

        message = {
            "type": "state_change",
            "category": category,
            "changes": changes,
            "timestamp": datetime.now().isoformat(),
            "correlation_id": self.correlation_id,
        }

        for callback in self._broadcast_callbacks:
            try:
                callback(message)
            except Exception as e:
                print(f"[StateManager] Broadcast callback failed: {e}")

    def get_full_state(self) -> Dict[str, Any]:
        """Get complete state snapshot."""
        return {
            "session_id": self.session_id,
            "interface_state": asdict(self.interface_state),
            "system_capabilities": asdict(self.system_capabilities),
            "user_config": asdict(self.user_config),
            "timestamp": datetime.now().isoformat(),
        }

    def detect_capabilities(self) -> None:
        """Auto-detect installed systems and extensions."""
        # Check for Tauri (uCode Markdown App)
        tauri_dir = Path("app/src-tauri")
        self.system_capabilities.has_tauri = tauri_dir.exists()

        # Check for MeshCore (now in library/ucode/)
        meshcore_dir = Path("library/ucode/meshcore")
        self.system_capabilities.has_meshcore = meshcore_dir.exists()

        # Check for Gemini API key
        from dev.goblin.core.config import Config

        config = Config()
        self.system_capabilities.has_gemini_api = bool(config.get_env("GEMINI_API_KEY"))

        # Scan extensions
        extensions_dir = Path("extensions")
        if extensions_dir.exists():
            extensions = []
            for ext_path in extensions_dir.glob("*/"):
                if ext_path.name not in ["__pycache__", "cloned"]:
                    extensions.append(ext_path.name)
            self.system_capabilities.extensions_loaded = extensions

        self.save_state()

    def new_correlation_id(self) -> str:
        """Generate new correlation ID for request tracking."""
        self.correlation_id = str(uuid.uuid4())
        return self.correlation_id

    def shutdown(self) -> None:
        """Clean shutdown - save state and cleanup."""
        self.save_state(force=True)
        self._ws_clients.clear()
        self._broadcast_callbacks.clear()


# Global singleton instance
_state_manager: Optional[StateManager] = None


def get_state_manager() -> StateManager:
    """Get or create the global StateManager instance."""
    global _state_manager
    if _state_manager is None:
        _state_manager = StateManager()
    return _state_manager


def initialize_state_manager() -> StateManager:
    """Initialize state manager and detect capabilities."""
    manager = get_state_manager()
    manager.detect_capabilities()
    return manager
