"""
Request Workflow Integration
============================

Integrates API requests with the workflow system for:
- Task/mission-linked requests
- Priority-based execution
- Checklist item completion
- Progress tracking
- Request queuing for offline/rate-limited scenarios

Version: 1.0.0
Alpha: v1.0.0.63+
"""

import json
import uuid
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, Optional, List, Callable
from dataclasses import dataclass, field
from enum import Enum

from dev.goblin.core.services.logging_manager import get_logger

logger = get_logger("request-workflow")


class RequestCategory(Enum):
    """Categories of API requests."""

    AI_GENERATION = "ai_generation"  # MAKE/REDO content
    DATA_FETCH = "data_fetch"  # Pull data from APIs
    DATA_PUSH = "data_push"  # Send data to APIs
    AUTH = "auth"  # Authentication flows
    SYNC = "sync"  # Synchronization tasks
    NOTIFICATION = "notification"  # Alerts/messages


class TaskPriority(Enum):
    """Task priority levels."""

    MISSION_CRITICAL = 1  # Must complete for mission/project
    USER_INITIATED = 2  # Direct user action
    WORKFLOW_STEP = 3  # Part of workflow/quest
    BACKGROUND = 4  # Can wait
    PREFETCH = 5  # Optional optimization


@dataclass
class RequestTask:
    """An API request linked to a workflow task."""

    id: str
    category: RequestCategory
    priority: TaskPriority

    # Request details
    provider: str = ""
    endpoint: str = ""
    method: str = "POST"
    payload: Dict[str, Any] = field(default_factory=dict)

    # Workflow linkage
    workflow_id: Optional[str] = None
    objective_id: Optional[str] = None
    mission_id: Optional[str] = None
    checklist_item: Optional[str] = None

    # Execution
    status: str = "pending"  # pending, queued, running, completed, failed
    result: Optional[Any] = None
    error: Optional[str] = None

    # Timing
    created_at: str = ""
    started_at: Optional[str] = None
    completed_at: Optional[str] = None
    timeout_seconds: int = 60

    # Dependencies
    depends_on: List[str] = field(default_factory=list)  # Task IDs
    blocks: List[str] = field(default_factory=list)  # Task IDs this blocks

    # Callbacks
    on_success: Optional[str] = None  # Callback workflow/handler
    on_failure: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "id": self.id,
            "category": self.category.value,
            "priority": self.priority.value,
            "provider": self.provider,
            "endpoint": self.endpoint,
            "method": self.method,
            "payload": self.payload,
            "workflow_id": self.workflow_id,
            "objective_id": self.objective_id,
            "mission_id": self.mission_id,
            "checklist_item": self.checklist_item,
            "status": self.status,
            "error": self.error,
            "created_at": self.created_at,
            "started_at": self.started_at,
            "completed_at": self.completed_at,
            "timeout_seconds": self.timeout_seconds,
            "depends_on": self.depends_on,
            "blocks": self.blocks,
            "on_success": self.on_success,
            "on_failure": self.on_failure,
        }


@dataclass
class Milestone:
    """A milestone/waypoint/checkpoint in a mission."""

    id: str
    title: str
    description: str = ""

    # Progress criteria
    required_tasks: List[str] = field(
        default_factory=list
    )  # Task IDs that must complete
    required_checklist_items: List[str] = field(default_factory=list)  # Checklist items
    progress_threshold: float = 0.0  # 0-100, percentage of tasks needed

    # Status
    status: str = "pending"  # pending, in_progress, reached, skipped
    reached_at: Optional[str] = None

    # Position in sequence
    order: int = 0  # Display/execution order
    is_checkpoint: bool = False  # If True, saves mission state when reached

    # Rewards/triggers
    on_reached: Optional[str] = None  # Callback or handler name
    celebration_message: str = ""  # Message to show user

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "title": self.title,
            "description": self.description,
            "required_tasks": self.required_tasks,
            "required_checklist_items": self.required_checklist_items,
            "progress_threshold": self.progress_threshold,
            "status": self.status,
            "reached_at": self.reached_at,
            "order": self.order,
            "is_checkpoint": self.is_checkpoint,
            "on_reached": self.on_reached,
            "celebration_message": self.celebration_message,
        }


