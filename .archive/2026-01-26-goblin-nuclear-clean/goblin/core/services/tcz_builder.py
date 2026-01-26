"""
⚠️ DEPRECATED: uDOS TCZ Package Builder
========================================

**Status:** DEPRECATED — Use APKBuilder instead
**Date:** 2026-01-24
**Migration:** See docs/decisions/ADR-0003-alpine-linux-migration.md

This module is kept for backwards compatibility only.
uDOS has migrated from TinyCore to Alpine Linux.

Use instead:
    from wizard.services.plugin_factory import APKBuilder
    builder = APKBuilder()
    builder.build_apk('core')

Legacy Usage (DO NOT USE):
    from dev.goblin.core.services.tcz_builder import TCZBuilder

    builder = TCZBuilder()  # ← Will raise deprecation warning
    builder.build_package('core')      # Build udos-core.tcz

Author: uDOS Team
Version: v1.0.0.14 (DEPRECATED)
"""

import warnings
import hashlib
import json
import os
import shutil
import subprocess
import tarfile
import tempfile
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

# Deprecation warning on module import
warnings.warn(
    "dev.goblin.core.services.tcz_builder is deprecated. "
    "Use wizard.services.plugin_factory.APKBuilder for Alpine packages. "
    "See docs/decisions/ADR-0003-alpine-linux-migration.md",
    DeprecationWarning,
    stacklevel=2,
)


class BuildResult(Enum):
    """Build result status."""

    SUCCESS = "success"
    FAILED = "failed"
    SKIPPED = "skipped"


@dataclass
class PackageSpec:
    """Specification for a TCZ package."""

    id: str
    name: str
    description: str
    version: str
    include_paths: List[str]
    exclude_patterns: List[str] = field(default_factory=list)
    dependencies: List[str] = field(default_factory=list)
    pip_deps: List[str] = field(default_factory=list)
    install_script: Optional[str] = None
    post_install: Optional[str] = None


@dataclass
class BuildProgress:
    """Build progress tracking."""

    package_id: str
    total_steps: int
    current_step: int
    current_task: str
    status: str


