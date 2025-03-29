"""
Tests for the RetryHandler class in the error handling module.

This module contains tests for the RetryHandler class in the AI-Orchestration-Platform.
"""

import pytest
from unittest.mock import AsyncMock
from src.orchestrator.error_handling import (
    RetryHandler,
    AuthenticationError,
    RateLimitError,
    ErrorCode
)


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
