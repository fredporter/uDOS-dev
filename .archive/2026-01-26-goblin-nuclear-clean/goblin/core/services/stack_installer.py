"""
uDOS Stack Installer Service
============================
Capability-based installation using stack definitions.

Usage:
    from dev.goblin.core.services.stack_installer import StackInstaller

    installer = StackInstaller()
    installer.install_stack('lite')  # Install Lite tier
    installer.list_stacks()          # Show available stacks
    installer.get_stack_info('full') # Get stack details

Author: uDOS Team
Version: v1.0.0.13
"""

import json
import os
import subprocess
import sys
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional


class InstallResult(Enum):
    """Installation result status."""

    SUCCESS = "success"
    PARTIAL = "partial"
    FAILED = "failed"
    CANCELLED = "cancelled"


@dataclass
class StackInfo:
    """Information about an installation stack."""

    id: str
    name: str
    description: str
    size_mb: int
    components: List[str]
    tcz_packages: List[str]
    pip_extras: List[str]
    features: Dict[str, bool]
    requires: Dict[str, Any]
    best_for: List[str]
    is_default: bool = False
    realm: Optional[str] = None


@dataclass
class ComponentInfo:
    """Information about a component."""

    id: str
    name: str
    description: str
    size_mb: int
    tcz: Optional[str] = None
    app: Optional[str] = None
    required: bool = False
    pip_deps: List[str] = field(default_factory=list)
    system_deps: List[str] = field(default_factory=list)
    realm: Optional[str] = None


@dataclass
class InstallProgress:
    """Installation progress tracking."""

    stack_id: str
    total_steps: int
    current_step: int
    current_component: str
    status: str
    errors: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)


