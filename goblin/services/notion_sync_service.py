"""
Notion Webhook Service

Manages:
- Webhook signature verification (HMAC-SHA256)
- Block change queueing
- SQLite storage
- Sync status tracking
"""

import os
import json
import hmac
import hashlib
import sqlite3
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Tuple

from dev.goblin.services.block_mapper import BlockMapper


class NotionSyncService:
    """Manage Notion webhook processing and queue"""
    
    def __init__(self, db_path: str = None):
        """Initialize sync service"""
        self.webhook_secret = os.getenv("NOTION_WEBHOOK_SECRET", "")
        
        # Database setup
        if db_path is None:
            # Use standard synced directory from Phase C
            db_path = "memory/synced/notion_sync.db"
        
        self.db_path = db_path
        Path(self.db_path).parent.mkdir(parents=True, exist_ok=True)
        
        self._init_connection()
        self._init_tables()
        self.block_mapper = BlockMapper()

    def _init_connection(self):
        """Initialize database connection"""
        self.conn = sqlite3.connect(self.db_path, check_same_thread=False)
        self.conn.row_factory = sqlite3.Row
        self.conn.execute("PRAGMA journal_mode=WAL")  # Better concurrency

    def _init_tables(self):
        """Create tables if they don't exist"""
        schema_path = Path(__file__).parent.parent / "schemas" / "sync_schema.sql"
        
        if schema_path.exists():
            with open(schema_path) as f:
                schema = f.read()
            self.conn.executescript(schema)
            self.conn.commit()

    def verify_webhook_signature(self, body: bytes, signature_header: str) -> bool:
        """
        Verify Notion webhook HMAC-SHA256

        Notion sends X-Notion-Signature header with format: Signature=<hmac>
        Algorithm: HMAC-SHA256(secret, body)

        Args:
            body: Raw request body bytes
            signature_header: X-Notion-Signature header value

        Returns:
            True if signature valid, False otherwise
        """
        if not self.webhook_secret:
            # No secret configured - accept all (dev/test mode)
            return True
        
        if not signature_header:
            # No signature provided - allow in dev mode
            return True

        # Extract hmac from header
        if not signature_header.startswith("Signature="):
            return False

        provided_sig = signature_header[len("Signature="):]

        # Calculate expected signature
        # Notion uses: HMAC-SHA256(secret, body)
        expected_sig = hmac.new(
            self.webhook_secret.encode(),
            body,
            hashlib.sha256
        ).hexdigest()

        # Compare signatures (timing-safe)
        return hmac.compare_digest(provided_sig, expected_sig)

    def enqueue_webhook(self, payload: dict) -> Dict:
        """
        Parse webhook and queue block changes

        Notion webhook payload contains:
        {
            "type": "block.update" | "block.create" | "block.delete",
            "object": "block",
            "request_id": "...",
            "timestamp": "...",
            "changes": [
                {
                    "type": "...",
                    "id": "...",
                    "properties": {...}
                }
            ]
        }

        Returns:
            {"queued": N, "failed": 0, "queue_id": [...]}
        """
        queued = 0
        failed = 0
        queue_ids = []

        # Determine action from payload type
        action_map = {
            "block.create": "create",
            "block.update": "update",
            "block.delete": "delete"
        }
        
        action = action_map.get(payload.get("type"), "update")

        # Process changes
        changes = payload.get("changes", [])
        if not changes:
            # Single block
            changes = [payload]

        for change in changes:
            try:
                block_id = change.get("id") or payload.get("id")
                if not block_id:
                    failed += 1
                    continue

                # Determine block type
                block_type = change.get("type", "paragraph")

                # Check if runtime block (by caption or metadata)
                runtime_type = self._detect_runtime_block(change)

                # Queue to database
                cursor = self.conn.execute(
                    """
                    INSERT INTO sync_queue 
                    (notion_block_id, database_id, block_type, runtime_type, action, payload, status)
                    VALUES (?, ?, ?, ?, ?, ?, 'pending')
                    """,
                    (
                        block_id,
                        payload.get("database_id", ""),
                        block_type,
                        runtime_type,
                        action,
                        json.dumps(change)
                    )
                )
                self.conn.commit()

                queue_ids.append(cursor.lastrowid)
                queued += 1

            except Exception as e:
                failed += 1
                print(f"[ERROR] Failed to queue block {block_id}: {e}")

        return {
            "queued": queued,
            "failed": failed,
            "queue_ids": queue_ids
        }

    def _detect_runtime_block(self, block: dict) -> Optional[str]:
        """
        Detect if block is a runtime block (STATE, FORM, IF, NAV, PANEL, MAP, SET)

        Runtime blocks are marked in captions: [uDOS:STATE], [uDOS:FORM], etc.

        Args:
            block: Notion block object

        Returns:
            Runtime type string or None
        """
        # Check caption for runtime marker
        caption = block.get("caption", [])
        if caption and isinstance(caption, list):
            caption_text = " ".join([
                text.get("plain_text", "") 
                for text in caption
            ])
            
            runtime_types = ["STATE", "FORM", "IF", "NAV", "PANEL", "MAP", "SET"]
            for rt in runtime_types:
                if f"[uDOS:{rt}]" in caption_text:
                    return rt

        # Alternative: Check metadata in annotations
        annotations = block.get("annotations", {})
        if "runtime_type" in annotations:
            return annotations["runtime_type"]

        return None

    def get_sync_status(self) -> Dict:
        """Return queue statistics"""
        cursor = self.conn.execute("""
            SELECT 
                COUNT(*) as total,
                SUM(CASE WHEN status='pending' THEN 1 ELSE 0 END) as pending,
                SUM(CASE WHEN status='processing' THEN 1 ELSE 0 END) as processing,
                SUM(CASE WHEN status='completed' THEN 1 ELSE 0 END) as completed,
                SUM(CASE WHEN status='failed' THEN 1 ELSE 0 END) as failed
            FROM sync_queue
        """)
        
        row = cursor.fetchone()
        return {
            "total": row[0] or 0,
            "pending": row[1] or 0,
            "processing": row[2] or 0,
            "completed": row[3] or 0,
            "failed": row[4] or 0
        }

    def list_pending_syncs(self, limit: int = 10) -> List[Dict]:
        """Get pending sync queue entries"""
        cursor = self.conn.execute("""
            SELECT id, notion_block_id, database_id, block_type, runtime_type, action, payload, created_at
            FROM sync_queue
            WHERE status='pending'
            ORDER BY created_at ASC
            LIMIT ?
        """, (limit,))
        
        return [dict(row) for row in cursor.fetchall()]

    def mark_processing(self, queue_id: int):
        """Mark queue entry as processing"""
        self.conn.execute(
            "UPDATE sync_queue SET status='processing' WHERE id=?",
            (queue_id,)
        )
        self.conn.commit()

    def mark_completed(self, queue_id: int, local_file_path: str = None):
        """Mark queue entry as completed"""
        cursor = self.conn.execute("""
            UPDATE sync_queue 
            SET status='completed', processed_at=CURRENT_TIMESTAMP
            WHERE id=?
        """, (queue_id,))
        
        # Insert into history
        if local_file_path:
            self.conn.execute("""
                INSERT INTO sync_history (notion_block_id, local_file_path, action, status)
                SELECT notion_block_id, ?, action, 'completed'
                FROM sync_queue WHERE id=?
            """, (local_file_path, queue_id))
        
        self.conn.commit()

    def mark_failed(self, queue_id: int, error_message: str):
        """Mark queue entry as failed"""
        self.conn.execute(
            """
            UPDATE sync_queue 
            SET status='failed', processed_at=CURRENT_TIMESTAMP, error_message=?
            WHERE id=?
            """,
            (error_message, queue_id)
        )
        self.conn.commit()

    def close(self):
        """Close database connection"""
        if hasattr(self, 'conn'):
            self.conn.close()

    def __del__(self):
        """Cleanup on deletion"""
        self.close()
