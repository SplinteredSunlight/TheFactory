# Agent Discovery and Capabilities Registry

This guide explains how to use the Agent Discovery Service and Agent Capabilities Registry in the AI-Orchestration-Platform.

## Overview

The Agent Discovery and Capabilities Registry provides a way to:

1. Register and discover agents in the system
2. Define and manage agent capabilities
3. Find agents based on their capabilities
4. Negotiate capabilities with agents
5. Validate data against capability schemas

These components are essential for building a dynamic, capability-based agent ecosystem where tasks can be routed to the most appropriate agents based on their capabilities.

## Architecture

The Agent Discovery and Capabilities Registry consists of two main components:

1. **Agent Discovery Service**: Manages agent registration, discovery, and status tracking
2. **Agent Capabilities Registry**: Manages capability definitions, schemas, and validation

```mermaid
graph TD
    subgraph "Agent Discovery and Capabilities Registry"
        ADS[AgentDiscoveryService] --> ACR[AgentCapabilitiesRegistry]
        ADS --> CM[CommunicationManager]
        ADS --> CB[CircuitBreaker]
    end
    
    subgraph "Agents"
        A1[Agent 1] --> ADS
        A2[Agent 2] --> ADS
        A3[Agent 3] --> ADS
    end
    
    subgraph "Task Management"
        TM[TaskManager] --> ADS
    end
    
    subgraph "API"
        API[API Endpoints] --> ADS
        API --> ACR
    end
```

## Agent Discovery Service

The Agent Discovery Service provides the following functionality:

- Register and unregister agents
- Update agent status
- Send and receive agent heartbeats
- Find agents by capability
- Negotiate capabilities with agents

### Registering an Agent

To register an agent with the discovery service:

```python
from src.orchestrator.agent_discovery import get_agent_discovery_service

# Get the agent discovery service
discovery_service = get_agent_discovery_service()

# Register an agent
result = await discovery_service.register_agent(
    agent_id="agent-1",
    name="Example Agent",
    capabilities=[
        {"name": "text_processing", "version": "1.0.0"},
        {"name": "image_generation", "version": "2.0.0"}
    ],
    status="idle",
    metadata={
        "provider": "OpenAI",
        "model": "gpt-4",
        "max_tokens": 8192
    }
)
```

### Finding Agents by Capability

To find agents with a specific capability:

```python
# Find agents with text processing capability
agents = await discovery_service.find_agents_by_capability(
    capability="text_processing",
    version="1.0.0",  # Optional
    status="idle",    # Optional
    active_only=True  # Only include active agents
)

# Find agents with multiple capabilities
agents = await discovery_service.find_agents_by_capabilities(
    capabilities=[
        {"name": "text_processing", "version": "1.0.0"},
        {"name": "image_generation", "version": "2.0.0"}
    ],
    match_all=True,  # Agents must have all capabilities
    status="idle"    # Optional
)
```

### Negotiating Capabilities

To negotiate capabilities with an agent:

```python
# Negotiate capabilities with an agent
result = await discovery_service.negotiate_capabilities(
    agent_id="agent-1",
    required_capabilities=[
        {"name": "text_processing", "version": "1.0.0"}
    ],
    optional_capabilities=[
        {"name": "image_generation", "version": "2.0.0"}
    ]
)

if result["success"]:
    # Agent has all required capabilities
    print(f"Agent has all required capabilities")
    print(f"Available optional capabilities: {result['available_optional_capabilities']}")
else:
    # Agent is missing some required capabilities
    print(f"Agent is missing required capabilities: {result['missing_capabilities']}")
```

### Agent Heartbeats

To send and receive agent heartbeats:

```python
# Send a heartbeat for an agent
result = await discovery_service.heartbeat(
    agent_id="agent-1",
    status="busy",  # Optional
    metadata={      # Optional
        "current_task": "task-123",
        "progress": 0.5
    }
)
```

## Agent Capabilities Registry

The Agent Capabilities Registry provides the following functionality:

- Register and unregister capabilities
- Define capability schemas
- Validate data against capability schemas
- List available capabilities

### Registering a Capability

To register a capability with the registry:

```python
from src.orchestrator.agent_discovery import get_agent_capabilities_registry

# Get the agent capabilities registry
capabilities_registry = get_agent_capabilities_registry()

# Register a simple capability
result = await capabilities_registry.register_capability(
    name="text_processing",
    description="Process and analyze text",
    versions=["1.0.0", "1.1.0", "2.0.0"],
    metadata={
        "category": "nlp",
        "languages": ["en", "fr", "es"]
    }
)

# Register a capability with a schema
result = await capabilities_registry.register_capability(
    name="image_generation",
    description="Generate images from text prompts",
    versions=["1.0.0"],
    schema={
        "type": "object",
        "properties": {
            "prompt": {"type": "string"},
            "width": {"type": "integer", "minimum": 64, "maximum": 1024},
            "height": {"type": "integer", "minimum": 64, "maximum": 1024},
            "style": {"type": "string", "enum": ["realistic", "cartoon", "abstract"]}
        },
        "required": ["prompt"]
    },
    metadata={
        "category": "image",
        "models": ["stable-diffusion", "dall-e"]
    }
)
```