class StackInstaller:
    """
    Capability-based stack installer for uDOS.

    Reads stack definitions from distribution/stacks/stacks.json
    and installs components based on selected tier.
    """

    def __init__(self, workspace_root: Optional[str] = None):
        """Initialize the stack installer."""
        if workspace_root:
            self.workspace_root = Path(workspace_root).resolve()
        else:
            # Try to find workspace root
            current = Path(__file__).resolve()
            while current.parent != current:
                if (current / "core").exists() and (current / "distribution").exists():
                    self.workspace_root = current
                    break
                current = current.parent
            else:
                self.workspace_root = Path.cwd()

        self.stacks_file = (
            self.workspace_root / "distribution" / "stacks" / "stacks.json"
        )
        self.install_base = self.workspace_root / "distribution" / "tcz"
        self.packages_dir = self.workspace_root / "distribution" / "plugins"

        # Detect system type
        self.system_type = self._detect_system()

        # Load stack definitions
        self.stacks: Dict[str, StackInfo] = {}
        self.components: Dict[str, ComponentInfo] = {}
        self._load_stacks()

        # Progress callback
        self.progress_callback: Optional[callable] = None

    def _detect_system(self) -> str:
        """Detect the operating system type."""
        if os.path.exists("/etc/os-release"):
            with open("/etc/os-release") as f:
                content = f.read()
                if "Tiny Core" in content or "tinycore" in content.lower():
                    return "tinycore"
                return "linux"
        elif sys.platform == "darwin":
            return "macos"
        elif sys.platform == "win32":
            return "windows"
        return "unknown"

    def _load_stacks(self) -> None:
        """Load stack definitions from JSON file."""
        if not self.stacks_file.exists():
            return

        try:
            with open(self.stacks_file) as f:
                data = json.load(f)

            # Load stacks
            for stack_id, stack_data in data.get("stacks", {}).items():
                self.stacks[stack_id] = StackInfo(
                    id=stack_data["id"],
                    name=stack_data["name"],
                    description=stack_data["description"],
                    size_mb=stack_data["size_mb"],
                    components=stack_data["components"],
                    tcz_packages=stack_data.get("tcz_packages", []),
                    pip_extras=stack_data.get("pip_extras", []),
                    features=stack_data["features"],
                    requires=stack_data["requires"],
                    best_for=stack_data.get("best_for", []),
                    is_default=stack_data.get("default", False),
                    realm=stack_data.get("realm"),
                )

            # Load components
            for comp_id, comp_data in data.get("components", {}).items():
                self.components[comp_id] = ComponentInfo(
                    id=comp_data["id"],
                    name=comp_data["name"],
                    description=comp_data["description"],
                    size_mb=comp_data["size_mb"],
                    tcz=comp_data.get("tcz"),
                    app=comp_data.get("app"),
                    required=comp_data.get("required", False),
                    pip_deps=comp_data.get("pip_deps", []),
                    system_deps=comp_data.get("system_deps", []),
                    realm=comp_data.get("realm"),
                )
        except Exception as e:
            print(f"Error loading stacks: {e}")

    def list_stacks(self) -> List[StackInfo]:
        """List all available stacks."""
        return list(self.stacks.values())

    def get_stack(self, stack_id: str) -> Optional[StackInfo]:
        """Get information about a specific stack."""
        return self.stacks.get(stack_id)

    def get_default_stack(self) -> Optional[StackInfo]:
        """Get the default stack (lite)."""
        for stack in self.stacks.values():
            if stack.is_default:
                return stack
        return self.stacks.get("lite")

    def get_component(self, comp_id: str) -> Optional[ComponentInfo]:
        """Get information about a specific component."""
        return self.components.get(comp_id)

    def check_requirements(self, stack_id: str) -> Dict[str, Any]:
        """
        Check if system meets stack requirements.

        Returns:
            Dict with 'met', 'missing', 'warnings' keys
        """
        stack = self.get_stack(stack_id)
        if not stack:
            return {"met": False, "missing": ["Stack not found"], "warnings": []}

        result = {"met": True, "missing": [], "warnings": []}
        requires = stack.requires

        # Check Python version
        if "python" in requires:
            import re

            req_version = requires["python"].replace(">=", "")
            current = f"{sys.version_info.major}.{sys.version_info.minor}"
            if current < req_version:
                result["met"] = False
                result["missing"].append(
                    f"Python {requires['python']} (have {current})"
                )

        # Check storage
        if "storage_mb" in requires:
            # Simple check - could be more sophisticated
            result["warnings"].append(f"Requires {requires['storage_mb']}MB storage")

        # Check internet requirement
        if "internet" in requires:
            if requires["internet"] == "required" or requires["internet"] is True:
                result["warnings"].append("Internet connection required")

        # Check API keys
        if "api_keys" in requires:
            for key in requires["api_keys"]:
                key_name = key.split(" ")[0]  # Handle "KEY (optional)"
                if key_name not in os.environ:
                    if "optional" in key.lower():
                        result["warnings"].append(f"API key recommended: {key_name}")
                    else:
                        result["warnings"].append(f"API key required: {key_name}")

        # Check system dependencies
        if "system_deps" in requires:
            for dep in requires["system_deps"]:
                # Try to find the dependency
                found = self._check_system_dep(dep)
                if not found:
                    result["warnings"].append(f"System dependency: {dep}")

        # Check platform
        if "platform" in requires:
            current_platform = self.system_type
            if current_platform not in requires["platform"]:
                result["met"] = False
                result["missing"].append(f"Platform: {requires['platform']}")

        return result

    def _check_system_dep(self, dep: str) -> bool:
        """Check if a system dependency is available."""
        try:
            if self.system_type == "macos":
                result = subprocess.run(
                    ["brew", "list", dep], capture_output=True, timeout=5
                )
                return result.returncode == 0
            elif self.system_type in ["linux", "tinycore"]:
                result = subprocess.run(["which", dep], capture_output=True, timeout=5)
                return result.returncode == 0
        except:
            pass
        return False

    def install_stack(
        self, stack_id: str, target_path: Optional[Path] = None, skip_deps: bool = False
    ) -> InstallResult:
        """
        Install a stack.

        Args:
            stack_id: ID of the stack to install
            target_path: Installation target (default: workspace)
            skip_deps: Skip pip dependency installation

        Returns:
            InstallResult enum
        """
        stack = self.get_stack(stack_id)
        if not stack:
            return InstallResult.FAILED

        target = target_path or self.workspace_root
        errors = []

        # Calculate total steps
        total_steps = len(stack.components)
        if stack.pip_extras and not skip_deps:
            total_steps += 1

        progress = InstallProgress(
            stack_id=stack_id,
            total_steps=total_steps,
            current_step=0,
            current_component="",
            status="starting",
        )

        self._report_progress(progress)

        # Install components
        for i, comp_id in enumerate(stack.components):
            component = self.get_component(comp_id)
            if not component:
                errors.append(f"Component not found: {comp_id}")
                continue

            progress.current_step = i + 1
            progress.current_component = component.name
            progress.status = f"Installing {component.name}"
            self._report_progress(progress)

            try:
                self._install_component(component, target)
            except Exception as e:
                errors.append(f"Failed to install {comp_id}: {e}")

        # Install pip dependencies
        if stack.pip_extras and not skip_deps:
            progress.current_step = total_steps
            progress.current_component = "pip dependencies"
            progress.status = "Installing Python packages"
            self._report_progress(progress)

            try:
                self._install_pip_deps(stack.pip_extras)
            except Exception as e:
                errors.append(f"Failed to install pip deps: {e}")

        progress.status = "complete"
        progress.errors = errors
        self._report_progress(progress)

        if errors:
            return (
                InstallResult.PARTIAL
                if progress.current_step > 0
                else InstallResult.FAILED
            )
        return InstallResult.SUCCESS

    def _install_component(self, component: ComponentInfo, target: Path) -> None:
        """Install a single component."""
        if component.tcz:
            tcz_path = self.install_base / component.tcz
            if tcz_path.exists():
                self._install_tcz(tcz_path, target)
            else:
                # Component might be built-in (part of workspace)
                pass

    def _install_tcz(self, tcz_path: Path, target: Path) -> None:
        """Install a TCZ package."""
        if self.system_type == "tinycore":
            # Native TCZ loading
            subprocess.run(["tce-load", "-i", str(tcz_path)], check=True)
        else:
            # Extract to target
            from dev.goblin.core.services.tcz_installer import TCZInstaller

            installer = TCZInstaller(str(target))
            installer.install_package(str(tcz_path))

    def _install_pip_deps(self, packages: List[str]) -> None:
        """Install pip dependencies."""
        if not packages:
            return

        cmd = [sys.executable, "-m", "pip", "install"] + packages
        subprocess.run(cmd, check=True, capture_output=True)

    def _report_progress(self, progress: InstallProgress) -> None:
        """Report installation progress."""
        if self.progress_callback:
            self.progress_callback(progress)

    def get_stack_comparison(self) -> str:
        """Get a formatted comparison table of all stacks."""
        lines = [
            "╔════════════════════════════════════════════════════════════════════════════╗",
            "║                        uDOS Installation Stacks                            ║",
            "╠════════════════════════════════════════════════════════════════════════════╣",
        ]

        # Header row
        lines.append(
            "║ Feature              │ Ultra │ Lite  │ Std   │ Full  │ Enter │ Wizard ║"
        )
        lines.append(
            "╠══════════════════════╪═══════╪═══════╪═══════╪═══════╪═══════╪════════╣"
        )

        # Size row
        sizes = ["8MB", "16MB", "28MB", "58MB", "120MB", "95MB"]
        lines.append(
            f"║ Size                 │ {sizes[0]:^5} │ {sizes[1]:^5} │ {sizes[2]:^5} │ {sizes[3]:^5} │ {sizes[4]:^5} │ {sizes[5]:^6} ║"
        )

        # Feature rows
        features = [
            ("Core System", "core_system"),
            ("Knowledge Base", "knowledge_base"),
            ("AI Assistant", "ai_assistant"),
            ("Graphics", "graphics"),
            ("Gameplay", "gameplay"),
            ("Transport", "transport"),
            ("Cloud", "cloud"),
            ("Wizard Server", "wizard_server"),
        ]

        stack_order = ["ultra", "lite", "standard", "full", "enterprise", "wizard"]

        for feature_name, feature_key in features:
            row = f"║ {feature_name:<20} │"
            for stack_id in stack_order:
                stack = self.stacks.get(stack_id)
                if stack and stack.features.get(feature_key, False):
                    mark = "  ✅  "
                else:
                    mark = "  ❌  "
                row += f" {mark}│" if stack_id != "wizard" else f" {mark} ║"
            lines.append(row)

        lines.append(
            "╚════════════════════════════════════════════════════════════════════════════╝"
        )

        return "\n".join(lines)

    def get_stack_details(self, stack_id: str) -> str:
        """Get detailed information about a stack."""
        stack = self.get_stack(stack_id)
        if not stack:
            return f"Stack not found: {stack_id}"

        lines = [
            f"╔══════════════════════════════════════════════════════════════╗",
            f"║  {stack.name:^56}  ║",
            f"╠══════════════════════════════════════════════════════════════╣",
            f"║  {stack.description:<56}  ║",
            f"╠══════════════════════════════════════════════════════════════╣",
            f"║  Size: {stack.size_mb}MB                                               ║",
            f"║  Components: {', '.join(stack.components):<43}  ║",
        ]

        if stack.realm:
            lines.append(f"║  Realm: {stack.realm:<49}  ║")

        lines.append(
            f"╠══════════════════════════════════════════════════════════════╣"
        )
        lines.append(
            f"║  Features:                                                   ║"
        )

        for feature, enabled in stack.features.items():
            status = "✅" if enabled else "❌"
            feature_name = feature.replace("_", " ").title()
            lines.append(f"║    {status} {feature_name:<52}  ║")

        lines.append(
            f"╠══════════════════════════════════════════════════════════════╣"
        )
        lines.append(
            f"║  Best For:                                                   ║"
        )

        for use_case in stack.best_for[:4]:
            lines.append(f"║    • {use_case:<52}  ║")

        lines.append(
            f"╚══════════════════════════════════════════════════════════════╝"
        )

        return "\n".join(lines)


