"""
Agent Configuration Examples

This module provides examples of how to use the unified agent configuration schema
to create and manage agents from both AI-Orchestrator and Fast-Agent frameworks.
"""

import asyncio
import json
from datetime import datetime
from typing import Dict, Any, List

from agent_manager.schemas import (
    AgentConfig,
    AgentFramework,
    AgentStatus,
    AgentCapability,
    AgentMetrics,
    AIOrchestrationConfig,
    FastAgentConfig
)

# Example 1: Creating an AI-Orchestrator agent configuration
def create_ai_orchestrator_agent() -> AgentConfig:
    """Create an example AI-Orchestrator agent configuration."""
    
    # Create the framework-specific configuration
    ai_orchestrator_config = AIOrchestrationConfig(
        name="Data Analyzer",
        description="An agent that specializes in data analysis and visualization",
        capabilities=[
            AgentCapability.TEXT_PROCESSING.value,
            AgentCapability.DATA_EXTRACTION.value,
            AgentCapability.IMAGE_ANALYSIS.value
        ],
        priority=2,
        metadata={
            "specialization": "data_analysis",
            "supported_formats": ["csv", "json", "xlsx"],
            "max_file_size_mb": 10
        },
        api_endpoint="http://localhost:8000/api/v1"
    )
    
    # Create the unified agent configuration
    agent_config = AgentConfig(
        agent_id="ai-orchestrator-data-analyzer-001",
        framework=AgentFramework.AI_ORCHESTRATOR,
        external_id=None,  # Will be set after registration
        status=AgentStatus.IDLE,
        created_at=datetime.now(),
        config=ai_orchestrator_config
    )
    
    return agent_config

# Example 2: Creating a Fast-Agent agent configuration
def create_fast_agent_agent() -> AgentConfig:
    """Create an example Fast-Agent agent configuration."""
    
    # Create the framework-specific configuration
    fast_agent_config = FastAgentConfig(
        name="Code Assistant",
        description="An agent that helps with code generation and review",
        capabilities=[
            AgentCapability.TEXT_GENERATION.value,
            AgentCapability.CODE_GENERATION.value,
            AgentCapability.REASONING.value
        ],
        priority=3,
        metadata={
            "specialization": "code_assistance",
            "supported_languages": ["python", "javascript", "typescript", "java"],
            "context_window": 16000
        },
        model="gpt-4",
        instruction="You are a helpful coding assistant that specializes in generating and reviewing code. Focus on best practices, readability, and performance.",
        servers=["fetch", "filesystem", "github"],
        use_anthropic=False
    )
    
    # Create the unified agent configuration
    agent_config = AgentConfig(
        agent_id="fast-agent-code-assistant-001",
        framework=AgentFramework.FAST_AGENT,
        external_id=None,  # Will be set after registration
        status=AgentStatus.IDLE,
        created_at=datetime.now(),
        config=fast_agent_config
    )
    
    return agent_config

# Example 3: Converting between dictionary and AgentConfig
def convert_between_dict_and_config() -> None:
    """Demonstrate conversion between dictionary and AgentConfig."""
    
    # Create an agent configuration
    agent_config = create_fast_agent_agent()
    
    # Convert to dictionary
    agent_dict = agent_config.to_dict()
    print("Agent as dictionary:")
    print(json.dumps(agent_dict, indent=2))
    
    # Convert back to AgentConfig
    reconstructed_config = AgentConfig.from_dict(agent_dict)
    print("\nReconstructed agent config:")
    print(f"ID: {reconstructed_config.agent_id}")
    print(f"Framework: {reconstructed_config.framework}")
    print(f"Name: {reconstructed_config.config.name}")
    print(f"Capabilities: {reconstructed_config.config.capabilities}")
    
    # Verify they are equivalent
    assert agent_config.agent_id == reconstructed_config.agent_id
    assert agent_config.framework == reconstructed_config.framework
    assert agent_config.config.name == reconstructed_config.config.name
    assert set(agent_config.config.capabilities) == set(reconstructed_config.config.capabilities)
    print("\nVerification successful: Original and reconstructed configs are equivalent")

