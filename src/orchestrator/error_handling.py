"""
Error Handling Module for AI-Orchestration-Platform

This module provides standardized error handling functionality for the AI-Orchestration-Platform,
including error formatting, logging, reporting, and recovery strategies.
"""

import asyncio
import datetime
import json
import logging
import time
import uuid
from enum import Enum
from typing import Any, Dict, List, Optional, Union, Callable, Type, TypeVar

# Configure logging
logger = logging.getLogger(__name__)


class ErrorSeverity(str, Enum):
    """Severity levels for errors."""
    CRITICAL = "CRITICAL"
    ERROR = "ERROR"
    WARNING = "WARNING"
    INFO = "INFO"


class ErrorCategory(str, Enum):
    """Categories of errors."""
    AUTHENTICATION = "AUTHENTICATION"
    AUTHORIZATION = "AUTHORIZATION"
    VALIDATION = "VALIDATION"
    RESOURCE = "RESOURCE"
    INTEGRATION = "INTEGRATION"
    SYSTEM = "SYSTEM"
    RATE_LIMIT = "RATE_LIMIT"


class Component(str, Enum):
    """System components."""
    AUTH = "AUTH"
    ORCHESTRATOR = "ORCHESTRATOR"
    FAST_AGENT = "FAST_AGENT"
    AGENT_MANAGER = "AGENT_MANAGER"
    TASK_SCHEDULER = "TASK_SCHEDULER"
    API_GATEWAY = "API_GATEWAY"
    INTEGRATION = "INTEGRATION"


class ErrorCode:
    """Error codes for the AI-Orchestration-Platform."""
    
    # Authentication errors
    AUTH_INVALID_TOKEN = "AUTH.AUTHENTICATION.INVALID_TOKEN"
    AUTH_EXPIRED_TOKEN = "AUTH.AUTHENTICATION.EXPIRED_TOKEN"
    AUTH_INVALID_API_KEY = "AUTH.AUTHENTICATION.INVALID_API_KEY"
    AUTH_INVALID_CREDENTIALS = "AUTH.AUTHENTICATION.INVALID_CREDENTIALS"
    
    # Authorization errors
    AUTH_INSUFFICIENT_SCOPE = "AUTH.AUTHORIZATION.INSUFFICIENT_SCOPE"
    AUTH_FORBIDDEN = "AUTH.AUTHORIZATION.FORBIDDEN"
    AUTH_AGENT_DISABLED = "AUTH.AUTHORIZATION.AGENT_DISABLED"
    
    # Validation errors
    VALIDATION_INVALID_PARAMS = "VALIDATION.INVALID_PARAMS"
    VALIDATION_MISSING_REQUIRED = "VALIDATION.MISSING_REQUIRED"
    VALIDATION_INVALID_FORMAT = "VALIDATION.INVALID_FORMAT"
    
    # Resource errors
    RESOURCE_NOT_FOUND = "RESOURCE.NOT_FOUND"
    RESOURCE_ALREADY_EXISTS = "RESOURCE.ALREADY_EXISTS"
    RESOURCE_UNAVAILABLE = "RESOURCE.UNAVAILABLE"
    
    # Integration errors
    INTEGRATION_CONNECTION_FAILED = "INTEGRATION.CONNECTION_FAILED"
    INTEGRATION_TIMEOUT = "INTEGRATION.TIMEOUT"
    INTEGRATION_INCOMPATIBLE = "INTEGRATION.INCOMPATIBLE"
    
    # System errors
    SYSTEM_INTERNAL_ERROR = "SYSTEM.INTERNAL_ERROR"
    SYSTEM_DEPENDENCY_FAILED = "SYSTEM.DEPENDENCY_FAILED"
    SYSTEM_CONFIGURATION_ERROR = "SYSTEM.CONFIGURATION_ERROR"
    
    # Rate limiting errors
    RATE_LIMIT_EXCEEDED = "RATE_LIMIT.EXCEEDED"
    RATE_LIMIT_QUOTA_EXCEEDED = "RATE_LIMIT.QUOTA_EXCEEDED"
    
    # Component-specific error codes
    ORCHESTRATOR_AGENT_NOT_FOUND = "ORCHESTRATOR.RESOURCE.AGENT_NOT_FOUND"
    ORCHESTRATOR_TASK_NOT_FOUND = "ORCHESTRATOR.RESOURCE.TASK_NOT_FOUND"
    ORCHESTRATOR_WORKFLOW_NOT_FOUND = "ORCHESTRATOR.RESOURCE.WORKFLOW_NOT_FOUND"
    ORCHESTRATOR_TASK_DISTRIBUTION_FAILED = "ORCHESTRATOR.SYSTEM.TASK_DISTRIBUTION_FAILED"
    
    FAST_AGENT_INITIALIZATION_FAILED = "FAST_AGENT.SYSTEM.INITIALIZATION_FAILED"
    FAST_AGENT_EXECUTION_FAILED = "FAST_AGENT.SYSTEM.EXECUTION_FAILED"
    FAST_AGENT_CONNECTION_FAILED = "FAST_AGENT.INTEGRATION.CONNECTION_FAILED"


