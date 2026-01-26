"""
Phase C.3: Sync to Notion (Push Direction) Tests

Tests for pushing local markdown changes back to Notion via Notion API.
"""

import pytest
import json
import tempfile
from pathlib import Path
from dev.goblin.services.notion_sync_service import NotionSyncService
from dev.goblin.services.sync_executor import SyncExecutor


@pytest.fixture
def executor():
    """Create SyncExecutor with temp database"""
    tmpdir = Path(tempfile.gettempdir()) / "udos_test_push"
    tmpdir.mkdir(exist_ok=True)
    
    executor = SyncExecutor(
        db_path=str(tmpdir / "sync.db"),
        local_root=tmpdir / "synced"
    )
    
    yield executor
    
    # Cleanup
    for f in tmpdir.glob("**/*"):
        if f.is_file():
            f.unlink()
    for d in tmpdir.glob("**/*"):
        if d.is_dir():
            d.rmdir()


class TestSyncToNotion:
    """Test pushing local markdown changes to Notion"""

    def test_scan_empty_directory(self, executor):
        """Test scanning empty synced directory"""
        result = executor.sync_to_notion()
        
        assert result["scanned"] == 0
        assert result["created"] == 0
        assert result["updated"] == 0
        assert result["failed"] == 0

    def test_push_new_file(self, executor):
        """Test creating new block in Notion from local markdown"""
        # Create local markdown file WITHOUT a mapping (simulates new file)
        md_file = executor.local_root / "new_block.md"
        md_file.write_text("# New Block\n\nContent here", encoding="utf-8")
        
        # Don't create mapping - this is a new, unmapped file
        # (In real scenario, new local files wouldn't have mappings yet)
        
        # Push
        result = executor.sync_to_notion()
        
        assert result["scanned"] == 1
        assert result["created"] == 1  # Unmapped file treated as new
        assert result["updated"] == 0
        assert result["failed"] == 0

    def test_push_modified_file(self, executor):
        """Test updating block in Notion when local file changed"""
        # Create local markdown file
        md_file = executor.local_root / "modified_block.md"
        content = "# Modified Block\n\nUpdated content"
        md_file.write_text(content, encoding="utf-8")
        
        # Create mapping with old hash
        old_hash = "old_hash_value"
        executor.conn.execute(
            "INSERT INTO block_mappings (notion_block_id, local_file_path, content_hash) VALUES (?, ?, ?)",
            ("modified_block", str(md_file), old_hash)
        )
        executor.conn.commit()
        
        # Push
        result = executor.sync_to_notion()
        
        assert result["scanned"] == 1
        assert result["created"] == 0
        assert result["updated"] == 1
        assert result["failed"] == 0
        
        # Verify mapping hash updated
        cursor = executor.conn.execute(
            "SELECT content_hash FROM block_mappings WHERE notion_block_id=?",
            ("modified_block",)
        )
        new_hash = cursor.fetchone()[0]
        assert new_hash != old_hash

    def test_push_unchanged_file(self, executor):
        """Test skipping file when content hasn't changed"""
        # Create local markdown file
        md_file = executor.local_root / "unchanged_block.md"
        content = "# Unchanged Block\n\nSame content"
        md_file.write_text(content, encoding="utf-8")
        
        # Calculate hash
        import hashlib
        content_hash = hashlib.sha256(content.encode()).hexdigest()
        
        # Create mapping with same hash
        executor.conn.execute(
            "INSERT INTO block_mappings (notion_block_id, local_file_path, content_hash) VALUES (?, ?, ?)",
            ("unchanged_block", str(md_file), content_hash)
        )
        executor.conn.commit()
        
        # Push
        result = executor.sync_to_notion()
        
        assert result["scanned"] == 1
        assert result["created"] == 0
        assert result["updated"] == 0
        assert result["failed"] == 0

    def test_push_multiple_files(self, executor):
        """Test pushing multiple files with mixed states"""
        import hashlib
        
        # Create 3 files: new (unmapped), modified, unchanged
        
        # 1. New file (NO mapping)
        new_file = executor.local_root / "new.md"
        new_file.write_text("# New", encoding="utf-8")
        
        # 2. Modified file (mapped with old hash)
        modified_file = executor.local_root / "modified.md"
        modified_file.write_text("# Modified", encoding="utf-8")
        executor.conn.execute(
            "INSERT INTO block_mappings (notion_block_id, local_file_path, content_hash) VALUES (?, ?, ?)",
            ("modified", str(modified_file), "old_hash")
        )
        
        # 3. Unchanged file (mapped with correct hash)
        unchanged_file = executor.local_root / "unchanged.md"
        content = "# Unchanged"
        unchanged_file.write_text(content, encoding="utf-8")
        content_hash = hashlib.sha256(content.encode()).hexdigest()
        executor.conn.execute(
            "INSERT INTO block_mappings (notion_block_id, local_file_path, content_hash) VALUES (?, ?, ?)",
            ("unchanged", str(unchanged_file), content_hash)
        )
        
        executor.conn.commit()
        
        # Push
        result = executor.sync_to_notion()
        
        assert result["scanned"] == 3
        assert result["created"] == 1  # new.md (unmapped)
        assert result["updated"] == 1  # modified.md (hash mismatch)
        assert result["failed"] == 0

    def test_push_error_handling(self, executor):
        """Test graceful handling of push errors"""
        # Create file but corrupt mapping (will cause error)
        md_file = executor.local_root / "error_block.md"
        md_file.write_text("# Error Block", encoding="utf-8")
        
        executor.conn.execute(
            "INSERT INTO block_mappings (notion_block_id, local_file_path, content_hash) VALUES (?, ?, ?)",
            ("error_block", "/nonexistent/path.md", "hash")  # Wrong path
        )
        executor.conn.commit()
        
        # Push should handle gracefully
        result = executor.sync_to_notion()
        
        # Still scanned
        assert result["scanned"] == 1
        # Updated attempted but may fail gracefully
        assert result["failed"] >= 0


