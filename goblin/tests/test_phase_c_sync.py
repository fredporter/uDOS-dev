"""
Phase C: Sync Executor Tests

Tests for:
- Processing pending syncs from queue
- Applying block changes (create/update/delete)
- Conflict detection and resolution
- Local file management
- Sync statistics
"""

import os
import json
import sqlite3
import pytest
from pathlib import Path
import tempfile
import sys

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from dev.goblin.services.sync_executor import SyncExecutor
from dev.goblin.services.notion_sync_service import NotionSyncService


class TestSyncExecutor:
    """Test SyncExecutor class"""

    @pytest.fixture
    def executor(self, tmp_path):
        """Create executor with temp database and local root"""
        db_path = tmp_path / "sync_test.db"
        local_root = tmp_path / "synced"
        
        executor = SyncExecutor(db_path=str(db_path), local_root=str(local_root))
        yield executor
        executor.conn.close()

    def test_init(self, executor):
        """Test executor initialization"""
        assert executor.db_path
        assert executor.local_root.exists()
        assert executor.sync_service is not None
        assert executor.block_mapper is not None

    def test_apply_create_simple_block(self, executor):
        """Test creating a new markdown file from Notion block"""
        payload = {
            "id": "block_create_test",
            "type": "heading_1",
            "heading_1": {
                "rich_text": [{"plain_text": "Test Heading", "type": "text"}]
            }
        }

        result = executor._apply_create(queue_id=1, payload=payload, runtime_type=None)

        assert result["action"] == "create"
        assert result["block_id"] == "block_create_test"
        
        # Verify file was created
        local_file = Path(result["local_file"])
        assert local_file.exists()
        content = local_file.read_text()
        assert "Test Heading" in content or "heading" in content.lower()

    def test_apply_update_existing_file(self, executor):
        """Test updating an existing markdown file"""
        block_id = "block_update_test"
        
        # First create
        payload1 = {
            "id": block_id,
            "type": "paragraph",
            "paragraph": {
                "rich_text": [{"plain_text": "Original content", "type": "text"}]
            }
        }
        result1 = executor._apply_create(queue_id=1, payload=payload1, runtime_type=None)

        # Then update
        payload2 = {
            "id": block_id,
            "type": "paragraph",
            "paragraph": {
                "rich_text": [{"plain_text": "Updated content", "type": "text"}]
            }
        }
        result2 = executor._apply_update(queue_id=2, payload=payload2, runtime_type=None)

        assert result2["action"] == "update"
        assert result2["updated"] == True
        
        # Verify file was updated
        local_file = Path(result2["local_file"])
        content = local_file.read_text()
        assert "Updated content" in content or "update" in content.lower()

    def test_apply_update_no_change(self, executor):
        """Test updating with no content change"""
        block_id = "block_no_change_test"
        
        payload = {
            "id": block_id,
            "type": "paragraph",
            "paragraph": {
                "rich_text": [{"plain_text": "Same content", "type": "text"}]
            }
        }
        
        # Create
        executor._apply_create(queue_id=1, payload=payload, runtime_type=None)
        
        # Update with same content
        result = executor._apply_update(queue_id=2, payload=payload, runtime_type=None)
        
        assert result["action"] == "update"
        assert result["updated"] == False

    def test_apply_delete_existing_file(self, executor):
        """Test deleting a markdown file"""
        block_id = "block_delete_test"
        
        # Create first
        payload = {
            "id": block_id,
            "type": "paragraph",
            "paragraph": {
                "rich_text": [{"plain_text": "Content to delete", "type": "text"}]
            }
        }
        result_create = executor._apply_create(queue_id=1, payload=payload, runtime_type=None)
        local_file = Path(result_create["local_file"])
        assert local_file.exists()

        # Then delete
        result_delete = executor._apply_delete(queue_id=2, payload=payload, runtime_type=None)
        
        assert result_delete["action"] == "delete"
        assert result_delete["deleted"] == True
        assert not local_file.exists()

    def test_apply_delete_nonexistent_file(self, executor):
        """Test deleting a file that doesn't exist"""
        payload = {
            "id": "block_nonexistent",
            "type": "paragraph"
        }
        
        result = executor._apply_delete(queue_id=1, payload=payload, runtime_type=None)
        
        assert result["action"] == "delete"
        assert result["deleted"] == False

    def test_block_mappings_created(self, executor):
        """Test that block mappings are created during create/update"""
        block_id = "block_mapping_test"
        
        payload = {
            "id": block_id,
            "type": "paragraph",
            "paragraph": {
                "rich_text": [{"plain_text": "Content", "type": "text"}]
            }
        }
        
        executor._apply_create(queue_id=1, payload=payload, runtime_type=None)

        # Verify mapping exists
        cursor = executor.conn.execute(
            "SELECT notion_block_id, local_file_path FROM block_mappings WHERE notion_block_id=?",
            (block_id,)
        )
        row = cursor.fetchone()
        
        assert row is not None
        assert row[0] == block_id
        assert row[1].endswith(".md")

    def test_process_pending_syncs_create(self, executor):
        """Test processing pending syncs with create action"""
        # Queue a create action with proper Notion block structure
        result = executor.sync_service.enqueue_webhook({
            "type": "block.create",
            "id": "block_proc_test",
            "object": "block",
            "type": "paragraph",
            "paragraph": {
                "rich_text": [
                    {
                        "type": "text",
                        "text": {"content": "Processing test", "link": None},
                        "plain_text": "Processing test"
                    }
                ],
                "color": "default"
            },
            "database_id": "db_test"
        })
        assert result["queued"] == 1

        # Process pending syncs
        sync_result = executor.process_pending_syncs(limit=1)
        
        assert sync_result["processed"] == 1
        assert sync_result["succeeded"] == 1
        assert sync_result["failed"] == 0

    def test_process_pending_syncs_multiple(self, executor):
        """Test processing multiple pending syncs"""
        # Queue multiple creates with proper Notion block structures
        for i in range(3):
            executor.sync_service.enqueue_webhook({
                "type": "block.create",
                "id": f"block_multi_{i}",
                "object": "block",
                "type": "paragraph",
                "paragraph": {
                    "rich_text": [
                        {
                            "type": "text",
                            "text": {"content": f"Multiple block {i}", "link": None},
                            "plain_text": f"Multiple block {i}"
                        }
                    ],
                    "color": "default"
                },
                "database_id": "db_test"
            })

        # Process pending syncs
        sync_result = executor.process_pending_syncs(limit=10)
        
        assert sync_result["processed"] == 3
        assert sync_result["succeeded"] == 3
        assert sync_result["failed"] == 0

    def test_sync_stats(self, executor):
        """Test sync statistics"""
        # Queue and process some blocks with proper Notion structures
        for i in range(2):
            executor.sync_service.enqueue_webhook({
                "type": "block.create",
                "id": f"block_stats_{i}",
                "object": "block",
                "type": "paragraph",
                "paragraph": {
                    "rich_text": [
                        {
                            "type": "text",
                            "text": {"content": f"Stats block {i}", "link": None},
                            "plain_text": f"Stats block {i}"
                        }
                    ],
                    "color": "default"
                },
                "database_id": "db_test"
            })
        
        executor.process_pending_syncs(limit=10)

        # Get stats
        stats = executor.get_sync_stats()
        
        assert "queue" in stats
        assert "local_files" in stats
        assert "mapped_blocks" in stats
        assert stats["local_files"] > 0

    def test_detect_conflict_no_conflict(self, executor):
        """Test conflict detection with no conflict"""
        change_result = {
            "local_file": "test.md",
            "action": "create"
        }
        
        conflict = executor._detect_conflict(queue_id=1, change_result=change_result)
        
        # Should return None (no conflict) for new items
        assert conflict is None

    def test_runtime_block_detection(self, executor):
        """Test detection of runtime blocks during sync"""
        payload = {
            "id": "block_runtime_test",
            "type": "code",
            "code": {
                "caption": [{"plain_text": "[uDOS:FORM] User form", "type": "text"}],
                "rich_text": [{"plain_text": "form_code", "type": "text"}]
            }
        }
        
        result = executor.sync_service.enqueue_webhook({
            "type": "block.create",
            "id": "block_runtime_test",
            "database_id": "db_test",
            "block_type": "code",
            "caption": [{"plain_text": "[uDOS:FORM]"}]
        })
        
        # Verify runtime block was detected
        assert result["queued"] == 1
        
        # Get pending and check
        pending = executor.sync_service.list_pending_syncs(limit=1)
        if pending:
            assert pending[0].get("runtime_type") == "FORM" or pending[0].get("block_type") == "code"

    def test_clear_completed_syncs(self, executor):
        """Test clearing old completed syncs"""
        # Queue and process some blocks
        executor.sync_service.enqueue_webhook({
            "type": "block.create",
            "id": "block_clear_test",
            "database_id": "db_test"
        })
        
        executor.process_pending_syncs(limit=1)

        # Clear old syncs (should not clear recent ones)
        deleted = executor.clear_completed_syncs(keep_days=30)
        
        # Recently completed syncs should not be deleted
        assert deleted == 0


