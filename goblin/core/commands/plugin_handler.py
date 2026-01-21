"""
PLUGIN Command Handler v1.1.0
Manages code containers + plugin discovery for uDOS.

Commands:
  PLUGIN LIST               - List installed code containers
  PLUGIN SCAN               - Discover all plugins (new in v1.1.0)
  PLUGIN DEPS <name>        - Show plugin dependencies (new in v1.1.0)
  PLUGIN VALIDATE           - Check all plugin dependencies (new in v1.1.0)
  PLUGIN STATUS [id]        - Show container status and version info
  PLUGIN INFO <id>          - Show detailed container/plugin information
  PLUGIN CLONE <id> <url>   - Clone a new container (Wizard only)
  PLUGIN UPDATE <id>        - Update container from source (Wizard only)
  PLUGIN PACKAGE <id>       - Package container for distribution (Wizard only)
  PLUGIN INSTALL <file>     - Install container from package (User device)
  PLUGIN VERIFY <id>        - Verify container integrity
  PLUGIN HELP               - Show this help

Architecture:
  - Plugin Discovery: Scans library/ and plugins/ for all available plugins
  - Code Containers: Wizard Server clones GitHub repos → packages as TCZ
  - Distribution: Private transport (mesh/QR/audio) to user devices

Security:
  - User devices NEVER access GitHub directly
  - Containers are READ-ONLY on user devices
  - All modifications go in uDOS wrapper layers
  - Updates require Wizard Server + private transport
"""

import json
import os
import subprocess
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, List, Optional

# Import plugin discovery system (v1.1.0+)
try:
    from wizard.github_integration import PluginDiscovery, PluginMetadata

    DISCOVERY_AVAILABLE = True
except ImportError:
    DISCOVERY_AVAILABLE = False

# Base paths
CONTAINERS_PATH = Path(__file__).parent.parent.parent / "extensions" / "cloned"
DISTRIBUTION_PATH = Path(__file__).parent.parent.parent / "distribution"
TRANSPORT_PATH = Path(__file__).parent.parent.parent / "extensions" / "transport"


