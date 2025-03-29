"""
Task Manager Module

This module provides a simple task manager for handling task data.
"""

import json
import os
import uuid
from datetime import datetime
from enum import Enum
from typing import Dict, List, Any, Optional


class TaskStatus(str, Enum):
    """Task status enum."""
    PLANNED = "planned"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    BLOCKED = "blocked"


class TaskPriority(str, Enum):
    """Task priority enum."""
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


class Phase:
    """Phase class representing a project phase."""
    
    def __init__(
        self,
        id: str,
        project_id: str,
        name: str,
        description: str,
        order: int,
        created_at: Optional[datetime] = None,
        updated_at: Optional[datetime] = None
    ):
        """
        Initialize a Phase.
        
        Args:
            id: Phase ID
            project_id: Project ID
            name: Phase name
            description: Phase description
            order: Phase order
            created_at: Creation timestamp
            updated_at: Update timestamp
        """
        self.id = id
        self.project_id = project_id
        self.name = name
        self.description = description
        self.order = order
        self.created_at = created_at or datetime.now()
        self.updated_at = updated_at or datetime.now()
    
    def to_dict(self) -> Dict[str, Any]:
        """
        Convert Phase to dictionary.
        
        Returns:
            Dictionary representation of Phase
        """
        return {
            "id": self.id,
            "project_id": self.project_id,
            "name": self.name,
            "description": self.description,
            "order": self.order,
            "created_at": self.created_at.isoformat() if isinstance(self.created_at, datetime) else self.created_at,
            "updated_at": self.updated_at.isoformat() if isinstance(self.updated_at, datetime) else self.updated_at
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Phase':
        """
        Create Phase from dictionary.
        
        Args:
            data: Dictionary representation of Phase
        
        Returns:
            Phase instance
        """
        created_at = data.get("created_at")
        if created_at and isinstance(created_at, str):
            created_at = datetime.fromisoformat(created_at)
        
        updated_at = data.get("updated_at")
        if updated_at and isinstance(updated_at, str):
            updated_at = datetime.fromisoformat(updated_at)
        
        return cls(
            id=data["id"],
            project_id=data["project_id"],
            name=data["name"],
            description=data["description"],
            order=data["order"],
            created_at=created_at,
            updated_at=updated_at
        )


class Task:
    """Task class representing a task."""
    
    def __init__(
        self,
        id: str,
        project_id: str,
        name: str,
        description: str,
        status: str,
        phase_id: Optional[str] = None,
        parent_id: Optional[str] = None,
        priority: Optional[str] = None,
        progress: Optional[float] = None,
        assignee_id: Optional[str] = None,
        assignee_type: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
        result: Optional[Dict[str, Any]] = None,
        error: Optional[Dict[str, Any]] = None,
        created_at: Optional[datetime] = None,
        updated_at: Optional[datetime] = None
    ):
        """
        Initialize a Task.
        
        Args:
            id: Task ID
            project_id: Project ID
            name: Task name
            description: Task description
            status: Task status
            phase_id: Phase ID
            parent_id: Parent task ID
            priority: Task priority
            progress: Task progress
            assignee_id: Assignee ID
            assignee_type: Assignee type
            metadata: Task metadata
            result: Task result
            error: Task error
            created_at: Creation timestamp
            updated_at: Update timestamp
        """
        self.id = id
        self.project_id = project_id
        self.name = name
        self.description = description
        self.status = status
        self.phase_id = phase_id
        self.parent_id = parent_id
        self.priority = priority
        self.progress = progress
        self.assignee_id = assignee_id
        self.assignee_type = assignee_type
        self.metadata = metadata or {}
        self.result = result
        self.error = error
        self.created_at = created_at or datetime.now()
        self.updated_at = updated_at or datetime.now()
    
    def to_dict(self) -> Dict[str, Any]:
        """
        Convert Task to dictionary.
        
        Returns:
            Dictionary representation of Task
        """
        return {
            "id": self.id,
            "project_id": self.project_id,
            "name": self.name,
            "description": self.description,
            "status": self.status,
            "phase_id": self.phase_id,
            "parent_id": self.parent_id,
            "priority": self.priority,
            "progress": self.progress,
            "assignee_id": self.assignee_id,
            "assignee_type": self.assignee_type,
            "metadata": self.metadata,
            "result": self.result,
            "error": self.error,
            "created_at": self.created_at.isoformat() if isinstance(self.created_at, datetime) else self.created_at,
            "updated_at": self.updated_at.isoformat() if isinstance(self.updated_at, datetime) else self.updated_at
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Task':
        """
        Create Task from dictionary.
        
        Args:
            data: Dictionary representation of Task
        
        Returns:
            Task instance
        """
        created_at = data.get("created_at")
        if created_at and isinstance(created_at, str):
            created_at = datetime.fromisoformat(created_at)
        
        updated_at = data.get("updated_at")
        if updated_at and isinstance(updated_at, str):
            updated_at = datetime.fromisoformat(updated_at)
        
        return cls(
            id=data["id"],
            project_id=data["project_id"],
            name=data["name"],
            description=data["description"],
            status=data["status"],
            phase_id=data.get("phase_id"),
            parent_id=data.get("parent_id"),
            priority=data.get("priority"),
            progress=data.get("progress"),
            assignee_id=data.get("assignee_id"),
            assignee_type=data.get("assignee_type"),
            metadata=data.get("metadata", {}),
            result=data.get("result"),
            error=data.get("error"),
            created_at=created_at,
            updated_at=updated_at
        )


class Project:
    """Project class representing a project."""
    
    def __init__(
        self,
        id: str,
        name: str,
        description: str,
        metadata: Optional[Dict[str, Any]] = None,
        created_at: Optional[datetime] = None,
        updated_at: Optional[datetime] = None
    ):
        """
        Initialize a Project.
        
        Args:
            id: Project ID
            name: Project name
            description: Project description
            metadata: Project metadata
            created_at: Creation timestamp
            updated_at: Update timestamp
        """
        self.id = id
        self.name = name
        self.description = description
        self.metadata = metadata or {}
        self.created_at = created_at or datetime.now()
        self.updated_at = updated_at or datetime.now()
        self.phases: Dict[str, Phase] = {}
        self.tasks: Dict[str, Task] = {}
    
    def to_dict(self) -> Dict[str, Any]:
        """
        Convert Project to dictionary.
        
        Returns:
            Dictionary representation of Project
        """
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "metadata": self.metadata,
            "created_at": self.created_at.isoformat() if isinstance(self.created_at, datetime) else self.created_at,
            "updated_at": self.updated_at.isoformat() if isinstance(self.updated_at, datetime) else self.updated_at
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Project':
        """
        Create Project from dictionary.
        
        Args:
            data: Dictionary representation of Project
        
        Returns:
            Project instance
        """
        created_at = data.get("created_at")
        if created_at and isinstance(created_at, str):
            created_at = datetime.fromisoformat(created_at)
        
        updated_at = data.get("updated_at")
        if updated_at and isinstance(updated_at, str):
            updated_at = datetime.fromisoformat(updated_at)
        
        return cls(
            id=data["id"],
            name=data["name"],
            description=data["description"],
            metadata=data.get("metadata", {}),
            created_at=created_at,
            updated_at=updated_at
        )


class TaskManager:
    """Task Manager class for managing tasks."""
    
    def __init__(self, data_path: str):
        """
        Initialize a TaskManager.
        
        Args:
            data_path: Path to task data
        """
        self.data_path = data_path
        self.projects: Dict[str, Project] = {}
        self.load_data()
    
    def load_data(self):
        """Load task data from file."""
        if not os.path.exists(self.data_path):
            os.makedirs(os.path.dirname(self.data_path), exist_ok=True)
            return
        
        try:
            with open(os.path.join(self.data_path, "tasks.json"), 'r') as f:
                data = json.load(f)
            
            # Load projects
            for project_data in data.get("projects", []):
                project = Project.from_dict(project_data)
                self.projects[project.id] = project
            
            # Load phases
            for phase_data in data.get("phases", []):
                phase = Phase.from_dict(phase_data)
                if phase.project_id in self.projects:
                    self.projects[phase.project_id].phases[phase.id] = phase
            
            # Load tasks
            for task_data in data.get("tasks", []):
                task = Task.from_dict(task_data)
                if task.project_id in self.projects:
                    self.projects[task.project_id].tasks[task.id] = task
        except Exception as e:
            print(f"Error loading task data: {e}")
    
    def save_data(self):
        """Save task data to file."""
        try:
            data = {
                "projects": [project.to_dict() for project in self.projects.values()],
                "phases": [],
                "tasks": []
            }
            
            for project in self.projects.values():
                data["phases"].extend([phase.to_dict() for phase in project.phases.values()])
                data["tasks"].extend([task.to_dict() for task in project.tasks.values()])
            
            os.makedirs(os.path.dirname(os.path.join(self.data_path, "tasks.json")), exist_ok=True)
            with open(os.path.join(self.data_path, "tasks.json"), 'w') as f:
                json.dump(data, f, indent=2)
        except Exception as e:
            print(f"Error saving task data: {e}")
    
    def create_project(
        self,
        name: str,
        description: str,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Project:
        """
        Create a new project.
        
        Args:
            name: Project name
            description: Project description
            metadata: Project metadata
        
        Returns:
            Created Project
        """
        project_id = f"project-{str(uuid.uuid4())}"
        project = Project(
            id=project_id,
            name=name,
            description=description,
            metadata=metadata
        )
        self.projects[project_id] = project
        return project
    
    def get_project(self, project_id: str) -> Optional[Project]:
        """
        Get a project by ID.
        
        Args:
            project_id: Project ID
        
        Returns:
            Project or None if not found
        """
        return self.projects.get(project_id)
    
    def update_project(
        self,
        project_id: str,
        name: Optional[str] = None,
        description: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Optional[Project]:
        """
        Update a project.
        
        Args:
            project_id: Project ID
            name: Project name
            description: Project description
            metadata: Project metadata
        
        Returns:
            Updated Project or None if not found
        """
        project = self.get_project(project_id)
        if not project:
            return None
        
        if name is not None:
            project.name = name
        
        if description is not None:
            project.description = description
        
        if metadata is not None:
            project.metadata = metadata
        
        project.updated_at = datetime.now()
        return project
    
    def delete_project(self, project_id: str) -> bool:
        """
        Delete a project.
        
        Args:
            project_id: Project ID
        
        Returns:
            True if project was deleted, False otherwise
        """
        if project_id in self.projects:
            del self.projects[project_id]
            return True
        return False
    
    def create_phase(
        self,
        project_id: str,
        name: str,
        description: str,
        order: int
    ) -> Optional[Phase]:
        """
        Create a new phase.
        
        Args:
            project_id: Project ID
            name: Phase name
            description: Phase description
            order: Phase order
        
        Returns:
            Created Phase or None if project not found
        """
        project = self.get_project(project_id)
        if not project:
            return None
        
        phase_id = f"phase-{str(uuid.uuid4())}"
        phase = Phase(
            id=phase_id,
            project_id=project_id,
            name=name,
            description=description,
            order=order
        )
        project.phases[phase_id] = phase
        return phase
    
    def get_phase(self, phase_id: str) -> Optional[Phase]:
        """
        Get a phase by ID.
        
        Args:
            phase_id: Phase ID
        
        Returns:
            Phase or None if not found
        """
        for project in self.projects.values():
            if phase_id in project.phases:
                return project.phases[phase_id]
        return None
    
    def update_phase(
        self,
        phase_id: str,
        name: Optional[str] = None,
        description: Optional[str] = None,
        order: Optional[int] = None
    ) -> Optional[Phase]:
        """
        Update a phase.
        
        Args:
            phase_id: Phase ID
            name: Phase name
            description: Phase description
            order: Phase order
        
        Returns:
            Updated Phase or None if not found
        """
        phase = self.get_phase(phase_id)
        if not phase:
            return None
        
        if name is not None:
            phase.name = name
        
        if description is not None:
            phase.description = description
        
        if order is not None:
            phase.order = order
        
        phase.updated_at = datetime.now()
        return phase
    
    def delete_phase(self, phase_id: str) -> bool:
        """
        Delete a phase.
        
        Args:
            phase_id: Phase ID
        
        Returns:
            True if phase was deleted, False otherwise
        """
        for project in self.projects.values():
            if phase_id in project.phases:
                del project.phases[phase_id]
                return True
        return False
    
    def create_task(
        self,
        name: str,
        description: str,
        project_id: str,
        status: str,
        phase_id: Optional[str] = None,
        parent_id: Optional[str] = None,
        priority: Optional[str] = None,
        progress: Optional[float] = None,
        assignee_id: Optional[str] = None,
        assignee_type: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
        result: Optional[Dict[str, Any]] = None,
        error: Optional[Dict[str, Any]] = None
    ) -> Optional[Task]:
        """
        Create a new task.
        
        Args:
            name: Task name
            description: Task description
            project_id: Project ID
            status: Task status
            phase_id: Phase ID
            parent_id: Parent task ID
            priority: Task priority
            progress: Task progress
            assignee_id: Assignee ID
            assignee_type: Assignee type
            metadata: Task metadata
            result: Task result
            error: Task error
        
        Returns:
            Created Task or None if project not found
        """
        project = self.get_project(project_id)
        if not project:
            return None
        
        task_id = f"task-{str(uuid.uuid4())}"
        task = Task(
            id=task_id,
            project_id=project_id,
            name=name,
            description=description,
            status=status,
            phase_id=phase_id,
            parent_id=parent_id,
            priority=priority,
            progress=progress,
            assignee_id=assignee_id,
            assignee_type=assignee_type,
            metadata=metadata,
            result=result,
            error=error
        )
        project.tasks[task_id] = task
        return task
    
    def get_task(self, task_id: str) -> Optional[Task]:
        """
        Get a task by ID.
        
        Args:
            task_id: Task ID
        
        Returns:
            Task or None if not found
        """
        for project in self.projects.values():
            if task_id in project.tasks:
                return project.tasks[task_id]
        return None
    
    def update_task(
        self,
        task_id: str,
        name: Optional[str] = None,
        description: Optional[str] = None,
        status: Optional[str] = None,
        phase_id: Optional[str] = None,
        parent_id: Optional[str] = None,
        priority: Optional[str] = None,
        progress: Optional[float] = None,
        assignee_id: Optional[str] = None,
        assignee_type: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
        result: Optional[Dict[str, Any]] = None,
        error: Optional[Dict[str, Any]] = None
    ) -> Optional[Task]:
        """
        Update a task.
        
        Args:
            task_id: Task ID
            name: Task name
            description: Task description
            status: Task status
            phase_id: Phase ID
            parent_id: Parent task ID
            priority: Task priority
            progress: Task progress
            assignee_id: Assignee ID
            assignee_type: Assignee type
            metadata: Task metadata
            result: Task result
            error: Task error
        
        Returns:
            Updated Task or None if not found
        """
        task = self.get_task(task_id)
        if not task:
            return None
        
        if name is not None:
            task.name = name
        
        if description is not None:
            task.description = description
        
        if status is not None:
            task.status = status
        
        if phase_id is not None:
            task.phase_id = phase_id
        
        if parent_id is not None:
            task.parent_id = parent_id
        
        if priority is not None:
            task.priority = priority
        
        if progress is not None:
            task.progress = progress
        
        if assignee_id is not None:
            task.assignee_id = assignee_id
        
        if assignee_type is not None:
            task.assignee_type = assignee_type
        
        if metadata is not None:
            task.metadata = metadata
        
        if result is not None:
            task.result = result
        
        if error is not None:
            task.error = error
        
        task.updated_at = datetime.now()
        return task
    
    def delete_task(self, task_id: str) -> bool:
        """
        Delete a task.
        
        Args:
            task_id: Task ID
        
        Returns:
            True if task was deleted, False otherwise
        """
        for project in self.projects.values():
            if task_id in project.tasks:
                del project.tasks[task_id]
                return True
        return False


def get_task_manager(data_path: str) -> TaskManager:
    """
    Get a TaskManager instance.
    
    Args:
        data_path: Path to task data
    
    Returns:
        TaskManager instance
    """
    return TaskManager(data_path)
