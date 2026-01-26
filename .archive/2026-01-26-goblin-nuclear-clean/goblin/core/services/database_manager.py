"""
uDOS Database Manager

Unified interface for the uDOS database ecosystem:
- knowledge.db: markdowndb index of /knowledge
- core.db: uCODE scripts, TypeScript, uPY library
- contacts.db: BizIntel contacts
- devices.db: Sonic Screwdriver device registry
- scripts.db: Wizard server script library

Usage:
    from dev.goblin.core.services.database_manager import DatabaseManager

    db = DatabaseManager()

    # Search knowledge
    results = db.knowledge.search("water purification")

    # Get device by ID
    device = db.devices.get("D1")

    # Find contacts
    contacts = db.contacts.search("John")
"""

import sqlite3
import json
import os
from pathlib import Path
from typing import Dict, List, Optional, Any, Union
from dataclasses import dataclass, field
from datetime import datetime

from dev.goblin.core.services.logging_manager import get_logger

logger = get_logger("database-manager")


@dataclass
class DatabaseConfig:
    """Configuration for a database connection."""

    name: str
    path: Path
    tables: List[str] = field(default_factory=list)
    read_only: bool = False


class DatabaseConnection:
    """Base class for database connections."""

    def __init__(self, config: DatabaseConfig):
        self.config = config
        self._conn: Optional[sqlite3.Connection] = None

    def connect(self) -> sqlite3.Connection:
        """Get or create database connection."""
        if self._conn is None:
            # Ensure directory exists
            self.config.path.parent.mkdir(parents=True, exist_ok=True)

            uri = f"file:{self.config.path}"
            if self.config.read_only:
                uri += "?mode=ro"

            self._conn = sqlite3.connect(self.config.path, check_same_thread=False)
            self._conn.row_factory = sqlite3.Row
            logger.info(f"[LOCAL] Connected to {self.config.name}")

        return self._conn

    def close(self):
        """Close database connection."""
        if self._conn:
            self._conn.close()
            self._conn = None
            logger.info(f"[LOCAL] Closed {self.config.name}")

    def execute(self, sql: str, params: tuple = ()) -> sqlite3.Cursor:
        """Execute SQL query."""
        conn = self.connect()
        return conn.execute(sql, params)

    def executemany(self, sql: str, params_list: List[tuple]) -> sqlite3.Cursor:
        """Execute SQL query with multiple parameter sets."""
        conn = self.connect()
        return conn.executemany(sql, params_list)

    def commit(self):
        """Commit transaction."""
        if self._conn:
            self._conn.commit()

    def fetchall(self, sql: str, params: tuple = ()) -> List[Dict]:
        """Execute query and fetch all results as dicts."""
        cursor = self.execute(sql, params)
        return [dict(row) for row in cursor.fetchall()]

    def fetchone(self, sql: str, params: tuple = ()) -> Optional[Dict]:
        """Execute query and fetch one result as dict."""
        cursor = self.execute(sql, params)
        row = cursor.fetchone()
        return dict(row) if row else None