class BaseError(Exception):
    """Base error class for the AI-Orchestration-Platform."""
    
    def __init__(
        self,
        code: str,
        message: str,
        details: Optional[Dict[str, Any]] = None,
        severity: ErrorSeverity = ErrorSeverity.ERROR,
        component: Optional[str] = None,
        http_status: int = 500,
        documentation_url: Optional[str] = None,
    ):
        """Initialize a new BaseError.
        
        Args:
            code: Error code
            message: Human-readable error message
            details: Additional error details
            severity: Error severity level
            component: System component that raised the error
            http_status: HTTP status code for the error
            documentation_url: URL to documentation about the error
        """
        self.code = code
        self.message = message
        self.details = details or {}
        self.severity = severity
        self.component = component
        self.http_status = http_status
        self.documentation_url = documentation_url
        self.request_id = str(uuid.uuid4())
        self.timestamp = datetime.datetime.now().isoformat()
        
        # Initialize the exception
        super().__init__(message)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert the error to a dictionary representation.
        
        Returns:
            Dictionary representation of the error
        """
        return {
            "error": {
                "code": self.code,
                "message": self.message,
                "details": self.details,
                "severity": self.severity,
                "component": self.component,
                "request_id": self.request_id,
                "timestamp": self.timestamp,
                "documentation_url": self.documentation_url,
            }
        }
    
    def to_json(self) -> str:
        """Convert the error to a JSON string.
        
        Returns:
            JSON string representation of the error
        """
        return json.dumps(self.to_dict())
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'BaseError':
        """Create an error from a dictionary representation.
        
        Args:
            data: Dictionary representation of the error
            
        Returns:
            A new BaseError instance
        """
        error_data = data.get("error", data)
        
        return cls(
            code=error_data.get("code", "UNKNOWN"),
            message=error_data.get("message", "Unknown error"),
            details=error_data.get("details"),
            severity=error_data.get("severity", ErrorSeverity.ERROR),
            component=error_data.get("component"),
            documentation_url=error_data.get("documentation_url"),
        )


# Specific error classes

class AuthenticationError(BaseError):
    """Error raised for authentication failures."""
    
    def __init__(
        self,
        message: str,
        code: str = ErrorCode.AUTH_INVALID_CREDENTIALS,
        details: Optional[Dict[str, Any]] = None,
        severity: ErrorSeverity = ErrorSeverity.ERROR,
        documentation_url: Optional[str] = None,
    ):
        """Initialize a new AuthenticationError.
        
        Args:
            message: Human-readable error message
            code: Error code
            details: Additional error details
            severity: Error severity level
            documentation_url: URL to documentation about the error
        """
        super().__init__(
            code=code,
            message=message,
            details=details,
            severity=severity,
            component=Component.AUTH,
            http_status=401,
            documentation_url=documentation_url,
        )


class AuthorizationError(BaseError):
    """Error raised for authorization failures."""
    
    def __init__(
        self,
        message: str,
        code: str = ErrorCode.AUTH_INSUFFICIENT_SCOPE,
        details: Optional[Dict[str, Any]] = None,
        severity: ErrorSeverity = ErrorSeverity.ERROR,
        documentation_url: Optional[str] = None,
    ):
        """Initialize a new AuthorizationError.
        
        Args:
            message: Human-readable error message
            code: Error code
            details: Additional error details
            severity: Error severity level
            documentation_url: URL to documentation about the error
        """
        super().__init__(
            code=code,
            message=message,
            details=details,
            severity=severity,
            component=Component.AUTH,
            http_status=403,
            documentation_url=documentation_url,
        )


class ValidationError(BaseError):
    """Error raised for input validation failures."""
    
    def __init__(
        self,
        message: str,
        code: str = ErrorCode.VALIDATION_INVALID_PARAMS,
        details: Optional[Dict[str, Any]] = None,
        severity: ErrorSeverity = ErrorSeverity.ERROR,
        component: Optional[str] = None,
        documentation_url: Optional[str] = None,
    ):
        """Initialize a new ValidationError.
        
        Args:
            message: Human-readable error message
            code: Error code
            details: Additional error details
            severity: Error severity level
            component: System component that raised the error
            documentation_url: URL to documentation about the error
        """
        super().__init__(
            code=code,
            message=message,
            details=details,
            severity=severity,
            component=component,
            http_status=400,
            documentation_url=documentation_url,
        )


class ResourceError(BaseError):
    """Error raised for resource-related failures."""
    
    def __init__(
        self,
        message: str,
        code: str = ErrorCode.RESOURCE_NOT_FOUND,
        details: Optional[Dict[str, Any]] = None,
        severity: ErrorSeverity = ErrorSeverity.ERROR,
        component: Optional[str] = None,
        documentation_url: Optional[str] = None,
    ):
        """Initialize a new ResourceError.
        
        Args:
            message: Human-readable error message
            code: Error code
            details: Additional error details
            severity: Error severity level
            component: System component that raised the error
            documentation_url: URL to documentation about the error
        """
        http_status = 404 if code == ErrorCode.RESOURCE_NOT_FOUND else 400
        
        super().__init__(
            code=code,
            message=message,
            details=details,
            severity=severity,
            component=component,
            http_status=http_status,
            documentation_url=documentation_url,
        )


class IntegrationError(BaseError):
    """Error raised for integration-related failures."""
    
    def __init__(
        self,
        message: str,
        code: str = ErrorCode.INTEGRATION_CONNECTION_FAILED,
        details: Optional[Dict[str, Any]] = None,
        severity: ErrorSeverity = ErrorSeverity.ERROR,
        component: Optional[str] = None,
        documentation_url: Optional[str] = None,
    ):
        """Initialize a new IntegrationError.
        
        Args:
            message: Human-readable error message
            code: Error code
            details: Additional error details
            severity: Error severity level
            component: System component that raised the error
            documentation_url: URL to documentation about the error
        """
        http_status = 502
        if code == ErrorCode.INTEGRATION_TIMEOUT:
            http_status = 504
        
        super().__init__(
            code=code,
            message=message,
            details=details,
            severity=severity,
            component=component or Component.INTEGRATION,
            http_status=http_status,
            documentation_url=documentation_url,
        )


class SystemError(BaseError):
    """Error raised for system-related failures."""
    
    def __init__(
        self,
        message: str,
        code: str = ErrorCode.SYSTEM_INTERNAL_ERROR,
        details: Optional[Dict[str, Any]] = None,
        severity: ErrorSeverity = ErrorSeverity.ERROR,
        component: Optional[str] = None,
        documentation_url: Optional[str] = None,
    ):
        """Initialize a new SystemError.
        
        Args:
            message: Human-readable error message
            code: Error code
            details: Additional error details
            severity: Error severity level
            component: System component that raised the error
            documentation_url: URL to documentation about the error
        """
        super().__init__(
            code=code,
            message=message,
            details=details,
            severity=severity,
            component=component or Component.SYSTEM,
            http_status=500,
            documentation_url=documentation_url,
        )


class RateLimitError(BaseError):
    """Error raised for rate limiting failures."""
    
    def __init__(
        self,
        message: str,
        code: str = ErrorCode.RATE_LIMIT_EXCEEDED,
        details: Optional[Dict[str, Any]] = None,
        severity: ErrorSeverity = ErrorSeverity.ERROR,
        component: Optional[str] = None,
        documentation_url: Optional[str] = None,
        retry_after: Optional[int] = None,
    ):
        """Initialize a new RateLimitError.
        
        Args:
            message: Human-readable error message
            code: Error code
            details: Additional error details
            severity: Error severity level
            component: System component that raised the error
            documentation_url: URL to documentation about the error
            retry_after: Seconds to wait before retrying
        """
        details = details or {}
        if retry_after is not None:
            details["retry_after"] = retry_after
        
        super().__init__(
            code=code,
            message=message,
            details=details,
            severity=severity,
            component=component,
            http_status=429,
            documentation_url=documentation_url,
        )


# Error handling utilities

class CircuitBreaker:
    """Circuit breaker implementation for preventing cascading failures."""
    
    def __init__(
        self,
        failure_threshold: int = 5,
        reset_timeout: int = 30,
        half_open_limit: int = 3,
        window_size: int = 60,
    ):
        """Initialize a new CircuitBreaker.
        
        Args:
            failure_threshold: Number of failures before opening the circuit
            reset_timeout: Seconds to wait before transitioning to half-open
            half_open_limit: Number of requests to allow in half-open state
            window_size: Time window in seconds for counting failures
        """
        self.failure_threshold = failure_threshold
        self.reset_timeout = reset_timeout
        self.half_open_limit = half_open_limit
        self.window_size = window_size
        
        self.failures = []
        self.state = "closed"  # closed, open, half-open
        self.last_failure_time = 0
        self.half_open_count = 0
    
    def allow_request(self) -> bool:
        """Check if a request is allowed to proceed.
        
        Returns:
            True if the request is allowed, False otherwise
        """
        now = time.time()
        
        # Clean up old failures
        self.failures = [f for f in self.failures if now - f < self.window_size]
        
        if self.state == "closed":
            return True
        elif self.state == "open":
            # Check if it's time to transition to half-open
            if now - self.last_failure_time >= self.reset_timeout:
                self.state = "half-open"
                self.half_open_count = 0
                return True
            return False
        elif self.state == "half-open":
            # Allow a limited number of requests in half-open state
            if self.half_open_count < self.half_open_limit:
                self.half_open_count += 1
                return True
            return False
        
        return True
    
    def record_success(self) -> None:
        """Record a successful request."""
        if self.state == "half-open":
            # If we've had enough successful requests in half-open state, close the circuit
            self.half_open_count += 1
            if self.half_open_count >= self.half_open_limit:
                self.state = "closed"
                self.failures = []
    
    def record_failure(self) -> None:
        """Record a failed request."""
        now = time.time()
        self.last_failure_time = now
        
        if self.state == "half-open":
            # Any failure in half-open state opens the circuit again
            self.state = "open"
            return
        
        # Add the failure and check if we need to open the circuit
        self.failures.append(now)
        if len(self.failures) >= self.failure_threshold:
            self.state = "open"


T = TypeVar('T')


class RetryHandler:
    """Handler for retrying operations with exponential backoff."""
    
    def __init__(
        self,
        max_retries: int = 3,
        backoff_factor: float = 0.5,
        jitter: bool = True,
        retry_exceptions: Optional[List[Type[Exception]]] = None,
    ):
        """Initialize a new RetryHandler.
        
        Args:
            max_retries: Maximum number of retries
            backoff_factor: Backoff factor for retry delays
            jitter: Whether to add jitter to retry delays
            retry_exceptions: List of exception types to retry on
        """
        self.max_retries = max_retries
        self.backoff_factor = backoff_factor
        self.jitter = jitter
        self.retry_exceptions = retry_exceptions or [
            AuthenticationError,
            IntegrationError,
            RateLimitError,
        ]
    
    async def execute(
        self,
        func: Callable[..., T],
        *args: Any,
        **kwargs: Any
    ) -> T:
        """Execute a function with retry logic.
        
        Args:
            func: Function to execute
            *args: Arguments for the function
            **kwargs: Keyword arguments for the function
            
        Returns:
            The result of the function
            
        Raises:
            The last exception if all retries fail
        """
        retries = 0
        last_exception = None
        
        while retries <= self.max_retries:
            try:
                if asyncio.iscoroutinefunction(func):
                    return await func(*args, **kwargs)
                else:
                    return func(*args, **kwargs)
            except tuple(self.retry_exceptions) as e:
                last_exception = e
                retries += 1
                
                if retries > self.max_retries:
                    break
                
                # Calculate delay with exponential backoff
                delay = self.backoff_factor * (2 ** (retries - 1))
                
                # Add jitter if enabled
                if self.jitter:
                    import random
                    delay = delay * (0.5 + random.random())
                
                # Special handling for rate limit errors with retry-after
                if isinstance(e, RateLimitError) and "retry_after" in e.details:
                    delay = e.details["retry_after"]
                
                # Log the retry
                logger.warning(
                    f"Retrying operation after error: {str(e)}. "
                    f"Retry {retries}/{self.max_retries} in {delay:.2f} seconds."
                )
                
                # Wait before retrying
                await asyncio.sleep(delay)
            except Exception as e:
                # Don't retry on other exceptions
                raise e
        
        # If we get here, all retries failed
        if last_exception:
            raise last_exception
        
        # This should never happen, but just in case
        raise SystemError(
            message="All retries failed with no exception",
            code=ErrorCode.SYSTEM_INTERNAL_ERROR,
        )


class ErrorHandler:
    """Handler for error processing, logging, and reporting."""
    
    def __init__(self, report_url: Optional[str] = None):
        """Initialize a new ErrorHandler.
        
        Args:
            report_url: URL for reporting errors
        """
        self.report_url = report_url
    
    def handle_error(self, error: Exception, context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Handle an error and return a formatted error response.
        
        Args:
            error: The error to handle
            context: Additional context for the error
            
        Returns:
            Formatted error response
        """
        # Log the error
        self.log_error(error, context)
        
        # Convert to a BaseError if it's not already
        if not isinstance(error, BaseError):
            error = self._convert_exception(error)
        
        # Return the formatted error response
        return error.to_dict()
    
    def log_error(self, error: Exception, context: Optional[Dict[str, Any]] = None) -> None:
        """Log an error for monitoring and debugging.
        
        Args:
            error: The error to log
            context: Additional context for the error
        """
        # Determine the log level based on the error severity
        log_level = logging.ERROR
        if isinstance(error, BaseError):
            if error.severity == ErrorSeverity.CRITICAL:
                log_level = logging.CRITICAL
            elif error.severity == ErrorSeverity.WARNING:
                log_level = logging.WARNING
            elif error.severity == ErrorSeverity.INFO:
                log_level = logging.INFO
        
        # Format the log message
        error_type = type(error).__name__
        error_message = str(error)
        context_str = f" Context: {context}" if context else ""
        
        # Log the error
        logger.log(
            log_level,
            f"{error_type}: {error_message}.{context_str}",
            exc_info=True,
        )
    
    async def report_error(self, error_report: Dict[str, Any]) -> Dict[str, Any]:
        """Report an error to the error tracking system.
        
        Args:
            error_report: The error report to submit
            
        Returns:
            Report ID and status
        """
        if not self.report_url:
            logger.warning("No report URL configured, error not reported")
            return {
                "report_id": str(uuid.uuid4()),
                "status": "received",
                "timestamp": datetime.datetime.now().isoformat(),
            }
        
        # In a real implementation, this would send the error report to a service
        # For now, we just log it and return a dummy response
        logger.info(f"Error report would be sent to {self.report_url}: {error_report}")
        
        return {
            "report_id": str(uuid.uuid4()),
            "status": "received",
            "timestamp": datetime.datetime.now().isoformat(),
        }
    
    def _convert_exception(self, exception: Exception) -> BaseError:
        """Convert a standard exception to a BaseError.
        
        Args:
            exception: The exception to convert
            
        Returns:
            A BaseError instance
        """
        error_type = type(exception).__name__
        error_message = str(exception)
        
        # Map common exception types to appropriate error classes
        if error_type in ("ConnectionError", "TimeoutError"):
            return IntegrationError(
                message=f"Connection error: {error_message}",
                code=ErrorCode.INTEGRATION_CONNECTION_FAILED,
            )
        elif error_type == "ValueError":
            return ValidationError(
                message=f"Validation error: {error_message}",
                code=ErrorCode.VALIDATION_INVALID_PARAMS,
            )
        elif error_type == "KeyError":
            return ResourceError(
                message=f"Resource not found: {error_message}",
                code=ErrorCode.RESOURCE_NOT_FOUND,
            )
        else:
            return SystemError(
                message=f"System error: {error_message}",
                code=ErrorCode.SYSTEM_INTERNAL_ERROR,
            )


