# Move 1: Notion Integration Quick Start

**Mission:** Webhook-driven Notion sync with Notion-compatible markdown blocks  
**Component:** Goblin Dev Server (`/dev/goblin/`)  
**Service:** `NotionSyncService` (already scaffolded)  
**Status:** Ready for implementation

---

## Setup Steps

### 1. Create Notion Internal Integration

1. Visit [https://www.notion.so/my-integrations](https://www.notion.so/my-integrations)
2. Click "Create new integration"
3. Name: `uDOS Dev`
4. Associate with workspace
5. Copy **Internal Integration Token** → Save to `dev/goblin/config/goblin.json` as `notion_api_key`

### 2. Grant Integration Permissions

In your Notion workspace:

1. Open a test page
2. Click share icon (top right)
3. Search for "uDOS Dev" integration
4. Grant access (Read, Update, Insert, Delete)
5. Copy **page_id** from URL → `dev/goblin/config/goblin.json` as `notion_test_page_id`

**URL format:** `https://notion.so/{workspace}/{page_id}?v={...}`  
Extract: `page_id` (32 hex chars before `?v`)

### 3. Configure Notion Webhook

1. Go to "Integrations" settings in your workspace
2. Select "uDOS Dev" integration
3. Enable "Webhooks"
4. Subscribe to events:
   - `page_update`
   - `block_update`
   - `database_update`
5. Webhook URL: `http://localhost:8767/api/v0/notion/webhook`
6. Copy **Webhook Secret** → Save to `goblin.json` as `notion_webhook_secret`

### 4. Update Configuration

File: `dev/goblin/config/goblin.json`

```json
{
  "notion": {
    "api_key": "secret_...",
    "webhook_secret": "whsec_...",
    "test_page_id": "xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx",
    "sync_mode": "bidirectional",
    "auto_publish": false
  }
}
```

---

## Implementation Phases

### Phase A: Block Mapping (Week 1)

**Goal:** Parse markdown → Notion blocks → Notion API format

**Files:**

- `dev/goblin/services/block_mapper.py` — Parse/convert logic
- `dev/goblin/schemas/block_schema.py` — Block data classes

**Spec:** [Notion-Compatible Block Architecture](../../docs/specs/notion-compatible-blocks.md)

````python
from dev.goblin.services.block_mapper import BlockMapper

mapper = BlockMapper()

# Parse markdown
blocks = mapper.parse_markdown("""
# Title

This is a paragraph.

```state
name: string = "Alice"
````

""")

# Convert to Notion format

notion_blocks = mapper.to_notion_api(blocks)

# → Sends to Notion API

# Convert back from Notion

markdown = mapper.from_notion_blocks(notion_blocks)

# → Back to markdown

````

**Checkpoint:** Test all block types in both directions

### Phase B: Webhook Handler (Week 1-2)

**Goal:** Receive Notion changes, queue for sync

**Files:**
- `dev/goblin/services/notion_sync_service.py` — Webhook + queue
- `dev/goblin/schemas/sync_queue.py` — SQLite schema

**Endpoint:** `POST /api/v0/notion/webhook`

```python
# Incoming Notion change
@app.post("/api/v0/notion/webhook")
async def handle_notion_webhook(request: Request):
    payload = await request.json()

    # Verify webhook signature
    signature = request.headers.get("x-notion-signature")
    if not verify_signature(signature, payload):
        return {"error": "Invalid signature"}, 401

    # Queue for sync
    await sync_service.queue_change(payload)
    return {"ok": True}
````

**SQLite Queue Schema:**

```sql
CREATE TABLE sync_queue (
  id INTEGER PRIMARY KEY,
  notion_id TEXT,
  change_type TEXT,  -- 'page_update', 'block_update'
  payload JSON,
  status TEXT,       -- 'pending', 'syncing', 'done', 'error'
  created_at DATETIME,
  synced_at DATETIME,
  error_message TEXT
);

CREATE TABLE block_mappings (
  id INTEGER PRIMARY KEY,
  local_path TEXT,        -- .md file path
  notion_page_id TEXT,    -- Notion page
  notion_block_id TEXT,   -- Specific block in page
  block_type TEXT,        -- 'state', 'paragraph', etc
  last_synced DATETIME,
  conflict_resolution TEXT  -- 'local', 'notion', 'manual'
);
```

**Checkpoint:** Webhook receives events, queue stores them

### Phase C: Bidirectional Sync (Week 2-3)

**Goal:** Sync local .md → Notion and Notion → local .md

**Files:**

- `dev/goblin/services/sync_executor.py` — Sync logic
- `dev/goblin/schemas/conflict_resolution.py` — Merge strategy

```python
# Sync local file to Notion
await sync_service.sync_to_notion(
    page_id="...",
    local_path="memory/ucode/project.md"
)

# Sync from Notion to local
markdown = await sync_service.sync_from_notion(
    page_id="...",
    output_path="memory/ucode/project.md"
)

# Resolve conflicts (Notion vs local changed)
merged = await sync_service.resolve_conflict(
    local_content="...",
    notion_blocks=[...],
    strategy="last-write-wins"  # or "manual"
)
```

**Conflict Resolution Strategies:**

1. **last-write-wins** — Later timestamp wins
2. **local-priority** — Keep local changes
3. **notion-priority** — Keep Notion changes
4. **manual** — Flag for user review

**Checkpoint:** Bidirectional sync works, conflicts resolved

### Phase D: Testing (Week 3)

**Goal:** Verify all block types sync correctly

**Tests:**

1. Standard markdown (h1, p, lists, quotes, etc.)
2. Runtime blocks (state, form, if, etc.)
3. Rich text (bold, italic, links, code)
4. Nested blocks (panel columns, toggle children)
5. Conflict resolution (concurrent edits)

**Test Workflow:**

````bash
# 1. Create test .md file
cat > memory/ucode/test-notion.md << 'EOF'
# Test Page

## Section 1

Standard paragraph text.

```state
name: string = "Test"
````

- Item 1
- Item 2

> Quote here

EOF

# 2. Sync to Notion

curl -X POST http://localhost:8767/api/v0/notion/sync \
 -H "Content-Type: application/json" \
 -d '{"page_id":"...", "local_path":"memory/ucode/test-notion.md"}'

# 3. Verify in Notion workspace

# (Check that blocks appeared correctly)

# 4. Make change in Notion

# (Edit a paragraph, add a block)

# 5. Receive webhook

# (Should auto-trigger)

# 6. Verify local .md updated

cat memory/ucode/test-notion.md

# (Should show Notion changes)

```

**Checkpoint:** All blocks sync bidirectionally without corruption

---

## API Endpoints (Goblin Dev Server)

```

POST /api/v0/notion/webhook Handle Notion webhooks
GET /api/v0/notion/sync/status View sync queue
POST /api/v0/notion/sync/to-notion Upload .md → Notion
POST /api/v0/notion/sync/from-notion Download Notion → .md
GET /api/v0/notion/maps View block mappings
POST /api/v0/notion/maps/resolve Resolve conflicts

````

---

## Dependencies

```txt
# requirements.txt additions
notion-client==2.0.0        # Official Notion Python SDK
pydantic==2.0.0            # Data validation
sqlalchemy==2.0.0          # ORM
aiosqlite==0.19.0          # Async SQLite
````

---

## Next Steps

1. ✅ Architecture designed (Notion-compatible blocks)
2. ✅ Configuration template created
3. ✅ Webhooks documented
4. ⏳ **Phase A:** Implement `BlockMapper` (parse/convert)
5. ⏳ **Phase B:** Implement webhook handler + queue
6. ⏳ **Phase C:** Implement bidirectional sync
7. ⏳ **Phase D:** Test with real Notion workspace

**Estimated Time:** 20-30 hours  
**Start:** When ready to implement Phase A

---

## References

- [Notion Block Reference](https://developers.notion.com/reference/block)
- [Notion Webhooks](https://developers.notion.com/reference/webhooks)
- [Notion Python SDK](https://github.com/ramnes/notion-sdk-py)
- [Notion-Compatible Block Spec](../../docs/specs/notion-compatible-blocks.md)
- [Move 1 Plan](../../docs/roadmap.md#move-1-notion-sync-integration-python-based)

---

_Ready to begin Move 1 when you give the signal!_
