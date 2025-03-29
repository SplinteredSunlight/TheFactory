"""
Example demonstrating how to use the Circuit Breaker pattern with Dagger operations.

This example shows how to wrap Dagger operations with the Circuit Breaker pattern
to provide resilience and prevent cascading failures.
"""

import asyncio
import logging
import random
import time
import dagger
from typing import Optional

from src.orchestrator.circuit_breaker import (
    CircuitBreaker,
    execute_with_circuit_breaker,
    CircuitBreakerOpenError
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class DaggerOperationError(Exception):
    """Exception raised when a Dagger operation fails."""
    pass


class UnstableDaggerService:
    """
    A simulated unstable Dagger service that occasionally fails.
    
    This class is used to demonstrate how the Circuit Breaker pattern
    can be used to handle failures in Dagger operations.
    """
    
    def __init__(self, failure_rate: float = 0.3, delay: float = 0.1):
        """
        Initialize the unstable service.
        
        Args:
            failure_rate: Probability of failure (0.0 to 1.0)
            delay: Simulated processing delay in seconds
        """
        self.failure_rate = failure_rate
        self.delay = delay
        self.failure_count = 0
        self.success_count = 0
    
    async def execute_operation(self, operation_id: str) -> str:
        """
        Execute a simulated Dagger operation that may fail.
        
        Args:
            operation_id: Identifier for the operation
        
        Returns:
            Result of the operation
        
        Raises:
            DaggerOperationError: If the operation fails
        """
        # Simulate processing delay
        await asyncio.sleep(self.delay)
        
        # Randomly fail based on failure rate
        if random.random() < self.failure_rate:
            self.failure_count += 1
            logger.error(f"Operation {operation_id} failed (failure #{self.failure_count})")
            raise DaggerOperationError(f"Operation {operation_id} failed")
        
        # Operation succeeded
        self.success_count += 1
        logger.info(f"Operation {operation_id} succeeded (success #{self.success_count})")
        return f"Result of operation {operation_id}"


async def execute_dagger_operation(
    client: dagger.Client,
    container_image: str,
    command: list[str],
    circuit_breaker: Optional[CircuitBreaker] = None
) -> str:
    """
    Execute a Dagger operation with circuit breaker protection.
    
    Args:
        client: Dagger client
        container_image: Container image to use
        command: Command to execute in the container
        circuit_breaker: Circuit breaker to use (optional)
    
    Returns:
        Output of the Dagger operation
    
    Raises:
        CircuitBreakerOpenError: If the circuit is open
        Exception: If the Dagger operation fails
    """
    # Create a function that executes the Dagger operation
    async def dagger_operation():
        try:
            # Execute the Dagger operation
            container = client.container().from_(container_image)
            result = await container.with_exec(command).stdout()
            return result
        except Exception as e:
            # Wrap the exception to provide more context
            raise DaggerOperationError(f"Dagger operation failed: {str(e)}") from e
    
    # If a circuit breaker is provided, use it to wrap the operation
    if circuit_breaker:
        return await execute_with_circuit_breaker(circuit_breaker, dagger_operation)
    else:
        # Otherwise, execute the operation directly
        return await dagger_operation()


async def run_with_real_dagger():
    """Run the example with a real Dagger client."""
    # Create a circuit breaker
    circuit_breaker = CircuitBreaker(
        failure_threshold=3,
        reset_timeout=5.0,
        name="dagger-operations"
    )
    
    # Connect to Dagger
    async with dagger.Connection() as client:
        # Execute some Dagger operations with circuit breaker protection
        for i in range(10):
            try:
                # Execute a simple echo command
                result = await execute_dagger_operation(
                    client=client,
                    container_image="alpine:latest",
                    command=["echo", f"Hello from operation {i}"],
                    circuit_breaker=circuit_breaker
                )
                logger.info(f"Result: {result}")
            except CircuitBreakerOpenError as e:
                logger.warning(f"Circuit breaker is open: {str(e)}")
            except DaggerOperationError as e:
                logger.error(f"Dagger operation failed: {str(e)}")
            
            # Wait a bit between operations
            await asyncio.sleep(0.5)
        
        # Print circuit breaker metrics
        logger.info(f"Circuit breaker metrics: {circuit_breaker.get_metrics()}")


async def run_with_simulated_dagger():
    """Run the example with a simulated unstable Dagger service."""
    # Create a circuit breaker
    circuit_breaker = CircuitBreaker(
        failure_threshold=3,
        reset_timeout=5.0,
        name="simulated-dagger-operations"
    )
    
    # Create an unstable service
    service = UnstableDaggerService(failure_rate=0.5, delay=0.2)
    
    # Execute some operations with circuit breaker protection
    for i in range(20):
        operation_id = f"op-{i}"
        
        try:
            # Wrap the service operation with the circuit breaker
            result = await execute_with_circuit_breaker(
                circuit_breaker,
                lambda: service.execute_operation(operation_id)
            )
            logger.info(f"Result: {result}")
        except CircuitBreakerOpenError as e:
            logger.warning(f"Circuit breaker is open: {str(e)}")
        except DaggerOperationError as e:
            logger.error(f"Service operation failed: {str(e)}")
        
        # Wait a bit between operations
        await asyncio.sleep(0.5)
        
        # Print circuit breaker state every 5 operations
        if (i + 1) % 5 == 0:
            metrics = circuit_breaker.get_metrics()
            logger.info(f"Circuit breaker state: {metrics['state']}")
            logger.info(f"Success count: {metrics['metrics']['success_count']}")
            logger.info(f"Failure count: {metrics['metrics']['failure_count']}")
            logger.info(f"Rejected count: {metrics['metrics']['rejected_count']}")
    
    # Print final circuit breaker metrics
    logger.info(f"Final circuit breaker metrics: {circuit_breaker.get_metrics()}")


async def main():
    """Run the example."""
    logger.info("Starting Circuit Breaker example with simulated Dagger service")
    await run_with_simulated_dagger()
    
    logger.info("\nStarting Circuit Breaker example with real Dagger client")
    try:
        await run_with_real_dagger()
    except Exception as e:
        logger.error(f"Error running with real Dagger: {str(e)}")


if __name__ == "__main__":
    asyncio.run(main())
