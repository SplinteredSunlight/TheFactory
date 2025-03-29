"""
Simple test for the Dagger integration components.
"""
import os
import sys
import unittest
from unittest.mock import MagicMock, patch

# Add path to import modules from src
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Mock the imports
sys.modules['dagger'] = MagicMock()
sys.modules['pydagger'] = MagicMock()
sys.modules['pydagger'].Engine = MagicMock

# Now we can import our modules
from src.agent_manager.dagger_adapter import DaggerAdapterConfig
from src.orchestrator.engine import Workflow


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


class TestWorkflowDaggerExecution(unittest.TestCase):
    """Test Workflow Dagger execution."""
    
    def test_workflow_execute_with_default_engine(self):
        """Test that the workflow execute method uses the default engine when not specified."""
        workflow = Workflow(name="test-workflow")
        
        # Add some tasks to the workflow
        workflow.add_task(name="task1", agent="agent1")
        workflow.add_task(name="task2", agent="agent2")
        
        # Execute the workflow
        result = workflow.execute()
        
        self.assertEqual(result["workflow_id"], workflow.id)
        self.assertEqual(result["status"], "success")
        self.assertEqual(len(result["tasks"]), 2)
        self.assertIn("placeholder", result["results"])
    
    def test_workflow_execute_with_dagger_engine(self):
        """Test that the workflow execute method uses the Dagger engine when specified."""
        workflow = Workflow(name="test-workflow")
        
        # Add some tasks to the workflow
        workflow.add_task(name="task1", agent="agent1")
        workflow.add_task(name="task2", agent="agent2")
        
        # Mock the _execute_with_dagger method
        original_method = workflow._execute_with_dagger
        workflow._execute_with_dagger = MagicMock(return_value={"status": "success", "engine": "dagger"})
        
        # Execute the workflow with Dagger engine
        result = workflow.execute(engine_type="dagger")
        
        # Restore the original method
        workflow._execute_with_dagger = original_method
        
        self.assertEqual(result["status"], "success")
        self.assertEqual(result["engine"], "dagger")
    
    def test_get_tasks_in_execution_order_simple(self):
        """Test the _get_tasks_in_execution_order method with simple dependencies."""
        workflow = Workflow(name="test-workflow")
        
        # Add some tasks with dependencies
        task1_id = workflow.add_task(name="task1", agent="agent1")
        task2_id = workflow.add_task(name="task2", agent="agent2", depends_on=[task1_id])
        task3_id = workflow.add_task(name="task3", agent="agent3", depends_on=[task2_id])
        
        # Get tasks in execution order
        ordered_tasks = workflow._get_tasks_in_execution_order()
        
        # Check that tasks are in correct order
        self.assertEqual(len(ordered_tasks), 3)
        self.assertEqual(ordered_tasks[0].id, task1_id)
        self.assertEqual(ordered_tasks[1].id, task2_id)
        self.assertEqual(ordered_tasks[2].id, task3_id)


if __name__ == '__main__':
    unittest.main()