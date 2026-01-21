# Phase B: Webhook Handler + SQLite Queue

**Purpose:** Implement Notion webhook endpoint on Goblin Dev Server to receive block updates from Notion

**Timeline:** 6-8 hours (4 implementation steps)

---

## Architecture

### Flow

```
Notion Workspace
    ↓ (webhook POST)
Goblin /api/v0/notion/webhook
    ↓ (verify signature)
NotionSyncService.enqueue_webhook()
    ↓ (store in SQLite)
sync_queue table (async processing)
    ↓ (next phase: process queue)
BlockMapper.from_notion_blocks()
    ↓ (convert to markdown)
Local markdown file
```

### Components

1. **`dev/goblin/routes/notion.py`** — FastAPI routes

   - `POST /api/v0/notion/webhook` — Receive webhooks
   - `GET /api/v0/notion/status` — Check sync status
   - `POST /api/v0/notion/sync/manual` — Trigger manual sync (dev)

2. **`dev/goblin/services/notion_sync_service.py`** — Sync logic

   - `verify_webhook_signature()` — HMAC-SHA256 verification
   - `enqueue_webhook()` — Parse and queue changes
   - `get_sync_status()` — Return queue stats
   - `list_pending_syncs()` — View queued blocks

3. **SQLite Tables** — Data storage
   - `sync_queue` — Pending block changes
   - `sync_history` — Completed syncs (audit log)
   - `block_mappings` — Local → Notion ID mapping

---

## Step 1: Create Notion Routes (1-2 hours)

### File: `dev/goblin/routes/notion.py`

```python
from fastapi import APIRouter, Request, HTTPException
from dev.goblin.services.notion_sync_service import NotionSyncService

router = APIRouter(prefix="/api/v0/notion", tags=["notion"])
sync_service = NotionSyncService()

@router.post("/webhook")
async def notion_webhook(request: Request):
    """
    Receive Notion webhook notifications

    Notion sends:
    - Block updates (create, update, delete)
    - Payload: {type, request_id, timestamp, changes[]}
    """
    # 1. Verify webhook signature (HMAC)
    # 2. Extract changes
    # 3. Parse block metadata
    # 4. Queue for processing
    # 5. Return 200 OK
    pass

@router.get("/status")
async def sync_status():
    """Get sync queue status"""
    return sync_service.get_sync_status()

@router.post("/sync/manual")
async def manual_sync(database_id: str = None):
    """Trigger manual sync (dev only)"""
    return sync_service.manual_sync(database_id)
```

**Checkpoint:** Webhook route accepts POST, verifies signature, stores in queue

---

## Step 2: Implement NotionSyncService (2-3 hours)

### File: `dev/goblin/services/notion_sync_service.py`

```python
import hmac
import hashlib
from datetime import datetime
import sqlite3

class NotionSyncService:
    """Manage Notion webhook processing and queue"""

    def __init__(self):
        self.webhook_secret = os.getenv("NOTION_WEBHOOK_SECRET")
        self.db = sqlite3.connect("memory/goblin/sync.db")
        self._init_tables()

    def verify_webhook_signature(self, body: bytes, signature: str) -> bool:
        """Verify Notion webhook HMAC-SHA256"""
        # Notion sends: X-Notion-Signature header
        # Format: Signature=<hmac>
        # Algorithm: HMAC-SHA256(secret, body)
        pass

    def enqueue_webhook(self, payload: dict) -> dict:
        """Parse webhook and queue blocks"""
        # 1. Extract changes from payload
        # 2. For each block change (create/update/delete):
        #    - Get block type
        #    - Extract metadata (caption, rich_text)
        #    - Determine runtime block type (STATE, FORM, IF, etc.)
        # 3. Insert into sync_queue
        # 4. Return: {queued: N, failed: 0}
        pass

    def get_sync_status(self) -> dict:
        """Return queue stats"""
        return {
            "queued": self.db.count("sync_queue WHERE status='pending'"),
            "processing": self.db.count("sync_queue WHERE status='processing'"),
            "completed": self.db.count("sync_queue WHERE status='completed'"),
            "failed": self.db.count("sync_queue WHERE status='failed'")
        }
```

**Checkpoint:** Webhook signature verified, blocks queued to SQLite

---

## Step 3: Create SQLite Schema (30 minutes)

### File: `dev/goblin/schemas/sync_schema.sql`

```sql
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
```

**Checkpoint:** Schema created, tables ready for queueing

---

## Step 4: Wire into Goblin Server (1-2 hours)

### File: `dev/goblin/server.py` (update)

```python
from dev.goblin.routes import notion

# Initialize Goblin server
app = FastAPI()

# Mount routes
app.include_router(notion.router)

# Initialize sync service
from dev.goblin.services.notion_sync_service import NotionSyncService
sync_service = NotionSyncService()

@app.on_event("startup")
async def startup():
    """Initialize services"""
    sync_service._init_tables()
    print("✅ Notion sync service ready on /api/v0/notion")
```

**Checkpoint:** Routes mounted, server ready to receive webhooks

---

## Testing Phase B

### 1. Verify Webhook Reception

```bash
# Start Goblin server
python dev/goblin/server.py

# In another terminal, simulate webhook
curl -X POST http://localhost:8767/api/v0/notion/webhook \
  -H "Content-Type: application/json" \
  -H "X-Notion-Signature: Signature=test" \
  -d '{"type":"block.update","object":"block"}'
```

### 2. Verify Signature Verification

```python
# Test signature verification
from dev.goblin.services.notion_sync_service import NotionSyncService

service = NotionSyncService()
valid = service.verify_webhook_signature(
    b"test body",
    "Signature=correct_hmac"
)
assert valid == True
```

### 3. Verify Queue Storage

```python
# Check sync_queue table
cursor = service.db.execute("SELECT COUNT(*) FROM sync_queue WHERE status='pending'")
pending = cursor.fetchone()[0]
print(f"Pending syncs: {pending}")
```

### 4. Create Real Test

```python
# Add blocks to your Notion database
# Edit a block in Notion
# Webhook fires → captured in sync_queue
# Check queue: service.get_sync_status()
# Should show: queued=1, pending=1
```

---

## Validation Checklist

- [ ] POST /api/v0/notion/webhook returns 200 OK
- [ ] X-Notion-Signature verified (HMAC-SHA256)
- [ ] Blocks queued to sync_queue with correct action (create/update/delete)
- [ ] Block type detected (heading_1, code, etc.)
- [ ] Runtime type identified (STATE, FORM, IF captions)
- [ ] sync_history logs completed operations
- [ ] /api/v0/notion/status returns accurate counts
- [ ] Failed blocks have error_message recorded
- [ ] Can manually trigger sync via /api/v0/notion/sync/manual

---

## Next: Phase C

After Phase B complete:

- Implement `sync_executor.py` — Process queue
- Add `sync_to_notion()` — Push local changes to Notion
- Add `sync_from_notion()` — Pull Notion changes to local
- Implement conflict resolution (last-write-wins)

---

## Files to Create

| File                                         | Lines | Purpose         |
| -------------------------------------------- | ----- | --------------- |
| `dev/goblin/routes/notion.py`                | 100+  | Webhook routes  |
| `dev/goblin/services/notion_sync_service.py` | 200+  | Sync logic      |
| `dev/goblin/schemas/sync_schema.sql`         | 50    | Database schema |
| `dev/goblin/tests/test_notion_sync.py`       | 150+  | Unit tests      |

**Total:** ~500 lines code + tests

---

**Status:** Ready to implement Phase B  
**Depends on:** Phase A (BlockMapper) ✅  
**Estimated:** 6-8 hours
