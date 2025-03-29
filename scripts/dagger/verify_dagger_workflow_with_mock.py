#!/usr/bin/env python3
"""
Verification script for the Dagger Workflow Integration using mock Dagger.
"""

import asyncio
import json
import os
import sys
import logging
from unittest.mock import MagicMock, AsyncMock

# Add project root to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Import the necessary modules
# Use mock modules instead of the installed ones
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), 'mock_modules'))

from mcp.types import (
    CallToolRequestSchema,
    ErrorCode,
    ListResourcesRequestSchema,
    ListResourceTemplatesRequestSchema,
    ListToolsRequestSchema,
    McpError,
    ReadResourceRequestSchema,
)

# Define WorkflowTemplate class for testing
class WorkflowTemplate:
    """Workflow template for testing."""
    
    def __init__(self, id, name, description, category=None, parameters=None, definition=None):
        """Initialize the workflow template."""
        self.id = id
        self.name = name
        self.description = description
        self.category = category
        self.parameters = parameters or {}
        self.definition = definition or {}
    
    def to_dict(self):
        """Convert the template to a dictionary."""
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "category": self.category,
            "parameters": self.parameters,
            "definition": self.definition
        }

# Import DaggerWorkflowIntegration after setting up the mock modules
from src.task_manager.mcp_servers.dagger_workflow_integration import DaggerWorkflowIntegration


class MockServer:
    """Mock MCP server for testing."""
    
    def __init__(self):
        """Initialize the mock server."""
        self._request_handlers = {}
        
        # Set up default handlers
        self._request_handlers[ListResourcesRequestSchema.__name__] = AsyncMock(
            return_value={"resources": []}
        )
        self._request_handlers[ListResourceTemplatesRequestSchema.__name__] = AsyncMock(
            return_value={"resourceTemplates": []}
        )
        self._request_handlers[ReadResourceRequestSchema.__name__] = AsyncMock()
        self._request_handlers[ListToolsRequestSchema.__name__] = AsyncMock(
            return_value={"tools": []}
        )
        self._request_handlers[CallToolRequestSchema.__name__] = AsyncMock()
    
    def set_request_handler(self, schema, handler):
        """Set a request handler."""
        self._request_handlers[schema.__name__] = handler


class MockTaskManager:
    """Mock Task Manager for testing."""
    
    def __init__(self):
        """Initialize the mock task manager."""
        self.projects = {
            "project-1": MagicMock(
                tasks={
                    "task-1": MagicMock(
                        metadata={"workflow_id": "workflow-1", "workflow_status": "completed"}
                    ),
                    "task-2": MagicMock(
                        metadata={"workflow_id": "workflow-2", "workflow_status": "in_progress"}
                    ),
                }
            )
        }
    
    def get_project(self, project_id):
        """Get a project by ID."""
        return self.projects.get(project_id)


class MockWorkflowIntegration:
    """Mock Workflow Integration for testing."""
    
    async def get_workflow_status(self, task_id):
        """Get workflow status."""
        return {"has_workflow": True, "status": "completed", "task_id": task_id}
    
    async def create_workflow_from_task(self, task_id, workflow_name=None, custom_inputs=None):
        """Create a workflow from a task."""
        return {
            "workflow_id": f"workflow-{task_id}",
            "status": "created",
            "task_id": task_id,
            "workflow_name": workflow_name or f"Workflow for {task_id}"
        }
    
    async def execute_task_workflow(self, task_id, workflow_type="containerized_workflow", workflow_params=None, skip_cache=False):
        """Execute a workflow for a task."""
        return {
            "execution_id": f"exec-{task_id}",
            "status": "running",
            "task_id": task_id,
            "workflow_type": workflow_type
        }
    
    async def create_workflows_for_project(self, project_id, phase_id=None, status=None):
        """Create workflows for a project."""
        return {"created": 2, "failed": 0, "project_id": project_id}
    
    async def execute_workflows_for_project(self, project_id, phase_id=None, status=None, workflow_type="containerized_workflow", skip_cache=False):
        """Execute workflows for a project."""
        return {"executed": 2, "failed": 0, "project_id": project_id}
    
    async def create_workflow_from_template(self, task_id, template, parameters=None):
        """Create a workflow from a template."""
        return {
            "workflow_id": f"template-workflow-{task_id}",
            "status": "created",
            "task_id": task_id,
            "template_id": template.id
        }