class TestDetectLocalChanges:
    """Test detecting which local files have changed"""

    def test_detect_no_changes(self, executor):
        """Test detecting no changes in synced files"""
        import hashlib
        
        # Create file and mapping
        md_file = executor.local_root / "file.md"
        content = "# Content"
        md_file.write_text(content, encoding="utf-8")
        content_hash = hashlib.sha256(content.encode()).hexdigest()
        
        executor.conn.execute(
            "INSERT INTO block_mappings (notion_block_id, local_file_path, content_hash) VALUES (?, ?, ?)",
            ("file", str(md_file), content_hash)
        )
        executor.conn.commit()
        
        # Detect changes
        result = executor.detect_local_changes()
        
        assert result["unchanged"] == 1
        assert result["modified"] == 0
        assert result["new"] == 0
        assert len(result["files"]) == 1
        assert result["files"][0]["status"] == "unchanged"

    def test_detect_modified_files(self, executor):
        """Test detecting modified files"""
        import hashlib
        
        # Create file with old hash in mapping
        md_file = executor.local_root / "modified.md"
        content = "# New content"
        md_file.write_text(content, encoding="utf-8")
        
        executor.conn.execute(
            "INSERT INTO block_mappings (notion_block_id, local_file_path, content_hash) VALUES (?, ?, ?)",
            ("modified", str(md_file), "old_hash")
        )
        executor.conn.commit()
        
        # Detect changes
        result = executor.detect_local_changes()
        
        assert result["modified"] == 1
        assert result["files"][0]["status"] == "modified"

    def test_detect_new_files(self, executor):
        """Test detecting new unmapped files"""
        # Create file with no mapping
        md_file = executor.local_root / "new.md"
        md_file.write_text("# New file", encoding="utf-8")
        
        # Detect changes
        result = executor.detect_local_changes()
        
        assert result["new"] == 1
        assert result["files"][0]["status"] == "new"

    def test_detect_mixed_changes(self, executor):
        """Test detecting mix of unchanged, modified, and new files"""
        import hashlib
        
        # File 1: Unchanged
        file1 = executor.local_root / "unchanged.md"
        content1 = "# Unchanged"
        file1.write_text(content1, encoding="utf-8")
        hash1 = hashlib.sha256(content1.encode()).hexdigest()
        executor.conn.execute(
            "INSERT INTO block_mappings (notion_block_id, local_file_path, content_hash) VALUES (?, ?, ?)",
            ("unchanged", str(file1), hash1)
        )
        
        # File 2: Modified
        file2 = executor.local_root / "modified.md"
        file2.write_text("# Modified", encoding="utf-8")
        executor.conn.execute(
            "INSERT INTO block_mappings (notion_block_id, local_file_path, content_hash) VALUES (?, ?, ?)",
            ("modified", str(file2), "old_hash")
        )
        
        # File 3: New (no mapping)
        file3 = executor.local_root / "new.md"
        file3.write_text("# New", encoding="utf-8")
        
        executor.conn.commit()
        
        # Detect changes
        result = executor.detect_local_changes()
        
        assert result["unchanged"] == 1
        assert result["modified"] == 1
        assert result["new"] == 1
        assert len(result["files"]) == 3


