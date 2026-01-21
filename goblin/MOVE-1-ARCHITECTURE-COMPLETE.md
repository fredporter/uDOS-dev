# Move 1: Notion-Compatible Blocks — Architecture Complete

**Date:** 2026-01-15  
**Status:** ✅ Architecture & specification complete, ready for implementation  
**Next:** Begin Phase A (BlockMapper implementation)

---

## What We Just Did

### 1. **Notion-Compatible Block Design** ✅

Created a specification that maps uDOS markdown blocks directly to Notion's block API:

**Standard Blocks (Notion-native):**

- Headings (h1, h2, h3) → `heading_1`, `heading_2`, `heading_3`
- Paragraphs → `paragraph`
- Quotes → `quote`
- Lists → `bulleted_list_item`, `numbered_list_item`
- Todo → `to_do`
- Code blocks → `code`
- Links → `bookmark`
- Images → `image`
- Dividers → `divider`

**Runtime Blocks (uDOS-specific, synced to Notion):**

- `STATE` → `code` with metadata
- `SET` → `code` with metadata
- `FORM` → `code` with form fields
- `IF` → `toggle` (collapsible heading)
- `NAV` → `callout` (navigation links)
- `PANEL` → `column_list` + `column`
- `MAP` → `table` (data grid)

**Key Insight:** Runtime blocks map to Notion blocks (code/toggle/callout/table), so they can sync bidirectionally. Same blocks work on desktop (Python) + mobile (TypeScript).

### 2. **Move 1 Documentation** ✅

Created three linked documents:

1. **[Notion-Compatible Block Architecture](../../docs/specs/notion-compatible-blocks.md)** — Design spec

   - Block mapping tables
   - Markdown syntax examples
   - Notion JSON payloads
   - Implementation strategy (Phase 1-3)

2. **[Move 1 Quick Start](./MOVE-1-QUICK-START.md)** — Setup & phases

   - Notion integration setup (create API key, webhook secret)
   - 4 implementation phases (A-D)
   - SQLite schema (sync_queue, block_mappings)
   - API endpoints
   - Test workflow

3. **[BlockMapper Implementation](./BLOCK-MAPPER-IMPLEMENTATION.md)** — Code scaffold
   - Complete Python class structure
   - Data classes (BlockType, RichText, Block)
   - Parse markdown → Block objects
   - Convert Block → Notion API format
   - Convert Notion → Markdown
   - Test cases

### 3. **Architecture Decisions Updated** ✅

- ADR-0002: TypeScript Runtime Required for Mobile/iPad (documented)
- Roadmap: v1.0.3.0 now explicitly about TypeScript runtime (not evaluation)
- Dev log: Comprehensive 2026-01-15 entry with all decisions + implementation plan

### 4. **Goblin Server Ready** ✅

Updated `/dev/goblin/README.md` with:

- Quick start section for Move 1
- Links to all documentation
- Setup instructions
- Launch commands

---

## Implementation Timeline

### Phase A: Block Mapping (Week 1)

**File:** `dev/goblin/services/block_mapper.py`

**Deliverables:**

- `BlockMapper` class (parse markdown → Notion blocks → markdown)
- `RichText`, `Block`, `BlockType` data classes
- Tests for all block types

**Estimated:** 8-10 hours

**Code provided in:** [BlockMapper Implementation](./BLOCK-MAPPER-IMPLEMENTATION.md)

### Phase B: Webhook Handler (Week 1-2)

**File:** `dev/goblin/services/notion_sync_service.py`

**Deliverables:**

- Notion webhook endpoint (`POST /api/v0/notion/webhook`)
- Signature verification
- SQLite sync_queue schema
- Queue storage + retrieval

**Estimated:** 6-8 hours

### Phase C: Bidirectional Sync (Week 2-3)

**File:** `dev/goblin/services/sync_executor.py`

**Deliverables:**

- `sync_to_notion()` — Upload markdown → Notion
- `sync_from_notion()` — Download Notion → markdown
- `resolve_conflict()` — Merge strategy (last-write-wins, local-priority, notion-priority, manual)

