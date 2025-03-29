"""
Tests for the Rate Limiting Module

This module contains tests for the Rate Limiting Module in the AI-Orchestration-Platform.
"""

import asyncio
import pytest
import time
from typing import Dict, List, Any, Optional, Tuple

from src.orchestrator.rate_limiting import (
    RateLimiter,
    RateLimitType,
    RateLimitExceededError,
    get_rate_limiter
)
from src.orchestrator.communication import (
    MessageType,
    MessagePriority,
    AgentCommunicationManager,
    get_communication_manager
)


@pytest.fixture
def rate_limiter():
    """Fixture for creating a RateLimiter."""
    limiter = RateLimiter()
    yield limiter
    # Clean up
    asyncio.run(limiter.shutdown())


class TestRateLimiter:
    """Tests for the RateLimiter class."""
    
    @pytest.mark.asyncio
    async def test_check_rate_limit(self, rate_limiter):
        """Test checking rate limits."""
        # First request should be allowed
        is_allowed, retry_after = await rate_limiter.check_rate_limit(
            agent_id="test_agent",
            message_type="direct",
            priority="medium"
        )
        
        assert is_allowed is True
        assert retry_after is None
        
        # Configure a very low rate limit for testing
        rate_limiter.rate_limits[RateLimitType.AGENT]["test_agent"] = (1, 60)  # 1 message per minute
        
        # First request with the new limit should be allowed
        is_allowed, retry_after = await rate_limiter.check_rate_limit(
            agent_id="test_agent",
            message_type="direct",
            priority="medium"
        )
        
        assert is_allowed is True
        assert retry_after is None
        
        # Second request should be rate limited
        is_allowed, retry_after = await rate_limiter.check_rate_limit(
            agent_id="test_agent",
            message_type="direct",
            priority="medium"
        )
        
        assert is_allowed is False
        assert retry_after is not None
        assert retry_after > 0
    
    @pytest.mark.asyncio
    async def test_token_replenishment(self, rate_limiter):
        """Test token replenishment."""
        # Configure a rate limit for testing
        rate_limiter.rate_limits[RateLimitType.AGENT]["test_agent"] = (1, 1)  # 1 message per second
        
        # First request should be allowed
        is_allowed, _ = await rate_limiter.check_rate_limit(
            agent_id="test_agent",
            message_type="direct",
            priority="medium"
        )
        
        assert is_allowed is True
        
        # Second request should be rate limited
        is_allowed, _ = await rate_limiter.check_rate_limit(
            agent_id="test_agent",
            message_type="direct",
            priority="medium"
        )
        
        assert is_allowed is False
        
        # Wait for token replenishment
        await asyncio.sleep(1.1)
        
        # After waiting, the request should be allowed again
        is_allowed, _ = await rate_limiter.check_rate_limit(
            agent_id="test_agent",
            message_type="direct",
            priority="medium"
        )
        
        assert is_allowed is True
    
    @pytest.mark.asyncio
    async def test_different_rate_limits(self, rate_limiter):
        """Test different rate limit types."""
        # Configure rate limits for testing
        rate_limiter.rate_limits[RateLimitType.AGENT]["agent1"] = (1, 60)  # 1 message per minute
        rate_limiter.rate_limits[RateLimitType.MESSAGE_TYPE]["broadcast"] = (1, 60)  # 1 broadcast per minute
        rate_limiter.rate_limits[RateLimitType.PRIORITY]["high"] = (2, 60)  # 2 high priority messages per minute
        
        # Agent rate limit
        is_allowed, _ = await rate_limiter.check_rate_limit(
            agent_id="agent1",
            message_type="direct",
            priority="medium"
        )
        
        assert is_allowed is True
        
        is_allowed, _ = await rate_limiter.check_rate_limit(
            agent_id="agent1",
            message_type="direct",
            priority="medium"
        )
        
        assert is_allowed is False
        
        # Message type rate limit
        is_allowed, _ = await rate_limiter.check_rate_limit(
            agent_id="agent2",
            message_type="broadcast",
            priority="medium"
        )
        
        assert is_allowed is True
        
        is_allowed, _ = await rate_limiter.check_rate_limit(
            agent_id="agent2",
            message_type="broadcast",
            priority="medium"
        )
        
        assert is_allowed is False
        
        # Priority rate limit
        is_allowed, _ = await rate_limiter.check_rate_limit(
            agent_id="agent3",
            message_type="direct",
            priority="high"
        )
        
        assert is_allowed is True
        
        is_allowed, _ = await rate_limiter.check_rate_limit(
            agent_id="agent3",
            message_type="direct",
            priority="high"
        )
        
        assert is_allowed is True
        
        is_allowed, _ = await rate_limiter.check_rate_limit(
            agent_id="agent3",
            message_type="direct",
            priority="high"
        )
        
        assert is_allowed is False
    
    @pytest.mark.asyncio
    async def test_get_rate_limiter_singleton(self):
        """Test getting the RateLimiter singleton instance."""
        limiter1 = get_rate_limiter()
        limiter2 = get_rate_limiter()
        
        assert limiter1 is limiter2
        
        # Clean up
        await limiter1.shutdown()


