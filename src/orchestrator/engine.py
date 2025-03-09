"""
Orchestration Engine Module

This module provides the core orchestration functionality for the AI-Orchestration-Platform.
It manages workflows, tasks, and their execution across different AI agents.
"""

import logging
import uuid
from typing import Dict, List, Any, Optional, Union
from datetime import datetime

# Configure logging
logger = logging.getLogger(__name__)

class Task:
    """Represents a single task in a workflow."""
    
    def __init__(self, id: str, name: str, agent: str, inputs: Optional[Dict[str, Any]] = None):
        """
        Initialize a new Task.
        
        Args:
            id: Unique identifier for the task
            name: Human-readable name for the task
            agent: The agent type that will execute this task
            inputs: Dictionary of input parameters for the task
        """
        self.id = id
        self.name = name
        self.agent = agent
        self.inputs = inputs or {}
        self.outputs: Dict[str, Any] = {}
        self.status = "pending"
        self.depends_on: List[str] = []
        self.created_at = datetime.now()
        self.started_at: Optional[datetime] = None
        self.completed_at: Optional[datetime] = None
        self.error: Optional[str] = None
    
    def add_dependency(self, task_id: str) -> None:
        """
        Add a dependency on another task.
        
        Args:
            task_id: The ID of the task this task depends on
        """
        if task_id not in self.depends_on:
            self.depends_on.append(task_id)
    
    def is_ready(self, completed_tasks: List[str]) -> bool:
        """
        Check if this task is ready to execute.
        
        Args:
            completed_tasks: List of IDs of completed tasks
            
        Returns:
            True if all dependencies are satisfied, False otherwise
        """
        return all(dep in completed_tasks for dep in self.depends_on)
    
    def to_dict(self) -> Dict[str, Any]:
        """
        Convert the task to a dictionary representation.
        
        Returns:
            Dictionary representation of the task
        """
        return {
            "id": self.id,
            "name": self.name,
            "agent": self.agent,
            "inputs": self.inputs,
            "outputs": self.outputs,
            "status": self.status,
            "depends_on": self.depends_on,
            "created_at": self.created_at.isoformat(),
            "started_at": self.started_at.isoformat() if self.started_at else None,
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
            "error": self.error
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Task':
        """
        Create a task from a dictionary representation.
        
        Args:
            data: Dictionary representation of the task
            
        Returns:
            A new Task instance
        """
        task = cls(
            id=data["id"],
            name=data["name"],
            agent=data["agent"],
            inputs=data.get("inputs", {})
        )
        task.outputs = data.get("outputs", {})
        task.status = data.get("status", "pending")
        task.depends_on = data.get("depends_on", [])
        
        # Parse datetime fields if they exist
        if "created_at" in data and data["created_at"]:
            task.created_at = datetime.fromisoformat(data["created_at"])
        if "started_at" in data and data["started_at"]:
            task.started_at = datetime.fromisoformat(data["started_at"])
        if "completed_at" in data and data["completed_at"]:
            task.completed_at = datetime.fromisoformat(data["completed_at"])
            
        task.error = data.get("error")
        return task


class Workflow:
    """Represents a workflow composed of multiple tasks."""
    
    def __init__(self, name: str, description: Optional[str] = None):
        """
        Initialize a new Workflow.
        
        Args:
            name: Name of the workflow
            description: Optional description of the workflow
        """
        self.id = str(uuid.uuid4())
        self.name = name
        self.description = description
        self.tasks: Dict[str, Task] = {}
        self.status = "pending"
        self.created_at = datetime.now()
        self.started_at: Optional[datetime] = None
        self.completed_at: Optional[datetime] = None
        self.error: Optional[str] = None
    
    def add_task(self, name: str, agent: str, inputs: Optional[Dict[str, Any]] = None, 
                depends_on: Optional[List[str]] = None) -> str:
        """
        Add a task to the workflow.
        
        Args:
            name: Name of the task
            agent: Agent type that will execute the task
            inputs: Optional dictionary of input parameters
            depends_on: Optional list of task IDs this task depends on
            
        Returns:
            The ID of the newly created task
        """
        task_id = f"{self.name}_{name}_{len(self.tasks)}"
        task = Task(id=task_id, name=name, agent=agent, inputs=inputs)
        
        if depends_on:
            for dep_id in depends_on:
                if dep_id in self.tasks:
                    task.add_dependency(dep_id)
                else:
                    raise ValueError(f"Dependency task {dep_id} does not exist")
        
        self.tasks[task_id] = task
        return task_id
    
    def get_task(self, task_id: str) -> Task:
        """
        Get a task by ID.
        
        Args:
            task_id: ID of the task to retrieve
            
        Returns:
            The requested Task
            
        Raises:
            KeyError: If the task does not exist
        """
        if task_id not in self.tasks:
            raise KeyError(f"Task {task_id} not found in workflow {self.name}")
        return self.tasks[task_id]
    
    def get_next_tasks(self) -> List[Task]:
        """
        Get the next tasks that are ready to execute.
        
        Returns:
            List of tasks that are ready to execute
        """
        completed_task_ids = [
            task_id for task_id, task in self.tasks.items() 
            if task.status == "completed"
        ]
        
        return [
            task for task_id, task in self.tasks.items()
            if task.status == "pending" and task.is_ready(completed_task_ids)
        ]
    
    def execute(self, **kwargs) -> Dict[str, Any]:
        """
        Execute the workflow.
        
        This is a placeholder implementation that would be replaced with actual execution logic.
        
        Args:
            **kwargs: Additional parameters to pass to the workflow execution
            
        Returns:
            Dictionary containing the workflow execution results
        """
        # This would be implemented with actual execution logic
        # For now, just return a placeholder result
        return {
            "workflow_id": self.id,
            "status": "success",
            "tasks": {task_id: task.to_dict() for task_id, task in self.tasks.items()},
            "results": {"placeholder": "This is a placeholder for actual results"}
        }
    
    def to_dict(self) -> Dict[str, Any]:
        """
        Convert the workflow to a dictionary representation.
        
        Returns:
            Dictionary representation of the workflow
        """
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "tasks": {task_id: task.to_dict() for task_id, task in self.tasks.items()},
            "status": self.status,
            "created_at": self.created_at.isoformat(),
            "started_at": self.started_at.isoformat() if self.started_at else None,
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
            "error": self.error
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Workflow':
        """
        Create a workflow from a dictionary representation.
        
        Args:
            data: Dictionary representation of the workflow
            
        Returns:
            A new Workflow instance
        """
        workflow = cls(
            name=data["name"],
            description=data.get("description")
        )
        workflow.id = data.get("id", workflow.id)
        workflow.status = data.get("status", "pending")
        
        # Parse datetime fields if they exist
        if "created_at" in data and data["created_at"]:
            workflow.created_at = datetime.fromisoformat(data["created_at"])
        if "started_at" in data and data["started_at"]:
            workflow.started_at = datetime.fromisoformat(data["started_at"])
        if "completed_at" in data and data["completed_at"]:
            workflow.completed_at = datetime.fromisoformat(data["completed_at"])
            
        workflow.error = data.get("error")
        
        # Add tasks
        tasks_data = data.get("tasks", {})
        for task_id, task_data in tasks_data.items():
            task = Task.from_dict(task_data)
            workflow.tasks[task_id] = task
            
        return workflow
    
    def from_config(self, config: Dict[str, Any]) -> 'Workflow':
        """
        Configure the workflow from a configuration dictionary.
        
        Args:
            config: Configuration dictionary
            
        Returns:
            Self, for method chaining
        """
        self.name = config.get("name", self.name)
        self.description = config.get("description", self.description)
        
        # Clear existing tasks
        self.tasks = {}
        
        # Add tasks from config
        tasks_config = config.get("tasks", [])
        for task_config in tasks_config:
            task_id = task_config["id"]
            task = Task(
                id=task_id,
                name=task_config["name"],
                agent=task_config["agent"],
                inputs=task_config.get("inputs", {})
            )
            
            # Add dependencies
            depends_on = task_config.get("depends_on", [])
            for dep_id in depends_on:
                task.add_dependency(dep_id)
                
            self.tasks[task_id] = task
            
        return self


class OrchestrationEngine:
    """Main orchestration engine for managing workflows and their execution."""
    
    def __init__(self):
        """Initialize a new OrchestrationEngine."""
        self.workflows: Dict[str, Workflow] = {}
        # In a real implementation, this would be connected to an agent manager
        # self.agent_manager = AgentManager()
    
    def create_workflow(self, name: str, description: Optional[str] = None) -> Workflow:
        """
        Create a new workflow.
        
        Args:
            name: Name of the workflow
            description: Optional description of the workflow
            
        Returns:
            The newly created Workflow
        """
        workflow = Workflow(name=name, description=description)
        self.workflows[workflow.id] = workflow
        return workflow
    
    def get_workflow(self, workflow_id: str) -> Workflow:
        """
        Get a workflow by ID.
        
        Args:
            workflow_id: ID of the workflow to retrieve
            
        Returns:
            The requested Workflow
            
        Raises:
            KeyError: If the workflow does not exist
        """
        if workflow_id not in self.workflows:
            raise KeyError(f"Workflow {workflow_id} not found")
        return self.workflows[workflow_id]
    
    def execute_workflow(self, workflow_id: str, **kwargs) -> Dict[str, Any]:
        """
        Execute a workflow.
        
        Args:
            workflow_id: ID of the workflow to execute
            **kwargs: Additional parameters to pass to the workflow execution
            
        Returns:
            Dictionary containing the workflow execution results
            
        Raises:
            KeyError: If the workflow does not exist
        """
        workflow = self.get_workflow(workflow_id)
        return workflow.execute(**kwargs)
    
    def list_workflows(self) -> List[Dict[str, Any]]:
        """
        List all workflows.
        
        Returns:
            List of workflow dictionaries
        """
        return [workflow.to_dict() for workflow in self.workflows.values()]
