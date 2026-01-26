"""
Workflow & Quest Service
========================

Manages learning paths and roleplay/fantasy progression:
1. Real-world learning workflows (Surface layer)
2. Fantasy quest progression (Dungeon, Space layers)
3. Horror survival scenarios (Upside Down)

Ties together:
- Template system (layer theming)
- AI generation (dynamic content)
- Knowledge bank (source material)
- Map system (layer navigation)

Version: 1.0.0
Alpha: v1.0.0.62+
"""

import json
import uuid
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, Optional, List
from dataclasses import dataclass, field, asdict
from enum import Enum, auto

from dev.goblin.core.services.logging_manager import get_logger
from dev.goblin.core.services.template_loader import (
    get_template_loader,
    LayerTheme,
    layer_to_theme,
)

logger = get_logger("workflow-quest")


class WorkflowType(Enum):
    """Types of workflow/quest."""

    LEARNING = "learning"  # Real-world skill acquisition
    EXPLORATION = "exploration"  # Knowledge discovery
    QUEST = "quest"  # Fantasy quest chain
    SURVIVAL = "survival"  # Horror/survival scenario
    CHALLENGE = "challenge"  # Timed/scored task


class QuestStatus(Enum):
    """Quest/workflow status."""

    NOT_STARTED = "not_started"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    ABANDONED = "abandoned"


class ObjectiveType(Enum):
    """Types of objectives within a quest."""

    LEARN = "learn"  # Read/study content
    PRACTICE = "practice"  # Apply knowledge
    CREATE = "create"  # Make something
    DISCOVER = "discover"  # Find/explore
    SURVIVE = "survive"  # Endure scenario
    COLLECT = "collect"  # Gather items/knowledge


@dataclass
class Objective:
    """A single objective within a workflow/quest."""

    id: str
    title: str
    description: str
    obj_type: ObjectiveType
    status: QuestStatus = QuestStatus.NOT_STARTED

    # Optional requirements
    knowledge_file: Optional[str] = None  # Path to knowledge content
    skill_name: Optional[str] = None  # Skill to practice
    target_count: int = 1  # How many times to complete
    current_count: int = 0

    # Rewards
    xp_reward: int = 10
    unlocks: List[str] = field(default_factory=list)  # IDs of unlocked content

    # Metadata
    layer_id: int = 0
    created_at: str = ""
    completed_at: Optional[str] = None


@dataclass
class Workflow:
    """A workflow or quest with multiple objectives."""

    id: str
    title: str
    description: str
    workflow_type: WorkflowType
    status: QuestStatus = QuestStatus.NOT_STARTED

    # Layer theming
    layer_id: int = 0
    layer_theme: Optional[LayerTheme] = None

    # Objectives
    objectives: List[Objective] = field(default_factory=list)

    # Progress
    xp_total: int = 0
    xp_earned: int = 0
    time_limit_minutes: Optional[int] = None

    # Prerequisites
    prerequisites: List[str] = field(default_factory=list)  # Workflow IDs
    required_layer: Optional[int] = None

    # Metadata
    created_at: str = ""
    started_at: Optional[str] = None
    completed_at: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        data = asdict(self)
        # Convert enums to strings
        data["workflow_type"] = self.workflow_type.value
        data["status"] = self.status.value
        data["layer_theme"] = self.layer_theme.value if self.layer_theme else None
        data["objectives"] = [
            {**asdict(obj), "obj_type": obj.obj_type.value, "status": obj.status.value}
            for obj in self.objectives
        ]
        return data

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Workflow":
        """Create from dictionary."""
        # Convert strings back to enums
        data["workflow_type"] = WorkflowType(data["workflow_type"])
        data["status"] = QuestStatus(data["status"])
        data["layer_theme"] = (
            LayerTheme(data["layer_theme"]) if data.get("layer_theme") else None
        )
        data["objectives"] = [
            Objective(
                **{
                    **obj,
                    "obj_type": ObjectiveType(obj["obj_type"]),
                    "status": QuestStatus(obj["status"]),
                }
            )
            for obj in data.get("objectives", [])
        ]
        return cls(**data)


@dataclass
class UserProgress:
    """User's overall progress across workflows."""

    user_id: str = "default"
    total_xp: int = 0
    level: int = 1

    # Completed workflows by type
    completed_learning: List[str] = field(default_factory=list)
    completed_quests: List[str] = field(default_factory=list)
    completed_challenges: List[str] = field(default_factory=list)

    # Active workflows
    active_workflows: List[str] = field(default_factory=list)

    # Unlocked content
    unlocked_layers: List[int] = field(
        default_factory=lambda: [0]
    )  # Start with surface
    unlocked_skills: List[str] = field(default_factory=list)

    # Statistics
    knowledge_files_read: int = 0
    time_spent_minutes: int = 0

    def level_up_check(self) -> bool:
        """Check and apply level up."""
        xp_per_level = 100 * self.level  # Scaling XP requirement
        if self.total_xp >= xp_per_level:
            self.level += 1
            return True
        return False


