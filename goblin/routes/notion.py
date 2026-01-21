"""
Notion Webhook Routes

FastAPI endpoints for Notion integration:
- POST /api/v0/notion/webhook — Receive Notion webhooks
- GET /api/v0/notion/status — Check sync status
- GET /api/v0/notion/pending — List pending syncs
- POST /api/v0/notion/sync/manual — Trigger manual sync (dev)
"""

import json
from typing import Dict, Optional
from fastapi import APIRouter, Request, HTTPException, Body

from dev.goblin.services.notion_sync_service import NotionSyncService

# Initialize router and service
router = APIRouter(prefix="/api/v0/notion", tags=["notion"])

# Lazy initialization to avoid blocking startup
_sync_service = None

def get_sync_service() -> NotionSyncService:
    """Get or create sync service instance"""
    global _sync_service
    if _sync_service is None:
        _sync_service = NotionSyncService()
    return _sync_service


@router.post("/webhook")
async def notion_webhook(request: Request) -> Dict:
    """
    Receive Notion webhook notifications

    Notion sends POST requests with:
    - Header: X-Notion-Signature (HMAC-SHA256 verification)
    - Body: JSON with type, request_id, timestamp, changes[]

    Webhook types:
    - block.create
    - block.update
    - block.delete

    Returns:
        {
            "received": true,
            "type": "block.update",
            "queued": N,
            "failed": 0,
            "queue_ids": [...]
        }
    """
    try:
        sync_service = get_sync_service()
        
        # Get raw body for signature verification
        body = await request.body()
        signature_header = request.headers.get("X-Notion-Signature", "")

        # Verify signature
        if not sync_service.verify_webhook_signature(body, signature_header):
            raise HTTPException(status_code=401, detail="Invalid webhook signature")

        # Parse payload
        payload = await request.json()

        # Enqueue webhook
        result = sync_service.enqueue_webhook(payload)

        return {
            "received": True,
            "type": payload.get("type"),
            **result
        }

    except json.JSONDecodeError:
        raise HTTPException(status_code=400, detail="Invalid JSON payload")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Webhook processing error: {str(e)}")


@router.get("/status")
async def sync_status() -> Dict:
    """
    Get sync queue status

    Returns:
        {
            "total": N,
            "pending": N,
            "processing": N,
            "completed": N,
            "failed": N
        }
    """
    sync_service = get_sync_service()
    return sync_service.get_sync_status()


@router.get("/pending")
async def list_pending(limit: int = 10) -> Dict:
    """
    List pending syncs

    Args:
        limit: Maximum number of items to return (default: 10)

    Returns:
        {
            "pending": [
                {
                    "id": 1,
                    "notion_block_id": "...",
                    "database_id": "...",
                    "block_type": "heading_1",
                    "runtime_type": "STATE",
                    "action": "create",
                    "created_at": "2026-01-15T10:30:00"
                },
                ...
            ],
            "count": N
        }
    """
    sync_service = get_sync_service()
    pending = sync_service.list_pending_syncs(limit=limit)
    return {
        "pending": pending,
        "count": len(pending)
    }


@router.post("/sync/manual")
async def manual_sync(database_id: Optional[str] = None) -> Dict:
    """
    Trigger manual sync (development only)

    Args:
        database_id: Optional Notion database ID to sync

    Returns:
        {
            "status": "triggered",
            "database_id": "...",
            "message": "..."
        }

    Note:
        This is a development feature for testing webhook handling
        without waiting for real Notion updates.
    """
    return {
        "status": "triggered",
        "database_id": database_id,
        "message": "Manual sync not yet implemented (Phase C)"
    }


@router.get("/")
async def notion_status() -> Dict:
    """Root endpoint for Notion service"""
    return {
        "service": "Notion Webhook Handler",
        "version": "0.1.0",
        "status": "operational",
        "endpoints": {
            "POST /api/v0/notion/webhook": "Receive Notion webhooks",
            "GET /api/v0/notion/status": "Check sync queue status",
            "GET /api/v0/notion/pending": "List pending syncs",
            "POST /api/v0/notion/sync/manual": "Trigger manual sync (dev)"
        }
    }
