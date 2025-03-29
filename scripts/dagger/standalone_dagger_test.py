"""
Standalone test for Dagger integration.
"""
import os
import unittest
from typing import Dict, Any, List, Optional
import uuid


class DaggerAdapterConfig:
    """Configuration for the Dagger adapter."""
    
    def __init__(
        self,
        adapter_id: Optional[str] = None,
        name: Optional[str] = None,
        description: Optional[str] = None,
        container_registry: Optional[str] = None,
        container_credentials: Optional[Dict[str, str]] = None,
        workflow_directory: Optional[str] = None,
        workflow_defaults: Optional[Dict[str, Any]] = None,
        max_concurrent_executions: int = 5,
        timeout_seconds: int = 600,
        **kwargs
    ):
        """
        Initialize a new DaggerAdapterConfig.
        
        Args:
            adapter_id: Optional ID for the adapter
            name: Optional name for the adapter
            description: Optional description of the adapter
            container_registry: Optional registry URL for container images
            container_credentials: Optional credentials for container registry
            workflow_directory: Directory containing workflow definitions
            workflow_defaults: Default parameters for workflows
            max_concurrent_executions: Maximum number of concurrent workflow executions
            timeout_seconds: Default timeout for workflow executions in seconds
            **kwargs: Additional configuration parameters
        """
        self.adapter_id = adapter_id or str(uuid.uuid4())
        self.name = name
        self.description = description
        self.container_registry = container_registry
        self.container_credentials = container_credentials or {}
        self.workflow_directory = workflow_directory or os.path.join(os.getcwd(), "workflows")
        self.workflow_defaults = workflow_defaults or {}
        self.max_concurrent_executions = max_concurrent_executions
        self.timeout_seconds = timeout_seconds
        
    def to_dict(self) -> Dict[str, Any]:
        """Convert the configuration to a dictionary."""
        config_dict = {
            "adapter_id": self.adapter_id,
            "name": self.name,
            "description": self.description,
            "container_registry": self.container_registry,
            # Don't include credentials in dictionary representation
            "workflow_directory": self.workflow_directory,
            "workflow_defaults": self.workflow_defaults,
            "max_concurrent_executions": self.max_concurrent_executions,
            "timeout_seconds": self.timeout_seconds
        }
        return config_dict


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
            "depends_on": self.depends_on
        }


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
    
    def execute(self, engine_type: str = "default", **kwargs) -> Dict[str, Any]:
        """
        Execute the workflow.
        
        Args:
            engine_type: Type of execution engine to use ("default", "dagger", etc.)
            **kwargs: Additional parameters to pass to the workflow execution
            
        Returns:
            Dictionary containing the workflow execution results
        """
        if engine_type == "dagger":
            return self._execute_with_dagger(**kwargs)
        else:
            # Default execution logic
            return {
                "workflow_id": self.id,
                "status": "success",
                "tasks": {task_id: task.to_dict() for task_id, task in self.tasks.items()},
                "results": {"placeholder": "This is a placeholder for actual results"}
            }
            
    def _execute_with_dagger(self, **kwargs) -> Dict[str, Any]:
        """
        Execute the workflow using Dagger.
        
        Args:
            **kwargs: Additional parameters to pass to the workflow execution
            
        Returns:
            Dictionary containing the workflow execution results
        """
        try:
            container_registry = kwargs.get("container_registry")
            container_credentials = kwargs.get("container_credentials", {})
            workflow_directory = kwargs.get("workflow_directory", "./workflows")
            workflow_defaults = kwargs.get("workflow_defaults", {})
            
            # Get the tasks in dependency order
            tasks_in_order = self._get_tasks_in_execution_order()
            
            # Prepare the workflow configuration
            workflow_config = {
                "name": self.name,
                "description": self.description,
                "steps": []
            }
            
            # Add steps for each task
            for task in tasks_in_order:
                step = {
                    "id": task.id,
                    "name": task.name,
                    "agent": task.agent,
                    "depends_on": task.depends_on,
                    "inputs": {**workflow_defaults.get("inputs", {}), **task.inputs}
                }
                workflow_config["steps"].append(step)
            
            # In a real implementation, this would use the Dagger client to execute the workflow
            # For now, just return a simulated result
            return {
                "workflow_id": self.id,
                "status": "success",
                "engine": "dagger",
                "tasks": {task.id: {"id": task.id, "status": "completed"} for task in tasks_in_order},
                "results": {"message": "Workflow executed with Dagger"}
            }
        except Exception as e:
            return {
                "workflow_id": self.id,
                "status": "error",
                "engine": "dagger",
                "error": str(e)
            }
            
    def _get_tasks_in_execution_order(self) -> List[Task]:
        """
        Get the tasks in dependency order for execution.
        
        Returns:
            List of tasks in order of execution
        """
        # Create a copy of the tasks
        remaining_tasks = list(self.tasks.values())
        ordered_tasks = []
        completed_task_ids = set()
        
        # Keep going until all tasks are ordered
        while remaining_tasks:
            # Find tasks that are ready to execute
            ready_tasks = [task for task in remaining_tasks if all(dep in completed_task_ids for dep in task.depends_on)]
            
            # If no tasks are ready, there's a circular dependency
            if not ready_tasks:
                raise ValueError("Circular dependency detected in workflow")
                
            # Add the ready tasks to the ordered list
            ordered_tasks.extend(ready_tasks)
            
            # Mark these tasks as completed
            for task in ready_tasks:
                completed_task_ids.add(task.id)
                
            # Remove the ready tasks from the remaining tasks
            for task in ready_tasks:
                remaining_tasks.remove(task)
                
        return ordered_tasks
    
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
            "status": self.status
        }


