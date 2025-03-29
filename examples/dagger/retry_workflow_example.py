"""
Example demonstrating the retry mechanism for Dagger workflows.

This example shows how to configure and use the retry mechanism for handling
transient failures in Dagger workflow executions.
"""

import asyncio
import logging
from src.orchestrator.engine import OrchestrationEngine
from src.orchestrator.error_handling import IntegrationError

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def simulate_transient_failure(attempt):
    """Simulate a transient failure that succeeds after a few attempts."""
    if attempt < 2:
        logger.info(f"Attempt {attempt + 1}: Simulating a transient failure...")
        raise IntegrationError("Simulated transient failure", "INTEGRATION.CONNECTION_FAILED")
    else:
        logger.info(f"Attempt {attempt + 1}: Success!")
        return {"message": "Operation completed successfully"}


async def run_workflow_with_retry():
    """Run a workflow with retry for transient failures."""
    # Create an orchestration engine
    engine = OrchestrationEngine()
    
    # Create a workflow
    workflow = engine.create_workflow(
        name="retry_example_workflow",
        description="Example workflow demonstrating retry mechanism"
    )
    
    # Add tasks to the workflow
    task1_id = workflow.add_task(
        name="data_fetch",
        agent="data_fetcher",
        inputs={
            "url": "https://example.com/data",
            "format": "json"
        }
    )
    
    task2_id = workflow.add_task(
        name="data_process",
        agent="data_processor",
        inputs={
            "operation": "transform",
            "schema": {
                "fields": ["name", "value", "timestamp"]
            }
        },
        depends_on=[task1_id]
    )
    
    # Configure retry parameters
    retry_config = {
        "max_retries": 3,                # Maximum number of retry attempts
        "retry_backoff_factor": 0.5,     # Exponential backoff factor
        "retry_jitter": True,            # Add jitter to avoid thundering herd
        "enable_retry": True             # Enable retry mechanism
    }
    
    # Execute the workflow with Dagger and retry configuration
    logger.info("Executing workflow with retry mechanism...")
    result = await engine.execute_workflow(
        workflow_id=workflow.id,
        engine_type="dagger",
        container_registry="docker.io",
        workflow_directory="workflows",
        **retry_config
    )
    
    logger.info(f"Workflow execution result: {result}")
    return result


async def run_workflow_without_retry():
    """Run a workflow without retry for comparison."""
    # Create an orchestration engine
    engine = OrchestrationEngine()
    
    # Create a workflow
    workflow = engine.create_workflow(
        name="no_retry_example_workflow",
        description="Example workflow without retry mechanism"
    )
    
    # Add a task to the workflow
    workflow.add_task(
        name="data_fetch",
        agent="data_fetcher",
        inputs={
            "url": "https://example.com/data",
            "format": "json"
        }
    )
    
    # Execute the workflow with Dagger but disable retry
    logger.info("Executing workflow without retry mechanism...")
    result = await engine.execute_workflow(
        workflow_id=workflow.id,
        engine_type="dagger",
        container_registry="docker.io",
        workflow_directory="workflows",
        enable_retry=False  # Disable retry mechanism
    )
    
    logger.info(f"Workflow execution result: {result}")
    return result


async def main():
    """Run the example."""
    logger.info("=== Dagger Workflow Retry Mechanism Example ===")
    
    # Example 1: Workflow with retry mechanism
    logger.info("\n=== Example 1: Workflow with retry mechanism ===")
    try:
        await run_workflow_with_retry()
    except Exception as e:
        logger.error(f"Error in workflow with retry: {e}")
    
    # Example 2: Workflow without retry mechanism
    logger.info("\n=== Example 2: Workflow without retry mechanism ===")
    try:
        await run_workflow_without_retry()
    except Exception as e:
        logger.error(f"Error in workflow without retry: {e}")
    
    logger.info("\n=== Example complete ===")


if __name__ == "__main__":
    asyncio.run(main())
