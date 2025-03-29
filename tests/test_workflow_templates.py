#!/usr/bin/env python3
"""
Test script for the workflow templates feature.

This script tests the workflow templates functionality in the Dagger Workflow Integration.
"""

import asyncio
import json
import os
import sys
import logging
import unittest
from datetime import datetime

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# Add the project root to the Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Import the workflow templates module
from src.task_manager.mcp_servers.workflow_templates import (
    WorkflowTemplate,
    WorkflowTemplateRegistry,
    get_template_registry
)


class TestWorkflowTemplates(unittest.TestCase):
    """Test cases for the workflow templates feature."""
    
    def setUp(self):
        """Set up the test environment."""
        # Create a temporary directory for templates
        self.temp_dir = os.path.join(os.path.dirname(__file__), "temp_templates")
        os.makedirs(self.temp_dir, exist_ok=True)
        
        # Create a template registry
        self.registry = WorkflowTemplateRegistry(self.temp_dir)
    
    def tearDown(self):
        """Clean up the test environment."""
        # Remove temporary files
        for filename in os.listdir(self.temp_dir):
            file_path = os.path.join(self.temp_dir, filename)
            if os.path.isfile(file_path):
                os.unlink(file_path)
        
        # Remove the temporary directory
        os.rmdir(self.temp_dir)
    
    def test_template_creation(self):
        """Test creating a workflow template."""
        # Create a template
        template = WorkflowTemplate(
            template_id="test_template",
            name="Test Template",
            description="A test template",
            category="test",
            version="1.0.0",
            parameters={"param1": "value1", "param2": "value2"},
            stages=[
                {
                    "id": "stage1",
                    "name": "Stage 1",
                    "description": "First stage",
                    "agent": "agent1",
                    "inputs": {
                        "input1": "${parameters.param1}",
                        "input2": "value2"
                    }
                },
                {
                    "id": "stage2",
                    "name": "Stage 2",
                    "description": "Second stage",
                    "agent": "agent2",
                    "depends_on": ["stage1"],
                    "inputs": {
                        "input1": "${parameters.param2}",
                        "input2": "value2"
                    }
                }
            ],
            metadata={"tags": ["test", "example"]}
        )
        
        # Check template properties
        self.assertEqual(template.template_id, "test_template")
        self.assertEqual(template.name, "Test Template")
        self.assertEqual(template.description, "A test template")
        self.assertEqual(template.category, "test")
        self.assertEqual(template.version, "1.0.0")
        self.assertEqual(template.parameters, {"param1": "value1", "param2": "value2"})
        self.assertEqual(len(template.stages), 2)
        self.assertEqual(template.metadata, {"tags": ["test", "example"]})
    
    def test_template_serialization(self):
        """Test serializing and deserializing a template."""
        # Create a template
        template = WorkflowTemplate(
            template_id="test_template",
            name="Test Template",
            description="A test template",
            category="test",
            version="1.0.0",
            parameters={"param1": "value1", "param2": "value2"},
            stages=[
                {
                    "id": "stage1",
                    "name": "Stage 1",
                    "description": "First stage",
                    "agent": "agent1",
                    "inputs": {
                        "input1": "${parameters.param1}",
                        "input2": "value2"
                    }
                }
            ],
            metadata={"tags": ["test", "example"]}
        )
        
        # Convert to dictionary
        template_dict = template.to_dict()
        
        # Create a new template from the dictionary
        new_template = WorkflowTemplate.from_dict(template_dict)
        
        # Check that the new template is the same as the original
        self.assertEqual(new_template.template_id, template.template_id)
        self.assertEqual(new_template.name, template.name)
        self.assertEqual(new_template.description, template.description)
        self.assertEqual(new_template.category, template.category)
        self.assertEqual(new_template.version, template.version)
        self.assertEqual(new_template.parameters, template.parameters)
        self.assertEqual(len(new_template.stages), len(template.stages))
        self.assertEqual(new_template.metadata, template.metadata)
    
    def test_template_yaml_serialization(self):
        """Test serializing and deserializing a template to/from YAML."""
        # Create a template
        template = WorkflowTemplate(
            template_id="test_template",
            name="Test Template",
            description="A test template",
            category="test",
            version="1.0.0",
            parameters={"param1": "value1", "param2": "value2"},
            stages=[
                {
                    "id": "stage1",
                    "name": "Stage 1",
                    "description": "First stage",
                    "agent": "agent1",
                    "inputs": {
                        "input1": "${parameters.param1}",
                        "input2": "value2"
                    }
                }
            ],
            metadata={"tags": ["test", "example"]}
        )
        
        # Convert to YAML
        yaml_str = template.to_yaml()
        
        # Create a new template from the YAML
        new_template = WorkflowTemplate.from_yaml(yaml_str)
        
        # Check that the new template is the same as the original
        self.assertEqual(new_template.template_id, template.template_id)
        self.assertEqual(new_template.name, template.name)
        self.assertEqual(new_template.description, template.description)
        self.assertEqual(new_template.category, template.category)
        self.assertEqual(new_template.version, template.version)
        self.assertEqual(new_template.parameters, template.parameters)
        self.assertEqual(len(new_template.stages), len(template.stages))
        self.assertEqual(new_template.metadata, template.metadata)
    
    def test_template_yaml_file_serialization(self):
        """Test serializing and deserializing a template to/from a YAML file."""
        # Create a template
        template = WorkflowTemplate(
            template_id="test_template",
            name="Test Template",
            description="A test template",
            category="test",
            version="1.0.0",
            parameters={"param1": "value1", "param2": "value2"},
            stages=[
                {
                    "id": "stage1",
                    "name": "Stage 1",
                    "description": "First stage",
                    "agent": "agent1",
                    "inputs": {
                        "input1": "${parameters.param1}",
                        "input2": "value2"
                    }
                }
            ],
            metadata={"tags": ["test", "example"]}
        )
        
        # Save to a YAML file
        file_path = os.path.join(self.temp_dir, "test_template.yaml")
        template.to_yaml_file(file_path)
        
        # Create a new template from the YAML file
        new_template = WorkflowTemplate.from_yaml_file(file_path)
        
        # Check that the new template is the same as the original
        self.assertEqual(new_template.template_id, template.template_id)
        self.assertEqual(new_template.name, template.name)
        self.assertEqual(new_template.description, template.description)
        self.assertEqual(new_template.category, template.category)
        self.assertEqual(new_template.version, template.version)
        self.assertEqual(new_template.parameters, template.parameters)
        self.assertEqual(len(new_template.stages), len(template.stages))
        self.assertEqual(new_template.metadata, template.metadata)
    
    def test_template_customization(self):
        """Test customizing a template."""
        # Create a template
        template = WorkflowTemplate(
            template_id="test_template",
            name="Test Template",
            description="A test template",
            category="test",
            version="1.0.0",
            parameters={"param1": "value1", "param2": "value2"},
            stages=[
                {
                    "id": "stage1",
                    "name": "Stage 1",
                    "description": "First stage",
                    "agent": "agent1",
                    "inputs": {
                        "input1": "${parameters.param1}",
                        "input2": "value2"
                    }
                }
            ],
            metadata={"tags": ["test", "example"]}
        )
        
        # Customize the template
        custom_params = {"param1": "custom_value1", "param3": "value3"}
        custom_template = template.customize(custom_params)
        
        # Check that the custom template has the custom parameters
        self.assertEqual(custom_template.parameters["param1"], "custom_value1")
        self.assertEqual(custom_template.parameters["param2"], "value2")
        self.assertEqual(custom_template.parameters["param3"], "value3")
        
        # Check that the original template is unchanged
        self.assertEqual(template.parameters["param1"], "value1")
        self.assertEqual(template.parameters["param2"], "value2")
        self.assertNotIn("param3", template.parameters)
        
        # Check that the custom template has a different ID
        self.assertNotEqual(custom_template.template_id, template.template_id)
        self.assertTrue(custom_template.template_id.startswith(f"{template.template_id}_custom_"))
        
        # Check that the custom template has metadata about customization
        self.assertEqual(custom_template.metadata["customized_from"], template.template_id)
        self.assertIn("customized_at", custom_template.metadata)
    
    def test_template_parameter_substitution(self):
        """Test parameter substitution in template stages."""
        # Create a template
        template = WorkflowTemplate(
            template_id="test_template",
            name="Test Template",
            description="A test template",
            category="test",
            version="1.0.0",
            parameters={"param1": "value1", "param2": "value2"},
            stages=[
                {
                    "id": "stage1",
                    "name": "Stage 1",
                    "description": "First stage",
                    "agent": "agent1",
                    "inputs": {
                        "input1": "${parameters.param1}",
                        "input2": "value2"
                    }
                }
            ],
            metadata={"tags": ["test", "example"]}
        )
        
        # Create a workflow definition
        workflow_def = template.create_workflow_definition("task_123")
        
        # Check that the parameters are substituted
        self.assertEqual(workflow_def["task_id"], "task_123")
        self.assertEqual(workflow_def["name"], "Test Template for Task task_123")
        self.assertEqual(workflow_def["description"], "A test template")
        self.assertEqual(workflow_def["template_id"], "test_template")
        self.assertEqual(workflow_def["parameters"], {"param1": "value1", "param2": "value2"})
        self.assertEqual(len(workflow_def["stages"]), 1)
        
        # Check that the parameters are substituted in the stages
        stage = workflow_def["stages"][0]
        self.assertEqual(stage["id"], "stage1")
        self.assertEqual(stage["name"], "Stage 1")
        self.assertEqual(stage["description"], "First stage")
        self.assertEqual(stage["agent"], "agent1")
        self.assertEqual(stage["inputs"]["input1"], "${parameters.param1}")  # Not substituted yet
        self.assertEqual(stage["inputs"]["input2"], "value2")
        
        # Check that the metadata is set
        self.assertEqual(workflow_def["metadata"]["created_from_template"], "test_template")
        self.assertIn("created_at", workflow_def["metadata"])
        self.assertEqual(workflow_def["metadata"]["template_version"], "1.0.0")
    
    def test_template_registry(self):
        """Test the template registry."""
        # Create a template
        template = WorkflowTemplate(
            template_id="test_template",
            name="Test Template",
            description="A test template",
            category="test",
            version="1.0.0",
            parameters={"param1": "value1", "param2": "value2"},
            stages=[
                {
                    "id": "stage1",
                    "name": "Stage 1",
                    "description": "First stage",
                    "agent": "agent1",
                    "inputs": {
                        "input1": "${parameters.param1}",
                        "input2": "value2"
                    }
                }
            ],
            metadata={"tags": ["test", "example"]}
        )
        
        # Register the template
        self.registry.register_template(template)
        
        # Get the template
        retrieved_template = self.registry.get_template("test_template")
        
        # Check that the retrieved template is the same as the original
        self.assertEqual(retrieved_template.template_id, template.template_id)
        self.assertEqual(retrieved_template.name, template.name)
        self.assertEqual(retrieved_template.description, template.description)
        self.assertEqual(retrieved_template.category, template.category)
        self.assertEqual(retrieved_template.version, template.version)
        self.assertEqual(retrieved_template.parameters, template.parameters)
        self.assertEqual(len(retrieved_template.stages), len(template.stages))
        self.assertEqual(retrieved_template.metadata, template.metadata)
        
        # List templates
        templates = self.registry.list_templates()
        
        # Check that the template is in the list
        self.assertEqual(len(templates), 1)
        self.assertEqual(templates[0]["template_id"], "test_template")
        self.assertEqual(templates[0]["name"], "Test Template")
        self.assertEqual(templates[0]["description"], "A test template")
        self.assertEqual(templates[0]["category"], "test")
        self.assertEqual(templates[0]["version"], "1.0.0")
        
        # Get categories
        categories = self.registry.get_categories()
        
        # Check that the category is in the list
        self.assertEqual(len(categories), 1)
        self.assertEqual(categories[0], "test")
        
        # Save the template
        self.registry.save_template(template)
        
        # Check that the template was saved
        file_path = os.path.join(self.temp_dir, "test_template.yaml")
        self.assertTrue(os.path.exists(file_path))
        
        # Create a new registry and check that it loads the template
        new_registry = WorkflowTemplateRegistry(self.temp_dir)
        new_template = new_registry.get_template("test_template")
        
        # Check that the new template is the same as the original
        self.assertEqual(new_template.template_id, template.template_id)
        self.assertEqual(new_template.name, template.name)
        self.assertEqual(new_template.description, template.description)
        self.assertEqual(new_template.category, template.category)
        self.assertEqual(new_template.version, template.version)
        self.assertEqual(new_template.parameters, template.parameters)
        self.assertEqual(len(new_template.stages), len(template.stages))
        self.assertEqual(new_template.metadata, template.metadata)
    
    def test_builtin_templates(self):
        """Test the built-in templates."""
        # Get the global template registry
        registry = get_template_registry()
        
        # Check that the built-in templates are registered
        cicd_template = registry.get_template("cicd_pipeline")
        self.assertIsNotNone(cicd_template)
        self.assertEqual(cicd_template.name, "CI/CD Pipeline")
        self.assertEqual(cicd_template.category, "deployment")
        
        data_template = registry.get_template("data_processing")
        self.assertIsNotNone(data_template)
        self.assertEqual(data_template.name, "Data Processing Pipeline")
        self.assertEqual(data_template.category, "data")
        
        ml_template = registry.get_template("ml_training")
        self.assertIsNotNone(ml_template)
        self.assertEqual(ml_template.name, "ML Training Pipeline")
        self.assertEqual(ml_template.category, "machine_learning")
        
        maintenance_template = registry.get_template("scheduled_maintenance")
        self.assertIsNotNone(maintenance_template)
        self.assertEqual(maintenance_template.name, "Scheduled Maintenance")
        self.assertEqual(maintenance_template.category, "operations")
        
        # Check that the categories are correct
        categories = registry.get_categories()
        self.assertIn("deployment", categories)
        self.assertIn("data", categories)
        self.assertIn("machine_learning", categories)
        self.assertIn("operations", categories)


if __name__ == "__main__":
    unittest.main()
