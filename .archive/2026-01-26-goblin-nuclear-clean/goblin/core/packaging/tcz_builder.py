"""
TinyCore TCZ Package Builder

Builds .tcz packages for TinyCore Linux distribution.
Handles dependency management, metadata generation, and validation.
"""

import os
import json
import shutil
import hashlib
import subprocess
from pathlib import Path
from typing import List, Dict, Optional, Set
from dataclasses import dataclass
from datetime import datetime

from dev.goblin.core.services.logging_manager import get_logger

logger = get_logger("tcz-builder")


@dataclass
class PackageSpec:
    """TCZ package specification"""

    name: str
    version: str
    description: str
    author: str = "Fred Porter"
    license: str = "MIT"
    website: str = "https://github.com/fredpook/uDOS"

    # Files to include
    source_dirs: List[Path] = None
    executables: Dict[str, Path] = None  # {target_path: source_file}
    configs: Dict[str, Path] = None
    docs: List[Path] = None

    # Dependencies
    dependencies: List[str] = None  # Other TCZ packages

    # Build options
    compression: str = "gzip"  # gzip or xz
    block_size: str = "4K"

    def __post_init__(self):
        if self.source_dirs is None:
            self.source_dirs = []
        if self.executables is None:
            self.executables = {}
        if self.configs is None:
            self.configs = {}
        if self.docs is None:
            self.docs = []
        if self.dependencies is None:
            self.dependencies = []


