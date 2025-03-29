"""
Rate Limiting Module for AI-Orchestration-Platform

This module provides rate limiting functionality for the Agent Communication Module.
It helps prevent abuse and ensures fair usage of the communication system.
"""

import asyncio
import logging
import time
from datetime import datetime
from enum import Enum
from typing import Dict, List, Any, Optional, Set, Tuple, Union, DefaultDict
from collections import defaultdict

from src.orchestrator.error_handling import (
    BaseError,
    ErrorCode,
    ErrorSeverity,
    Component,
    ResourceError,
    get_error_handler
)

# Configure logging
logger = logging.getLogger(__name__)

# Error handler
error_handler = get_error_handler()


class RateLimitExceededError(BaseError):
    """Error raised when rate limit is exceeded."""
    
    def __init__(
        self,
        message: str,
        details: Optional[Dict[str, Any]] = None,
        retry_after: int = 60,
        severity: ErrorSeverity = ErrorSeverity.WARNING,
    ):
        super().__init__(
            code=ErrorCode.RATE_LIMIT_EXCEEDED,
            message=message,
            details=details,
            severity=severity,
            component=Component.ORCHESTRATOR,
            http_status=429,
            documentation_url=None,
        )
        self.retry_after = retry_after


class RateLimitType(str, Enum):
    """Types of rate limits."""
    AGENT = "agent"  # Rate limit per agent
    MESSAGE_TYPE = "message_type"  # Rate limit per message type
    PRIORITY = "priority"  # Rate limit per priority level
    GLOBAL = "global"  # Global rate limit


