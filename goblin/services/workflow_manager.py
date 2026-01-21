"""
Workflow Manager - uDOS Native Todo/Project System

Alternative to Notion for project/task management with:
- Todo lists with status tracking
- Project organization
- Dependencies and sequencing
- Integration with roadmap.md
- Local-first (SQLite)

Designed as alternative to external project management tools.
"""

from pathlib import Path
from typing import List, Dict, Optional, Any
from datetime import datetime
from enum import Enum
import sqlite3


class TaskStatus(Enum):
    """Task status enumeration."""
    NOT_STARTED = "not-started"
    IN_PROGRESS = "in-progress"
    COMPLETED = "completed"
    BLOCKED = "blocked"
    DEFERRED = "deferred"


class WorkflowManager:
    """Native workflow/todo manager for uDOS."""
    
    def __init__(self, db_path: str = "memory/goblin/workflow.db"):
        """Initialize workflow manager.
        
        Args:
            db_path: Path to SQLite database
        """
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._init_db()
    
    def _init_db(self):
        """Initialize database schema."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Projects table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS projects (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                description TEXT,
                status TEXT DEFAULT 'active',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Tasks table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS tasks (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                project_id INTEGER,
                title TEXT NOT NULL,
                description TEXT,
                status TEXT DEFAULT 'not-started',
                priority INTEGER DEFAULT 5,
                depends_on TEXT,
                file_refs TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                completed_at TIMESTAMP,
                FOREIGN KEY (project_id) REFERENCES projects(id)
            )
        """)
        
        # Tags table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS tags (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT UNIQUE NOT NULL
            )
        """)
        
        # Task tags junction
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS task_tags (
                task_id INTEGER,
                tag_id INTEGER,
                FOREIGN KEY (task_id) REFERENCES tasks(id),
                FOREIGN KEY (tag_id) REFERENCES tags(id),
                PRIMARY KEY (task_id, tag_id)
            )
        """)
        
        conn.commit()
        conn.close()
    
    def create_project(self, name: str, description: str = "") -> int:
        """Create a new project.
        
        Args:
            name: Project name
            description: Optional description
            
        Returns:
            Project ID
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute(
            "INSERT INTO projects (name, description) VALUES (?, ?)",
            (name, description)
        )
        
        project_id = cursor.lastrowid
        conn.commit()
        conn.close()
        
        return project_id
    
    def create_task(
        self,
        project_id: int,
        title: str,
        description: str = "",
        priority: int = 5,
        depends_on: Optional[List[int]] = None,
        tags: Optional[List[str]] = None
    ) -> int:
        """Create a new task.
        
        Args:
            project_id: Parent project ID
            title: Task title
            description: Optional description
            priority: Priority (1-10, 1=highest)
            depends_on: Optional list of task IDs this depends on
            tags: Optional list of tags
            
        Returns:
            Task ID
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        depends_str = ",".join(map(str, depends_on)) if depends_on else None
        
        cursor.execute(
            """INSERT INTO tasks 
               (project_id, title, description, priority, depends_on)
               VALUES (?, ?, ?, ?, ?)""",
            (project_id, title, description, priority, depends_str)
        )
        
        task_id = cursor.lastrowid
        
        # Add tags
        if tags:
            for tag_name in tags:
                # Insert or get tag ID
                cursor.execute(
                    "INSERT OR IGNORE INTO tags (name) VALUES (?)",
                    (tag_name,)
                )
                cursor.execute("SELECT id FROM tags WHERE name = ?", (tag_name,))
                tag_id = cursor.fetchone()[0]
                
                # Link task to tag
                cursor.execute(
                    "INSERT INTO task_tags (task_id, tag_id) VALUES (?, ?)",
                    (task_id, tag_id)
                )
        
        conn.commit()
        conn.close()
        
        return task_id
    
    def update_task_status(self, task_id: int, status: TaskStatus):
        """Update task status.
        
        Args:
            task_id: Task ID
            status: New status
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        completed_at = datetime.now() if status == TaskStatus.COMPLETED else None
        
        cursor.execute(
            """UPDATE tasks 
               SET status = ?, 
                   updated_at = CURRENT_TIMESTAMP,
                   completed_at = ?
               WHERE id = ?""",
            (status.value, completed_at, task_id)
        )
        
        conn.commit()
        conn.close()
    
    def get_project_tasks(self, project_id: int) -> List[Dict[str, Any]]:
        """Get all tasks for a project.
        
        Args:
            project_id: Project ID
            
        Returns:
            List of tasks
        """
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        cursor.execute(
            """SELECT t.*, GROUP_CONCAT(tg.name) as tags
               FROM tasks t
               LEFT JOIN task_tags tt ON t.id = tt.task_id
               LEFT JOIN tags tg ON tt.tag_id = tg.id
               WHERE t.project_id = ?
               GROUP BY t.id
               ORDER BY t.priority, t.created_at""",
            (project_id,)
        )
        
        tasks = [dict(row) for row in cursor.fetchall()]
        conn.close()
        
        return tasks
    
    def get_blocked_tasks(self) -> List[Dict[str, Any]]:
        """Get all blocked tasks.
        
        Returns:
            List of blocked tasks
        """
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        cursor.execute(
            """SELECT * FROM tasks 
               WHERE status = 'blocked'
               ORDER BY priority"""
        )
        
        tasks = [dict(row) for row in cursor.fetchall()]
        conn.close()
        
        return tasks
    
    def export_to_markdown(self, project_id: Optional[int] = None) -> str:
        """Export tasks to Markdown format.
        
        Args:
            project_id: Optional project ID (None = all projects)
            
        Returns:
            Markdown string
        """
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        if project_id:
            cursor.execute("SELECT * FROM projects WHERE id = ?", (project_id,))
            projects = [dict(cursor.fetchone())]
        else:
            cursor.execute("SELECT * FROM projects WHERE status = 'active'")
            projects = [dict(row) for row in cursor.fetchall()]
        
        md = "# uDOS Workflow\n\n"
        md += f"_Generated: {datetime.now().strftime('%Y-%m-%d %H:%M')}_\n\n"
        
        for project in projects:
            md += f"## {project['name']}\n\n"
            if project['description']:
                md += f"{project['description']}\n\n"
            
            tasks = self.get_project_tasks(project['id'])
            
            for task in tasks:
                checkbox = "x" if task['status'] == TaskStatus.COMPLETED.value else " "
                md += f"- [{checkbox}] **{task['title']}** "
                md += f"(Priority: {task['priority']}, Status: {task['status']})\n"
                
                if task['description']:
                    md += f"  - {task['description']}\n"
                
                if task['tags']:
                    md += f"  - Tags: {task['tags']}\n"
                
                md += "\n"
        
        conn.close()
        return md