class PluginHandler:
    """Handler for PLUGIN commands - Code Container management."""

    def __init__(self, viewport=None, logger=None):
        """
        Initialize plugin handler.

        Args:
            viewport: Output viewport for display
            logger: Session logger
        """
        self.viewport = viewport
        self.logger = logger
        self.containers_path = CONTAINERS_PATH
        self.distribution_path = DISTRIBUTION_PATH
        self.transport_path = TRANSPORT_PATH

        # Detect if running on Wizard Server (has web access)
        self.is_wizard = self._detect_wizard_mode()

        # Initialize plugin discovery system (v1.1.0+)
        self.discovery = None
        if DISCOVERY_AVAILABLE:
            try:
                self.discovery = PluginDiscovery()
                if self.logger:
                    self.logger.info("[WIZ] Plugin discovery system initialized")
            except Exception as e:
                if self.logger:
                    self.logger.warning(
                        f"[WIZ] Could not initialize plugin discovery: {e}"
                    )
                self.discovery = None

    def _detect_wizard_mode(self) -> bool:
        """
        Detect if running on Wizard Server.

        Returns:
            True if Wizard Server (has web access), False for user device
        """
        # Check for wizard marker file or environment variable
        wizard_marker = Path(__file__).parent.parent.parent / ".wizard"
        if wizard_marker.exists():
            return True
        if os.environ.get("UDOS_WIZARD_MODE") == "1":
            return True
        return False

    def handle_command(self, params: List[str]) -> str:
        """
        Route PLUGIN commands.

        Args:
            params: Command parameters

        Returns:
            Command result message
        """
        if not params or params[0].upper() == "HELP":
            return self._show_help()

        subcommand = params[0].upper()

        # v1.1.0 - Plugin Discovery Commands
        if subcommand == "SCAN":
            return self._scan_plugins(params[1:])

        elif subcommand == "DEPS":
            if len(params) < 2:
                return "❌ Usage: PLUGIN DEPS <plugin_name> [--recursive]"
            return self._show_dependencies(params[1:])

        elif subcommand == "VALIDATE":
            return self._validate_dependencies()

        # Original Container Management Commands
        elif subcommand == "LIST":
            return self._list_containers()

        elif subcommand == "STATUS":
            container_id = params[1] if len(params) > 1 else None
            return self._show_status(container_id)

        elif subcommand == "INFO":
            if len(params) < 2:
                return "❌ Usage: PLUGIN INFO <container_id>"
            return self._show_info(params[1])

        elif subcommand == "CLONE":
            if not self.is_wizard:
                return "❌ PLUGIN CLONE requires Wizard Server (web access)"
            if len(params) < 3:
                return "❌ Usage: PLUGIN CLONE <container_id> <github_url>"
            return self._clone_container(params[1], params[2])

        elif subcommand == "UPDATE":
            if not self.is_wizard:
                return "❌ PLUGIN UPDATE requires Wizard Server (web access)"
            if len(params) < 2:
                return "❌ Usage: PLUGIN UPDATE <container_id>"
            return self._update_container(params[1])

        elif subcommand == "PACKAGE":
            if not self.is_wizard:
                return "❌ PLUGIN PACKAGE requires Wizard Server"
            if len(params) < 2:
                return "❌ Usage: PLUGIN PACKAGE <container_id>"
            return self._package_container(params[1])

        elif subcommand == "INSTALL":
            if len(params) < 2:
                return "❌ Usage: PLUGIN INSTALL <package_file>"
            return self._install_package(params[1])

        elif subcommand == "VERIFY":
            if len(params) < 2:
                return "❌ Usage: PLUGIN VERIFY <container_id>"
            return self._verify_container(params[1])

        elif subcommand == "SEARCH":
            if len(params) < 2:
                return "❌ Usage: PLUGIN SEARCH <query>"
            return self._search_plugins(" ".join(params[1:]))

        elif subcommand == "REMOVE":
            if len(params) < 2:
                return "❌ Usage: PLUGIN REMOVE <container_id>"
            return self._remove_container(params[1])

        elif subcommand == "UPDATES":
            return self._check_updates()

        elif subcommand == "CATEGORIES":
            return self._list_categories()

        else:
            return f"❌ Unknown subcommand: {subcommand}\n\n" + self._show_help()

    # ═══════════════════════════════════════════════════════════════
    # Container Discovery
    # ═══════════════════════════════════════════════════════════════

    def _get_containers(self) -> Dict[str, Dict[str, Any]]:
        """
        Discover all installed code containers.

        Returns:
            Dict mapping container_id to container info
        """
        containers = {}

        if not self.containers_path.exists():
            return containers

        for item in self.containers_path.iterdir():
            if item.is_dir() and not item.name.startswith("."):
                manifest_path = item / "container.json"
                if manifest_path.exists():
                    try:
                        with open(manifest_path) as f:
                            manifest = json.load(f)
                        containers[item.name] = {
                            "path": item,
                            "manifest": manifest,
                            "has_git": (item / ".git").exists(),
                        }
                    except (json.JSONDecodeError, IOError) as e:
                        containers[item.name] = {
                            "path": item,
                            "manifest": None,
                            "error": str(e),
                            "has_git": (item / ".git").exists(),
                        }
                else:
                    # Directory exists but no manifest
                    containers[item.name] = {
                        "path": item,
                        "manifest": None,
                        "has_git": (item / ".git").exists(),
                    }

        return containers

    # ═══════════════════════════════════════════════════════════════
    # Command Handlers
    # ═══════════════════════════════════════════════════════════════

    def _list_containers(self) -> str:
        """List all installed code containers."""
        containers = self._get_containers()

        mode = "🧙 WIZARD" if self.is_wizard else "📱 USER DEVICE"

        lines = [
            "╔═══════════════════════════════════════════════════════════════╗",
            "║              CODE CONTAINERS (PLUGIN LIST)                    ║",
            f"║  Mode: {mode:<54}║",
            "╠═══════════════════════════════════════════════════════════════╣",
        ]

        if not containers:
            lines.append(
                "║  No containers installed                                      ║"
            )
        else:
            lines.append(
                "║  ID            │ Name                    │ Status             ║"
            )
            lines.append(
                "╟───────────────┼─────────────────────────┼────────────────────╢"
            )

            for cid, info in containers.items():
                manifest = info.get("manifest")
                if manifest and "container" in manifest:
                    name = manifest["container"].get("name", "Unknown")[:23]
                    has_git = "✓ git" if info.get("has_git") else "○ pkg"
                else:
                    name = "(no manifest)"
                    has_git = "? unknown"

                status = f"{has_git}"
                lines.append(f"║  {cid:<13}│ {name:<23} │ {status:<18} ║")

        lines.append(
            "╚═══════════════════════════════════════════════════════════════╝"
        )

        return "\n".join(lines)

    def _show_status(self, container_id: Optional[str] = None) -> str:
        """Show container status and version info."""
        containers = self._get_containers()

        if container_id:
            if container_id not in containers:
                return f"❌ Container not found: {container_id}"
            containers = {container_id: containers[container_id]}

        lines = []

        for cid, info in containers.items():
            manifest = info.get("manifest")
            path = info.get("path")

            lines.append(f"┌─ {cid} ─────────────────────────────────────────────")

            if manifest and "container" in manifest:
                c = manifest["container"]
                lines.append(f"│  Name:     {c.get('name', 'Unknown')}")
                lines.append(f"│  Source:   {c.get('source', 'Unknown')}")
                lines.append(f"│  Ref:      {c.get('ref', 'Unknown')}")
                lines.append(
                    f"│  Commit:   {c.get('commit', 'Not tracked')[:12] if c.get('commit') else 'Not tracked'}"
                )
                lines.append(f"│  Cloned:   {c.get('cloned_at', 'Unknown')}")
                lines.append(f"│  Updated:  {c.get('last_update', 'Unknown')}")

                # Check git status if available
                if info.get("has_git") and self.is_wizard:
                    git_status = self._get_git_status(path)
                    lines.append(f"│  Git:      {git_status}")
            else:
                lines.append(f"│  ⚠️  No manifest found")
                if info.get("has_git"):
                    lines.append(f"│  Git repo exists but needs manifest")

            # Check for wrapper
            wrapper_path = self.transport_path / cid
            if wrapper_path.exists():
                lines.append(
                    f"│  Wrapper:  ✓ {wrapper_path.relative_to(self.containers_path.parent.parent)}"
                )
            else:
                lines.append(f"│  Wrapper:  ○ Not found")

            lines.append(f"└───────────────────────────────────────────────────────")
            lines.append("")

        return "\n".join(lines)

    def _show_info(self, container_id: str) -> str:
        """Show detailed container information."""
        containers = self._get_containers()

        if container_id not in containers:
            return f"❌ Container not found: {container_id}"

        info = containers[container_id]
        manifest = info.get("manifest")

        if not manifest:
            return f"❌ No manifest for container: {container_id}"

        lines = [
            "╔═══════════════════════════════════════════════════════════════╗",
            f"║  CONTAINER: {container_id:<49}║",
            "╠═══════════════════════════════════════════════════════════════╣",
        ]

        # Container info
        if "container" in manifest:
            c = manifest["container"]
            lines.append(f"║  Name:        {c.get('name', 'Unknown'):<47}║")
            lines.append(f"║  Description: {c.get('description', 'N/A')[:47]:<47}║")
            lines.append(f"║  Type:        {c.get('type', 'Unknown'):<47}║")
            lines.append(f"║  Source:      {c.get('source', 'Unknown')[:47]:<47}║")
            lines.append(f"║  Ref:         {c.get('ref', 'main'):<47}║")

        lines.append(
            "╟───────────────────────────────────────────────────────────────╢"
        )

        # Policy info
        if "policy" in manifest:
            p = manifest["policy"]
            lines.append(
                f"║  Read-Only:   {'Yes' if p.get('read_only', True) else 'No':<47}║"
            )
            lines.append(
                f"║  Auto-Update: {'Yes' if p.get('auto_update', False) else 'No':<47}║"
            )
            lines.append(
                f"║  Channel:     {p.get('update_channel', 'wizard_only'):<47}║"
            )

        lines.append(
            "╟───────────────────────────────────────────────────────────────╢"
        )

        # Integration info
        if "integration" in manifest:
            i = manifest["integration"]
            lines.append(
                f"║  Wrapper:     {(i.get('wrapper_path') or 'None')[:47]:<47}║"
            )
            lines.append(
                f"║  Service:     {(i.get('service_path') or 'None')[:47]:<47}║"
            )
            lines.append(
                f"║  Handler:     {(i.get('handler_path') or 'None')[:47]:<47}║"
            )

        lines.append(
            "╚═══════════════════════════════════════════════════════════════╝"
        )

        return "\n".join(lines)

    def _clone_container(self, container_id: str, github_url: str) -> str:
        """
        Clone a new container from GitHub (Wizard Server only).

        Args:
            container_id: Unique container identifier
            github_url: GitHub repository URL

        Returns:
            Result message
        """
        if not self.is_wizard:
            return "❌ PLUGIN CLONE requires Wizard Server"

        container_path = self.containers_path / container_id

        if container_path.exists():
            return f"❌ Container already exists: {container_id}"

        # Clone the repository
        try:
            result = subprocess.run(
                ["git", "clone", github_url, str(container_path)],
                capture_output=True,
                text=True,
                timeout=120,
            )

            if result.returncode != 0:
                return f"❌ Clone failed: {result.stderr}"

            # Get commit hash
            commit_result = subprocess.run(
                ["git", "-C", str(container_path), "rev-parse", "HEAD"],
                capture_output=True,
                text=True,
            )
            commit = (
                commit_result.stdout.strip() if commit_result.returncode == 0 else None
            )

            # Create container manifest
            now = datetime.utcnow().isoformat() + "Z"
            manifest = {
                "container": {
                    "id": container_id,
                    "name": container_id.replace("-", " ").title(),
                    "description": f"Cloned from {github_url}",
                    "type": "git",
                    "source": github_url,
                    "ref": "main",
                    "cloned_at": now,
                    "last_update": now,
                    "commit": commit,
                    "version": None,
                },
                "policy": {
                    "read_only": True,
                    "auto_update": False,
                    "update_channel": "wizard_only",
                    "verify_signatures": False,
                },
                "integration": {
                    "wrapper_path": f"extensions/transport/{container_id}/",
                    "service_path": None,
                    "handler_path": None,
                    "install_script": None,
                },
                "metadata": {
                    "license": None,
                    "homepage": github_url,
                    "documentation": None,
                    "maintainer": "uDOS Wizard Server",
                },
            }

            manifest_path = container_path / "container.json"
            with open(manifest_path, "w") as f:
                json.dump(manifest, f, indent=2)

            return f"""✅ Container cloned successfully!

   ID:      {container_id}
   Source:  {github_url}
   Commit:  {commit[:12] if commit else 'Unknown'}
   Path:    {container_path}

Next steps:
   PLUGIN STATUS {container_id}  - Verify installation
   PLUGIN PACKAGE {container_id} - Create distribution package
"""

        except subprocess.TimeoutExpired:
            return "❌ Clone timed out (120s)"
        except Exception as e:
            return f"❌ Clone error: {e}"

    def _update_container(self, container_id: str) -> str:
        """
        Update container from source (Wizard Server only).

        Args:
            container_id: Container to update

        Returns:
            Result message
        """
        if not self.is_wizard:
            return "❌ PLUGIN UPDATE requires Wizard Server"

        container_path = self.containers_path / container_id

        if not container_path.exists():
            return f"❌ Container not found: {container_id}"

        if not (container_path / ".git").exists():
            return f"❌ Container is not a git repository: {container_id}"

        try:
            # Get current commit
            old_commit = subprocess.run(
                ["git", "-C", str(container_path), "rev-parse", "HEAD"],
                capture_output=True,
                text=True,
            ).stdout.strip()

            # Pull updates
            result = subprocess.run(
                ["git", "-C", str(container_path), "pull", "--ff-only"],
                capture_output=True,
                text=True,
                timeout=60,
            )

            if result.returncode != 0:
                return f"❌ Update failed: {result.stderr}"

            # Get new commit
            new_commit = subprocess.run(
                ["git", "-C", str(container_path), "rev-parse", "HEAD"],
                capture_output=True,
                text=True,
            ).stdout.strip()

            # Update manifest
            manifest_path = container_path / "container.json"
            if manifest_path.exists():
                with open(manifest_path) as f:
                    manifest = json.load(f)

                manifest["container"]["last_update"] = (
                    datetime.utcnow().isoformat() + "Z"
                )
                manifest["container"]["commit"] = new_commit

                with open(manifest_path, "w") as f:
                    json.dump(manifest, f, indent=2)

            if old_commit == new_commit:
                return f"✅ Container {container_id} is already up to date\n   Commit: {new_commit[:12]}"
            else:
                return f"""✅ Container {container_id} updated!

   Old:  {old_commit[:12]}
   New:  {new_commit[:12]}

Run PLUGIN PACKAGE {container_id} to create distribution package.
"""

        except subprocess.TimeoutExpired:
            return "❌ Update timed out (60s)"
        except Exception as e:
            return f"❌ Update error: {e}"

    def _package_container(self, container_id: str) -> str:
        """
        Package container for distribution (Wizard Server only).

        Args:
            container_id: Container to package

        Returns:
            Result message
        """
        if not self.is_wizard:
            return "❌ PLUGIN PACKAGE requires Wizard Server"

        container_path = self.containers_path / container_id

        if not container_path.exists():
            return f"❌ Container not found: {container_id}"

        # Ensure distribution directory exists
        self.distribution_path.mkdir(parents=True, exist_ok=True)

        # Get version from manifest
        manifest_path = container_path / "container.json"
        version = "0.0.0"
        if manifest_path.exists():
            try:
                with open(manifest_path) as f:
                    manifest = json.load(f)
                commit = manifest.get("container", {}).get("commit", "")[:8]
                version = commit if commit else "0.0.0"
            except:
                pass

        # Create tarball (TCZ-ready format)
        package_name = f"{container_id}-{version}.tar.gz"
        package_path = self.distribution_path / package_name

        try:
            result = subprocess.run(
                [
                    "tar",
                    "-czf",
                    str(package_path),
                    "-C",
                    str(self.containers_path),
                    container_id,
                ],
                capture_output=True,
                text=True,
                timeout=60,
            )

            if result.returncode != 0:
                return f"❌ Package failed: {result.stderr}"

            # Get package size
            size = package_path.stat().st_size
            size_str = (
                f"{size / 1024:.1f} KB"
                if size < 1024 * 1024
                else f"{size / 1024 / 1024:.1f} MB"
            )

            return f"""✅ Container packaged successfully!

   Package:  {package_name}
   Size:     {size_str}
   Path:     {package_path}

Distribution commands:
   QR SEND {package_path}      - Send via QR relay
   MESH SEND <device> {package_path}  - Send via mesh
   AUDIO SEND {package_path}   - Send via audio relay
"""

        except subprocess.TimeoutExpired:
            return "❌ Package timed out (60s)"
        except Exception as e:
            return f"❌ Package error: {e}"

    def _install_package(self, package_file: str) -> str:
        """
        Install container from package (User device).

        Args:
            package_file: Path to package file

        Returns:
            Result message
        """
        package_path = Path(package_file)

        if not package_path.exists():
            # Try distribution folder
            package_path = self.distribution_path / package_file
            if not package_path.exists():
                return f"❌ Package not found: {package_file}"

        if not package_path.name.endswith((".tar.gz", ".tgz")):
            return "❌ Package must be .tar.gz or .tgz format"

        try:
            # Extract to containers folder
            result = subprocess.run(
                ["tar", "-xzf", str(package_path), "-C", str(self.containers_path)],
                capture_output=True,
                text=True,
                timeout=60,
            )

            if result.returncode != 0:
                return f"❌ Install failed: {result.stderr}"

            # Get container name from package
            container_id = package_path.name.split("-")[0]

            return f"""✅ Container installed successfully!

   Package:   {package_path.name}
   Container: {container_id}
   Path:      {self.containers_path / container_id}

Run PLUGIN STATUS {container_id} to verify installation.
"""

        except subprocess.TimeoutExpired:
            return "❌ Install timed out (60s)"
        except Exception as e:
            return f"❌ Install error: {e}"

    def _verify_container(self, container_id: str) -> str:
        """
        Verify container integrity.

        Args:
            container_id: Container to verify

        Returns:
            Verification result
        """
        container_path = self.containers_path / container_id

        if not container_path.exists():
            return f"❌ Container not found: {container_id}"

        checks = []
        all_passed = True

        # Check manifest exists
        manifest_path = container_path / "container.json"
        if manifest_path.exists():
            checks.append("✓ container.json exists")
            try:
                with open(manifest_path) as f:
                    manifest = json.load(f)
                checks.append("✓ container.json is valid JSON")

                if "container" in manifest:
                    checks.append("✓ container section present")
                else:
                    checks.append("✗ missing container section")
                    all_passed = False

                if "policy" in manifest:
                    checks.append("✓ policy section present")
                else:
                    checks.append("○ policy section missing (optional)")

            except json.JSONDecodeError as e:
                checks.append(f"✗ Invalid JSON: {e}")
                all_passed = False
        else:
            checks.append("✗ container.json missing")
            all_passed = False

        # Check git status (if git repo)
        git_path = container_path / ".git"
        if git_path.exists():
            checks.append("✓ git repository present")

            # Check for uncommitted changes
            if self.is_wizard:
                result = subprocess.run(
                    ["git", "-C", str(container_path), "status", "--porcelain"],
                    capture_output=True,
                    text=True,
                )
                if result.stdout.strip():
                    checks.append("⚠ uncommitted changes detected")
                else:
                    checks.append("✓ no uncommitted changes")
        else:
            checks.append("○ not a git repository (installed from package)")

        # Check wrapper exists
        wrapper_path = self.transport_path / container_id
        if wrapper_path.exists():
            checks.append(f"✓ wrapper layer exists at {wrapper_path.name}")
        else:
            checks.append(f"○ no wrapper layer (extensions/transport/{container_id}/)")

        status = "✅ VERIFIED" if all_passed else "⚠️ ISSUES FOUND"

        return f"""
┌─ VERIFY: {container_id} ────────────────────────────────────
│
│  Status: {status}
│
│  Checks:
│    {chr(10) + '│    '.join(checks)}
│
└─────────────────────────────────────────────────────────────
"""

    def _get_git_status(self, path: Path) -> str:
        """Get git status summary for a container."""
        try:
            result = subprocess.run(
                ["git", "-C", str(path), "status", "--porcelain"],
                capture_output=True,
                text=True,
                timeout=5,
            )
            if result.returncode == 0:
                if result.stdout.strip():
                    return "dirty (uncommitted changes)"
                else:
                    return "clean"
            return "unknown"
        except:
            return "error"

    def _show_help(self) -> str:
        """Show PLUGIN command help."""
        mode = "🧙 WIZARD SERVER" if self.is_wizard else "📱 USER DEVICE"

        wizard_cmds = (
            """
  WIZARD-ONLY COMMANDS (requires web access):
  ────────────────────────────────────────────
  PLUGIN CLONE <id> <url>   Clone container from GitHub
  PLUGIN UPDATE <id>        Pull updates from source
  PLUGIN PACKAGE <id>       Create distribution package
"""
            if self.is_wizard
            else """
  ⚠️  Running on User Device - some commands unavailable
  ─────────────────────────────────────────────────────
  CLONE, UPDATE, PACKAGE require Wizard Server (web access)
"""
        )

        return f"""
╔═══════════════════════════════════════════════════════════════╗
║                  PLUGIN COMMAND HELP                          ║
║  Mode: {mode:<54}║
╚═══════════════════════════════════════════════════════════════╝

� PLUGIN DISCOVERY (NEW in v1.1.0)
─────────────────────────────────────────────────────────────────
  PLUGIN SCAN [--save path] Discover all plugins across tiers
  PLUGIN DEPS <name>        Show plugin dependencies
  PLUGIN DEPS <name> --recursive    Show all transitive deps
  PLUGIN DEPS <name> --reverse      Show what depends on plugin
  PLUGIN VALIDATE           Check all plugin dependencies

📦 CODE CONTAINER MANAGEMENT
─────────────────────────────────────────────────────────────────
  PLUGIN LIST               List installed containers
  PLUGIN STATUS [id]        Show container status
  PLUGIN INFO <id>          Show detailed information
  PLUGIN VERIFY <id>        Verify container integrity
  PLUGIN SEARCH <query>     Search available plugins
  PLUGIN CATEGORIES         List plugin categories
  PLUGIN UPDATES            Check for available updates
  PLUGIN REMOVE <id>        Remove a container

📥 INSTALLATION (User Device)
─────────────────────────────────────────────────────────────────
  PLUGIN INSTALL <file>     Install from package (.tar.gz)
{wizard_cmds}
🏗️ ARCHITECTURE
─────────────────────────────────────────────────────────────────
  Plugin Discovery: Scans library/ and plugins/ for all plugins
  Code Containers: Wizard clones GitHub → packages → distributes
  Transport: Private mesh/QR/audio only (no direct web access)
  
  User devices receive READ-ONLY containers.
  Modifications go in uDOS wrapper layers.

📚 EXAMPLES
─────────────────────────────────────────────────────────────────
  PLUGIN SCAN                        # Discover all plugins
  PLUGIN DEPS api                    # Show API dependencies
  PLUGIN DEPS api --recursive        # All transitive deps
  PLUGIN DEPS core --reverse         # What needs core?
  PLUGIN VALIDATE                    # Check all dependencies
  
  PLUGIN LIST
  PLUGIN STATUS meshcore
  PLUGIN INFO meshcore
  PLUGIN VERIFY meshcore
  PLUGIN SEARCH editor
  PLUGIN UPDATES
"""

    def _search_plugins(self, query: str) -> str:
        """Search for plugins by name or description."""
        containers = self._get_containers()

        query_lower = query.lower()
        results = []

        for cid, info in containers.items():
            manifest = info.get("manifest")
            if not manifest:
                continue

            container = manifest.get("container", {})
            name = container.get("name", cid)
            desc = container.get("description", "")
            category = manifest.get("metadata", {}).get("category", "")

            # Search in id, name, description, category
            if (
                query_lower in cid.lower()
                or query_lower in name.lower()
                or query_lower in desc.lower()
                or query_lower in category.lower()
            ):
                results.append(
                    {
                        "id": cid,
                        "name": name,
                        "description": desc[:50] + "..." if len(desc) > 50 else desc,
                        "category": category,
                    }
                )

        if not results:
            return f"🔍 No plugins found matching '{query}'"

        lines = [f"🔍 Search Results for '{query}'", "═" * 60]

        for r in results:
            lines.append(f"\n📦 {r['id']}")
            lines.append(f"   Name: {r['name']}")
            if r["category"]:
                lines.append(f"   Category: {r['category']}")
            lines.append(f"   {r['description']}")

        lines.append(f"\n📊 Found {len(results)} plugin(s)")
        return "\n".join(lines)

    def _remove_container(self, container_id: str) -> str:
        """Remove a container (user device only, not Wizard)."""
        container_path = self.containers_path / container_id

        if not container_path.exists():
            return f"❌ Container not found: {container_id}"

        # Check if it's a git repo (Wizard cloned)
        if (container_path / ".git").exists() and self.is_wizard:
            return (
                f"⚠️ Cannot remove git repository on Wizard Server\n"
                f"   Use git commands directly or remove .git first"
            )

        # Confirm removal
        import shutil

        try:
            shutil.rmtree(container_path)
            return f"✅ Removed container: {container_id}"
        except Exception as e:
            return f"❌ Failed to remove {container_id}: {e}"

    def _check_updates(self) -> str:
        """Check for available updates."""
        containers = self._get_containers()

        updates = []
        checked = 0

        for cid, info in containers.items():
            manifest = info.get("manifest")
            if not manifest:
                continue

            checked += 1
            container = manifest.get("container", {})

            # Check if git repo with remote
            if info.get("has_git") and self.is_wizard:
                try:
                    result = subprocess.run(
                        [
                            "git",
                            "-C",
                            str(info["path"]),
                            "remote",
                            "show",
                            "origin",
                            "-n",
                        ],
                        capture_output=True,
                        text=True,
                        timeout=5,
                    )
                    if "out of date" in result.stdout.lower():
                        updates.append(
                            {
                                "id": cid,
                                "name": container.get("name", cid),
                                "current": container.get("version", "unknown"),
                            }
                        )
                except:
                    pass

        if not updates:
            return f"✅ All {checked} plugins are up to date"

        lines = ["📥 Updates Available", "═" * 60]

        for u in updates:
            lines.append(f"\n📦 {u['id']}")
            lines.append(f"   Name: {u['name']}")
            lines.append(f"   Current: {u['current']}")

        if self.is_wizard:
            lines.append(f"\n💡 Run 'PLUGIN UPDATE <id>' to update")
        else:
            lines.append(f"\n💡 Request update from Wizard Server")

        return "\n".join(lines)

    def _list_categories(self) -> str:
        """List all plugin categories."""
        containers = self._get_containers()

        categories = {}

        for cid, info in containers.items():
            manifest = info.get("manifest")
            if not manifest:
                continue

            category = manifest.get("metadata", {}).get("category", "uncategorized")
            if category not in categories:
                categories[category] = []
            categories[category].append(cid)

        lines = ["📂 Plugin Categories", "═" * 60]

        for cat in sorted(categories.keys()):
            plugins = categories[cat]
            lines.append(f"\n{cat.upper()} ({len(plugins)})")
            for p in sorted(plugins):
                lines.append(f"  • {p}")

        return "\n".join(lines)

    # ═══════════════════════════════════════════════════════════════
    # Plugin Discovery Commands (v1.1.0+)
    # ═══════════════════════════════════════════════════════════════

    def _scan_plugins(self, params: List[str]) -> str:
        """
        PLUGIN SCAN - Discover all plugins across tiers.

        Args:
            params: Optional parameters (--save <path>)

        Returns:
            Formatted discovery results
        """
        if not self.discovery:
            return "❌ Plugin discovery system not available"

        if self.logger:
            self.logger.info("[WIZ] Starting plugin scan...")

        try:
            # Discover all plugins
            plugins = self.discovery.discover_all()

            # Check for --save parameter
            save_path = None
            if "--save" in params:
                idx = params.index("--save")
                if idx + 1 < len(params):
                    save_path = Path(params[idx + 1])

            # Save registry if requested
            if save_path:
                self.discovery.save_registry(save_path)
                if self.logger:
                    self.logger.info(f"[WIZ] Registry saved to {save_path}")
            else:
                # Default save location
                default_path = Path("memory/plugin-registry.json")
                self.discovery.save_registry(default_path)

            # Format output
            output = self.discovery.format_plugin_list()

            if self.logger:
                self.logger.info(f"[WIZ] Discovered {len(plugins)} plugins")

            return output

        except Exception as e:
            error_msg = f"❌ Plugin scan failed: {e}"
            if self.logger:
                self.logger.error(f"[WIZ] {error_msg}")
            return error_msg

    def _show_dependencies(self, params: List[str]) -> str:
        """
        PLUGIN DEPS - Show plugin dependencies.

        Args:
            params: [plugin_name, --recursive, --reverse]

        Returns:
            Formatted dependency tree
        """
        if not self.discovery:
            return "❌ Plugin discovery system not available"

        plugin_name = params[0]
        recursive = "--recursive" in params
        reverse = "--reverse" in params

        try:
            # Get plugin
            plugin = self.discovery.get_plugin(plugin_name)
            if not plugin:
                return f"❌ Plugin '{plugin_name}' not found\n\n💡 Run 'PLUGIN SCAN' to discover plugins"

            lines = [f"📦 Dependencies for '{plugin_name}'", "═" * 60, ""]

            if reverse:
                # Show what depends on this plugin
                dependents = self.discovery.get_dependents(plugin_name)
                if dependents:
                    lines.append(f"⬆️  Plugins depending on '{plugin_name}':")
                    for dep in dependents:
                        lines.append(f"  • {dep}")
                else:
                    lines.append(f"ℹ️  No plugins depend on '{plugin_name}'")
            else:
                # Show what this plugin depends on
                deps = self.discovery.get_dependencies(plugin_name, recursive=recursive)
                if deps:
                    mode = "recursive" if recursive else "direct"
                    lines.append(f"⬇️  {mode.capitalize()} dependencies:")
                    for dep in deps:
                        lines.append(f"  • {dep}")
                else:
                    lines.append(f"ℹ️  '{plugin_name}' has no dependencies")

            return "\n".join(lines)

        except Exception as e:
            error_msg = f"❌ Could not get dependencies: {e}"
            if self.logger:
                self.logger.error(f"[WIZ] {error_msg}")
            return error_msg

    def _validate_dependencies(self) -> str:
        """
        PLUGIN VALIDATE - Check all plugin dependencies.

        Returns:
            Validation report
        """
        if not self.discovery:
            return "❌ Plugin discovery system not available"

        if self.logger:
            self.logger.info("[WIZ] Validating plugin dependencies...")

        try:
            # Run validation
            missing = self.discovery.validate_dependencies()

            lines = ["🔍 Plugin Dependency Validation", "═" * 60, ""]

            if not missing:
                lines.append("✅ All plugin dependencies are satisfied!")
                lines.append(f"\nℹ️  Validated {len(self.discovery.plugins)} plugins")
            else:
                lines.append(
                    f"❌ Found {len(missing)} plugins with missing dependencies:\n"
                )
                for plugin_name, missing_deps in missing.items():
                    lines.append(f"📦 {plugin_name}")
                    for dep in missing_deps:
                        lines.append(f"   ❌ Missing: {dep}")
                    lines.append("")

                lines.append("💡 To fix:")
                lines.append("   1. Run 'PLUGIN SCAN' to update registry")
                lines.append("   2. Install missing plugins via Wizard Server")
                lines.append("   3. Run 'PLUGIN VALIDATE' again")

            if self.logger:
                if missing:
                    self.logger.warning(
                        f"[WIZ] Validation failed: {len(missing)} plugins with missing deps"
                    )
                else:
                    self.logger.info("[WIZ] Validation passed")

            return "\n".join(lines)

        except Exception as e:
            error_msg = f"❌ Validation failed: {e}"
            if self.logger:
                self.logger.error(f"[WIZ] {error_msg}")
            return error_msg
