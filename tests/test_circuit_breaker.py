"""
Unit tests for the Circuit Breaker pattern implementation.
"""

import pytest
import asyncio
import time
from unittest.mock import MagicMock, patch

from src.orchestrator.circuit_breaker import (
    CircuitBreaker,
    CircuitState,
    CircuitBreakerOpenError,
    execute_with_circuit_breaker,
    get_circuit_breaker,
    reset_all_circuit_breakers,
    get_all_circuit_breakers
)


class TestCircuitBreaker:
    """Test cases for the CircuitBreaker class."""

    def test_initial_state(self):
        """Test that the circuit breaker starts in the closed state."""
        cb = CircuitBreaker()
        assert cb.state == CircuitState.CLOSED
        assert cb.allow_request() is True
        assert cb.failure_count == 0
        assert cb.last_failure_time is None

    def test_failure_threshold(self):
        """Test that the circuit breaker opens after reaching the failure threshold."""
        cb = CircuitBreaker(failure_threshold=3)
        assert cb.state == CircuitState.CLOSED
        
        # Record failures
        cb.record_failure()
        assert cb.state == CircuitState.CLOSED
        assert cb.failure_count == 1
        
        cb.record_failure()
        assert cb.state == CircuitState.CLOSED
        assert cb.failure_count == 2
        
        cb.record_failure()
        assert cb.state == CircuitState.OPEN
        assert cb.failure_count == 3
        assert cb.allow_request() is False

    def test_reset_timeout(self):
        """Test that the circuit breaker transitions to half-open after the reset timeout."""
        cb = CircuitBreaker(failure_threshold=1, reset_timeout=0.1)
        
        # Open the circuit
        cb.record_failure()
        assert cb.state == CircuitState.OPEN
        assert cb.allow_request() is False
        
        # Wait for the reset timeout
        time.sleep(0.2)
        
        # Circuit should now be half-open
        assert cb.allow_request() is True
        assert cb.state == CircuitState.HALF_OPEN

    def test_success_in_half_open(self):
        """Test that a successful request in half-open state closes the circuit."""
        cb = CircuitBreaker(failure_threshold=1, reset_timeout=0.1)
        
        # Open the circuit
        cb.record_failure()
        assert cb.state == CircuitState.OPEN
        
        # Wait for the reset timeout
        time.sleep(0.2)
        
        # Circuit should now be half-open
        assert cb.allow_request() is True
        assert cb.state == CircuitState.HALF_OPEN
        
        # Record a success
        cb.record_success()
        assert cb.state == CircuitState.CLOSED
        assert cb.failure_count == 0

    def test_failure_in_half_open(self):
        """Test that a failed request in half-open state reopens the circuit."""
        cb = CircuitBreaker(failure_threshold=1, reset_timeout=0.1)
        
        # Open the circuit
        cb.record_failure()
        assert cb.state == CircuitState.OPEN
        
        # Wait for the reset timeout
        time.sleep(0.2)
        
        # Circuit should now be half-open
        assert cb.allow_request() is True
        assert cb.state == CircuitState.HALF_OPEN
        
        # Record a failure
        cb.record_failure()
        assert cb.state == CircuitState.OPEN
        assert cb.allow_request() is False

    def test_half_open_max_calls(self):
        """Test that only a limited number of requests are allowed in half-open state."""
        cb = CircuitBreaker(failure_threshold=1, reset_timeout=0.1, half_open_max_calls=2)
        
        # Open the circuit
        cb.record_failure()
        assert cb.state == CircuitState.OPEN
        
        # Wait for the reset timeout
        time.sleep(0.2)
        
        # Circuit should now be half-open
        assert cb.allow_request() is True  # First call allowed
        assert cb.allow_request() is True  # Second call allowed
        assert cb.allow_request() is False  # Third call rejected
        assert cb.state == CircuitState.HALF_OPEN

    def test_metrics(self):
        """Test that metrics are correctly tracked."""
        cb = CircuitBreaker(failure_threshold=2)
        
        # Record some operations
        cb.record_success()
        cb.record_success()
        cb.record_failure()
        cb.record_failure()  # This should open the circuit
        
        # Try a request that should be rejected
        assert cb.allow_request() is False
        
        # Get metrics
        metrics = cb.get_metrics()
        
        assert metrics["name"] == "default"
        assert metrics["state"] == "open"
        assert metrics["failure_count"] == 2
        assert metrics["metrics"]["success_count"] == 2
        assert metrics["metrics"]["failure_count"] == 2
        assert metrics["metrics"]["rejected_count"] == 1
        assert metrics["metrics"]["state_changes"] == 1

    def test_reset(self):
        """Test that reset returns the circuit breaker to its initial state."""
        cb = CircuitBreaker(failure_threshold=1)
        
        # Open the circuit
        cb.record_failure()
        assert cb.state == CircuitState.OPEN
        
        # Reset the circuit breaker
        cb.reset()
        
        # Check that it's back to initial state
        assert cb.state == CircuitState.CLOSED
        assert cb.failure_count == 0
        assert cb.last_failure_time is None
        assert cb.allow_request() is True


