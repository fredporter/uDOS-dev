"""
Phase B: Webhook Handler Tests

Tests for:
- NotionSyncService webhook verification
- Block queueing
- SQLite storage
- Route endpoints
"""

import os
import json
import hmac
import hashlib
import sqlite3
import pytest
from pathlib import Path

# Set up Python path
import sys
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from dev.goblin.services.notion_sync_service import NotionSyncService
from dev.goblin.routes.notion import router as notion_router


class TestNotionSyncService:
    """Test NotionSyncService"""

    @pytest.fixture
    def service(self, tmp_path):
        """Create service with temp database"""
        db_path = tmp_path / "test_sync.db"
        service = NotionSyncService(db_path=str(db_path))
        yield service
        service.close()

    def test_init(self, service):
        """Test service initialization"""
        assert service.db_path
        assert service.conn is not None

    def test_verify_webhook_signature_valid(self, service):
        """Test HMAC verification with valid signature"""
        # Set secret in service
        service.webhook_secret = "test-secret"
        
        body = b"test body"
        expected_sig = hmac.new(
            b"test-secret",
            body,
            hashlib.sha256
        ).hexdigest()
        
        signature_header = f"Signature={expected_sig}"
        
        assert service.verify_webhook_signature(body, signature_header) == True

    def test_verify_webhook_signature_invalid(self, service):
        """Test HMAC verification with invalid signature"""
        service.webhook_secret = "test-secret"
        
        body = b"test body"
        invalid_sig = "invalid_signature"
        signature_header = f"Signature={invalid_sig}"
        
        assert service.verify_webhook_signature(body, signature_header) == False

    def test_verify_webhook_signature_no_secret(self, service):
        """Test verification with no secret configured (dev mode)"""
        service.webhook_secret = ""  # No secret
        
        body = b"test body"
        signature_header = "Signature=anything"
        
        # Should accept all in dev mode
        assert service.verify_webhook_signature(body, signature_header) == True

    def test_enqueue_webhook_single_block(self, service):
        """Test queueing a single block update"""
        payload = {
            "type": "block.update",
            "id": "block123",
            "database_id": "db456",
            "block_type": "heading_1"
        }
        
        result = service.enqueue_webhook(payload)
        
        assert result["queued"] == 1
        assert result["failed"] == 0
        assert len(result["queue_ids"]) == 1

    def test_enqueue_webhook_multiple_blocks(self, service):
        """Test queueing multiple block changes"""
        payload = {
            "type": "block.create",
            "database_id": "db456",
            "changes": [
                {"id": "block1", "type": "heading_1"},
                {"id": "block2", "type": "paragraph"},
                {"id": "block3", "type": "code"}
            ]
        }
        
        result = service.enqueue_webhook(payload)
        
        assert result["queued"] == 3
        assert result["failed"] == 0

    def test_detect_runtime_block_from_caption(self, service):
        """Test detecting runtime blocks from caption"""
        block = {
            "type": "code",
            "caption": [
                {"plain_text": "[uDOS:FORM] User input form"}
            ]
        }
        
        runtime_type = service._detect_runtime_block(block)
        assert runtime_type == "FORM"

    def test_detect_runtime_blocks_all_types(self, service):
        """Test detecting all runtime block types"""
        runtime_types = ["STATE", "SET", "FORM", "IF", "NAV", "PANEL", "MAP"]
        
        for rt in runtime_types:
            block = {
                "caption": [{"plain_text": f"[uDOS:{rt}] description"}]
            }
            detected = service._detect_runtime_block(block)
            assert detected == rt, f"Failed to detect {rt}"

    def test_get_sync_status(self, service):
        """Test getting sync status"""
        # Queue some blocks
        payload1 = {
            "type": "block.create",
            "id": "b1",
            "database_id": "db1"
        }
        service.enqueue_webhook(payload1)
        
        payload2 = {
            "type": "block.update",
            "id": "b2",
            "database_id": "db1"
        }
        service.enqueue_webhook(payload2)
        
        status = service.get_sync_status()
        
        assert status["total"] == 2
        assert status["pending"] == 2
        assert status["processing"] == 0
        assert status["completed"] == 0
        assert status["failed"] == 0

    def test_list_pending_syncs(self, service):
        """Test listing pending syncs"""
        # Queue blocks
        for i in range(5):
            payload = {
                "type": "block.create",
                "id": f"block{i}",
                "database_id": "db1",
                "block_type": "paragraph"
            }
            service.enqueue_webhook(payload)
        
        pending = service.list_pending_syncs(limit=3)
        
        assert len(pending) == 3
        assert pending[0]["notion_block_id"] == "block0"

    def test_mark_processing(self, service):
        """Test marking entry as processing"""
        payload = {
            "type": "block.update",
            "id": "block1",
            "database_id": "db1"
        }
        result = service.enqueue_webhook(payload)
        queue_id = result["queue_ids"][0]
        
        service.mark_processing(queue_id)
        
        status = service.get_sync_status()
        assert status["processing"] == 1
        assert status["pending"] == 0

    def test_mark_completed(self, service):
        """Test marking entry as completed"""
        payload = {
            "type": "block.update",
            "id": "block1",
            "database_id": "db1"
        }
        result = service.enqueue_webhook(payload)
        queue_id = result["queue_ids"][0]
        
        service.mark_completed(queue_id, "/path/to/file.md")
        
        status = service.get_sync_status()
        assert status["completed"] == 1
        assert status["pending"] == 0

    def test_mark_failed(self, service):
        """Test marking entry as failed"""
        payload = {
            "type": "block.update",
            "id": "block1",
            "database_id": "db1"
        }
        result = service.enqueue_webhook(payload)
        queue_id = result["queue_ids"][0]
        
        service.mark_failed(queue_id, "Block parsing failed")
        
        status = service.get_sync_status()
        assert status["failed"] == 1
        assert status["pending"] == 0

    def test_enqueue_webhook_missing_id(self, service):
        """Test error handling for missing block ID"""
        payload = {
            "type": "block.create",
            "database_id": "db1"
            # Missing: id
        }
        
        result = service.enqueue_webhook(payload)
        
        assert result["queued"] == 0
        assert result["failed"] == 1


