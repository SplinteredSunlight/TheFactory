#!/usr/bin/env python3
"""
Circuit Breaker Pattern with Dagger Example

This example demonstrates how to use the circuit breaker pattern with Dagger
to prevent cascading failures in a distributed system.
"""

import asyncio
import json
import logging
import os
import random
import sys
from datetime import datetime

# Add the project root to the Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from src.agent_manager.dagger_adapter import DaggerAdapter, DaggerAdapterConfig
from src.agent_manager.schemas import AgentExecutionConfig
from src.orchestrator.circuit_breaker import CircuitBreaker, CircuitBreakerOpenError, get_circuit_breaker

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Global variables
SUCCESS_RATE = 0.3  # 30% success rate initially
RECOVERY_TIME = 5  # Time in seconds before service starts recovering
TOTAL_REQUESTS = 20  # Total number of requests to make


class MockDaggerService:
    """Mock Dagger service that can fail randomly."""
    
    def __init__(self, initial_success_rate=0.3, recovery_time=5):
        """Initialize the mock service.
        
        Args:
            initial_success_rate: Initial probability of success (0.0 to 1.0)
            recovery_time: Time in seconds before service starts recovering
        """
        self.success_rate = initial_success_rate
        self.recovery_time = recovery_time
        self.start_time = datetime.now()
        
    async def execute_workflow(self, workflow_id, inputs=None):
        """Execute a workflow with a chance of failure.
        
        Args:
            workflow_id: ID of the workflow to execute
            inputs: Inputs for the workflow
            
        Returns:
            Result of the workflow execution
            
        Raises:
            Exception: If the workflow execution fails
        """
        # Calculate current success rate based on time elapsed
        elapsed_seconds = (datetime.now() - self.start_time).total_seconds()
        if elapsed_seconds > self.recovery_time:
            # Gradually increase success rate after recovery time
            recovery_factor = min(1.0, (elapsed_seconds - self.recovery_time) / 10)
            current_success_rate = min(1.0, self.success_rate + recovery_factor)
        else:
            current_success_rate = self.success_rate
            
        # Simulate random success/failure
        if random.random() < current_success_rate:
            # Success
            await asyncio.sleep(0.1)  # Simulate processing time
            return {
                "workflow_id": workflow_id,
                "status": "completed",
                "result": {"message": f"Workflow {workflow_id} completed successfully"},
                "timestamp": datetime.now().isoformat()
            }
        else:
            # Failure
            await asyncio.sleep(0.2)  # Failed requests take longer
            raise Exception(f"Workflow {workflow_id} failed: Service unavailable")