### Validating Data Against a Capability Schema

To validate data against a capability schema:

```python
# Validate data against a capability schema
is_valid, error = await capabilities_registry.validate_capability(
    name="image_generation",
    version="1.0.0",
    data={
        "prompt": "A beautiful sunset over the ocean",
        "width": 512,
        "height": 512,
        "style": "realistic"
    }
)

if is_valid:
    print("Data is valid")
else:
    print(f"Data is invalid: {error}")
```

## Best Practices

### Agent Registration

- Use meaningful agent IDs that are unique and descriptive
- Include all relevant capabilities when registering an agent
- Provide detailed metadata to help with agent selection
- Update agent status regularly to reflect its current state

### Capability Registration

- Use semantic versioning for capability versions
- Provide detailed schemas for capabilities to enable validation
- Include metadata to help with capability discovery
- Use consistent naming conventions for capabilities

### Agent Discovery

- Use specific capability requirements when finding agents
- Consider agent status and activity when selecting agents
- Use capability negotiation to ensure agents have the required capabilities
- Implement fallback mechanisms for when no suitable agents are found

### Heartbeats and Status Updates

- Send regular heartbeats to indicate agent activity
- Update agent status when starting or completing tasks
- Include relevant metadata in heartbeats to provide context
- Handle agent failures gracefully by detecting missed heartbeats

## Example

See the [Agent Discovery Example](../../examples/agent_discovery_example.py) for a complete example of how to use the Agent Discovery and Capabilities Registry.

## API Reference

### Agent Discovery Service

#### `get_agent_discovery_service(heartbeat_interval=30, inactive_timeout=60)`

Get the singleton instance of the AgentDiscoveryService.

- `heartbeat_interval`: Interval in seconds for agent heartbeats
- `inactive_timeout`: Number of seconds after which an agent is considered inactive

#### `register_agent(agent_id, name, capabilities, status="idle", metadata=None, use_circuit_breaker=True)`

Register a new agent or update an existing one.

- `agent_id`: Unique identifier for the agent
- `name`: Name of the agent
- `capabilities`: List of agent capabilities
- `status`: Status of the agent
- `metadata`: Additional metadata for the agent
- `use_circuit_breaker`: Whether to use circuit breaker protection

#### `unregister_agent(agent_id, use_circuit_breaker=True)`

Unregister an agent.

- `agent_id`: Unique identifier for the agent
- `use_circuit_breaker`: Whether to use circuit breaker protection

#### `update_agent_status(agent_id, status, use_circuit_breaker=True)`

Update the status of an agent.

- `agent_id`: Unique identifier for the agent
- `status`: New status for the agent
- `use_circuit_breaker`: Whether to use circuit breaker protection

#### `heartbeat(agent_id, status=None, metadata=None)`

Send a heartbeat for an agent.

- `agent_id`: Unique identifier for the agent
- `status`: Optional new status for the agent
- `metadata`: Optional metadata to update

#### `get_agent(agent_id)`

Get information about an agent.

- `agent_id`: Unique identifier for the agent

#### `list_agents(status=None, active_only=False, capability=None, capability_version=None)`

List all agents, optionally filtered by status, activity, or capability.

- `status`: Filter agents by status
- `active_only`: Only include active agents
- `capability`: Filter agents by capability
- `capability_version`: Filter agents by capability version

#### `find_agents_by_capability(capability, version=None, status=None, active_only=True, limit=None)`

Find agents that have a specific capability.

- `capability`: Capability to search for
- `version`: Optional version of the capability
- `status`: Optional status filter
- `active_only`: Only include active agents
- `limit`: Maximum number of agents to return

#### `find_agents_by_capabilities(capabilities, match_all=True, status=None, active_only=True, limit=None)`

Find agents that have specific capabilities.

- `capabilities`: List of capabilities to search for, each with name and optional version
- `match_all`: Whether agents must have all capabilities or just one
- `status`: Optional status filter
- `active_only`: Only include active agents
- `limit`: Maximum number of agents to return

#### `negotiate_capabilities(agent_id, required_capabilities, optional_capabilities=None)`

Negotiate capabilities with an agent.

- `agent_id`: Unique identifier for the agent
- `required_capabilities`: List of required capabilities
- `optional_capabilities`: List of optional capabilities

### Agent Capabilities Registry

#### `get_agent_capabilities_registry()`

Get the singleton instance of the AgentCapabilitiesRegistry.

#### `register_capability(name, description, versions, schema=None, metadata=None)`

Register a new capability or update an existing one.

- `name`: Name of the capability
- `description`: Description of the capability
- `versions`: List of supported versions
- `schema`: Optional JSON schema for the capability
- `metadata`: Additional metadata for the capability

#### `unregister_capability(name)`

Unregister a capability.

- `name`: Name of the capability

#### `get_capability(name)`

Get information about a capability.

- `name`: Name of the capability

#### `list_capabilities(version=None)`

List all capabilities, optionally filtered by version.

- `version`: Filter capabilities by version

#### `validate_capability(name, version, data)`

Validate data against a capability schema.

- `name`: Name of the capability
- `version`: Version of the capability
- `data`: Data to validate
