#!/usr/bin/env python3
"""Debug sync executor"""
import tempfile
from pathlib import Path
from dev.goblin.services.sync_executor import SyncExecutor

tmpdir = Path(tempfile.gettempdir()) / 'udos_test'
tmpdir.mkdir(exist_ok=True)

executor = SyncExecutor(db_path=str(tmpdir / 'sync.db'), local_root=tmpdir / 'synced')

# Queue block
print("[1] Queueing block...")
result = executor.sync_service.enqueue_webhook({
    'type': 'block.create',
    'id': 'test_block_1',
    'object': 'block',
    'type': 'paragraph',
    'paragraph': {
        'rich_text': [{'type': 'text', 'text': {'content': 'Debug test', 'link': None}, 'plain_text': 'Debug test'}],
        'color': 'default'
    },
    'database_id': 'db_test'
})
print(f"Queued result: {result}")

# Check pending
cursor = executor.conn.execute("SELECT COUNT(*) FROM sync_queue WHERE status='pending'")
pending = cursor.fetchone()[0]
print(f"[2] Pending syncs in queue: {pending}")

# Process
print("[3] Processing...")
sync_result = executor.process_pending_syncs(limit=5)
print(f"Process result: {sync_result}")

# Check files
synced_dir = tmpdir / 'synced'
print(f"\n[4] Synced dir exists: {synced_dir.exists()}")
if synced_dir.exists():
    files = list(synced_dir.glob('*.md'))
    print(f"Files created: {len(files)}")
    for f in files:
        print(f"  - {f.name}: {len(f.read_text())} bytes")

# Check mappings
cursor = executor.conn.execute("SELECT COUNT(*) FROM block_mappings")
mappings = cursor.fetchone()[0]
print(f"\n[5] Block mappings in DB: {mappings}")

# Check history
cursor = executor.conn.execute("SELECT COUNT(*) FROM sync_history WHERE status='completed'")
completed = cursor.fetchone()[0]
print(f"[6] Completed syncs in history: {completed}")
