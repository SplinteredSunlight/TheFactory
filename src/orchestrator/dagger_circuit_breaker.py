"""
Dagger Circuit Breaker Module for AI-Orchestration-Platform

This module provides a circuit breaker implementation specifically designed for Dagger operations,
extending the base CircuitBreaker class to handle Dagger-specific error patterns and recovery strategies.
"""

import asyncio
import logging
import time
from typing import Any, Callable, Dict, List, Optional, TypeVar, Union

# Import the base CircuitBreaker class
from .error_handling import CircuitBreaker, BaseError, ErrorCode, ErrorSeverity, Component

# Configure logging
logger = logging.getLogger(__name__)

# Type variable for generic function return type
T = TypeVar('T')


class DaggerCircuitBreakerError(BaseError):
    """Error raised when a circuit breaker prevents an operation."""
    
    def __init__(
        self,
        message: str,
        details: Optional[Dict[str, Any]] = None,
        severity: ErrorSeverity = ErrorSeverity.ERROR,
        documentation_url: Optional[str] = None,
    ):
        """Initialize a new DaggerCircuitBreakerError.
        
        Args:
            message: Human-readable error message
            details: Additional error details
            severity: Error severity level
            documentation_url: URL to documentation about the error
        """
        super().__init__(
            code="DAGGER.CIRCUIT_BREAKER.OPEN",
            message=message,
            details=details,
            severity=severity,
            component=Component.ORCHESTRATOR,
            http_status=503,  # Service Unavailable
            documentation_url=documentation_url,
        )


class DaggerCircuitBreaker(CircuitBreaker):
    """Circuit breaker implementation specifically for Dagger operations."""
    
    def __init__(
        self,
        name: str,
        failure_threshold: int = 5,
        reset_timeout: int = 30,
        half_open_limit: int = 3,
        window_size: int = 60,
        dagger_error_types: Optional[List[str]] = None,
    ):
        """Initialize a new DaggerCircuitBreaker.
        
        Args:
            name: Name of the circuit breaker for identification
            failure_threshold: Number of failures before opening the circuit
            reset_timeout: Seconds to wait before transitioning to half-open
            half_open_limit: Number of requests to allow in half-open state
            window_size: Time window in seconds for counting failures
            dagger_error_types: List of Dagger error types that should trigger the circuit breaker
        """
        super().__init__(
            failure_threshold=failure_threshold,
            reset_timeout=reset_timeout,
            half_open_limit=half_open_limit,
            window_size=window_size,
        )
        self.name = name
        self.dagger_error_types = dagger_error_types or [
            "ConnectionError",
            "TimeoutError",
            "InternalError",
            "ResourceExhaustedError",
        ]
        
        # Additional metrics for monitoring
        self.total_requests = 0
        self.successful_requests = 0
        self.failed_requests = 0
        self.prevented_requests = 0
        self.last_state_change = time.time()
        self.state_changes = []
    
    def allow_request(self) -> bool:
        """Check if a request is allowed to proceed.
        
        Returns:
            True if the request is allowed, False otherwise
        """
        self.total_requests += 1
        allowed = super().allow_request()
        
        if not allowed:
            self.prevented_requests += 1
            logger.warning(
                f"Circuit breaker '{self.name}' is {self.state}, request prevented. "
                f"Total prevented: {self.prevented_requests}"
            )
        
        return allowed
    
    def record_success(self) -> None:
        """Record a successful request."""
        self.successful_requests += 1
        
        previous_state = self.state
        super().record_success()
        
        # Log state changes
        if previous_state != self.state:
            now = time.time()
            self.state_changes.append({
                "from": previous_state,
                "to": self.state,
                "timestamp": now,
                "duration": now - self.last_state_change
            })
            self.last_state_change = now
            
            logger.info(
                f"Circuit breaker '{self.name}' state changed from {previous_state} to {self.state}"
            )
    
    def record_failure(self) -> None:
        """Record a failed request."""
        self.failed_requests += 1
        
        previous_state = self.state
        super().record_failure()
        
        # Log state changes
        if previous_state != self.state:
            now = time.time()
            self.state_changes.append({
                "from": previous_state,
                "to": self.state,
                "timestamp": now,
                "duration": now - self.last_state_change
            })
            self.last_state_change = now
            
            logger.warning(
                f"Circuit breaker '{self.name}' state changed from {previous_state} to {self.state} "
                f"after {len(self.failures)} failures"
            )
    
    def is_dagger_error(self, error: Exception) -> bool:
        """Check if an error is a Dagger error that should trigger the circuit breaker.
        
        Args:
            error: The error to check
            
        Returns:
            True if the error is a Dagger error, False otherwise
        """
        error_type = type(error).__name__
        
        # Check if the error type is in the list of Dagger error types
        if error_type in self.dagger_error_types:
            return True
        
        # Check if the error is from the Dagger module
        if hasattr(error, "__module__") and "dagger" in getattr(error, "__module__", "").lower():
            return True
        
        return False
    
    def get_metrics(self) -> Dict[str, Any]:
        """Get metrics for the circuit breaker.
        
        Returns:
            Dictionary of circuit breaker metrics
        """
        return {
            "name": self.name,
            "state": self.state,
            "total_requests": self.total_requests,
            "successful_requests": self.successful_requests,
            "failed_requests": self.failed_requests,
            "prevented_requests": self.prevented_requests,
            "failure_count": len(self.failures),
            "failure_threshold": self.failure_threshold,
            "reset_timeout": self.reset_timeout,
            "half_open_limit": self.half_open_limit,
            "half_open_count": self.half_open_count,
            "window_size": self.window_size,
            "last_failure_time": self.last_failure_time,
            "last_state_change": self.last_state_change,
            "state_changes": self.state_changes[-10:],  # Last 10 state changes
        }
    
    def reset(self) -> None:
        """Reset the circuit breaker to its initial state."""
        self.failures = []
        self.state = "closed"
        self.last_failure_time = 0
        self.half_open_count = 0
        
        # Log the reset
        logger.info(f"Circuit breaker '{self.name}' has been reset to closed state")


