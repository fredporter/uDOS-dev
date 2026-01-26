#!/usr/bin/env python3
"""
Task Scheduler API Tests

Tests for FastAPI endpoints for task management and scheduling.

Usage:
    # Start Goblin server first
    python wizard/launch_goblin_dev.py
    
    # In another terminal:
    python test_task_scheduler_api.py
"""

import sys
import time
import requests
from pathlib import Path
from datetime import datetime, timedelta

BASE_URL = "http://localhost:8767"
TIMEOUT = 5


def print_header(test_name):
    """Print test header"""
    print("\n" + "=" * 80)
    print(f"TEST: {test_name}")
    print("=" * 80)


def test_create_task():
    """Test POST /api/v0/tasks/create"""
    print_header("Create Task")
    
    payload = {
        "name": "Email Report",
        "description": "Send weekly email report",
        "schedule": "weekly"
    }
    
    try:
        response = requests.post(
            f"{BASE_URL}/api/v0/tasks/create",
            json=payload,
            timeout=TIMEOUT
        )
        response.raise_for_status()
        task = response.json()
        
        print(f"✅ Created task: {task['id']}")
        print(f"   Name: {task['name']}")
        print(f"   State: {task['state']}")
        
        return task
    except Exception as e:
        print(f"❌ Error: {e}")
        return None


def test_get_task(task):
    """Test GET /api/v0/tasks/{id}"""
    print_header("Get Task Details")
    
    if not task:
        print("⚠️  Skipping (no task created)")
        assert False, "Test failed"
    
    try:
        response = requests.get(
            f"{BASE_URL}/api/v0/tasks/{task['id']}",
            timeout=TIMEOUT
        )
        response.raise_for_status()
        result = response.json()
        
        print(f"✅ Retrieved task: {result['id']}")
        print(f"   Name: {result['name']}")
        print(f"   Schedule: {result['schedule']}")
        print(f"   State: {result['state']}")
        
        assert True
    except Exception as e:
        print(f"❌ Error: {e}")
        assert False, "Test failed"


def test_list_tasks():
    """Test GET /api/v0/tasks"""
    print_header("List All Tasks")
    
    try:
        response = requests.get(
            f"{BASE_URL}/api/v0/tasks?limit=10",
            timeout=TIMEOUT
        )
        response.raise_for_status()
        data = response.json()
        tasks = data["tasks"]
        
        print(f"✅ Retrieved {len(tasks)} tasks")
        for task in list(tasks)[:3]:
            print(f"   - {task['name']} ({task['state']})")
        
        assert True
    except Exception as e:
        print(f"❌ Error: {e}")
        assert False, "Test failed"


def test_list_tasks_by_state():
    """Test GET /api/v0/tasks?state=plant"""
    print_header("List Tasks by State")
    
    try:
        response = requests.get(
            f"{BASE_URL}/api/v0/tasks?state=plant&limit=10",
            timeout=TIMEOUT
        )
        response.raise_for_status()
        data = response.json()
        tasks = data["tasks"]
        
        print(f"✅ Retrieved {len(tasks)} tasks in 'plant' state")
        for task in list(tasks)[:3]:
            print(f"   - {task['name']}")
        
        assert True
    except Exception as e:
        print(f"❌ Error: {e}")
        assert False, "Test failed"


def test_schedule_task(task):
    """Test POST /api/v0/tasks/{id}/schedule"""
    print_header("Schedule Task for Execution")
    
    if not task:
        print("⚠️  Skipping (no task created)")
        return None
    
    try:
        response = requests.post(
            f"{BASE_URL}/api/v0/tasks/{task['id']}/schedule",
            json={},
            timeout=TIMEOUT
        )
        response.raise_for_status()
        result = response.json()
        
        print(f"✅ Scheduled task: {task['id']}")
        print(f"   Run ID: {result['run_id']}")
        print(f"   State: {result['state']}")
        print(f"   Scheduled for: {result['scheduled_for']}")
        
        return result
    except Exception as e:
        print(f"❌ Error: {e}")
        return None


def test_pending_queue():
    """Test GET /api/v0/tasks/queue/pending"""
    print_header("Get Pending Queue")
    
    try:
        response = requests.get(
            f"{BASE_URL}/api/v0/tasks/queue/pending?limit=10",
            timeout=TIMEOUT
        )
        response.raise_for_status()
        data = response.json()
        queue = data.get("pending", [])
        
        print(f"✅ Retrieved {len(queue)} pending tasks")
        for entry in list(queue)[:3]:
            print(f"   - {entry.get('name', 'N/A')} (scheduled: {entry.get('scheduled_for', 'N/A')})")
        
        assert True
    except Exception as e:
        print(f"❌ Error: {e}")
        assert False, "Test failed"