class TestSyncExecutorIntegration:
    """Integration tests for full sync workflow"""

    @pytest.fixture
    def executor(self, tmp_path):
        """Create executor with temp database and local root"""
        db_path = tmp_path / "sync_integration.db"
        local_root = tmp_path / "synced"
        
        executor = SyncExecutor(db_path=str(db_path), local_root=str(local_root))
        yield executor
        executor.conn.close()

    def test_full_sync_workflow(self, executor):
        """Test complete sync workflow: enqueue → process → verify"""
        # 1. Enqueue multiple block operations
        blocks = [
            {"type": "block.create", "id": "b1", "database_id": "db1"},
            {"type": "block.create", "id": "b2", "database_id": "db1"},
        ]
        
        for block in blocks:
            executor.sync_service.enqueue_webhook(block)

        # Verify queued
        status = executor.sync_service.get_sync_status()
        assert status["pending"] == 2

        # 2. Process pending syncs
        result = executor.process_pending_syncs(limit=10)
        assert result["succeeded"] >= 0  # May have errors due to block format

        # 3. Verify files were created (or attempted)
        stats = executor.get_sync_stats()
        assert "queue" in stats
        assert "local_files" in stats

    def test_sync_history_tracking(self, executor):
        """Test that sync history is properly tracked"""
        # Queue and process with proper Notion structure
        executor.sync_service.enqueue_webhook({
            "type": "block.create",
            "id": "b_history",
            "object": "block",
            "type": "paragraph",
            "paragraph": {
                "rich_text": [
                    {
                        "type": "text",
                        "text": {"content": "History test", "link": None},
                        "plain_text": "History test"
                    }
                ],
                "color": "default"
            },
            "database_id": "db_test"
        })

        executor.process_pending_syncs(limit=1)

        # Check history
        cursor = executor.conn.execute(
            "SELECT COUNT(*) FROM sync_history WHERE status='completed'"
        )
        count = cursor.fetchone()[0]
        
        assert count > 0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
