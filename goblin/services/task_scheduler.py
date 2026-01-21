"""
Task Scheduler Service - Organic Cron Model

Implements an organic task scheduling system with states:
    Plant   → Task defined, awaiting first run
    Sprout  → Task started, initializing
    Prune   → Task executing, making decisions
    Trellis → Task growing, extending execution
    Harvest → Task completing, collecting results
    Compost → Task completed, archiving results

Author: uDOS Team
Version: 0.1.0
"""

import sqlite3
import logging
import json
from pathlib import Path
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
import uuid

logger = logging.getLogger("goblin.tasks")


class TaskScheduler:
    """Manage task scheduling and execution with organic cron model"""
    
    def __init__(self, db_path: Optional[Path] = None, notion_sync_service=None):
        """
        Initialize task scheduler
        
        Args:
            db_path: Path to SQLite database (default: memory/synced/goblin.db)
            notion_sync_service: Optional NotionSyncService for Notion integration
        """
        if db_path is None:
            db_path = Path(__file__).parent.parent.parent.parent / "memory" / "synced" / "goblin.db"
        
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self.notion_sync = notion_sync_service
        
        # Initialize database
        self._init_db()
        
        logger.info(f"[TASKS] Scheduler initialized - DB: {self.db_path}")
    
    def _init_db(self):
        """Initialize database schema"""
        # Look for schema in multiple locations
        schema_path = Path(__file__).parent.parent / "schemas" / "task_schema.sql"
        if not schema_path.exists():
            schema_path = Path(__file__).parent / "task_schema.sql"
        
        try:
            with sqlite3.connect(self.db_path) as conn:
                if schema_path.exists():
                    with open(schema_path, 'r') as f:
                        conn.executescript(f.read())
                    logger.debug("[TASKS] Database schema initialized")
                else:
                    logger.warning(f"[TASKS] Schema file not found: {schema_path}")
        except sqlite3.Error as e:
            logger.error(f"[TASKS] Database initialization error: {e}")
    
    def create_task(self, name: str, description: str = "", schedule: str = "daily") -> Dict[str, Any]:
        """
        Create a new task (Plant state)
        
        Args:
            name: Task name
            description: Task description
            schedule: Schedule (daily, weekly, monthly, etc.)
        
        Returns:
            Task object with id, name, state=plant, etc.
        """
        task_id = f"task_{uuid.uuid4().hex[:12]}"
        
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.execute(
                    """INSERT INTO tasks (id, name, description, schedule, state)
                       VALUES (?, ?, ?, ?, ?)""",
                    (task_id, name, description, schedule, "plant")
                )
                conn.commit()
            
            logger.info(f"[TASKS] Task created: {task_id} - {name}")
            
            return {
                "id": task_id,
                "name": name,
                "description": description,
                "schedule": schedule,
                "state": "plant",
                "created_at": datetime.now().isoformat()
            }
        except sqlite3.Error as e:
            logger.error(f"[TASKS] Create task error: {e}")
            return {"error": str(e)}
    
    def get_task(self, task_id: str) -> Optional[Dict[str, Any]]:
        """Get task by ID"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.execute("SELECT * FROM tasks WHERE id = ?", (task_id,))
                row = cursor.fetchone()
                
                if row:
                    return dict(row)
            return None
        except sqlite3.Error as e:
            logger.error(f"[TASKS] Get task error: {e}")
            return None
    
    def list_tasks(self, state: Optional[str] = None, limit: int = 50) -> List[Dict[str, Any]]:
        """
        List tasks, optionally filtered by state
        
        Args:
            state: Filter by state (plant/sprout/prune/trellis/harvest/compost)
            limit: Maximum results
        
        Returns:
            List of task objects
        """
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.row_factory = sqlite3.Row
                
                if state:
                    cursor = conn.execute(
                        "SELECT * FROM tasks WHERE state = ? LIMIT ?",
                        (state, limit)
                    )
                else:
                    cursor = conn.execute("SELECT * FROM tasks LIMIT ?", (limit,))
                
                return [dict(row) for row in cursor.fetchall()]
        except sqlite3.Error as e:
            logger.error(f"[TASKS] List tasks error: {e}")
            return []
    
    def schedule_task(self, task_id: str, scheduled_for: Optional[datetime] = None) -> Dict[str, Any]:
        """
        Schedule a task for execution (move to sprout state)
        
        Args:
            task_id: Task ID
            scheduled_for: When to execute (default: now)
        
        Returns:
            Queue entry
        """
        if scheduled_for is None:
            scheduled_for = datetime.now()
        
        run_id = f"run_{uuid.uuid4().hex[:12]}"
        
        try:
            with sqlite3.connect(self.db_path) as conn:
                # Create task run
                conn.execute(
                    """INSERT INTO task_runs (id, task_id, state)
                       VALUES (?, ?, ?)""",
                    (run_id, task_id, "sprout")
                )
                
                # Add to queue
                conn.execute(
                    """INSERT INTO task_queue (task_id, run_id, state, scheduled_for)
                       VALUES (?, ?, ?, ?)""",
                    (task_id, run_id, "pending", scheduled_for)
                )
                
                # Update task state to sprout
                conn.execute(
                    "UPDATE tasks SET state = ?, updated_at = CURRENT_TIMESTAMP WHERE id = ?",
                    ("sprout", task_id)
                )
                
                conn.commit()
            
            logger.info(f"[TASKS] Task scheduled: {task_id} → run {run_id}")
            
            return {
                "task_id": task_id,
                "run_id": run_id,
                "state": "pending",
                "scheduled_for": scheduled_for.isoformat()
            }
        except sqlite3.Error as e:
            logger.error(f"[TASKS] Schedule task error: {e}")
            return {"error": str(e)}
    
    def get_pending_queue(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Get pending tasks from queue"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.execute(
                    """SELECT q.*, t.name, t.schedule FROM task_queue q
                       JOIN tasks t ON q.task_id = t.id
                       WHERE q.state = 'pending' AND q.scheduled_for <= CURRENT_TIMESTAMP
                       LIMIT ?""",
                    (limit,)
                )
                return [dict(row) for row in cursor.fetchall()]
        except sqlite3.Error as e:
            logger.error(f"[TASKS] Get pending queue error: {e}")
            return []
    
    def mark_processing(self, queue_id: int) -> bool:
        """Mark queue entry as processing (prune state)"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.execute(
                    "UPDATE task_queue SET state = 'processing' WHERE id = ?",
                    (queue_id,)
                )
                conn.commit()
            logger.debug(f"[TASKS] Queue {queue_id} marked as processing")
            return True
        except sqlite3.Error as e:
            logger.error(f"[TASKS] Mark processing error: {e}")
            return False
    
    def complete_task(self, run_id: str, result: str = "success", output: str = "") -> bool:
        """
        Complete a task run (harvest → compost)
        
        Args:
            run_id: Run ID
            result: success | failed
            output: Task output/result
        
        Returns:
            Success flag
        """
        try:
            with sqlite3.connect(self.db_path) as conn:
                # Update task run
                conn.execute(
                    """UPDATE task_runs 
                       SET state = 'compost', result = ?, output = ?, completed_at = CURRENT_TIMESTAMP
                       WHERE id = ?""",
                    (result, output, run_id)
                )
                
                # Get task_id from run
                cursor = conn.execute("SELECT task_id FROM task_runs WHERE id = ?", (run_id,))
                row = cursor.fetchone()
                task_id = row[0] if row else None
                
                # Update queue entry
                conn.execute(
                    "UPDATE task_queue SET state = 'completed', processed_at = CURRENT_TIMESTAMP WHERE run_id = ?",
                    (run_id,)
                )
                
                # Update task state to harvest
                if task_id:
                    conn.execute(
                        "UPDATE tasks SET state = ?, updated_at = CURRENT_TIMESTAMP WHERE id = ?",
                        ("harvest", task_id)
                    )
                
                conn.commit()
            
            logger.info(f"[TASKS] Task run completed: {run_id} - {result}")
            return True
        except sqlite3.Error as e:
            logger.error(f"[TASKS] Complete task error: {e}")
            return False
    
    def get_task_history(self, task_id: str, limit: int = 20) -> List[Dict[str, Any]]:
        """Get task execution history (runs)"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.execute(
                    """SELECT * FROM task_runs 
                       WHERE task_id = ?
                       ORDER BY created_at DESC
                       LIMIT ?""",
                    (task_id, limit)
                )
                return [dict(row) for row in cursor.fetchall()]
        except sqlite3.Error as e:
            logger.error(f"[TASKS] Get history error: {e}")
            return []
    
    def get_stats(self) -> Dict[str, Any]:
        """Get scheduler statistics"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                # Task counts by state
                cursor = conn.execute(
                    "SELECT state, COUNT(*) as count FROM tasks GROUP BY state"
                )
                task_stats = {row[0]: row[1] for row in cursor.fetchall()}
                
                # Queue counts
                cursor = conn.execute(
                    "SELECT COUNT(*) FROM task_queue WHERE state = 'pending'"
                )
                pending_count = cursor.fetchone()[0]
                
                # Recent runs
                cursor = conn.execute(
                    "SELECT COUNT(*) FROM task_runs WHERE result = 'success' AND completed_at > datetime('now', '-1 day')"
                )
                successful_today = cursor.fetchone()[0]
                
                return {
                    "tasks": task_stats,
                    "pending_queue": pending_count,
                    "successful_today": successful_today
                }
        except sqlite3.Error as e:
            logger.error(f"[TASKS] Get stats error: {e}")
            return {}
        """
        Schedule task for execution
        
        Args:
            task: {
                "name": "Task name",
                "type": "research | scrape | summarize | code | write",
                "project_id": "...",
                "cadence": "once | daily | weekly",
                "priority": "high | medium | low",
                "provider_hint": "ollama | openrouter | vib"
            }
        """
        task_id = f"task_{len(self.queue) + 1:03d}"
        
        scheduled_task = {
            **task,
            "task_id": task_id,
            "status": "scheduled",
            "scheduled_at": datetime.now().isoformat(),
            "phase": CronPhase.PLANT.value
        }
        
        self.queue.append(scheduled_task)
        
        logger.info(f"[GOBLIN:SCHEDULER] Scheduled task: {task.get('name')} ({task_id})")
        
        return {
            "status": "scheduled",
            "task_id": task_id,
            "scheduled_at": scheduled_task["scheduled_at"]
        }
    
    async def get_queue(self) -> Dict[str, Any]:
        """Get current task queue"""
        pending = [t for t in self.queue if t["status"] == "scheduled"]
        running = [t for t in self.queue if t["status"] == "running"]
        completed = [t for t in self.queue if t["status"] == "completed"]
        
        return {
            "total": len(self.queue),
            "pending": pending,
            "running": running,
            "completed": completed
        }
    
    async def get_runs(self) -> List[Dict[str, Any]]:
        """Get task execution history"""
        return self.runs.copy()
    
    async def execute_next(self) -> Optional[Dict[str, Any]]:
        """
        Execute next task in queue (organic cron logic)
        
        Returns execution result or None if queue empty
        """
        # Find next task based on:
        # 1. Priority
        # 2. Cadence timing
        # 3. Current phase
        # 4. Quota availability
        
        pending_tasks = [t for t in self.queue if t["status"] == "scheduled"]
        
        if not pending_tasks:
            return None
        
        # Simple priority sort for v0
        task = max(pending_tasks, key=lambda t: self._priority_score(t))
        
        logger.info(f"[GOBLIN:SCHEDULER] Executing task: {task['task_id']}")
        
        # Mark as running
        task["status"] = "running"
        task["started_at"] = datetime.now().isoformat()
        
        # Execute (placeholder)
        result = await self._execute_task(task)
        
        # Record run
        run = {
            "run_id": f"run_{len(self.runs) + 1:03d}",
            "task_id": task["task_id"],
            "started_at": task["started_at"],
            "completed_at": datetime.now().isoformat(),
            "result": result,
            "provider": result.get("provider", "unknown"),
            "cost": result.get("cost", 0.0)
        }
        
        self.runs.append(run)
        
        # Mark as completed
        task["status"] = "completed"
        task["completed_at"] = run["completed_at"]
        
        return run
    
    async def _execute_task(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """Execute task (placeholder for provider integration)"""
        # TODO: Integrate with Ollama/OpenRouter
        # TODO: Implement provider rotation
        # TODO: Apply quota limits
        
        return {
            "status": "completed",
            "provider": "ollama",
            "model": "mistral",
            "cost": 0.0,
            "output": "Task executed successfully (placeholder)"
        }
    
    def _priority_score(self, task: Dict[str, Any]) -> int:
        """Calculate priority score for task scheduling"""
        priority_map = {"high": 3, "medium": 2, "low": 1}
        base_score = priority_map.get(task.get("priority", "medium"), 2)
        
        # Boost score based on cadence timing
        # TODO: Check last run time and cadence
        
        return base_score
