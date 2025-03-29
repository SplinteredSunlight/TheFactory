# Unified Agent Configuration Schema

This module provides a unified configuration schema for representing agents from different frameworks (AI-Orchestrator and Fast-Agent) in the AI-Orchestration-Platform.

## Overview

The unified agent configuration schema allows you to:

1. Define a common structure for agent metadata
2. Support framework-specific configuration options
3. Include validation logic
4. Use the schema in both backend and frontend components

## Backend Schema (Pydantic Models)

The backend schema is defined using Pydantic models in `schemas.py`. The main components are:

### Core Models

- `AgentConfig`: The main configuration model that represents an agent from any framework
- `AIOrchestrationConfig`: Configuration specific to AI-Orchestrator agents
- `FastAgentConfig`: Configuration specific to Fast-Agent agents
- `AgentMetrics`: Metrics for agent performance and usage

### Enums

- `AgentFramework`: Supported agent frameworks (AI-Orchestrator, Fast-Agent)
- `AgentStatus`: Possible agent statuses (IDLE, BUSY, OFFLINE, ERROR)
- `AgentCapability`: Common agent capabilities (TEXT_GENERATION, CODE_GENERATION, etc.)

### Example Usage (Backend)

```python
from agent_manager.schemas import (
    AgentConfig,
    AgentFramework,
    AgentStatus,
    AgentCapability,
    FastAgentConfig
)

# Create a Fast-Agent configuration
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
        "supported_languages": ["python", "javascript", "typescript", "java"]
    },
    model="gpt-4",
    instruction="You are a helpful coding assistant...",
    servers=["fetch", "filesystem", "github"],
    use_anthropic=False
)

# Create the unified agent configuration
agent_config = AgentConfig(
    agent_id="fast-agent-code-assistant-001",
    framework=AgentFramework.FAST_AGENT,
    status=AgentStatus.IDLE,
    created_at=datetime.now(),
    config=fast_agent_config
)

# Convert to dictionary for API responses
agent_dict = agent_config.to_dict()

# Convert from dictionary (e.g., from API requests)
reconstructed_config = AgentConfig.from_dict(agent_dict)
```

For more detailed examples, see `src/examples/agent_config_examples.py`.

## Frontend Schema (TypeScript Interfaces)

The frontend schema is defined using TypeScript interfaces in `src/frontend/src/types/agent.ts`. The main components are:

### Core Interfaces

- `AgentConfig`: The main configuration interface that represents an agent from any framework
- `AIOrchestrationConfig`: Configuration specific to AI-Orchestrator agents
- `FastAgentConfig`: Configuration specific to Fast-Agent agents
- `Agent`: A simplified representation of an agent for UI display
- `AgentMetrics`: Metrics for agent performance and usage

### Enums

- `AgentFramework`: Supported agent frameworks (AI_ORCHESTRATOR, FAST_AGENT)
- `AgentStatus`: Possible agent statuses (IDLE, BUSY, OFFLINE, ERROR)
- `AgentCapability`: Common agent capabilities (TEXT_GENERATION, CODE_GENERATION, etc.)

### Helper Functions

- `configToAgent`: Convert an AgentConfig to an Agent for UI display
- `agentToConfig`: Convert an Agent to an AgentConfig for API requests
- `createAIOrchestrationAgent`: Create a new AI-Orchestrator agent configuration
- `createFastAgentAgent`: Create a new Fast-Agent agent configuration

### Example Usage (Frontend)

```typescript
import { 
  AgentConfig, 
  AgentFramework, 
  AgentStatus, 
  AgentCapability,
  createFastAgentAgent,
  configToAgent
} from '../types/agent';

// Create a Fast-Agent configuration
const config = createFastAgentAgent(
  "Code Assistant",
  "An agent that helps with code generation and review",
  "You are a helpful coding assistant...",
  "gpt-4",
  false,
  ["fetch", "filesystem", "github"]
);

// Add additional metadata
config.config.metadata = {
  specialization: "code_assistance",
  supported_languages: ["python", "javascript", "typescript", "java"]
};

// Convert to Agent for UI display
const agent = configToAgent(config);

// Update agent status and metrics
config.status = AgentStatus.BUSY;
config.lastActive = new Date().toISOString();
config.metrics = {
  memoryUsage: 256.5,
  cpuUsage: 12.3,
  requestsProcessed: 42,
  averageResponseTime: 0.85,
  lastUpdated: new Date().toISOString()
};
```

For more detailed examples, see `src/frontend/src/examples/AgentConfigExamples.tsx`.

## Integration with Existing Code

### Backend Integration

The unified agent configuration schema can be integrated with the existing backend code by:

1. Using the `AgentConfig` model in API endpoints
2. Converting between `AgentConfig` and framework-specific models in adapters
3. Validating agent configurations using Pydantic's validation

### Frontend Integration

The unified agent configuration schema can be integrated with the existing frontend code by:

1. Using the `Agent` interface in UI components
2. Converting between `Agent` and `AgentConfig` when communicating with the API
3. Using the helper functions to create and manipulate agent configurations

## Benefits

- **Consistency**: Ensures consistent representation of agents across the platform
- **Type Safety**: Provides type checking and validation for agent configurations
- **Flexibility**: Supports framework-specific configuration options
- **Interoperability**: Allows seamless communication between backend and frontend

## Future Improvements

- Add more validation rules for specific agent types
- Support for additional agent frameworks
- Enhanced metrics and monitoring capabilities
- Support for agent versioning and history
