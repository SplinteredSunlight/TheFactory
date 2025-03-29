"""
Result Reporting System Module

This module provides a client library for reporting detailed results from agents
back to the AI-Orchestration-Platform. It handles authentication, error handling,
and provides methods for reporting various types of results.
"""

import asyncio
import logging
import os
from datetime import datetime
from typing import Any, Dict, List, Optional, Union, Callable

from src.orchestrator.auth import AuthenticationError, AuthorizationError
from src.orchestrator.error_handling import (
    BaseError,
    ErrorCode,
    ErrorSeverity,
    Component,
    ResourceError,
    IntegrationError,
    SystemError,
    RetryHandler,
    CircuitBreaker,
    get_error_handler
)

# Import the Orchestrator API Client
from src.fast_agent_integration.orchestrator_client import get_client

# Configure logging
logger = logging.getLogger(__name__)

# Error handler
error_handler = get_error_handler()


class ResultType:
    """Types of results that can be reported."""
    TASK_COMPLETION = "task_completion"
    TASK_PROGRESS = "task_progress"
    TASK_ERROR = "task_error"
    AGENT_STATUS = "agent_status"
    AGENT_METRICS = "agent_metrics"
    AGENT_LOG = "agent_log"
    CUSTOM = "custom"


class ResultSeverity:
    """Severity levels for reported results."""
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"
    DEBUG = "debug"