class TestExecuteWithCircuitBreaker:
    """Test cases for the execute_with_circuit_breaker function."""

    @pytest.mark.asyncio
    async def test_successful_execution(self):
        """Test that a successful operation is executed normally."""
        cb = CircuitBreaker()
        
        # Define a mock operation
        mock_operation = MagicMock(return_value="success")
        
        # Execute with circuit breaker
        result = await execute_with_circuit_breaker(cb, mock_operation)
        
        # Check results
        assert result == "success"
        assert cb.state == CircuitState.CLOSED
        assert cb.metrics["success_count"] == 1
        assert cb.metrics["failure_count"] == 0

    @pytest.mark.asyncio
    async def test_failed_execution(self):
        """Test that a failed operation is handled correctly."""
        cb = CircuitBreaker(failure_threshold=1)
        
        # Define a mock operation that raises an exception
        mock_operation = MagicMock(side_effect=ValueError("test error"))
        
        # Execute with circuit breaker
        with pytest.raises(ValueError, match="test error"):
            await execute_with_circuit_breaker(cb, mock_operation)
        
        # Check results
        assert cb.state == CircuitState.OPEN
        assert cb.metrics["success_count"] == 0
        assert cb.metrics["failure_count"] == 1

    @pytest.mark.asyncio
    async def test_circuit_open(self):
        """Test that requests are rejected when the circuit is open."""
        cb = CircuitBreaker(failure_threshold=1)
        
        # Open the circuit
        cb.record_failure()
        assert cb.state == CircuitState.OPEN
        
        # Define a mock operation
        mock_operation = MagicMock(return_value="success")
        
        # Execute with circuit breaker
        with pytest.raises(CircuitBreakerOpenError):
            await execute_with_circuit_breaker(cb, mock_operation)
        
        # Check that the operation was not called
        mock_operation.assert_not_called()

    @pytest.mark.asyncio
    async def test_async_operation(self):
        """Test that async operations are handled correctly."""
        cb = CircuitBreaker()
        
        # Define an async operation
        async def async_operation():
            await asyncio.sleep(0.1)
            return "async success"
        
        # Execute with circuit breaker
        result = await execute_with_circuit_breaker(cb, async_operation)
        
        # Check results
        assert result == "async success"
        assert cb.metrics["success_count"] == 1


class TestCircuitBreakerRegistry:
    """Test cases for the circuit breaker registry functions."""

    def test_get_circuit_breaker(self):
        """Test that get_circuit_breaker returns the same instance for the same name."""
        # Reset the registry
        reset_all_circuit_breakers()
        
        # Get a circuit breaker
        cb1 = get_circuit_breaker("test")
        cb2 = get_circuit_breaker("test")
        
        # Check that they are the same instance
        assert cb1 is cb2
        
        # Get a different circuit breaker
        cb3 = get_circuit_breaker("other")
        
        # Check that it's a different instance
        assert cb1 is not cb3

    def test_reset_all_circuit_breakers(self):
        """Test that reset_all_circuit_breakers resets all circuit breakers."""
        # Reset the registry
        reset_all_circuit_breakers()
        
        # Get some circuit breakers and open them
        cb1 = get_circuit_breaker("test1")
        cb2 = get_circuit_breaker("test2")
        
        cb1.record_failure()
        cb1.record_failure()
        cb1.record_failure()
        cb1.record_failure()
        cb1.record_failure()
        
        cb2.record_failure()
        cb2.record_failure()
        cb2.record_failure()
        cb2.record_failure()
        cb2.record_failure()
        
        # Check that they are open
        assert cb1.state == CircuitState.OPEN
        assert cb2.state == CircuitState.OPEN
        
        # Reset all circuit breakers
        reset_all_circuit_breakers()
        
        # Check that they are closed
        assert cb1.state == CircuitState.CLOSED
        assert cb2.state == CircuitState.CLOSED

    def test_get_all_circuit_breakers(self):
        """Test that get_all_circuit_breakers returns all circuit breakers."""
        # Reset the registry
        reset_all_circuit_breakers()
        
        # Get some circuit breakers
        cb1 = get_circuit_breaker("test1")
        cb2 = get_circuit_breaker("test2")
        
        # Get all circuit breakers
        all_cbs = get_all_circuit_breakers()
        
        # Check that they are in the registry
        assert "test1" in all_cbs
        assert "test2" in all_cbs
        assert all_cbs["test1"] is cb1
        assert all_cbs["test2"] is cb2
