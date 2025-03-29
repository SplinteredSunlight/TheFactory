"""
Circuit Breaker Pattern implementation for Dagger operations.

This module provides a circuit breaker implementation that can be used to wrap
Dagger operations to prevent cascading failures and provide resilience.
"""

import time
import logging
import asyncio
from enum import Enum
from typing import Callable, TypeVar, Any, Optional, Dict

# Set up logging
logger = logging.getLogger(__name__)

# Type variables for generic functions
T = TypeVar('T')


class CircuitState(Enum):
    """Enum representing the possible states of a circuit breaker."""
    CLOSED = 'closed'  # Normal operation, requests are allowed
    OPEN = 'open'      # Circuit is open, requests are not allowed
    HALF_OPEN = 'half_open'  # Testing if the circuit can be closed again


class CircuitBreakerError(Exception):
    """Base exception for circuit breaker errors."""
    pass


class CircuitBreakerOpenError(CircuitBreakerError):
    """Exception raised when a request is made while the circuit is open."""
    pass


class CircuitBreaker:
    """
    Implementation of the Circuit Breaker pattern for Dagger operations.
    
    The circuit breaker monitors for failures in the wrapped operation.
    When the number of failures exceeds a threshold, the circuit breaker
    trips and all further requests fail immediately until a timeout period
    has elapsed.
    """
    
    def __init__(
        self,
        failure_threshold: int = 5,
        reset_timeout: float = 60.0,
        half_open_max_calls: int = 1,
        name: str = "default"
    ):
        """
        Initialize a new circuit breaker.
        
        Args:
            failure_threshold: Number of failures before the circuit opens
            reset_timeout: Time in seconds before attempting to close the circuit
            half_open_max_calls: Maximum number of calls allowed in half-open state
            name: Name of this circuit breaker (for logging)
        """
        self.failure_threshold = failure_threshold
        self.reset_timeout = reset_timeout
        self.half_open_max_calls = half_open_max_calls
        self.name = name
        
        # State tracking
        self.state = CircuitState.CLOSED
        self.failure_count = 0
        self.last_failure_time: Optional[float] = None
        self.half_open_calls = 0
        
        # Metrics
        self.metrics: Dict[str, int] = {
            "success_count": 0,
            "failure_count": 0,
            "rejected_count": 0,
            "state_changes": 0
        }
        
        logger.info(f"Circuit breaker '{name}' initialized with failure_threshold={failure_threshold}, "
                   f"reset_timeout={reset_timeout}s")
    
    def allow_request(self) -> bool:
        """
        Check if a request should be allowed based on the current circuit state.
        
        Returns:
            bool: True if the request should be allowed, False otherwise
        """
        if self.state == CircuitState.CLOSED:
            return True
        
        elif self.state == CircuitState.OPEN:
            # Check if the reset timeout has elapsed
            if (self.last_failure_time is not None and 
                time.time() - self.last_failure_time > self.reset_timeout):
                # Transition to half-open state
                logger.info(f"Circuit breaker '{self.name}' transitioning from OPEN to HALF-OPEN")
                self._transition_to_state(CircuitState.HALF_OPEN)
                self.half_open_calls = 0
                return True
            
            # Circuit is still open
            self.metrics["rejected_count"] += 1
            return False
        
        elif self.state == CircuitState.HALF_OPEN:
            # Allow a limited number of calls in half-open state
            if self.half_open_calls < self.half_open_max_calls:
                self.half_open_calls += 1
                return True
            
            # Too many calls in half-open state
            self.metrics["rejected_count"] += 1
            return False
        
        # Should never reach here
        return False
    
    def record_success(self) -> None:
        """Record a successful operation."""
        self.metrics["success_count"] += 1
        
        if self.state == CircuitState.HALF_OPEN:
            # If successful while half-open, close the circuit
            logger.info(f"Circuit breaker '{self.name}' transitioning from HALF-OPEN to CLOSED")
            self._transition_to_state(CircuitState.CLOSED)
            self.failure_count = 0
    
    def record_failure(self) -> None:
        """Record a failed operation."""
        self.failure_count += 1
        self.last_failure_time = time.time()
        self.metrics["failure_count"] += 1
        
        if self.state == CircuitState.CLOSED and self.failure_count >= self.failure_threshold:
            # Too many failures, open the circuit
            logger.warning(f"Circuit breaker '{self.name}' transitioning from CLOSED to OPEN "
                          f"after {self.failure_count} failures")
            self._transition_to_state(CircuitState.OPEN)
        
        elif self.state == CircuitState.HALF_OPEN:
            # Failed while half-open, reopen the circuit
            logger.warning(f"Circuit breaker '{self.name}' transitioning from HALF-OPEN to OPEN "
                          f"after a failure")
            self._transition_to_state(CircuitState.OPEN)
    
    def _transition_to_state(self, new_state: CircuitState) -> None:
        """
        Transition the circuit breaker to a new state.
        
        Args:
            new_state: The new state to transition to
        """
        if self.state != new_state:
            self.state = new_state
            self.metrics["state_changes"] += 1
    
    def get_metrics(self) -> Dict[str, Any]:
        """
        Get metrics about this circuit breaker.
        
        Returns:
            Dict containing metrics about the circuit breaker
        """
        return {
            "name": self.name,
            "state": self.state.value,
            "failure_count": self.failure_count,
            "last_failure_time": self.last_failure_time,
            "metrics": self.metrics
        }
    
    def reset(self) -> None:
        """Reset the circuit breaker to its initial state."""
        self.state = CircuitState.CLOSED
        self.failure_count = 0
        self.last_failure_time = None
        self.half_open_calls = 0
        logger.info(f"Circuit breaker '{self.name}' has been reset")


async def execute_with_circuit_breaker(
    circuit_breaker: CircuitBreaker,
    operation: Callable[[], T]
) -> T:
    """
    Execute an operation with circuit breaker protection.
    
    Args:
        circuit_breaker: The circuit breaker to use
        operation: The operation to execute (can be a regular function or coroutine)
    
    Returns:
        The result of the operation
    
    Raises:
        CircuitBreakerOpenError: If the circuit is open
        Any exception raised by the operation
    """
    if not circuit_breaker.allow_request():
        raise CircuitBreakerOpenError(f"Circuit breaker '{circuit_breaker.name}' is open")
    
    try:
        # Handle both coroutines and regular functions
        if asyncio.iscoroutinefunction(operation) or asyncio.iscoroutine(operation):
            result = await operation()
        else:
            result = operation()
        
        circuit_breaker.record_success()
        return result
    except Exception as e:
        circuit_breaker.record_failure()
        raise e


# Registry to store circuit breakers by name
_circuit_breakers: Dict[str, CircuitBreaker] = {}


def get_circuit_breaker(name: str = "default") -> CircuitBreaker:
    """
    Get a circuit breaker by name, creating it if it doesn't exist.
    
    Args:
        name: Name of the circuit breaker
    
    Returns:
        The circuit breaker instance
    """
    if name not in _circuit_breakers:
        _circuit_breakers[name] = CircuitBreaker(name=name)
    
    return _circuit_breakers[name]


def reset_all_circuit_breakers() -> None:
    """Reset all circuit breakers in the registry."""
    for cb in _circuit_breakers.values():
        cb.reset()


def get_all_circuit_breakers() -> Dict[str, CircuitBreaker]:
    """Get all circuit breakers in the registry."""
    return _circuit_breakers