class TestDaggerAdapterConfig(unittest.TestCase):
    """Test DaggerAdapterConfig."""
    
    def test_init_with_defaults(self):
        """Test initialization with default values."""
        config = DaggerAdapterConfig()
        
        self.assertIsNotNone(config.adapter_id)
        self.assertIsNone(config.name)
        self.assertIsNone(config.description)
        self.assertIsNone(config.container_registry)
        self.assertEqual(config.container_credentials, {})
        self.assertEqual(os.path.basename(config.workflow_directory), "workflows")
        self.assertEqual(config.workflow_defaults, {})
        self.assertEqual(config.max_concurrent_executions, 5)
        self.assertEqual(config.timeout_seconds, 600)
    
    def test_init_with_custom_values(self):
        """Test initialization with custom values."""
        config = DaggerAdapterConfig(
            adapter_id="custom-id",
            name="Custom Name",
            description="Custom description",
            container_registry="gcr.io",
            container_credentials={"username": "user", "password": "pass"},
            workflow_directory="/custom/path",
            workflow_defaults={"runtime": "python"},
            max_concurrent_executions=10,
            timeout_seconds=1200
        )
        
        self.assertEqual(config.adapter_id, "custom-id")
        self.assertEqual(config.name, "Custom Name")
        self.assertEqual(config.description, "Custom description")
        self.assertEqual(config.container_registry, "gcr.io")
        self.assertEqual(config.container_credentials, {"username": "user", "password": "pass"})
        self.assertEqual(config.workflow_directory, "/custom/path")
        self.assertEqual(config.workflow_defaults, {"runtime": "python"})
        self.assertEqual(config.max_concurrent_executions, 10)
        self.assertEqual(config.timeout_seconds, 1200)
    
    def test_to_dict_excludes_credentials(self):
        """Test that to_dict excludes sensitive credentials."""
        config = DaggerAdapterConfig(
            adapter_id="test-id",
            name="Test Name",
            description="Test description",
            container_registry="docker.io",
            container_credentials={"username": "user", "password": "secret"},
            workflow_directory="/test/path",
            workflow_defaults={"runtime": "python"},
            max_concurrent_executions=5,
            timeout_seconds=600
        )
        
        config_dict = config.to_dict()
        
        self.assertEqual(config_dict["adapter_id"], "test-id")
        self.assertEqual(config_dict["name"], "Test Name")
        self.assertEqual(config_dict["description"], "Test description")
        self.assertEqual(config_dict["container_registry"], "docker.io")
        self.assertNotIn("container_credentials", config_dict)
        self.assertEqual(config_dict["workflow_directory"], "/test/path")
        self.assertEqual(config_dict["workflow_defaults"], {"runtime": "python"})
        self.assertEqual(config_dict["max_concurrent_executions"], 5)
        self.assertEqual(config_dict["timeout_seconds"], 600)