class KnowledgeDatabase(DatabaseConnection):
    """Knowledge bank database (markdowndb index)."""

    def __init__(self, base_path: Path):
        config = DatabaseConfig(
            name="knowledge.db",
            path=base_path / "knowledge.db",
            tables=["files", "file_tags", "file_links", "knowledge_coordinates"],
        )
        super().__init__(config)

    def initialize(self):
        """Create knowledge database schema."""
        conn = self.connect()
        conn.executescript(
            """
            -- Main files table (markdowndb compatible)
            CREATE TABLE IF NOT EXISTS files (
                id TEXT PRIMARY KEY,
                file_path TEXT NOT NULL UNIQUE,
                url_path TEXT,
                file_type TEXT DEFAULT 'md',
                metadata TEXT,  -- JSON frontmatter
                title TEXT,
                description TEXT,
                content_hash TEXT,
                word_count INTEGER,
                category TEXT,
                tier INTEGER DEFAULT 4,
                created_at TIMESTAMP,
                updated_at TIMESTAMP,
                indexed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
            
            -- Tags for files
            CREATE TABLE IF NOT EXISTS file_tags (
                file_id TEXT REFERENCES files(id),
                tag TEXT NOT NULL,
                PRIMARY KEY (file_id, tag)
            );
            
            -- Links between files
            CREATE TABLE IF NOT EXISTS file_links (
                source_id TEXT REFERENCES files(id),
                target_id TEXT REFERENCES files(id),
                link_text TEXT,
                link_type TEXT DEFAULT 'internal',
                PRIMARY KEY (source_id, target_id, link_text)
            );
            
            -- TILE coordinate links
            CREATE TABLE IF NOT EXISTS knowledge_coordinates (
                file_id TEXT REFERENCES files(id),
                tile_x INTEGER,
                tile_y INTEGER,
                tile_layer TEXT,
                location_name TEXT,
                PRIMARY KEY (file_id, tile_x, tile_y)
            );
            
            -- Indexes
            CREATE INDEX IF NOT EXISTS idx_files_category ON files(category);
            CREATE INDEX IF NOT EXISTS idx_files_tier ON files(tier);
            CREATE INDEX IF NOT EXISTS idx_tags_tag ON file_tags(tag);
            CREATE INDEX IF NOT EXISTS idx_coords_tile ON knowledge_coordinates(tile_x, tile_y);
        """
        )
        conn.commit()
        logger.info("[LOCAL] Initialized knowledge.db schema")

    def search(
        self,
        query: str,
        category: Optional[str] = None,
        tier: Optional[int] = None,
        limit: int = 20,
    ) -> List[Dict]:
        """Search knowledge files by content or metadata."""
        sql = """
            SELECT f.*, GROUP_CONCAT(t.tag) as tags
            FROM files f
            LEFT JOIN file_tags t ON f.id = t.file_id
            WHERE (f.title LIKE ? OR f.description LIKE ? OR f.file_path LIKE ?)
        """
        params = [f"%{query}%", f"%{query}%", f"%{query}%"]

        if category:
            sql += " AND f.category = ?"
            params.append(category)
        if tier:
            sql += " AND f.tier <= ?"
            params.append(tier)

        sql += " GROUP BY f.id ORDER BY f.title LIMIT ?"
        params.append(limit)

        return self.fetchall(sql, tuple(params))

    def get_by_path(self, file_path: str) -> Optional[Dict]:
        """Get knowledge file by path."""
        return self.fetchone("SELECT * FROM files WHERE file_path = ?", (file_path,))

    def get_by_category(self, category: str) -> List[Dict]:
        """Get all files in a category."""
        return self.fetchall(
            "SELECT * FROM files WHERE category = ? ORDER BY title", (category,)
        )

    def get_by_tag(self, tag: str) -> List[Dict]:
        """Get all files with a specific tag."""
        return self.fetchall(
            """
            SELECT f.* FROM files f
            JOIN file_tags t ON f.id = t.file_id
            WHERE t.tag = ?
            ORDER BY f.title
        """,
            (tag,),
        )

    def get_by_tile(self, tile_x: int, tile_y: int) -> List[Dict]:
        """Get knowledge linked to TILE coordinates."""
        return self.fetchall(
            """
            SELECT f.*, k.tile_layer, k.location_name
            FROM files f
            JOIN knowledge_coordinates k ON f.id = k.file_id
            WHERE k.tile_x = ? AND k.tile_y = ?
        """,
            (tile_x, tile_y),
        )

    def index_file(self, file_path: str, metadata: Dict, content: str):
        """Index a knowledge file."""
        file_id = Path(file_path).stem

        self.execute(
            """
            INSERT OR REPLACE INTO files
            (id, file_path, title, description, metadata, category, tier, 
             word_count, updated_at, indexed_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
            (
                file_id,
                file_path,
                metadata.get("title", file_id),
                metadata.get("description", ""),
                json.dumps(metadata),
                metadata.get("category", ""),
                metadata.get("tier", 4),
                len(content.split()),
                metadata.get("updated", datetime.now().isoformat()),
                datetime.now().isoformat(),
            ),
        )

        # Index tags
        if "tags" in metadata:
            self.execute("DELETE FROM file_tags WHERE file_id = ?", (file_id,))
            for tag in metadata["tags"]:
                self.execute(
                    "INSERT INTO file_tags (file_id, tag) VALUES (?, ?)", (file_id, tag)
                )

        self.commit()
        logger.info(f"[LOCAL] Indexed {file_path}")


class CoreDatabase(DatabaseConnection):
    """Core scripts and code database."""

    def __init__(self, base_path: Path):
        config = DatabaseConfig(
            name="core.db",
            path=base_path / "core.db",
            tables=["scripts", "script_tags", "upy_functions", "ts_components"],
        )
        super().__init__(config)

    def initialize(self):
        """Create core database schema."""
        conn = self.connect()
        conn.executescript(
            """
            -- Scripts (uCODE, uPY, shell)
            CREATE TABLE IF NOT EXISTS scripts (
                id TEXT PRIMARY KEY,
                name TEXT NOT NULL,
                language TEXT NOT NULL,
                file_path TEXT,
                content TEXT,
                description TEXT,
                author TEXT,
                version TEXT,
                category TEXT,
                is_system BOOLEAN DEFAULT FALSE,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP
            );
            
            -- Script tags
            CREATE TABLE IF NOT EXISTS script_tags (
                script_id TEXT REFERENCES scripts(id),
                tag TEXT NOT NULL,
                PRIMARY KEY (script_id, tag)
            );
            
            -- uPY function library
            CREATE TABLE IF NOT EXISTS upy_functions (
                id TEXT PRIMARY KEY,
                name TEXT NOT NULL,
                signature TEXT,
                docstring TEXT,
                source TEXT,
                module TEXT,
                category TEXT,
                is_builtin BOOLEAN DEFAULT FALSE,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
            
            -- TypeScript components (for Tauri app)
            CREATE TABLE IF NOT EXISTS ts_components (
                id TEXT PRIMARY KEY,
                name TEXT NOT NULL,
                component_type TEXT,
                file_path TEXT,
                props TEXT,  -- JSON
                description TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
            
            -- Link to knowledge
            CREATE TABLE IF NOT EXISTS script_knowledge_links (
                script_id TEXT REFERENCES scripts(id),
                file_path TEXT,
                link_type TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                PRIMARY KEY (script_id, file_path)
            );
            
            -- Indexes
            CREATE INDEX IF NOT EXISTS idx_scripts_language ON scripts(language);
            CREATE INDEX IF NOT EXISTS idx_scripts_category ON scripts(category);
            CREATE INDEX IF NOT EXISTS idx_upy_module ON upy_functions(module);
        """
        )
        conn.commit()
        logger.info("[LOCAL] Initialized core.db schema")

    def get_scripts(
        self, language: Optional[str] = None, category: Optional[str] = None
    ) -> List[Dict]:
        """Get scripts optionally filtered by language or category."""
        sql = "SELECT * FROM scripts WHERE 1=1"
        params = []

        if language:
            sql += " AND language = ?"
            params.append(language)
        if category:
            sql += " AND category = ?"
            params.append(category)

        sql += " ORDER BY name"
        return self.fetchall(sql, tuple(params))

    def get_script(self, script_id: str) -> Optional[Dict]:
        """Get script by ID."""
        return self.fetchone("SELECT * FROM scripts WHERE id = ?", (script_id,))

    def search_scripts(self, query: str) -> List[Dict]:
        """Search scripts by name or description."""
        return self.fetchall(
            """
            SELECT * FROM scripts
            WHERE name LIKE ? OR description LIKE ?
            ORDER BY name
        """,
            (f"%{query}%", f"%{query}%"),
        )

    def get_upy_functions(self, module: Optional[str] = None) -> List[Dict]:
        """Get uPY functions optionally filtered by module."""
        if module:
            return self.fetchall(
                "SELECT * FROM upy_functions WHERE module = ? ORDER BY name", (module,)
            )
        return self.fetchall("SELECT * FROM upy_functions ORDER BY module, name")

    def add_script(self, name: str, language: str, content: str, **kwargs):
        """Add a script to the database."""
        script_id = f"{language}-{name}".lower().replace(" ", "-")

        self.execute(
            """
            INSERT OR REPLACE INTO scripts
            (id, name, language, content, description, author, version, 
             category, is_system, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
            (
                script_id,
                name,
                language,
                content,
                kwargs.get("description", ""),
                kwargs.get("author", "system"),
                kwargs.get("version", "1.0.0"),
                kwargs.get("category", ""),
                kwargs.get("is_system", False),
                datetime.now().isoformat(),
            ),
        )
        self.commit()
        return script_id


class ContactsDatabase(DatabaseConnection):
    """BizIntel contacts database."""

    def __init__(self, base_path: Path):
        config = DatabaseConfig(
            name="contacts.db",
            path=base_path / "user" / "contacts.db",
            tables=["businesses", "people", "contact_tags"],
        )
        super().__init__(config)

    def initialize(self):
        """Create contacts database schema."""
        conn = self.connect()
        conn.executescript(
            """
            -- Businesses
            CREATE TABLE IF NOT EXISTS businesses (
                id TEXT PRIMARY KEY,
                name TEXT NOT NULL,
                category TEXT,
                address TEXT,
                phone TEXT,
                email TEXT,
                website TEXT,
                notes TEXT,
                tile_x INTEGER,
                tile_y INTEGER,
                rating INTEGER,
                last_contact TIMESTAMP,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP
            );
            
            -- People
            CREATE TABLE IF NOT EXISTS people (
                id TEXT PRIMARY KEY,
                name TEXT NOT NULL,
                business_id TEXT REFERENCES businesses(id),
                role TEXT,
                phone TEXT,
                email TEXT,
                notes TEXT,
                last_contact TIMESTAMP,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP
            );
            
            -- Contact tags
            CREATE TABLE IF NOT EXISTS contact_tags (
                contact_id TEXT,
                contact_type TEXT,  -- 'business' or 'person'
                tag TEXT NOT NULL,
                PRIMARY KEY (contact_id, contact_type, tag)
            );
            
            -- Link to knowledge
            CREATE TABLE IF NOT EXISTS business_knowledge_links (
                business_id TEXT REFERENCES businesses(id),
                file_path TEXT,
                link_type TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                PRIMARY KEY (business_id, file_path)
            );
            
            -- Indexes
            CREATE INDEX IF NOT EXISTS idx_businesses_category ON businesses(category);
            CREATE INDEX IF NOT EXISTS idx_businesses_tile ON businesses(tile_x, tile_y);
            CREATE INDEX IF NOT EXISTS idx_people_business ON people(business_id);
        """
        )
        conn.commit()
        logger.info("[LOCAL] Initialized contacts.db schema")

    def search(
        self, query: str, contact_type: Optional[str] = None
    ) -> Dict[str, List[Dict]]:
        """Search contacts by name."""
        results = {"businesses": [], "people": []}

        if not contact_type or contact_type == "business":
            results["businesses"] = self.fetchall(
                """
                SELECT * FROM businesses
                WHERE name LIKE ? OR category LIKE ?
                ORDER BY name
            """,
                (f"%{query}%", f"%{query}%"),
            )

        if not contact_type or contact_type == "person":
            results["people"] = self.fetchall(
                """
                SELECT p.*, b.name as business_name
                FROM people p
                LEFT JOIN businesses b ON p.business_id = b.id
                WHERE p.name LIKE ? OR p.role LIKE ?
                ORDER BY p.name
            """,
                (f"%{query}%", f"%{query}%"),
            )

        return results

    def get_business(self, business_id: str) -> Optional[Dict]:
        """Get business by ID."""
        return self.fetchone("SELECT * FROM businesses WHERE id = ?", (business_id,))

    def get_person(self, person_id: str) -> Optional[Dict]:
        """Get person by ID."""
        return self.fetchone(
            """
            SELECT p.*, b.name as business_name
            FROM people p
            LEFT JOIN businesses b ON p.business_id = b.id
            WHERE p.id = ?
        """,
            (person_id,),
        )

    def get_by_tile(self, tile_x: int, tile_y: int) -> List[Dict]:
        """Get businesses at TILE coordinates."""
        return self.fetchall(
            "SELECT * FROM businesses WHERE tile_x = ? AND tile_y = ?", (tile_x, tile_y)
        )


class DevicesDatabase(DatabaseConnection):
    """Sonic Screwdriver device registry."""

    def __init__(self, base_path: Path):
        config = DatabaseConfig(
            name="devices.db",
            path=base_path / "wizard" / "devices.db",
            tables=["devices", "device_connections", "firmware_packages"],
        )
        super().__init__(config)

    def initialize(self):
        """Create devices database schema."""
        conn = self.connect()
        conn.executescript(
            """
            -- Device registry
            CREATE TABLE IF NOT EXISTS devices (
                id TEXT PRIMARY KEY,
                hardware_type TEXT NOT NULL,
                firmware_version TEXT,
                device_role TEXT DEFAULT 'node',
                mesh_channel INTEGER DEFAULT 1,
                friendly_name TEXT,
                public_key TEXT,
                last_seen TIMESTAMP,
                status TEXT DEFAULT 'offline',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP
            );
            
            -- Device connections
            CREATE TABLE IF NOT EXISTS device_connections (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                device_id TEXT REFERENCES devices(id),
                connection_type TEXT,
                connection_string TEXT,
                signal_strength INTEGER,
                latency_ms INTEGER,
                last_contact TIMESTAMP
            );
            
            -- Firmware packages
            CREATE TABLE IF NOT EXISTS firmware_packages (
                id TEXT PRIMARY KEY,
                package_name TEXT NOT NULL,
                version TEXT NOT NULL,
                chip_type TEXT NOT NULL,
                file_path TEXT,
                file_size INTEGER,
                sha256 TEXT,
                features TEXT,
                release_date TIMESTAMP,
                is_stable BOOLEAN DEFAULT TRUE,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
            
            -- Device firmware history
            CREATE TABLE IF NOT EXISTS device_firmware_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                device_id TEXT REFERENCES devices(id),
                firmware_id TEXT REFERENCES firmware_packages(id),
                installed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                install_method TEXT,
                success BOOLEAN
            );
            
            -- Link to knowledge
            CREATE TABLE IF NOT EXISTS device_knowledge_links (
                device_id TEXT REFERENCES devices(id),
                file_path TEXT,
                link_type TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                PRIMARY KEY (device_id, file_path)
            );
            
            -- Indexes
            CREATE INDEX IF NOT EXISTS idx_devices_status ON devices(status);
            CREATE INDEX IF NOT EXISTS idx_devices_role ON devices(device_role);
            CREATE INDEX IF NOT EXISTS idx_firmware_chip ON firmware_packages(chip_type);
        """
        )
        conn.commit()
        logger.info("[LOCAL] Initialized devices.db schema")

    def get(self, device_id: str) -> Optional[Dict]:
        """Get device by ID."""
        return self.fetchone("SELECT * FROM devices WHERE id = ?", (device_id,))

    def get_all(self, status: Optional[str] = None) -> List[Dict]:
        """Get all devices optionally filtered by status."""
        if status:
            return self.fetchall(
                "SELECT * FROM devices WHERE status = ? ORDER BY friendly_name",
                (status,),
            )
        return self.fetchall("SELECT * FROM devices ORDER BY friendly_name")

    def get_by_role(self, role: str) -> List[Dict]:
        """Get devices by role."""
        return self.fetchall(
            "SELECT * FROM devices WHERE device_role = ? ORDER BY friendly_name",
            (role,),
        )

    def update_status(self, device_id: str, status: str):
        """Update device status."""
        self.execute(
            """
            UPDATE devices 
            SET status = ?, last_seen = ?, updated_at = ?
            WHERE id = ?
        """,
            (status, datetime.now().isoformat(), datetime.now().isoformat(), device_id),
        )
        self.commit()

    def register_device(self, device_id: str, hardware_type: str, **kwargs):
        """Register a new device."""
        self.execute(
            """
            INSERT OR REPLACE INTO devices
            (id, hardware_type, firmware_version, device_role, mesh_channel,
             friendly_name, status, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """,
            (
                device_id,
                hardware_type,
                kwargs.get("firmware_version", ""),
                kwargs.get("device_role", "node"),
                kwargs.get("mesh_channel", 1),
                kwargs.get("friendly_name", device_id),
                kwargs.get("status", "offline"),
                datetime.now().isoformat(),
            ),
        )
        self.commit()
        logger.info(f"[LOCAL] Registered device {device_id}")


class ScriptsDatabase(DatabaseConnection):
    """Wizard server script library."""

    def __init__(self, base_path: Path):
        config = DatabaseConfig(
            name="scripts.db",
            path=base_path / "wizard" / "scripts.db",
            tables=["wizard_scripts", "ai_providers", "web_tools"],
        )
        super().__init__(config)

    def initialize(self):
        """Create scripts database schema."""
        conn = self.connect()
        conn.executescript(
            """
            -- Wizard scripts
            CREATE TABLE IF NOT EXISTS wizard_scripts (
                id TEXT PRIMARY KEY,
                name TEXT NOT NULL,
                script_type TEXT,
                content TEXT,
                description TEXT,
                triggers TEXT,  -- JSON array of trigger conditions
                enabled BOOLEAN DEFAULT TRUE,
                last_run TIMESTAMP,
                run_count INTEGER DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP
            );
            
            -- AI provider configurations
            CREATE TABLE IF NOT EXISTS ai_providers (
                id TEXT PRIMARY KEY,
                name TEXT NOT NULL,
                provider_type TEXT,
                api_endpoint TEXT,
                model TEXT,
                config TEXT,  -- JSON
                is_active BOOLEAN DEFAULT FALSE,
                usage_count INTEGER DEFAULT 0,
                last_used TIMESTAMP,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
            
            -- Web scraping tools
            CREATE TABLE IF NOT EXISTS web_tools (
                id TEXT PRIMARY KEY,
                name TEXT NOT NULL,
                tool_type TEXT,
                url_pattern TEXT,
                selector TEXT,
                config TEXT,  -- JSON
                enabled BOOLEAN DEFAULT TRUE,
                last_run TIMESTAMP,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
            
            -- Link to knowledge
            CREATE TABLE IF NOT EXISTS script_knowledge_links (
                script_id TEXT REFERENCES wizard_scripts(id),
                file_path TEXT,
                link_type TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                PRIMARY KEY (script_id, file_path)
            );
            
            -- Indexes
            CREATE INDEX IF NOT EXISTS idx_scripts_type ON wizard_scripts(script_type);
            CREATE INDEX IF NOT EXISTS idx_providers_type ON ai_providers(provider_type);
        """
        )
        conn.commit()
        logger.info("[LOCAL] Initialized scripts.db schema")

    def get_scripts(
        self, script_type: Optional[str] = None, enabled_only: bool = True
    ) -> List[Dict]:
        """Get wizard scripts."""
        sql = "SELECT * FROM wizard_scripts WHERE 1=1"
        params = []

        if script_type:
            sql += " AND script_type = ?"
            params.append(script_type)
        if enabled_only:
            sql += " AND enabled = TRUE"

        sql += " ORDER BY name"
        return self.fetchall(sql, tuple(params))

    def get_providers(self, active_only: bool = True) -> List[Dict]:
        """Get AI providers."""
        if active_only:
            return self.fetchall(
                "SELECT * FROM ai_providers WHERE is_active = TRUE ORDER BY name"
            )
        return self.fetchall("SELECT * FROM ai_providers ORDER BY name")

    def get_active_provider(self) -> Optional[Dict]:
        """Get the currently active AI provider."""
        return self.fetchone(
            "SELECT * FROM ai_providers WHERE is_active = TRUE LIMIT 1"
        )


class DatabaseManager:
    """
    Unified database manager for uDOS.

    Provides access to all databases through a single interface:
        db = DatabaseManager()
        db.knowledge.search("water")
        db.devices.get("D1")
        db.contacts.search("John")
    """

    def __init__(self, base_path: Optional[Path] = None):
        """
        Initialize database manager.

        Args:
            base_path: Base path for databases (default: memory/bank/)
        """
        if base_path is None:
            # Get project root from this file's location
            project_root = Path(__file__).parent.parent.parent
            base_path = project_root / "memory" / "bank"

        self.base_path = Path(base_path)

        # Initialize database connections
        self.knowledge = KnowledgeDatabase(self.base_path)
        self.core = CoreDatabase(self.base_path)
        self.contacts = ContactsDatabase(self.base_path)
        self.devices = DevicesDatabase(self.base_path)
        self.scripts = ScriptsDatabase(self.base_path)

        logger.info(f"[LOCAL] DatabaseManager initialized at {self.base_path}")

    def initialize_all(self):
        """Initialize all database schemas."""
        self.knowledge.initialize()
        self.core.initialize()
        self.contacts.initialize()
        self.devices.initialize()
        self.scripts.initialize()
        logger.info("[LOCAL] All databases initialized")

    def close_all(self):
        """Close all database connections."""
        self.knowledge.close()
        self.core.close()
        self.contacts.close()
        self.devices.close()
        self.scripts.close()
        logger.info("[LOCAL] All database connections closed")

    def stats(self) -> Dict[str, Dict]:
        """Get statistics for all databases."""
        stats = {}

        try:
            stats["knowledge"] = {
                "files": (
                    self.knowledge.fetchone("SELECT COUNT(*) as count FROM files")[
                        "count"
                    ]
                    if self.knowledge._conn
                    else 0
                ),
                "tags": (
                    self.knowledge.fetchone(
                        "SELECT COUNT(DISTINCT tag) as count FROM file_tags"
                    )["count"]
                    if self.knowledge._conn
                    else 0
                ),
            }
        except:
            stats["knowledge"] = {"files": 0, "tags": 0}

        try:
            stats["core"] = {
                "scripts": (
                    self.core.fetchone("SELECT COUNT(*) as count FROM scripts")["count"]
                    if self.core._conn
                    else 0
                ),
                "functions": (
                    self.core.fetchone("SELECT COUNT(*) as count FROM upy_functions")[
                        "count"
                    ]
                    if self.core._conn
                    else 0
                ),
            }
        except:
            stats["core"] = {"scripts": 0, "functions": 0}

        try:
            stats["contacts"] = {
                "businesses": (
                    self.contacts.fetchone("SELECT COUNT(*) as count FROM businesses")[
                        "count"
                    ]
                    if self.contacts._conn
                    else 0
                ),
                "people": (
                    self.contacts.fetchone("SELECT COUNT(*) as count FROM people")[
                        "count"
                    ]
                    if self.contacts._conn
                    else 0
                ),
            }
        except:
            stats["contacts"] = {"businesses": 0, "people": 0}

        try:
            stats["devices"] = {
                "total": (
                    self.devices.fetchone("SELECT COUNT(*) as count FROM devices")[
                        "count"
                    ]
                    if self.devices._conn
                    else 0
                ),
                "online": (
                    self.devices.fetchone(
                        "SELECT COUNT(*) as count FROM devices WHERE status = 'online'"
                    )["count"]
                    if self.devices._conn
                    else 0
                ),
            }
        except:
            stats["devices"] = {"total": 0, "online": 0}

        try:
            stats["scripts"] = {
                "wizard": (
                    self.scripts.fetchone(
                        "SELECT COUNT(*) as count FROM wizard_scripts"
                    )["count"]
                    if self.scripts._conn
                    else 0
                ),
                "providers": (
                    self.scripts.fetchone(
                        "SELECT COUNT(*) as count FROM ai_providers WHERE is_active = TRUE"
                    )["count"]
                    if self.scripts._conn
                    else 0
                ),
            }
        except:
            stats["scripts"] = {"wizard": 0, "providers": 0}

        return stats

    def __enter__(self):
        """Context manager entry."""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.close_all()


# CLI interface
if __name__ == "__main__":
    import sys

    db = DatabaseManager()

    if len(sys.argv) < 2:
        print("Usage: python -m core.services.database_manager <command>")
        print()
        print("Commands:")
        print("  init     - Initialize all databases")
        print("  stats    - Show database statistics")
        print("  search   - Search knowledge")
        sys.exit(0)

    command = sys.argv[1].lower()

    if command == "init":
        db.initialize_all()
        print("✅ All databases initialized")

    elif command == "stats":
        stats = db.stats()
        print("\n📊 Database Statistics")
        print("=" * 40)
        for name, data in stats.items():
            print(f"\n{name}:")
            for key, value in data.items():
                print(f"  {key}: {value}")

    elif command == "search":
        if len(sys.argv) < 3:
            print("Usage: python -m core.services.database_manager search <query>")
            sys.exit(1)
        query = " ".join(sys.argv[2:])
        results = db.knowledge.search(query)
        print(f"\nFound {len(results)} results for '{query}':")
        for r in results[:10]:
            print(f"  - {r.get('title', r.get('file_path'))}")

    db.close_all()