# CLI interface
if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="uDOS Stack Installer")
    parser.add_argument(
        "action",
        choices=["list", "info", "check", "install", "compare"],
        help="Action to perform",
    )
    parser.add_argument(
        "stack", nargs="?", default="lite", help="Stack ID (default: lite)"
    )
    parser.add_argument(
        "--skip-deps", action="store_true", help="Skip pip dependency installation"
    )

    args = parser.parse_args()

    installer = StackInstaller()

    if args.action == "list":
        print("\nAvailable Stacks:")
        print("-" * 60)
        for stack in installer.list_stacks():
            default = " (DEFAULT)" if stack.is_default else ""
            print(f"  {stack.id:<12} {stack.name:<15} {stack.size_mb:>3}MB{default}")
            print(f"               {stack.description}")
            print()

    elif args.action == "info":
        print(installer.get_stack_details(args.stack))

    elif args.action == "check":
        result = installer.check_requirements(args.stack)
        print(f"\nRequirements for '{args.stack}':")
        print(f"  Met: {'✅ Yes' if result['met'] else '❌ No'}")
        if result["missing"]:
            print(f"  Missing: {', '.join(result['missing'])}")
        if result["warnings"]:
            print(f"  Warnings:")
            for w in result["warnings"]:
                print(f"    ⚠️  {w}")

    elif args.action == "install":

        def progress_cb(p):
            print(f"  [{p.current_step}/{p.total_steps}] {p.status}")

        installer.progress_callback = progress_cb
        print(f"\nInstalling stack: {args.stack}")
        result = installer.install_stack(args.stack, skip_deps=args.skip_deps)
        print(f"Result: {result.value}")

    elif args.action == "compare":
        print(installer.get_stack_comparison())
