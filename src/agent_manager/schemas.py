"""
Agent Configuration Schema Module

This module defines the unified schema for agent configuration in the AI-Orchestration-Platform.
It provides a common structure for representing agents from different frameworks.
"""

from enum import Enum
from typing import Dict, List, Optional, Union, Any
from datetime import datetime
from pydantic import BaseModel, Field, validator, root_validator


class AgentFramework(str, Enum):
    """Supported agent frameworks."""
    AI_ORCHESTRATOR = "ai-orchestrator"
    FAST_AGENT = "fast-agent"
    DAGGER = "dagger"


class AgentStatus(str, Enum):
    """Possible agent statuses."""
    IDLE = "idle"
    BUSY = "busy"
    OFFLINE = "offline"
    ERROR = "error"


class AgentCapability(str, Enum):
    """Common agent capabilities."""
    TEXT_GENERATION = "text_generation"
    CODE_GENERATION = "code_generation"
    TEXT_PROCESSING = "text_processing"
    IMAGE_ANALYSIS = "image_analysis"
    DATA_EXTRACTION = "data_extraction"
    CONVERSATION = "conversation"
    REASONING = "reasoning"
    LONG_CONTEXT = "long_context"
    CONTAINERIZED_WORKFLOW = "containerized_workflow"
    DAGGER_PIPELINE = "dagger_pipeline"
    CUSTOM = "custom"


class AgentMetrics(BaseModel):
    """Metrics for agent performance and usage."""
    memory_usage: Optional[float] = Field(None, description="Memory usage in MB")
    cpu_usage: Optional[float] = Field(None, description="CPU usage percentage")
    requests_processed: Optional[int] = Field(None, description="Number of requests processed")
    average_response_time: Optional[float] = Field(None, description="Average response time in seconds")
    last_updated: Optional[datetime] = Field(None, description="When metrics were last updated")


class BaseAgentConfig(BaseModel):
    """Base configuration for all agents."""
    name: str = Field(..., description="Human-readable name for the agent")
    description: Optional[str] = Field(None, description="Optional description of the agent")
    capabilities: List[str] = Field(default_factory=list, description="List of agent capabilities")
    priority: int = Field(default=1, description="Agent priority (higher is better)")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional metadata")


class AIOrchestrationConfig(BaseAgentConfig):
    """Configuration specific to AI-Orchestrator agents."""
    api_endpoint: Optional[str] = Field(None, description="API endpoint for the AI-Orchestrator service")
    api_key: Optional[str] = Field(None, description="API key for authentication")


class FastAgentConfig(BaseAgentConfig):
    """Configuration specific to Fast-Agent agents."""
    model: str = Field(default="gpt-4", description="Model to use")
    instruction: str = Field(..., description="Instructions for the agent")
    servers: List[str] = Field(default_factory=list, description="List of MCP servers to use")
    use_anthropic: bool = Field(default=False, description="Whether to use Anthropic instead of OpenAI")


class DaggerContainerConfig(BaseModel):
    """Configuration for a Dagger container."""
    image: str = Field(..., description="Container image to use")
    environment: Dict[str, str] = Field(default_factory=dict, description="Environment variables for the container")
    volumes: List[Dict[str, str]] = Field(default_factory=list, description="Volumes to mount in the container")
    command: Optional[List[str]] = Field(None, description="Command to run in the container")
    working_dir: Optional[str] = Field(None, description="Working directory for the container")
    registry_credentials: Optional[Dict[str, str]] = Field(None, description="Credentials for the container registry")


class DaggerConfig(BaseAgentConfig):
    """Configuration specific to Dagger agents."""
    container_registry: Optional[str] = Field(None, description="Optional registry URL for container images")
    container_credentials: Optional[Dict[str, str]] = Field(None, description="Optional credentials for container registry")
    workflow_directory: Optional[str] = Field(None, description="Directory containing workflow definitions")
    workflow_defaults: Dict[str, Any] = Field(default_factory=dict, description="Default parameters for workflows")
    max_concurrent_executions: int = Field(default=5, description="Maximum number of concurrent workflow executions")
    timeout_seconds: int = Field(default=600, description="Default timeout for workflow executions in seconds")


