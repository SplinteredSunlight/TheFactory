import { createSlice, PayloadAction } from '@reduxjs/toolkit';
import { api } from '../../services/api';

// Define types for the configuration state
export interface SystemEndpoint {
  id: string;
  name: string;
  url: string;
  enabled: boolean;
  authType: 'none' | 'basic' | 'token' | 'oauth';
  credentials?: {
    username?: string;
    password?: string;
    token?: string;
    clientId?: string;
    clientSecret?: string;
  };
}

export interface SystemConnection {
  id: string;
  sourceSystemId: string;
  targetSystemId: string;
  connectionType: 'one-way' | 'two-way';
  enabled: boolean;
  syncInterval: number; // in minutes
  dataMapping: {
    id: string;
    sourceField: string;
    targetField: string;
    transformationType: 'none' | 'format' | 'custom';
    transformationConfig?: any;
  }[];
}

export interface SyncHistory {
  id: string;
  connectionId: string;
  timestamp: string;
  status: 'success' | 'partial' | 'failed';
  recordsProcessed: number;
  recordsSucceeded: number;
  recordsFailed: number;
  errorMessage?: string;
}

interface ConfigurationState {
  systems: SystemEndpoint[];
  connections: SystemConnection[];
  syncHistory: SyncHistory[];
  loading: boolean;
  error: string | null;
}

const initialState: ConfigurationState = {
  systems: [
    {
      id: 'orchestrator',
      name: 'AI-Orchestrator',
      url: 'http://localhost:8000',
      enabled: true,
      authType: 'token',
      credentials: {
        token: '',
      },
    },
    {
      id: 'fast-agent',
      name: 'Fast-Agent',
      url: 'http://localhost:8001',
      enabled: true,
      authType: 'token',
      credentials: {
        token: '',
      },
    },
  ],
  connections: [
    {
      id: 'orchestrator-fast-agent',
      sourceSystemId: 'orchestrator',
      targetSystemId: 'fast-agent',
      connectionType: 'two-way',
      enabled: true,
      syncInterval: 5,
      dataMapping: [
        {
          id: 'task-mapping',
          sourceField: 'task',
          targetField: 'task',
          transformationType: 'none',
        },
        {
          id: 'result-mapping',
          sourceField: 'result',
          targetField: 'result',
          transformationType: 'none',
        },
      ],
    },
  ],
  syncHistory: [],
  loading: false,
  error: null,
};

// Create the configuration slice
const configurationSlice = createSlice({
  name: 'configuration',
  initialState,
  reducers: {
    setLoading: (state: ConfigurationState, action: PayloadAction<boolean>) => {
      state.loading = action.payload;
    },
    setError: (state: ConfigurationState, action: PayloadAction<string | null>) => {
      state.error = action.payload;
    },
    addSystem: (state: ConfigurationState, action: PayloadAction<SystemEndpoint>) => {
      state.systems.push(action.payload);
    },
    updateSystem: (state: ConfigurationState, action: PayloadAction<SystemEndpoint>) => {
      const index = state.systems.findIndex((system: SystemEndpoint) => system.id === action.payload.id);
      if (index !== -1) {
        state.systems[index] = action.payload;
      }
    },
    removeSystem: (state: ConfigurationState, action: PayloadAction<string>) => {
      state.systems = state.systems.filter((system: SystemEndpoint) => system.id !== action.payload);
      // Also remove any connections that use this system
      state.connections = state.connections.filter(
        (connection: SystemConnection) => 
          connection.sourceSystemId !== action.payload && 
          connection.targetSystemId !== action.payload
      );
    },
    toggleSystemEnabled: (state: ConfigurationState, action: PayloadAction<string>) => {
      const system = state.systems.find((system: SystemEndpoint) => system.id === action.payload);
      if (system) {
        system.enabled = !system.enabled;
      }
    },
    addConnection: (state: ConfigurationState, action: PayloadAction<SystemConnection>) => {
      state.connections.push(action.payload);
    },
    updateConnection: (state: ConfigurationState, action: PayloadAction<SystemConnection>) => {
      const index = state.connections.findIndex((connection: SystemConnection) => connection.id === action.payload.id);
      if (index !== -1) {
        state.connections[index] = action.payload;
      }
    },
    removeConnection: (state: ConfigurationState, action: PayloadAction<string>) => {
      state.connections = state.connections.filter((connection: SystemConnection) => connection.id !== action.payload);
    },
    toggleConnectionEnabled: (state: ConfigurationState, action: PayloadAction<string>) => {
      const connection = state.connections.find((connection: SystemConnection) => connection.id === action.payload);
      if (connection) {
        connection.enabled = !connection.enabled;
      }
    },
    addSyncHistory: (state: ConfigurationState, action: PayloadAction<SyncHistory>) => {
      state.syncHistory.unshift(action.payload);
      // Keep only the last 100 sync history records
      if (state.syncHistory.length > 100) {
        state.syncHistory = state.syncHistory.slice(0, 100);
      }
    },
  },
  extraReducers: (builder) => {
    // Handle API endpoints when they are added
  },
});