class RateLimiter:
    """
    Rate limiter for the Agent Communication Module.
    
    The RateLimiter is responsible for:
    1. Enforcing rate limits on message sending
    2. Implementing different rate limit types
    3. Handling burst allowances
    4. Providing retry-after information
    """
    
    def __init__(self):
        """Initialize a new RateLimiter."""
        # Rate limit configurations
        self.rate_limits = {
            RateLimitType.AGENT: {
                "default": (100, 60),  # 100 messages per minute per agent
            },
            RateLimitType.MESSAGE_TYPE: {
                "direct": (50, 60),  # 50 direct messages per minute
                "broadcast": (10, 60),  # 10 broadcast messages per minute
                "task_request": (20, 60),  # 20 task requests per minute
                "task_response": (20, 60),  # 20 task responses per minute
                "status_update": (30, 60),  # 30 status updates per minute
                "error": (20, 60),  # 20 error messages per minute
                "system": (10, 60),  # 10 system messages per minute
                "default": (50, 60),  # Default: 50 messages per minute
            },
            RateLimitType.PRIORITY: {
                "high": (50, 60),  # 50 high priority messages per minute
                "medium": (100, 60),  # 100 medium priority messages per minute
                "low": (200, 60),  # 200 low priority messages per minute
                "default": (100, 60),  # Default: 100 messages per minute
            },
            RateLimitType.GLOBAL: {
                "default": (1000, 60),  # 1000 messages per minute globally
            },
        }
        
        # Token buckets for rate limiting
        self.token_buckets: DefaultDict[str, Dict[str, Any]] = defaultdict(dict)
        
        # Lock for thread safety
        self.lock = asyncio.Lock()
        
        # Start the token replenishment task
        self.replenishment_task = asyncio.create_task(self._replenish_tokens())
    
    async def check_rate_limit(
        self,
        agent_id: str,
        message_type: str,
        priority: str,
    ) -> Tuple[bool, Optional[int]]:
        """
        Check if a message exceeds the rate limit.
        
        Args:
            agent_id: ID of the agent sending the message
            message_type: Type of the message
            priority: Priority of the message
            
        Returns:
            Tuple of (is_allowed, retry_after)
            is_allowed: True if the message is allowed, False if it exceeds the rate limit
            retry_after: Seconds to wait before retrying, or None if the message is allowed
        """
        async with self.lock:
            now = time.time()
            
            # Check agent rate limit
            agent_bucket = self._get_or_create_bucket(
                f"agent:{agent_id}",
                *self.rate_limits[RateLimitType.AGENT].get("default")
            )
            if agent_bucket["tokens"] < 1:
                retry_after = int(agent_bucket["last_replenished"] + agent_bucket["interval"] - now)
                return False, max(1, retry_after)
            
            # Check message type rate limit
            message_type_bucket = self._get_or_create_bucket(
                f"message_type:{message_type}",
                *self.rate_limits[RateLimitType.MESSAGE_TYPE].get(
                    message_type,
                    self.rate_limits[RateLimitType.MESSAGE_TYPE]["default"]
                )
            )
            if message_type_bucket["tokens"] < 1:
                retry_after = int(message_type_bucket["last_replenished"] + message_type_bucket["interval"] - now)
                return False, max(1, retry_after)
            
            # Check priority rate limit
            priority_bucket = self._get_or_create_bucket(
                f"priority:{priority}",
                *self.rate_limits[RateLimitType.PRIORITY].get(
                    priority,
                    self.rate_limits[RateLimitType.PRIORITY]["default"]
                )
            )
            if priority_bucket["tokens"] < 1:
                retry_after = int(priority_bucket["last_replenished"] + priority_bucket["interval"] - now)
                return False, max(1, retry_after)
            
            # Check global rate limit
            global_bucket = self._get_or_create_bucket(
                "global",
                *self.rate_limits[RateLimitType.GLOBAL]["default"]
            )
            if global_bucket["tokens"] < 1:
                retry_after = int(global_bucket["last_replenished"] + global_bucket["interval"] - now)
                return False, max(1, retry_after)
            
            # Consume tokens
            agent_bucket["tokens"] -= 1
            message_type_bucket["tokens"] -= 1
            priority_bucket["tokens"] -= 1
            global_bucket["tokens"] -= 1
            
            return True, None
    
    def _get_or_create_bucket(
        self,
        key: str,
        max_tokens: int,
        interval: int
    ) -> Dict[str, Any]:
        """
        Get or create a token bucket.
        
        Args:
            key: Key for the bucket
            max_tokens: Maximum number of tokens in the bucket
            interval: Interval in seconds for token replenishment
            
        Returns:
            Token bucket dictionary
        """
        now = time.time()
        
        if key not in self.token_buckets:
            self.token_buckets[key] = {
                "tokens": max_tokens,
                "max_tokens": max_tokens,
                "interval": interval,
                "last_replenished": now,
            }
        
        return self.token_buckets[key]
    
    async def _replenish_tokens(self) -> None:
        """Periodically replenish tokens in all buckets."""
        while True:
            try:
                await asyncio.sleep(1)  # Check every second
                
                async with self.lock:
                    now = time.time()
                    
                    for key, bucket in self.token_buckets.items():
                        # Calculate time since last replenishment
                        time_passed = now - bucket["last_replenished"]
                        
                        # Calculate tokens to add
                        tokens_to_add = (time_passed / bucket["interval"]) * bucket["max_tokens"]
                        
                        if tokens_to_add >= 1:
                            # Add tokens
                            bucket["tokens"] = min(
                                bucket["tokens"] + int(tokens_to_add),
                                bucket["max_tokens"]
                            )
                            
                            # Update last replenished time
                            bucket["last_replenished"] = now
            except asyncio.CancelledError:
                break
            except Exception as e:
                error_handler.log_error(e, {"operation": "replenish_tokens"})
                logger.error(f"Error in token replenishment task: {str(e)}")
    
    async def shutdown(self) -> None:
        """Shutdown the rate limiter."""
        if hasattr(self, 'replenishment_task') and self.replenishment_task:
            self.replenishment_task.cancel()
            try:
                await self.replenishment_task
            except asyncio.CancelledError:
                pass
        
        logger.info("Rate limiter shut down")


# Singleton instance
_rate_limiter_instance: Optional[RateLimiter] = None


def get_rate_limiter() -> RateLimiter:
    """
    Get the RateLimiter singleton instance.
    
    Returns:
        The RateLimiter instance
    """
    global _rate_limiter_instance
    
    if _rate_limiter_instance is None:
        _rate_limiter_instance = RateLimiter()
    
    return _rate_limiter_instance
