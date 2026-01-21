"""
Task Scheduler Routes - API Endpoints

Endpoints for task scheduling and management:
    POST   /api/v0/tasks/create         - Create new task
    GET    /api/v0/tasks/<id>           - Get task details
    GET    /api/v0/tasks                - List tasks (optional state filter)
    POST   /api/v0/tasks/<id>/schedule  - Schedule task execution
    GET    /api/v0/tasks/queue          - Get pending queue
    POST   /api/v0/tasks/<run_id>/complete - Mark run as complete
    GET    /api/v0/tasks/<id>/history   - Get task execution history
    GET    /api/v0/tasks/stats          - Get scheduler statistics

Author: uDOS Team
Version: 0.1.0 (Experimental)
"""

from fastapi import APIRouter, HTTPException, Body
from pydantic import BaseModel, Field
from typing import Dict, List, Any, Optional
from datetime import datetime
import logging

from dev.goblin.services.task_scheduler import TaskScheduler

logger = logging.getLogger("goblin.tasks.routes")

# Create router
router = APIRouter(prefix="/api/v0/tasks", tags=["tasks"])

# Global scheduler instance (lazy initialized)
_scheduler = None


def get_scheduler() -> TaskScheduler:
    """Get or create the global TaskScheduler instance"""
    global _scheduler
    if _scheduler is None:
        logger.info("[TASKS] Initializing TaskScheduler...")
        _scheduler = TaskScheduler()
    return _scheduler


# Request/Response Models

class CreateTaskRequest(BaseModel):
    """Request to create task"""
    name: str = Field(..., description="Task name")
    description: str = Field("", description="Task description")
    schedule: str = Field("daily", description="Schedule (daily, weekly, monthly, etc.)")


class TaskResponse(BaseModel):
    """Task object response"""
    id: str
    name: str
    description: str
    schedule: str
    state: str  # plant|sprout|prune|trellis|harvest|compost
    created_at: str


class ScheduleTaskRequest(BaseModel):
    """Request to schedule task execution"""
    scheduled_for: Optional[str] = Field(None, description="ISO datetime when to execute (default: now)")


class CompleteTaskRequest(BaseModel):
    """Request to mark task run as complete"""
    result: str = Field("success", description="success | failed")
    output: str = Field("", description="Task execution output")


class QueueEntryResponse(BaseModel):
    """Task queue entry"""
    id: int
    task_id: str
    run_id: str
    state: str  # pending|processing|completed|failed
    scheduled_for: str
    name: str
    schedule: str


class TaskRunResponse(BaseModel):
    """Task execution run"""
    id: str
    task_id: str
    state: str
    started_at: Optional[str] = None
    completed_at: Optional[str] = None
    result: Optional[str] = None
    output: Optional[str] = None


# Routes

@router.post("/create", response_model=TaskResponse)
async def create_task(request: CreateTaskRequest):
    """Create a new task (plant state)"""
    try:
        scheduler = get_scheduler()
        result = scheduler.create_task(
            name=request.name,
            description=request.description,
            schedule=request.schedule
        )
        
        if "error" in result:
            raise HTTPException(status_code=400, detail=result["error"])
        
        logger.info(f"[TASKS] Task created: {result.get('id')}")
        return result
        
    except Exception as e:
        logger.error(f"[TASKS] Create task error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{task_id}", response_model=TaskResponse)
async def get_task(task_id: str):
    """Get task details"""
    try:
        scheduler = get_scheduler()
        task = scheduler.get_task(task_id)
        
        if not task:
            raise HTTPException(status_code=404, detail=f"Task not found: {task_id}")
        
        return task
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"[TASKS] Get task error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("", response_model=Dict[str, Any])
async def list_tasks(state: Optional[str] = None, limit: int = 50):
    """List tasks, optionally filtered by state"""
    try:
        scheduler = get_scheduler()
        tasks = scheduler.list_tasks(state=state, limit=limit)
        
        logger.info(f"[TASKS] Listed {len(tasks)} tasks" + (f" (state={state})" if state else ""))
        
        return {
            "total": len(tasks),
            "tasks": tasks,
            "filter": state or "all"
        }
    except Exception as e:
        logger.error(f"[TASKS] List tasks error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/{task_id}/schedule", response_model=Dict[str, Any])
async def schedule_task(task_id: str, request: ScheduleTaskRequest):
    """Schedule a task for execution (sprout state)"""
    try:
        scheduler = get_scheduler()
        
        # Parse scheduled_for if provided
        scheduled_for = None
        if request.scheduled_for:
            scheduled_for = datetime.fromisoformat(request.scheduled_for.replace('Z', '+00:00'))
        
        result = scheduler.schedule_task(task_id, scheduled_for)
        
        if "error" in result:
            raise HTTPException(status_code=400, detail=result["error"])
        
        logger.info(f"[TASKS] Task scheduled: {task_id}")
        return result
        
    except ValueError as e:
        raise HTTPException(status_code=400, detail=f"Invalid datetime format: {str(e)}")
    except Exception as e:
        logger.error(f"[TASKS] Schedule task error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/queue/pending", response_model=Dict[str, Any])
async def get_pending_queue(limit: int = 10):
    """Get pending tasks from queue"""
    try:
        scheduler = get_scheduler()
        pending = scheduler.get_pending_queue(limit)
        
        logger.info(f"[TASKS] Retrieved {len(pending)} pending queue entries")
        
        return {
            "total": len(pending),
            "pending": pending,
            "limit": limit
        }
    except Exception as e:
        logger.error(f"[TASKS] Get queue error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/{run_id}/complete", response_model=Dict[str, Any])
async def complete_task(run_id: str, request: CompleteTaskRequest):
    """Mark task run as complete (harvest → compost)"""
    try:
        scheduler = get_scheduler()
        
        success = scheduler.complete_task(
            run_id=run_id,
            result=request.result,
            output=request.output
        )
        
        if not success:
            raise HTTPException(status_code=400, detail=f"Failed to complete task: {run_id}")
        
        logger.info(f"[TASKS] Task completed: {run_id} - {request.result}")
        
        return {
            "run_id": run_id,
            "result": request.result,
            "state": "compost",
            "completed_at": datetime.now().isoformat()
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"[TASKS] Complete task error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{task_id}/history", response_model=Dict[str, Any])
async def get_task_history(task_id: str, limit: int = 20):
    """Get task execution history"""
    try:
        scheduler = get_scheduler()
        history = scheduler.get_task_history(task_id, limit)
        
        logger.info(f"[TASKS] Retrieved {len(history)} history entries for {task_id}")
        
        return {
            "task_id": task_id,
            "total": len(history),
            "runs": history,
            "limit": limit
        }
    except Exception as e:
        logger.error(f"[TASKS] Get history error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/stats/all", response_model=Dict[str, Any])
async def get_stats():
    """Get scheduler statistics"""
    try:
        scheduler = get_scheduler()
        stats = scheduler.get_stats()
        
        logger.info("[TASKS] Retrieved scheduler statistics")
        
        return {
            "timestamp": datetime.now().isoformat(),
            **stats
        }
    except Exception as e:
        logger.error(f"[TASKS] Get stats error: {e}")
        raise HTTPException(status_code=500, detail=str(e))
