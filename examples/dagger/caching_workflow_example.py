"""
Example demonstrating caching in Dagger workflows.

This example shows how to use and configure the caching mechanism for Dagger workflows
to improve performance by reusing results from previous executions.
"""

import asyncio
import logging
import time
import os
import json
from src.orchestrator.engine import OrchestrationEngine
from src.agent_manager.dagger_adapter import DaggerAdapter, DaggerAdapterConfig

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def run_workflow_with_caching():
    """Run a workflow with caching enabled."""
    # Create an orchestration engine
    engine = OrchestrationEngine()
    
    # Create a workflow
    workflow = engine.create_workflow(
        name="caching_example_workflow",
        description="Example workflow demonstrating caching mechanism"
    )
    
    # Add tasks to the workflow
    task1_id = workflow.add_task(
        name="expensive_computation",
        agent="data_processor",
        inputs={
            "operation": "compute",
            "data": [1, 2, 3, 4, 5]
        }
    )
    
    task2_id = workflow.add_task(
        name="format_results",
        agent="formatter",
        inputs={
            "format": "json",
            "pretty_print": True
        },
        depends_on=[task1_id]
    )
    
    # Configure caching parameters
    cache_config = {
        "caching_enabled": True,
        "cache_directory": "./.dagger_cache",
        "cache_ttl_seconds": 3600  # 1 hour
    }
    
    # Execute the workflow with Dagger and caching configuration
    logger.info("Executing workflow with caching enabled (first run)...")
    start_time = time.time()
    result1 = await engine.execute_workflow(
        workflow_id=workflow.id,
        engine_type="dagger",
        container_registry="docker.io",
        workflow_directory="workflows",
        **cache_config
    )
    execution_time1 = time.time() - start_time
    
    logger.info(f"First execution completed in {execution_time1:.2f} seconds")
    logger.info(f"Result: {result1}")
    
    # Execute the same workflow again - should use cached results
    logger.info("\nExecuting the same workflow again (should use cache)...")
    start_time = time.time()
    result2 = await engine.execute_workflow(
        workflow_id=workflow.id,
        engine_type="dagger",
        container_registry="docker.io",
        workflow_directory="workflows",
        **cache_config
    )
    execution_time2 = time.time() - start_time
    
    logger.info(f"Second execution completed in {execution_time2:.2f} seconds")
    logger.info(f"Result: {result2}")
    logger.info(f"Performance improvement: {(execution_time1 / execution_time2):.2f}x faster")
    
    return result1, result2, execution_time1, execution_time2


async def run_workflow_with_cache_control():
    """Run a workflow with explicit cache control."""
    # Create an orchestration engine
    engine = OrchestrationEngine()
    
    # Create a workflow
    workflow = engine.create_workflow(
        name="cache_control_workflow",
        description="Example workflow demonstrating cache control"
    )
    
    # Add a task with cache control
    workflow.add_task(
        name="controlled_task",
        agent="data_processor",
        inputs={
            "operation": "compute",
            "data": [1, 2, 3, 4, 5],
            "skip_cache": True  # Explicitly skip cache for this task
        }
    )
    
    # Configure caching parameters
    cache_config = {
        "caching_enabled": True,
        "cache_directory": "./.dagger_cache",
        "cache_ttl_seconds": 3600  # 1 hour
    }
    
    # Execute the workflow with cache skipping
    logger.info("\nExecuting workflow with cache skipping...")
    result = await engine.execute_workflow(
        workflow_id=workflow.id,
        engine_type="dagger",
        container_registry="docker.io",
        workflow_directory="workflows",
        **cache_config
    )
    
    logger.info(f"Result: {result}")
    return result


async def examine_cache():
    """Examine the cache directory and contents."""
    cache_dir = "./.dagger_cache"
    cache_file = os.path.join(cache_dir, "cache.json")
    
    if os.path.exists(cache_file):
        with open(cache_file, "r") as f:
            cache_data = json.load(f)
        
        logger.info(f"\nCache file found at {cache_file}")
        logger.info(f"Number of cache entries: {len(cache_data)}")
        
        # Print some information about the cache entries
        for key, entry in cache_data.items():
            logger.info(f"Cache key: {key[:8]}... (truncated)")
            logger.info(f"  Expiry: {time.ctime(entry.get('expiry', 0))}")
            logger.info(f"  Timestamp: {time.ctime(entry.get('timestamp', 0))}")
    else:
        logger.info(f"\nNo cache file found at {cache_file}")


async def main():
    """Run the example."""
    logger.info("=== Dagger Workflow Caching Example ===")
    
    # Example 1: Basic caching
    logger.info("\n=== Example 1: Basic caching ===")
    try:
        result1, result2, time1, time2 = await run_workflow_with_caching()
        logger.info(f"Cache effectiveness: {(time1 / time2):.2f}x faster on second run")
    except Exception as e:
        logger.error(f"Error in workflow with caching: {e}")
    
    # Example 2: Cache control
    logger.info("\n=== Example 2: Cache control ===")
    try:
        await run_workflow_with_cache_control()
    except Exception as e:
        logger.error(f"Error in workflow with cache control: {e}")
    
    # Examine the cache
    logger.info("\n=== Cache examination ===")
    try:
        await examine_cache()
    except Exception as e:
        logger.error(f"Error examining cache: {e}")
    
    logger.info("\n=== Example complete ===")


if __name__ == "__main__":
    asyncio.run(main())
