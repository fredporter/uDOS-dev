"""
⚠️ DEPRECATED: TCZ Installer Service for uDOS
=============================================

**Status:** DEPRECATED — Use APK packages instead
**Date:** 2026-01-24
**Migration:** See docs/decisions/ADR-0003-alpine-linux-migration.md

This module is kept for backwards compatibility only.
uDOS has migrated from TinyCore to Alpine Linux.

For Alpine Linux:
    # Use APK package manager
    apk add udos-core

    # Or use unified installer
    ./bin/install.sh

Legacy Usage (DO NOT USE):
    Handles Tiny Core Linux extension (.tcz) installation and management.

Author: uDOS Team
Version: 1.0.0.0 (DEPRECATED)
"""

import warnings
import hashlib
import json
import os
import shutil
import subprocess
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Dict, List, Optional

# Deprecation warning on module import
warnings.warn(
    "dev.goblin.core.services.tcz_installer is deprecated. "
    "uDOS uses Alpine APK packages. Use 'apk add udos-*' instead. "
    "See docs/decisions/ADR-0003-alpine-linux-migration.md",
    DeprecationWarning,
    stacklevel=2,
)

# ============================================================================
# Enums
# ============================================================================


class SystemType(Enum):
    """Target system type."""

    TINY_CORE = "tinycore"  # Native TCZ support
    LINUX = "linux"  # Extract to /opt
    MACOS = "macos"  # Extract to ~/Library/Application Support
    WINDOWS = "windows"  # Extract to AppData


class InstallStatus(Enum):
    """Installation status."""

    NOT_INSTALLED = "not_installed"
    INSTALLED = "installed"
    MOUNTED = "mounted"
    FAILED = "failed"
    PENDING = "pending"


class VerifyResult(Enum):
    """Package verification result."""

    VALID = "valid"
    INVALID_CHECKSUM = "invalid_checksum"
    INVALID_SIGNATURE = "invalid_signature"
    MISSING_MANIFEST = "missing_manifest"
    CORRUPTED = "corrupted"


# ============================================================================
# Data Classes
# ============================================================================


@dataclass
class PackageInfo:
    """TCZ package information."""

    name: str
    version: str
    checksum: str
    size: int
    dependencies: List[str] = field(default_factory=list)
    provides: List[str] = field(default_factory=list)
    description: str = ""
    author: str = ""
    license: str = ""
    build_date: str = ""

    def to_dict(self) -> Dict:
        return {
            "name": self.name,
            "version": self.version,
            "checksum": self.checksum,
            "size": self.size,
            "dependencies": self.dependencies,
            "provides": self.provides,
            "description": self.description,
            "author": self.author,
            "license": self.license,
            "build_date": self.build_date,
        }


@dataclass
class InstalledPackage:
    """Installed package record."""

    name: str
    version: str
    install_path: str
    install_date: str
    status: InstallStatus
    system_type: SystemType
    checksum: str
    mount_point: Optional[str] = None

    def to_dict(self) -> Dict:
        return {
            "name": self.name,
            "version": self.version,
            "install_path": self.install_path,
            "install_date": self.install_date,
            "status": self.status.value,
            "system_type": self.system_type.value,
            "checksum": self.checksum,
            "mount_point": self.mount_point,
        }

    @classmethod
    def from_dict(cls, data: Dict) -> "InstalledPackage":
        return cls(
            name=data["name"],
            version=data["version"],
            install_path=data["install_path"],
            install_date=data["install_date"],
            status=InstallStatus(data["status"]),
            system_type=SystemType(data["system_type"]),
            checksum=data["checksum"],
            mount_point=data.get("mount_point"),
        )


@dataclass
class InstallResult:
    """Installation result."""

    success: bool
    package: Optional[InstalledPackage] = None
    error: Optional[str] = None
    warnings: List[str] = field(default_factory=list)


# ============================================================================
# TCZ Installer Service
# ============================================================================


