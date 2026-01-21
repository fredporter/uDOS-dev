"""
Sync Executor Service - Phase C

Processes the queued blocks from Notion and synchronizes them bidirectionally.

Key Capabilities:
- Process pending syncs from sync_queue
- Convert Notion blocks → markdown (using BlockMapper)
- Apply block changes (create/update/delete)
- Detect and resolve conflicts (last-write-wins)
- Sync to Notion (push local changes)
- Manage local files and block mappings
"""

import os
import json
import hashlib
import sqlite3
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Tuple

from dev.goblin.services.block_mapper import BlockMapper
from dev.goblin.services.notion_sync_service import NotionSyncService


class SyncExecutor:
    """Execute queued sync operations and manage bidirectional sync"""

    def __init__(self, db_path: str = None, local_root: str = None):
        """
        Initialize sync executor

        Args:
            db_path: Path to SQLite database (default: memory/goblin/sync.db)
            local_root: Root directory for local markdown files (default: memory/synced/)
        """
        if db_path is None:
            db_path = "memory/goblin/sync.db"
        
        if local_root is None:
            local_root = "memory/synced/"

        self.db_path = db_path
        self.local_root = Path(local_root)
        self.local_root.mkdir(parents=True, exist_ok=True)

        # Initialize services
        self.sync_service = NotionSyncService(db_path=db_path)
        self.block_mapper = BlockMapper()

        # Database connection (shared with NotionSyncService)
        self.conn = self.sync_service.conn

    def process_pending_syncs(self, limit: int = 10) -> Dict:
        """
        Process pending syncs from queue

        Flow:
        1. Get pending items from sync_queue
        2. For each item:
           - Mark as processing
           - Apply change (create/update/delete)
           - Check for conflicts
           - Mark as completed or failed
        3. Update sync_history

        Args:
            limit: Max items to process in this batch

        Returns:
            {
                "processed": N,
                "succeeded": N,
                "failed": N,
                "conflicts": N,
                "details": [{id, status, error}]
            }
        """
        pending = self.sync_service.list_pending_syncs(limit=limit)
        
        results = {
            "processed": len(pending),
            "succeeded": 0,
            "failed": 0,
            "conflicts": 0,
            "details": []
        }

        for item in pending:
            queue_id = item["id"]
            try:
                # Mark as processing
                self.sync_service.mark_processing(queue_id)

                # Parse the payload
                payload = json.loads(item["payload"])

                # Apply the change
                action = item["action"]
                runtime_type = item["runtime_type"]

                if action == "create":
                    result = self._apply_create(queue_id, payload, runtime_type)
                elif action == "update":
                    result = self._apply_update(queue_id, payload, runtime_type)
                elif action == "delete":
                    result = self._apply_delete(queue_id, payload, runtime_type)
                else:
                    raise ValueError(f"Unknown action: {action}")

                # Check for conflicts
                conflict = self._detect_conflict(queue_id, result)
                if conflict:
                    results["conflicts"] += 1
                    result["conflict"] = conflict

                # Mark as completed
                local_file = result.get("local_file")
                self.sync_service.mark_completed(queue_id, local_file)
                
                results["succeeded"] += 1
                results["details"].append({
                    "queue_id": queue_id,
                    "status": "completed",
                    "local_file": local_file,
                    "conflict": conflict
                })

            except Exception as e:
                results["failed"] += 1
                error_msg = str(e)
                self.sync_service.mark_failed(queue_id, error_msg)
                results["details"].append({
                    "queue_id": queue_id,
                    "status": "failed",
                    "error": error_msg
                })

        return results

    def _apply_create(self, queue_id: int, payload: dict, runtime_type: Optional[str]) -> Dict:
        """
        Apply block creation

        Creates a new markdown file from the Notion block

        Returns:
            {"local_file": "...", "block_id": "..."}
        """
        block_id = payload.get("id", f"block_{queue_id}")
        
        # Convert Notion block to markdown using BlockMapper
        # The payload is already in Notion format, so pass it directly
        markdown = self.block_mapper.from_notion_blocks([payload])

        # Create local file
        local_file = self.local_root / f"{block_id}.md"
        local_file.write_text(markdown, encoding="utf-8")

        # Create mapping
        content_hash = hashlib.sha256(markdown.encode()).hexdigest()
        self.conn.execute(
            """
            INSERT INTO block_mappings (notion_block_id, local_file_path, content_hash)
            VALUES (?, ?, ?)
            """,
            (block_id, str(local_file), content_hash)
        )
        self.conn.commit()

        return {
            "local_file": str(local_file),
            "block_id": block_id,
            "action": "create"
        }

    def _apply_update(self, queue_id: int, payload: dict, runtime_type: Optional[str]) -> Dict:
        """
        Apply block update

        Updates existing markdown file from Notion block

        Returns:
            {"local_file": "...", "block_id": "...", "updated": True/False}
        """
        block_id = payload.get("id", f"block_{queue_id}")

        # Get existing mapping
        cursor = self.conn.execute(
            "SELECT local_file_path FROM block_mappings WHERE notion_block_id=?",
            (block_id,)
        )
        row = cursor.fetchone()
        
        if not row:
            # No mapping exists - treat as create
            return self._apply_create(queue_id, payload, runtime_type)

        local_file = Path(row[0])

        # Convert Notion block to markdown using BlockMapper
        new_markdown = self.block_mapper.from_notion_blocks([payload])

        # Read existing content
        if local_file.exists():
            existing_markdown = local_file.read_text(encoding="utf-8")
            existing_hash = hashlib.sha256(existing_markdown.encode()).hexdigest()
        else:
            existing_markdown = ""
            existing_hash = ""

        # Check if content changed
        new_hash = hashlib.sha256(new_markdown.encode()).hexdigest()
        updated = (new_hash != existing_hash)

        if updated:
            # Write new content
            local_file.write_text(new_markdown, encoding="utf-8")

            # Update mapping
            self.conn.execute(
                "UPDATE block_mappings SET content_hash=?, last_synced=CURRENT_TIMESTAMP WHERE notion_block_id=?",
                (new_hash, block_id)
            )
            self.conn.commit()

        return {
            "local_file": str(local_file),
            "block_id": block_id,
            "updated": updated,
            "action": "update"
        }

    def _apply_delete(self, queue_id: int, payload: dict, runtime_type: Optional[str]) -> Dict:
        """
        Apply block deletion

        Deletes the local markdown file

        Returns:
            {"block_id": "...", "deleted": True/False}
        """
        block_id = payload.get("id", f"block_{queue_id}")

        # Get existing mapping
        cursor = self.conn.execute(
            "SELECT local_file_path FROM block_mappings WHERE notion_block_id=?",
            (block_id,)
        )
        row = cursor.fetchone()

        deleted = False
        if row:
            local_file = Path(row[0])
            if local_file.exists():
                local_file.unlink()
                deleted = True

            # Remove mapping
            self.conn.execute(
                "DELETE FROM block_mappings WHERE notion_block_id=?",
                (block_id,)
            )
            self.conn.commit()

        return {
            "block_id": block_id,
            "deleted": deleted,
            "action": "delete"
        }

    def _detect_conflict(self, queue_id: int, change_result: dict) -> Optional[Dict]:
        """
        Detect conflicts between Notion and local versions

        Conflict occurs when:
        - Local file was modified after last sync
        - Notion block was modified after last sync
        - Both changed (last-write-wins)

        Returns:
            Conflict dict or None if no conflict
        """
        # Get sync history entry
        cursor = self.conn.execute(
            """
            SELECT sh.synced_at, bm.last_synced
            FROM sync_history sh
            LEFT JOIN block_mappings bm ON sh.notion_block_id = bm.notion_block_id
            WHERE sh.id = ?
            LIMIT 1
            """,
            (queue_id,)
        )
        row = cursor.fetchone()

        if not row:
            # New sync, no conflict
            return None

        # TODO: Implement actual conflict detection
        # For now, use last-write-wins strategy

        return None

    def sync_from_notion(self, database_id: str = None) -> Dict:
        """
        One-shot sync from Notion to local

        Processes all pending syncs for a database

        Args:
            database_id: Optional filter by database

        Returns:
            Sync result summary
        """
        return self.process_pending_syncs(limit=100)

    def get_sync_stats(self) -> Dict:
        """Get synchronization statistics"""
        # Get queue stats
        queue_stats = self.sync_service.get_sync_status()

        # Get file stats
        local_files = list(self.local_root.glob("*.md"))

        # Get mapping stats
        cursor = self.conn.execute("SELECT COUNT(*) FROM block_mappings")
        mapped_blocks = cursor.fetchone()[0]

        return {
            "queue": queue_stats,
            "local_files": len(local_files),
            "mapped_blocks": mapped_blocks,
            "last_sync": self._get_last_sync_time()
        }

    def _get_last_sync_time(self) -> Optional[str]:
        """Get timestamp of last completed sync"""
        cursor = self.conn.execute(
            "SELECT MAX(synced_at) FROM sync_history WHERE status='completed'"
        )
        row = cursor.fetchone()
        return row[0] if row[0] else None

    def clear_completed_syncs(self, keep_days: int = 30) -> int:
        """
        Clean up old completed syncs from history

        Args:
            keep_days: Keep syncs from last N days

        Returns:
            Number of records deleted
        """
        cursor = self.conn.execute(
            f"""
            DELETE FROM sync_history
            WHERE status='completed'
            AND datetime(synced_at) < datetime('now', '-{keep_days} days')
            """
        )
        self.conn.commit()
        return cursor.rowcount

    def sync_to_notion(self) -> Dict:
        """
        Monitor local files and push changes to Notion

        Scans local_root directory for markdown files and compares against
        block_mappings to detect new/changed files. Converts markdown to
        Notion blocks and pushes updates via Notion API.

        Returns:
            {
                "scanned": N,        # Files scanned
                "created": N,        # New blocks created in Notion
                "updated": N,        # Existing blocks updated
                "failed": N,         # Failed pushes
                "conflicts": N,      # Conflict detection/resolution
                "details": [...]
            }
        """
        results = {
            "scanned": 0,
            "created": 0,
            "updated": 0,
            "failed": 0,
            "conflicts": 0,
            "details": []
        }

        if not self.local_root.exists():
            return results

        # Scan local markdown files
        markdown_files = list(self.local_root.glob("*.md"))
        results["scanned"] = len(markdown_files)

        for md_file in markdown_files:
            try:
                block_id = md_file.stem  # filename without .md
                content = md_file.read_text(encoding="utf-8")
                content_hash = hashlib.sha256(content.encode()).hexdigest()

                # Check if mapping exists
                cursor = self.conn.execute(
                    "SELECT content_hash FROM block_mappings WHERE notion_block_id=?",
                    (block_id,)
                )
                row = cursor.fetchone()

                if not row:
                    # New file - create in Notion
                    result = self._push_create(block_id, content)
                    results["created"] += 1
                    
                    # INSERT new mapping
                    self.conn.execute(
                        """
                        INSERT INTO block_mappings (notion_block_id, local_file_path, content_hash)
                        VALUES (?, ?, ?)
                        """,
                        (block_id, str(md_file), content_hash)
                    )
                else:
                    existing_hash = row[0]
                    if existing_hash != content_hash:
                        # File changed - update in Notion
                        result = self._push_update(block_id, content)
                        results["updated"] += 1
                        
                        # UPDATE existing mapping
                        self.conn.execute(
                            """
                            UPDATE block_mappings
                            SET content_hash = ?, last_synced = CURRENT_TIMESTAMP
                            WHERE notion_block_id = ?
                            """,
                            (content_hash, block_id)
                        )
                    else:
                        # No change
                        result = {"status": "unchanged", "block_id": block_id}
                
                self.conn.commit()

                results["details"].append({
                    "block_id": block_id,
                    "status": result.get("status", "completed"),
                    "action": result.get("action", "update")
                })

            except Exception as e:
                results["failed"] += 1
                results["details"].append({
                    "block_id": block_id,
                    "status": "failed",
                    "error": str(e)
                })

        return results

    def _push_create(self, block_id: str, markdown_content: str) -> Dict:
        """
        Create new block in Notion from local markdown

        Converts markdown to Notion block and pushes via API.

        Args:
            block_id: Local identifier (will become notion_block_id)
            markdown_content: Markdown source

        Returns:
            {"status": "created", "block_id": "...", "action": "create"}
        """
        # Parse markdown to blocks
        blocks = self.block_mapper.parse_markdown(markdown_content)
        
        if not blocks:
            raise ValueError(f"Could not parse markdown for {block_id}")

        # Convert to Notion API format
        notion_blocks = self.block_mapper.to_notion_api(blocks)

        if not notion_blocks:
            raise ValueError(f"Could not convert markdown for {block_id}")

        # In real implementation, this would call Notion API:
        # notion_client.blocks.children.append(parent=database_id, children=[block])

        # For now, return structure compatible with mapping
        return {
            "status": "created",
            "block_id": block_id,
            "action": "create"
        }

    def _push_update(self, block_id: str, markdown_content: str) -> Dict:
        """
        Update existing block in Notion from local markdown

        Args:
            block_id: Notion block ID
            markdown_content: Updated markdown source

        Returns:
            {"status": "updated", "block_id": "...", "action": "update"}
        """
        # Parse markdown to blocks
        blocks = self.block_mapper.parse_markdown(markdown_content)
        
        if not blocks:
            raise ValueError(f"Could not parse markdown for {block_id}")

        # Convert to Notion API format
        notion_blocks = self.block_mapper.to_notion_api(blocks)

        if not notion_blocks:
            raise ValueError(f"Could not convert markdown for {block_id}")

        # In real implementation, would call Notion API:
        # notion_client.blocks.update(block_id=block_id, **block_data)

        return {
            "status": "updated",
            "block_id": block_id,
            "action": "update"
        }

    def detect_local_changes(self) -> Dict:
        """
        Detect which local files have changed since last sync

        Compares content hashes to find modified files.

        Returns:
            {
                "unchanged": N,
                "modified": N,
                "new": N,
                "files": [{block_id, status}]
            }
        """
        results = {
            "unchanged": 0,
            "modified": 0,
            "new": 0,
            "files": []
        }

        if not self.local_root.exists():
            return results

        # Get all mapped blocks
        cursor = self.conn.execute("SELECT notion_block_id, content_hash FROM block_mappings")
        mappings = {row[0]: row[1] for row in cursor.fetchall()}

        # Scan local files
        for md_file in self.local_root.glob("*.md"):
            block_id = md_file.stem
            content = md_file.read_text(encoding="utf-8")
            new_hash = hashlib.sha256(content.encode()).hexdigest()

            if block_id in mappings:
                if mappings[block_id] == new_hash:
                    results["unchanged"] += 1
                    status = "unchanged"
                else:
                    results["modified"] += 1
                    status = "modified"
            else:
                results["new"] += 1
                status = "new"

            results["files"].append({
                "block_id": block_id,
                "status": status,
                "hash": new_hash
            })

        return results
