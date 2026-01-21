"""
Workflow Manager Routes for Goblin Dev Server
"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import List, Optional

from ..services.workflow_manager import TaskStatus

router = APIRouter(prefix="/api/v0/workflow", tags=["workflow"])

# Lazy initialization - only create when needed
_workflow_instance = None


def get_workflow():
    """Lazy-load workflow manager."""
    global _workflow_instance
    if _workflow_instance is None:
        from ..services.workflow_manager import WorkflowManager
        _workflow_instance = WorkflowManager()
    return _workflow_instance


class ProjectCreate(BaseModel):
    """Project creation request."""
    name: str
    description: str = ""


class TaskCreate(BaseModel):
    """Task creation request."""
    project_id: int
    title: str
    description: str = ""
    priority: int = 5
    depends_on: Optional[List[int]] = None
    tags: Optional[List[str]] = None


class TaskStatusUpdate(BaseModel):
    """Task status update request."""
    status: str  # Will be validated against TaskStatus enum


@router.get("/health")
async def health_check():
    """Check workflow manager availability."""
    workflow = get_workflow()
    return {"status": "ok", "db_path": str(workflow.db_path)}


@router.post("/projects")
async def create_project(project: ProjectCreate):
    """Create a new project."""
    try:
        workflow = get_workflow()
        project_id = workflow.create_project(
            name=project.name,
            description=project.description
        )
        return {"project_id": project_id, "name": project.name}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/tasks")
async def create_task(task: TaskCreate):
    """Create a new task."""
    try:
        workflow = get_workflow()
        task_id = workflow.create_task(
            project_id=task.project_id,
            title=task.title,
            description=task.description,
            priority=task.priority,
            depends_on=task.depends_on,
            tags=task.tags
        )
        return {"task_id": task_id, "title": task.title}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.patch("/tasks/{task_id}/status")
async def update_task_status(task_id: int, update: TaskStatusUpdate):
    """Update task status."""
    try:
        workflow = get_workflow()
        # Validate status
        status = TaskStatus(update.status)
        workflow.update_task_status(task_id, status)
        return {"task_id": task_id, "status": status.value}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=f"Invalid status: {update.status}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/projects/{project_id}/tasks")
async def get_project_tasks(project_id: int):
    """Get all tasks for a project."""
    try:
        workflow = get_workflow()
        tasks = workflow.get_project_tasks(project_id)
        return {"project_id": project_id, "tasks": tasks, "count": len(tasks)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/tasks/blocked")
async def get_blocked_tasks():
    """Get all blocked tasks."""
    try:
        workflow = get_workflow()
        tasks = workflow.get_blocked_tasks()
        return {"tasks": tasks, "count": len(tasks)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/export/markdown")
async def export_markdown(project_id: Optional[int] = None):
    """Export workflow to Markdown.
    
    Args:
        project_id: Optional project ID (None = all projects)
    """
    try:
        workflow = get_workflow()
        markdown = workflow.export_to_markdown(project_id)
        return {"markdown": markdown}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