async def execute_with_circuit_breaker(
    circuit_breaker: DaggerCircuitBreaker,
    operation: Callable[..., T],
    *args: Any,
    **kwargs: Any
) -> T:
    """Execute a Dagger operation with circuit breaker protection.
    
    Args:
        circuit_breaker: The circuit breaker to use
        operation: The Dagger operation to execute
        *args: Arguments for the operation
        **kwargs: Keyword arguments for the operation
        
    Returns:
        The result of the operation
        
    Raises:
        DaggerCircuitBreakerError: If the circuit breaker is open
        Exception: Any exception raised by the operation
    """
    # Check if the request is allowed
    if not circuit_breaker.allow_request():
        raise DaggerCircuitBreakerError(
            message=f"Circuit breaker '{circuit_breaker.name}' is {circuit_breaker.state}, request prevented",
            details={
                "circuit_breaker": circuit_breaker.name,
                "state": circuit_breaker.state,
                "reset_timeout": circuit_breaker.reset_timeout,
                "last_failure_time": circuit_breaker.last_failure_time,
                "time_remaining": max(0, circuit_breaker.reset_timeout - (time.time() - circuit_breaker.last_failure_time)),
            }
        )
    
    try:
        # Execute the operation
        if asyncio.iscoroutinefunction(operation):
            result = await operation(*args, **kwargs)
        else:
            result = operation(*args, **kwargs)
        
        # Record the success
        circuit_breaker.record_success()
        
        return result
    except Exception as e:
        # Check if this is a Dagger error that should trigger the circuit breaker
        if circuit_breaker.is_dagger_error(e):
            # Record the failure
            circuit_breaker.record_failure()
            
            logger.error(
                f"Dagger operation failed with error: {str(e)}. "
                f"Circuit breaker '{circuit_breaker.name}' recorded failure."
            )
        else:
            # Log but don't count as a circuit breaker failure
            logger.warning(
                f"Operation failed with non-Dagger error: {str(e)}. "
                f"Not counted as circuit breaker failure."
            )
        
        # Re-raise the exception
        raise


