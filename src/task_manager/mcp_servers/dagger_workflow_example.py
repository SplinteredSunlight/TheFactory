#!/usr/bin/env python3
"""
Example script for using the Dagger Workflow Integration.

This script demonstrates how to use the Dagger Workflow Integration to create and execute workflows.
"""

import os
import json
import logging
import argparse
from typing import Dict, Any, Optional

from workflow_templates import (
    WorkflowTemplate,
    get_template_registry,
)
from dagger_workflow_integration import (
    DaggerWorkflowIntegration,
)

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


def create_custom_template() -> WorkflowTemplate:
    """Create a custom workflow template for demonstration."""
    return WorkflowTemplate(
        template_id="custom_example",
        name="Custom Example Workflow",
        description="A custom example workflow for demonstration",
        category="example",
        version="1.0.0",
        parameters={
            "input_file": "data.csv",
            "output_dir": "/tmp/output",
            "threshold": 0.5,
        },
        stages=[
            {
                "id": "prepare",
                "name": "Prepare Data",
                "description": "Prepare the input data",
                "agent": "data_preparer",
                "inputs": {
                    "input_file": "${parameters.input_file}",
                    "output_dir": "${parameters.output_dir}",
                }
            },
            {
                "id": "process",
                "name": "Process Data",
                "description": "Process the prepared data",
                "agent": "data_processor",
                "depends_on": ["prepare"],
                "inputs": {
                    "input_dir": "${parameters.output_dir}",
                    "threshold": "${parameters.threshold}",
                    "prepared_file": "${stages.prepare.outputs.result}",
                }
            },
            {
                "id": "analyze",
                "name": "Analyze Results",
                "description": "Analyze the processing results",
                "agent": "data_analyzer",
                "depends_on": ["process"],
                "inputs": {
                    "input_file": "${stages.process.outputs.result}",
                    "output_dir": "${parameters.output_dir}",
                }
            }
        ],
        metadata={
            "tags": ["example", "demo"],
            "complexity": "low",
            "estimated_duration": "5m"
        }
    )


def create_and_execute_workflow(
    template_id: str,
    task_id: str,
    parameters: Optional[Dict[str, Any]] = None,
    templates_dir: Optional[str] = None
) -> Dict[str, Any]:
    """
    Create and execute a workflow from a template.
    
    Args:
        template_id: ID of the template to use
        task_id: ID of the task to create a workflow for
        parameters: Custom parameters to override defaults
        templates_dir: Directory containing workflow templates
        
    Returns:
        Workflow execution result
    """
    # Initialize the Dagger workflow integration
    integration = DaggerWorkflowIntegration(templates_dir=templates_dir)
    
    # Register a custom template if it doesn't exist
    if template_id == "custom_example" and not integration.get_template(template_id):
        template = create_custom_template()
        integration.save_workflow_template(template)
    
    # List available templates
    logger.info("Available templates:")
    for template in integration.list_templates():
        logger.info(f"  - {template['template_id']}: {template['name']} ({template['category']})")
    
    # Create a workflow from the template
    logger.info(f"Creating workflow from template {template_id} for task {task_id}")
    workflow = integration.create_workflow(template_id, task_id, parameters)
    workflow_id = workflow["workflow_id"]
    
    # Print workflow details
    logger.info(f"Created workflow {workflow_id}")
    logger.info(f"Workflow name: {workflow['name']}")
    logger.info(f"Workflow description: {workflow['description']}")
    logger.info(f"Workflow parameters: {json.dumps(workflow['parameters'], indent=2)}")
    logger.info(f"Workflow stages: {len(workflow['stages'])}")
    
    # Execute the workflow
    logger.info(f"Executing workflow {workflow_id}")
    result = integration.execute_workflow(workflow_id)
    
    # Print workflow status
    status = integration.get_workflow_status(workflow_id)
    logger.info(f"Workflow status: {status['status']}")
    if status['status'] == "completed":
        logger.info(f"Workflow completed at: {status['completed_at']}")
    elif status['status'] == "failed":
        logger.error(f"Workflow failed: {status.get('error', 'Unknown error')}")
    
    # Print stage statuses
    logger.info("Stage statuses:")
    for stage_id, stage_status in status["stages"].items():
        logger.info(f"  - {stage_id}: {stage_status['status']}")
        if stage_status['status'] == "failed":
            logger.error(f"    Error: {stage_status.get('error', 'Unknown error')}")
    
    return result


def main():
    """Main function."""
    parser = argparse.ArgumentParser(description="Dagger Workflow Integration Example")
    parser.add_argument(
        "--template",
        default="custom_example",
        help="Template ID to use (default: custom_example)"
    )
    parser.add_argument(
        "--task",
        default="example_task_001",
        help="Task ID to create a workflow for (default: example_task_001)"
    )
    parser.add_argument(
        "--templates-dir",
        default=os.path.join(os.path.dirname(__file__), "templates"),
        help="Directory containing workflow templates"
    )
    parser.add_argument(
        "--param",
        action="append",
        default=[],
        help="Custom parameters in the format key=value (can be used multiple times)"
    )
    
    args = parser.parse_args()
    
    # Parse custom parameters
    parameters = {}
    for param in args.param:
        if "=" in param:
            key, value = param.split("=", 1)
            parameters[key] = value
    
    # Create templates directory if it doesn't exist
    os.makedirs(args.templates_dir, exist_ok=True)
    
    # Create and execute workflow
    result = create_and_execute_workflow(
        template_id=args.template,
        task_id=args.task,
        parameters=parameters,
        templates_dir=args.templates_dir
    )
    
    # Print result
    logger.info(f"Workflow execution result: {json.dumps(result, indent=2)}")


if __name__ == "__main__":
    main()
