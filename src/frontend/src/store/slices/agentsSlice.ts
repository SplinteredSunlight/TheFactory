import { createSlice, PayloadAction } from '@reduxjs/toolkit';
import { 
  Agent, 
  AgentStatus, 
  AgentFramework, 
  AgentMetrics, 
  AgentListResponse,
  AgentConfig,
  configToAgent
} from '../../types/agent';
import { api } from '../../services/api';

// Note: The Agent interface is now imported from types/agent.ts

export interface AgentsState {
  agents: Agent[];
  selectedAgentId: string | null;
  isLoading: boolean;
  error: string | null;
  totalCount: number;
  currentPage: number;
  totalPages: number;
}

const initialState: AgentsState = {
  agents: [],
  selectedAgentId: null,
  isLoading: false,
  error: null,
  totalCount: 0,
  currentPage: 1,
  totalPages: 1
};

const agentsSlice = createSlice({
  name: 'agents',
  initialState,
  reducers: {
    fetchAgentsStart: (state) => {
      state.isLoading = true;
      state.error = null;
    },
    fetchAgentsSuccess: (state, action: PayloadAction<AgentListResponse>) => {
      state.isLoading = false;
      state.agents = action.payload.agents;
      state.totalCount = action.payload.count;
      state.currentPage = action.payload.page || 1;
      state.totalPages = action.payload.totalPages || 1;
    },
    fetchAgentsFailure: (state, action: PayloadAction<string>) => {
      state.isLoading = false;
      state.error = action.payload;
    },
    selectAgent: (state, action: PayloadAction<string>) => {
      state.selectedAgentId = action.payload;
    },
    updateAgentStatus: (state, action: PayloadAction<{ id: string; status: AgentStatus }>) => {
      const agent = state.agents.find(a => a.id === action.payload.id);
      if (agent) {
        agent.status = action.payload.status;
      }
    },
    updateAgentMetrics: (state, action: PayloadAction<{ id: string; metrics: Partial<AgentMetrics> }>) => {
      const agent = state.agents.find(a => a.id === action.payload.id);
      if (agent) {
        agent.metrics = { ...agent.metrics, ...action.payload.metrics };
        agent.lastActive = new Date().toISOString();
      }
    },
    updateAgentLoad: (state, action: PayloadAction<{ id: string; load: number }>) => {
      const agent = state.agents.find(a => a.id === action.payload.id);
      if (agent) {
        agent.currentLoad = action.payload.load;
        agent.lastActive = new Date().toISOString();
      }
    },
    clearAgentError: (state) => {
      state.error = null;
    },
    addAgent: (state, action: PayloadAction<Agent>) => {
      state.agents.push(action.payload);
      state.totalCount += 1;
    },
    updateAgent: (state, action: PayloadAction<Agent>) => {
      const index = state.agents.findIndex(a => a.id === action.payload.id);
      if (index !== -1) {
        state.agents[index] = action.payload;
      }
    },
    removeAgent: (state, action: PayloadAction<string>) => {
      state.agents = state.agents.filter(a => a.id !== action.payload);
      state.totalCount -= 1;
      if (state.selectedAgentId === action.payload) {
        state.selectedAgentId = null;
      }
    },
  },
});

export const {
  fetchAgentsStart,
  fetchAgentsSuccess,
  fetchAgentsFailure,
  selectAgent,
  updateAgentStatus,
  updateAgentMetrics,
  updateAgentLoad,
  clearAgentError,
  addAgent,
  updateAgent,
  removeAgent,
} = agentsSlice.actions;

export default agentsSlice.reducer;

// Define API endpoints for agents
const agentsApi = api.injectEndpoints({
  endpoints: (builder) => ({
    getAgents: builder.query<AgentListResponse, { page?: number; limit?: number; framework?: AgentFramework }>({
      query: (params) => ({
        url: '/agents',
        params,
      }),
      transformResponse: (response: { agents: AgentConfig[] } & Omit<AgentListResponse, 'agents'>) => ({
        ...response,
        agents: response.agents.map(configToAgent),
      }),
    }),
    getAgent: builder.query<Agent, string>({
      query: (id) => `/agents/${id}`,
      transformResponse: (response: AgentConfig) => configToAgent(response),
    }),
    createAgent: builder.mutation<Agent, AgentConfig>({
      query: (agent) => ({
        url: '/agents',
        method: 'POST',
        body: agent,
      }),
      transformResponse: (response: AgentConfig) => configToAgent(response),
    }),
    updateAgent: builder.mutation<Agent, AgentConfig>({
      query: (agent) => ({
        url: `/agents/${agent.agentId}`,
        method: 'PUT',
        body: agent,
      }),
      transformResponse: (response: AgentConfig) => configToAgent(response),
    }),
    deleteAgent: builder.mutation<void, string>({
      query: (id) => ({
        url: `/agents/${id}`,
        method: 'DELETE',
      }),
    }),
    executeAgent: builder.mutation<any, { agentId: string; query: string; parameters?: Record<string, any> }>({
      query: ({ agentId, ...body }) => ({
        url: `/agents/${agentId}/execute`,
        method: 'POST',
        body,
      }),
    }),
  }),
});

export const {
  useGetAgentsQuery,
  useGetAgentQuery,
  useCreateAgentMutation,
  useUpdateAgentMutation,
  useDeleteAgentMutation,
  useExecuteAgentMutation,
} = agentsApi;
