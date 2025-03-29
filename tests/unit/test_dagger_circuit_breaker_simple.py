"""
Simple unit tests for the Dagger Circuit Breaker implementation.

This module provides basic tests for the DaggerCircuitBreaker class without
depending on the full test infrastructure.
"""

import asyncio
import time
import unittest
from unittest.mock import AsyncMock, MagicMock

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.orchestrator.dagger_circuit_breaker import (
    DaggerCircuitBreaker,
    DaggerCircuitBreakerError,
    execute_with_circuit_breaker,
    get_circuit_breaker_registry
)


class TestDaggerCircuitBreaker(unittest.TestCase):
    """Test cases for the DaggerCircuitBreaker class."""

    def test_initial_state(self):
        """Test that the circuit breaker starts in the closed state."""
        cb = DaggerCircuitBreaker(name="test")
        self.assertEqual(cb.state, "closed")
        self.assertTrue(cb.allow_request())
        self.assertEqual(len(cb.failures), 0)
        self.assertEqual(cb.last_failure_time, 0)
        self.assertEqual(cb.total_requests, 1)  # allow_request increments this

    def test_failure_threshold(self):
        """Test that the circuit breaker opens after reaching the failure threshold."""
        cb = DaggerCircuitBreaker(name="test", failure_threshold=3)
        self.assertEqual(cb.state, "closed")
        
        # Record failures
        cb.record_failure()
        self.assertEqual(cb.state, "closed")
        self.assertEqual(len(cb.failures), 1)
        self.assertEqual(cb.failed_requests, 1)
        
        cb.record_failure()
        self.assertEqual(cb.state, "closed")
        self.assertEqual(len(cb.failures), 2)
        self.assertEqual(cb.failed_requests, 2)
        
        cb.record_failure()
        self.assertEqual(cb.state, "open")
        self.assertEqual(len(cb.failures), 3)
        self.assertEqual(cb.failed_requests, 3)
        self.assertFalse(cb.allow_request())
        self.assertEqual(cb.prevented_requests, 1)

    def test_reset_timeout(self):
        """Test that the circuit breaker transitions to half-open after the reset timeout."""
        cb = DaggerCircuitBreaker(name="test", failure_threshold=1, reset_timeout=0.1)
        
        # Open the circuit
        cb.record_failure()
        self.assertEqual(cb.state, "open")
        self.assertFalse(cb.allow_request())
        
        # Wait for the reset timeout
        time.sleep(0.2)
        
        # Circuit should now be half-open
        self.assertTrue(cb.allow_request())
        self.assertEqual(cb.state, "half-open")

    def test_success_in_half_open(self):
        """Test that a successful request in half-open state closes the circuit."""
        cb = DaggerCircuitBreaker(name="test", failure_threshold=1, reset_timeout=0.1)
        
        # Open the circuit
        cb.record_failure()
        self.assertEqual(cb.state, "open")
        
        # Wait for the reset timeout
        time.sleep(0.2)
        
        # Circuit should now be half-open
        self.assertTrue(cb.allow_request())
        self.assertEqual(cb.state, "half-open")
        
        # Record a success
        cb.record_success()
        self.assertEqual(cb.state, "closed")
        self.assertEqual(cb.successful_requests, 1)
        self.assertEqual(len(cb.state_changes), 2)  # open -> half-open -> closed

    def test_reset(self):
        """Test that reset returns the circuit breaker to its initial state."""
        cb = DaggerCircuitBreaker(name="test-reset", failure_threshold=1)
        
        # Open the circuit
        cb.record_failure()
        self.assertEqual(cb.state, "open")
        
        # Reset the circuit breaker
        cb.reset()
        
        # Check that it's back to initial state
        self.assertEqual(cb.state, "closed")
        self.assertEqual(len(cb.failures), 0)
        self.assertEqual(cb.last_failure_time, 0)
        self.assertTrue(cb.allow_request())

    def test_is_dagger_error(self):
        """Test the is_dagger_error method."""
        cb = DaggerCircuitBreaker(name="test-errors")
        
        # Test with a standard error
        standard_error = ValueError("Standard error")
        self.assertFalse(cb.is_dagger_error(standard_error))
        
        # Test with an error type in the dagger_error_types list
        connection_error = ConnectionError("Connection error")
        self.assertTrue(cb.is_dagger_error(connection_error))
        
        # Test with a custom error from a dagger module
        class MockDaggerError(Exception):
            pass
        
        # Mock the __module__ attribute
        MockDaggerError.__module__ = "dagger.errors"
        dagger_error = MockDaggerError("Dagger error")
        self.assertTrue(cb.is_dagger_error(dagger_error))


class TestDaggerCircuitBreakerRegistry(unittest.TestCase):
    """Test cases for the DaggerCircuitBreakerRegistry class."""

    def test_registry_singleton(self):
        """Test that get_circuit_breaker_registry returns the same instance."""
        registry1 = get_circuit_breaker_registry()
        registry2 = get_circuit_breaker_registry()
        
        self.assertIs(registry1, registry2)

    def test_register_and_get(self):
        """Test registering and retrieving circuit breakers."""
        registry = get_circuit_breaker_registry()
        
        # Create a circuit breaker
        cb = DaggerCircuitBreaker(name="test-registry")
        
        # Register it
        registry.register(cb)
        
        # Get it back
        retrieved_cb = registry.get("test-registry")
        
        self.assertIs(retrieved_cb, cb)

    def test_get_or_create(self):
        """Test get_or_create method."""
        registry = get_circuit_breaker_registry()
        
        # Get a circuit breaker that doesn't exist yet
        cb1 = registry.get_or_create("test-get-or-create")
        
        # Get it again
        cb2 = registry.get_or_create("test-get-or-create")
        
        # They should be the same instance
        self.assertIs(cb1, cb2)
        
        # Check that it has the default parameters
        self.assertEqual(cb1.failure_threshold, 5)
        
        # Get a circuit breaker with custom parameters
        cb3 = registry.get_or_create(
            "test-get-or-create-custom",
            failure_threshold=10,
            reset_timeout=60
        )
        
        # Check that it has the custom parameters
        self.assertEqual(cb3.failure_threshold, 10)
        self.assertEqual(cb3.reset_timeout, 60)


class TestExecuteWithCircuitBreaker(unittest.TestCase):
    """Test cases for the execute_with_circuit_breaker function."""

    def test_successful_execution(self):
        """Test that a successful operation is executed normally."""
        cb = DaggerCircuitBreaker(name="test-execute")
        
        # Define a mock operation
        mock_operation = MagicMock(return_value="success")
        
        # Execute with circuit breaker
        result = asyncio.run(execute_with_circuit_breaker(cb, mock_operation))
        
        # Check results
        self.assertEqual(result, "success")
        self.assertEqual(cb.state, "closed")
        self.assertEqual(cb.successful_requests, 1)
        self.assertEqual(cb.failed_requests, 0)

    def test_circuit_open(self):
        """Test that requests are rejected when the circuit is open."""
        cb = DaggerCircuitBreaker(name="test-execute-open", failure_threshold=1)
        
        # Open the circuit
        cb.record_failure()
        self.assertEqual(cb.state, "open")
        
        # Define a mock operation
        mock_operation = MagicMock(return_value="success")
        
        # Execute with circuit breaker
        with self.assertRaises(DaggerCircuitBreakerError):
            asyncio.run(execute_with_circuit_breaker(cb, mock_operation))
        
        # Check that the operation was not called
        mock_operation.assert_not_called()


if __name__ == '__main__':
    unittest.main()