class ResultReportingClient:
    """Client for reporting results back to the AI-Orchestration-Platform."""

    def __init__(
        self,
        agent_id: str,
        api_key: Optional[str] = None,
        client_id: Optional[str] = None,
        base_url: Optional[str] = None,
    ):
        """Initialize the Result Reporting Client.

        Args:
            agent_id: ID of the agent reporting results
            api_key: API key for authenticating with the orchestrator
            client_id: Identifier for the client
            base_url: Base URL for the orchestrator API (for remote orchestrators)
        """
        self.agent_id = agent_id
        self.api_key = api_key or os.environ.get("ORCHESTRATOR_API_KEY") or "fast-agent-default-key"
        self.client_id = client_id or f"result-reporter-{agent_id}"
        self.base_url = base_url
        
        # Orchestrator client (will be initialized in initialize())
        self.orchestrator = None
        
        # Error handling
        self.retry_handler = RetryHandler(
            max_retries=3,
            backoff_factor=0.5,
            jitter=True
        )
        self.circuit_breaker = CircuitBreaker(
            failure_threshold=5,
            reset_timeout=30,
            half_open_limit=3
        )
        
        # Result cache for offline operation
        self.result_cache = []
        self.max_cache_size = 100
        self.is_flushing = False
        self.flush_lock = asyncio.Lock()

    async def initialize(self) -> None:
        """Initialize the client and authenticate with the orchestrator."""
        # Get the orchestrator client
        self.orchestrator = await get_client(
            api_key=self.api_key,
            client_id=self.client_id,
            base_url=self.base_url,
        )
        
        # Start background task to flush cached results
        asyncio.create_task(self._flush_cache_periodically())

    async def _flush_cache_periodically(self, interval: int = 60) -> None:
        """Periodically flush the result cache.
        
        Args:
            interval: Interval in seconds between flush attempts
        """
        while True:
            await asyncio.sleep(interval)
            if self.result_cache:
                await self.flush_cache()

    async def flush_cache(self) -> bool:
        """Flush the result cache to the orchestrator.
        
        Returns:
            True if the cache was flushed successfully, False otherwise
        """
        if not self.result_cache or self.is_flushing:
            return True
        
        async with self.flush_lock:
            self.is_flushing = True
            try:
                # Copy the cache to avoid modification during iteration
                cache_copy = self.result_cache.copy()
                self.result_cache = []
                
                # Send each result
                for result in cache_copy:
                    try:
                        await self._send_result(result)
                    except Exception as e:
                        # If sending fails, add back to the cache
                        self.result_cache.append(result)
                        logger.warning(f"Failed to send cached result: {str(e)}")
                        
                        # If we've reached the circuit breaker limit, stop trying
                        if not self.circuit_breaker.allow_request():
                            logger.error("Circuit breaker open, stopping cache flush")
                            self.result_cache.extend(cache_copy[cache_copy.index(result) + 1:])
                            return False
                
                return True
            finally:
                self.is_flushing = False

    async def _send_result(self, result: Dict[str, Any]) -> bool:
        """Send a result to the orchestrator.
        
        Args:
            result: Result data to send
            
        Returns:
            True if the result was sent successfully, False otherwise
            
        Raises:
            AuthenticationError: If authentication fails
            AuthorizationError: If the client doesn't have the required permissions
            Various other exceptions depending on the result type
        """
        # Check if circuit breaker allows the request
        if not self.circuit_breaker.allow_request():
            raise IntegrationError(
                message="Circuit breaker is open, too many recent failures",
                code=ErrorCode.INTEGRATION_CONNECTION_FAILED,
                component=Component.FAST_AGENT,
                severity=ErrorSeverity.ERROR,
                details={"circuit_breaker_state": "open"}
            )
        
        try:
            # Handle different result types
            result_type = result.get("type")
            
            if result_type == ResultType.TASK_COMPLETION:
                # Handle task completion
                await self.orchestrator.handle_task_response(
                    task_id=result["task_id"],
                    agent_id=self.agent_id,
                    status="completed",
                    result=result["data"],
                    error=None
                )
            
            elif result_type == ResultType.TASK_PROGRESS:
                # For progress updates, we use the agent message system
                await self.orchestrator.send_agent_message(
                    sender_id=self.agent_id,
                    message_type="task_progress",
                    content={
                        "task_id": result["task_id"],
                        "progress": result["data"],
                        "timestamp": result["timestamp"]
                    },
                    recipient_id="orchestrator",
                    correlation_id=result["task_id"],
                    priority="medium"
                )
            
            elif result_type == ResultType.TASK_ERROR:
                # Handle task error
                await self.orchestrator.handle_task_response(
                    task_id=result["task_id"],
                    agent_id=self.agent_id,
                    status="failed",
                    result=None,
                    error=result["data"]["message"]
                )
            
            elif result_type == ResultType.AGENT_STATUS:
                # Update agent status
                await self.orchestrator.update_agent_status_in_distributor(
                    agent_id=self.agent_id,
                    is_online=result["data"]["is_online"],
                    current_load=result["data"].get("current_load")
                )
            
            elif result_type == ResultType.AGENT_METRICS:
                # For metrics, we use the agent message system
                await self.orchestrator.send_agent_message(
                    sender_id=self.agent_id,
                    message_type="agent_metrics",
                    content={
                        "metrics": result["data"],
                        "timestamp": result["timestamp"]
                    },
                    recipient_id="orchestrator",
                    priority="low"
                )
            
            elif result_type == ResultType.AGENT_LOG:
                # For logs, we use the agent message system
                await self.orchestrator.send_agent_message(
                    sender_id=self.agent_id,
                    message_type="agent_log",
                    content={
                        "log": result["data"],
                        "severity": result.get("severity", "info"),
                        "timestamp": result["timestamp"]
                    },
                    recipient_id="orchestrator",
                    priority="low"
                )
            
            elif result_type == ResultType.CUSTOM:
                # For custom results, we use the agent message system
                await self.orchestrator.send_agent_message(
                    sender_id=self.agent_id,
                    message_type="custom_result",
                    content={
                        "result_id": result.get("result_id", "unknown"),
                        "data": result["data"],
                        "timestamp": result["timestamp"]
                    },
                    recipient_id=result.get("recipient_id", "orchestrator"),
                    correlation_id=result.get("correlation_id"),
                    priority=result.get("priority", "medium")
                )
            
            # Record success with circuit breaker
            self.circuit_breaker.record_success()
            
            return True
            
        except (AuthenticationError, AuthorizationError) as e:
            # Record failure with circuit breaker
            self.circuit_breaker.record_failure()
            
            # Log the error
            error_handler.log_error(e, {
                "agent_id": self.agent_id,
                "result_type": result.get("type")
            })
            
            raise
        except Exception as e:
            # Record failure with circuit breaker
            self.circuit_breaker.record_failure()
            
            # Log the error
            error_handler.log_error(e, {
                "agent_id": self.agent_id,
                "result_type": result.get("type")
            })
            
            raise

    async def _add_to_cache(self, result: Dict[str, Any]) -> None:
        """Add a result to the cache.
        
        Args:
            result: Result data to cache
        """
        # Add timestamp if not present
        if "timestamp" not in result:
            result["timestamp"] = datetime.now().isoformat()
        
        # Add to cache
        self.result_cache.append(result)
        
        # Trim cache if it gets too large
        if len(self.result_cache) > self.max_cache_size:
            # Remove oldest entries
            self.result_cache = self.result_cache[-self.max_cache_size:]
            logger.warning(f"Result cache exceeded max size, trimmed to {self.max_cache_size} entries")

    async def report_result(self, result: Dict[str, Any], send_immediately: bool = True) -> bool:
        """Report a result to the orchestrator.
        
        Args:
            result: Result data to report
            send_immediately: Whether to send the result immediately or cache it
            
        Returns:
            True if the result was sent or cached successfully, False otherwise
        """
        # Add to cache
        await self._add_to_cache(result)
        
        # Send immediately if requested
        if send_immediately:
            try:
                return await self._send_result(result)
            except Exception as e:
                logger.warning(f"Failed to send result immediately, will retry later: {str(e)}")
                return False
        
        return True

    async def report_task_completion(
        self,
        task_id: str,
        result_data: Dict[str, Any],
        send_immediately: bool = True
    ) -> bool:
        """Report task completion.
        
        Args:
            task_id: ID of the completed task
            result_data: Result data for the task
            send_immediately: Whether to send the result immediately or cache it
            
        Returns:
            True if the result was sent or cached successfully, False otherwise
        """
        result = {
            "type": ResultType.TASK_COMPLETION,
            "task_id": task_id,
            "data": result_data,
            "timestamp": datetime.now().isoformat()
        }
        
        return await self.report_result(result, send_immediately)

    async def report_task_progress(
        self,
        task_id: str,
        progress_data: Dict[str, Any],
        send_immediately: bool = True
    ) -> bool:
        """Report task progress.
        
        Args:
            task_id: ID of the task
            progress_data: Progress data for the task
            send_immediately: Whether to send the result immediately or cache it
            
        Returns:
            True if the result was sent or cached successfully, False otherwise
        """
        result = {
            "type": ResultType.TASK_PROGRESS,
            "task_id": task_id,
            "data": progress_data,
            "timestamp": datetime.now().isoformat()
        }
        
        return await self.report_result(result, send_immediately)

    async def report_task_error(
        self,
        task_id: str,
        error_message: str,
        error_details: Optional[Dict[str, Any]] = None,
        send_immediately: bool = True
    ) -> bool:
        """Report task error.
        
        Args:
            task_id: ID of the task
            error_message: Error message
            error_details: Additional error details
            send_immediately: Whether to send the result immediately or cache it
            
        Returns:
            True if the result was sent or cached successfully, False otherwise
        """
        result = {
            "type": ResultType.TASK_ERROR,
            "task_id": task_id,
            "data": {
                "message": error_message,
                "details": error_details or {}
            },
            "timestamp": datetime.now().isoformat()
        }
        
        return await self.report_result(result, send_immediately)

    async def report_agent_status(
        self,
        is_online: bool,
        current_load: Optional[int] = None,
        send_immediately: bool = True
    ) -> bool:
        """Report agent status.
        
        Args:
            is_online: Whether the agent is online
            current_load: Current load of the agent (number of active tasks)
            send_immediately: Whether to send the result immediately or cache it
            
        Returns:
            True if the result was sent or cached successfully, False otherwise
        """
        result = {
            "type": ResultType.AGENT_STATUS,
            "data": {
                "is_online": is_online,
                "current_load": current_load
            },
            "timestamp": datetime.now().isoformat()
        }
        
        return await self.report_result(result, send_immediately)

    async def report_agent_metrics(
        self,
        metrics: Dict[str, Any],
        send_immediately: bool = True
    ) -> bool:
        """Report agent metrics.
        
        Args:
            metrics: Dictionary of metrics to report
            send_immediately: Whether to send the result immediately or cache it
            
        Returns:
            True if the result was sent or cached successfully, False otherwise
        """
        result = {
            "type": ResultType.AGENT_METRICS,
            "data": metrics,
            "timestamp": datetime.now().isoformat()
        }
        
        return await self.report_result(result, send_immediately)

    async def report_agent_log(
        self,
        log_message: str,
        severity: str = ResultSeverity.INFO,
        log_context: Optional[Dict[str, Any]] = None,
        send_immediately: bool = True
    ) -> bool:
        """Report agent log.
        
        Args:
            log_message: Log message
            severity: Severity of the log message
            log_context: Additional context for the log message
            send_immediately: Whether to send the result immediately or cache it
            
        Returns:
            True if the result was sent or cached successfully, False otherwise
        """
        result = {
            "type": ResultType.AGENT_LOG,
            "data": {
                "message": log_message,
                "context": log_context or {}
            },
            "severity": severity,
            "timestamp": datetime.now().isoformat()
        }
        
        return await self.report_result(result, send_immediately)

    async def report_custom_result(
        self,
        result_id: str,
        data: Dict[str, Any],
        recipient_id: Optional[str] = None,
        correlation_id: Optional[str] = None,
        priority: str = "medium",
        send_immediately: bool = True
    ) -> bool:
        """Report a custom result.
        
        Args:
            result_id: Identifier for the result
            data: Result data
            recipient_id: ID of the recipient (None for orchestrator)
            correlation_id: ID to correlate related results
            priority: Priority of the result (high, medium, low)
            send_immediately: Whether to send the result immediately or cache it
            
        Returns:
            True if the result was sent or cached successfully, False otherwise
        """
        result = {
            "type": ResultType.CUSTOM,
            "result_id": result_id,
            "data": data,
            "recipient_id": recipient_id,
            "correlation_id": correlation_id,
            "priority": priority,
            "timestamp": datetime.now().isoformat()
        }
        
        return await self.report_result(result, send_immediately)

    async def shutdown(self) -> None:
        """Shutdown the client and flush any cached results."""
        # Flush the cache
        await self.flush_cache()
        
        # Shutdown the orchestrator client
        if self.orchestrator:
            await self.orchestrator.shutdown()


# Singleton instances by agent ID
_client_instances: Dict[str, ResultReportingClient] = {}


async def get_result_reporting_client(
    agent_id: str,
    api_key: Optional[str] = None,
    client_id: Optional[str] = None,
    base_url: Optional[str] = None,
) -> ResultReportingClient:
    """Get a ResultReportingClient instance for an agent.

    Args:
        agent_id: ID of the agent reporting results
        api_key: API key for authenticating with the orchestrator
        client_id: Identifier for the client
        base_url: Base URL for the orchestrator API (for remote orchestrators)

    Returns:
        The ResultReportingClient instance
    """
    global _client_instances
    
    if agent_id not in _client_instances:
        _client_instances[agent_id] = ResultReportingClient(
            agent_id=agent_id,
            api_key=api_key,
            client_id=client_id,
            base_url=base_url,
        )
        await _client_instances[agent_id].initialize()
    
    return _client_instances[agent_id]