class TCZBuilder:
    """Build TinyCore TCZ packages"""

    def __init__(self, workspace: Path, output_dir: Path):
        """
        Initialize TCZ builder.

        Args:
            workspace: Project root directory
            output_dir: Directory for built packages
        """
        self.workspace = workspace
        self.output_dir = output_dir
        self.build_dir = output_dir / "build"

        # Create directories
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.build_dir.mkdir(parents=True, exist_ok=True)

        logger.info(f"[LOCAL] TCZ Builder initialized (output={output_dir})")

    def build_package(self, spec: PackageSpec) -> Path:
        """
        Build TCZ package from specification.

        Args:
            spec: Package specification

        Returns:
            Path to built .tcz file
        """
        logger.info(f"[LOCAL] Building package: {spec.name} v{spec.version}")

        # Create package directory
        pkg_name = f"{spec.name}-{spec.version}"
        pkg_dir = self.build_dir / pkg_name

        if pkg_dir.exists():
            shutil.rmtree(pkg_dir)

        pkg_dir.mkdir(parents=True)

        try:
            # 1. Copy source files
            self._copy_sources(spec, pkg_dir)

            # 2. Copy executables
            self._copy_executables(spec, pkg_dir)

            # 3. Copy configs
            self._copy_configs(spec, pkg_dir)

            # 4. Copy documentation
            self._copy_docs(spec, pkg_dir)

            # 5. Create SquashFS archive
            tcz_file = self._create_squashfs(spec, pkg_dir)

            # 6. Generate metadata files
            self._generate_metadata(spec, tcz_file)

            # 7. Validate package
            self._validate_package(tcz_file)

            logger.info(f"[LOCAL] Package built successfully: {tcz_file}")
            return tcz_file

        except Exception as e:
            logger.error(f"[LOCAL] Package build failed: {e}")
            raise

    def _copy_sources(self, spec: PackageSpec, pkg_dir: Path):
        """Copy source directories"""
        lib_dir = pkg_dir / "usr" / "local" / "lib" / "udos"
        lib_dir.mkdir(parents=True, exist_ok=True)

        for source in spec.source_dirs:
            src_path = self.workspace / source
            if not src_path.exists():
                raise FileNotFoundError(f"Source not found: {src_path}")

            dest = lib_dir / source.name

            if src_path.is_dir():
                shutil.copytree(
                    src_path,
                    dest,
                    ignore=shutil.ignore_patterns(
                        "__pycache__",
                        "*.pyc",
                        "*.pyo",
                        ".git",
                        ".dev",
                        ".archive",
                        ".tmp",
                        "tests",
                        "test_*",
                    ),
                )
            else:
                shutil.copy2(src_path, dest)

            logger.debug(f"[LOCAL] Copied source: {source} -> {dest}")

    def _copy_executables(self, spec: PackageSpec, pkg_dir: Path):
        """Copy executable files"""
        bin_dir = pkg_dir / "usr" / "local" / "bin"
        bin_dir.mkdir(parents=True, exist_ok=True)

        for target, source in spec.executables.items():
            src_path = self.workspace / source
            if not src_path.exists():
                raise FileNotFoundError(f"Executable not found: {src_path}")

            dest = bin_dir / Path(target).name
            shutil.copy2(src_path, dest)

            # Make executable
            dest.chmod(0o755)

            logger.debug(f"[LOCAL] Copied executable: {source} -> {dest}")

    def _copy_configs(self, spec: PackageSpec, pkg_dir: Path):
        """Copy configuration files"""
        etc_dir = pkg_dir / "etc" / "udos"
        etc_dir.mkdir(parents=True, exist_ok=True)

        for target, source in spec.configs.items():
            src_path = self.workspace / source
            if not src_path.exists():
                logger.warning(f"[LOCAL] Config not found: {src_path}")
                continue

            dest = etc_dir / Path(target).name
            shutil.copy2(src_path, dest)

            logger.debug(f"[LOCAL] Copied config: {source} -> {dest}")

    def _copy_docs(self, spec: PackageSpec, pkg_dir: Path):
        """Copy documentation files"""
        doc_dir = pkg_dir / "usr" / "local" / "share" / "doc" / "udos"
        doc_dir.mkdir(parents=True, exist_ok=True)

        for doc in spec.docs:
            src_path = self.workspace / doc
            if not src_path.exists():
                logger.warning(f"[LOCAL] Doc not found: {src_path}")
                continue

            if src_path.is_dir():
                dest = doc_dir / src_path.name
                shutil.copytree(
                    src_path, dest, ignore=shutil.ignore_patterns("*.dev", "*.tmp")
                )
            else:
                shutil.copy2(src_path, doc_dir / src_path.name)

            logger.debug(f"[LOCAL] Copied doc: {doc}")

    def _create_squashfs(self, spec: PackageSpec, pkg_dir: Path) -> Path:
        """Create SquashFS archive"""
        tcz_file = self.output_dir / f"{spec.name}.tcz"

        # Build mksquashfs command
        cmd = [
            "mksquashfs",
            str(pkg_dir),
            str(tcz_file),
            "-noappend",
            "-comp",
            spec.compression,
            "-b",
            spec.block_size,
        ]

        logger.info(f"[LOCAL] Creating SquashFS: {tcz_file}")

        try:
            result = subprocess.run(cmd, check=True, capture_output=True, text=True)
            logger.debug(f"[LOCAL] mksquashfs output: {result.stdout}")

        except subprocess.CalledProcessError as e:
            logger.error(f"[LOCAL] mksquashfs failed: {e.stderr}")
            raise RuntimeError(f"Failed to create SquashFS: {e.stderr}")
        except FileNotFoundError:
            raise RuntimeError(
                "mksquashfs not found. Install squashfs-tools: apt-get install squashfs-tools"
            )

        return tcz_file

    def _generate_metadata(self, spec: PackageSpec, tcz_file: Path):
        """Generate TCZ metadata files"""
        base = tcz_file.with_suffix("")

        # 1. Dependencies (.tcz.dep)
        if spec.dependencies:
            dep_file = Path(str(tcz_file) + ".dep")
            with open(dep_file, "w") as f:
                f.write("\n".join(spec.dependencies) + "\n")
            logger.debug(f"[LOCAL] Created: {dep_file.name}")

        # 2. MD5 checksum (.tcz.md5.txt)
        md5_file = Path(str(tcz_file) + ".md5.txt")
        md5_hash = self._calculate_md5(tcz_file)
        with open(md5_file, "w") as f:
            f.write(f"{md5_hash}  {tcz_file.name}\n")
        logger.debug(f"[LOCAL] Created: {md5_file.name}")

        # 3. Package info (.tcz.info)
        info_file = Path(str(tcz_file) + ".info")
        self._generate_info_file(spec, tcz_file, info_file)
        logger.debug(f"[LOCAL] Created: {info_file.name}")

        # 4. File list (.tcz.list)
        list_file = Path(str(tcz_file) + ".list")
        self._generate_file_list(tcz_file, list_file)
        logger.debug(f"[LOCAL] Created: {list_file.name}")

    def _calculate_md5(self, filepath: Path) -> str:
        """Calculate MD5 checksum"""
        md5 = hashlib.md5()
        with open(filepath, "rb") as f:
            for chunk in iter(lambda: f.read(4096), b""):
                md5.update(chunk)
        return md5.hexdigest()

    def _generate_info_file(self, spec: PackageSpec, tcz_file: Path, info_file: Path):
        """Generate .tcz.info metadata file"""
        size = tcz_file.stat().st_size / (1024 * 1024)  # MB
        today = datetime.now().strftime("%Y-%m-%d")

        info_content = f"""Title:          {tcz_file.name}
Description:    {spec.description}
Version:        {spec.version}
Author:         {spec.author}
Original-site:  {spec.website}
Copying-policy: {spec.license}
Size:           {size:.1f}M
Extension_by:   {spec.author}
Tags:           udos knowledge-system offline python
Comments:       Part of uDOS - Offline-first knowledge system
                {spec.description}
Change-log:     {today} Package created
Current:        {today}
"""

        with open(info_file, "w") as f:
            f.write(info_content)

    def _generate_file_list(self, tcz_file: Path, list_file: Path):
        """Generate file listing using unsquashfs"""
        try:
            result = subprocess.run(
                ["unsquashfs", "-ll", str(tcz_file)],
                check=True,
                capture_output=True,
                text=True,
            )

            # Parse output and extract file paths
            lines = result.stdout.strip().split("\n")
            files = []

            for line in lines[3:]:  # Skip header
                if line.strip():
                    parts = line.split()
                    if len(parts) >= 6:
                        filepath = " ".join(parts[5:])
                        files.append(filepath)

            with open(list_file, "w") as f:
                f.write("\n".join(files) + "\n")

        except subprocess.CalledProcessError as e:
            logger.error(f"[LOCAL] unsquashfs failed: {e.stderr}")
            raise
        except FileNotFoundError:
            logger.warning("[LOCAL] unsquashfs not found, skipping file list")

    def _validate_package(self, tcz_file: Path):
        """Validate TCZ package"""
        logger.info(f"[LOCAL] Validating package: {tcz_file.name}")

        # 1. Check file exists
        if not tcz_file.exists():
            raise FileNotFoundError(f"Package file not found: {tcz_file}")

        # 2. Check minimum size (should be > 1KB)
        size = tcz_file.stat().st_size
        if size < 1024:
            raise ValueError(f"Package too small: {size} bytes")

        # 3. Verify MD5 checksum
        md5_file = Path(str(tcz_file) + ".md5.txt")
        if md5_file.exists():
            with open(md5_file) as f:
                expected_md5 = f.read().split()[0]
            actual_md5 = self._calculate_md5(tcz_file)

            if expected_md5 != actual_md5:
                raise ValueError(
                    f"MD5 mismatch: expected {expected_md5}, got {actual_md5}"
                )

        # 4. Test SquashFS listing
        try:
            subprocess.run(
                ["unsquashfs", "-l", str(tcz_file)], check=True, capture_output=True
            )
        except subprocess.CalledProcessError:
            raise ValueError(f"Invalid SquashFS archive: {tcz_file}")

        logger.info(f"[LOCAL] Package validation passed: {tcz_file.name}")

    def build_all(self, specs: List[PackageSpec]) -> List[Path]:
        """Build multiple packages"""
        built = []

        for spec in specs:
            try:
                tcz_file = self.build_package(spec)
                built.append(tcz_file)
            except Exception as e:
                logger.error(f"[LOCAL] Failed to build {spec.name}: {e}")
                raise

        logger.info(f"[LOCAL] Built {len(built)} packages successfully")
        return built

    def clean_build(self):
        """Clean build directory"""
        if self.build_dir.exists():
            shutil.rmtree(self.build_dir)
            self.build_dir.mkdir()
        logger.info("[LOCAL] Build directory cleaned")


