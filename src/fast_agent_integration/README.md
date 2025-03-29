# Fast-Agent Integration Module

This module provides integration between the AI-Orchestration-Platform and Fast-Agent framework. It allows the AI-Orchestrator to create, manage, and execute Fast-Agent agents through a standardized adapter interface.

## Overview

The Fast-Agent Integration Module consists of several components:

1. **Core Adapter**: The low-level adapter that communicates directly with the Fast-Agent framework.
2. **Adapter Implementation**: Implementation of the AgentAdapter interface for Fast-Agent.
3. **Factory**: A factory for creating Fast-Agent agents through the AgentManager.
4. **MCP Server**: An MCP server that exposes Fast-Agent functionality to other components.

## Installation

The Fast-Agent Integration Module is included in the AI-Orchestration-Platform. No additional installation is required.

## Configuration

The module can be configured through the following environment variables:

- `ORCHESTRATOR_API_KEY`: API key for authenticating with the orchestrator.

You can also configure the module through the `fast_agent.yaml` configuration file in the `config` directory.

## Usage

### Basic Usage

```python
import asyncio
from agent_manager.manager import AgentManager
from fast_agent_integration.factory import register_fast_agent_factory

async def main():
    # Create an AgentManager
    agent_manager = AgentManager()
    
    # Register the Fast-Agent factory
    factory = await register_fast_agent_factory(
        agent_manager=agent_manager,
        app_name="example-app",
    )
    
    try:
        # Create a Fast-Agent agent
        agent = agent_manager.create_agent(
            agent_type="fast_agent",
            name="Example Agent",
            description="An example agent",
            instruction="You are a helpful AI assistant.",
            model="gpt-4",
        )
        
        # Execute the agent
        result = agent.execute(
            query="What are the key features of the AI-Orchestration-Platform?",
        )
        
        print(f"Agent response: {result['outputs']['response']}")
        
    finally:
        # Clean up resources
        await factory.shutdown()

# Run the example
asyncio.run(main())
```

### Advanced Usage

For more advanced usage examples, see the `examples.py` file in this directory.

## API Reference

### FastAgentAdapter

The `FastAgentAdapter` class provides the core functionality for interacting with the Fast-Agent framework.

```python
from fast_agent_integration.adapter import FastAgentAdapter, get_adapter

# Get the adapter singleton instance
adapter = await get_adapter(
    config_path="path/to/config.yaml",
    app_name="my-app",
    api_key="my-api-key",
)

# Create an agent
agent_id = await adapter.create_agent(
    name="My Agent",
    instruction="You are a helpful AI assistant.",
    model="gpt-4",
    use_anthropic=False,
)

# Run the agent
response = await adapter.run_agent(
    agent_id=agent_id,
    query="Hello, world!",
)

# Delete the agent
await adapter.delete_agent(agent_id)

# Shutdown the adapter
await adapter.shutdown()
```

### FastAgentAdapterImpl

The `FastAgentAdapterImpl` class implements the `AgentAdapter` interface for Fast-Agent.

```python
from fast_agent_integration.fast_agent_adapter import FastAgentAdapterImpl

# Create the adapter
adapter = FastAgentAdapterImpl(
    config_path="path/to/config.yaml",
    app_name="my-app",
    api_key="my-api-key",
)

# Initialize the adapter
await adapter.initialize()

# Create an agent
external_id = await adapter.create_agent(
    agent_id="my-agent-id",
    name="My Agent",
    description="My agent description",
    instruction="You are a helpful AI assistant.",
    model="gpt-4",
    use_anthropic=False,
)

# Get agent information
agent_info = await adapter.get_agent(external_id)

# List all agents
agents = await adapter.list_agents()

# Execute the agent
result = await adapter.execute_agent(
    agent_id=external_id,
    query="Hello, world!",
)

# Delete the agent
success = await adapter.delete_agent(external_id)

# Shutdown the adapter
await adapter.shutdown()
```

### FastAgentFactory

The `FastAgentFactory` class provides a factory for creating Fast-Agent agents through the AgentManager.

```python
from agent_manager.manager import AgentManager
from fast_agent_integration.factory import FastAgentFactory

# Create an AgentManager
agent_manager = AgentManager()

# Create the factory
factory = FastAgentFactory(
    agent_manager=agent_manager,
    config_path="path/to/config.yaml",
    app_name="my-app",
    api_key="my-api-key",
)

# Initialize the factory
await factory.initialize()

# Create an agent through the AgentManager
agent = agent_manager.create_agent(
    agent_type="fast_agent",
    name="My Agent",
    description="My agent description",
    instruction="You are a helpful AI assistant.",
    model="gpt-4",
    use_anthropic=False,
)

# Shutdown the factory
await factory.shutdown()
```

## Authentication

The Fast-Agent Integration Module uses the authentication mechanism provided by the AI-Orchestration-Platform. It supports:

- API key authentication for initial connection
- JWT tokens for session-based authentication
- Token refresh for long-running sessions
- Agent-specific authentication tokens

## Error Handling

The module provides comprehensive error handling for various scenarios:

- Authentication errors
- Authorization errors
- Agent creation errors
- Agent execution errors
- Network errors

## Testing

The module includes unit tests for all components. To run the tests:

```bash
python -m unittest discover -s tests
```

## Contributing

Contributions to the Fast-Agent Integration Module are welcome. Please follow the standard contribution guidelines for the AI-Orchestration-Platform.

## License

This module is part of the AI-Orchestration-Platform and is licensed under the same terms.
