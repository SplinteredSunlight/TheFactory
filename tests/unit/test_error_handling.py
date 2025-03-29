"""
Tests for the error handling protocol implementation.

This module contains tests for the error handling functionality in the AI-Orchestration-Platform.
"""

import asyncio
import datetime
import json
import pytest
import uuid
from unittest.mock import MagicMock, patch, AsyncMock

import sys
import os
from unittest.mock import MagicMock, patch, AsyncMock

# Add the src directory to the path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../src')))

# Mock external modules
sys.modules['mcp_agent'] = MagicMock()
sys.modules['mcp_agent.app'] = MagicMock()
sys.modules['mcp_agent.agents'] = MagicMock()
sys.modules['mcp_agent.agents.agent'] = MagicMock()
sys.modules['mcp_agent.workflows'] = MagicMock()
sys.modules['mcp_agent.workflows.llm'] = MagicMock()
sys.modules['mcp_agent.workflows.llm.augmented_llm_anthropic'] = MagicMock()
sys.modules['mcp_agent.workflows.llm.augmented_llm_openai'] = MagicMock()

from orchestrator.error_handling import (
    BaseError,
    AuthenticationError,
    AuthorizationError,
    ValidationError,
    ResourceError,
    IntegrationError,
    SystemError,
    RateLimitError,
    ErrorCode,
    ErrorSeverity,
    Component,
    CircuitBreaker,
    RetryHandler,
    ErrorHandler,
    get_error_handler
)

from fast_agent_integration.adapter import FastAgentAdapter


class TestErrorClasses:
    """Tests for the error classes."""

    def test_base_error(self):
        """Test the BaseError class."""
        error = BaseError(
            code="TEST.ERROR",
            message="Test error message",
            details={"key": "value"},
            severity=ErrorSeverity.ERROR,
            component=Component.FAST_AGENT,
            http_status=400,
            documentation_url="https://example.com/docs/errors/test-error"
        )
        
        # Check properties
        assert error.code == "TEST.ERROR"
        assert error.message == "Test error message"
        assert error.details == {"key": "value"}
        assert error.severity == ErrorSeverity.ERROR
        assert error.component == Component.FAST_AGENT
        assert error.http_status == 400
        assert error.documentation_url == "https://example.com/docs/errors/test-error"
        assert isinstance(error.request_id, str)
        assert isinstance(error.timestamp, str)
        
        # Check string representation
        assert str(error) == "Test error message"
        
        # Check dictionary representation
        error_dict = error.to_dict()
        assert error_dict["error"]["code"] == "TEST.ERROR"
        assert error_dict["error"]["message"] == "Test error message"
        assert error_dict["error"]["details"] == {"key": "value"}
        assert error_dict["error"]["severity"] == ErrorSeverity.ERROR
        assert error_dict["error"]["component"] == Component.FAST_AGENT
        assert error_dict["error"]["documentation_url"] == "https://example.com/docs/errors/test-error"
        
        # Check JSON representation
        error_json = error.to_json()
        error_from_json = json.loads(error_json)
        assert error_from_json["error"]["code"] == "TEST.ERROR"
        
        # Check from_dict method
        reconstructed_error = BaseError.from_dict(error_dict)
        assert reconstructed_error.code == "TEST.ERROR"
        assert reconstructed_error.message == "Test error message"

    def test_specific_error_classes(self):
        """Test the specific error classes."""
        # Authentication error
        auth_error = AuthenticationError(
            message="Invalid credentials",
            code=ErrorCode.AUTH_INVALID_CREDENTIALS,
            details={"client_id": "test-client"}
        )
        assert auth_error.code == ErrorCode.AUTH_INVALID_CREDENTIALS
        assert auth_error.http_status == 401
        assert auth_error.component == Component.AUTH
        
        # Authorization error
        authz_error = AuthorizationError(
            message="Insufficient scope",
            code=ErrorCode.AUTH_INSUFFICIENT_SCOPE,
            details={"required_scopes": ["read", "write"]}
        )
        assert authz_error.code == ErrorCode.AUTH_INSUFFICIENT_SCOPE
        assert authz_error.http_status == 403
        assert authz_error.component == Component.AUTH
        
        # Validation error
        validation_error = ValidationError(
            message="Invalid parameters",
            code=ErrorCode.VALIDATION_INVALID_PARAMS,
            details={"invalid_fields": ["name", "email"]}
        )
        assert validation_error.code == ErrorCode.VALIDATION_INVALID_PARAMS
        assert validation_error.http_status == 400
        
        # Resource error
        resource_error = ResourceError(
            message="Resource not found",
            code=ErrorCode.RESOURCE_NOT_FOUND,
            details={"resource_id": "123"}
        )
        assert resource_error.code == ErrorCode.RESOURCE_NOT_FOUND
        assert resource_error.http_status == 404
        
        # Integration error
        integration_error = IntegrationError(
            message="Connection failed",
            code=ErrorCode.INTEGRATION_CONNECTION_FAILED,
            details={"service": "external-api"}
        )
        assert integration_error.code == ErrorCode.INTEGRATION_CONNECTION_FAILED
        assert integration_error.http_status == 502
        
        # System error
        system_error = SystemError(
            message="Internal error",
            code=ErrorCode.SYSTEM_INTERNAL_ERROR,
            details={"subsystem": "database"}
        )
        assert system_error.code == ErrorCode.SYSTEM_INTERNAL_ERROR
        assert system_error.http_status == 500
        
        # Rate limit error
        rate_limit_error = RateLimitError(
            message="Rate limit exceeded",
            code=ErrorCode.RATE_LIMIT_EXCEEDED,
            details={"limit": 100, "current": 120},
            retry_after=60
        )
        assert rate_limit_error.code == ErrorCode.RATE_LIMIT_EXCEEDED
        assert rate_limit_error.http_status == 429
        assert rate_limit_error.details["retry_after"] == 60


