"""
Tests for the Result Reporting System.

This module contains tests for the Result Reporting System client library.
"""

import asyncio
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from datetime import datetime

from src.fast_agent_integration.result_reporting import (
    ResultReportingClient,
    get_result_reporting_client,
    ResultType,
    ResultSeverity
)


@pytest.fixture
def mock_orchestrator_client():
    """Create a mock orchestrator client."""
    mock_client = AsyncMock()
    mock_client.handle_task_response = AsyncMock(return_value={"status": "success"})
    mock_client.send_agent_message = AsyncMock(return_value="message-123")
    mock_client.update_agent_status_in_distributor = AsyncMock(return_value={"status": "updated"})
    mock_client.shutdown = AsyncMock()
    return mock_client


@pytest.fixture
async def result_reporting_client(mock_orchestrator_client):
    """Create a result reporting client with a mock orchestrator client."""
    with patch("src.fast_agent_integration.result_reporting.get_client", return_value=mock_orchestrator_client):
        client = ResultReportingClient(
            agent_id="test-agent",
            api_key="test-key",
            client_id="test-client"
        )
        client.orchestrator = mock_orchestrator_client
        # Disable background task
        client._flush_cache_periodically = AsyncMock()
        await client.initialize()
        yield client


class TestResultReportingClient:
    """Tests for the ResultReportingClient class."""

    @pytest.mark.asyncio
    async def test_initialization(self, result_reporting_client, mock_orchestrator_client):
        """Test that the client initializes correctly."""
        assert result_reporting_client.agent_id == "test-agent"
        assert result_reporting_client.api_key == "test-key"
        assert result_reporting_client.client_id == "test-client"
        assert result_reporting_client.orchestrator == mock_orchestrator_client
        assert result_reporting_client.result_cache == []

    @pytest.mark.asyncio
    async def test_report_task_completion(self, result_reporting_client, mock_orchestrator_client):
        """Test reporting task completion."""
        task_id = "task-123"
        result_data = {"output": "Task completed successfully"}
        
        success = await result_reporting_client.report_task_completion(
            task_id=task_id,
            result_data=result_data
        )
        
        assert success is True
        mock_orchestrator_client.handle_task_response.assert_called_once_with(
            task_id=task_id,
            agent_id="test-agent",
            status="completed",
            result=result_data,
            error=None
        )

    @pytest.mark.asyncio
    async def test_report_task_progress(self, result_reporting_client, mock_orchestrator_client):
        """Test reporting task progress."""
        task_id = "task-123"
        progress_data = {"percent_complete": 50, "message": "Halfway there"}
        
        success = await result_reporting_client.report_task_progress(
            task_id=task_id,
            progress_data=progress_data
        )
        
        assert success is True
        mock_orchestrator_client.send_agent_message.assert_called_once()
        call_args = mock_orchestrator_client.send_agent_message.call_args[1]
        assert call_args["sender_id"] == "test-agent"
        assert call_args["message_type"] == "task_progress"
        assert call_args["content"]["task_id"] == task_id
        assert call_args["content"]["progress"] == progress_data
        assert "timestamp" in call_args["content"]
        assert call_args["recipient_id"] == "orchestrator"
        assert call_args["correlation_id"] == task_id

    @pytest.mark.asyncio
    async def test_report_task_error(self, result_reporting_client, mock_orchestrator_client):
        """Test reporting task error."""
        task_id = "task-123"
        error_message = "Task failed due to network error"
        error_details = {"status_code": 500, "service": "external-api"}
        
        success = await result_reporting_client.report_task_error(
            task_id=task_id,
            error_message=error_message,
            error_details=error_details
        )
        
        assert success is True
        mock_orchestrator_client.handle_task_response.assert_called_once_with(
            task_id=task_id,
            agent_id="test-agent",
            status="failed",
            result=None,
            error=error_message
        )

    @pytest.mark.asyncio
    async def test_report_agent_status(self, result_reporting_client, mock_orchestrator_client):
        """Test reporting agent status."""
        is_online = True
        current_load = 5
        
        success = await result_reporting_client.report_agent_status(
            is_online=is_online,
            current_load=current_load
        )
        
        assert success is True
        mock_orchestrator_client.update_agent_status_in_distributor.assert_called_once_with(
            agent_id="test-agent",
            is_online=is_online,
            current_load=current_load
        )

    @pytest.mark.asyncio
    async def test_report_agent_metrics(self, result_reporting_client, mock_orchestrator_client):
        """Test reporting agent metrics."""
        metrics = {
            "requests_processed": 100,
            "average_response_time": 0.5,
            "error_rate": 0.01
        }
        
        success = await result_reporting_client.report_agent_metrics(
            metrics=metrics
        )
        
        assert success is True
        mock_orchestrator_client.send_agent_message.assert_called_once()
        call_args = mock_orchestrator_client.send_agent_message.call_args[1]
        assert call_args["sender_id"] == "test-agent"
        assert call_args["message_type"] == "agent_metrics"
        assert call_args["content"]["metrics"] == metrics
        assert "timestamp" in call_args["content"]
        assert call_args["recipient_id"] == "orchestrator"
        assert call_args["priority"] == "low"

    @pytest.mark.asyncio
    async def test_report_agent_log(self, result_reporting_client, mock_orchestrator_client):
        """Test reporting agent log."""
        log_message = "Agent started processing task"
        severity = ResultSeverity.INFO
        log_context = {"task_id": "task-123", "timestamp": datetime.now().isoformat()}
        
        success = await result_reporting_client.report_agent_log(
            log_message=log_message,
            severity=severity,
            log_context=log_context
        )
        
        assert success is True
        mock_orchestrator_client.send_agent_message.assert_called_once()
        call_args = mock_orchestrator_client.send_agent_message.call_args[1]
        assert call_args["sender_id"] == "test-agent"
        assert call_args["message_type"] == "agent_log"
        assert call_args["content"]["log"]["message"] == log_message
        assert call_args["content"]["log"]["context"] == log_context
        assert call_args["content"]["severity"] == severity
        assert "timestamp" in call_args["content"]
        assert call_args["recipient_id"] == "orchestrator"
        assert call_args["priority"] == "low"

    @pytest.mark.asyncio
    async def test_report_custom_result(self, result_reporting_client, mock_orchestrator_client):
        """Test reporting custom result."""
        result_id = "custom-result-123"
        data = {"key": "value", "nested": {"field": 42}}
        recipient_id = "another-agent"
        correlation_id = "correlation-123"
        priority = "high"
        
        success = await result_reporting_client.report_custom_result(
            result_id=result_id,
            data=data,
            recipient_id=recipient_id,
            correlation_id=correlation_id,
            priority=priority
        )
        
        assert success is True
        mock_orchestrator_client.send_agent_message.assert_called_once()
        call_args = mock_orchestrator_client.send_agent_message.call_args[1]
        assert call_args["sender_id"] == "test-agent"
        assert call_args["message_type"] == "custom_result"
        assert call_args["content"]["result_id"] == result_id
        assert call_args["content"]["data"] == data
        assert "timestamp" in call_args["content"]
        assert call_args["recipient_id"] == recipient_id
        assert call_args["correlation_id"] == correlation_id
        assert call_args["priority"] == priority

    @pytest.mark.asyncio
    async def test_cache_and_flush(self, result_reporting_client, mock_orchestrator_client):
        """Test caching results and flushing the cache."""
        # Disable immediate sending
        task_id = "task-123"
        result_data = {"output": "Task completed successfully"}
        
        # Add to cache but don't send immediately
        success = await result_reporting_client.report_task_completion(
            task_id=task_id,
            result_data=result_data,
            send_immediately=False
        )
        
        assert success is True
        assert len(result_reporting_client.result_cache) == 1
        mock_orchestrator_client.handle_task_response.assert_not_called()
        
        # Flush the cache
        flush_success = await result_reporting_client.flush_cache()
        
        assert flush_success is True
        assert len(result_reporting_client.result_cache) == 0
        mock_orchestrator_client.handle_task_response.assert_called_once()

    @pytest.mark.asyncio
    async def test_shutdown(self, result_reporting_client, mock_orchestrator_client):
        """Test shutting down the client."""
        # Add something to the cache
        await result_reporting_client.report_task_completion(
            task_id="task-123",
            result_data={"output": "Task completed successfully"},
            send_immediately=False
        )
        
        # Shutdown
        await result_reporting_client.shutdown()
        
        # Cache should be flushed
        assert len(result_reporting_client.result_cache) == 0
        mock_orchestrator_client.handle_task_response.assert_called_once()
        mock_orchestrator_client.shutdown.assert_called_once()

    @pytest.mark.asyncio
    async def test_circuit_breaker(self, result_reporting_client, mock_orchestrator_client):
        """Test circuit breaker functionality."""
        # Make the orchestrator client raise an exception
        mock_orchestrator_client.handle_task_response.side_effect = Exception("Connection error")
        
        # Record failures to open the circuit breaker
        result_reporting_client.circuit_breaker.failure_threshold = 2
        
        # First failure
        success = await result_reporting_client.report_task_completion(
            task_id="task-1",
            result_data={"output": "Task completed successfully"}
        )
        assert success is False
        
        # Second failure
        success = await result_reporting_client.report_task_completion(
            task_id="task-2",
            result_data={"output": "Task completed successfully"}
        )
        assert success is False
        
        # Circuit breaker should be open now
        assert not result_reporting_client.circuit_breaker.allow_request()
        
        # Reset the circuit breaker for other tests
        result_reporting_client.circuit_breaker.reset()


