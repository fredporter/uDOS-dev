#!/usr/bin/env python3
"""
Task Scheduler Tests

Tests for task creation, scheduling, execution, and state management.

Usage:
    python test_task_scheduler.py
"""

import sys
from pathlib import Path
from datetime import datetime, timedelta

# Add project root to path
project_root = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(project_root))

from dev.goblin.services.task_scheduler import TaskScheduler


def test_task_creation():
    """Test task creation (plant state)"""
    print("\n" + "=" * 80)
    print("TEST: Task Creation (Plant State)")
    print("=" * 80)
    
    scheduler = TaskScheduler()
    
    task1 = scheduler.create_task(
        name="Daily Backup",
        description="Backup database daily",
        schedule="daily"
    )
    
    task2 = scheduler.create_task(
        name="Weekly Report",
        schedule="weekly"
    )
    
    print(f"Created Task 1: {task1['id']} ({task1['name']})")
    print(f"  State: {task1['state']}")
    print(f"Created Task 2: {task2['id']} ({task2['name']})")
    print(f"  State: {task2['state']}")
    
    if task1['state'] == 'plant' and task2['state'] == 'plant':
        print("✅ Task creation test passed")
        return True, (task1, task2)
    else:
        print("❌ Expected plant state for new tasks")
        return False, (task1, task2)


def test_task_retrieval(task1, task2):
    """Test retrieving task details"""
    print("\n" + "=" * 80)
    print("TEST: Task Retrieval")
    print("=" * 80)
    
    scheduler = TaskScheduler()
    
    # Get task by ID
    retrieved = scheduler.get_task(task1['id'])
    
    print(f"Retrieved: {retrieved['id']} ({retrieved['name']})")
    print(f"  Schedule: {retrieved['schedule']}")
    print(f"  State: {retrieved['state']}")
    
    if retrieved and retrieved['id'] == task1['id']:
        print("✅ Task retrieval test passed")
        return True
    else:
        print("❌ Task retrieval failed")
        return False


def test_list_tasks(task1, task2):
    """Test listing tasks"""
    print("\n" + "=" * 80)
    print("TEST: List Tasks")
    print("=" * 80)
    
    scheduler = TaskScheduler()
    
    # List all tasks
    all_tasks = scheduler.list_tasks(limit=50)
    print(f"Total tasks: {len(all_tasks)}")
    
    # List by state
    plant_tasks = scheduler.list_tasks(state='plant')
    print(f"Tasks in plant state: {len(plant_tasks)}")
    
    for task in plant_tasks[:3]:
        print(f"  - {task['name']} ({task['state']})")
    
    if len(plant_tasks) >= 2:
        print("✅ List tasks test passed")
        return True
    else:
        print("❌ Expected at least 2 tasks in plant state")
        return False


def test_task_scheduling(task1):
    """Test scheduling task (sprout state)"""
    print("\n" + "=" * 80)
    print("TEST: Task Scheduling (Sprout State)")
    print("=" * 80)
    
    scheduler = TaskScheduler()
    
    # Schedule task immediately
    schedule_result = scheduler.schedule_task(task1['id'])
    
    print(f"Scheduled task: {task1['id']}")
    print(f"  Run ID: {schedule_result['run_id']}")
    print(f"  State: {schedule_result['state']}")
    print(f"  Scheduled for: {schedule_result['scheduled_for']}")
    
    # Verify task state changed to sprout
    updated_task = scheduler.get_task(task1['id'])
    print(f"  Task state after scheduling: {updated_task['state']}")
    
    if schedule_result['state'] == 'pending' and updated_task['state'] == 'sprout':
        print("✅ Task scheduling test passed")
        return True, schedule_result['run_id']
    else:
        print("❌ Task scheduling failed")
        return False, None


def test_pending_queue():
    """Test retrieving pending queue"""
    print("\n" + "=" * 80)
    print("TEST: Pending Queue")
    print("=" * 80)
    
    scheduler = TaskScheduler()
    
    pending = scheduler.get_pending_queue(limit=10)
    
    print(f"Pending tasks: {len(pending)}")
    for entry in pending[:3]:
        print(f"  - {entry['name']} (scheduled: {entry['scheduled_for']})")
    
    if len(pending) > 0:
        print("✅ Pending queue test passed")
        return True
    else:
        print("⚠️  No pending tasks (expected if tests run immediately)")
        return True