class MockTemplateRegistry:
    """Mock Template Registry for testing."""
    
    def __init__(self):
        """Initialize the mock template registry."""
        self.templates = {
            "ml-training": WorkflowTemplate(
                id="ml-training",
                name="ML Training Workflow",
                description="Workflow for training machine learning models",
                category="ml",
                parameters={
                    "epochs": {"type": "integer", "default": 10},
                    "batch_size": {"type": "integer", "default": 32}
                },
                definition={"steps": ["preprocess", "train", "evaluate"]}
            ),
            "data-processing": WorkflowTemplate(
                id="data-processing",
                name="Data Processing Workflow",
                description="Workflow for processing data",
                category="data",
                parameters={
                    "input_format": {"type": "string", "default": "csv"},
                    "output_format": {"type": "string", "default": "parquet"}
                },
                definition={"steps": ["extract", "transform", "load"]}
            )
        }
        self.categories = ["ml", "data"]
    
    def list_templates(self, category=None):
        """List templates."""
        if category:
            return [t.to_dict() for t in self.templates.values() if t.category == category]
        return [t.to_dict() for t in self.templates.values()]
    
    def get_categories(self):
        """Get categories."""
        return self.categories
    
    def get_template(self, template_id):
        """Get a template by ID."""
        return self.templates.get(template_id)