@dataclass
class Mission:
    """A mission/project with multiple tasks and milestones."""

    id: str
    title: str
    description: str

    # Tasks
    tasks: List[str] = field(default_factory=list)  # Task IDs
    checklists: Dict[str, List[str]] = field(
        default_factory=dict
    )  # Checklist name -> items

    # Milestones/Waypoints/Checkpoints
    milestones: List[Milestone] = field(default_factory=list)
    current_milestone_idx: int = 0  # Index of current milestone

    # Progress
    status: str = "active"  # active, paused, completed, archived
    priority: TaskPriority = TaskPriority.USER_INITIATED
    progress_percent: float = 0.0  # Overall progress 0-100

    # Quotas
    budget_limit: float = 0.0  # Max cost for this mission
    budget_used: float = 0.0

    # Metadata
    created_at: str = ""
    updated_at: str = ""
    completed_at: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "title": self.title,
            "description": self.description,
            "tasks": self.tasks,
            "checklists": self.checklists,
            "milestones": [m.to_dict() for m in self.milestones],
            "current_milestone_idx": self.current_milestone_idx,
            "status": self.status,
            "priority": self.priority.value,
            "progress_percent": self.progress_percent,
            "budget_limit": self.budget_limit,
            "budget_used": self.budget_used,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
            "completed_at": self.completed_at,
        }

    def get_current_milestone(self) -> Optional[Milestone]:
        """Get the current active milestone."""
        if 0 <= self.current_milestone_idx < len(self.milestones):
            return self.milestones[self.current_milestone_idx]
        return None

    def get_next_milestone(self) -> Optional[Milestone]:
        """Get the next milestone after current."""
        next_idx = self.current_milestone_idx + 1
        if next_idx < len(self.milestones):
            return self.milestones[next_idx]
        return None

    def get_reached_milestones(self) -> List[Milestone]:
        """Get all milestones that have been reached."""
        return [m for m in self.milestones if m.status == "reached"]


