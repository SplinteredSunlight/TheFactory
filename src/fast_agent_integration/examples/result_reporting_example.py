#!/usr/bin/env python3
"""
Result Reporting System Example

This example demonstrates how to use the Result Reporting System to report
various types of results from agents back to the AI-Orchestration-Platform.
"""

import asyncio
import logging
import os
import sys
import time
from datetime import datetime
from typing import Dict, Any

# Add the project root to the Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../")))

from src.fast_agent_integration.result_reporting import (
    get_result_reporting_client,
    ResultType,
    ResultSeverity
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


async def simulate_task_execution(agent_id: str, task_id: str) -> None:
    """
    Simulate a task execution with progress updates and final result.
    
    Args:
        agent_id: ID of the agent executing the task
        task_id: ID of the task being executed
    """
    # Get the result reporting client
    result_reporter = await get_result_reporting_client(agent_id=agent_id)
    
    logger.info(f"Agent {agent_id} starting task {task_id}")
    
    # Report agent status as busy
    await result_reporter.report_agent_status(
        is_online=True,
        current_load=1
    )
    
    # Report task progress (0%)
    await result_reporter.report_task_progress(
        task_id=task_id,
        progress_data={
            "percent_complete": 0,
            "message": "Task started",
            "stage": "initialization"
        }
    )
    
    # Simulate work (25%)
    await asyncio.sleep(1)
    await result_reporter.report_task_progress(
        task_id=task_id,
        progress_data={
            "percent_complete": 25,
            "message": "Processing data",
            "stage": "data_processing"
        }
    )
    
    # Report some metrics
    await result_reporter.report_agent_metrics(
        metrics={
            "memory_usage_mb": 256,
            "cpu_usage_percent": 15,
            "active_tasks": 1
        }
    )
    
    # Simulate more work (50%)
    await asyncio.sleep(1)
    await result_reporter.report_task_progress(
        task_id=task_id,
        progress_data={
            "percent_complete": 50,
            "message": "Analyzing results",
            "stage": "analysis"
        }
    )
    
    # Log some information
    await result_reporter.report_agent_log(
        log_message="Analysis phase completed successfully",
        severity=ResultSeverity.INFO,
        log_context={
            "task_id": task_id,
            "stage": "analysis",
            "duration_ms": 1050
        }
    )
    
    # Simulate more work (75%)
    await asyncio.sleep(1)
    await result_reporter.report_task_progress(
        task_id=task_id,
        progress_data={
            "percent_complete": 75,
            "message": "Generating report",
            "stage": "report_generation"
        }
    )
    
    # Simulate final work (100%)
    await asyncio.sleep(1)
    await result_reporter.report_task_progress(
        task_id=task_id,
        progress_data={
            "percent_complete": 100,
            "message": "Task completed",
            "stage": "completion"
        }
    )
    
    # Report task completion
    await result_reporter.report_task_completion(
        task_id=task_id,
        result_data={
            "summary": "Task completed successfully",
            "execution_time_ms": 4000,
            "output": {
                "report_url": "https://example.com/reports/12345",
                "items_processed": 1000,
                "success_rate": 0.99
            }
        }
    )
    
    # Report agent status as idle
    await result_reporter.report_agent_status(
        is_online=True,
        current_load=0
    )
    
    logger.info(f"Agent {agent_id} completed task {task_id}")


async def simulate_task_error(agent_id: str, task_id: str) -> None:
    """
    Simulate a task execution that encounters an error.
    
    Args:
        agent_id: ID of the agent executing the task
        task_id: ID of the task being executed
    """
    # Get the result reporting client
    result_reporter = await get_result_reporting_client(agent_id=agent_id)
    
    logger.info(f"Agent {agent_id} starting task {task_id} (will fail)")
    
    # Report agent status as busy
    await result_reporter.report_agent_status(
        is_online=True,
        current_load=1
    )
    
    # Report task progress (0%)
    await result_reporter.report_task_progress(
        task_id=task_id,
        progress_data={
            "percent_complete": 0,
            "message": "Task started",
            "stage": "initialization"
        }
    )
    
    # Simulate work (25%)
    await asyncio.sleep(1)
    await result_reporter.report_task_progress(
        task_id=task_id,
        progress_data={
            "percent_complete": 25,
            "message": "Processing data",
            "stage": "data_processing"
        }
    )
    
    # Simulate an error
    await asyncio.sleep(1)
    
    # Log the error
    await result_reporter.report_agent_log(
        log_message="External API connection failed",
        severity=ResultSeverity.ERROR,
        log_context={
            "task_id": task_id,
            "stage": "data_processing",
            "service": "external-api",
            "status_code": 500
        }
    )
    
    # Report task error
    await result_reporter.report_task_error(
        task_id=task_id,
        error_message="Failed to connect to external API",
        error_details={
            "service": "external-api",
            "status_code": 500,
            "retry_count": 3,
            "last_error": "Connection timeout"
        }
    )
    
    # Report agent status as idle
    await result_reporter.report_agent_status(
        is_online=True,
        current_load=0
    )
    
    logger.info(f"Agent {agent_id} failed task {task_id}")


async def simulate_custom_reporting(agent_id: str) -> None:
    """
    Simulate custom result reporting.
    
    Args:
        agent_id: ID of the agent
    """
    # Get the result reporting client
    result_reporter = await get_result_reporting_client(agent_id=agent_id)
    
    logger.info(f"Agent {agent_id} sending custom results")
    
    # Report a custom result
    await result_reporter.report_custom_result(
        result_id="system-health",
        data={
            "system_health": {
                "memory_available_mb": 4096,
                "disk_space_available_gb": 50,
                "cpu_temperature_celsius": 45,
                "network_latency_ms": 25
            },
            "timestamp": datetime.now().isoformat()
        }
    )
    
    # Report another custom result to a specific recipient
    await result_reporter.report_custom_result(
        result_id="collaboration-data",
        data={
            "shared_context": {
                "user_preferences": {
                    "theme": "dark",
                    "language": "en-US"
                },
                "session_id": "session-12345"
            }
        },
        recipient_id="ui-agent",
        correlation_id="session-12345",
        priority="high"
    )
    
    logger.info(f"Agent {agent_id} sent custom results")


async def main() -> None:
    """Run the example."""
    agent_id = "example-agent"
    
    # Simulate a successful task
    task_id_1 = f"task-{int(time.time())}-1"
    await simulate_task_execution(agent_id, task_id_1)
    
    # Simulate a failed task
    task_id_2 = f"task-{int(time.time())}-2"
    await simulate_task_error(agent_id, task_id_2)
    
    # Simulate custom reporting
    await simulate_custom_reporting(agent_id)
    
    # Get the result reporting client and shut it down
    result_reporter = await get_result_reporting_client(agent_id=agent_id)
    await result_reporter.shutdown()


if __name__ == "__main__":
    asyncio.run(main())