async def verify_dagger_workflow_integration():
    """Verify the Dagger Workflow Integration."""
    logger.info("Starting verification of Dagger Workflow Integration...")
    
    # Create mock objects
    server = MockServer()
    task_manager = MockTaskManager()
    workflow_integration = MockWorkflowIntegration()
    template_registry = MockTemplateRegistry()
    
    # Create the integration
    integration = DaggerWorkflowIntegration(
        server=server,
        task_manager=task_manager,
        dagger_config_path="test-config.yaml",
        templates_dir="test-templates"
    )
    
    # Replace the workflow integration and template registry with our mocks
    integration.workflow_integration = workflow_integration
    integration.template_registry = template_registry
    
    # Test getting all workflows
    logger.info("Testing _get_all_workflows...")
    workflows = await integration._get_all_workflows()
    assert len(workflows) == 2, f"Expected 2 workflows, got {len(workflows)}"
    assert "task-1" in workflows, "Expected task-1 in workflows"
    assert "task-2" in workflows, "Expected task-2 in workflows"
    logger.info("_get_all_workflows test passed!")
    
    # Test getting workflow stats
    logger.info("Testing _get_workflow_stats...")
    stats = await integration._get_workflow_stats()
    assert stats["total_workflows"] == 2, f"Expected 2 total workflows, got {stats['total_workflows']}"
    assert stats["completed_workflows"] == 1, f"Expected 1 completed workflow, got {stats['completed_workflows']}"
    assert stats["in_progress_workflows"] == 1, f"Expected 1 in-progress workflow, got {stats['in_progress_workflows']}"
    assert stats["success_rate"] == 50.0, f"Expected 50.0% success rate, got {stats['success_rate']}%"
    logger.info("_get_workflow_stats test passed!")
    
    # Test getting project workflows
    logger.info("Testing _get_project_workflows...")
    project_workflows = await integration._get_project_workflows("project-1")
    assert len(project_workflows) == 2, f"Expected 2 project workflows, got {len(project_workflows)}"
    logger.info("_get_project_workflows test passed!")
    
    # Test creating a workflow from a task
    logger.info("Testing _handle_create_workflow_from_task...")
    result = await integration._handle_create_workflow_from_task({"task_id": "task-1", "workflow_name": "Test Workflow"})
    assert "content" in result, "Expected content in result"
    assert len(result["content"]) == 1, f"Expected 1 content item, got {len(result['content'])}"
    assert result["content"][0]["type"] == "text", f"Expected text type, got {result['content'][0]['type']}"
    logger.info("_handle_create_workflow_from_task test passed!")
    
    # Test executing a workflow
    logger.info("Testing _handle_execute_task_workflow...")
    result = await integration._handle_execute_task_workflow({"task_id": "task-1", "workflow_type": "containerized_workflow"})
    assert "content" in result, "Expected content in result"
    assert len(result["content"]) == 1, f"Expected 1 content item, got {len(result['content'])}"
    assert result["content"][0]["type"] == "text", f"Expected text type, got {result['content'][0]['type']}"
    logger.info("_handle_execute_task_workflow test passed!")
    
    # Test getting workflow status
    logger.info("Testing _handle_get_workflow_status...")
    result = await integration._handle_get_workflow_status({"task_id": "task-1"})
    assert "content" in result, "Expected content in result"
    assert len(result["content"]) == 1, f"Expected 1 content item, got {len(result['content'])}"
    assert result["content"][0]["type"] == "text", f"Expected text type, got {result['content'][0]['type']}"
    logger.info("_handle_get_workflow_status test passed!")
    
    # Test creating workflows for a project
    logger.info("Testing _handle_create_workflows_for_project...")
    result = await integration._handle_create_workflows_for_project({"project_id": "project-1"})
    assert "content" in result, "Expected content in result"
    assert len(result["content"]) == 1, f"Expected 1 content item, got {len(result['content'])}"
    assert result["content"][0]["type"] == "text", f"Expected text type, got {result['content'][0]['type']}"
    logger.info("_handle_create_workflows_for_project test passed!")
    
    # Test executing workflows for a project
    logger.info("Testing _handle_execute_workflows_for_project...")
    result = await integration._handle_execute_workflows_for_project({"project_id": "project-1", "workflow_type": "dagger_pipeline"})
    assert "content" in result, "Expected content in result"
    assert len(result["content"]) == 1, f"Expected 1 content item, got {len(result['content'])}"
    assert result["content"][0]["type"] == "text", f"Expected text type, got {result['content'][0]['type']}"
    logger.info("_handle_execute_workflows_for_project test passed!")
    
    # Test listing workflow templates
    logger.info("Testing _handle_list_workflow_templates...")
    result = await integration._handle_list_workflow_templates({})
    assert "content" in result, "Expected content in result"
    assert len(result["content"]) == 1, f"Expected 1 content item, got {len(result['content'])}"
    assert result["content"][0]["type"] == "text", f"Expected text type, got {result['content'][0]['type']}"
    logger.info("_handle_list_workflow_templates test passed!")
    
    # Test getting a workflow template
    logger.info("Testing _handle_get_workflow_template...")
    result = await integration._handle_get_workflow_template({"template_id": "ml-training"})
    assert "content" in result, "Expected content in result"
    assert len(result["content"]) == 1, f"Expected 1 content item, got {len(result['content'])}"
    assert result["content"][0]["type"] == "text", f"Expected text type, got {result['content'][0]['type']}"
    logger.info("_handle_get_workflow_template test passed!")
    
    # Test creating a workflow from a template
    logger.info("Testing _handle_create_workflow_from_template...")
    result = await integration._handle_create_workflow_from_template({
        "task_id": "task-1",
        "template_id": "ml-training",
        "parameters": {"epochs": 20, "batch_size": 64}
    })
    assert "content" in result, "Expected content in result"
    assert len(result["content"]) == 1, f"Expected 1 content item, got {len(result['content'])}"
    assert result["content"][0]["type"] == "text", f"Expected text type, got {result['content'][0]['type']}"
    logger.info("_handle_create_workflow_from_template test passed!")
    
    # Test handling Dagger workflow resources
    logger.info("Testing _handle_dagger_workflow_resource...")
    
    # Test workflows resource
    result = await integration._handle_dagger_workflow_resource("task-manager://dagger/workflows")
    assert "contents" in result, "Expected contents in result"
    assert len(result["contents"]) == 1, f"Expected 1 content item, got {len(result['contents'])}"
    assert result["contents"][0]["uri"] == "task-manager://dagger/workflows", f"Expected task-manager://dagger/workflows URI, got {result['contents'][0]['uri']}"
    
    # Test stats resource
    result = await integration._handle_dagger_workflow_resource("task-manager://dagger/stats")
    assert "contents" in result, "Expected contents in result"
    assert len(result["contents"]) == 1, f"Expected 1 content item, got {len(result['contents'])}"
    assert result["contents"][0]["uri"] == "task-manager://dagger/stats", f"Expected task-manager://dagger/stats URI, got {result['contents'][0]['uri']}"
    
    # Test templates resource
    result = await integration._handle_dagger_workflow_resource("task-manager://dagger/templates")
    assert "contents" in result, "Expected contents in result"
    assert len(result["contents"]) == 1, f"Expected 1 content item, got {len(result['contents'])}"
    assert result["contents"][0]["uri"] == "task-manager://dagger/templates", f"Expected task-manager://dagger/templates URI, got {result['contents'][0]['uri']}"
    
    logger.info("_handle_dagger_workflow_resource test passed!")
    
    logger.info("All verification tests passed!")
    return True


if __name__ == "__main__":
    # Run the verification
    loop = asyncio.get_event_loop()
    success = loop.run_until_complete(verify_dagger_workflow_integration())
    
    if success:
        logger.info("Dagger Workflow Integration verification completed successfully!")
        sys.exit(0)
    else:
        logger.error("Dagger Workflow Integration verification failed!")
        sys.exit(1)
