"""
uDOS Unified File Picker Service (v1.2.30)

Shared file picking logic for CLI, TUI, and GUI interfaces.

Consolidates functionality from:
- core/ui/file_browser.py (workspace navigation, filtering)
- core/ui/file_picker.py (fuzzy search, SQLite tracking)
- app/src/components/file-picker.js (Desktop app file picker)

Provides:
- Workspace management (5 workspaces)
- File filtering by extension
- Recent file tracking
- Bookmarks
- Fuzzy search
- Path validation

Author: uDOS Development Team
Version: 1.2.30
"""

import sqlite3
import difflib
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from pathlib import Path
from typing import Dict, List, Optional, Set, Tuple


class Workspace(Enum):
    """Available workspace locations"""

    KNOWLEDGE = "knowledge"
    DOCS = "memory/docs"
    DRAFTS = "memory/drafts"
    SANDBOX = "memory/ucode/sandbox"
    SCRIPTS = "memory/ucode/scripts"


@dataclass
class FileEntry:
    """File or directory entry"""

    path: Path
    name: str
    is_dir: bool
    extension: str = ""
    size: int = 0
    mtime: float = 0.0

    def __post_init__(self):
        if not self.is_dir and not self.extension:
            self.extension = self.path.suffix
        if self.path.exists():
            stat = self.path.stat()
            if not self.is_dir:
                self.size = stat.st_size
            self.mtime = stat.st_mtime

    def to_dict(self) -> dict:
        """Convert to dictionary for JSON serialization"""
        return {
            "path": str(self.path),
            "name": self.name,
            "is_dir": self.is_dir,
            "extension": self.extension,
            "size": self.size,
            "mtime": self.mtime,
        }


@dataclass
class FilePickerState:
    """Current file picker state"""

    workspace: Workspace = Workspace.SCRIPTS
    current_path: Path = None
    entries: List[FileEntry] = field(default_factory=list)
    selection_index: int = 0
    filter_extensions: List[str] = field(
        default_factory=lambda: [".upy", ".md", ".json"]
    )
    show_hidden: bool = False
    recent_files: List[str] = field(default_factory=list)
    bookmarks: List[str] = field(default_factory=list)
    workspace_paths: Dict[str, str] = field(default_factory=dict)

    @property
    def selected_entry(self) -> Optional[FileEntry]:
        """Get currently selected entry"""
        if 0 <= self.selection_index < len(self.entries):
            return self.entries[self.selection_index]
        return None