class DaggerCircuitBreakerRegistry:
    """Registry for managing multiple circuit breakers."""
    
    def __init__(self):
        """Initialize a new DaggerCircuitBreakerRegistry."""
        self.circuit_breakers: Dict[str, DaggerCircuitBreaker] = {}
    
    def register(self, circuit_breaker: DaggerCircuitBreaker) -> None:
        """Register a circuit breaker.
        
        Args:
            circuit_breaker: The circuit breaker to register
        """
        self.circuit_breakers[circuit_breaker.name] = circuit_breaker
        logger.info(f"Circuit breaker '{circuit_breaker.name}' registered")
    
    def unregister(self, name: str) -> None:
        """Unregister a circuit breaker.
        
        Args:
            name: Name of the circuit breaker to unregister
        """
        if name in self.circuit_breakers:
            del self.circuit_breakers[name]
            logger.info(f"Circuit breaker '{name}' unregistered")
    
    def get(self, name: str) -> Optional[DaggerCircuitBreaker]:
        """Get a circuit breaker by name.
        
        Args:
            name: Name of the circuit breaker to get
            
        Returns:
            The circuit breaker, or None if not found
        """
        return self.circuit_breakers.get(name)
    
    def get_or_create(
        self,
        name: str,
        failure_threshold: int = 5,
        reset_timeout: int = 30,
        half_open_limit: int = 3,
        window_size: int = 60,
        dagger_error_types: Optional[List[str]] = None,
    ) -> DaggerCircuitBreaker:
        """Get a circuit breaker by name, or create it if it doesn't exist.
        
        Args:
            name: Name of the circuit breaker
            failure_threshold: Number of failures before opening the circuit
            reset_timeout: Seconds to wait before transitioning to half-open
            half_open_limit: Number of requests to allow in half-open state
            window_size: Time window in seconds for counting failures
            dagger_error_types: List of Dagger error types that should trigger the circuit breaker
            
        Returns:
            The circuit breaker
        """
        if name not in self.circuit_breakers:
            circuit_breaker = DaggerCircuitBreaker(
                name=name,
                failure_threshold=failure_threshold,
                reset_timeout=reset_timeout,
                half_open_limit=half_open_limit,
                window_size=window_size,
                dagger_error_types=dagger_error_types,
            )
            self.register(circuit_breaker)
        
        return self.circuit_breakers[name]
    
    def reset_all(self) -> None:
        """Reset all circuit breakers."""
        for circuit_breaker in self.circuit_breakers.values():
            circuit_breaker.reset()
        
        logger.info(f"All circuit breakers ({len(self.circuit_breakers)}) have been reset")
    
    def get_all_metrics(self) -> Dict[str, Dict[str, Any]]:
        """Get metrics for all circuit breakers.
        
        Returns:
            Dictionary of circuit breaker metrics, keyed by circuit breaker name
        """
        return {
            name: circuit_breaker.get_metrics()
            for name, circuit_breaker in self.circuit_breakers.items()
        }


# Singleton instance
_circuit_breaker_registry_instance: Optional[DaggerCircuitBreakerRegistry] = None


def get_circuit_breaker_registry() -> DaggerCircuitBreakerRegistry:
    """Get the DaggerCircuitBreakerRegistry singleton instance.
    
    Returns:
        The DaggerCircuitBreakerRegistry instance
    """
    global _circuit_breaker_registry_instance
    
    if _circuit_breaker_registry_instance is None:
        _circuit_breaker_registry_instance = DaggerCircuitBreakerRegistry()
    
    return _circuit_breaker_registry_instance