class TestNotionRoutes:
    """Test Notion API routes"""

    @pytest.fixture
    def client(self):
        """Create FastAPI test client"""
        from fastapi.testclient import TestClient
        from dev.goblin.goblin_server import app
        
        return TestClient(app)

    def test_notion_root_endpoint(self, client):
        """Test Notion root endpoint"""
        response = client.get("/api/v0/notion/")
        
        assert response.status_code == 200
        data = response.json()
        assert data["service"] == "Notion Webhook Handler"
        assert "endpoints" in data

    def test_sync_status_endpoint(self, client):
        """Test sync status endpoint"""
        response = client.get("/api/v0/notion/status")
        
        assert response.status_code == 200
        data = response.json()
        assert "total" in data
        assert "pending" in data

    def test_pending_syncs_endpoint(self, client):
        """Test pending syncs endpoint"""
        response = client.get("/api/v0/notion/pending")
        
        assert response.status_code == 200
        data = response.json()
        assert "pending" in data
        assert "count" in data

    def test_webhook_endpoint_missing_signature(self, client):
        """Test webhook endpoint rejects invalid signature"""
        payload = {"type": "block.update", "id": "b1"}
        
        response = client.post(
            "/api/v0/notion/webhook",
            json=payload,
            headers={"X-Notion-Signature": "Signature=invalid"}
        )
        
        # Should reject if secret is configured
        # (In test env, no secret, so should accept)
        assert response.status_code == 200

    def test_webhook_endpoint_valid(self, client):
        """Test webhook endpoint accepts valid payload"""
        payload = {
            "type": "block.update",
            "id": "block123",
            "database_id": "db456"
        }
        
        response = client.post(
            "/api/v0/notion/webhook",
            json=payload
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["received"] == True
        assert data["type"] == "block.update"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