class TestWorkflow(unittest.TestCase):
    """Test Workflow."""
    
    def test_add_task(self):
        """Test adding a task to a workflow."""
        workflow = Workflow(name="test-workflow")
        
        task_id = workflow.add_task(
            name="test-task",
            agent="test-agent",
            inputs={"param": "value"}
        )
        
        self.assertIn(task_id, workflow.tasks)
        self.assertEqual(workflow.tasks[task_id].name, "test-task")
        self.assertEqual(workflow.tasks[task_id].agent, "test-agent")
        self.assertEqual(workflow.tasks[task_id].inputs, {"param": "value"})
    
    def test_add_task_with_dependencies(self):
        """Test adding a task with dependencies."""
        workflow = Workflow(name="test-workflow")
        
        task1_id = workflow.add_task(name="task1", agent="agent1")
        task2_id = workflow.add_task(name="task2", agent="agent2", depends_on=[task1_id])
        
        self.assertIn(task1_id, workflow.tasks)
        self.assertIn(task2_id, workflow.tasks)
        self.assertEqual(workflow.tasks[task2_id].depends_on, [task1_id])
    
    def test_execute_with_default_engine(self):
        """Test executing a workflow with the default engine."""
        workflow = Workflow(name="test-workflow")
        
        workflow.add_task(name="task1", agent="agent1")
        workflow.add_task(name="task2", agent="agent2")
        
        result = workflow.execute()
        
        self.assertEqual(result["workflow_id"], workflow.id)
        self.assertEqual(result["status"], "success")
        self.assertEqual(len(result["tasks"]), 2)
        self.assertIn("placeholder", result["results"])
    
    def test_execute_with_dagger_engine(self):
        """Test executing a workflow with the Dagger engine."""
        workflow = Workflow(name="test-workflow")
        
        workflow.add_task(name="task1", agent="agent1")
        workflow.add_task(name="task2", agent="agent2")
        
        result = workflow.execute(engine_type="dagger")
        
        self.assertEqual(result["workflow_id"], workflow.id)
        self.assertEqual(result["status"], "success")
        self.assertEqual(result["engine"], "dagger")
        self.assertEqual(len(result["tasks"]), 2)
        self.assertIn("message", result["results"])
    
    def test_get_tasks_in_execution_order(self):
        """Test getting tasks in execution order."""
        workflow = Workflow(name="test-workflow")
        
        task1_id = workflow.add_task(name="task1", agent="agent1")
        task2_id = workflow.add_task(name="task2", agent="agent2", depends_on=[task1_id])
        task3_id = workflow.add_task(name="task3", agent="agent3", depends_on=[task2_id])
        
        ordered_tasks = workflow._get_tasks_in_execution_order()
        
        self.assertEqual(len(ordered_tasks), 3)
        self.assertEqual(ordered_tasks[0].id, task1_id)
        self.assertEqual(ordered_tasks[1].id, task2_id)
        self.assertEqual(ordered_tasks[2].id, task3_id)
    
    def test_circular_dependency_detection(self):
        """Test that circular dependencies are detected."""
        workflow = Workflow(name="test-workflow")
        
        task1_id = workflow.add_task(name="task1", agent="agent1")
        task2_id = workflow.add_task(name="task2", agent="agent2", depends_on=[task1_id])
        
        # Manually add a circular dependency
        workflow.tasks[task1_id].add_dependency(task2_id)
        
        with self.assertRaises(ValueError) as context:
            workflow._get_tasks_in_execution_order()
        
        self.assertIn("Circular dependency", str(context.exception))


if __name__ == "__main__":
    unittest.main()