class TestCircuitBreaker:
    """Tests for the CircuitBreaker class."""

    def test_initial_state(self):
        """Test the initial state of the circuit breaker."""
        cb = CircuitBreaker()
        assert cb.state == "closed"
        assert cb.allow_request() is True

    def test_open_circuit(self):
        """Test opening the circuit after failures."""
        cb = CircuitBreaker(failure_threshold=3)
        
        # Record failures
        for _ in range(3):
            cb.record_failure()
        
        # Circuit should be open
        assert cb.state == "open"
        assert cb.allow_request() is False

    def test_half_open_circuit(self):
        """Test transitioning to half-open state."""
        cb = CircuitBreaker(failure_threshold=3, reset_timeout=0.1)
        
        # Open the circuit
        for _ in range(3):
            cb.record_failure()
        
        assert cb.state == "open"
        
        # Wait for reset timeout
        import time
        time.sleep(0.2)
        
        # Circuit should be half-open
        assert cb.allow_request() is True
        assert cb.state == "half-open"

    def test_half_open_to_closed(self):
        """Test transitioning from half-open to closed state."""
        cb = CircuitBreaker(failure_threshold=3, reset_timeout=0.1, half_open_limit=2)
        
        # Open the circuit
        for _ in range(3):
            cb.record_failure()
        
        # Wait for reset timeout
        import time
        time.sleep(0.2)
        
        # Circuit should be half-open
        assert cb.allow_request() is True
        assert cb.state == "half-open"
        
        # Record successes
        cb.record_success()
        cb.record_success()
        
        # Circuit should be closed
        assert cb.state == "closed"
        assert cb.allow_request() is True

    def test_half_open_to_open(self):
        """Test transitioning from half-open to open state on failure."""
        cb = CircuitBreaker(failure_threshold=3, reset_timeout=0.1)
        
        # Open the circuit
        for _ in range(3):
            cb.record_failure()
        
        # Wait for reset timeout
        import time
        time.sleep(0.2)
        
        # Circuit should be half-open
        assert cb.allow_request() is True
        assert cb.state == "half-open"
        
        # Record a failure
        cb.record_failure()
        
        # Circuit should be open again
        assert cb.state == "open"
        assert cb.allow_request() is False