def test_complete_task(schedule_result):
    """Test POST /api/v0/tasks/{run_id}/complete"""
    print_header("Complete Task Execution")
    
    if not schedule_result or 'run_id' not in schedule_result:
        print("⚠️  Skipping (no scheduled task)")
        assert False, "Test failed"
    
    run_id = schedule_result['run_id']
    
    try:
        response = requests.post(
            f"{BASE_URL}/api/v0/tasks/{run_id}/complete",
            json={
                "result": "success",
                "output": "Task completed successfully via API"
            },
            timeout=TIMEOUT
        )
        response.raise_for_status()
        result = response.json()
        
        print(f"✅ Completed task: {run_id}")
        print(f"   Result: {result.get('result', 'N/A')}")
        print(f"   Output: {result.get('output', 'N/A')}")
        
        assert True
    except Exception as e:
        print(f"❌ Error: {e}")
        assert False, "Test failed"


def test_task_history(task):
    """Test GET /api/v0/tasks/{id}/history"""
    print_header("Get Task Execution History")
    
    if not task:
        print("⚠️  Skipping (no task created)")
        assert False, "Test failed"
    
    try:
        response = requests.get(
            f"{BASE_URL}/api/v0/tasks/{task['id']}/history?limit=10",
            timeout=TIMEOUT
        )
        response.raise_for_status()
        data = response.json()
        history = data.get("runs", [])
        
        print(f"✅ Retrieved {len(history)} execution runs")
        for run in list(history)[:3]:
            result = run.get('result', 'pending')
            print(f"   - Run: {run.get('id', 'N/A')} - Result: {result}")
        
        assert True
    except Exception as e:
        print(f"❌ Error: {e}")
        assert False, "Test failed"


def test_scheduler_stats():
    """Test GET /api/v0/tasks/stats/all"""
    print_header("Get Scheduler Statistics")
    
    try:
        response = requests.get(
            f"{BASE_URL}/api/v0/tasks/stats/all",
            timeout=TIMEOUT
        )
        response.raise_for_status()
        stats = response.json()
        
        print(f"✅ Retrieved scheduler statistics")
        print(f"   Tasks by state: {stats.get('tasks', {})}")
        print(f"   Pending queue: {stats.get('pending_queue', 0)}")
        print(f"   Successful today: {stats.get('successful_today', 0)}")
        
        assert True
    except Exception as e:
        print(f"❌ Error: {e}")
        assert False, "Test failed"


def check_server():
    """Check if server is running"""
    print("\n" + "=" * 80)
    print("🔍 Checking Goblin Dev Server...")
    print("=" * 80)
    
    try:
        response = requests.get(f"{BASE_URL}/health", timeout=TIMEOUT)
        print(f"✅ Server is running at {BASE_URL}")
        assert True
    except Exception as e:
        print(f"❌ Cannot connect to server at {BASE_URL}")
        print(f"   Error: {e}")
        print("\n   Start the server with:")
        print("   python wizard/launch_goblin_dev.py")
        assert False, "Test failed"


def run_all_tests():
    """Run all API tests"""
    if not check_server():
        assert False, "Test failed"
    
    print("\n" + "=" * 80)
    print("🧪 TASK SCHEDULER API TESTS")
    print("=" * 80)
    
    passed = 0
    failed = 0
    task = None
    schedule_result = None
    
    # Test 1: Create Task
    task = test_create_task()
    if task:
        passed += 1
    else:
        failed += 1
    
    # Test 2: Get Task
    if test_get_task(task):
        passed += 1
    else:
        failed += 1
    
    # Test 3: List All Tasks
    if test_list_tasks():
        passed += 1
    else:
        failed += 1
    
    # Test 4: List by State
    if test_list_tasks_by_state():
        passed += 1
    else:
        failed += 1
    
    # Test 5: Schedule Task
    schedule_result = test_schedule_task(task)
    if schedule_result:
        passed += 1
    else:
        failed += 1
    
    # Test 6: Pending Queue
    if test_pending_queue():
        passed += 1
    else:
        failed += 1
    
    # Test 7: Complete Task
    if test_complete_task(schedule_result):
        passed += 1
    else:
        failed += 1
    
    # Test 8: Task History
    if test_task_history(task):
        passed += 1
    else:
        failed += 1
    
    # Test 9: Scheduler Stats
    if test_scheduler_stats():
        passed += 1
    else:
        failed += 1
    
    print("\n" + "=" * 80)
    if failed == 0:
        print(f"✅ ALL TASK SCHEDULER API TESTS PASSED ({passed}/{passed})")
    else:
        print(f"⚠️  TESTS COMPLETED: {passed} passed, {failed} failed")
    print("=" * 80)
    
    return failed == 0


if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)