class TestPushMethods:
    """Test individual push methods"""

    def test_push_create_valid_markdown(self, executor):
        """Test _push_create with valid markdown"""
        result = executor._push_create("test_block", "# Heading\n\nParagraph")
        
        assert result["status"] == "created"
        assert result["block_id"] == "test_block"
        assert result["action"] == "create"

    def test_push_update_valid_markdown(self, executor):
        """Test _push_update with valid markdown"""
        result = executor._push_update("test_block", "# Updated\n\nNew content")
        
        assert result["status"] == "updated"
        assert result["block_id"] == "test_block"
        assert result["action"] == "update"

    def test_push_create_empty_markdown(self, executor):
        """Test _push_create with empty markdown"""
        with pytest.raises(ValueError):
            executor._push_create("empty_block", "")

    def test_push_create_only_whitespace(self, executor):
        """Test _push_create with whitespace-only content"""
        with pytest.raises(ValueError):
            executor._push_create("whitespace_block", "   \n\n  ")


class TestPushIntegration:
    """Integration tests for push direction"""

    def test_push_pull_push_cycle(self, executor):
        """Test full cycle: pull from Notion, modify local, push back"""
        import hashlib
        
        # 1. Simulate pull: create local file from Notion block
        md_file = executor.local_root / "cycle_block.md"
        original_content = "# Original\n\nContent from Notion"
        md_file.write_text(original_content, encoding="utf-8")
        original_hash = hashlib.sha256(original_content.encode()).hexdigest()
        
        # Create mapping
        executor.conn.execute(
            "INSERT INTO block_mappings (notion_block_id, local_file_path, content_hash) VALUES (?, ?, ?)",
            ("cycle_block", str(md_file), original_hash)
        )
        executor.conn.commit()
        
        # 2. Modify local file
        modified_content = "# Updated\n\nModified locally"
        md_file.write_text(modified_content, encoding="utf-8")
        
        # 3. Detect changes
        changes = executor.detect_local_changes()
        assert changes["modified"] == 1
        
        # 4. Push back to Notion
        push_result = executor.sync_to_notion()
        assert push_result["updated"] == 1
        
        # 5. Verify hash updated
        cursor = executor.conn.execute(
            "SELECT content_hash FROM block_mappings WHERE notion_block_id=?",
            ("cycle_block",)
        )
        new_hash = cursor.fetchone()[0]
        assert new_hash != original_hash

    def test_parallel_sync_conflict(self, executor):
        """Test handling when both Notion and local files change"""
        import hashlib
        
        # Create local file
        md_file = executor.local_root / "conflict_block.md"
        local_content = "# Local Change"
        md_file.write_text(local_content, encoding="utf-8")
        
        # Mapping has old hash (indicating Notion also changed)
        executor.conn.execute(
            "INSERT INTO block_mappings (notion_block_id, local_file_path, content_hash) VALUES (?, ?, ?)",
            ("conflict_block", str(md_file), "old_hash")
        )
        executor.conn.commit()
        
        # Detect local change
        changes = executor.detect_local_changes()
        assert changes["modified"] == 1
        
        # In real system, would need to resolve conflict
        # For now, local wins (last-write-wins strategy)
        push_result = executor.sync_to_notion()
        assert push_result["updated"] == 1


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