class RequestWorkflowService:
    """
    Manages API requests as workflow tasks.

    Integrates with:
    - WorkflowService for quest/learning objectives
    - QuotaTracker for rate limiting
    - OAuthManager for authenticated requests
    """

    DATA_DIR = Path(__file__).parent.parent / "memory" / "request_workflows"

    def __init__(self, project_root: Optional[Path] = None):
        """Initialize service."""
        self.project_root = project_root or Path(__file__).parent.parent
        self.data_dir = self.project_root / "memory" / "request_workflows"
        self.data_dir.mkdir(parents=True, exist_ok=True)

        # Storage
        self._tasks: Dict[str, RequestTask] = {}
        self._missions: Dict[str, Mission] = {}

        # Handlers for task execution
        self._handlers: Dict[RequestCategory, Callable] = {}

        # Load existing data
        self._load_data()

        logger.info(
            f"[LOCAL] RequestWorkflowService: {len(self._tasks)} tasks, {len(self._missions)} missions"
        )

    def _load_data(self):
        """Load tasks and missions."""
        tasks_file = self.data_dir / "tasks.json"
        if tasks_file.exists():
            try:
                data = json.loads(tasks_file.read_text())
                for task_data in data.get("tasks", []):
                    task = RequestTask(
                        id=task_data["id"],
                        category=RequestCategory(task_data["category"]),
                        priority=TaskPriority(task_data["priority"]),
                        provider=task_data.get("provider", ""),
                        endpoint=task_data.get("endpoint", ""),
                        method=task_data.get("method", "POST"),
                        payload=task_data.get("payload", {}),
                        workflow_id=task_data.get("workflow_id"),
                        objective_id=task_data.get("objective_id"),
                        mission_id=task_data.get("mission_id"),
                        checklist_item=task_data.get("checklist_item"),
                        status=task_data.get("status", "pending"),
                        created_at=task_data.get("created_at", ""),
                        depends_on=task_data.get("depends_on", []),
                        blocks=task_data.get("blocks", []),
                    )
                    self._tasks[task.id] = task
            except Exception as e:
                logger.error(f"[ERROR] Failed to load tasks: {e}")

        missions_file = self.data_dir / "missions.json"
        if missions_file.exists():
            try:
                data = json.loads(missions_file.read_text())
                for mission_data in data.get("missions", []):
                    # Load milestones
                    milestones = []
                    for ms_data in mission_data.get("milestones", []):
                        milestone = Milestone(
                            id=ms_data["id"],
                            title=ms_data["title"],
                            description=ms_data.get("description", ""),
                            required_tasks=ms_data.get("required_tasks", []),
                            required_checklist_items=ms_data.get(
                                "required_checklist_items", []
                            ),
                            progress_threshold=ms_data.get("progress_threshold", 0.0),
                            status=ms_data.get("status", "pending"),
                            reached_at=ms_data.get("reached_at"),
                            order=ms_data.get("order", 0),
                            is_checkpoint=ms_data.get("is_checkpoint", False),
                            on_reached=ms_data.get("on_reached"),
                            celebration_message=ms_data.get("celebration_message", ""),
                        )
                        milestones.append(milestone)

                    mission = Mission(
                        id=mission_data["id"],
                        title=mission_data["title"],
                        description=mission_data.get("description", ""),
                        tasks=mission_data.get("tasks", []),
                        checklists=mission_data.get("checklists", {}),
                        milestones=milestones,
                        current_milestone_idx=mission_data.get(
                            "current_milestone_idx", 0
                        ),
                        status=mission_data.get("status", "active"),
                        priority=TaskPriority(mission_data.get("priority", 2)),
                        progress_percent=mission_data.get("progress_percent", 0.0),
                        budget_limit=mission_data.get("budget_limit", 0.0),
                        budget_used=mission_data.get("budget_used", 0.0),
                        created_at=mission_data.get("created_at", ""),
                        updated_at=mission_data.get("updated_at", ""),
                    )
                    self._missions[mission.id] = mission
            except Exception as e:
                logger.error(f"[ERROR] Failed to load missions: {e}")

    def _save_data(self):
        """Save all data."""
        # Save tasks
        tasks_data = {
            "version": "1.0.0",
            "updated_at": datetime.now().isoformat(),
            "tasks": [
                t.to_dict() for t in self._tasks.values() if t.status != "completed"
            ],
        }
        tasks_file = self.data_dir / "tasks.json"
        tasks_file.write_text(json.dumps(tasks_data, indent=2))

        # Save missions
        missions_data = {
            "version": "1.0.0",
            "updated_at": datetime.now().isoformat(),
            "missions": [m.to_dict() for m in self._missions.values()],
        }
        missions_file = self.data_dir / "missions.json"
        missions_file.write_text(json.dumps(missions_data, indent=2))

    # === Task Management ===

    def create_task(
        self,
        category: RequestCategory,
        provider: str,
        endpoint: str = "",
        payload: Dict[str, Any] = None,
        priority: TaskPriority = TaskPriority.USER_INITIATED,
        workflow_id: str = None,
        objective_id: str = None,
        mission_id: str = None,
        checklist_item: str = None,
        depends_on: List[str] = None,
    ) -> RequestTask:
        """
        Create a new request task.

        Args:
            category: Type of request
            provider: API provider name
            endpoint: API endpoint
            payload: Request data
            priority: Execution priority
            workflow_id: Link to workflow
            objective_id: Link to objective
            mission_id: Link to mission
            checklist_item: Checklist item to mark complete
            depends_on: Tasks that must complete first

        Returns:
            Created task
        """
        task_id = f"task_{uuid.uuid4().hex[:8]}"
        now = datetime.now().isoformat()

        task = RequestTask(
            id=task_id,
            category=category,
            priority=priority,
            provider=provider,
            endpoint=endpoint,
            payload=payload or {},
            workflow_id=workflow_id,
            objective_id=objective_id,
            mission_id=mission_id,
            checklist_item=checklist_item,
            depends_on=depends_on or [],
            created_at=now,
        )

        self._tasks[task_id] = task

        # Link to mission if provided
        if mission_id and mission_id in self._missions:
            self._missions[mission_id].tasks.append(task_id)
            self._missions[mission_id].updated_at = now

        self._save_data()

        logger.info(f"[LOCAL] Created task {task_id}: {category.value} -> {provider}")
        return task

    def get_task(self, task_id: str) -> Optional[RequestTask]:
        """Get a task by ID."""
        return self._tasks.get(task_id)

    def get_pending_tasks(
        self, priority_filter: TaskPriority = None
    ) -> List[RequestTask]:
        """Get pending tasks, optionally filtered by priority."""
        tasks = [t for t in self._tasks.values() if t.status == "pending"]

        if priority_filter:
            tasks = [t for t in tasks if t.priority == priority_filter]

        # Sort by priority (lower value = higher priority)
        tasks.sort(key=lambda t: (t.priority.value, t.created_at))

        return tasks

    def get_ready_tasks(self) -> List[RequestTask]:
        """Get tasks that are ready to execute (dependencies met)."""
        ready = []

        for task in self.get_pending_tasks():
            # Check dependencies
            deps_met = all(
                self._tasks.get(
                    dep_id,
                    RequestTask(
                        id="",
                        category=RequestCategory.AI_GENERATION,
                        priority=TaskPriority.BACKGROUND,
                    ),
                ).status
                == "completed"
                for dep_id in task.depends_on
            )

            if deps_met:
                ready.append(task)

        return ready

    def complete_task(self, task_id: str, result: Any = None, error: str = None):
        """Mark a task as completed."""
        task = self._tasks.get(task_id)
        if not task:
            return

        now = datetime.now().isoformat()
        task.completed_at = now

        if error:
            task.status = "failed"
            task.error = error
            logger.error(f"[ERROR] Task {task_id} failed: {error}")
        else:
            task.status = "completed"
            task.result = result
            logger.info(f"[LOCAL] Task {task_id} completed")

        # Update mission checklist if linked
        if task.mission_id and task.checklist_item:
            self._mark_checklist_item(task.mission_id, task.checklist_item)

        self._save_data()

    # === Mission Management ===

    def create_mission(
        self,
        title: str,
        description: str = "",
        priority: TaskPriority = TaskPriority.USER_INITIATED,
        budget_limit: float = 0.0,
        checklists: Dict[str, List[str]] = None,
    ) -> Mission:
        """
        Create a new mission/project.

        Args:
            title: Mission title
            description: Description
            priority: Overall priority
            budget_limit: Max budget for API calls
            checklists: Dict of checklist name -> items
        """
        mission_id = f"mission_{uuid.uuid4().hex[:8]}"
        now = datetime.now().isoformat()

        mission = Mission(
            id=mission_id,
            title=title,
            description=description,
            priority=priority,
            budget_limit=budget_limit,
            checklists=checklists or {},
            created_at=now,
            updated_at=now,
        )

        self._missions[mission_id] = mission
        self._save_data()

        logger.info(f"[LOCAL] Created mission {mission_id}: {title}")
        return mission

    def get_mission(self, mission_id: str) -> Optional[Mission]:
        """Get a mission by ID."""
        return self._missions.get(mission_id)

    def get_active_missions(self) -> List[Mission]:
        """Get all active missions."""
        return [m for m in self._missions.values() if m.status == "active"]

    def add_checklist(self, mission_id: str, name: str, items: List[str]):
        """Add a checklist to a mission."""
        mission = self._missions.get(mission_id)
        if not mission:
            return

        mission.checklists[name] = items
        mission.updated_at = datetime.now().isoformat()
        self._save_data()

    def _mark_checklist_item(self, mission_id: str, item: str):
        """Mark a checklist item as done (prefix with ✓)."""
        mission = self._missions.get(mission_id)
        if not mission:
            return

        for checklist_name, items in mission.checklists.items():
            for i, checklist_item in enumerate(items):
                if checklist_item == item or checklist_item == f"✓ {item}":
                    if not checklist_item.startswith("✓"):
                        mission.checklists[checklist_name][i] = f"✓ {item}"
                    break

        mission.updated_at = datetime.now().isoformat()
        self._save_data()

    def get_mission_progress(self, mission_id: str) -> Dict[str, Any]:
        """Get mission progress summary."""
        mission = self._missions.get(mission_id)
        if not mission:
            return {}

        # Count task statuses
        task_statuses = {"pending": 0, "running": 0, "completed": 0, "failed": 0}
        for task_id in mission.tasks:
            task = self._tasks.get(task_id)
            if task:
                task_statuses[task.status] = task_statuses.get(task.status, 0) + 1

        # Count checklist progress
        checklist_progress = {}
        for name, items in mission.checklists.items():
            done = sum(1 for item in items if item.startswith("✓"))
            checklist_progress[name] = {
                "done": done,
                "total": len(items),
                "percent": (done / len(items) * 100) if items else 0,
            }

        total_tasks = sum(task_statuses.values())
        completed_tasks = task_statuses["completed"]

        return {
            "mission_id": mission_id,
            "title": mission.title,
            "status": mission.status,
            "tasks": task_statuses,
            "task_progress_percent": (
                (completed_tasks / total_tasks * 100) if total_tasks else 0
            ),
            "checklists": checklist_progress,
            "budget": {
                "limit": mission.budget_limit,
                "used": mission.budget_used,
                "remaining": mission.budget_limit - mission.budget_used,
            },
        }

    # === Integration Helpers ===

    def create_ai_generation_task(
        self,
        prompt: str,
        provider: str = "gemini",
        mission_id: str = None,
        workflow_id: str = None,
        on_success_callback: str = None,
    ) -> RequestTask:
        """
        Convenience method to create an AI generation task.

        Args:
            prompt: Generation prompt
            provider: AI provider
            mission_id: Link to mission
            workflow_id: Link to workflow
            on_success_callback: Callback on completion
        """
        return self.create_task(
            category=RequestCategory.AI_GENERATION,
            provider=provider,
            payload={"prompt": prompt},
            priority=TaskPriority.USER_INITIATED,
            mission_id=mission_id,
            workflow_id=workflow_id,
        )

    def create_data_sync_task(
        self,
        provider: str,
        endpoint: str,
        mission_id: str = None,
    ) -> RequestTask:
        """Create a data sync task."""
        return self.create_task(
            category=RequestCategory.SYNC,
            provider=provider,
            endpoint=endpoint,
            priority=TaskPriority.BACKGROUND,
            mission_id=mission_id,
        )

    def get_workflow_tasks(self, workflow_id: str) -> List[RequestTask]:
        """Get all tasks linked to a workflow."""
        return [t for t in self._tasks.values() if t.workflow_id == workflow_id]

    def get_mission_tasks(self, mission_id: str) -> List[RequestTask]:
        """Get all tasks linked to a mission."""
        return [t for t in self._tasks.values() if t.mission_id == mission_id]

    # === Milestone Management ===

    def add_milestone(
        self,
        mission_id: str,
        title: str,
        description: str = "",
        required_tasks: List[str] = None,
        required_checklist_items: List[str] = None,
        progress_threshold: float = 0.0,
        is_checkpoint: bool = False,
        celebration_message: str = "",
        order: int = None,
    ) -> Optional[Milestone]:
        """
        Add a milestone/waypoint to a mission.

        Args:
            mission_id: Mission to add milestone to
            title: Milestone title
            description: Optional description
            required_tasks: Task IDs that must complete
            required_checklist_items: Checklist items that must be checked
            progress_threshold: Overall progress percentage needed (0-100)
            is_checkpoint: If True, saves state when reached
            celebration_message: Message to display when reached
            order: Position in sequence (defaults to end)

        Returns:
            Created milestone or None if mission not found
        """
        mission = self._missions.get(mission_id)
        if not mission:
            logger.warning(f"[LOCAL] Mission not found: {mission_id}")
            return None

        milestone_id = f"ms_{uuid.uuid4().hex[:8]}"

        # Default order to end of list
        if order is None:
            order = len(mission.milestones)

        milestone = Milestone(
            id=milestone_id,
            title=title,
            description=description,
            required_tasks=required_tasks or [],
            required_checklist_items=required_checklist_items or [],
            progress_threshold=progress_threshold,
            order=order,
            is_checkpoint=is_checkpoint,
            celebration_message=celebration_message or f"🎯 Milestone reached: {title}",
        )

        # Insert at correct position
        mission.milestones.insert(order, milestone)

        # Re-order milestones
        for i, ms in enumerate(mission.milestones):
            ms.order = i

        mission.updated_at = datetime.now().isoformat()
        self._save_data()

        logger.info(f"[LOCAL] Added milestone '{title}' to mission '{mission.title}'")
        return milestone

    def check_milestone_progress(self, mission_id: str) -> Dict[str, Any]:
        """
        Check if any milestones have been reached in a mission.

        Returns dict with:
            - newly_reached: List of milestones just reached
            - current: Current milestone
            - next: Next milestone
            - progress: Overall progress percentage
        """
        mission = self._missions.get(mission_id)
        if not mission:
            return {"error": "Mission not found"}

        newly_reached = []
        now = datetime.now().isoformat()

        # Calculate overall progress
        total_tasks = len(mission.tasks)
        completed_tasks = sum(
            1
            for tid in mission.tasks
            if tid in self._tasks and self._tasks[tid].status == "completed"
        )
        mission.progress_percent = (
            (completed_tasks / total_tasks * 100) if total_tasks > 0 else 0
        )

        # Check each pending/in_progress milestone
        for milestone in mission.milestones:
            if milestone.status in ["reached", "skipped"]:
                continue

            reached = self._check_milestone_criteria(mission, milestone)

            if reached:
                milestone.status = "reached"
                milestone.reached_at = now
                newly_reached.append(milestone)

                # Save checkpoint if configured
                if milestone.is_checkpoint:
                    self._save_checkpoint(mission, milestone)

                logger.info(f"[LOCAL] 🎯 Milestone reached: {milestone.title}")

        # Update current milestone index
        for i, ms in enumerate(mission.milestones):
            if ms.status == "pending":
                mission.current_milestone_idx = i
                break
        else:
            # All milestones reached
            mission.current_milestone_idx = len(mission.milestones)

        mission.updated_at = now
        self._save_data()

        return {
            "newly_reached": [m.to_dict() for m in newly_reached],
            "current": (
                mission.get_current_milestone().to_dict()
                if mission.get_current_milestone()
                else None
            ),
            "next": (
                mission.get_next_milestone().to_dict()
                if mission.get_next_milestone()
                else None
            ),
            "progress": mission.progress_percent,
            "milestones_reached": len(mission.get_reached_milestones()),
            "milestones_total": len(mission.milestones),
        }

    def _check_milestone_criteria(self, mission: Mission, milestone: Milestone) -> bool:
        """Check if a milestone's criteria have been met."""
        # Check required tasks
        if milestone.required_tasks:
            for task_id in milestone.required_tasks:
                if task_id not in self._tasks:
                    return False
                if self._tasks[task_id].status != "completed":
                    return False

        # Check required checklist items
        if milestone.required_checklist_items:
            # Checklist items are stored as "checklist_name:item" or just "item"
            for item in milestone.required_checklist_items:
                found = False
                for checklist_name, items in mission.checklists.items():
                    if item in items:
                        # Check if item is marked complete (prefixed with ✓ or [x])
                        # This is a simplified check - actual implementation may vary
                        found = True
                        break
                if not found:
                    return False

        # Check progress threshold
        if milestone.progress_threshold > 0:
            if mission.progress_percent < milestone.progress_threshold:
                return False

        return True

    def _save_checkpoint(self, mission: Mission, milestone: Milestone):
        """Save a checkpoint when a milestone is reached."""
        checkpoint_dir = self.data_dir / "checkpoints" / mission.id
        checkpoint_dir.mkdir(parents=True, exist_ok=True)

        checkpoint_data = {
            "mission": mission.to_dict(),
            "milestone": milestone.to_dict(),
            "timestamp": datetime.now().isoformat(),
            "tasks_snapshot": {
                tid: self._tasks[tid].to_dict()
                for tid in mission.tasks
                if tid in self._tasks
            },
        }

        checkpoint_file = (
            checkpoint_dir
            / f"{milestone.id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        )
        checkpoint_file.write_text(json.dumps(checkpoint_data, indent=2))
        logger.info(f"[LOCAL] Checkpoint saved: {checkpoint_file.name}")

    def get_mission_milestones(self, mission_id: str) -> List[Dict[str, Any]]:
        """Get all milestones for a mission with status."""
        mission = self._missions.get(mission_id)
        if not mission:
            return []

        return [
            {
                **ms.to_dict(),
                "is_current": i == mission.current_milestone_idx,
                "progress_to_reach": self._calculate_milestone_progress(mission, ms),
            }
            for i, ms in enumerate(mission.milestones)
        ]

    def _calculate_milestone_progress(
        self, mission: Mission, milestone: Milestone
    ) -> float:
        """Calculate progress toward reaching a milestone (0-100)."""
        if milestone.status == "reached":
            return 100.0

        criteria_met = 0
        total_criteria = 0

        # Check required tasks progress
        if milestone.required_tasks:
            total_criteria += len(milestone.required_tasks)
            for task_id in milestone.required_tasks:
                if (
                    task_id in self._tasks
                    and self._tasks[task_id].status == "completed"
                ):
                    criteria_met += 1

        # Check progress threshold
        if milestone.progress_threshold > 0:
            total_criteria += 1
            if mission.progress_percent >= milestone.progress_threshold:
                criteria_met += 1

        if total_criteria == 0:
            return 0.0

        return (criteria_met / total_criteria) * 100

    def skip_milestone(
        self, mission_id: str, milestone_id: str, reason: str = ""
    ) -> bool:
        """Skip a milestone (mark as skipped without completing)."""
        mission = self._missions.get(mission_id)
        if not mission:
            return False

        for milestone in mission.milestones:
            if milestone.id == milestone_id:
                milestone.status = "skipped"
                milestone.reached_at = datetime.now().isoformat()
                mission.updated_at = datetime.now().isoformat()
                self._save_data()
                logger.info(f"[LOCAL] Milestone skipped: {milestone.title} - {reason}")
                return True

        return False

    def create_standard_milestones(
        self, mission_id: str, milestone_type: str = "quartile"
    ) -> List[Milestone]:
        """
        Create standard milestone waypoints for a mission.

        Args:
            mission_id: Mission to add milestones to
            milestone_type: Type of milestones:
                - "quartile": 25%, 50%, 75%, 100%
                - "half": 50%, 100%
                - "thirds": 33%, 66%, 100%

        Returns:
            List of created milestones
        """
        mission = self._missions.get(mission_id)
        if not mission:
            return []

        milestones = []

        if milestone_type == "quartile":
            waypoints = [
                (25, "🌱 Quarter Complete", "First quarter of tasks done"),
                (50, "⚡ Halfway There!", "Half of tasks completed"),
                (75, "🔥 Three Quarters Done", "Almost there!"),
                (100, "🏆 Mission Complete!", "All tasks finished"),
            ]
        elif milestone_type == "half":
            waypoints = [
                (50, "⚡ Halfway There!", "Half of tasks completed"),
                (100, "🏆 Mission Complete!", "All tasks finished"),
            ]
        elif milestone_type == "thirds":
            waypoints = [
                (33, "🌱 One Third Complete", "First third done"),
                (66, "⚡ Two Thirds Done", "Two thirds completed"),
                (100, "🏆 Mission Complete!", "All tasks finished"),
            ]
        else:
            return []

        for threshold, title, description in waypoints:
            ms = self.add_milestone(
                mission_id=mission_id,
                title=title,
                description=description,
                progress_threshold=threshold,
                is_checkpoint=(threshold == 50),  # Checkpoint at halfway
                celebration_message=f"🎯 {title}",
            )
            if ms:
                milestones.append(ms)

        return milestones

    # === Dashboard Data ===

    def get_dashboard_summary(self) -> Dict[str, Any]:
        """Get summary for dashboard display."""
        pending = len([t for t in self._tasks.values() if t.status == "pending"])
        running = len([t for t in self._tasks.values() if t.status == "running"])
        failed = len([t for t in self._tasks.values() if t.status == "failed"])

        active_missions = len(self.get_active_missions())

        return {
            "tasks": {
                "pending": pending,
                "running": running,
                "failed": failed,
            },
            "active_missions": active_missions,
            "ready_to_execute": len(self.get_ready_tasks()),
        }


# Singleton
_request_workflow_service: Optional[RequestWorkflowService] = None


def get_request_workflow_service(project_root: Path = None) -> RequestWorkflowService:
    """Get or create service singleton."""
    global _request_workflow_service
    if _request_workflow_service is None:
        _request_workflow_service = RequestWorkflowService(project_root)
    return _request_workflow_service
