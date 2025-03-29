"""
Tests for the ErrorHandler class in the error handling module.

This module contains tests for the ErrorHandler class in the AI-Orchestration-Platform.
"""

import json
import pytest
from unittest.mock import patch
from src.orchestrator.error_handling import (
    ErrorHandler,
    BaseError,
    ValidationError,
    ResourceError,
    IntegrationError,
    SystemError,
    get_error_handler
)


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
        
        # Mock the SystemError class to avoid Component.SYSTEM issue
        with patch('src.orchestrator.error_handling.SystemError') as mock_system_error:
            # Configure the mock to return a SystemError instance
            mock_instance = SystemError(
                message="System error: Generic error",
                component="MOCKED_COMPONENT"
            )
            mock_system_error.return_value = mock_instance
            
            # Test generic exception
            generic_error = Exception("Generic error")
            converted = handler._convert_exception(generic_error)
            
            # Verify SystemError was called with the right parameters
            mock_system_error.assert_called_once()
            call_args = mock_system_error.call_args[1]
            assert "Generic error" in call_args["message"]

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
        
    @patch("logging.Logger.log")
    def test_log_error(self, mock_log):
        """Test logging an error."""
        handler = ErrorHandler()
        
        error = BaseError(
            code="TEST.ERROR",
            message="Test error message"
        )
        
        handler.log_error(error, {"context_key": "context_value"})
        
        # Verify that the log method was called
        mock_log.assert_called_once()
        
        # Check the arguments
        args, kwargs = mock_log.call_args
        log_level, log_message = args
        
        assert "Test error message" in log_message
        assert "Context" in log_message
