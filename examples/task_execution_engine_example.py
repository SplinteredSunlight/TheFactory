"""
Example demonstrating the use of the Task Execution Engine.

This example shows how to:
1. Create tasks
2. Schedule tasks for execution
3. Schedule task dependencies
4. Monitor task execution status
5. Handle task results
"""

import asyncio
import logging
import os
import sys
import time
from datetime import datetime, timedelta

# Add the project root to the Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.task_manager.manager import get_task_manager, TaskStatus, TaskPriority
from src.task_manager.task_execution_engine import (
    get_task_execution_engine,
    TaskExecutionStatus,
    TaskExecutionPriority,
    RetryStrategy,
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


async def create_sample_tasks():
    """Create sample tasks for the example."""
    # Get the task manager
    task_manager = get_task_manager()
    
    # Create a project
    project = task_manager.create_project(
        name="Example Project",
        description="A project for demonstrating the Task Execution Engine",
    )
    
    # Create a phase
    phase = project.add_phase(
        phase_id="phase_1",
        name="Example Phase",
        description="A phase for demonstrating the Task Execution Engine",
    )
    
    # Create tasks
    tasks = []
    
    # Task 1: Data Preparation
    task1 = task_manager.create_task(
        name="Data Preparation",
        description="Prepare data for processing",
        project_id=project.id,
        phase_id=phase.id,
        priority=TaskPriority.HIGH,
        metadata={
            "workflow_type": "containerized_workflow",
            "container_image": "python:3.9-slim",
            "command": ["python", "-c", "print('Preparing data...'); import time; time.sleep(2); print('Data prepared!')"],
        },
    )
    tasks.append(task1)
    
    # Task 2: Data Processing (depends on Task 1)
    task2 = task_manager.create_task(
        name="Data Processing",
        description="Process the prepared data",
        project_id=project.id,
        phase_id=phase.id,
        priority=TaskPriority.MEDIUM,
        metadata={
            "workflow_type": "containerized_workflow",
            "container_image": "python:3.9-slim",
            "command": ["python", "-c", "print('Processing data...'); import time; time.sleep(3); print('Data processed!')"],
        },
    )
    tasks.append(task2)
    
    # Task 3: Data Analysis (depends on Task 2)
    task3 = task_manager.create_task(
        name="Data Analysis",
        description="Analyze the processed data",
        project_id=project.id,
        phase_id=phase.id,
        priority=TaskPriority.MEDIUM,
        metadata={
            "workflow_type": "containerized_workflow",
            "container_image": "python:3.9-slim",
            "command": ["python", "-c", "print('Analyzing data...'); import time; time.sleep(2); print('Data analyzed!')"],
        },
    )
    tasks.append(task3)
    
    # Task 4: Report Generation (depends on Task 3)
    task4 = task_manager.create_task(
        name="Report Generation",
        description="Generate a report from the analyzed data",
        project_id=project.id,
        phase_id=phase.id,
        priority=TaskPriority.LOW,
        metadata={
            "workflow_type": "containerized_workflow",
            "container_image": "python:3.9-slim",
            "command": ["python", "-c", "print('Generating report...'); import time; time.sleep(1); print('Report generated!')"],
        },
    )
    tasks.append(task4)
    
    return project, tasks


async def schedule_tasks_individually(tasks):
    """Schedule tasks individually with dependencies."""
    # Get the task execution engine
    engine = get_task_execution_engine()
    
    # Schedule tasks with dependencies
    execution_map = {}  # task_id -> execution_id
    
    # Schedule Task 1 (Data Preparation)
    result1 = await engine.schedule_task(
        task_id=tasks[0].id,
        workflow_type="containerized_workflow",
        priority=TaskExecutionPriority.HIGH,
        workflow_params={
            "inputs": {
                "container_image": tasks[0].metadata.get("container_image"),
                "command": tasks[0].metadata.get("command"),
            }
        },
        retry_strategy=RetryStrategy.EXPONENTIAL_BACKOFF,
        max_retries=2,
    )
    execution_map[tasks[0].id] = result1["execution_id"]
    logger.info(f"Scheduled task '{tasks[0].name}' with execution ID: {result1['execution_id']}")
    
    # Schedule Task 2 (Data Processing) - depends on Task 1
    result2 = await engine.schedule_task(
        task_id=tasks[1].id,
        workflow_type="containerized_workflow",
        priority=TaskExecutionPriority.MEDIUM,
        workflow_params={
            "inputs": {
                "container_image": tasks[1].metadata.get("container_image"),
                "command": tasks[1].metadata.get("command"),
            }
        },
        dependencies=[execution_map[tasks[0].id]],  # Depends on Task 1
        retry_strategy=RetryStrategy.EXPONENTIAL_BACKOFF,
        max_retries=2,
    )
    execution_map[tasks[1].id] = result2["execution_id"]
    logger.info(f"Scheduled task '{tasks[1].name}' with execution ID: {result2['execution_id']}")
    
    # Schedule Task 3 (Data Analysis) - depends on Task 2
    result3 = await engine.schedule_task(
        task_id=tasks[2].id,
        workflow_type="containerized_workflow",
        priority=TaskExecutionPriority.MEDIUM,
        workflow_params={
            "inputs": {
                "container_image": tasks[2].metadata.get("container_image"),
                "command": tasks[2].metadata.get("command"),
            }
        },
        dependencies=[execution_map[tasks[1].id]],  # Depends on Task 2
        retry_strategy=RetryStrategy.EXPONENTIAL_BACKOFF,
        max_retries=2,
    )
    execution_map[tasks[2].id] = result3["execution_id"]
    logger.info(f"Scheduled task '{tasks[2].name}' with execution ID: {result3['execution_id']}")
    
    # Schedule Task 4 (Report Generation) - depends on Task 3
    result4 = await engine.schedule_task(
        task_id=tasks[3].id,
        workflow_type="containerized_workflow",
        priority=TaskExecutionPriority.LOW,
        workflow_params={
            "inputs": {
                "container_image": tasks[3].metadata.get("container_image"),
                "command": tasks[3].metadata.get("command"),
            }
        },
        dependencies=[execution_map[tasks[2].id]],  # Depends on Task 3
        retry_strategy=RetryStrategy.EXPONENTIAL_BACKOFF,
        max_retries=2,
    )
    execution_map[tasks[3].id] = result4["execution_id"]
    logger.info(f"Scheduled task '{tasks[3].name}' with execution ID: {result4['execution_id']}")
    
    return execution_map


async def schedule_tasks_as_graph(tasks):
    """Schedule tasks as a dependency graph."""
    # Get the task execution engine
    engine = get_task_execution_engine()
    
    # Create a task graph
    task_graph = {
        tasks[0].id: [],  # Task 1 has no dependencies
        tasks[1].id: [tasks[0].id],  # Task 2 depends on Task 1
        tasks[2].id: [tasks[1].id],  # Task 3 depends on Task 2
        tasks[3].id: [tasks[2].id],  # Task 4 depends on Task 3
    }
    
    # Create workflow parameters for each task
    workflow_params = {}
    for task in tasks:
        workflow_params[task.id] = {
            "inputs": {
                "container_image": task.metadata.get("container_image"),
                "command": task.metadata.get("command"),
            }
        }
    
    # Schedule the task graph
    result = await engine.schedule_task_graph(
        task_graph=task_graph,
        workflow_type="containerized_workflow",
        workflow_params=workflow_params,
        retry_strategy=RetryStrategy.EXPONENTIAL_BACKOFF,
        max_retries=2,
    )
    
    # Create a map of task_id -> execution_id
    execution_map = {}
    for execution_info in result["executions"]:
        task_id = execution_info["task_id"]
        execution_id = execution_info["execution_id"]
        execution_map[task_id] = execution_id
        
        # Get the task name
        task_name = next((task.name for task in tasks if task.id == task_id), task_id)
        logger.info(f"Scheduled task '{task_name}' with execution ID: {execution_id}")
    
    logger.info(f"Task execution order: {result['task_order']}")
    
    return execution_map


async def monitor_executions(execution_map, tasks):
    """Monitor the status of task executions."""
    # Get the task execution engine
    engine = get_task_execution_engine()
    
    # Create a map of execution_id -> task_name for easier reference
    execution_to_task = {}
    for task in tasks:
        if task.id in execution_map:
            execution_to_task[execution_map[task.id]] = task.name
    
    # Monitor executions until all are complete
    all_complete = False
    while not all_complete:
        # Get status of all executions
        all_complete = True
        
        for execution_id, task_name in execution_to_task.items():
            # Get execution info
            execution_info = await engine.get_execution(execution_id)
            
            if not execution_info:
                logger.warning(f"Execution {execution_id} not found")
                continue
            
            status = execution_info["status"]
            
            # Check if execution is complete
            if status not in (TaskExecutionStatus.COMPLETED, TaskExecutionStatus.FAILED, TaskExecutionStatus.CANCELLED):
                all_complete = False
            
            # Log status
            logger.info(f"Task '{task_name}' (Execution {execution_id}): {status}")
            
            # If execution failed, log the error
            if status == TaskExecutionStatus.FAILED:
                logger.error(f"Task '{task_name}' failed: {execution_info.get('error')}")
            
            # If execution completed, log the result
            if status == TaskExecutionStatus.COMPLETED and execution_info.get("result"):
                logger.info(f"Task '{task_name}' result: {execution_info['result']}")
        
        # Get overall statistics
        stats = await engine.get_execution_stats()
        logger.info(f"Execution statistics: {stats}")
        
        # Wait before checking again
        if not all_complete:
            await asyncio.sleep(2)
    
    logger.info("All executions complete!")


async def main():
    """Main function for the example."""
    logger.info("Starting Task Execution Engine example")
    
    # Create sample tasks
    logger.info("Creating sample tasks")
    project, tasks = await create_sample_tasks()
    logger.info(f"Created project '{project.name}' with {len(tasks)} tasks")
    
    # Schedule tasks
    logger.info("Scheduling tasks as a dependency graph")
    execution_map = await schedule_tasks_as_graph(tasks)
    
    # Monitor executions
    logger.info("Monitoring task executions")
    await monitor_executions(execution_map, tasks)
    
    logger.info("Example complete!")


if __name__ == "__main__":
    # Run the example
    asyncio.run(main())
