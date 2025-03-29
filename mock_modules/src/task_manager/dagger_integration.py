"""
Mock Task Manager Dagger Integration module for testing.

This module provides mock implementations of Task Manager Dagger Integration classes and functions
for testing purposes.
"""

from typing import Dict, List, Optional, Any, Union
from datetime import datetime

# Import DaggerAdapter for patching in tests
from src.agent_manager.dagger_adapter import DaggerAdapter, DaggerAdapterConfig

# Import get_task_manager for patching in tests
def get_task_manager(data_dir=None):
    """Get a TaskManager instance."""
    from src.task_manager.manager import get_task_manager as real_get_task_manager
    return real_get_task_manager(data_dir)


class TaskWorkflowIntegration:
    """Mock TaskWorkflowIntegration class."""
    
    def __init__(self, dagger_config_path=None):
        """Initialize a new TaskWorkflowIntegration."""
        from src.agent_manager.dagger_adapter import DaggerAdapter, DaggerAdapterConfig
        from src.task_manager.manager import get_task_manager
        
        self.task_manager = get_task_manager()
        self.dagger_adapter = DaggerAdapter(DaggerAdapterConfig())
        self._initialized = True
    
    async def initialize(self):
        """Initialize the integration."""
        pass
    
    async def create_workflow_from_task(self, task_id, workflow_name=None, custom_inputs=None):
        """Create a Dagger workflow from a task."""
        task = self.task_manager.get_task(task_id)
        if not task:
            raise ValueError(f"Task not found: {task_id}")
        
        self.task_manager.update_task_status(task_id, "in_progress")
        
        import uuid
        workflow_id = f"workflow_{uuid.uuid4().hex[:8]}"
        
        self.task_manager.update_task(
            task_id=task_id,
            metadata={
                **task.metadata,
                "workflow_id": workflow_id,
                "workflow_created_at": datetime.now().isoformat(),
            },
        )
        
        return {
            "workflow_id": workflow_id,
            "task_id": task_id,
            "name": workflow_name or task.name,
            "description": task.description,
            "inputs": custom_inputs or task.metadata.get("workflow_inputs", {}),
        }
    
    async def execute_task_workflow(self, task_id, workflow_type="containerized_workflow", workflow_params=None, skip_cache=False):
        """Execute a workflow for a task."""
        task = self.task_manager.get_task(task_id)
        if not task:
            raise ValueError(f"Task not found: {task_id}")
        
        workflow_id = task.metadata.get("workflow_id")
        if not workflow_id:
            workflow_info = await self.create_workflow_from_task(task_id)
            workflow_id = workflow_info["workflow_id"]
        
        self.task_manager.update_task_status(task_id, "in_progress")
        self.task_manager.update_task(
            task_id=task_id,
            metadata={
                **task.metadata,
                "workflow_id": workflow_id,
                "workflow_started_at": datetime.now().isoformat(),
                "workflow_type": workflow_type,
            },
        )
        
        if workflow_params is None:
            workflow_params = {}
        
        workflow_params.update({
            "task_id": task_id,
            "workflow_id": workflow_id,
            "skip_cache": skip_cache,
        })
        
        from src.agent_manager.schemas import AgentExecutionConfig, AgentExecutionResult
        execution_config = AgentExecutionConfig(
            task_id=task_id,
            execution_type=workflow_type,
            parameters=workflow_params,
        )
        
        result = await self.dagger_adapter.execute(execution_config)
        
        if result.success:
            self.task_manager.update_task(
                task_id=task_id,
                status="completed",
                progress=100.0,
                result=result.result,
                metadata={
                    **task.metadata,
                    "workflow_completed_at": datetime.now().isoformat(),
                    "workflow_status": "completed",
                },
            )
            
            return {
                "success": True,
                "task_id": task_id,
                "workflow_id": workflow_id,
                "result": result.result,
            }
        else:
            self.task_manager.update_task(
                task_id=task_id,
                status="failed",
                error=result.error,
                metadata={
                    **task.metadata,
                    "workflow_failed_at": datetime.now().isoformat(),
                    "workflow_status": "failed",
                    "workflow_error": result.error,
                },
            )
            
            return {
                "success": False,
                "task_id": task_id,
                "workflow_id": workflow_id,
                "error": result.error,
            }
    
    async def get_workflow_status(self, task_id):
        """Get the status of a workflow for a task."""
        task = self.task_manager.get_task(task_id)
        if not task:
            raise ValueError(f"Task not found: {task_id}")
        
        workflow_id = task.metadata.get("workflow_id")
        if not workflow_id:
            return {
                "task_id": task_id,
                "has_workflow": False,
                "message": "No workflow associated with this task",
            }
        
        workflow_status = task.metadata.get("workflow_status", "unknown")
        
        return {
            "task_id": task_id,
            "has_workflow": True,
            "workflow_id": workflow_id,
            "workflow_status": workflow_status,
            "workflow_type": task.metadata.get("workflow_type"),
            "workflow_created_at": task.metadata.get("workflow_created_at"),
            "workflow_started_at": task.metadata.get("workflow_started_at"),
            "workflow_completed_at": task.metadata.get("workflow_completed_at"),
            "workflow_failed_at": task.metadata.get("workflow_failed_at"),
            "workflow_error": task.metadata.get("workflow_error"),
        }
    
    async def create_workflows_for_project(self, project_id, phase_id=None, status=None):
        """Create workflows for all tasks in a project or phase."""
        project = self.task_manager.get_project(project_id)
        if not project:
            raise ValueError(f"Project not found: {project_id}")
        
        tasks = []
        for task_id, task in project.tasks.items():
            if phase_id and task.phase_id != phase_id:
                continue
            if status and task.status != status:
                continue
            tasks.append(task)
        
        result = {}
        for task in tasks:
            try:
                workflow_info = await self.create_workflow_from_task(task.id)
                result[task.id] = workflow_info["workflow_id"]
            except Exception as e:
                pass
        
        return result
    
    async def execute_workflows_for_project(self, project_id, phase_id=None, status=None, workflow_type="containerized_workflow", skip_cache=False):
        """Execute workflows for all tasks in a project or phase."""
        project = self.task_manager.get_project(project_id)
        if not project:
            raise ValueError(f"Project not found: {project_id}")
        
        tasks = []
        for task_id, task in project.tasks.items():
            if phase_id and task.phase_id != phase_id:
                continue
            if status and task.status != status:
                continue
            tasks.append(task)
        
        result = {}
        for task in tasks:
            try:
                execution_result = await self.execute_task_workflow(
                    task_id=task.id,
                    workflow_type=workflow_type,
                    skip_cache=skip_cache,
                )
                result[task.id] = execution_result
            except Exception as e:
                result[task.id] = {
                    "success": False,
                    "task_id": task.id,
                    "error": str(e),
                }
        
        return result
    
    async def shutdown(self):
        """Shutdown the integration."""
        if self._initialized:
            await self.dagger_adapter.shutdown()
            self._initialized = False


def get_task_workflow_integration(dagger_config_path=None):
    """Get a TaskWorkflowIntegration instance."""
    return TaskWorkflowIntegration(dagger_config_path)
