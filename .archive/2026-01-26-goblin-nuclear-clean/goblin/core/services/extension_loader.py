"""
Extension Loader

Loads system and user extensions following Alpine APK plugin model.

Note: TCZ plugin support is deprecated. Use APK packages for Alpine Linux.
See docs/decisions/ADR-0003-alpine-linux-migration.md
"""

import json
import importlib.util
from pathlib import Path
from typing import Dict, List, Optional, Any
import sys

from ..config.paths import get_system_path, get_user_path


class ExtensionManifest:
    """Parsed extension manifest."""

    def __init__(self, data: Dict[str, Any]):
        self.id = data["id"]
        self.version = data["version"]
        self.name = data["name"]
        self.description = data.get("description", "")
        self.author = data.get("author", "Unknown")
        self.license = data.get("license", "Unknown")

        # Compatibility
        compat = data.get("compatibility", {})
        self.udos_version = compat.get("udos_version", ">=1.0.0")
        self.platforms = compat.get("platforms", [])
        self.requires_gui = compat.get("requires_gui", False)

        # Dependencies (Alpine APK format preferred)
        deps = data.get("dependencies", {})
        # tcz_deps is deprecated, use apk_deps instead
        self.tcz_deps = deps.get("tcz", [])  # DEPRECATED
        self.apk_deps = deps.get("apk", [])  # Preferred for Alpine
        self.python_deps = deps.get("python", [])

        # Permissions
        self.permissions = data.get("permissions", [])

        # Entry points
        entry = data.get("entry_points", {})
        self.commands = entry.get("commands", [])
        self.hooks = entry.get("hooks", [])
        self.services = entry.get("services", [])


class ExtensionLoader:
    """
    Loads extensions from system and user directories.

    System extensions: /opt/udos/lib/extensions/ (trusted)
    User extensions: ~/.udos/memory/sandbox/extensions/ (sandboxed)
    """

    def __init__(self):
        # Extension directories
        system_base = get_system_path("lib")
        if not system_base.exists():
            # Development mode - use extensions/ in project root
            system_base = get_system_path("extensions")

        self.system_extensions = (
            system_base / "extensions"
            if (system_base / "extensions").exists()
            else system_base
        )
        self.user_extensions = get_user_path("sandbox/extensions")

        # Loaded extensions
        self.loaded: Dict[str, Dict[str, Any]] = {}

        # Registered command handlers
        self.command_handlers: Dict[str, Any] = {}

        # Hooks
        self.hooks: Dict[str, List[callable]] = {}

    def load_all(self) -> None:
        """Load all extensions (system then user)."""
        print("[ExtensionLoader] Loading extensions...")

        # System extensions (trusted)
        if self.system_extensions.exists():
            for manifest_file in self.system_extensions.glob("*/extension.json"):
                try:
                    self.load_extension(manifest_file, trusted=True)
                except Exception as e:
                    print(
                        f"[WARN] Failed to load system extension {manifest_file}: {e}"
                    )

        # User extensions (sandboxed)
        if self.user_extensions.exists():
            for manifest_file in self.user_extensions.glob("*/extension.json"):
                try:
                    self.load_extension(manifest_file, trusted=False)
                except Exception as e:
                    print(f"[WARN] Failed to load user extension {manifest_file}: {e}")

        print(f"[ExtensionLoader] Loaded {len(self.loaded)} extensions")

    def load_extension(self, manifest_path: Path, trusted: bool = False) -> None:
        """
        Load single extension.

        Args:
            manifest_path: Path to extension.json
            trusted: Whether extension is trusted (system extension)
        """
        # Parse manifest
        manifest_data = json.loads(manifest_path.read_text())
        manifest = ExtensionManifest(manifest_data)

        ext_id = manifest.id
        ext_dir = manifest_path.parent

        # Validate permissions for user extensions
        if not trusted:
            self._validate_permissions(manifest.permissions)

        # Check if already loaded
        if ext_id in self.loaded:
            print(f"[WARN] Extension {ext_id} already loaded, skipping")
            return

        # Load Python module if exists
        module = None
        init_file = ext_dir / "__init__.py"

        if init_file.exists():
            try:
                # Load module
                spec = importlib.util.spec_from_file_location(ext_id, init_file)
                module = importlib.util.module_from_spec(spec)
                sys.modules[ext_id] = module
                spec.loader.exec_module(module)

                # Call setup if exists
                if hasattr(module, "setup"):
                    module.setup()

            except Exception as e:
                print(f"[ERROR] Failed to load extension module {ext_id}: {e}")
                return

        # Register extension
        self.loaded[ext_id] = {
            "manifest": manifest,
            "module": module,
            "trusted": trusted,
            "path": ext_dir,
        }

        # Register commands
        for command in manifest.commands:
            self._register_command(command, module)

        # Register hooks
        for hook in manifest.hooks:
            self._register_hook(hook, module)

        print(
            f"[ExtensionLoader] Loaded extension: {manifest.name} v{manifest.version}"
        )

    def _validate_permissions(self, permissions: List[str]) -> None:
        """
        Validate requested permissions for user extensions.

        Args:
            permissions: List of permission strings

        Raises:
            SecurityError: If permission not allowed
        """
        allowed_permissions = [
            "filesystem:sandbox",  # Access to user sandbox only
            "api:commands",  # Register commands
            "network:private",  # Mesh networking only
        ]

        for perm in permissions:
            # Check exact match or prefix match for sandbox paths
            if perm not in allowed_permissions:
                if not perm.startswith("filesystem:sandbox/"):
                    raise SecurityError(
                        f"Permission not allowed for user extensions: {perm}"
                    )

    def _register_command(self, command_name: str, module: Any) -> None:
        """Register command handler from extension."""
        if module and hasattr(module, "handle_command"):
            self.command_handlers[command_name] = module.handle_command
            print(f"[ExtensionLoader] Registered command: {command_name}")

    def _register_hook(self, hook_name: str, module: Any) -> None:
        """Register hook from extension."""
        if module and hasattr(module, f"hook_{hook_name}"):
            if hook_name not in self.hooks:
                self.hooks[hook_name] = []
            self.hooks[hook_name].append(getattr(module, f"hook_{hook_name}"))
            print(f"[ExtensionLoader] Registered hook: {hook_name}")

    def get_extension(self, ext_id: str) -> Optional[Dict[str, Any]]:
        """Get loaded extension by ID."""
        return self.loaded.get(ext_id)

    def list_extensions(self) -> List[Dict[str, Any]]:
        """List all loaded extensions."""
        return [
            {
                "id": ext_id,
                "name": ext["manifest"].name,
                "version": ext["manifest"].version,
                "trusted": ext["trusted"],
            }
            for ext_id, ext in self.loaded.items()
        ]

    def call_hooks(self, hook_name: str, *args, **kwargs) -> List[Any]:
        """
        Call all registered hooks.

        Args:
            hook_name: Hook name
            *args, **kwargs: Arguments to pass to hooks

        Returns:
            List of return values from hooks
        """
        results = []
        for hook in self.hooks.get(hook_name, []):
            try:
                result = hook(*args, **kwargs)
                results.append(result)
            except Exception as e:
                print(f"[ERROR] Hook {hook_name} failed: {e}")
        return results


class SecurityError(Exception):
    """Extension security violation."""

    pass


# Singleton instance
_extension_loader = None


def get_extension_loader() -> ExtensionLoader:
    """Get singleton ExtensionLoader instance."""
    global _extension_loader
    if _extension_loader is None:
        _extension_loader = ExtensionLoader()
    return _extension_loader
