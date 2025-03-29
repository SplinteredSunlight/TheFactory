#!/usr/bin/env python3
"""
Verify Dagger Workflow Integration

This script verifies that the Dagger Workflow Integration is working properly.
It creates a sample project and task, then creates and executes a Dagger workflow for the task.
"""

import asyncio
import json
import os
import sys
import logging
from datetime import datetime

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# Add the project root to the Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Import the task manager and workflow integration
from src.task_manager.manager import get_task_manager, TaskStatus
from src.task_manager.dagger_integration import get_task_workflow_integration


async def verify_integration():
    """Verify that the Dagger Workflow Integration is working properly."""
    logger.info("Verifying Dagger Workflow Integration...")
    
    # Initialize the task manager
    data_dir = os.environ.get("TASK_MANAGER_DATA_DIR")
    task_manager = get_task_manager(data_dir)
    
    # Initialize the workflow integration
    dagger_config_path = os.environ.get("TASK_MANAGER_DAGGER_CONFIG")
    workflow_integration = get_task_workflow_integration(dagger_config_path)
    
    # Create a verification project
    logger.info("Creating verification project...")
    project = task_manager.create_project(
        name="Dagger Verification Project",
        description="A project for verifying the Dagger Workflow Integration",
        metadata={
            "created_at": datetime.now().isoformat(),
            "verification": True,
        },
    )
    
    # Create a verification task
    logger.info("Creating verification task...")
    task = task_manager.create_task(
        name="Dagger Verification Task",
        description="A task for verifying the Dagger Workflow Integration",
        project_id=project.id,
        status="planned",
        priority="medium",
        metadata={
            "verification": True,
            "workflow_inputs": {
                "input1": "value1",
                "input2": "value2",
            },
        },
    )
    
    # Create a workflow for the task
    logger.info(f"Creating workflow for task {task.id}...")
    try:
        workflow_info = await workflow_integration.create_workflow_from_task(
            task_id=task.id,
            workflow_name="Verification Workflow",
        )
        logger.info(f"Successfully created workflow: {json.dumps(workflow_info, indent=2)}")
    except Exception as e:
        logger.error(f"Failed to create workflow: {e}")
        return False
    
    # Get the workflow status
    logger.info(f"Getting workflow status for task {task.id}...")
    try:
        status = await workflow_integration.get_workflow_status(task_id=task.id)
        logger.info(f"Successfully got workflow status: {json.dumps(status, indent=2)}")
    except Exception as e:
        logger.error(f"Failed to get workflow status: {e}")
        return False
    
    # Execute the workflow
    logger.info(f"Executing workflow for task {task.id}...")
    try:
        execution_result = await workflow_integration.execute_task_workflow(
            task_id=task.id,
            workflow_type="containerized_workflow",
        )
        logger.info(f"Successfully executed workflow: {json.dumps(execution_result, indent=2)}")
    except Exception as e:
        logger.error(f"Failed to execute workflow: {e}")
        return False
    
    # Get the updated workflow status
    logger.info(f"Getting updated workflow status for task {task.id}...")
    try:
        status = await workflow_integration.get_workflow_status(task_id=task.id)
        logger.info(f"Successfully got updated workflow status: {json.dumps(status, indent=2)}")
    except Exception as e:
        logger.error(f"Failed to get updated workflow status: {e}")
        return False
    
    # Clean up
    logger.info("Cleaning up...")
    try:
        # Delete the task
        task_manager.delete_task(task.id)
        
        # Delete the project
        task_manager.delete_project(project.id)
    except Exception as e:
        logger.error(f"Failed to clean up: {e}")
        # Continue anyway
    
    # Shutdown the workflow integration
    logger.info("Shutting down workflow integration...")
    await workflow_integration.shutdown()
    
    logger.info("Verification completed successfully!")
    return True


def main():
    """Run the verification."""
    # Check if Dagger is enabled
    if not os.environ.get("TASK_MANAGER_DAGGER_ENABLED", "").lower() in ("1", "true", "yes"):
        logger.error("Dagger is not enabled. Set TASK_MANAGER_DAGGER_ENABLED=1 to enable it.")
        sys.exit(1)
    
    # Check if Dagger config is specified
    if not os.environ.get("TASK_MANAGER_DAGGER_CONFIG"):
        logger.warning("Dagger config not specified. Using default config.")
    
    try:
        # Run the verification
        success = asyncio.run(verify_integration())
        
        if success:
            logger.info("Verification succeeded!")
            sys.exit(0)
        else:
            logger.error("Verification failed!")
            sys.exit(1)
    except KeyboardInterrupt:
        logger.info("Verification interrupted by user")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Error during verification: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
