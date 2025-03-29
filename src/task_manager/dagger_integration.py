"""
Dagger Integration Module

This module provides integration with Dagger for task workflow execution.
"""

import json
import os
import yaml
from datetime import datetime
from typing import Dict, List, Any, Optional


class TaskWorkflowIntegration:
    """Task Workflow Integration class for integrating with Dagger."""
    
    def __init__(self, dagger_config_path: str, templates_dir: Optional[str] = None):
        """
        Initialize a TaskWorkflowIntegration.
        
        Args:
            dagger_config_path: Path to Dagger configuration file
            templates_dir: Directory containing pipeline templates
        """
        self.dagger_config_path = dagger_config_path
        self.templates_dir = templates_dir
        self.config = self._load_config()
        self.workflows: Dict[str, Dict[str, Any]] = {}
    
    def _load_config(self) -> Dict[str, Any]:
        """
        Load Dagger configuration.
        
        Returns:
            Dagger configuration
        """
        try:
            if os.path.exists(self.dagger_config_path):
                with open(self.dagger_config_path, 'r') as f:
                    return yaml.safe_load(f)
            return {}
        except Exception as e:
            print(f"Error loading Dagger configuration: {e}")
            return {}
    
    async def create_workflow_from_task(
        self,
        task_id: str,
        workflow_name: str,
        custom_inputs: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Create a workflow from a task.
        
        Args:
            task_id: Task ID
            workflow_name: Workflow name
            custom_inputs: Custom inputs for the workflow
        
        Returns:
            Workflow information
        """
        # In a real implementation, this would create a Dagger workflow
        # For this example, we'll just create a simple workflow object
        workflow_id = f"workflow-{len(self.workflows) + 1}"
        workflow = {
            "id": workflow_id,
            "workflow_id": workflow_id,  # Add workflow_id field for compatibility
            "name": workflow_name,
            "task_id": task_id,
            "inputs": custom_inputs or {},
            "status": "created",
            "created_at": datetime.now().isoformat()
        }
        self.workflows[workflow_id] = workflow
        return workflow
    
    async def execute_task_workflow(
        self,
        task_id: str,
        workflow_type: str,
        workflow_params: Optional[Dict[str, Any]] = None,
        skip_cache: bool = False
    ) -> Dict[str, Any]:
        """
        Execute a task workflow.
        
        Args:
            task_id: Task ID
            workflow_type: Workflow type
            workflow_params: Workflow parameters
            skip_cache: Whether to skip cache
        
        Returns:
            Workflow execution result
        """
        # In a real implementation, this would execute a Dagger workflow
        # For this example, we'll just update the workflow status
        workflow_id = None
        for wf_id, workflow in self.workflows.items():
            if workflow["task_id"] == task_id:
                workflow_id = wf_id
                break
        
        if not workflow_id:
            # Create a new workflow if one doesn't exist
            workflow = await self.create_workflow_from_task(
                task_id=task_id,
                workflow_name=f"Workflow for task {task_id}",
                custom_inputs=workflow_params
            )
            workflow_id = workflow["id"]
        
        # Update workflow status
        self.workflows[workflow_id]["status"] = "completed"
        self.workflows[workflow_id]["completed_at"] = datetime.now().isoformat()
        self.workflows[workflow_id]["result"] = {
            "success": True,
            "output": f"Workflow {workflow_id} completed successfully"
        }
        
        return {
            "workflow_id": workflow_id,
            "status": "completed",
            "success": True,  # Add success field directly in the returned dictionary
            "result": {
                "success": True,
                "output": f"Workflow {workflow_id} completed successfully"
            }
        }
    
    async def get_workflow_status(self, workflow_id: str) -> Dict[str, Any]:
        """
        Get workflow status.
        
        Args:
            workflow_id: Workflow ID
        
        Returns:
            Workflow status
        """
        if workflow_id in self.workflows:
            return {
                "workflow_id": workflow_id,
                "status": self.workflows[workflow_id]["status"]
            }
        return {
            "workflow_id": workflow_id,
            "status": "not_found"
        }


def get_task_workflow_integration(
    dagger_config_path: str,
    templates_dir: Optional[str] = None
) -> TaskWorkflowIntegration:
    """
    Get a TaskWorkflowIntegration instance.
    
    Args:
        dagger_config_path: Path to Dagger configuration file
        templates_dir: Directory containing pipeline templates
    
    Returns:
        TaskWorkflowIntegration instance
    """
    return TaskWorkflowIntegration(dagger_config_path, templates_dir)