**Estimated:** 8-10 hours

### Phase D: Testing (Week 3)

**Deliverables:**

- Test all block types (standard + runtime)
- Verify bidirectional sync
- Test conflict resolution
- Real Notion workspace testing

**Estimated:** 4-6 hours

**Total:** ~26-34 hours

---

## Architecture Alignment

### Desktop (macOS) Strategy

```
uDOS App (Tauri) → Wizard/Goblin Server (Python) → Notion API
```

- Python services handle all execution (no JavaScript runtime needed)
- Tauri calls Python via HTTP (localhost:8767 for dev, 8765 for prod)
- Full Notion sync + AI routing + task scheduling

### Mobile/iPad Strategy (v1.0.3.0+)

```
Native App (iOS/iPadOS) → TypeScript Runtime → Offline Execution
                         ↓
                    MeshCore Sync (when online)
                         ↓
                    Desktop Wizard/Goblin
```

- Native TypeScript runtime (no Python available)
- Offline presentation + execution of runtime blocks
- Sync state with desktop when MeshCore available

**Same blocks work everywhere** because we designed them to map to both:

- Python execution (desktop)
- TypeScript execution (mobile)
- Notion blocks (sync)

---

## Key Files

| File                                                                                                                       | Purpose                |
| -------------------------------------------------------------------------------------------------------------------------- | ---------------------- |
| [docs/specs/notion-compatible-blocks.md](../../docs/specs/notion-compatible-blocks.md)                                     | Design specification   |
| [docs/decisions/ADR-0002-typescript-runtime-for-mobile.md](../../docs/decisions/ADR-0002-typescript-runtime-for-mobile.md) | Architecture decision  |
| [docs/roadmap.md](../../docs/roadmap.md)                                                                                   | Updated Move 1-3 plans |
| [docs/devlog/2026-01.md](../../docs/devlog/2026-01.md)                                                                     | Development log entry  |
| [dev/goblin/MOVE-1-QUICK-START.md](./MOVE-1-QUICK-START.md)                                                                | Setup + phases         |
| [dev/goblin/BLOCK-MAPPER-IMPLEMENTATION.md](./BLOCK-MAPPER-IMPLEMENTATION.md)                                              | Code scaffold          |
| [dev/goblin/README.md](./README.md)                                                                                        | Quick start links      |

---

## Next Steps

### Immediate (When Ready)

1. Create Notion Internal Integration

   - Visit https://www.notion.so/my-integrations
   - Create integration named "uDOS Dev"
   - Get API key + webhook secret

2. Configure Goblin

   - Update `dev/goblin/config/goblin.json`
   - Set notion.api_key, notion.webhook_secret, notion.test_page_id

3. Implement Phase A
   - Create `dev/goblin/services/block_mapper.py`
   - Use [BlockMapper Implementation](./BLOCK-MAPPER-IMPLEMENTATION.md) as guide
   - Run tests: `pytest dev/goblin/tests/test_block_mapper.py`

### Later (Phases B-D)

- Phase B: Webhook + queue (Week 1-2)
- Phase C: Bidirectional sync (Week 2-3)
- Phase D: Testing (Week 3)

---

## Benefits

✅ **Notion-Native from Day 1** — No special sync layer, blocks map directly to Notion API  
✅ **Desktop + Mobile Support** — Same markdown blocks work on Python (desktop) + TypeScript (mobile)  
✅ **Future-Proof** — As Notion adds block types, we just add mapping  
✅ **Clean Architecture** — Standard blocks (markdown) separate from runtime blocks (executable)  
✅ **Bidirectional Sync** — Notion ↔ local .md files, conflict resolution built-in

---

## Questions?

See [Move 1 Quick Start](./MOVE-1-QUICK-START.md#setup-steps) for Notion setup  
See [BlockMapper Implementation](./BLOCK-MAPPER-IMPLEMENTATION.md) for code details  
See [Notion-Compatible Block Spec](../../docs/specs/notion-compatible-blocks.md) for design rationale

---

_Ready to build. What's next?_
