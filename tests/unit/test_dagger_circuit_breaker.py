"""
Unit tests for the Dagger Circuit Breaker implementation.

This module tests the Dagger-specific circuit breaker implementation that extends
the base circuit breaker with Dagger-specific functionality.
"""

import asyncio
import pytest
import time
from unittest.mock import AsyncMock, MagicMock, patch

from src.orchestrator.dagger_circuit_breaker import (
    DaggerCircuitBreaker,
    DaggerCircuitBreakerError,
    execute_with_circuit_breaker,
    get_circuit_breaker_registry
)


class TestDaggerCircuitBreaker:
    """Test cases for the DaggerCircuitBreaker class."""

    def test_initial_state(self):
        """Test that the circuit breaker starts in the closed state."""
        cb = DaggerCircuitBreaker(name="test")
        assert cb.state == "closed"
        assert cb.allow_request() is True
        assert len(cb.failures) == 0
        assert cb.last_failure_time == 0
        assert cb.total_requests == 1  # allow_request increments this

    def test_failure_threshold(self):
        """Test that the circuit breaker opens after reaching the failure threshold."""
        cb = DaggerCircuitBreaker(name="test", failure_threshold=3)
        assert cb.state == "closed"
        
        # Record failures
        cb.record_failure()
        assert cb.state == "closed"
        assert len(cb.failures) == 1
        assert cb.failed_requests == 1
        
        cb.record_failure()
        assert cb.state == "closed"
        assert len(cb.failures) == 2
        assert cb.failed_requests == 2
        
        cb.record_failure()
        assert cb.state == "open"
        assert len(cb.failures) == 3
        assert cb.failed_requests == 3
        assert cb.allow_request() is False
        assert cb.prevented_requests == 1

    def test_reset_timeout(self):
        """Test that the circuit breaker transitions to half-open after the reset timeout."""
        cb = DaggerCircuitBreaker(name="test", failure_threshold=1, reset_timeout=0.1)
        
        # Open the circuit
        cb.record_failure()
        assert cb.state == "open"
        assert cb.allow_request() is False
        
        # Wait for the reset timeout
        time.sleep(0.2)
        
        # Circuit should now be half-open
        assert cb.allow_request() is True
        assert cb.state == "half-open"

    def test_success_in_half_open(self):
        """Test that a successful request in half-open state closes the circuit."""
        cb = DaggerCircuitBreaker(name="test", failure_threshold=1, reset_timeout=0.1)
        
        # Open the circuit
        cb.record_failure()
        assert cb.state == "open"
        
        # Wait for the reset timeout
        time.sleep(0.2)
        
        # Circuit should now be half-open
        assert cb.allow_request() is True
        assert cb.state == "half-open"
        
        # Record a success
        cb.record_success()
        assert cb.state == "closed"
        assert cb.successful_requests == 1
        assert len(cb.state_changes) == 2  # open -> half-open -> closed

    def test_failure_in_half_open(self):
        """Test that a failed request in half-open state reopens the circuit."""
        cb = DaggerCircuitBreaker(name="test", failure_threshold=1, reset_timeout=0.1)
        
        # Open the circuit
        cb.record_failure()
        assert cb.state == "open"
        
        # Wait for the reset timeout
        time.sleep(0.2)
        
        # Circuit should now be half-open
        assert cb.allow_request() is True
        assert cb.state == "half-open"
        
        # Record a failure
        cb.record_failure()
        assert cb.state == "open"
        assert cb.allow_request() is False
        assert len(cb.state_changes) == 2  # closed -> open -> half-open -> open

    def test_half_open_limit(self):
        """Test that only a limited number of requests are allowed in half-open state."""
        cb = DaggerCircuitBreaker(name="test", failure_threshold=1, reset_timeout=0.1, half_open_limit=2)
        
        # Open the circuit
        cb.record_failure()
        assert cb.state == "open"
        
        # Wait for the reset timeout
        time.sleep(0.2)
        
        # Circuit should now be half-open
        assert cb.allow_request() is True  # First call allowed
        assert cb.allow_request() is True  # Second call allowed
        assert cb.allow_request() is False  # Third call rejected
        assert cb.state == "half-open"
        assert cb.prevented_requests == 1

    def test_metrics(self):
        """Test that metrics are correctly tracked."""
        cb = DaggerCircuitBreaker(name="test-metrics", failure_threshold=2)
        
        # Record some operations
        cb.record_success()
        cb.record_success()
        cb.record_failure()
        cb.record_failure()  # This should open the circuit
        
        # Try a request that should be rejected
        assert cb.allow_request() is False
        
        # Get metrics
        metrics = cb.get_metrics()
        
        assert metrics["name"] == "test-metrics"
        assert metrics["state"] == "open"
        assert metrics["failure_count"] == 2
        assert metrics["successful_requests"] == 2
        assert metrics["failed_requests"] == 2
        assert metrics["prevented_requests"] == 1
        assert len(metrics["state_changes"]) > 0

    def test_reset(self):
        """Test that reset returns the circuit breaker to its initial state."""
        cb = DaggerCircuitBreaker(name="test-reset", failure_threshold=1)
        
        # Open the circuit
        cb.record_failure()
        assert cb.state == "open"
        
        # Reset the circuit breaker
        cb.reset()
        
        # Check that it's back to initial state
        assert cb.state == "closed"
        assert len(cb.failures) == 0
        assert cb.last_failure_time == 0
        assert cb.allow_request() is True

    def test_is_dagger_error(self):
        """Test the is_dagger_error method."""
        cb = DaggerCircuitBreaker(name="test-errors")
        
        # Test with a standard error
        standard_error = ValueError("Standard error")
        assert cb.is_dagger_error(standard_error) is False
        
        # Test with an error type in the dagger_error_types list
        connection_error = ConnectionError("Connection error")
        assert cb.is_dagger_error(connection_error) is True
        
        # Test with a custom error from a dagger module
        class MockDaggerError(Exception):
            pass
        
        # Mock the __module__ attribute
        MockDaggerError.__module__ = "dagger.errors"
        dagger_error = MockDaggerError("Dagger error")
        assert cb.is_dagger_error(dagger_error) is True