class TestRetryHandler:
    """Tests for the RetryHandler class."""

    @pytest.mark.asyncio
    async def test_successful_execution(self):
        """Test successful execution without retries."""
        handler = RetryHandler()
        
        # Mock function that succeeds
        mock_func = AsyncMock(return_value="success")
        
        result = await handler.execute(mock_func, "arg1", arg2="value2")
        
        assert result == "success"
        mock_func.assert_called_once_with("arg1", arg2="value2")

    @pytest.mark.asyncio
    async def test_retry_on_error(self):
        """Test retrying on error."""
        handler = RetryHandler(max_retries=2, backoff_factor=0.01)
        
        # Mock function that fails twice then succeeds
        mock_func = AsyncMock(side_effect=[
            AuthenticationError("Retry 1"),
            AuthenticationError("Retry 2"),
            "success"
        ])
        
        result = await handler.execute(mock_func)
        
        assert result == "success"
        assert mock_func.call_count == 3

    @pytest.mark.asyncio
    async def test_max_retries_exceeded(self):
        """Test exceeding maximum retries."""
        handler = RetryHandler(max_retries=2, backoff_factor=0.01)
        
        # Mock function that always fails
        error = AuthenticationError("Always fails")
        mock_func = AsyncMock(side_effect=error)
        
        with pytest.raises(AuthenticationError) as excinfo:
            await handler.execute(mock_func)
        
        assert mock_func.call_count == 3  # Initial call + 2 retries
        assert str(excinfo.value) == "Always fails"

    @pytest.mark.asyncio
    async def test_non_retryable_error(self):
        """Test non-retryable error."""
        handler = RetryHandler(max_retries=2, backoff_factor=0.01)
        
        # Mock function that raises a non-retryable error
        error = ValueError("Non-retryable")
        mock_func = AsyncMock(side_effect=error)
        
        with pytest.raises(ValueError) as excinfo:
            await handler.execute(mock_func)
        
        assert mock_func.call_count == 1  # Only the initial call
        assert str(excinfo.value) == "Non-retryable"

    @pytest.mark.asyncio
    async def test_rate_limit_error_with_retry_after(self):
        """Test rate limit error with retry-after header."""
        handler = RetryHandler(max_retries=1, backoff_factor=10)  # Large backoff to ensure it's not used
        
        # Mock function that fails with rate limit error then succeeds
        rate_limit_error = RateLimitError(
            message="Rate limited",
            retry_after=0.01  # Small value for testing
        )
        mock_func = AsyncMock(side_effect=[rate_limit_error, "success"])
        
        result = await handler.execute(mock_func)
        
        assert result == "success"
        assert mock_func.call_count == 2


class TestErrorHandler:
    """Tests for the ErrorHandler class."""

    def test_handle_error_base_error(self):
        """Test handling a BaseError."""
        handler = ErrorHandler()
        
        error = BaseError(
            code="TEST.ERROR",
            message="Test error message"
        )
        
        result = handler.handle_error(error)
        
        assert result["error"]["code"] == "TEST.ERROR"
        assert result["error"]["message"] == "Test error message"

    def test_handle_error_standard_exception(self):
        """Test handling a standard exception."""
        handler = ErrorHandler()
        
        error = ValueError("Invalid value")
        
        result = handler.handle_error(error)
        
        assert "error" in result
        assert "code" in result["error"]
        assert "message" in result["error"]
        assert "Validation error: Invalid value" in result["error"]["message"]

    def test_convert_exception(self):
        """Test converting standard exceptions to BaseError."""
        handler = ErrorHandler()
        
        # Test ValueError
        value_error = ValueError("Invalid value")
        converted = handler._convert_exception(value_error)
        assert isinstance(converted, ValidationError)
        assert "Invalid value" in converted.message
        
        # Test KeyError
        key_error = KeyError("missing_key")
        converted = handler._convert_exception(key_error)
        assert isinstance(converted, ResourceError)
        assert "missing_key" in converted.message
        
        # Test ConnectionError
        conn_error = ConnectionError("Connection failed")
        converted = handler._convert_exception(conn_error)
        assert isinstance(converted, IntegrationError)
        assert "Connection failed" in converted.message
        
        # Test generic exception
        generic_error = Exception("Generic error")
        converted = handler._convert_exception(generic_error)
        assert isinstance(converted, SystemError)
        assert "Generic error" in converted.message

    @pytest.mark.asyncio
    async def test_report_error(self):
        """Test reporting an error."""
        handler = ErrorHandler(report_url="https://example.com/report")
        
        error_report = {
            "error_code": "TEST.ERROR",
            "message": "Test error message",
            "severity": "ERROR"
        }
        
        result = await handler.report_error(error_report)
        
        assert "report_id" in result
        assert "status" in result
        assert result["status"] == "received"

    def test_get_error_handler(self):
        """Test getting the error handler singleton."""
        handler1 = get_error_handler()
        handler2 = get_error_handler()
        
        assert handler1 is handler2