# Singleton instance
_error_handler_instance: Optional[ErrorHandler] = None


def get_error_handler(report_url: Optional[str] = None) -> ErrorHandler:
    """Get the ErrorHandler singleton instance.
    
    Args:
        report_url: URL for reporting errors
        
    Returns:
        The ErrorHandler instance
    """
    global _error_handler_instance
    
    if _error_handler_instance is None:
        _error_handler_instance = ErrorHandler(report_url=report_url)
    
    return _error_handler_instance


class ErrorHandlingMiddleware:
    """Middleware for handling errors in API requests."""
    
    def __init__(self, app, error_handler: Optional[ErrorHandler] = None):
        """Initialize the middleware.
        
        Args:
            app: The application to wrap
            error_handler: The error handler to use
        """
        self.app = app
        self.error_handler = error_handler or get_error_handler()
    
    async def __call__(self, scope, receive, send):
        """Process a request and handle any errors.
        
        Args:
            scope: The request scope
            receive: The receive function
            send: The send function
        """
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return
        
        # Create a new send function that catches errors
        async def send_with_error_handling(message):
            await send(message)
        
        try:
            await self.app(scope, receive, send_with_error_handling)
        except Exception as e:
            # Handle the error
            error_response = self.error_handler.handle_error(e, {"scope": scope})
            
            # Convert the error response to a proper HTTP response
            if isinstance(e, BaseError):
                status_code = e.http_status
            else:
                status_code = 500
            
            # Send the response headers
            await send({
                "type": "http.response.start",
                "status": status_code,
                "headers": [
                    (b"content-type", b"application/json"),
                ],
            })
            
            # Send the response body
            await send({
                "type": "http.response.body",
                "body": json.dumps(error_response).encode("utf-8"),
            })
