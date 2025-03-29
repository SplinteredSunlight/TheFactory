import { createSlice, PayloadAction } from '@reduxjs/toolkit';

export interface SystemMetrics {
  cpuUsage: number;
  memoryUsage: number;
  activeAgents: number;
  totalAgents: number;
  activeTasks: number;
  completedTasks: number;
  failedTasks: number;
  averageTaskCompletionTime: number;
  successRate: number;
}

export interface TimeSeriesData {
  timestamp: string;
  value: number;
}

export interface MetricsState {
  system: SystemMetrics;
  timeSeriesData: {
    cpuUsage: TimeSeriesData[];
    memoryUsage: TimeSeriesData[];
    activeAgents: TimeSeriesData[];
    activeTasks: TimeSeriesData[];
    taskCompletionRate: TimeSeriesData[];
  };
  isLoading: boolean;
  error: string | null;
  timeRange: '1h' | '24h' | '7d' | '30d';
}

const initialState: MetricsState = {
  system: {
    cpuUsage: 0,
    memoryUsage: 0,
    activeAgents: 0,
    totalAgents: 0,
    activeTasks: 0,
    completedTasks: 0,
    failedTasks: 0,
    averageTaskCompletionTime: 0,
    successRate: 0,
  },
  timeSeriesData: {
    cpuUsage: [],
    memoryUsage: [],
    activeAgents: [],
    activeTasks: [],
    taskCompletionRate: [],
  },
  isLoading: false,
  error: null,
  timeRange: '24h',
};

const metricsSlice = createSlice({
  name: 'metrics',
  initialState,
  reducers: {
    fetchMetricsStart: (state) => {
      state.isLoading = true;
      state.error = null;
    },
    fetchMetricsSuccess: (state, action: PayloadAction<{ system: SystemMetrics; timeSeriesData: MetricsState['timeSeriesData'] }>) => {
      state.isLoading = false;
      state.system = action.payload.system;
      state.timeSeriesData = action.payload.timeSeriesData;
    },
    fetchMetricsFailure: (state, action: PayloadAction<string>) => {
      state.isLoading = false;
      state.error = action.payload;
    },
    updateSystemMetrics: (state, action: PayloadAction<Partial<SystemMetrics>>) => {
      state.system = { ...state.system, ...action.payload };
    },
    addTimeSeriesDataPoint: (state, action: PayloadAction<{ metric: keyof MetricsState['timeSeriesData']; dataPoint: TimeSeriesData }>) => {
      const { metric, dataPoint } = action.payload;
      state.timeSeriesData[metric].push(dataPoint);
      
      // Keep only the last 100 data points to prevent excessive memory usage
      if (state.timeSeriesData[metric].length > 100) {
        state.timeSeriesData[metric].shift();
      }
    },
    setTimeRange: (state, action: PayloadAction<MetricsState['timeRange']>) => {
      state.timeRange = action.payload;
    },
    clearMetricsError: (state) => {
      state.error = null;
    },
  },
});

export const {
  fetchMetricsStart,
  fetchMetricsSuccess,
  fetchMetricsFailure,
  updateSystemMetrics,
  addTimeSeriesDataPoint,
  setTimeRange,
  clearMetricsError,
} = metricsSlice.actions;

export default metricsSlice.reducer;