class TCZBuilder:
    """
    Builds TCZ packages for uDOS components.

    Supports building individual packages or all packages defined
    in the stack definitions.
    """

    # Package specifications
    PACKAGE_SPECS = {
        "core": PackageSpec(
            id="core",
            name="udos-core",
            description="uDOS Core System - TUI, uPY, commands",
            version="1.0.0.13",
            include_paths=[
                "core/",
                "bin/",
                "start_udos.sh",
                "uDOS.py",
                "requirements.txt",
            ],
            exclude_patterns=[
                "__pycache__",
                "*.pyc",
                ".DS_Store",
                "*.egg-info",
                ".pytest_cache",
            ],
            dependencies=[
                "python3.9.tcz",
                "python3.9-pip.tcz",
            ],
            pip_deps=[
                "prompt_toolkit",
                "pyyaml",
                "rich",
            ],
        ),
        "knowledge": PackageSpec(
            id="knowledge",
            name="udos-knowledge",
            description="uDOS Knowledge Bank - 230+ survival guides",
            version="1.0.0.0",
            include_paths=[
                "knowledge/",
            ],
            exclude_patterns=[
                "__pycache__",
                ".DS_Store",
            ],
            dependencies=[
                "udos-core.tcz",
            ],
        ),
        "ai": PackageSpec(
            id="ai",
            name="udos-ai",
            description="uDOS AI Assistant - Gemini integration",
            version="1.0.0.0",
            include_paths=[
                "core/services/gemini_generator.py",
                "core/commands/ok_handler.py",
                "core/commands/make_handler.py",
            ],
            dependencies=[
                "udos-core.tcz",
            ],
            pip_deps=[
                "google-generativeai",
            ],
        ),
        "transport": PackageSpec(
            id="transport",
            name="udos-transport",
            description="uDOS Private Transports - QR, Audio, MeshCore",
            version="1.0.0.0",
            include_paths=[
                "extensions/transport/",
                "core/commands/qr_handler.py",
                "core/commands/audio_handler.py",
            ],
            dependencies=[
                "udos-core.tcz",
            ],
            pip_deps=[
                "qrcode",
                "pyzbar",
                "pyaudio",
            ],
        ),
        "graphics": PackageSpec(
            id="graphics",
            name="udos-graphics",
            description="uDOS Graphics - Fonts, ASCII art, Teletext",
            version="1.0.0.0",
            include_paths=[
                "core/services/graphics_library.py",
                "core/services/graphics_compositor.py",
                "core/services/ascii_generator.py",
                "core/data/fonts/",
            ],
            dependencies=[
                "udos-core.tcz",
            ],
            pip_deps=[
                "pillow",
            ],
        ),
        "gameplay": PackageSpec(
            id="gameplay",
            name="udos-gameplay",
            description="uDOS Gameplay - XP, maps, quests",
            version="1.0.0.0",
            include_paths=[
                "extensions/play/",
                "core/services/mission_manager.py",
                "core/commands/map_command_handler.py",
            ],
            dependencies=[
                "udos-core.tcz",
                "udos-graphics.tcz",
            ],
        ),
        "cloud": PackageSpec(
            id="cloud",
            name="udos-cloud",
            description="uDOS Cloud Extensions - Groups, sharing, tunnels",
            version="1.0.0.0",
            include_paths=[
                "extensions/cloud/",
            ],
            exclude_patterns=[
                "__pycache__",
                "*.pyc",
            ],
            dependencies=[
                "udos-core.tcz",
            ],
            pip_deps=[
                "fastapi",
                "uvicorn",
                "sqlalchemy",
            ],
        ),
        "wizard": PackageSpec(
            id="wizard",
            name="udos-wizard",
            description="uDOS Wizard Server - Web proxy, Gmail relay",
            version="1.0.0.0",
            include_paths=[
                "extensions/wizard_server/",
                "extensions/api/",
            ],
            dependencies=[
                "udos-core.tcz",
                "udos-cloud.tcz",
            ],
            pip_deps=[
                "aiohttp",
                "beautifulsoup4",
                "google-api-python-client",
            ],
        ),
    }

    def __init__(self, workspace_root: Optional[str] = None):
        """Initialize the TCZ builder."""
        if workspace_root:
            self.workspace_root = Path(workspace_root).resolve()
        else:
            current = Path(__file__).resolve()
            while current.parent != current:
                if (current / "core").exists():
                    self.workspace_root = current
                    break
                current = current.parent
            else:
                self.workspace_root = Path.cwd()

        self.output_dir = self.workspace_root / "distribution" / "tcz"
        self.build_dir = self.workspace_root / "distribution" / ".build"

        # Ensure output directory exists
        self.output_dir.mkdir(parents=True, exist_ok=True)

        # Progress callback
        self.progress_callback: Optional[callable] = None

    def get_package_spec(self, package_id: str) -> Optional[PackageSpec]:
        """Get specification for a package."""
        return self.PACKAGE_SPECS.get(package_id)

    def list_packages(self) -> List[str]:
        """List all available package IDs."""
        return list(self.PACKAGE_SPECS.keys())

    def build_package(
        self,
        package_id: str,
        output_dir: Optional[Path] = None,
        include_deps: bool = False,
    ) -> Tuple[BuildResult, str]:
        """
        Build a single TCZ package.

        Args:
            package_id: ID of the package to build
            output_dir: Override output directory
            include_deps: Also build dependency packages

        Returns:
            Tuple of (BuildResult, output_path or error_message)
        """
        spec = self.get_package_spec(package_id)
        if not spec:
            return BuildResult.FAILED, f"Unknown package: {package_id}"

        output = output_dir or self.output_dir

        # Build dependencies first if requested
        if include_deps:
            for dep in spec.dependencies:
                dep_id = dep.replace("udos-", "").replace(".tcz", "")
                if dep_id in self.PACKAGE_SPECS:
                    self.build_package(dep_id, output)

        try:
            return self._build_tcz(spec, output)
        except Exception as e:
            return BuildResult.FAILED, str(e)

    def _build_tcz(
        self, spec: PackageSpec, output_dir: Path
    ) -> Tuple[BuildResult, str]:
        """Build the actual TCZ package."""
        # Create temporary build directory
        build_path = self.build_dir / spec.name
        if build_path.exists():
            shutil.rmtree(build_path)
        build_path.mkdir(parents=True)

        progress = BuildProgress(
            package_id=spec.id,
            total_steps=6,
            current_step=0,
            current_task="Starting",
            status="building",
        )

        try:
            # Step 1: Create directory structure
            progress.current_step = 1
            progress.current_task = "Creating structure"
            self._report_progress(progress)

            pkg_root = build_path / "opt" / "udos"
            pkg_root.mkdir(parents=True)
            (build_path / "usr" / "local" / "tce.installed").mkdir(parents=True)

            # Step 2: Copy files
            progress.current_step = 2
            progress.current_task = "Copying files"
            self._report_progress(progress)

            for include_path in spec.include_paths:
                src = self.workspace_root / include_path
                if src.is_file():
                    dst = pkg_root / include_path
                    dst.parent.mkdir(parents=True, exist_ok=True)
                    shutil.copy2(src, dst)
                elif src.is_dir():
                    dst = pkg_root / include_path
                    shutil.copytree(
                        src, dst, ignore=shutil.ignore_patterns(*spec.exclude_patterns)
                    )

            # Step 3: Create install script
            progress.current_step = 3
            progress.current_task = "Creating install script"
            self._report_progress(progress)

            install_script = self._generate_install_script(spec)
            install_path = build_path / "usr" / "local" / "tce.installed" / spec.name
            install_path.write_text(install_script)
            install_path.chmod(0o755)

            # Step 4: Create manifest
            progress.current_step = 4
            progress.current_task = "Creating manifest"
            self._report_progress(progress)

            manifest = self._generate_manifest(spec, build_path)
            (pkg_root / "MANIFEST.json").write_text(json.dumps(manifest, indent=2))

            # Step 5: Build package
            progress.current_step = 5
            progress.current_task = "Building package"
            self._report_progress(progress)

            tcz_path = output_dir / f"{spec.name}.tcz"

            # Check for mksquashfs (required for native TCZ)
            if shutil.which("mksquashfs"):
                # Build native TCZ
                subprocess.run(
                    [
                        "mksquashfs",
                        str(build_path),
                        str(tcz_path),
                        "-noappend",
                        "-comp",
                        "xz",
                    ],
                    check=True,
                    capture_output=True,
                )
            else:
                # Create tar.gz as fallback
                tcz_path = output_dir / f"{spec.name}.tar.gz"
                with tarfile.open(tcz_path, "w:gz") as tar:
                    tar.add(build_path, arcname="")

            # Step 6: Generate metadata files
            progress.current_step = 6
            progress.current_task = "Generating metadata"
            self._report_progress(progress)

            # MD5 checksum
            md5_hash = self._calculate_md5(tcz_path)
            (output_dir / f"{spec.name}.tcz.md5.txt").write_text(
                f"{md5_hash}  {spec.name}.tcz\n"
            )

            # Dependencies file
            if spec.dependencies:
                (output_dir / f"{spec.name}.tcz.dep").write_text(
                    "\n".join(spec.dependencies) + "\n"
                )

            # Info file
            info = (
                f"{spec.name}.tcz\n"
                f"Title:\t\t{spec.description}\n"
                f"Description:\t{spec.description}\n"
                f"Version:\t{spec.version}\n"
                f"Author:\t\tuDOS Team\n"
                f"Original-site:\thttps://github.com/udos-project/uDOS\n"
                f"Copying-policy:\tMIT\n"
                f"Size:\t\t{tcz_path.stat().st_size // 1024}K\n"
            )
            (output_dir / f"{spec.name}.tcz.info").write_text(info)

            progress.status = "complete"
            self._report_progress(progress)

            return BuildResult.SUCCESS, str(tcz_path)

        finally:
            # Cleanup build directory
            if build_path.exists():
                shutil.rmtree(build_path)

    def _generate_install_script(self, spec: PackageSpec) -> str:
        """Generate the post-install script for the package."""
        lines = [
            "#!/bin/sh",
            f"# Post-install script for {spec.name}",
            "",
        ]

        # Add pip dependencies
        if spec.pip_deps:
            lines.extend(
                [
                    "# Install Python dependencies",
                    "if [ -f /opt/udos/.venv/bin/pip ]; then",
                    f'    /opt/udos/.venv/bin/pip install {" ".join(spec.pip_deps)}',
                    "fi",
                    "",
                ]
            )

        # Add custom install script
        if spec.install_script:
            lines.extend(
                [
                    "# Custom install commands",
                    spec.install_script,
                    "",
                ]
            )

        # Add post-install commands
        if spec.post_install:
            lines.extend(
                [
                    "# Post-install commands",
                    spec.post_install,
                    "",
                ]
            )

        lines.extend(
            [
                f'echo "{spec.name} installed successfully"',
            ]
        )

        return "\n".join(lines)

    def _generate_manifest(self, spec: PackageSpec, build_path: Path) -> Dict[str, Any]:
        """Generate the package manifest."""
        # Count files
        file_count = 0
        total_size = 0
        for root, dirs, files in os.walk(build_path):
            for f in files:
                file_count += 1
                total_size += (Path(root) / f).stat().st_size

        return {
            "package": spec.name,
            "version": spec.version,
            "description": spec.description,
            "dependencies": spec.dependencies,
            "pip_dependencies": spec.pip_deps,
            "files": file_count,
            "size": total_size,
            "built": __import__("datetime").datetime.now().isoformat(),
        }

    def _calculate_md5(self, file_path: Path) -> str:
        """Calculate MD5 checksum of a file."""
        md5 = hashlib.md5()
        with open(file_path, "rb") as f:
            for chunk in iter(lambda: f.read(8192), b""):
                md5.update(chunk)
        return md5.hexdigest()

    def _report_progress(self, progress: BuildProgress) -> None:
        """Report build progress."""
        if self.progress_callback:
            self.progress_callback(progress)

    def build_all(
        self, output_dir: Optional[Path] = None
    ) -> Dict[str, Tuple[BuildResult, str]]:
        """
        Build all packages.

        Returns:
            Dict mapping package_id to (result, path_or_error)
        """
        output = output_dir or self.output_dir
        results = {}

        # Build in dependency order
        build_order = [
            "core",
            "knowledge",
            "ai",
            "graphics",
            "transport",
            "gameplay",
            "cloud",
            "wizard",
        ]

        for package_id in build_order:
            result, message = self.build_package(package_id, output)
            results[package_id] = (result, message)

            if result == BuildResult.FAILED:
                print(f"  ❌ {package_id}: {message}")
            else:
                print(f"  ✅ {package_id}: {message}")

        return results

    def get_build_summary(self) -> str:
        """Get a summary of available packages to build."""
        lines = [
            "╔══════════════════════════════════════════════════════════════╗",
            "║                  TCZ Package Builder                         ║",
            "╠══════════════════════════════════════════════════════════════╣",
        ]

        for pkg_id, spec in self.PACKAGE_SPECS.items():
            lines.append(f"║  {spec.name:<20} v{spec.version:<10}           ║")
            lines.append(f"║    {spec.description[:50]:<50}  ║")
            if spec.dependencies:
                deps = ", ".join(d.replace(".tcz", "") for d in spec.dependencies)
                lines.append(f"║    Deps: {deps[:48]:<48}  ║")
            lines.append(
                f"╟──────────────────────────────────────────────────────────────╢"
            )

        lines[-1] = "╚══════════════════════════════════════════════════════════════╝"

        return "\n".join(lines)