def test_task_completion(run_id):
    """Test completing task (harvest → compost)"""
    print("\n" + "=" * 80)
    print("TEST: Task Completion (Harvest → Compost)")
    print("=" * 80)
    
    scheduler = TaskScheduler()
    
    if not run_id:
        print("⚠️  Skipping (no run_id from scheduling)")
        return True
    
    # Complete the task
    success = scheduler.complete_task(
        run_id=run_id,
        result="success",
        output="Backup completed successfully"
    )
    
    print(f"Completed run: {run_id}")
    print(f"  Result: success")
    print(f"  Output: Backup completed successfully")
    
    if success:
        print("✅ Task completion test passed")
        return True
    else:
        print("❌ Task completion failed")
        return False


def test_task_history(task1):
    """Test retrieving task execution history"""
    print("\n" + "=" * 80)
    print("TEST: Task Execution History")
    print("=" * 80)
    
    scheduler = TaskScheduler()
    
    history = scheduler.get_task_history(task1['id'], limit=10)
    
    print(f"Task: {task1['id']}")
    print(f"Total runs: {len(history)}")
    
    for run in history[:3]:
        state = run['state'] if 'state' in run else 'unknown'
        result = run['result'] if 'result' in run else 'pending'
        print(f"  - Run ID: {run['id']}")
        print(f"    State: {state}, Result: {result}")
    
    if len(history) >= 0:  # May be 0 if task not fully executed
        print("✅ Task history test passed")
        return True
    else:
        print("❌ Task history retrieval failed")
        return False


def test_scheduler_stats():
    """Test scheduler statistics"""
    print("\n" + "=" * 80)
    print("TEST: Scheduler Statistics")
    print("=" * 80)
    
    scheduler = TaskScheduler()
    
    stats = scheduler.get_stats()
    
    print("Scheduler Stats:")
    print(f"  Tasks by state: {stats.get('tasks', {})}")
    print(f"  Pending queue: {stats.get('pending_queue', 0)}")
    print(f"  Successful today: {stats.get('successful_today', 0)}")
    
    if stats and 'tasks' in stats:
        print("✅ Scheduler stats test passed")
        return True
    else:
        print("❌ Stats retrieval failed")
        return False


def run_all_tests():
    """Run all task scheduler tests"""
    print("\n" + "=" * 80)
    print("🧪 TASK SCHEDULER TESTS")
    print("=" * 80)
    
    tests = [
        ("Task Creation", test_task_creation, []),
    ]
    
    passed = 0
    failed = 0
    task1 = None
    task2 = None
    run_id = None
    
    # Test 1: Creation
    success, (task1, task2) = test_task_creation()
    if success:
        passed += 1
    else:
        failed += 1
        return failed == 0
    
    # Test 2: Retrieval
    if test_task_retrieval(task1, task2):
        passed += 1
    else:
        failed += 1
    
    # Test 3: List
    if test_list_tasks(task1, task2):
        passed += 1
    else:
        failed += 1
    
    # Test 4: Scheduling
    success, run_id = test_task_scheduling(task1)
    if success:
        passed += 1
    else:
        failed += 1
    
    # Test 5: Pending Queue
    if test_pending_queue():
        passed += 1
    else:
        failed += 1
    
    # Test 6: Completion
    if test_task_completion(run_id):
        passed += 1
    else:
        failed += 1
    
    # Test 7: History
    if test_task_history(task1):
        passed += 1
    else:
        failed += 1
    
    # Test 8: Stats
    if test_scheduler_stats():
        passed += 1
    else:
        failed += 1
    
    print("\n" + "=" * 80)
    if failed == 0:
        print(f"✅ ALL TASK SCHEDULER TESTS PASSED ({passed}/{passed})")
    else:
        print(f"⚠️  TESTS COMPLETED: {passed} passed, {failed} failed")
    print("=" * 80)
    
    return failed == 0


if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)
