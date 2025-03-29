#!/usr/bin/env python3
"""
Tests for the Dagger Workflow Integration for Task Management MCP Server.
"""

import asyncio
import json
import os
import sys
import unittest
from unittest.mock import MagicMock, patch, AsyncMock

# Add project root to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.task_manager.mcp_servers.dagger_workflow_integration import DaggerWorkflowIntegration
from src.task_manager.mcp_servers.workflow_templates import WorkflowTemplate


class TestDaggerWorkflowIntegration(unittest.TestCase):
    """Test cases for the Dagger Workflow Integration."""

    def setUp(self):
        """Set up test fixtures."""
        self.server = MagicMock()
        self.server._request_handlers = {}
        
        # Mock the original handlers
        self.server._request_handlers["ListResourcesRequestSchema"] = AsyncMock(
            return_value={"resources": []}
        )
        self.server._request_handlers["ListResourceTemplatesRequestSchema"] = AsyncMock(
            return_value={"resourceTemplates": []}
        )
        self.server._request_handlers["ReadResourceRequestSchema"] = AsyncMock()
        self.server._request_handlers["ListToolsRequestSchema"] = AsyncMock(
            return_value={"tools": []}
        )
        self.server._request_handlers["CallToolRequestSchema"] = AsyncMock()
        
        # Mock task manager
        self.task_manager = MagicMock()
        self.task_manager.projects = {
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
        self.task_manager.get_project = MagicMock(return_value=self.task_manager.projects["project-1"])
        
        # Mock workflow integration
        self.workflow_integration = MagicMock()
        self.workflow_integration.get_workflow_status = AsyncMock(
            return_value={"has_workflow": True, "status": "completed"}
        )
        self.workflow_integration.create_workflow_from_task = AsyncMock(
            return_value={"workflow_id": "new-workflow", "status": "created"}
        )
        self.workflow_integration.execute_task_workflow = AsyncMock(
            return_value={"execution_id": "exec-1", "status": "running"}
        )
        self.workflow_integration.create_workflows_for_project = AsyncMock(
            return_value={"created": 2, "failed": 0}
        )
        self.workflow_integration.execute_workflows_for_project = AsyncMock(
            return_value={"executed": 2, "failed": 0}
        )
        self.workflow_integration.create_workflow_from_template = AsyncMock(
            return_value={"workflow_id": "template-workflow", "status": "created"}
        )
        
        # Mock template registry
        self.template_registry = MagicMock()
        self.template_registry.list_templates = MagicMock(
            return_value=[{"id": "template-1", "name": "Template 1"}]
        )
        self.template_registry.get_categories = MagicMock(
            return_value=["ml", "data-processing"]
        )
        self.template_registry.get_template = MagicMock(
            return_value=WorkflowTemplate(
                id="template-1",
                name="Template 1",
                description="Test template",
                category="ml",
                parameters={},
                definition={}
            )
        )
        
        # Create integration with mocks
        with patch("src.task_manager.dagger_integration.get_task_workflow_integration", 
                  return_value=self.workflow_integration):
            with patch("src.task_manager.mcp_servers.workflow_templates.get_template_registry",
                      return_value=self.template_registry):
                self.integration = DaggerWorkflowIntegration(
                    server=self.server,
                    task_manager=self.task_manager,
                    dagger_config_path="test-config.yaml",
                    templates_dir="test-templates"
                )

    async def test_get_all_workflows(self):
        """Test getting all workflows."""
        workflows = await self.integration._get_all_workflows()
        self.assertEqual(len(workflows), 2)
        self.assertIn("task-1", workflows)
        self.assertIn("task-2", workflows)

    async def test_get_workflow_stats(self):
        """Test getting workflow statistics."""
        stats = await self.integration._get_workflow_stats()
        self.assertEqual(stats["total_workflows"], 2)
        self.assertEqual(stats["completed_workflows"], 1)
        self.assertEqual(stats["in_progress_workflows"], 1)
        self.assertEqual(stats["success_rate"], 50.0)

    async def test_get_project_workflows(self):
        """Test getting workflows for a project."""
        workflows = await self.integration._get_project_workflows("project-1")
        self.assertEqual(len(workflows), 2)
        self.assertIn("task-1", workflows)
        self.assertIn("task-2", workflows)

    async def test_handle_create_workflow_from_task(self):
        """Test creating a workflow from a task."""
        args = {"task_id": "task-1", "workflow_name": "Test Workflow"}
        result = await self.integration._handle_create_workflow_from_task(args)
        self.assertIn("content", result)
        self.assertEqual(len(result["content"]), 1)
        self.assertEqual(result["content"][0]["type"], "text")
        
        # Verify the workflow integration was called correctly
        self.workflow_integration.create_workflow_from_task.assert_called_once_with(
            task_id="task-1",
            workflow_name="Test Workflow",
            custom_inputs=None
        )

    async def test_handle_execute_task_workflow(self):
        """Test executing a workflow for a task."""
        args = {"task_id": "task-1", "workflow_type": "containerized_workflow"}
        result = await self.integration._handle_execute_task_workflow(args)
        self.assertIn("content", result)
        self.assertEqual(len(result["content"]), 1)
        self.assertEqual(result["content"][0]["type"], "text")
        
        # Verify the workflow integration was called correctly
        self.workflow_integration.execute_task_workflow.assert_called_once_with(
            task_id="task-1",
            workflow_type="containerized_workflow",
            workflow_params={},
            skip_cache=False
        )

    async def test_handle_get_workflow_status(self):
        """Test getting workflow status."""
        args = {"task_id": "task-1"}
        result = await self.integration._handle_get_workflow_status(args)
        self.assertIn("content", result)
        self.assertEqual(len(result["content"]), 1)
        self.assertEqual(result["content"][0]["type"], "text")
        
        # Verify the workflow integration was called correctly
        self.workflow_integration.get_workflow_status.assert_called_with(
            task_id="task-1"
        )

    async def test_handle_create_workflows_for_project(self):
        """Test creating workflows for a project."""
        args = {"project_id": "project-1"}
        result = await self.integration._handle_create_workflows_for_project(args)
        self.assertIn("content", result)
        self.assertEqual(len(result["content"]), 1)
        self.assertEqual(result["content"][0]["type"], "text")
        
        # Verify the workflow integration was called correctly
        self.workflow_integration.create_workflows_for_project.assert_called_once_with(
            project_id="project-1",
            phase_id=None,
            status=None
        )

    async def test_handle_execute_workflows_for_project(self):
        """Test executing workflows for a project."""
        args = {"project_id": "project-1", "workflow_type": "dagger_pipeline"}
        result = await self.integration._handle_execute_workflows_for_project(args)
        self.assertIn("content", result)
        self.assertEqual(len(result["content"]), 1)
        self.assertEqual(result["content"][0]["type"], "text")
        
        # Verify the workflow integration was called correctly
        self.workflow_integration.execute_workflows_for_project.assert_called_once_with(
            project_id="project-1",
            phase_id=None,
            status=None,
            workflow_type="dagger_pipeline",
            skip_cache=False
        )

    async def test_handle_list_workflow_templates(self):
        """Test listing workflow templates."""
        args = {}
        result = await self.integration._handle_list_workflow_templates(args)
        self.assertIn("content", result)
        self.assertEqual(len(result["content"]), 1)
        self.assertEqual(result["content"][0]["type"], "text")
        
        # Verify the template registry was called correctly
        self.template_registry.list_templates.assert_called_with(None)
        self.template_registry.get_categories.assert_called_once()

    async def test_handle_get_workflow_template(self):
        """Test getting a workflow template."""
        args = {"template_id": "template-1"}
        result = await self.integration._handle_get_workflow_template(args)
        self.assertIn("content", result)
        self.assertEqual(len(result["content"]), 1)
        self.assertEqual(result["content"][0]["type"], "text")
        
        # Verify the template registry was called correctly
        self.template_registry.get_template.assert_called_once_with("template-1")

    async def test_handle_create_workflow_from_template(self):
        """Test creating a workflow from a template."""
        args = {
            "task_id": "task-1",
            "template_id": "template-1",
            "parameters": {"param1": "value1"}
        }
        result = await self.integration._handle_create_workflow_from_template(args)
        self.assertIn("content", result)
        self.assertEqual(len(result["content"]), 1)
        self.assertEqual(result["content"][0]["type"], "text")
        
        # Verify the template registry and workflow integration were called correctly
        self.template_registry.get_template.assert_called_with("template-1")
        self.workflow_integration.create_workflow_from_template.assert_called_once()

    async def test_handle_dagger_workflow_resource(self):
        """Test handling Dagger workflow resources."""
        # Test workflows resource
        result = await self.integration._handle_dagger_workflow_resource("task-manager://dagger/workflows")
        self.assertIn("contents", result)
        self.assertEqual(len(result["contents"]), 1)
        self.assertEqual(result["contents"][0]["uri"], "task-manager://dagger/workflows")
        
        # Test stats resource
        result = await self.integration._handle_dagger_workflow_resource("task-manager://dagger/stats")
        self.assertIn("contents", result)
        self.assertEqual(len(result["contents"]), 1)
        self.assertEqual(result["contents"][0]["uri"], "task-manager://dagger/stats")
        
        # Test templates resource
        result = await self.integration._handle_dagger_workflow_resource("task-manager://dagger/templates")
        self.assertIn("contents", result)
        self.assertEqual(len(result["contents"]), 1)
        self.assertEqual(result["contents"][0]["uri"], "task-manager://dagger/templates")


def run_tests():
    """Run the tests."""
    loader = unittest.TestLoader()
    suite = loader.loadTestsFromTestCase(TestDaggerWorkflowIntegration)
    runner = unittest.TextTestRunner()
    runner.run(suite)


if __name__ == "__main__":
    # Run the tests using asyncio
    loop = asyncio.get_event_loop()
    for test_name in dir(TestDaggerWorkflowIntegration):
        if test_name.startswith("test_"):
            test_method = getattr(TestDaggerWorkflowIntegration, test_name)
            if asyncio.iscoroutinefunction(test_method):
                test_instance = TestDaggerWorkflowIntegration("setUp")
                test_instance.setUp()
                loop.run_until_complete(test_method(test_instance))
    
    print("All tests completed successfully!")