@pytest.mark.asyncio
class TestExecuteWithCircuitBreaker:
    """Test cases for the execute_with_circuit_breaker function."""

    async def test_successful_execution(self):
        """Test that a successful operation is executed normally."""
        cb = DaggerCircuitBreaker(name="test-execute")
        
        # Define a mock operation
        mock_operation = AsyncMock(return_value="success")
        
        # Execute with circuit breaker
        result = await execute_with_circuit_breaker(cb, mock_operation)
        
        # Check results
        assert result == "success"
        assert cb.state == "closed"
        assert cb.successful_requests == 1
        assert cb.failed_requests == 0

    async def test_failed_execution(self):
        """Test that a failed operation is handled correctly."""
        cb = DaggerCircuitBreaker(name="test-execute-fail", failure_threshold=1)
        
        # Define a mock operation that raises an exception
        mock_operation = AsyncMock(side_effect=ValueError("test error"))
        
        # Execute with circuit breaker
        with pytest.raises(ValueError, match="test error"):
            await execute_with_circuit_breaker(cb, mock_operation)
        
        # Check results
        assert cb.state == "closed"  # Not a Dagger error, so circuit stays closed
        assert cb.successful_requests == 0
        assert cb.failed_requests == 0  # Not counted as a circuit breaker failure

    async def test_dagger_error_execution(self):
        """Test that a Dagger error is handled correctly."""
        cb = DaggerCircuitBreaker(name="test-execute-dagger-error", failure_threshold=1)
        
        # Define a mock operation that raises a Dagger error
        class MockDaggerError(Exception):
            pass
        
        # Mock the __module__ attribute
        MockDaggerError.__module__ = "dagger.errors"
        mock_operation = AsyncMock(side_effect=MockDaggerError("dagger error"))
        
        # Execute with circuit breaker
        with pytest.raises(MockDaggerError, match="dagger error"):
            await execute_with_circuit_breaker(cb, mock_operation)
        
        # Check results
        assert cb.state == "open"  # Dagger error, so circuit opens
        assert cb.successful_requests == 0
        assert cb.failed_requests == 1

    async def test_circuit_open(self):
        """Test that requests are rejected when the circuit is open."""
        cb = DaggerCircuitBreaker(name="test-execute-open", failure_threshold=1)
        
        # Open the circuit
        cb.record_failure()
        assert cb.state == "open"
        
        # Define a mock operation
        mock_operation = AsyncMock(return_value="success")
        
        # Execute with circuit breaker
        with pytest.raises(DaggerCircuitBreakerError):
            await execute_with_circuit_breaker(cb, mock_operation)
        
        # Check that the operation was not called
        mock_operation.assert_not_called()

    async def test_sync_operation(self):
        """Test that synchronous operations are handled correctly."""
        cb = DaggerCircuitBreaker(name="test-execute-sync")
        
        # Define a synchronous operation
        def sync_operation():
            return "sync success"
        
        # Execute with circuit breaker
        result = await execute_with_circuit_breaker(cb, sync_operation)
        
        # Check results
        assert result == "sync success"
        assert cb.successful_requests == 1


