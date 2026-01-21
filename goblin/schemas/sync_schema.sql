-- sync_queue: Pending block changes from Notion
CREATE TABLE IF NOT EXISTS sync_queue (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    notion_block_id TEXT NOT NULL,
    database_id TEXT NOT NULL,
    block_type TEXT,              -- heading_1, code, etc.
    runtime_type TEXT,            -- STATE, FORM, IF, etc. (if runtime block)
    action TEXT NOT NULL,         -- 'create' | 'update' | 'delete'
    payload JSON NOT NULL,        -- Full Notion block object
    status TEXT DEFAULT 'pending', -- pending, processing, completed, failed
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    processed_at DATETIME,
    error_message TEXT
);

-- sync_history: Completed syncs (audit log)
CREATE TABLE IF NOT EXISTS sync_history (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    notion_block_id TEXT NOT NULL,
    local_file_path TEXT,
    action TEXT,
    status TEXT,
    synced_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- block_mappings: Local ↔ Notion ID mapping
CREATE TABLE IF NOT EXISTS block_mappings (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    notion_block_id TEXT UNIQUE NOT NULL,
    local_file_path TEXT,
    content_hash TEXT,            -- SHA256 of content (conflict detection)
    last_synced DATETIME DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_sync_queue_status ON sync_queue(status);
CREATE INDEX IF NOT EXISTS idx_block_mappings_notion_id ON block_mappings(notion_block_id);