@pytest.mark.asyncio
class TestFastAgentAdapterErrorHandling:
    """Tests for the FastAgentAdapter error handling."""

    async def test_authentication_error_handling(self):
        """Test handling authentication errors."""
        # Mock the orchestrator engine
        mock_orchestrator = AsyncMock()
        mock_orchestrator.authenticate.side_effect = AuthenticationError("Invalid API key")
        
        # Create adapter with mocked orchestrator
        with patch('fast_agent_integration.adapter.OrchestratorEngine', return_value=mock_orchestrator):
            with patch('fast_agent_integration.adapter.MCPApp'):
                adapter = FastAgentAdapter(app_name="test-app", api_key="invalid-key")
                
                # Test authentication
                result = await adapter.authenticate()
                
                assert result is False
                mock_orchestrator.authenticate.assert_called_once()

    async def test_circuit_breaker_integration(self):
        """Test circuit breaker integration."""
        # Mock the orchestrator engine
        mock_orchestrator = AsyncMock()
        
        # Create adapter with mocked orchestrator and circuit breaker
        with patch('fast_agent_integration.adapter.OrchestratorEngine', return_value=mock_orchestrator):
            with patch('fast_agent_integration.adapter.MCPApp'):
                adapter = FastAgentAdapter(app_name="test-app")
                
                # Mock the circuit breaker
                adapter.circuit_breaker = MagicMock()
                adapter.circuit_breaker.allow_request.return_value = False
                
                # Test create_agent with open circuit breaker
                with pytest.raises(IntegrationError) as excinfo:
                    await adapter.create_agent("test-agent", "test instruction")
                
                assert "Circuit breaker is open" in str(excinfo.value)
                assert excinfo.value.code == ErrorCode.INTEGRATION_CONNECTION_FAILED
                adapter.circuit_breaker.allow_request.assert_called_once()

    async def test_retry_handler_integration(self):
        """Test retry handler integration."""
        # Mock the orchestrator engine
        mock_orchestrator = AsyncMock()
        mock_orchestrator.authenticate.side_effect = [
            AuthenticationError("Temporary error"),
            {"access_token": "token", "refresh_token": "refresh", "expires_in": 3600}
        ]
        
        # Create adapter with mocked orchestrator
        with patch('fast_agent_integration.adapter.OrchestratorEngine', return_value=mock_orchestrator):
            with patch('fast_agent_integration.adapter.MCPApp'):
                adapter = FastAgentAdapter(app_name="test-app")
                
                # Test authentication with retry
                result = await adapter.authenticate()
                
                assert result is True
                assert mock_orchestrator.authenticate.call_count == 2
                assert adapter.access_token == "token"
                assert adapter.refresh_token == "refresh"
                assert adapter.token_expiry == 3600

    async def test_error_standardization(self):
        """Test error standardization."""
        # Mock the orchestrator engine
        mock_orchestrator = AsyncMock()
        mock_orchestrator.get_agent.side_effect = KeyError("agent_not_found")
        
        # Create adapter with mocked orchestrator
        with patch('fast_agent_integration.adapter.OrchestratorEngine', return_value=mock_orchestrator):
            with patch('fast_agent_integration.adapter.MCPApp'):
                with patch('fast_agent_integration.adapter.Agent'):
                    adapter = FastAgentAdapter(app_name="test-app")
                    
                    # Mock authentication
                    adapter.ensure_authenticated = AsyncMock(return_value=True)
                    
                    # Add a mock agent
                    adapter.active_agents = {"test-agent": MagicMock()}
                    
                    # Test run_agent with error
                    with pytest.raises(SystemError) as excinfo:
                        await adapter.run_agent("test-agent", "test query")
                    
                    assert excinfo.value.code == ErrorCode.FAST_AGENT_EXECUTION_FAILED
                    assert "test-agent" in excinfo.value.details["agent_id"]
