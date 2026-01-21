"""
Install Command Handler for uDOS
================================

Handles INSTALL.* commands for TCZ package management.
Provides TUI interface for the TCZ installer service.

Commands:
- INSTALL <package>     - Install a TCZ package
- INSTALL LIST          - List installed packages
- INSTALL CHECK         - Check for updates
- INSTALL REMOVE <name> - Remove installed package
- INSTALL VERIFY <path> - Verify package integrity
- INSTALL STATUS        - Show installer status
- INSTALL HELP          - Show help

Author: uDOS Team
Version: 1.0.0.0
"""

from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from dev.goblin.core.services.logging_manager import get_logger
from dev.goblin.core.services.tcz_installer import (
    TCZInstaller,
    InstallStatus,
    VerifyResult,
    SystemType,
)

logger = get_logger("command-install")


class InstallHandler:
    """
    Handler for INSTALL commands.

    Provides TUI interface for TCZ package installation on
    Tiny Core Linux and compatibility mode on other systems.
    """

    def __init__(self, workspace_root: str):
        """
        Initialize handler.

        Args:
            workspace_root: uDOS workspace root path
        """
        self.workspace_root = Path(workspace_root)
        self.installer = TCZInstaller(workspace_root)

        # Subcommand dispatch
        self.subcommands = {
            "LIST": self._handle_list,
            "CHECK": self._handle_check,
            "REMOVE": self._handle_remove,
            "VERIFY": self._handle_verify,
            "STATUS": self._handle_status,
            "HELP": self._handle_help,
        }

    def handle_command(self, args: List[str]) -> Dict[str, Any]:
        """
        Handle INSTALL command.

        Args:
            args: Command arguments

        Returns:
            Result dictionary with 'content' and 'success' keys
        """
        if not args:
            return self._handle_help([])

        # Check for subcommand
        subcommand = args[0].upper()

        if subcommand in self.subcommands:
            return self.subcommands[subcommand](args[1:])
        else:
            # Assume it's a package path
            return self._handle_install(args)

    def _handle_install(self, args: List[str]) -> Dict[str, Any]:
        """Install a TCZ package."""
        if not args:
            return {
                "success": False,
                "content": self._format_error(
                    "No package specified", "INSTALL <package_path>"
                ),
            }

        package_path = args[0]

        # Resolve path
        path = Path(package_path)
        if not path.is_absolute():
            # Try relative to workspace
            path = self.workspace_root / package_path

        if not path.exists():
            # Try distribution/plugins
            path = self.workspace_root / "distribution/plugins" / package_path
            if not path.exists():
                return {
                    "success": False,
                    "content": self._format_error(
                        f"Package not found: {package_path}",
                        "Use PLUGIN LIST to see available packages",
                    ),
                }

        # Install
        logger.info(f"[LOCAL] Installing package: {path}")
        result = self.installer.install(str(path))

        if result.success:
            pkg = result.package
            content = self._format_success(
                f"Package '{pkg.name}' installed successfully",
                [
                    f"Version: {pkg.version}",
                    f"Location: {pkg.install_path}",
                    f"Status: {pkg.status.value}",
                ],
            )
            if result.warnings:
                content += "\n\n⚠️  Warnings:\n"
                for warning in result.warnings:
                    content += f"   • {warning}\n"
            return {"success": True, "content": content}
        else:
            return {
                "success": False,
                "content": self._format_error(result.error or "Installation failed"),
            }

    def _handle_list(self, args: List[str]) -> Dict[str, Any]:
        """List installed packages."""
        packages = self.installer.list_installed()

        if not packages:
            return {
                "success": True,
                "content": self._format_info(
                    "No packages installed",
                    [
                        "Use INSTALL <package> to install a package",
                        "Use PLUGIN LIST to see available packages",
                    ],
                ),
            }

        lines = [
            "┌─────────────────────────────────────────────────────────────────────────────┐"
        ]
        lines.append(
            "│ INSTALLED PACKAGES                                                          │"
        )
        lines.append(
            "├─────────────────────────────────────────────────────────────────────────────┤"
        )

        for pkg in packages:
            status_icon = (
                "✅"
                if pkg.status == InstallStatus.INSTALLED
                else "🔵" if pkg.status == InstallStatus.MOUNTED else "⚠️"
            )
            name_ver = f"{pkg.name} v{pkg.version}"
            lines.append(f"│ {status_icon} {name_ver:<30} {pkg.status.value:<12} │")
            lines.append(f"│    Path: {pkg.install_path:<52} │")
            lines.append(f"│    Installed: {pkg.install_date[:10]:<47} │")
            lines.append(
                "├─────────────────────────────────────────────────────────────────────────────┤"
            )

        lines[-1] = (
            "└─────────────────────────────────────────────────────────────────────────────┘"
        )

        lines.append("")
        lines.append(f"Total: {len(packages)} packages installed")
        lines.append(f"System: {self.installer.system_type.value}")

        return {"success": True, "content": "\n".join(lines)}

    def _handle_check(self, args: List[str]) -> Dict[str, Any]:
        """Check for package updates."""
        updates = self.installer.check_updates()

        if not updates:
            return {
                "success": True,
                "content": self._format_success(
                    "All packages are up to date",
                    [f"Checked {len(self.installer.registry)} packages"],
                ),
            }

        lines = [
            "┌─────────────────────────────────────────────────────────────────────────────┐"
        ]
        lines.append(
            "│ AVAILABLE UPDATES                                                           │"
        )
        lines.append(
            "├─────────────────────────────────────────────────────────────────────────────┤"
        )

        for name, new_version in updates.items():
            old_version = self.installer.registry[name].version
            lines.append(f"│ 📦 {name:<30} {old_version} → {new_version:<15} │")

        lines.append(
            "└─────────────────────────────────────────────────────────────────────────────┘"
        )
        lines.append("")
        lines.append(f"💡 Use INSTALL <package> to update")

        return {"success": True, "content": "\n".join(lines)}

    def _handle_remove(self, args: List[str]) -> Dict[str, Any]:
        """Remove an installed package."""
        if not args:
            return {
                "success": False,
                "content": self._format_error(
                    "No package specified", "INSTALL REMOVE <package_name>"
                ),
            }

        package_name = args[0]

        logger.info(f"[LOCAL] Removing package: {package_name}")
        result = self.installer.uninstall(package_name)

        if result.success:
            return {
                "success": True,
                "content": self._format_success(f"Package '{package_name}' removed"),
            }
        else:
            return {
                "success": False,
                "content": self._format_error(result.error or "Removal failed"),
            }

    def _handle_verify(self, args: List[str]) -> Dict[str, Any]:
        """Verify a package's integrity."""
        if not args:
            return {
                "success": False,
                "content": self._format_error(
                    "No package path specified", "INSTALL VERIFY <package_path>"
                ),
            }

        package_path = args[0]

        # Resolve path
        path = Path(package_path)
        if not path.is_absolute():
            path = self.workspace_root / package_path

        if not path.exists():
            return {
                "success": False,
                "content": self._format_error(f"Package not found: {package_path}"),
            }

        result, info = self.installer.verify_package(str(path))

        if result == VerifyResult.VALID:
            lines = [
                "┌─────────────────────────────────────────────────────────────────────────────┐",
                "│ ✅ PACKAGE VERIFICATION PASSED                                              │",
                "├─────────────────────────────────────────────────────────────────────────────┤",
            ]
            if info:
                lines.append(f"│ Name: {info.name:<58} │")
                lines.append(f"│ Version: {info.version:<55} │")
                lines.append(
                    f"│ Size: {info.size:,} bytes{' ' * (50 - len(str(info.size)))}│"
                )
                lines.append(f"│ Checksum: {info.checksum[:32]}...{' ' * 18} │")
                if info.dependencies:
                    lines.append(
                        f"│ Dependencies: {', '.join(info.dependencies):<47} │"
                    )
            lines.append(
                "└─────────────────────────────────────────────────────────────────────────────┘"
            )

            return {"success": True, "content": "\n".join(lines)}
        else:
            return {
                "success": False,
                "content": self._format_error(
                    f"Package verification failed: {result.value}",
                    "Package may be corrupted or tampered with",
                ),
            }

    def _handle_status(self, args: List[str]) -> Dict[str, Any]:
        """Show installer status."""
        lines = [
            "┌─────────────────────────────────────────────────────────────────────────────┐"
        ]
        lines.append(
            "│ TCZ INSTALLER STATUS                                                        │"
        )
        lines.append(
            "├─────────────────────────────────────────────────────────────────────────────┤"
        )

        # System info
        system_icons = {
            SystemType.TINY_CORE: "🐧",
            SystemType.LINUX: "🐧",
            SystemType.MACOS: "🍎",
            SystemType.WINDOWS: "🪟",
        }
        icon = system_icons.get(self.installer.system_type, "💻")
        lines.append(f"│ {icon} System Type: {self.installer.system_type.value:<48} │")
        lines.append(f"│ 📁 Install Base: {str(self.installer.install_base):<44} │")
        lines.append(f"│ 📦 Packages Dir: {str(self.installer.packages_dir):<44} │")
        lines.append(
            "├─────────────────────────────────────────────────────────────────────────────┤"
        )

        # Package stats
        total = len(self.installer.registry)
        mounted = sum(
            1
            for p in self.installer.registry.values()
            if p.status == InstallStatus.MOUNTED
        )
        installed = sum(
            1
            for p in self.installer.registry.values()
            if p.status == InstallStatus.INSTALLED
        )

        lines.append(f"│ Total Packages: {total:<51} │")
        lines.append(f"│   Mounted (TCZ): {mounted:<50} │")
        lines.append(f"│   Extracted: {installed:<54} │")
        lines.append(
            "├─────────────────────────────────────────────────────────────────────────────┤"
        )

        # Capabilities
        lines.append(
            "│ Capabilities:                                                               │"
        )
        if self.installer.system_type == SystemType.TINY_CORE:
            lines.append(
                "│   ✅ Native TCZ mounting                                                    │"
            )
            lines.append(
                "│   ✅ tce-load integration                                                   │"
            )
            lines.append(
                "│   ✅ Persistence via onboot.lst                                             │"
            )
        else:
            lines.append(
                "│   ⚠️  Compatibility mode (extraction-based)                                 │"
            )
            lines.append(
                "│   ✅ Package verification                                                   │"
            )
            lines.append(
                "│   ✅ Dependency tracking                                                    │"
            )

        lines.append(
            "└─────────────────────────────────────────────────────────────────────────────┘"
        )

        return {"success": True, "content": "\n".join(lines)}

    def _handle_help(self, args: List[str]) -> Dict[str, Any]:
        """Show help."""
        help_text = """
┌─────────────────────────────────────────────────────────────────────────────┐
│ INSTALL COMMANDS                                                            │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│ INSTALL <package>      Install a TCZ package                                │
│                        Example: INSTALL meshcore.tcz                        │
│                                                                             │
│ INSTALL LIST           List all installed packages                          │
│                                                                             │
│ INSTALL CHECK          Check for available updates                          │
│                                                                             │
│ INSTALL REMOVE <name>  Remove an installed package                          │
│                        Example: INSTALL REMOVE meshcore                     │
│                                                                             │
│ INSTALL VERIFY <path>  Verify package integrity                             │
│                        Checks checksum and manifest                         │
│                                                                             │
│ INSTALL STATUS         Show installer status and capabilities               │
│                                                                             │
│ INSTALL HELP           Show this help                                       │
│                                                                             │
├─────────────────────────────────────────────────────────────────────────────┤
│ Notes:                                                                      │
│ • On Tiny Core: Uses native TCZ mounting via tce-load                       │
│ • On Other Systems: Extracts packages to local directory                    │
│ • Use PLUGIN commands to manage plugin repositories                         │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
"""
        return {"success": True, "content": help_text.strip()}

    # ========================================================================
    # Formatting Helpers
    # ========================================================================

    def _format_error(self, message: str, hint: str = None) -> str:
        """Format error message."""
        lines = ["", f"❌ Error: {message}"]
        if hint:
            lines.append(f"   💡 {hint}")
        lines.append("")
        return "\n".join(lines)

    def _format_success(self, message: str, details: List[str] = None) -> str:
        """Format success message."""
        lines = ["", f"✅ {message}"]
        if details:
            for detail in details:
                lines.append(f"   • {detail}")
        lines.append("")
        return "\n".join(lines)

    def _format_info(self, message: str, hints: List[str] = None) -> str:
        """Format info message."""
        lines = ["", f"ℹ️  {message}"]
        if hints:
            lines.append("")
            for hint in hints:
                lines.append(f"   💡 {hint}")
        lines.append("")
        return "\n".join(lines)


# ============================================================================
# Module-level handler function
# ============================================================================

_handler_instance = None


def get_handler(workspace_root: str) -> InstallHandler:
    """Get or create handler instance."""
    global _handler_instance
    if _handler_instance is None:
        _handler_instance = InstallHandler(workspace_root)
    return _handler_instance


def handle_command(workspace_root: str, args: List[str]) -> Dict[str, Any]:
    """Handle INSTALL command."""
    handler = get_handler(workspace_root)
    return handler.handle_command(args)