class FilePickerService:
    """
    Unified file picking service for all interfaces.

    Workspaces:
    - knowledge: Core distributable knowledge base (read-only)
    - docs: User documentation and guides
    - drafts: Work in progress documents
    - sandbox: Experimental uPY scripts
    - scripts: User uPY scripts

    Features:
    - Workspace switching with path memory
    - File filtering by extension
    - Recent file tracking (SQLite)
    - Bookmarks
    - Fuzzy search
    """

    # Default file extensions to show
    DEFAULT_EXTENSIONS = [".upy", ".md", ".json"]

    # File type categories
    FILE_TYPES = {
        "text": {".txt", ".md", ".rst", ".log"},
        "code": {".py", ".js", ".ts", ".html", ".css", ".json", ".yaml", ".yml"},
        "config": {".ini", ".cfg", ".conf", ".env", ".toml"},
        "script": {".sh", ".bash", ".zsh", ".bat", ".ps1", ".upy"},
        "data": {".csv", ".xml", ".sql", ".db", ".sqlite"},
    }

    def __init__(self, root_path: Path = None):
        """
        Initialize file picker service.

        Args:
            root_path: Project root path (auto-detected if None)
        """
        self._init_root(root_path)
        self.state = FilePickerState()

        # Workspace path mapping
        self.workspaces = {
            Workspace.KNOWLEDGE: self.root / "knowledge",
            Workspace.DOCS: self.root / "memory" / "docs",
            Workspace.DRAFTS: self.root / "memory" / "drafts",
            Workspace.SANDBOX: self.root / "memory" / "ucode" / "sandbox",
            Workspace.SCRIPTS: self.root / "memory" / "ucode" / "scripts",
        }

        # Initialize database for tracking
        self._init_database()

        # Set initial workspace
        self.set_workspace(Workspace.SCRIPTS)

    def _init_root(self, root_path: Path = None):
        """Initialize root path"""
        if root_path:
            self.root = Path(root_path)
        else:
            try:
                from dev.goblin.core.utils.paths import PATHS

                self.root = PATHS.ROOT
            except ImportError:
                # Fallback: find project root by looking for uDOS.py
                current = Path(__file__).resolve()
                for parent in current.parents:
                    if (parent / "uDOS.py").exists():
                        self.root = parent
                        break
                else:
                    self.root = Path.cwd()

    def _init_database(self):
        """Initialize SQLite database for file access tracking"""
        self.db_path = self.root / "memory" / "logs" / "file_access.db"
        self.db_path.parent.mkdir(parents=True, exist_ok=True)

        with sqlite3.connect(self.db_path) as conn:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS file_access (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    file_path TEXT NOT NULL,
                    workspace TEXT NOT NULL,
                    access_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    access_type TEXT DEFAULT 'open',
                    file_size INTEGER,
                    file_mtime REAL
                )
            """
            )

            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS file_bookmarks (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    file_path TEXT NOT NULL UNIQUE,
                    workspace TEXT NOT NULL,
                    bookmark_name TEXT,
                    created_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    tags TEXT
                )
            """
            )

            conn.execute(
                "CREATE INDEX IF NOT EXISTS idx_file_access_time ON file_access(access_time)"
            )
            conn.execute(
                "CREATE INDEX IF NOT EXISTS idx_file_path ON file_access(file_path)"
            )

    # ─── Workspace Management ───────────────────────────────────────

    def set_workspace(self, workspace: Workspace) -> bool:
        """
        Switch to a different workspace.

        Args:
            workspace: Target workspace

        Returns:
            True if switched successfully
        """
        # Remember current path before switching
        if self.state.current_path:
            self._remember_workspace_path()

        self.state.workspace = workspace
        workspace_path = self.workspaces.get(workspace)

        # Try to restore last path for this workspace
        restored = self._restore_workspace_path(workspace)
        if restored and restored.exists():
            self.state.current_path = restored
        elif workspace_path:
            # Ensure workspace exists (except knowledge which is read-only)
            if not workspace_path.exists() and workspace != Workspace.KNOWLEDGE:
                workspace_path.mkdir(parents=True, exist_ok=True)
            self.state.current_path = workspace_path
        else:
            return False

        self._refresh_entries()
        return True

    def get_workspace_path(self, workspace: Workspace = None) -> Path:
        """Get path for workspace"""
        ws = workspace or self.state.workspace
        return self.workspaces.get(ws, self.root)

    def _remember_workspace_path(self):
        """Remember current path for workspace"""
        ws_name = self.state.workspace.value
        self.state.workspace_paths[ws_name] = str(self.state.current_path)

    def _restore_workspace_path(self, workspace: Workspace) -> Optional[Path]:
        """Restore last path for workspace"""
        ws_name = workspace.value
        path_str = self.state.workspace_paths.get(ws_name)
        if path_str:
            path = Path(path_str)
            if path.exists():
                return path
        return None

    # ─── Directory Navigation ───────────────────────────────────────

    def navigate_to(self, path: Path | str) -> bool:
        """
        Navigate to a specific path.

        Args:
            path: Target path (absolute or relative to workspace)

        Returns:
            True if navigation successful
        """
        target = Path(path) if isinstance(path, str) else path

        # Make relative paths absolute from workspace
        if not target.is_absolute():
            target = self.get_workspace_path() / target

        if not target.exists() or not target.is_dir():
            return False

        self.state.current_path = target
        self._refresh_entries()
        return True

    def navigate_up(self) -> bool:
        """Navigate to parent directory"""
        if not self.state.current_path:
            return False

        # Don't navigate above workspace root
        workspace_root = self.get_workspace_path()
        if self.state.current_path == workspace_root:
            return False

        parent = self.state.current_path.parent
        if parent.exists():
            self.state.current_path = parent
            self._refresh_entries()
            return True
        return False

    def navigate_into(self, entry: FileEntry = None) -> bool:
        """
        Navigate into directory.

        Args:
            entry: Directory entry (uses selected if None)

        Returns:
            True if navigation successful
        """
        if entry is None:
            entry = self.state.selected_entry

        if entry and entry.is_dir and entry.path.exists():
            self.state.current_path = entry.path
            self._refresh_entries()
            return True
        return False

    def _refresh_entries(self):
        """Scan current directory and populate entries"""
        if not self.state.current_path or not self.state.current_path.exists():
            self.state.entries = []
            return

        entries = []

        try:
            # Sort: directories first, then alphabetically
            items = sorted(
                self.state.current_path.iterdir(),
                key=lambda p: (not p.is_dir(), p.name.lower()),
            )

            for item in items:
                # Skip hidden files unless enabled
                if item.name.startswith(".") and not self.state.show_hidden:
                    continue

                if item.is_dir():
                    entries.append(FileEntry(path=item, name=item.name, is_dir=True))
                else:
                    # Apply extension filter
                    if self._passes_filter(item):
                        entries.append(
                            FileEntry(
                                path=item,
                                name=item.name,
                                is_dir=False,
                            )
                        )

            self.state.entries = entries

            # Reset selection if out of bounds
            if self.state.selection_index >= len(entries):
                self.state.selection_index = max(0, len(entries) - 1)

        except PermissionError:
            self.state.entries = []

    def _passes_filter(self, path: Path) -> bool:
        """Check if file passes extension filter"""
        if not self.state.filter_extensions:
            return True
        return path.suffix.lower() in self.state.filter_extensions

    # ─── File Selection ─────────────────────────────────────────────

    def select_index(self, index: int) -> bool:
        """Select entry by index"""
        if 0 <= index < len(self.state.entries):
            self.state.selection_index = index
            return True
        return False

    def select_next(self) -> bool:
        """Select next entry"""
        if self.state.selection_index < len(self.state.entries) - 1:
            self.state.selection_index += 1
            return True
        return False

    def select_previous(self) -> bool:
        """Select previous entry"""
        if self.state.selection_index > 0:
            self.state.selection_index -= 1
            return True
        return False

    def get_selected(self) -> Optional[FileEntry]:
        """Get currently selected entry"""
        return self.state.selected_entry

    def open_selected(self) -> Optional[FileEntry]:
        """
        Open selected file or navigate into directory.

        Returns:
            FileEntry if file opened, None if directory navigated
        """
        entry = self.state.selected_entry
        if not entry:
            return None

        if entry.is_dir:
            self.navigate_into(entry)
            return None
        else:
            self.record_access(entry.path, "open")
            return entry

    # ─── File Access Tracking ───────────────────────────────────────

    def record_access(self, path: Path, access_type: str = "open"):
        """
        Record file access for recent files tracking.

        Args:
            path: File path
            access_type: Type of access (open, edit, create, delete)
        """
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.execute(
                    """
                    INSERT INTO file_access (file_path, workspace, access_type, file_size, file_mtime)
                    VALUES (?, ?, ?, ?, ?)
                """,
                    (
                        str(path),
                        self.state.workspace.value,
                        access_type,
                        path.stat().st_size if path.exists() else None,
                        path.stat().st_mtime if path.exists() else None,
                    ),
                )

                # Keep only last 1000 entries
                conn.execute(
                    """
                    DELETE FROM file_access
                    WHERE id NOT IN (
                        SELECT id FROM file_access
                        ORDER BY access_time DESC
                        LIMIT 1000
                    )
                """
                )
        except Exception:
            pass  # Don't fail on tracking errors

    def get_recent_files(
        self, count: int = 20, workspace: str = None, days: int = 30
    ) -> List[Dict]:
        """
        Get recently accessed files.

        Args:
            count: Maximum files to return
            workspace: Filter by workspace (None for all)
            days: Days to look back

        Returns:
            List of file info dicts
        """
        cutoff = datetime.now() - timedelta(days=days)

        query = """
            SELECT file_path, workspace, MAX(access_time) as last_access,
                   COUNT(*) as access_count, file_size, file_mtime
            FROM file_access
            WHERE access_time > ?
        """
        params = [cutoff.isoformat()]

        if workspace:
            query += " AND workspace = ?"
            params.append(workspace)

        query += " GROUP BY file_path, workspace ORDER BY last_access DESC LIMIT ?"
        params.append(count)

        results = []
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.row_factory = sqlite3.Row
                for row in conn.execute(query, params):
                    info = dict(row)
                    path = Path(info["file_path"])
                    info["exists"] = path.exists()
                    info["extension"] = path.suffix.lower()
                    info["name"] = path.name
                    results.append(info)
        except Exception:
            pass

        return results

    # ─── Bookmarks ──────────────────────────────────────────────────

    def add_bookmark(self, path: Path, name: str = None, tags: str = None) -> bool:
        """Add file to bookmarks"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.execute(
                    """
                    INSERT OR REPLACE INTO file_bookmarks (file_path, workspace, bookmark_name, tags)
                    VALUES (?, ?, ?, ?)
                """,
                    (str(path), self.state.workspace.value, name or path.name, tags),
                )
            return True
        except Exception:
            return False

    def remove_bookmark(self, path: Path) -> bool:
        """Remove file from bookmarks"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.execute(
                    "DELETE FROM file_bookmarks WHERE file_path = ?", (str(path),)
                )
            return True
        except Exception:
            return False

    def get_bookmarks(self, workspace: str = None) -> List[Dict]:
        """Get bookmarked files"""
        query = "SELECT * FROM file_bookmarks"
        params = []

        if workspace:
            query += " WHERE workspace = ?"
            params.append(workspace)

        query += " ORDER BY created_time DESC"

        results = []
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.row_factory = sqlite3.Row
                for row in conn.execute(query, params):
                    info = dict(row)
                    path = Path(info["file_path"])
                    info["exists"] = path.exists()
                    results.append(info)
        except Exception:
            pass

        return results

    # ─── Search ─────────────────────────────────────────────────────

    def search(
        self, query: str, recursive: bool = True, fuzzy_threshold: float = 0.6
    ) -> List[FileEntry]:
        """
        Search for files matching query.

        Args:
            query: Search string
            recursive: Search subdirectories
            fuzzy_threshold: Minimum similarity for fuzzy matching

        Returns:
            List of matching FileEntry objects
        """
        results = []
        query_lower = query.lower()

        search_root = self.state.current_path or self.get_workspace_path()

        def search_dir(path: Path):
            try:
                for item in path.iterdir():
                    if item.name.startswith("."):
                        continue

                    if item.is_dir():
                        if recursive:
                            search_dir(item)
                    else:
                        # Exact match
                        if query_lower in item.name.lower():
                            if self._passes_filter(item):
                                results.append(
                                    FileEntry(
                                        path=item,
                                        name=item.name,
                                        is_dir=False,
                                    )
                                )
                        # Fuzzy match
                        elif fuzzy_threshold > 0:
                            ratio = difflib.SequenceMatcher(
                                None, query_lower, item.name.lower()
                            ).ratio()
                            if ratio >= fuzzy_threshold:
                                if self._passes_filter(item):
                                    results.append(
                                        FileEntry(
                                            path=item,
                                            name=item.name,
                                            is_dir=False,
                                        )
                                    )
            except PermissionError:
                pass

        search_dir(search_root)

        # Sort by relevance (exact matches first, then by name)
        results.sort(
            key=lambda e: (0 if query_lower in e.name.lower() else 1, e.name.lower())
        )

        return results[:50]  # Limit results

    # ─── Filtering ──────────────────────────────────────────────────

    def set_filter(self, extensions: List[str] = None):
        """
        Set extension filter.

        Args:
            extensions: List of extensions (e.g., ['.md', '.json']) or None to clear
        """
        self.state.filter_extensions = extensions or []
        self._refresh_entries()

    def add_filter(self, extension: str):
        """Add extension to filter"""
        ext = extension if extension.startswith(".") else f".{extension}"
        if ext not in self.state.filter_extensions:
            self.state.filter_extensions.append(ext)
            self._refresh_entries()

    def remove_filter(self, extension: str):
        """Remove extension from filter"""
        ext = extension if extension.startswith(".") else f".{extension}"
        if ext in self.state.filter_extensions:
            self.state.filter_extensions.remove(ext)
            self._refresh_entries()

    def toggle_hidden(self) -> bool:
        """Toggle hidden file visibility"""
        self.state.show_hidden = not self.state.show_hidden
        self._refresh_entries()
        return self.state.show_hidden

    # ─── API Methods (for IPC/HTTP) ─────────────────────────────────

    def list_directory(self, path: str = None) -> Dict:
        """
        List directory contents (API method).

        Args:
            path: Path to list (uses current if None). Can be relative or absolute.

        Returns:
            Dict with 'files', 'folders', 'path' keys
        """
        # Resolve path
        if path:
            target = Path(path)
            # If relative path, resolve from root
            if not target.is_absolute():
                target = self.root / path
        else:
            target = self.state.current_path or self.workspaces[Workspace.SCRIPTS]

        if not target or not target.exists():
            return {"error": f"Path not found: {target}", "files": [], "folders": []}

        if not target.is_dir():
            return {"error": f"Not a directory: {target}", "files": [], "folders": []}

        files = []
        folders = []

        try:
            for item in sorted(target.iterdir(), key=lambda p: p.name.lower()):
                # Skip hidden files unless enabled
                if item.name.startswith(".") and not self.state.show_hidden:
                    continue

                if item.is_dir():
                    folders.append(item.name)
                elif self._passes_filter(item):
                    # Return file info with name and size
                    try:
                        size = item.stat().st_size
                    except:
                        size = 0
                    files.append({"name": item.name, "size": size})
        except PermissionError:
            return {"error": "Permission denied", "files": [], "folders": []}
        except Exception as e:
            return {
                "error": f"Failed to list directory: {e}",
                "files": [],
                "folders": [],
            }

        return {
            "path": str(target),
            "files": files,
            "folders": folders,
        }

    def get_state_dict(self) -> Dict:
        """Get current state as dictionary (for JSON serialization)"""
        return {
            "workspace": self.state.workspace.value,
            "current_path": (
                str(self.state.current_path) if self.state.current_path else None
            ),
            "selection_index": self.state.selection_index,
            "filter_extensions": self.state.filter_extensions,
            "show_hidden": self.state.show_hidden,
            "entries": [e.to_dict() for e in self.state.entries],
            "workspaces": {ws.name: str(path) for ws, path in self.workspaces.items()},
        }

    # ─── File Type Classification ───────────────────────────────────

    def classify_file_type(self, extension: str) -> str:
        """Classify file by extension"""
        ext = (
            extension.lower() if extension.startswith(".") else f".{extension.lower()}"
        )
        for category, exts in self.FILE_TYPES.items():
            if ext in exts:
                return category
        return "other"


# ─── Convenience Function ───────────────────────────────────────────

_service_instance: FilePickerService = None


def get_file_picker_service(root_path: Path = None) -> FilePickerService:
    """Get singleton file picker service instance"""
    global _service_instance
    if _service_instance is None:
        _service_instance = FilePickerService(root_path)
    return _service_instance


# ─── Backwards Compatibility ────────────────────────────────────────

# For code using FilePicker directly
FilePicker = FilePickerService


# ─── Test ───────────────────────────────────────────────────────────

if __name__ == "__main__":
    service = FilePickerService()

    print(f"Root: {service.root}")
    print(f"Current workspace: {service.state.workspace.value}")
    print(f"Current path: {service.state.current_path}")
    print(f"Entries: {len(service.state.entries)}")

    # List directory via API
    result = service.list_directory()
    print(f"\nFiles: {result['files'][:5]}")
    print(f"Folders: {result['folders'][:5]}")

    # Test search
    matches = service.search("test", recursive=True)
    print(f"\nSearch 'test': {len(matches)} matches")