class AgentConfig(BaseModel):
    """Unified agent configuration schema."""
    agent_id: str = Field(..., description="Unique identifier for the agent")
    framework: AgentFramework = Field(..., description="Agent framework")
    external_id: Optional[str] = Field(None, description="ID of the agent in the external framework")
    status: AgentStatus = Field(default=AgentStatus.IDLE, description="Current agent status")
    created_at: datetime = Field(default_factory=datetime.now, description="When the agent was created")
    last_active: Optional[datetime] = Field(None, description="When the agent was last active")
    metrics: Optional[AgentMetrics] = Field(None, description="Agent performance metrics")
    
    # Framework-specific configuration
    config: Union[AIOrchestrationConfig, FastAgentConfig, DaggerConfig] = Field(
        ..., description="Framework-specific configuration"
    )
    
    @validator('config')
    def validate_config_type(cls, v, values):
        """Validate that the config type matches the framework."""
        framework = values.get('framework')
        if framework == AgentFramework.AI_ORCHESTRATOR and not isinstance(v, AIOrchestrationConfig):
            raise ValueError("AI-Orchestrator agents must use AIOrchestrationConfig")
        if framework == AgentFramework.FAST_AGENT and not isinstance(v, FastAgentConfig):
            raise ValueError("Fast-Agent agents must use FastAgentConfig")
        if framework == AgentFramework.DAGGER and not isinstance(v, DaggerConfig):
            raise ValueError("Dagger agents must use DaggerConfig")
        return v
    
    @root_validator(skip_on_failure=True)
    def set_default_capabilities(cls, values):
        """Set default capabilities based on the framework."""
        framework = values.get('framework')
        config = values.get('config')
        
        if config and not config.capabilities:
            if framework == AgentFramework.AI_ORCHESTRATOR:
                config.capabilities = [
                    AgentCapability.TEXT_PROCESSING.value,
                    AgentCapability.IMAGE_ANALYSIS.value,
                    AgentCapability.DATA_EXTRACTION.value
                ]
            elif framework == AgentFramework.FAST_AGENT:
                config.capabilities = [
                    AgentCapability.TEXT_GENERATION.value,
                    AgentCapability.CODE_GENERATION.value,
                    AgentCapability.CONVERSATION.value
                ]
                
                # Add additional capabilities based on model
                if config.model and "gpt-4" in config.model:
                    config.capabilities.append(AgentCapability.REASONING.value)
                
                # Add capabilities based on provider
                if config.use_anthropic:
                    config.capabilities.append(AgentCapability.LONG_CONTEXT.value)
            elif framework == AgentFramework.DAGGER:
                config.capabilities = [
                    AgentCapability.CONTAINERIZED_WORKFLOW.value,
                    AgentCapability.DAGGER_PIPELINE.value
                ]
        
        return values
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert the agent configuration to a dictionary representation."""
        return {
            "id": self.agent_id,
            "name": self.config.name,
            "description": self.config.description,
            "framework": self.framework.value,
            "external_id": self.external_id,
            "status": self.status.value,
            "capabilities": self.config.capabilities,
            "created_at": self.created_at.isoformat(),
            "last_active": self.last_active.isoformat() if self.last_active else None,
            "metrics": self.metrics.dict() if self.metrics else None,
            "metadata": {
                "framework": self.framework.value,
                "priority": self.config.priority,
                **self.config.metadata,
                **({"model": self.config.model} if hasattr(self.config, "model") else {}),
                **({"use_anthropic": self.config.use_anthropic} if hasattr(self.config, "use_anthropic") else {}),
                **({"servers": self.config.servers} if hasattr(self.config, "servers") else {}),
                **({"api_endpoint": self.config.api_endpoint} if hasattr(self.config, "api_endpoint") else {})
            }
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'AgentConfig':
        """Create an agent configuration from a dictionary representation."""
        framework = data.get("framework") or data.get("metadata", {}).get("framework")
        if not framework:
            raise ValueError("Framework not specified in data")
        
        # Convert to enum
        framework_enum = AgentFramework(framework)
        
        # Create the appropriate config
        if framework_enum == AgentFramework.AI_ORCHESTRATOR:
            config = AIOrchestrationConfig(
                name=data.get("name", ""),
                description=data.get("description"),
                capabilities=data.get("capabilities", []),
                priority=data.get("metadata", {}).get("priority", 1),
                metadata=data.get("metadata", {}),
                api_endpoint=data.get("metadata", {}).get("api_endpoint"),
                api_key=None  # Don't include API key in from_dict for security
            )
        elif framework_enum == AgentFramework.DAGGER:
            config = DaggerConfig(
                name=data.get("name", ""),
                description=data.get("description"),
                capabilities=data.get("capabilities", []),
                priority=data.get("metadata", {}).get("priority", 1),
                metadata=data.get("metadata", {}),
                container_registry=data.get("metadata", {}).get("container_registry"),
                container_credentials=None,  # Don't include credentials in from_dict for security
                workflow_directory=data.get("metadata", {}).get("workflow_directory"),
                workflow_defaults=data.get("metadata", {}).get("workflow_defaults", {}),
                max_concurrent_executions=data.get("metadata", {}).get("max_concurrent_executions", 5),
                timeout_seconds=data.get("metadata", {}).get("timeout_seconds", 600)
            )
        else:  # Fast-Agent
            config = FastAgentConfig(
                name=data.get("name", ""),
                description=data.get("description"),
                capabilities=data.get("capabilities", []),
                priority=data.get("metadata", {}).get("priority", 1),
                metadata=data.get("metadata", {}),
                model=data.get("metadata", {}).get("model", "gpt-4"),
                instruction=data.get("metadata", {}).get("instruction", f"You are an AI agent named {data.get('name', 'Agent')}"),
                servers=data.get("metadata", {}).get("servers", []),
                use_anthropic=data.get("metadata", {}).get("use_anthropic", False)
            )
        
        # Parse datetime fields
        created_at = data.get("created_at")
        if created_at and isinstance(created_at, str):
            created_at = datetime.fromisoformat(created_at)
        else:
            created_at = datetime.now()
            
        last_active = data.get("last_active")
        if last_active and isinstance(last_active, str):
            last_active = datetime.fromisoformat(last_active)
        else:
            last_active = None
        
        # Create metrics if present
        metrics = None
        if data.get("metrics"):
            metrics = AgentMetrics(**data["metrics"])
        
        # Create the agent config
        return cls(
            agent_id=data.get("id"),
            framework=framework_enum,
            external_id=data.get("external_id"),
            status=AgentStatus(data.get("status", "idle")),
            created_at=created_at,
            last_active=last_active,
            metrics=metrics,
            config=config
        )


class AgentExecutionInput(BaseModel):
    """Input for agent execution."""
    query: str = Field(..., description="Query to send to the agent")
    parameters: Dict[str, Any] = Field(default_factory=dict, description="Additional parameters")


class AgentExecutionOutput(BaseModel):
    """Output from agent execution."""
    agent_id: str = Field(..., description="ID of the agent that executed the query")
    status: str = Field(..., description="Status of the execution")
    outputs: Dict[str, Any] = Field(..., description="Execution outputs")
    timestamp: datetime = Field(default_factory=datetime.now, description="When the execution completed")
    error: Optional[str] = Field(None, description="Error message if execution failed")


class AgentListResponse(BaseModel):
    """Response for listing agents."""
    agents: List[Dict[str, Any]] = Field(..., description="List of agent dictionaries")
    count: int = Field(..., description="Total number of agents")
    page: Optional[int] = Field(None, description="Current page number")
    total_pages: Optional[int] = Field(None, description="Total number of pages")
