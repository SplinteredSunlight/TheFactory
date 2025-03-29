"""
Tests for the error classes in the error handling module.

This module contains tests for the error classes in the AI-Orchestration-Platform.
"""

import json
import pytest
from src.orchestrator.error_handling import (
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
    Component
)


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
        assert auth_error.component == Component.AUTH
        
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
        
        # System error - use a specific component instead of Component.SYSTEM
        system_error = SystemError(
            message="Internal error",
            code=ErrorCode.SYSTEM_INTERNAL_ERROR,
            details={"subsystem": "database"},
            component=Component.ORCHESTRATOR  # Use a specific component
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