class TCZInstaller:
    """
    Manages TCZ package installation across different system types.

    On Tiny Core Linux:
    - Uses native tce-load for installation
    - Mounts squashfs packages
    - Integrates with /usr/local/tce.installed

    On other systems:
    - Extracts to platform-appropriate location
    - Manages symlinks for binary access
    - Tracks installations in local database
    """

    def __init__(self, workspace_root: str):
        """
        Initialize installer.

        Args:
            workspace_root: uDOS workspace root path
        """
        self.workspace_root = Path(workspace_root)
        self.system_type = self._detect_system()

        # Paths based on system type
        if self.system_type == SystemType.TINY_CORE:
            self.install_base = Path("/usr/local/tce.installed")
            self.packages_dir = Path("/etc/sysconfig/tcedir/optional")
        elif self.system_type == SystemType.MACOS:
            self.install_base = (
                Path.home() / "Library/Application Support/uDOS/packages"
            )
            self.packages_dir = self.workspace_root / "distribution/plugins"
        elif self.system_type == SystemType.LINUX:
            self.install_base = Path.home() / ".local/share/uDOS/packages"
            self.packages_dir = self.workspace_root / "distribution/plugins"
        else:  # Windows
            self.install_base = Path(os.environ.get("APPDATA", "")) / "uDOS/packages"
            self.packages_dir = self.workspace_root / "distribution/plugins"

        # Registry for tracking installations
        self.registry_path = self.workspace_root / "memory/extensions/installed.json"
        self.registry: Dict[str, InstalledPackage] = {}

        # Ensure directories exist
        self.install_base.mkdir(parents=True, exist_ok=True)
        self.packages_dir.mkdir(parents=True, exist_ok=True)
        self.registry_path.parent.mkdir(parents=True, exist_ok=True)

        self._load_registry()

    def _detect_system(self) -> SystemType:
        """Detect current system type."""
        import platform

        system = platform.system().lower()

        if system == "linux":
            # Check for Tiny Core
            if os.path.exists("/etc/sysconfig/tcedir"):
                return SystemType.TINY_CORE
            return SystemType.LINUX
        elif system == "darwin":
            return SystemType.MACOS
        elif system == "windows":
            return SystemType.WINDOWS
        else:
            return SystemType.LINUX  # Default fallback

    def _load_registry(self):
        """Load installation registry."""
        if self.registry_path.exists():
            try:
                with open(self.registry_path) as f:
                    data = json.load(f)
                    self.registry = {
                        name: InstalledPackage.from_dict(info)
                        for name, info in data.items()
                    }
            except Exception:
                self.registry = {}

    def _save_registry(self):
        """Save installation registry."""
        with open(self.registry_path, "w") as f:
            json.dump(
                {name: pkg.to_dict() for name, pkg in self.registry.items()},
                f,
                indent=2,
            )

    def verify_package(
        self, package_path: str
    ) -> tuple[VerifyResult, Optional[PackageInfo]]:
        """
        Verify package integrity.

        Args:
            package_path: Path to .tcz package

        Returns:
            Tuple of (result, package_info if valid)
        """
        path = Path(package_path)

        if not path.exists():
            return VerifyResult.CORRUPTED, None

        # Look for manifest - try several patterns
        manifest_path = None
        candidates = [
            path.with_suffix(".json"),  # package.json
            path.parent / f"{path.stem}.json",  # package-name.json
            path.parent / "manifest.json",  # manifest.json (common)
            path.parent / f"{path.stem.split('-')[0]}.json",  # base-name.json
        ]

        for candidate in candidates:
            if candidate.exists():
                manifest_path = candidate
                break

        if not manifest_path:
            return VerifyResult.MISSING_MANIFEST, None

        try:
            with open(manifest_path) as f:
                manifest = json.load(f)
        except Exception:
            return VerifyResult.CORRUPTED, None

        # Calculate checksum
        sha256 = hashlib.sha256()
        with open(path, "rb") as f:
            for chunk in iter(lambda: f.read(8192), b""):
                sha256.update(chunk)
        actual_checksum = sha256.hexdigest()

        # Support both 'checksum' and 'package_checksum' fields
        expected_checksum = manifest.get(
            "checksum", manifest.get("package_checksum", "")
        )
        if expected_checksum and actual_checksum != expected_checksum:
            return VerifyResult.INVALID_CHECKSUM, None

        # Build package info - use 'id' or 'name' field
        info = PackageInfo(
            name=manifest.get("id", manifest.get("name", path.stem)),
            version=manifest.get("version", "unknown"),
            checksum=actual_checksum,
            size=path.stat().st_size,
            dependencies=manifest.get("dependencies", []),
            provides=manifest.get("provides", []),
            description=manifest.get("description", ""),
            author=manifest.get("author", ""),
            license=manifest.get("license", ""),
            build_date=manifest.get("built_at", manifest.get("build_date", "")),
        )

        return VerifyResult.VALID, info

    def install(self, package_path: str, verify: bool = True) -> InstallResult:
        """
        Install a TCZ package.

        Args:
            package_path: Path to .tcz package
            verify: Whether to verify package first

        Returns:
            InstallResult with status and details
        """
        path = Path(package_path)

        # Verify if requested
        if verify:
            result, info = self.verify_package(package_path)
            if result != VerifyResult.VALID:
                return InstallResult(
                    success=False, error=f"Package verification failed: {result.value}"
                )
        else:
            # Basic info extraction
            info = PackageInfo(
                name=path.stem.split("-")[0],
                version="unknown",
                checksum="",
                size=path.stat().st_size,
            )

        # Check if already installed
        if info.name in self.registry:
            existing = self.registry[info.name]
            if existing.version == info.version:
                return InstallResult(
                    success=True,
                    package=existing,
                    warnings=["Package already installed"],
                )

        # Install based on system type
        if self.system_type == SystemType.TINY_CORE:
            return self._install_tinycore(path, info)
        else:
            return self._install_extract(path, info)

    def _install_tinycore(self, path: Path, info: PackageInfo) -> InstallResult:
        """Install on Tiny Core Linux using native tools."""
        try:
            # Copy to optional directory
            dest = self.packages_dir / path.name
            if not dest.exists():
                shutil.copy2(path, dest)

            # Load the extension
            result = subprocess.run(
                ["tce-load", "-i", str(dest)], capture_output=True, text=True
            )

            if result.returncode != 0:
                return InstallResult(
                    success=False, error=f"tce-load failed: {result.stderr}"
                )

            # Record installation
            installed = InstalledPackage(
                name=info.name,
                version=info.version,
                install_path=str(dest),
                install_date=datetime.now().isoformat(),
                status=InstallStatus.MOUNTED,
                system_type=self.system_type,
                checksum=info.checksum,
                mount_point=f"/tmp/tcloop/{info.name}",
            )

            self.registry[info.name] = installed
            self._save_registry()

            return InstallResult(success=True, package=installed)

        except Exception as e:
            return InstallResult(success=False, error=str(e))

    def _install_extract(self, path: Path, info: PackageInfo) -> InstallResult:
        """Install by extracting package (non-Tiny Core systems)."""
        try:
            # Determine extraction method
            install_dir = self.install_base / info.name
            install_dir.mkdir(parents=True, exist_ok=True)

            # Try unsquashfs first (for real .tcz)
            if shutil.which("unsquashfs"):
                result = subprocess.run(
                    ["unsquashfs", "-d", str(install_dir), "-f", str(path)],
                    capture_output=True,
                    text=True,
                )
                if result.returncode != 0:
                    # Fall back to tar if squashfs fails
                    return self._extract_fallback(path, install_dir, info)
            else:
                # No unsquashfs, use fallback
                return self._extract_fallback(path, install_dir, info)

            # Record installation
            installed = InstalledPackage(
                name=info.name,
                version=info.version,
                install_path=str(install_dir),
                install_date=datetime.now().isoformat(),
                status=InstallStatus.INSTALLED,
                system_type=self.system_type,
                checksum=info.checksum,
            )

            self.registry[info.name] = installed
            self._save_registry()

            # Create bin symlinks if applicable
            self._create_symlinks(install_dir, info.name)

            return InstallResult(success=True, package=installed)

        except Exception as e:
            return InstallResult(success=False, error=str(e))

    def _extract_fallback(
        self, path: Path, install_dir: Path, info: PackageInfo
    ) -> InstallResult:
        """Fallback extraction for .tar.gz packages."""
        try:
            # Check if there's a .tar.gz version
            tar_path = path.with_suffix(".tar.gz")
            if tar_path.exists():
                shutil.unpack_archive(str(tar_path), str(install_dir))
            else:
                # Try treating as tar.gz anyway
                try:
                    shutil.unpack_archive(str(path), str(install_dir))
                except Exception:
                    return InstallResult(
                        success=False,
                        error="Cannot extract package. Need unsquashfs or .tar.gz version.",
                    )

            # Record installation
            installed = InstalledPackage(
                name=info.name,
                version=info.version,
                install_path=str(install_dir),
                install_date=datetime.now().isoformat(),
                status=InstallStatus.INSTALLED,
                system_type=self.system_type,
                checksum=info.checksum,
            )

            self.registry[info.name] = installed
            self._save_registry()

            return InstallResult(success=True, package=installed)

        except Exception as e:
            return InstallResult(success=False, error=str(e))

    def _create_symlinks(self, install_dir: Path, package_name: str):
        """Create symlinks for binaries in package."""
        # Look for bin directory
        bin_dir = install_dir / "usr/local/bin"
        if not bin_dir.exists():
            bin_dir = install_dir / "bin"

        if not bin_dir.exists():
            return

        # Target bin directory
        if self.system_type == SystemType.MACOS:
            target_bin = Path.home() / ".local/bin"
        else:
            target_bin = Path.home() / ".local/bin"

        target_bin.mkdir(parents=True, exist_ok=True)

        # Create symlinks for executables
        for binary in bin_dir.iterdir():
            if binary.is_file() and os.access(binary, os.X_OK):
                link = target_bin / binary.name
                if link.exists():
                    link.unlink()
                link.symlink_to(binary)

    def uninstall(self, package_name: str) -> InstallResult:
        """
        Uninstall a package.

        Args:
            package_name: Name of package to uninstall

        Returns:
            InstallResult with status
        """
        if package_name not in self.registry:
            return InstallResult(
                success=False, error=f"Package '{package_name}' not installed"
            )

        installed = self.registry[package_name]

        try:
            if self.system_type == SystemType.TINY_CORE:
                # Tiny Core unload
                result = subprocess.run(
                    ["tce-audit", "-r", package_name], capture_output=True, text=True
                )
                # Remove from optional
                tcz_path = self.packages_dir / f"{package_name}.tcz"
                if tcz_path.exists():
                    tcz_path.unlink()
            else:
                # Remove extracted directory
                install_path = Path(installed.install_path)
                if install_path.exists():
                    shutil.rmtree(install_path)

                # Remove symlinks
                if self.system_type == SystemType.MACOS:
                    bin_dir = Path.home() / ".local/bin"
                else:
                    bin_dir = Path.home() / ".local/bin"

                for link in bin_dir.iterdir():
                    if link.is_symlink():
                        target = link.resolve()
                        if str(installed.install_path) in str(target):
                            link.unlink()

            # Remove from registry
            del self.registry[package_name]
            self._save_registry()

            return InstallResult(success=True)

        except Exception as e:
            return InstallResult(success=False, error=str(e))

    def list_installed(self) -> List[InstalledPackage]:
        """Get list of installed packages."""
        return list(self.registry.values())

    def get_status(self, package_name: str) -> Optional[InstalledPackage]:
        """Get status of a specific package."""
        return self.registry.get(package_name)

    def check_updates(self, repository_url: Optional[str] = None) -> Dict[str, str]:
        """
        Check for available updates.

        Args:
            repository_url: Optional repository URL to check

        Returns:
            Dict of {package_name: new_version} for packages with updates
        """
        # In offline-first model, this checks local manifests
        # Wizard Server handles actual remote checking
        updates = {}

        # Check distribution/plugins for newer versions
        for name, installed in self.registry.items():
            plugin_dir = self.packages_dir / name
            if plugin_dir.exists():
                manifest_path = plugin_dir / f"{name}.json"
                if manifest_path.exists():
                    try:
                        with open(manifest_path) as f:
                            manifest = json.load(f)
                        if manifest.get("version", "") != installed.version:
                            updates[name] = manifest["version"]
                    except Exception:
                        pass

        return updates


# ============================================================================
# Convenience Functions
# ============================================================================


def get_installer(workspace_root: str) -> TCZInstaller:
    """Get installer instance."""
    return TCZInstaller(workspace_root)


def quick_install(workspace_root: str, package_path: str) -> InstallResult:
    """Quick install a package."""
    installer = get_installer(workspace_root)
    return installer.install(package_path)
