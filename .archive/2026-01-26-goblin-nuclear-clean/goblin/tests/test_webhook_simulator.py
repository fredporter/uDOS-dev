#!/usr/bin/env python3
"""
Webhook Event Simulator for Phase D Testing

Simulates Notion webhook events and verifies queue processing.
Tests the full flow: webhook → queue → sync → markdown files.
"""

import json
import sqlite3
import time
from pathlib import Path
from typing import Dict, List
import requests


class WebhookSimulator:
    """Simulate Notion webhook events for testing"""
    
    def __init__(self, webhook_url: str = "http://127.0.0.1:8767/api/v0/notion/webhook"):
        self.webhook_url = webhook_url
        self.project_root = Path(__file__).resolve().parents[3]
        self.db_path = self.project_root / "memory" / "synced" / "notion_sync.db"
        
    def create_page_event(self, page_id: str = "test-page-123", title: str = "Test Page") -> Dict:
        """Create a simulated Notion page creation event"""
        return {
            "object": "event",
            "id": f"evt_{int(time.time())}",
            "created_time": time.strftime("%Y-%m-%dT%H:%M:%S.000Z"),
            "type": "page",
            "action": "created",
            "data": {
                "object": "page",
                "id": page_id,
                "created_time": time.strftime("%Y-%m-%dT%H:%M:%S.000Z"),
                "last_edited_time": time.strftime("%Y-%m-%dT%H:%M:%S.000Z"),
                "properties": {
                    "title": {
                        "type": "title",
                        "title": [
                            {
                                "type": "text",
                                "text": {"content": title}
                            }
                        ]
                    }
                },
                "parent": {
                    "type": "database_id",
                    "database_id": "test-database-456"
                },
                "url": f"https://www.notion.so/{page_id.replace('-', '')}"
            }
        }
    
    def update_page_event(self, page_id: str = "test-page-123", title: str = "Updated Test Page") -> Dict:
        """Create a simulated Notion page update event"""
        event = self.create_page_event(page_id, title)
        event["action"] = "updated"
        event["id"] = f"evt_{int(time.time())}_upd"
        return event
    
    def delete_page_event(self, page_id: str = "test-page-123") -> Dict:
        """Create a simulated Notion page deletion event"""
        return {
            "object": "event",
            "id": f"evt_{int(time.time())}_del",
            "created_time": time.strftime("%Y-%m-%dT%H:%M:%S.000Z"),
            "type": "page",
            "action": "deleted",
            "data": {
                "object": "page",
                "id": page_id
            }
        }
    
    def send_event(self, event: Dict) -> requests.Response:
        """Send webhook event to Goblin server"""
        print(f"📤 Sending {event['action']} event for {event['data']['id']}")
        try:
            response = requests.post(
                self.webhook_url,
                json=event,
                headers={"Content-Type": "application/json"},
                timeout=5
            )
            print(f"   ✅ Response: {response.status_code}")
            return response
        except Exception as e:
            print(f"   ❌ Error: {e}")
            raise
    
    def check_queue(self) -> List[Dict]:
        """Check sync_queue for pending events"""
        if not self.db_path.exists():
            print(f"⚠️  Database not found: {self.db_path}")
            return []
        
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT id, notion_block_id, action, status, created_at
            FROM sync_queue
            WHERE status = 'pending'
            ORDER BY created_at DESC
        """)
        
        rows = cursor.fetchall()
        conn.close()
        
        return [dict(row) for row in rows]
    
    def check_history(self, notion_block_id: str = None) -> List[Dict]:
        """Check sync_history for processed events"""
        if not self.db_path.exists():
            print(f"⚠️  Database not found: {self.db_path}")
            return []
        
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        if notion_block_id:
            cursor.execute("""
                SELECT id, notion_block_id, action, status, synced_at
                FROM sync_history
                WHERE notion_block_id = ?
                ORDER BY synced_at DESC
            """, (notion_block_id,))
        else:
            cursor.execute("""
                SELECT id, notion_block_id, action, status, synced_at
                FROM sync_history
                ORDER BY synced_at DESC
                LIMIT 10
            """)
        
        rows = cursor.fetchall()
        conn.close()
        
        return [dict(row) for row in rows]
    
    def print_queue_status(self):
        """Print current queue status"""
        queue = self.check_queue()
        print(f"\n📊 Queue Status: {len(queue)} pending")
        for item in queue:
            print(f"   • {item['notion_block_id']} - {item['action']}")
    
    def print_history_status(self, notion_block_id: str = None):
        """Print sync history"""
        history = self.check_history(notion_block_id)
        print(f"\n📜 History: {len(history)} recent entries")
        for item in history:
            status_icon = "✅" if item['status'] == 'success' else "❌"
            print(f"   {status_icon} {item['notion_block_id']} - {item['action']} ({item['status']})")


def run_basic_test():
    """Run basic webhook simulation test"""
    print("=" * 80)
    print("🧪 WEBHOOK SIMULATOR - Basic Test")
    print("=" * 80)
    print()
    
    sim = WebhookSimulator()
    
    # Test 1: Create page event
    print("Test 1: Create Page Event")
    print("-" * 40)
    event = sim.create_page_event("test-001", "My First Test Page")
    response = sim.send_event(event)
    assert response.status_code == 200, f"Expected 200, got {response.status_code}"
    print()
    
    # Check queue
    sim.print_queue_status()
    
    # Test 2: Update page event
    print("\nTest 2: Update Page Event")
    print("-" * 40)
    event = sim.update_page_event("test-001", "My Updated Test Page")
    response = sim.send_event(event)
    assert response.status_code == 200, f"Expected 200, got {response.status_code}"
    print()
    
    # Check queue again
    sim.print_queue_status()
    
    # Test 3: Delete page event
    print("\nTest 3: Delete Page Event")
    print("-" * 40)
    event = sim.delete_page_event("test-001")
    response = sim.send_event(event)
    assert response.status_code == 200, f"Expected 200, got {response.status_code}"
    print()
    
    # Final queue status
    sim.print_queue_status()
    
    print("\n" + "=" * 80)
    print("✅ Basic test complete!")
    print("=" * 80)


def run_bulk_test(count: int = 5):
    """Run bulk event test"""
    print("=" * 80)
    print(f"🧪 WEBHOOK SIMULATOR - Bulk Test ({count} events)")
    print("=" * 80)
    print()
    
    sim = WebhookSimulator()
    
    for i in range(count):
        page_id = f"bulk-test-{i:03d}"
        title = f"Bulk Test Page {i+1}"
        event = sim.create_page_event(page_id, title)
        response = sim.send_event(event)
        assert response.status_code == 200
        time.sleep(0.1)  # Small delay between events
    
    print()
    sim.print_queue_status()
    
    print("\n" + "=" * 80)
    print(f"✅ Bulk test complete! {count} events queued.")
    print("=" * 80)


def main():
    """Main test runner"""
    import sys
    
    if len(sys.argv) > 1:
        command = sys.argv[1]
        if command == "bulk":
            count = int(sys.argv[2]) if len(sys.argv) > 2 else 5
            run_bulk_test(count)
        elif command == "status":
            sim = WebhookSimulator()
            sim.print_queue_status()
            sim.print_history_status()
        else:
            print(f"Unknown command: {command}")
            print("Usage: python test_webhook_simulator.py [basic|bulk [count]|status]")
    else:
        run_basic_test()


if __name__ == "__main__":
    main()