# CLI interface
if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="uDOS TCZ Package Builder")
    parser.add_argument(
        "action",
        choices=["list", "build", "build-all", "info"],
        help="Action to perform",
    )
    parser.add_argument("package", nargs="?", help="Package ID to build")
    parser.add_argument("--output", "-o", type=Path, help="Output directory")
    parser.add_argument("--deps", action="store_true", help="Also build dependencies")

    args = parser.parse_args()

    builder = TCZBuilder()

    if args.action == "list":
        print("\nAvailable packages:")
        for pkg_id in builder.list_packages():
            spec = builder.get_package_spec(pkg_id)
            print(f"  {pkg_id:<12} - {spec.description}")

    elif args.action == "info":
        print(builder.get_build_summary())

    elif args.action == "build":
        if not args.package:
            print("Error: Package ID required for build")
            exit(1)

        def progress_cb(p):
            print(f"  [{p.current_step}/{p.total_steps}] {p.current_task}")

        builder.progress_callback = progress_cb

        print(f"\nBuilding {args.package}...")
        result, message = builder.build_package(
            args.package, args.output, include_deps=args.deps
        )
        print(f"\nResult: {result.value}")
        print(f"Output: {message}")

    elif args.action == "build-all":
        print("\nBuilding all packages...")
        results = builder.build_all(args.output)

        success = sum(1 for r, _ in results.values() if r == BuildResult.SUCCESS)
        print(f"\n{success}/{len(results)} packages built successfully")