def create_core_spec(version: str) -> PackageSpec:
    """Create package spec for udos-core"""
    return PackageSpec(
        name="udos-core",
        version=version,
        description="uDOS Core - TUI, uPY interpreter, command system",
        source_dirs=[
            Path("core"),
            Path("knowledge"),
        ],
        executables={
            "udos": Path("bin/start_udos.sh"),
            "upy": Path("core/runtime/upy/interpreter.py"),
        },
        configs={
            "udos.conf": Path("core/config/default.json"),
        },
        docs=[
            Path("README.md"),
            Path("LICENSE.txt"),
            Path("docs"),
        ],
        dependencies=[
            "python3.12.tcz",
            "ncurses.tcz",
            "readline.tcz",
        ],
    )


def create_api_spec(version: str) -> PackageSpec:
    """Create package spec for udos-api"""
    return PackageSpec(
        name="udos-api",
        version=version,
        description="uDOS API Server - REST and WebSocket endpoints",
        source_dirs=[
            Path("extensions/api"),
        ],
        executables={
            "udos-api": Path("extensions/api/server.py"),
        },
        docs=[
            Path("extensions/api/README.md"),
        ],
        dependencies=[
            "udos-core.tcz",
            "python3.12-flask.tcz",
            "python3.12-websocket.tcz",
        ],
    )


def create_wizard_spec(version: str) -> PackageSpec:
    """Create package spec for udos-wizard"""
    return PackageSpec(
        name="udos-wizard",
        version=version,
        description="uDOS Wizard Server - Always-on services and AI integration",
        source_dirs=[
            Path("wizard"),
        ],
        executables={
            "udos-wizard": Path("wizard/server.py"),
        },
        docs=[
            Path("wizard/README.md"),
        ],
        dependencies=[
            "udos-core.tcz",
            "udos-api.tcz",
            "python3.12-requests.tcz",
            "python3.12-yaml.tcz",
            "git.tcz",
            "openssh.tcz",
        ],
    )


if __name__ == "__main__":
    # Example usage
    from dev.goblin.core.version import get_version_string

    workspace = Path(__file__).parent.parent.parent
    output = workspace / "distribution" / "tcz"

    builder = TCZBuilder(workspace, output)

    # Get current version
    version = get_version_string("core")

    # Build core package
    spec = create_core_spec(version)
    tcz_file = builder.build_package(spec)

    print(f"✅ Built: {tcz_file}")