class WorkflowService:
    """
    Manages workflows and quests for learning and roleplay.
    """

    STORAGE_PATH = Path(__file__).parent.parent.parent / "memory" / "workflows"

    def __init__(self, project_root: Optional[Path] = None):
        """Initialize workflow service."""
        self.project_root = project_root or Path(__file__).parent.parent.parent
        self.storage_path = self.project_root / "memory" / "workflows"
        self.storage_path.mkdir(parents=True, exist_ok=True)

        # Template loader for theming
        self._template_loader = get_template_loader()

        # Cache
        self._workflows: Dict[str, Workflow] = {}
        self._user_progress: Optional[UserProgress] = None

        # Load existing data
        self._load_all()

        logger.info(f"[LOCAL] WorkflowService: {len(self._workflows)} workflows loaded")

    def _load_all(self):
        """Load all workflows and user progress."""
        # Load workflows
        workflows_file = self.storage_path / "workflows.json"
        if workflows_file.exists():
            try:
                data = json.loads(workflows_file.read_text())
                for wf_data in data.get("workflows", []):
                    wf = Workflow.from_dict(wf_data)
                    self._workflows[wf.id] = wf
            except Exception as e:
                logger.error(f"[ERROR] Failed to load workflows: {e}")

        # Load user progress
        progress_file = self.storage_path / "progress.json"
        if progress_file.exists():
            try:
                data = json.loads(progress_file.read_text())
                self._user_progress = UserProgress(**data)
            except Exception:
                self._user_progress = UserProgress()
        else:
            self._user_progress = UserProgress()

    def _save_all(self):
        """Save all workflows and progress."""
        # Save workflows
        workflows_data = {
            "version": "1.0.0",
            "updated_at": datetime.now().isoformat(),
            "workflows": [wf.to_dict() for wf in self._workflows.values()],
        }
        (self.storage_path / "workflows.json").write_text(
            json.dumps(workflows_data, indent=2)
        )

        # Save progress
        (self.storage_path / "progress.json").write_text(
            json.dumps(asdict(self._user_progress), indent=2)
        )

    # === Workflow Creation ===

    def create_learning_workflow(
        self,
        title: str,
        topic: str,
        knowledge_files: List[str] = None,
        layer_id: int = 0,
    ) -> Workflow:
        """
        Create a learning workflow for real-world skill acquisition.

        Args:
            title: Workflow title
            topic: Main topic/skill to learn
            knowledge_files: Optional list of knowledge files to study
            layer_id: Layer for theming (usually 0 for surface/real-world)
        """
        workflow_id = f"learn_{uuid.uuid4().hex[:8]}"
        now = datetime.now().isoformat()

        objectives = []

        # Reading objectives
        if knowledge_files:
            for i, kf in enumerate(knowledge_files):
                objectives.append(
                    Objective(
                        id=f"{workflow_id}_read_{i}",
                        title=f"Study: {Path(kf).stem}",
                        description=f"Read and understand {kf}",
                        obj_type=ObjectiveType.LEARN,
                        knowledge_file=kf,
                        xp_reward=20,
                        layer_id=layer_id,
                        created_at=now,
                    )
                )

        # Practice objective
        objectives.append(
            Objective(
                id=f"{workflow_id}_practice",
                title=f"Practice: {topic}",
                description=f"Apply what you learned about {topic}",
                obj_type=ObjectiveType.PRACTICE,
                skill_name=topic,
                target_count=3,
                xp_reward=50,
                layer_id=layer_id,
                created_at=now,
            )
        )

        workflow = Workflow(
            id=workflow_id,
            title=title,
            description=f"Learning path for {topic}",
            workflow_type=WorkflowType.LEARNING,
            layer_id=layer_id,
            layer_theme=layer_to_theme(layer_id),
            objectives=objectives,
            xp_total=sum(o.xp_reward for o in objectives),
            created_at=now,
        )

        self._workflows[workflow_id] = workflow
        self._save_all()

        logger.info(f"[LOCAL] Created learning workflow: {workflow_id}")
        return workflow

    def create_quest(
        self,
        title: str,
        description: str,
        layer_id: int = -1,
        objectives_data: List[Dict[str, Any]] = None,
    ) -> Workflow:
        """
        Create a fantasy quest for roleplay/gamification.

        Args:
            title: Quest title
            description: Quest narrative
            layer_id: Layer (usually negative for dungeon/fantasy)
            objectives_data: List of objective definitions
        """
        workflow_id = f"quest_{uuid.uuid4().hex[:8]}"
        now = datetime.now().isoformat()

        objectives = []
        if objectives_data:
            for i, obj_data in enumerate(objectives_data):
                objectives.append(
                    Objective(
                        id=f"{workflow_id}_obj_{i}",
                        title=obj_data.get("title", f"Objective {i+1}"),
                        description=obj_data.get("description", ""),
                        obj_type=ObjectiveType(obj_data.get("type", "discover")),
                        xp_reward=obj_data.get("xp", 25),
                        target_count=obj_data.get("count", 1),
                        unlocks=obj_data.get("unlocks", []),
                        layer_id=layer_id,
                        created_at=now,
                    )
                )

        workflow = Workflow(
            id=workflow_id,
            title=title,
            description=description,
            workflow_type=WorkflowType.QUEST,
            layer_id=layer_id,
            layer_theme=layer_to_theme(layer_id),
            objectives=objectives,
            xp_total=sum(o.xp_reward for o in objectives),
            created_at=now,
        )

        self._workflows[workflow_id] = workflow
        self._save_all()

        logger.info(f"[LOCAL] Created quest: {workflow_id}")
        return workflow

    def create_survival_scenario(
        self,
        title: str,
        description: str,
        layer_id: int = -50,  # Upside Down depth
        time_limit_minutes: int = None,
    ) -> Workflow:
        """
        Create a survival scenario (Upside Down themed).

        Args:
            title: Scenario title
            description: Scenario narrative
            layer_id: Layer (usually -11 to -100 for Upside Down)
            time_limit_minutes: Optional time pressure
        """
        workflow_id = f"survive_{uuid.uuid4().hex[:8]}"
        now = datetime.now().isoformat()

        # Survival scenarios have specific objectives
        objectives = [
            Objective(
                id=f"{workflow_id}_assess",
                title="Assess Situation",
                description="Identify immediate threats and resources",
                obj_type=ObjectiveType.SURVIVE,
                xp_reward=15,
                layer_id=layer_id,
                created_at=now,
            ),
            Objective(
                id=f"{workflow_id}_secure",
                title="Secure Area",
                description="Make your immediate area safe",
                obj_type=ObjectiveType.SURVIVE,
                xp_reward=25,
                layer_id=layer_id,
                created_at=now,
            ),
            Objective(
                id=f"{workflow_id}_escape",
                title="Find Escape Route",
                description="Locate path to safety",
                obj_type=ObjectiveType.DISCOVER,
                xp_reward=40,
                layer_id=layer_id,
                created_at=now,
            ),
        ]

        workflow = Workflow(
            id=workflow_id,
            title=title,
            description=description,
            workflow_type=WorkflowType.SURVIVAL,
            layer_id=layer_id,
            layer_theme=LayerTheme.UPSIDE_DOWN,
            objectives=objectives,
            xp_total=sum(o.xp_reward for o in objectives),
            time_limit_minutes=time_limit_minutes,
            created_at=now,
        )

        self._workflows[workflow_id] = workflow
        self._save_all()

        logger.info(f"[LOCAL] Created survival scenario: {workflow_id}")
        return workflow

    # === Progress Tracking ===

    def start_workflow(self, workflow_id: str) -> Optional[Workflow]:
        """Start a workflow."""
        if workflow_id not in self._workflows:
            return None

        workflow = self._workflows[workflow_id]
        if workflow.status != QuestStatus.NOT_STARTED:
            return workflow

        workflow.status = QuestStatus.IN_PROGRESS
        workflow.started_at = datetime.now().isoformat()

        # Add to active list
        if workflow_id not in self._user_progress.active_workflows:
            self._user_progress.active_workflows.append(workflow_id)

        self._save_all()
        logger.info(f"[LOCAL] Started workflow: {workflow_id}")
        return workflow

    def complete_objective(
        self, workflow_id: str, objective_id: str
    ) -> Optional[Objective]:
        """Mark an objective as complete."""
        if workflow_id not in self._workflows:
            return None

        workflow = self._workflows[workflow_id]
        objective = next((o for o in workflow.objectives if o.id == objective_id), None)

        if not objective:
            return None

        objective.current_count += 1
        if objective.current_count >= objective.target_count:
            objective.status = QuestStatus.COMPLETED
            objective.completed_at = datetime.now().isoformat()

            # Award XP
            workflow.xp_earned += objective.xp_reward
            self._user_progress.total_xp += objective.xp_reward

            # Check for level up
            if self._user_progress.level_up_check():
                logger.info(f"[LOCAL] Level up! Now level {self._user_progress.level}")

            # Process unlocks
            for unlock in objective.unlocks:
                if unlock.startswith("layer:"):
                    layer_id = int(unlock.split(":")[1])
                    if layer_id not in self._user_progress.unlocked_layers:
                        self._user_progress.unlocked_layers.append(layer_id)
                elif unlock.startswith("skill:"):
                    skill = unlock.split(":")[1]
                    if skill not in self._user_progress.unlocked_skills:
                        self._user_progress.unlocked_skills.append(skill)

        # Check if workflow is complete
        if all(o.status == QuestStatus.COMPLETED for o in workflow.objectives):
            workflow.status = QuestStatus.COMPLETED
            workflow.completed_at = datetime.now().isoformat()

            # Update progress
            if workflow_id in self._user_progress.active_workflows:
                self._user_progress.active_workflows.remove(workflow_id)

            if workflow.workflow_type == WorkflowType.LEARNING:
                self._user_progress.completed_learning.append(workflow_id)
            elif workflow.workflow_type == WorkflowType.QUEST:
                self._user_progress.completed_quests.append(workflow_id)
            elif workflow.workflow_type == WorkflowType.CHALLENGE:
                self._user_progress.completed_challenges.append(workflow_id)

            logger.info(f"[LOCAL] Workflow completed: {workflow_id}")

        self._save_all()
        return objective

    # === Queries ===

    def get_workflow(self, workflow_id: str) -> Optional[Workflow]:
        """Get workflow by ID."""
        return self._workflows.get(workflow_id)

    def get_active_workflows(self) -> List[Workflow]:
        """Get all active workflows."""
        return [
            self._workflows[wf_id]
            for wf_id in self._user_progress.active_workflows
            if wf_id in self._workflows
        ]

    def get_available_for_layer(self, layer_id: int) -> List[Workflow]:
        """Get workflows available for a specific layer."""
        theme = layer_to_theme(layer_id)
        return [
            wf
            for wf in self._workflows.values()
            if wf.layer_theme == theme and wf.status == QuestStatus.NOT_STARTED
        ]

    def get_progress(self) -> UserProgress:
        """Get user progress."""
        return self._user_progress

    def get_themed_summary(self, layer_id: int = 0) -> str:
        """Get progress summary themed for layer."""
        template = self._template_loader.get_for_layer(layer_id)
        progress = self._user_progress

        theme = layer_to_theme(layer_id)

        if theme == LayerTheme.SURFACE:
            return f"""📊 Learning Progress
Level: {progress.level} | XP: {progress.total_xp}
Completed Paths: {len(progress.completed_learning)}
Active: {len(progress.active_workflows)}
Knowledge Files Read: {progress.knowledge_files_read}"""

        elif theme == LayerTheme.DUNGEON:
            return f"""⚔️ Adventurer Status
Level: {progress.level} | XP: {progress.total_xp}
Quests Completed: {len(progress.completed_quests)}
Active Quests: {len(progress.active_workflows)}
Layers Unlocked: {len(progress.unlocked_layers)}"""

        elif theme == LayerTheme.UPSIDE_DOWN:
            return f"""🔻 Survivor Status
Stability: {100 - progress.level * 5}%
Breaches Survived: {len(progress.completed_quests)}
Active Threats: {len(progress.active_workflows)}
Safe Zones: {len(progress.unlocked_layers)}"""

        elif theme == LayerTheme.SPACE_HUMOR:
            return f"""🌌 Hitchhiker Status
Mostly Harmless Level: {progress.level}
Improbability Score: {progress.total_xp}
Completed Entries: {len(progress.completed_learning)}
Towel Status: {'Present' if progress.level > 0 else 'Missing'}"""

        else:  # SPACE_SERIOUS
            return f"""📚 Foundation Record
Rank: {progress.level} | Contribution: {progress.total_xp}
Encyclopedia Entries: {len(progress.completed_learning)}
Active Research: {len(progress.active_workflows)}
Archive Access: Layer {max(progress.unlocked_layers)}"""


# Singleton
_workflow_service: Optional[WorkflowService] = None


def get_workflow_service() -> WorkflowService:
    """Get or create workflow service singleton."""
    global _workflow_service
    if _workflow_service is None:
        _workflow_service = WorkflowService()
    return _workflow_service


# Convenience functions
def create_learning_path(title: str, topic: str, **kwargs) -> Workflow:
    """Create a learning workflow."""
    return get_workflow_service().create_learning_workflow(title, topic, **kwargs)


def create_quest(title: str, description: str, **kwargs) -> Workflow:
    """Create a fantasy quest."""
    return get_workflow_service().create_quest(title, description, **kwargs)


def get_progress_summary(layer_id: int = 0) -> str:
    """Get themed progress summary."""
    return get_workflow_service().get_themed_summary(layer_id)