@pytest.mark.asyncio
async def test_get_result_reporting_client():
    """Test the get_result_reporting_client function."""
    with patch("src.fast_agent_integration.result_reporting.ResultReportingClient") as mock_client_class:
        mock_client = AsyncMock()
        mock_client_class.return_value = mock_client
        
        # First call should create a new client
        client1 = await get_result_reporting_client(
            agent_id="test-agent",
            api_key="test-key"
        )
        
        assert client1 == mock_client
        mock_client_class.assert_called_once_with(
            agent_id="test-agent",
            api_key="test-key",
            client_id=None,
            base_url=None
        )
        mock_client.initialize.assert_called_once()
        
        # Reset mocks
        mock_client_class.reset_mock()
        mock_client.initialize.reset_mock()
        
        # Second call with same agent_id should return the same client
        client2 = await get_result_reporting_client(
            agent_id="test-agent",
            api_key="different-key"  # This should be ignored
        )
        
        assert client2 == client1
        mock_client_class.assert_not_called()
        mock_client.initialize.assert_not_called()
        
        # Call with different agent_id should create a new client
        mock_client2 = AsyncMock()
        mock_client_class.return_value = mock_client2
        
        client3 = await get_result_reporting_client(
            agent_id="another-agent"
        )
        
        assert client3 == mock_client2
        mock_client_class.assert_called_once()
        mock_client2.initialize.assert_called_once()