class DaggerCircuitBreakerExample:
    """Example of using the circuit breaker pattern with Dagger."""
    
    def __init__(self):
        """Initialize the example."""
        # Create a mock Dagger service
        self.mock_service = MockDaggerService(
            initial_success_rate=SUCCESS_RATE,
            recovery_time=RECOVERY_TIME
        )
        
        # Create a Dagger adapter
        config = DaggerAdapterConfig(
            max_retries=1,
            retry_backoff_factor=0.5,
            retry_jitter=True,
            caching_enabled=False
        )
        self.dagger_adapter = DaggerAdapter(config)
        
        # Override the _execute_dagger_pipeline method to use our mock service
        self.dagger_adapter._execute_dagger_pipeline = self._mock_execute_dagger_pipeline
        
        # Get a circuit breaker
        self.circuit_breaker = get_circuit_breaker(
            "example_circuit_breaker",
            failure_threshold=3,
            reset_timeout=3,
            half_open_timeout=1
        )
        
        # Initialize counters
        self.total_requests = 0
        self.successful_requests = 0
        self.failed_requests = 0
        self.circuit_open_requests = 0
        
    async def _mock_execute_dagger_pipeline(self, params):
        """Mock implementation of _execute_dagger_pipeline.
        
        Args:
            params: Parameters for the pipeline
            
        Returns:
            Result of the pipeline execution
            
        Raises:
            Exception: If the pipeline execution fails
        """
        workflow_id = params.get("pipeline_definition", "unknown")
        inputs = params.get("inputs", {})
        
        # Execute the workflow using the mock service
        result = await self.mock_service.execute_workflow(workflow_id, inputs)
        
        return result
        
    async def execute_request(self, request_id, use_circuit_breaker=True):
        """Execute a request with or without circuit breaker protection.
        
        Args:
            request_id: ID of the request
            use_circuit_breaker: Whether to use circuit breaker protection
            
        Returns:
            Result of the request
        """
        self.total_requests += 1
        
        # Create an execution config
        execution_config = AgentExecutionConfig(
            task_id=f"task-{request_id}",
            execution_type="dagger_pipeline",
            parameters={
                "pipeline_definition": f"workflow-{request_id}",
                "inputs": {"request_id": request_id},
                "use_circuit_breaker": use_circuit_breaker
            }
        )
        
        try:
            # Execute the request
            start_time = datetime.now()
            
            if use_circuit_breaker:
                # Use the circuit breaker pattern
                try:
                    result = await self.dagger_adapter.execute(execution_config)
                    if result.success:
                        self.successful_requests += 1
                        logger.info(f"Request {request_id} succeeded with circuit breaker")
                    else:
                        self.failed_requests += 1
                        logger.warning(f"Request {request_id} failed with circuit breaker: {result.error}")
                    return result
                except CircuitBreakerOpenError as e:
                    self.circuit_open_requests += 1
                    logger.warning(f"Request {request_id} blocked by circuit breaker: {e}")
                    return AgentExecutionResult(
                        success=False,
                        error=f"Circuit breaker is open: {str(e)}",
                        result=None
                    )
            else:
                # Execute without circuit breaker
                result = await self.dagger_adapter.execute(execution_config)
                if result.success:
                    self.successful_requests += 1
                    logger.info(f"Request {request_id} succeeded without circuit breaker")
                else:
                    self.failed_requests += 1
                    logger.warning(f"Request {request_id} failed without circuit breaker: {result.error}")
                return result
                
        except Exception as e:
            self.failed_requests += 1
            logger.error(f"Request {request_id} failed with exception: {e}")
            return AgentExecutionResult(
                success=False,
                error=str(e),
                result=None
            )
            
    async def run_example(self):
        """Run the example."""
        logger.info(f"Starting circuit breaker example with {TOTAL_REQUESTS} requests")
        logger.info(f"Initial success rate: {SUCCESS_RATE * 100:.1f}%")
        logger.info(f"Recovery time: {RECOVERY_TIME} seconds")
        
        # Initialize the adapter
        await self.dagger_adapter.initialize()
        
        # Execute requests with circuit breaker
        logger.info("\n--- With Circuit Breaker ---")
        with_cb_results = []
        for i in range(TOTAL_REQUESTS):
            result = await self.execute_request(f"cb-{i}", use_circuit_breaker=True)
            with_cb_results.append(result)
            await asyncio.sleep(0.5)  # Space out requests
            
        # Reset counters
        self.total_requests = 0
        self.successful_requests = 0
        self.failed_requests = 0
        self.circuit_open_requests = 0
        
        # Execute requests without circuit breaker
        logger.info("\n--- Without Circuit Breaker ---")
        without_cb_results = []
        for i in range(TOTAL_REQUESTS):
            result = await self.execute_request(f"no-cb-{i}", use_circuit_breaker=False)
            without_cb_results.append(result)
            await asyncio.sleep(0.5)  # Space out requests
            
        # Print summary
        logger.info("\n--- Summary ---")
        logger.info("With Circuit Breaker:")
        logger.info(f"  Total requests: {TOTAL_REQUESTS}")
        logger.info(f"  Successful requests: {sum(1 for r in with_cb_results if r.success)}")
        logger.info(f"  Failed requests: {sum(1 for r in with_cb_results if not r.success and 'circuit breaker is open' not in r.error.lower())}")
        logger.info(f"  Requests blocked by circuit breaker: {sum(1 for r in with_cb_results if not r.success and 'circuit breaker is open' in r.error.lower())}")
        
        logger.info("\nWithout Circuit Breaker:")
        logger.info(f"  Total requests: {TOTAL_REQUESTS}")
        logger.info(f"  Successful requests: {sum(1 for r in without_cb_results if r.success)}")
        logger.info(f"  Failed requests: {sum(1 for r in without_cb_results if not r.success)}")
        
        # Shutdown the adapter
        await self.dagger_adapter.shutdown()


# Helper class for JSON serialization
class AgentExecutionResult:
    """Result of an agent execution."""
    
    def __init__(self, success, error=None, result=None):
        """Initialize the result.
        
        Args:
            success: Whether the execution succeeded
            error: Error message if the execution failed
            result: Result of the execution
        """
        self.success = success
        self.error = error
        self.result = result


async def main():
    """Run the example."""
    example = DaggerCircuitBreakerExample()
    await example.run_example()


if __name__ == "__main__":
    asyncio.run(main())
