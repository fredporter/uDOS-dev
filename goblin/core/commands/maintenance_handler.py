#!/usr/bin/env python3
"""
Maintenance Command Handler - TIDY, CLEAN, BACKUP, RESTORE
Unified maintenance operations for uDOS Alpha v1.0.0.0+

Handles:
- TIDY: Organize files into .archive, .tmp, .dev folders
- CLEAN: Delete files from local-only folders
- BACKUP: Create timestamped snapshots
- RESTORE: Recover files from backups

Author: GitHub Copilot
Date: January 4, 2026
Version: Alpha v1.0.0.0
"""

import os
import shutil
from pathlib import Path
from datetime import datetime, timedelta
import json
import hashlib
from typing import Dict, List, Tuple, Optional
from .base_handler import BaseCommandHandler


class MaintenanceHandler(BaseCommandHandler):
    """Unified maintenance operations handler."""

    # File classification patterns
    FILE_PATTERNS = {
        ".archive": [
            "*-old.*",
            "*-backup.*",
            "*-bak.*",
            "*.bak",
            "*.backup",
            "*~",
            "*-v[0-9]*.*",  # Versioned files
            "*-[0-9][0-9][0-9][0-9]-[0-9][0-9]-[0-9][0-9].*",  # Dated backups
        ],
        ".dev": [
            "*-wip.*",
            "*-draft.*",
            "*-dev.*",
            "IMPLEMENTATION-*.md",
            "MIGRATION-*.md",
            "TEST-*.md",
            "MENU-*.md",
            "DESIGN-*.md",
            "NOTES-*.md",
            "build*.log",
            "dev-server.log",
            "install*.log",
            "*.dev.js",
            "*.dev.ts",
            "*.test.js.map",
        ],
        ".tmp": [
            "*.tmp",
            "*.temp",
            "*-temp.*",
            "*.pyc",
            "__pycache__",
            "*.cache",
            ".DS_Store",
            "Thumbs.db",
            "desktop.ini",
        ],
    }

    # Protected patterns - NEVER move or delete
    PROTECTED_PATTERNS = [
        "memory/bank/user/*.json",
        "memory/ucode/tests/*.py",
        "core/version.json",
        "*/version.json",
        ".git/*",
        ".venv/*",
        "node_modules/*",
    ]

    # Scope mapping
    SCOPE_MAP = {
        "current": {"path": Path.cwd(), "recursive": False},
        "+subfolders": {"path": Path.cwd(), "recursive": True},
        "workspace": {"path": None, "recursive": True},  # Determined at runtime
        "all": {"path": None, "recursive": True},  # Repo root
    }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.backup_root = Path(".backup")
        self.retention_days = {
            ".archive": 30,
            ".tmp": 1,
            ".dev": None,  # Manual cleanup only
            ".cache": None,  # Size-based
            ".backup": 7,
            "logs": 7,
        }

    def handle_tidy(self, params, grid, parser):
        """
        TIDY command - Organize files into appropriate local-only folders.

        Usage:
            TIDY                     - Show interactive menu
            TIDY current             - Tidy current folder only
            TIDY +subfolders         - Tidy current + subfolders
            TIDY workspace           - Tidy workspace folder
            TIDY all                 - Tidy all folders in repo
            TIDY --backup            - Create backup before tidying
            TIDY --dry-run           - Preview only

        Returns:
            Operation report
        """
        try:
            # Parse parameters
            scope = self._parse_scope(params)
            create_backup = "--backup" in params
            dry_run = "--dry-run" in params

            # Show interactive menu if no params
            if not params:
                return self._show_tidy_menu()

            # Get scan path
            scan_path, recursive = self._get_scan_path(scope)

            # Scan for files to tidy
            files_to_move = self._scan_files_for_tidy(scan_path, recursive)

            if not files_to_move:
                return self.output_formatter.format_info(
                    "No files found that need tidying"
                )

            # Create backup if requested
            backup_id = None
            if create_backup and not dry_run:
                backup_id = self._create_backup(
                    [f for files in files_to_move.values() for f in files],
                    reason="pre-tidy",
                )

            # Show preview
            if dry_run:
                return self._preview_tidy(files_to_move, scan_path)

            # Execute tidy operation
            results = self._execute_tidy(files_to_move)

            # Generate report
            return self._generate_tidy_report(results, scope, backup_id)

        except Exception as e:
            return self.output_formatter.format_error(
                "TIDY operation failed", error_details=str(e)
            )

    def handle_clean(self, params, grid, parser):
        """
        CLEAN command - Delete files from local-only folders.

        Usage:
            CLEAN                    - Show interactive menu
            CLEAN current            - Clean current folder only
            CLEAN +subfolders        - Clean current + subfolders
            CLEAN workspace          - Clean workspace folder
            CLEAN all                - Clean all folders in repo
            CLEAN --backup           - Create backup before cleaning
            CLEAN --dry-run          - Preview only
            CLEAN --archives         - Clean only .archive folders
            CLEAN --tmp              - Clean only .tmp folders
            CLEAN --dev              - Clean only .dev folders
            CLEAN --logs             - Clean memory/logs
            CLEAN --backups          - Delete .backup folders
            CLEAN --days=N           - Keep last N days

        Returns:
            Operation report
        """
        try:
            # Parse parameters
            scope = self._parse_scope(params)
            create_backup = "--backup" in params or self._should_auto_backup(params)
            dry_run = "--dry-run" in params
            retention_days = self._parse_retention_days(params)

            # Parse target folders
            targets = self._parse_clean_targets(params)

            # Show interactive menu if no params
            if not params:
                return self._show_clean_menu()

            # Get scan path
            scan_path, recursive = self._get_scan_path(scope)

            # Scan for files to clean
            files_to_delete = self._scan_files_for_clean(
                scan_path, recursive, targets, retention_days
            )

            if not files_to_delete:
                return self.output_formatter.format_info(
                    "No files found that need cleaning"
                )

            # Create backup if requested
            backup_id = None
            if create_backup and not dry_run:
                backup_id = self._create_backup(
                    [f for files in files_to_delete.values() for f in files],
                    reason="pre-clean",
                )

            # Show preview
            if dry_run:
                return self._preview_clean(files_to_delete, scan_path)

            # Require confirmation for destructive operations
            if not self._confirm_clean(files_to_delete, params):
                return self.output_formatter.format_info("Clean operation cancelled")

            # Execute clean operation
            results = self._execute_clean(files_to_delete)

            # Generate report
            return self._generate_clean_report(results, scope, backup_id)

        except Exception as e:
            return self.output_formatter.format_error(
                "CLEAN operation failed", error_details=str(e)
            )

    def handle_backup(self, params, grid, parser):
        """
        BACKUP command - Create timestamped snapshots.

        Usage:
            BACKUP                   - Backup entire workspace
            BACKUP current           - Backup current folder
            BACKUP --before-tidy     - Auto-backup (internal use)
            BACKUP --before-clean    - Auto-backup (internal use)

        Returns:
            Backup confirmation with ID
        """
        try:
            scope = self._parse_scope(params)
            reason = self._parse_backup_reason(params)

            # Get scan path
            scan_path, recursive = self._get_scan_path(scope)

            # Collect files to backup
            files = self._collect_files_for_backup(scan_path, recursive)

            if not files:
                return self.output_formatter.format_info(
                    "No files to backup in specified scope"
                )

            # Create backup
            backup_id = self._create_backup(files, reason)

            return self.output_formatter.format_success(
                f"Backup created: {backup_id}\\n"
                + f"Files backed up: {len(files)}\\n"
                + f"Location: {self.backup_root / backup_id}"
            )

        except Exception as e:
            return self.output_formatter.format_error(
                "BACKUP operation failed", error_details=str(e)
            )

    def handle_restore(self, params, grid, parser):
        """
        RESTORE command - Recover files from backups.

        Usage:
            RESTORE                  - Show available backups
            RESTORE latest           - Restore most recent backup
            RESTORE <backup_id>      - Restore specific backup
            RESTORE file.txt         - Restore single file from .archive
            RESTORE --from-backup    - Interactive restore from .backup
            RESTORE --from-archive   - Interactive restore from .archive

        Returns:
            Restore confirmation
        """
        try:
            # Show available backups if no params
            if not params:
                return self._list_backups()

            # Parse restore target
            target = params[0] if params else "latest"

            if target == "latest":
                backup_id = self._get_latest_backup()
            else:
                backup_id = target

            # Execute restore
            results = self._execute_restore(backup_id)

            return self.output_formatter.format_success(
                f"Restore completed from: {backup_id}\\n"
                + f"Files restored: {results['files_restored']}\\n"
                + f"Destination: {results['restore_path']}"
            )

        except Exception as e:
            return self.output_formatter.format_error(
                "RESTORE operation failed", error_details=str(e)
            )

    # ============================================
    # Internal Helper Methods
    # ============================================

    def _parse_scope(self, params: List[str]) -> str:
        """Parse scope from parameters (case-insensitive)."""
        params_lower = [p.lower() for p in params]
        for scope in self.SCOPE_MAP.keys():
            if scope in params_lower:
                return scope
        return "current"  # default

    def _get_scan_path(self, scope: str) -> Tuple[Path, bool]:
        """Get scan path and recursive flag for scope."""
        scope_config = self.SCOPE_MAP.get(scope, self.SCOPE_MAP["current"])

        if scope == "workspace":
            # Find workspace root (parent with .code-workspace file)
            path = self._find_workspace_root()
        elif scope == "all":
            # Find git repo root
            path = self._find_repo_root()
        else:
            path = scope_config["path"]

        return path, scope_config["recursive"]

    def _find_workspace_root(self) -> Path:
        """Find workspace root by looking for .code-workspace file."""
        current = Path.cwd()
        while current != current.parent:
            if list(current.glob("*.code-workspace")):
                return current
            current = current.parent
        return Path.cwd()  # Fallback to current

    def _find_repo_root(self) -> Path:
        """Find git repository root."""
        current = Path.cwd()
        while current != current.parent:
            if (current / ".git").exists():
                return current
            current = current.parent
        return Path.cwd()  # Fallback to current

    def _scan_files_for_tidy(
        self, path: Path, recursive: bool
    ) -> Dict[str, List[Path]]:
        """Scan for files that need tidying."""
        import fnmatch

        files_by_target = {".archive": [], ".dev": [], ".tmp": []}

        # Get file list
        if recursive:
            files = [f for f in path.rglob("*") if f.is_file()]
        else:
            files = [f for f in path.glob("*") if f.is_file()]

        # Classify each file
        for file_path in files:
            # Skip protected files
            if self._is_protected(file_path):
                continue

            # Skip if already in target folder
            if any(
                part.startswith(".")
                and part in [".archive", ".dev", ".tmp", ".cache", ".backup"]
                for part in file_path.parts
            ):
                continue

            # Check patterns
            for target_folder, patterns in self.FILE_PATTERNS.items():
                for pattern in patterns:
                    if fnmatch.fnmatch(file_path.name, pattern):
                        files_by_target[target_folder].append(file_path)
                        break

        return {k: v for k, v in files_by_target.items() if v}  # Remove empty

    def _scan_files_for_clean(
        self,
        path: Path,
        recursive: bool,
        targets: List[str],
        retention_days: Optional[int],
    ) -> Dict[str, List[Path]]:
        """Scan for files to clean."""
        files_by_folder = {}

        # Find all target folders
        if recursive:
            folders = [f for f in path.rglob("*") if f.is_dir() and f.name in targets]
        else:
            folders = [f for f in path.glob("*") if f.is_dir() and f.name in targets]

        # Scan each folder
        for folder in folders:
            files = []

            # Only apply retention to temp folders, not archives
            # Archives (.archive, .backup) should be cleaned regardless of age
            apply_retention = retention_days is not None and folder.name not in [
                ".archive",
                ".backup",
            ]
            cutoff_date = (
                datetime.now() - timedelta(days=retention_days)
                if apply_retention
                else None
            )

            for file_path in folder.rglob("*"):
                if not file_path.is_file():
                    continue

                # Check age if retention policy applies
                if cutoff_date:
                    mtime = datetime.fromtimestamp(file_path.stat().st_mtime)
                    if mtime > cutoff_date:
                        continue  # Too recent, keep it

                files.append(file_path)

            if files:
                files_by_folder[str(folder)] = files

        return files_by_folder

    def _is_protected(self, file_path: Path) -> bool:
        """Check if file matches protected patterns."""
        import fnmatch

        file_str = str(file_path)
        return any(
            fnmatch.fnmatch(file_str, pattern) for pattern in self.PROTECTED_PATTERNS
        )

    def _create_backup(self, files: List[Path], reason: str = "manual") -> str:
        """Create timestamped backup."""
        from dev.goblin.core.utils.filename_generator import FilenameGenerator

        # Generate backup ID
        gen = FilenameGenerator()
        timestamp = gen.generate_timestamp()
        backup_id = f"{timestamp}-{reason}"
        backup_dir = self.backup_root / backup_id

        # Create backup directory
        backup_dir.mkdir(parents=True, exist_ok=True)

        # Create manifest
        manifest = {
            "backup_id": backup_id,
            "timestamp": datetime.now().isoformat(),
            "reason": reason,
            "files": [],
        }

        # Copy files
        for file_path in files:
            try:
                # Preserve directory structure
                rel_path = file_path.relative_to(Path.cwd())
                dest_path = backup_dir / rel_path
                dest_path.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(file_path, dest_path)

                manifest["files"].append(
                    {
                        "path": str(rel_path),
                        "size": file_path.stat().st_size,
                        "mtime": file_path.stat().st_mtime,
                    }
                )
            except Exception as e:
                self.logger.warning(f"Failed to backup {file_path}: {e}")

        # Save manifest
        manifest_path = backup_dir / "manifest.json"
        with open(manifest_path, "w") as f:
            json.dump(manifest, f, indent=2)

        # Create 'latest' symlink
        latest_link = self.backup_root / "latest"
        if latest_link.exists() or latest_link.is_symlink():
            latest_link.unlink()
        latest_link.symlink_to(backup_id)

        return backup_id

    def _execute_tidy(self, files_to_move: Dict[str, List[Path]]) -> Dict:
        """Execute tidy operation."""
        results = {"moved": 0, "failed": 0, "total_bytes": 0, "details": []}

        for target_folder, files in files_to_move.items():
            for file_path in files:
                try:
                    # Get file size before moving
                    size = file_path.stat().st_size

                    # Determine destination
                    parent_dir = file_path.parent
                    target_dir = parent_dir / target_folder
                    target_dir.mkdir(parents=True, exist_ok=True)

                    dest_path = target_dir / file_path.name

                    # Move file
                    shutil.move(str(file_path), str(dest_path))

                    results["moved"] += 1
                    results["total_bytes"] += size
                    results["details"].append(
                        {
                            "file": str(file_path),
                            "destination": str(dest_path),
                            "size": size,
                        }
                    )

                except Exception as e:
                    results["failed"] += 1
                    if self.logger:
                        self.logger.error(f"Failed to move {file_path}: {e}")

        return results

    def _execute_clean(self, files_to_delete: Dict[str, List[Path]]) -> Dict:
        """Execute clean operation."""
        results = {"deleted": 0, "failed": 0, "freed_bytes": 0}

        for folder, files in files_to_delete.items():
            for file_path in files:
                try:
                    size = file_path.stat().st_size
                    file_path.unlink()
                    results["deleted"] += 1
                    results["freed_bytes"] += size
                except Exception as e:
                    results["failed"] += 1
                    self.logger.error(f"Failed to delete {file_path}: {e}")

        # Clean empty directories
        for folder in files_to_delete.keys():
            folder_path = Path(folder)
            if folder_path.exists():
                self._remove_empty_dirs(folder_path)

        return results

    def _remove_empty_dirs(self, path: Path):
        """Remove empty directories recursively."""
        for dirpath in sorted(path.rglob("*"), key=lambda p: len(str(p)), reverse=True):
            if dirpath.is_dir() and not any(dirpath.iterdir()):
                try:
                    dirpath.rmdir()
                except Exception:
                    pass

    def _parse_clean_targets(self, params: List[str]) -> List[str]:
        """Parse target folders for clean operation."""
        targets = []
        if "--archives" in params:
            targets.append(".archive")
        if "--tmp" in params:
            targets.append(".tmp")
        if "--dev" in params:
            targets.append(".dev")
        if "--cache" in params:
            targets.append(".cache")
        if "--backups" in params:
            targets.append(".backup")

        # Default to all if none specified
        if not targets:
            targets = [".archive", ".tmp", ".dev", ".cache"]

        return targets

    def _parse_retention_days(self, params: List[str]) -> int:
        """Parse retention days from parameters."""
        # Force flag = clean everything (0 days retention)
        if "--force" in params:
            return 0

        for param in params:
            if param.startswith("--days="):
                return int(param.split("=")[1])
        return 30  # default

    def _should_auto_backup(self, params: List[str]) -> bool:
        """Determine if auto-backup should be created."""
        # Always backup for destructive operations unless --no-backup
        return "--no-backup" not in params

    def _confirm_clean(
        self, files_to_delete: Dict[str, List[Path]], params: List[str]
    ) -> bool:
        """Confirm destructive clean operation."""
        # Skip confirmation with --force
        if "--force" in params:
            return True

        total_files = sum(len(files) for files in files_to_delete.values())
        total_size = sum(
            sum(f.stat().st_size for f in files) for files in files_to_delete.values()
        )

        print(
            f"\\n⚠️  WARNING: About to delete {total_files} files ({total_size / (1024*1024):.2f} MB)\\n"
        )
        response = input("Type 'DELETE' to confirm: ")
        return response == "DELETE"

    def _show_tidy_menu(self) -> str:
        """Show interactive tidy menu."""
        return """
╔════════════════════════════════════════════════════════════╗
║                    TIDY - Organize Files                   ║
╠════════════════════════════════════════════════════════════╣
║  Scope Options:                                            ║
║    TIDY current         - Current folder only              ║
║    TIDY +subfolders     - Current + subfolders             ║
║    TIDY workspace       - Workspace folder                 ║
║    TIDY all             - All folders in repo              ║
║                                                            ║
║  Options:                                                  ║
║    --backup             - Create backup before tidying     ║
║    --dry-run            - Preview changes only             ║
╠════════════════════════════════════════════════════════════╣
║  Example: TIDY workspace --backup                          ║
╚════════════════════════════════════════════════════════════╝
"""

    def _show_clean_menu(self) -> str:
        """Show interactive clean menu."""
        return """
╔════════════════════════════════════════════════════════════╗
║                   CLEAN - Delete Files                     ║
╠════════════════════════════════════════════════════════════╣
║  ⚠️  WARNING: This will permanently delete files!          ║
╠════════════════════════════════════════════════════════════╣
║  Scope Options:                                            ║
║    CLEAN current        - Current folder only              ║
║    CLEAN +subfolders    - Current + subfolders             ║
║    CLEAN workspace      - Workspace folder                 ║
║    CLEAN all            - All folders in repo              ║
║                                                            ║
║  Target Options:                                           ║
║    --archives           - Clean .archive folders           ║
║    --tmp                - Clean .tmp folders               ║
║    --dev                - Clean .dev folders               ║
║    --cache              - Clean .cache folders             ║
║    --backups            - Delete .backup folders           ║
║    --logs               - Clean memory/logs                ║
║                                                            ║
║  Safety Options:                                           ║
║    --backup             - Create backup first (automatic)  ║
║    --dry-run            - Preview only                     ║
║    --days=N             - Keep last N days (default: 30)   ║
║    --force              - Clean all files, skip confirm    ║
╠════════════════════════════════════════════════════════════╣
║  Example: CLEAN workspace --archives --dry-run             ║
║           CLEAN all --force (dev mode: full clean)         ║
╚════════════════════════════════════════════════════════════╝
"""

    def _preview_tidy(
        self, files_to_move: Dict[str, List[Path]], scan_path: Path
    ) -> str:
        """Generate tidy preview."""
        lines = [
            "╔════════════════════════════════════════════════════════════╗",
            "║              TIDY Preview (Dry Run)                        ║",
            "╠════════════════════════════════════════════════════════════╣",
        ]

        total_files = 0
        for target_folder, files in files_to_move.items():
            total_files += len(files)
            lines.append(
                f"║  → {target_folder}: {len(files)} files{' ' * (40 - len(target_folder) - len(str(len(files))))} ║"
            )

        lines.extend(
            [
                "╠════════════════════════════════════════════════════════════╣",
                f"║  Total: {total_files} files would be moved{' ' * (33 - len(str(total_files)))} ║",
                "║  Run without --dry-run to execute                          ║",
                "╚════════════════════════════════════════════════════════════╝",
            ]
        )

        return "\\n".join(lines)

    def _preview_clean(
        self, files_to_delete: Dict[str, List[Path]], scan_path: Path
    ) -> str:
        """Generate clean preview."""
        lines = [
            "╔════════════════════════════════════════════════════════════╗",
            "║              CLEAN Preview (Dry Run)                       ║",
            "╠════════════════════════════════════════════════════════════╣",
        ]

        total_files = 0
        total_size = 0
        for folder, files in files_to_delete.items():
            size = sum(f.stat().st_size for f in files)
            total_files += len(files)
            total_size += size
            lines.append(
                f"║  {folder}: {len(files)} files ({size / (1024*1024):.2f} MB){' ' * 20} ║"
            )

        lines.extend(
            [
                "╠════════════════════════════════════════════════════════════╣",
                f"║  Total: {total_files} files ({total_size / (1024*1024):.2f} MB) would be deleted ║",
                "║  Run without --dry-run to execute                          ║",
                "╚════════════════════════════════════════════════════════════╝",
            ]
        )

        return "\\n".join(lines)

    def _generate_tidy_report(
        self, results: Dict, scope: str, backup_id: Optional[str]
    ) -> str:
        """Generate tidy operation report."""
        lines = [
            "╔════════════════════════════════════════════════════════════╗",
            "║              TIDY Operation Report - Success               ║",
            "╠════════════════════════════════════════════════════════════╣",
            f"║  Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S %Z'):<41} ║",
            f"║  Scope: {scope:<50} ║",
        ]

        if backup_id:
            lines.append(f"║  Backup: {backup_id:<47} ║")

        total_mb = results.get("total_bytes", 0) / (1024 * 1024)

        lines.extend(
            [
                "╠════════════════════════════════════════════════════════════╣",
                f"║  Files Moved: {results['moved']:<44} ║",
                f"║  Total Size: {total_mb:.2f} MB{' ' * (45 - len(f'{total_mb:.2f}'))} ║",
                f"║  Failures: {results['failed']:<47} ║",
                "╠════════════════════════════════════════════════════════════╣",
                "║  ✅ Tidy complete - workspace organized                    ║",
                "║                                                            ║",
                "║  💡 Tip: Run CLEAN to delete old files from .archive       ║",
                "║     Example: CLEAN --archives --dry-run                    ║",
                "╚════════════════════════════════════════════════════════════╝",
            ]
        )

        return "\\n".join(lines)

    def _generate_clean_report(
        self, results: Dict, scope: str, backup_id: Optional[str]
    ) -> str:
        """Generate clean operation report."""
        lines = [
            "╔════════════════════════════════════════════════════════════╗",
            "║              CLEAN Operation Report - Success              ║",
            "╠════════════════════════════════════════════════════════════╣",
            f"║  Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S %Z'):<41} ║",
            f"║  Scope: {scope:<50} ║",
        ]

        if backup_id:
            lines.append(f"║  Backup: {backup_id:<47} ║")

        lines.extend(
            [
                "╠════════════════════════════════════════════════════════════╣",
                f"║  Files Deleted: {results['deleted']:<42} ║",
                f"║  Space Freed: {results['freed_bytes'] / (1024*1024):.2f} MB{' ' * 34} ║",
                f"║  Failures: {results['failed']:<47} ║",
                "╠════════════════════════════════════════════════════════════╣",
                "║  ✅ Clean complete                                         ║",
                "╚════════════════════════════════════════════════════════════╝",
            ]
        )

        return "\\n".join(lines)

    def _list_backups(self) -> str:
        """List available backups."""
        if not self.backup_root.exists():
            return "No backups found"

        backups = sorted(
            self.backup_root.iterdir(), key=lambda p: p.stat().st_mtime, reverse=True
        )
        backups = [b for b in backups if b.is_dir()]

        lines = [
            "╔════════════════════════════════════════════════════════════╗",
            "║                    Available Backups                       ║",
            "╠════════════════════════════════════════════════════════════╣",
        ]

        for backup_dir in backups[:10]:  # Show last 10
            manifest_path = backup_dir / "manifest.json"
            if manifest_path.exists():
                with open(manifest_path) as f:
                    manifest = json.load(f)
                lines.append(f"║  {backup_dir.name:<55} ║")
                lines.append(f"║    Files: {len(manifest['files']):<48} ║")

        lines.extend(
            [
                "╠════════════════════════════════════════════════════════════╣",
                "║  Use: RESTORE latest   or   RESTORE <backup_id>            ║",
                "╚════════════════════════════════════════════════════════════╝",
            ]
        )

        return "\\n".join(lines)

    def _get_latest_backup(self) -> str:
        """Get most recent backup ID."""
        latest_link = self.backup_root / "latest"
        if latest_link.exists():
            return latest_link.resolve().name

        backups = sorted(
            self.backup_root.iterdir(), key=lambda p: p.stat().st_mtime, reverse=True
        )
        if backups:
            return backups[0].name

        raise ValueError("No backups found")

    def _execute_restore(self, backup_id: str) -> Dict:
        """Execute restore operation."""
        backup_dir = self.backup_root / backup_id

        if not backup_dir.exists():
            raise ValueError(f"Backup not found: {backup_id}")

        manifest_path = backup_dir / "manifest.json"
        with open(manifest_path) as f:
            manifest = json.load(f)

        results = {"files_restored": 0, "restore_path": Path.cwd()}

        for file_info in manifest["files"]:
            src = backup_dir / file_info["path"]
            dest = Path.cwd() / file_info["path"]

            try:
                dest.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(src, dest)
                results["files_restored"] += 1
            except Exception as e:
                self.logger.error(f"Failed to restore {file_info['path']}: {e}")

        return results

    def _collect_files_for_backup(self, path: Path, recursive: bool) -> List[Path]:
        """Collect files for backup."""
        if recursive:
            files = [
                f for f in path.rglob("*") if f.is_file() and not self._is_protected(f)
            ]
        else:
            files = [
                f for f in path.glob("*") if f.is_file() and not self._is_protected(f)
            ]

        # Exclude files already in local-only folders
        files = [
            f
            for f in files
            if not any(
                part.startswith(".")
                and part in [".archive", ".dev", ".tmp", ".cache", ".backup"]
                for part in f.parts
            )
        ]

        return files

    def _parse_backup_reason(self, params: List[str]) -> str:
        """Parse backup reason from parameters."""
        if "--before-tidy" in params:
            return "pre-tidy"
        elif "--before-clean" in params:
            return "pre-clean"
        return "manual"

    def _should_auto_backup(self, params: List[str]) -> bool:
        """Check if automatic backup should be created."""
        # Auto-backup for destructive operations
        destructive_flags = ["--archives", "--tmp", "--dev", "--logs", "--backups"]
        return any(flag in params for flag in destructive_flags)

    def _parse_clean_targets(self, params: List[str]) -> List[str]:
        """Parse target folders from parameters."""
        targets = []
        target_map = {
            "--archives": ".archive",
            "--tmp": ".tmp",
            "--dev": ".dev",
            "--cache": ".cache",
            "--backups": ".backup",
        }

        for flag, folder in target_map.items():
            if flag in params:
                targets.append(folder)

        # If --logs, add special logs path
        if "--logs" in params:
            targets.append("logs")

        # Default to all if none specified
        if not targets:
            targets = [".archive", ".tmp", ".dev", ".cache"]

        return targets

    def _confirm_clean(
        self, files_to_delete: Dict[str, List[Path]], targets: List[str]
    ) -> bool:
        """Prompt user for confirmation before cleaning."""
        total_files = sum(len(files) for files in files_to_delete.values())
        total_size = sum(
            sum(f.stat().st_size for f in files) for files in files_to_delete.values()
        )

        print(
            f"\n⚠️  About to delete {total_files} files ({total_size / (1024*1024):.2f} MB)"
        )
        print(f"Targets: {', '.join(targets)}")
        response = input("\nContinue? (yes/no): ").strip().lower()
        return response in ["yes", "y"]