@pytest.fixture
def communication_manager():
    """Fixture for creating an AgentCommunicationManager."""
    manager = AgentCommunicationManager()
    yield manager
    # Clean up
    asyncio.run(manager.shutdown())


class TestRateLimitingIntegration:
    """Tests for the integration of rate limiting with the communication module."""
    
    @pytest.mark.asyncio
    async def test_send_message_rate_limiting(self, communication_manager):
        """Test rate limiting when sending messages."""
        # Register agents
        await communication_manager.register_agent("sender")
        await communication_manager.register_agent("recipient")
        
        # Configure a very low rate limit for testing
        rate_limiter = get_rate_limiter()
        rate_limiter.rate_limits[RateLimitType.AGENT]["sender"] = (1, 60)  # 1 message per minute
        
        # First message should be allowed
        message_id = await communication_manager.send_message(
            sender_id="sender",
            message_type=MessageType.DIRECT,
            content={"text": "Hello, recipient!"},
            recipient_id="recipient",
            priority=MessagePriority.MEDIUM,
        )
        
        assert message_id is not None
        
        # Second message should be rate limited
        with pytest.raises(RateLimitExceededError) as excinfo:
            await communication_manager.send_message(
                sender_id="sender",
                message_type=MessageType.DIRECT,
                content={"text": "Hello again, recipient!"},
                recipient_id="recipient",
                priority=MessagePriority.MEDIUM,
            )
        
        # Check the error details
        assert "Rate limit exceeded" in str(excinfo.value)
        assert excinfo.value.retry_after > 0
        assert "sender_id" in excinfo.value.details
        assert excinfo.value.details["sender_id"] == "sender"
    
    @pytest.mark.asyncio
    async def test_different_agents_rate_limiting(self, communication_manager):
        """Test rate limiting for different agents."""
        # Register agents
        await communication_manager.register_agent("sender1")
        await communication_manager.register_agent("sender2")
        await communication_manager.register_agent("recipient")
        
        # Configure a very low rate limit for testing
        rate_limiter = get_rate_limiter()
        rate_limiter.rate_limits[RateLimitType.AGENT]["sender1"] = (1, 60)  # 1 message per minute
        
        # First message from sender1 should be allowed
        message_id1 = await communication_manager.send_message(
            sender_id="sender1",
            message_type=MessageType.DIRECT,
            content={"text": "Hello from sender1!"},
            recipient_id="recipient",
            priority=MessagePriority.MEDIUM,
        )
        
        assert message_id1 is not None
        
        # Second message from sender1 should be rate limited
        with pytest.raises(RateLimitExceededError):
            await communication_manager.send_message(
                sender_id="sender1",
                message_type=MessageType.DIRECT,
                content={"text": "Hello again from sender1!"},
                recipient_id="recipient",
                priority=MessagePriority.MEDIUM,
            )
        
        # Message from sender2 should be allowed
        message_id2 = await communication_manager.send_message(
            sender_id="sender2",
            message_type=MessageType.DIRECT,
            content={"text": "Hello from sender2!"},
            recipient_id="recipient",
            priority=MessagePriority.MEDIUM,
        )
        
        assert message_id2 is not None
    
    @pytest.mark.asyncio
    async def test_priority_based_rate_limiting(self, communication_manager):
        """Test rate limiting based on message priority."""
        # Register agents
        await communication_manager.register_agent("sender")
        await communication_manager.register_agent("recipient")
        
        # Configure rate limits for testing
        rate_limiter = get_rate_limiter()
        rate_limiter.rate_limits[RateLimitType.PRIORITY]["high"] = (2, 60)  # 2 high priority messages per minute
        rate_limiter.rate_limits[RateLimitType.PRIORITY]["medium"] = (1, 60)  # 1 medium priority message per minute
        
        # First high priority message should be allowed
        message_id1 = await communication_manager.send_message(
            sender_id="sender",
            message_type=MessageType.DIRECT,
            content={"text": "High priority message 1"},
            recipient_id="recipient",
            priority=MessagePriority.HIGH,
        )
        
        assert message_id1 is not None
        
        # Second high priority message should be allowed
        message_id2 = await communication_manager.send_message(
            sender_id="sender",
            message_type=MessageType.DIRECT,
            content={"text": "High priority message 2"},
            recipient_id="recipient",
            priority=MessagePriority.HIGH,
        )
        
        assert message_id2 is not None
        
        # Third high priority message should be rate limited
        with pytest.raises(RateLimitExceededError):
            await communication_manager.send_message(
                sender_id="sender",
                message_type=MessageType.DIRECT,
                content={"text": "High priority message 3"},
                recipient_id="recipient",
                priority=MessagePriority.HIGH,
            )
        
        # First medium priority message should be allowed
        message_id3 = await communication_manager.send_message(
            sender_id="sender",
            message_type=MessageType.DIRECT,
            content={"text": "Medium priority message 1"},
            recipient_id="recipient",
            priority=MessagePriority.MEDIUM,
        )
        
        assert message_id3 is not None
        
        # Second medium priority message should be rate limited
        with pytest.raises(RateLimitExceededError):
            await communication_manager.send_message(
                sender_id="sender",
                message_type=MessageType.DIRECT,
                content={"text": "Medium priority message 2"},
                recipient_id="recipient",
                priority=MessagePriority.MEDIUM,
            )