# Example 4: Using the schema with the agent manager
async def use_with_agent_manager() -> None:
    """Demonstrate how to use the schema with the agent manager."""
    
    # Import the agent manager
    from agent_manager.adapter import AgentAdapter
    from agent_manager.manager import AgentManager
    
    # Create an agent manager
    agent_manager = AgentManager()
    
    # Create an AI-Orchestrator agent configuration
    ai_orchestrator_config = create_ai_orchestrator_agent()
    
    # Create a Fast-Agent agent configuration
    fast_agent_config = create_fast_agent_agent()
    
    # In a real application, you would register these agents with their respective adapters
    # For demonstration purposes, we'll just print the configurations
    print("AI-Orchestrator Agent Configuration:")
    print(f"ID: {ai_orchestrator_config.agent_id}")
    print(f"Framework: {ai_orchestrator_config.framework}")
    print(f"Name: {ai_orchestrator_config.config.name}")
    print(f"Description: {ai_orchestrator_config.config.description}")
    print(f"Capabilities: {ai_orchestrator_config.config.capabilities}")
    print(f"API Endpoint: {ai_orchestrator_config.config.api_endpoint}")
    
    print("\nFast-Agent Agent Configuration:")
    print(f"ID: {fast_agent_config.agent_id}")
    print(f"Framework: {fast_agent_config.framework}")
    print(f"Name: {fast_agent_config.config.name}")
    print(f"Description: {fast_agent_config.config.description}")
    print(f"Capabilities: {fast_agent_config.config.capabilities}")
    print(f"Model: {fast_agent_config.config.model}")
    print(f"Instruction: {fast_agent_config.config.instruction}")
    print(f"Servers: {fast_agent_config.config.servers}")
    print(f"Use Anthropic: {fast_agent_config.config.use_anthropic}")

# Example 5: Updating agent metrics
def update_agent_metrics() -> AgentConfig:
    """Demonstrate how to update agent metrics."""
    
    # Create an agent configuration
    agent_config = create_fast_agent_agent()
    
    # Create metrics
    metrics = AgentMetrics(
        memory_usage=256.5,
        cpu_usage=12.3,
        requests_processed=42,
        average_response_time=0.85,
        last_updated=datetime.now()
    )
    
    # Update the agent configuration with metrics
    agent_config.metrics = metrics
    agent_config.status = AgentStatus.BUSY
    agent_config.last_active = datetime.now()
    
    return agent_config

# Run the examples
if __name__ == "__main__":
    # Example 1 & 2 are used by other examples
    
    # Example 3: Convert between dictionary and AgentConfig
    print("Example 3: Convert between dictionary and AgentConfig")
    print("=" * 80)
    convert_between_dict_and_config()
    print("\n")
    
    # Example 4: Use with agent manager
    print("Example 4: Use with agent manager")
    print("=" * 80)
    asyncio.run(use_with_agent_manager())
    print("\n")
    
    # Example 5: Update agent metrics
    print("Example 5: Update agent metrics")
    print("=" * 80)
    updated_agent = update_agent_metrics()
    print(f"Agent ID: {updated_agent.agent_id}")
    print(f"Status: {updated_agent.status}")
    print(f"Last Active: {updated_agent.last_active}")
    print(f"Memory Usage: {updated_agent.metrics.memory_usage} MB")
    print(f"CPU Usage: {updated_agent.metrics.cpu_usage}%")
    print(f"Requests Processed: {updated_agent.metrics.requests_processed}")
    print(f"Average Response Time: {updated_agent.metrics.average_response_time} seconds")
    print(f"Metrics Last Updated: {updated_agent.metrics.last_updated}")
