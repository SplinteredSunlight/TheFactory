/**
 * Agent Configuration Types
 * 
 * This module defines TypeScript interfaces for agent configuration in the AI-Orchestration-Platform.
 * These interfaces mirror the backend Pydantic models to ensure type consistency.
 */

/**
 * Supported agent frameworks
 */
export enum AgentFramework {
  AI_ORCHESTRATOR = "ai-orchestrator",
  FAST_AGENT = "fast-agent"
}

/**
 * Possible agent statuses
 */
export enum AgentStatus {
  IDLE = "idle",
  BUSY = "busy",
  OFFLINE = "offline",
  ERROR = "error"
}

/**
 * Common agent capabilities
 */
export enum AgentCapability {
  TEXT_GENERATION = "text_generation",
  CODE_GENERATION = "code_generation",
  TEXT_PROCESSING = "text_processing",
  IMAGE_ANALYSIS = "image_analysis",
  DATA_EXTRACTION = "data_extraction",
  CONVERSATION = "conversation",
  REASONING = "reasoning",
  LONG_CONTEXT = "long_context",
  CUSTOM = "custom"
}

/**
 * Metrics for agent performance and usage
 */
export interface AgentMetrics {
  memoryUsage?: number;
  cpuUsage?: number;
  requestsProcessed?: number;
  averageResponseTime?: number;
  lastUpdated?: string;
}

/**
 * Base configuration for all agents
 */
export interface BaseAgentConfig {
  name: string;
  description?: string;
  capabilities: string[];
  priority: number;
  metadata: Record<string, any>;
}

/**
 * Configuration specific to AI-Orchestrator agents
 */
export interface AIOrchestrationConfig extends BaseAgentConfig {
  apiEndpoint?: string;
  apiKey?: string;
}

/**
 * Configuration specific to Fast-Agent agents
 */
export interface FastAgentConfig extends BaseAgentConfig {
  model: string;
  instruction: string;
  servers: string[];
  useAnthropic: boolean;
}

/**
 * Framework-specific configuration type
 */
export type FrameworkConfig = AIOrchestrationConfig | FastAgentConfig;

/**
 * Unified agent configuration schema
 */
export interface AgentConfig {
  agentId: string;
  framework: AgentFramework;
  externalId?: string;
  status: AgentStatus;
  createdAt: string;
  lastActive?: string;
  metrics?: AgentMetrics;
  config: FrameworkConfig;
}

/**
 * Agent representation for the UI
 */
export interface Agent {
  id: string;
  name: string;
  description: string;
  framework: AgentFramework;
  externalId?: string;
  status: AgentStatus;
  capabilities: string[];
  createdAt: string;
  lastActive?: string;
  metrics?: AgentMetrics;
  currentLoad: number;
  priority: number;
  metadata: Record<string, any>;
}

/**
 * Input for agent execution
 */
export interface AgentExecutionInput {
  query: string;
  parameters?: Record<string, any>;
}

/**
 * Output from agent execution
 */
export interface AgentExecutionOutput {
  agentId: string;
  status: string;
  outputs: Record<string, any>;
  timestamp: string;
  error?: string;
}

/**
 * Response for listing agents
 */
export interface AgentListResponse {
  agents: Agent[];
  count: number;
  page?: number;
  totalPages?: number;
}

/**
 * Convert an AgentConfig to an Agent for UI display
 */
export function configToAgent(config: AgentConfig): Agent {
  return {
    id: config.agentId,
    name: config.config.name,
    description: config.config.description || "",
    framework: config.framework,
    externalId: config.externalId,
    status: config.status,
    capabilities: config.config.capabilities,
    createdAt: config.createdAt,
    lastActive: config.lastActive,
    metrics: config.metrics,
    currentLoad: 0, // This would be populated from real-time data
    priority: config.config.priority,
    metadata: {
      ...config.config.metadata,
      framework: config.framework,
      // Add framework-specific fields to metadata
      ...(config.framework === AgentFramework.FAST_AGENT && {
        model: (config.config as FastAgentConfig).model,
        useAnthropic: (config.config as FastAgentConfig).useAnthropic,
        servers: (config.config as FastAgentConfig).servers,
      }),
      ...(config.framework === AgentFramework.AI_ORCHESTRATOR && {
        apiEndpoint: (config.config as AIOrchestrationConfig).apiEndpoint,
      })
    }
  };
}

/**
 * Convert an Agent to an AgentConfig for API requests
 */
export function agentToConfig(agent: Agent): AgentConfig {
  const isAIOrchestrator = agent.framework === AgentFramework.AI_ORCHESTRATOR;
  
  // Create the appropriate framework-specific config
  const frameworkConfig: FrameworkConfig = isAIOrchestrator
    ? {
        name: agent.name,
        description: agent.description,
        capabilities: agent.capabilities,
        priority: agent.priority,
        metadata: agent.metadata,
        apiEndpoint: agent.metadata.apiEndpoint,
        apiKey: agent.metadata.apiKey
      } as AIOrchestrationConfig
    : {
        name: agent.name,
        description: agent.description,
        capabilities: agent.capabilities,
        priority: agent.priority,
        metadata: agent.metadata,
        model: agent.metadata.model || "gpt-4",
        instruction: agent.metadata.instruction || `You are an AI agent named ${agent.name}`,
        servers: agent.metadata.servers || [],
        useAnthropic: agent.metadata.useAnthropic || false
      } as FastAgentConfig;
  
  return {
    agentId: agent.id,
    framework: agent.framework,
    externalId: agent.externalId,
    status: agent.status,
    createdAt: agent.createdAt,
    lastActive: agent.lastActive,
    metrics: agent.metrics,
    config: frameworkConfig
  };
}

/**
 * Create a new AI-Orchestrator agent configuration
 */
export function createAIOrchestrationAgent(
  name: string,
  description: string,
  apiEndpoint?: string,
  capabilities?: string[]
): AgentConfig {
  const config: AIOrchestrationConfig = {
    name,
    description,
    capabilities: capabilities || [
      AgentCapability.TEXT_PROCESSING,
      AgentCapability.IMAGE_ANALYSIS,
      AgentCapability.DATA_EXTRACTION
    ],
    priority: 1,
    metadata: {},
    apiEndpoint
  };
  
  return {
    agentId: `ai-orchestrator-${Date.now()}`,
    framework: AgentFramework.AI_ORCHESTRATOR,
    status: AgentStatus.IDLE,
    createdAt: new Date().toISOString(),
    config
  };
}

/**
 * Create a new Fast-Agent agent configuration
 */
export function createFastAgentAgent(
  name: string,
  description: string,
  instruction: string,
  model: string = "gpt-4",
  useAnthropic: boolean = false,
  servers: string[] = []
): AgentConfig {
  const capabilities = [
    AgentCapability.TEXT_GENERATION,
    AgentCapability.CODE_GENERATION,
    AgentCapability.CONVERSATION
  ];
  
  // Add additional capabilities based on model
  if (model.includes("gpt-4")) {
    capabilities.push(AgentCapability.REASONING);
  }
  
  // Add capabilities based on provider
  if (useAnthropic) {
    capabilities.push(AgentCapability.LONG_CONTEXT);
  }
  
  const config: FastAgentConfig = {
    name,
    description,
    capabilities,
    priority: 1,
    metadata: {},
    model,
    instruction,
    servers,
    useAnthropic
  };
  
  return {
    agentId: `fast-agent-${Date.now()}`,
    framework: AgentFramework.FAST_AGENT,
    status: AgentStatus.IDLE,
    createdAt: new Date().toISOString(),
    config
  };
}