class TestDaggerCircuitBreakerRegistry:
    """Test cases for the DaggerCircuitBreakerRegistry class."""

    def test_registry_singleton(self):
        """Test that get_circuit_breaker_registry returns the same instance."""
        registry1 = get_circuit_breaker_registry()
        registry2 = get_circuit_breaker_registry()
        
        assert registry1 is registry2

    def test_register_and_get(self):
        """Test registering and retrieving circuit breakers."""
        registry = get_circuit_breaker_registry()
        
        # Create a circuit breaker
        cb = DaggerCircuitBreaker(name="test-registry")
        
        # Register it
        registry.register(cb)
        
        # Get it back
        retrieved_cb = registry.get("test-registry")
        
        assert retrieved_cb is cb

    def test_get_or_create(self):
        """Test get_or_create method."""
        registry = get_circuit_breaker_registry()
        
        # Get a circuit breaker that doesn't exist yet
        cb1 = registry.get_or_create("test-get-or-create")
        
        # Get it again
        cb2 = registry.get_or_create("test-get-or-create")
        
        # They should be the same instance
        assert cb1 is cb2
        
        # Check that it has the default parameters
        assert cb1.failure_threshold == 5
        
        # Get a circuit breaker with custom parameters
        cb3 = registry.get_or_create(
            "test-get-or-create-custom",
            failure_threshold=10,
            reset_timeout=60
        )
        
        # Check that it has the custom parameters
        assert cb3.failure_threshold == 10
        assert cb3.reset_timeout == 60

    def test_unregister(self):
        """Test unregistering circuit breakers."""
        registry = get_circuit_breaker_registry()
        
        # Create and register a circuit breaker
        cb = DaggerCircuitBreaker(name="test-unregister")
        registry.register(cb)
        
        # Verify it's registered
        assert registry.get("test-unregister") is cb
        
        # Unregister it
        registry.unregister("test-unregister")
        
        # Verify it's gone
        assert registry.get("test-unregister") is None

    def test_reset_all(self):
        """Test resetting all circuit breakers."""
        registry = get_circuit_breaker_registry()
        
        # Create and register some circuit breakers
        cb1 = registry.get_or_create("test-reset-all-1")
        cb2 = registry.get_or_create("test-reset-all-2")
        
        # Open the circuit breakers
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
        
        # Verify they're open
        assert cb1.state == "open"
        assert cb2.state == "open"
        
        # Reset all circuit breakers
        registry.reset_all()
        
        # Verify they're closed
        assert cb1.state == "closed"
        assert cb2.state == "closed"

    def test_get_all_metrics(self):
        """Test getting metrics for all circuit breakers."""
        registry = get_circuit_breaker_registry()
        
        # Create and register some circuit breakers
        cb1 = registry.get_or_create("test-metrics-1")
        cb2 = registry.get_or_create("test-metrics-2")
        
        # Record some operations
        cb1.record_success()
        cb2.record_failure()
        
        # Get all metrics
        metrics = registry.get_all_metrics()
        
        # Check that both circuit breakers are in the metrics
        assert "test-metrics-1" in metrics
        assert "test-metrics-2" in metrics
        
        # Check some specific metrics
        assert metrics["test-metrics-1"]["successful_requests"] == 1
        assert metrics["test-metrics-2"]["failed_requests"] == 1
