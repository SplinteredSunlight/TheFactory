"""
Mock Task Manager module for testing.

This module provides mock implementations of Task Manager classes and functions
for testing purposes.
"""

from enum import Enum
from typing import Dict, List, Optional, Any, Union
from datetime import datetime


class TaskStatus(str, Enum):
    """Task status enum."""
    PLANNED = "planned"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    BLOCKED = "blocked"


class TaskPriority(str, Enum):
    """Task priority enum."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class Task:
    """Mock Task class."""
    
    def __init__(self, id, name, description, project_id, phase_id=None, parent_id=None,
                 status=TaskStatus.PLANNED, priority=TaskPriority.MEDIUM, progress=0.0,
                 assignee_id=None, assignee_type=None, metadata=None, result=None, error=None):
        """Initialize a new Task."""
        self.id = id
        self.name = name
        self.description = description
        self.project_id = project_id
        self.phase_id = phase_id
        self.parent_id = parent_id
        self.status = status if isinstance(status, TaskStatus) else TaskStatus(status)
        self.priority = priority if isinstance(priority, TaskPriority) else TaskPriority(priority)
        self.progress = progress
        self.assignee_id = assignee_id
        self.assignee_type = assignee_type
        self.metadata = metadata or {}
        self.result = result
        self.error = error
        self.created_at = datetime.now()
        self.updated_at = datetime.now()
    
    def to_dict(self):
        """Convert the task to a dictionary."""
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "project_id": self.project_id,
            "phase_id": self.phase_id,
            "parent_id": self.parent_id,
            "status": self.status.value,
            "priority": self.priority.value,
            "progress": self.progress,
            "assignee_id": self.assignee_id,
            "assignee_type": self.assignee_type,
            "metadata": self.metadata,
            "result": self.result,
            "error": self.error,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
        }


class Phase:
    """Mock Phase class."""
    
    def __init__(self, id, name, description=None, order=0, metadata=None):
        """Initialize a new Phase."""
        self.id = id
        self.name = name
        self.description = description
        self.order = order
        self.metadata = metadata or {}
        self.tasks = []
    
    def to_dict(self):
        """Convert the phase to a dictionary."""
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "order": self.order,
            "metadata": self.metadata,
            "tasks": self.tasks,
        }


class Project:
    """Mock Project class."""
    
    def __init__(self, id, name, description=None, metadata=None):
        """Initialize a new Project."""
        self.id = id
        self.name = name
        self.description = description
        self.metadata = metadata or {}
        self.phases = {}
        self.tasks = {}
        self.created_at = datetime.now()
        self.updated_at = datetime.now()
    
    def add_phase(self, phase_id, name, description=None, order=0, metadata=None):
        """Add a phase to the project."""
        phase = Phase(phase_id, name, description, order, metadata)
        self.phases[phase_id] = phase
        return phase
    
    def to_dict(self):
        """Convert the project to a dictionary."""
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "metadata": self.metadata,
            "phases": {phase_id: phase.to_dict() for phase_id, phase in self.phases.items()},
            "tasks": {task_id: task.to_dict() for task_id, task in self.tasks.items()},
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
        }


class TaskManager:
    """Mock TaskManager class."""
    
    def __init__(self, data_dir=None):
        """Initialize a new TaskManager."""
        self.projects = {}
    
    def create_project(self, name, description=None, metadata=None):
        """Create a new project."""
        import uuid
        project_id = f"project_{uuid.uuid4().hex[:8]}"
        project = Project(project_id, name, description, metadata)
        self.projects[project_id] = project
        return project
    
    def get_project(self, project_id):
        """Get a project by ID."""
        return self.projects.get(project_id)
    
    def update_project(self, project_id, name=None, description=None, metadata=None):
        """Update a project."""
        project = self.get_project(project_id)
        if not project:
            return None
        
        if name is not None:
            project.name = name
        if description is not None:
            project.description = description
        if metadata is not None:
            project.metadata.update(metadata)
        
        project.updated_at = datetime.now()
        return project
    
    def delete_project(self, project_id):
        """Delete a project."""
        if project_id in self.projects:
            del self.projects[project_id]
            return True
        return False
    
    def create_task(self, name, description, project_id, phase_id=None, parent_id=None,
                    status="planned", priority="medium", progress=0.0,
                    assignee_id=None, assignee_type=None, metadata=None):
        """Create a new task."""
        project = self.get_project(project_id)
        if not project:
            return None
        
        import uuid
        task_id = f"task_{uuid.uuid4().hex[:8]}"
        
        task = Task(
            id=task_id,
            name=name,
            description=description,
            project_id=project_id,
            phase_id=phase_id,
            parent_id=parent_id,
            status=status,
            priority=priority,
            progress=progress,
            assignee_id=assignee_id,
            assignee_type=assignee_type,
            metadata=metadata,
        )
        
        project.tasks[task_id] = task
        
        if phase_id and phase_id in project.phases:
            project.phases[phase_id].tasks.append(task_id)
        
        return task
    
    def get_task(self, task_id):
        """Get a task by ID."""
        for project in self.projects.values():
            if task_id in project.tasks:
                return project.tasks[task_id]
        return None
    
    def update_task(self, task_id, name=None, description=None, phase_id=None, parent_id=None,
                    status=None, priority=None, progress=None, assignee_id=None, assignee_type=None,
                    metadata=None, result=None, error=None):
        """Update a task."""
        task = self.get_task(task_id)
        if not task:
            return None
        
        if name is not None:
            task.name = name
        if description is not None:
            task.description = description
        if phase_id is not None:
            task.phase_id = phase_id
        if parent_id is not None:
            task.parent_id = parent_id
        if status is not None:
            task.status = status if isinstance(status, TaskStatus) else TaskStatus(status)
        if priority is not None:
            task.priority = priority if isinstance(priority, TaskPriority) else TaskPriority(priority)
        if progress is not None:
            task.progress = progress
        if assignee_id is not None:
            task.assignee_id = assignee_id
        if assignee_type is not None:
            task.assignee_type = assignee_type
        if metadata is not None:
            task.metadata.update(metadata)
        if result is not None:
            task.result = result
        if error is not None:
            task.error = error
        
        task.updated_at = datetime.now()
        return task
    
    def delete_task(self, task_id):
        """Delete a task."""
        for project in self.projects.values():
            if task_id in project.tasks:
                del project.tasks[task_id]
                
                # Remove from phase if present
                for phase in project.phases.values():
                    if task_id in phase.tasks:
                        phase.tasks.remove(task_id)
                
                return True
        return False
    
    def update_task_status(self, task_id, status):
        """Update a task's status."""
        return self.update_task(task_id, status=status)
    
    def update_task_progress(self, task_id, progress):
        """Update a task's progress."""
        return self.update_task(task_id, progress=progress)
    
    def calculate_project_progress(self, project_id):
        """Calculate a project's progress."""
        project = self.get_project(project_id)
        if not project or not project.tasks:
            return 0.0
        
        total_progress = sum(task.progress for task in project.tasks.values())
        return total_progress / len(project.tasks)
    
    def calculate_phase_progress(self, project_id, phase_id):
        """Calculate a phase's progress."""
        project = self.get_project(project_id)
        if not project or phase_id not in project.phases:
            return 0.0
        
        phase = project.phases[phase_id]
        if not phase.tasks:
            return 0.0
        
        total_progress = sum(project.tasks[task_id].progress for task_id in phase.tasks if task_id in project.tasks)
        return total_progress / len(phase.tasks)
    
    def get_tasks_by_status(self, project_id, status):
        """Get tasks by status."""
        project = self.get_project(project_id)
        if not project:
            return []
        
        status_enum = status if isinstance(status, TaskStatus) else TaskStatus(status)
        return [task for task in project.tasks.values() if task.status == status_enum]
    
    def get_tasks_by_assignee(self, assignee_id, assignee_type=None):
        """Get tasks by assignee."""
        tasks = []
        for project in self.projects.values():
            for task in project.tasks.values():
                if task.assignee_id == assignee_id:
                    if assignee_type is None or task.assignee_type == assignee_type:
                        tasks.append(task)
        return tasks
    
    def save_data(self):
        """Save data to disk."""
        pass


def get_task_manager(data_dir=None):
    """Get a TaskManager instance."""
    return TaskManager(data_dir)