// Export actions
export const {
  setLoading,
  setError,
  addSystem,
  updateSystem,
  removeSystem,
  toggleSystemEnabled,
  addConnection,
  updateConnection,
  removeConnection,
  toggleConnectionEnabled,
  addSyncHistory,
} = configurationSlice.actions;

// Export reducer
export default configurationSlice.reducer;

// Define API endpoints for configuration
const configurationApi = api.injectEndpoints({
  endpoints: (builder: any) => ({
    getSystems: builder.query<SystemEndpoint[], void>({
      query: () => '/configuration/systems',
    }),
    getSystem: builder.query<SystemEndpoint, string>({
      query: (id: string) => `/configuration/systems/${id}`,
    }),
    addSystem: builder.mutation<SystemEndpoint, Omit<SystemEndpoint, 'id'>>({
      query: (system: Omit<SystemEndpoint, 'id'>) => ({
        url: '/configuration/systems',
        method: 'POST',
        body: system,
      }),
    }),
    updateSystem: builder.mutation<SystemEndpoint, SystemEndpoint>({
      query: (system: SystemEndpoint) => ({
        url: `/configuration/systems/${system.id}`,
        method: 'PUT',
        body: system,
      }),
    }),
    deleteSystem: builder.mutation<void, string>({
      query: (id: string) => ({
        url: `/configuration/systems/${id}`,
        method: 'DELETE',
      }),
    }),
    getConnections: builder.query<SystemConnection[], void>({
      query: () => '/configuration/connections',
    }),
    getConnection: builder.query<SystemConnection, string>({
      query: (id: string) => `/configuration/connections/${id}`,
    }),
    addConnection: builder.mutation<SystemConnection, Omit<SystemConnection, 'id'>>({
      query: (connection: Omit<SystemConnection, 'id'>) => ({
        url: '/configuration/connections',
        method: 'POST',
        body: connection,
      }),
    }),
    updateConnection: builder.mutation<SystemConnection, SystemConnection>({
      query: (connection: SystemConnection) => ({
        url: `/configuration/connections/${connection.id}`,
        method: 'PUT',
        body: connection,
      }),
    }),
    deleteConnection: builder.mutation<void, string>({
      query: (id: string) => ({
        url: `/configuration/connections/${id}`,
        method: 'DELETE',
      }),
    }),
    getSyncHistory: builder.query<SyncHistory[], void>({
      query: () => '/configuration/sync-history',
    }),
    testConnection: builder.mutation<{ success: boolean; message: string }, string>({
      query: (id: string) => ({
        url: `/configuration/connections/${id}/test`,
        method: 'POST',
      }),
    }),
    syncNow: builder.mutation<SyncHistory, string>({
      query: (id: string) => ({
        url: `/configuration/connections/${id}/sync`,
        method: 'POST',
      }),
    }),
  }),
});

// Export API hooks
export const {
  useGetSystemsQuery,
  useGetSystemQuery,
  useAddSystemMutation,
  useUpdateSystemMutation,
  useDeleteSystemMutation,
  useGetConnectionsQuery,
  useGetConnectionQuery,
  useAddConnectionMutation,
  useUpdateConnectionMutation,
  useDeleteConnectionMutation,
  useGetSyncHistoryQuery,
  useTestConnectionMutation,
  useSyncNowMutation,
} = configurationApi;
