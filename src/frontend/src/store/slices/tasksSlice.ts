import { createSlice, PayloadAction } from '@reduxjs/toolkit';

export interface Task {
  id: string;
  name: string;
  description: string;
  status: 'created' | 'assigned' | 'in_progress' | 'completed' | 'failed';
  agentId: string | null;
  type: string;
  priority: 'high' | 'medium' | 'low';
  createdAt: string;
  updatedAt: string;
  completedAt: string | null;
  progress: number;
  result: any | null;
  error: string | null;
  requiredCapabilities: string[];
}

interface TasksState {
  tasks: Task[];
  selectedTaskId: string | null;
  isLoading: boolean;
  error: string | null;
  filters: {
    status: Task['status'] | 'all';
    agentId: string | 'all';
    priority: Task['priority'] | 'all';
  };
}

const initialState: TasksState = {
  tasks: [],
  selectedTaskId: null,
  isLoading: false,
  error: null,
  filters: {
    status: 'all',
    agentId: 'all',
    priority: 'all',
  },
};

const tasksSlice = createSlice({
  name: 'tasks',
  initialState,
  reducers: {
    fetchTasksStart: (state) => {
      state.isLoading = true;
      state.error = null;
    },
    fetchTasksSuccess: (state, action: PayloadAction<Task[]>) => {
      state.isLoading = false;
      state.tasks = action.payload;
    },
    fetchTasksFailure: (state, action: PayloadAction<string>) => {
      state.isLoading = false;
      state.error = action.payload;
    },
    selectTask: (state, action: PayloadAction<string>) => {
      state.selectedTaskId = action.payload;
    },
    updateTaskStatus: (state, action: PayloadAction<{ id: string; status: Task['status'] }>) => {
      const task = state.tasks.find(t => t.id === action.payload.id);
      if (task) {
        task.status = action.payload.status;
        task.updatedAt = new Date().toISOString();
        if (action.payload.status === 'completed') {
          task.completedAt = new Date().toISOString();
        }
      }
    },
    updateTaskProgress: (state, action: PayloadAction<{ id: string; progress: number }>) => {
      const task = state.tasks.find(t => t.id === action.payload.id);
      if (task) {
        task.progress = action.payload.progress;
        task.updatedAt = new Date().toISOString();
      }
    },
    updateTaskResult: (state, action: PayloadAction<{ id: string; result: any }>) => {
      const task = state.tasks.find(t => t.id === action.payload.id);
      if (task) {
        task.result = action.payload.result;
        task.updatedAt = new Date().toISOString();
      }
    },
    updateTaskError: (state, action: PayloadAction<{ id: string; error: string }>) => {
      const task = state.tasks.find(t => t.id === action.payload.id);
      if (task) {
        task.error = action.payload.error;
        task.updatedAt = new Date().toISOString();
      }
    },
    setTaskFilters: (state, action: PayloadAction<Partial<TasksState['filters']>>) => {
      state.filters = { ...state.filters, ...action.payload };
    },
    clearTaskError: (state) => {
      state.error = null;
    },
  },
});

export const {
  fetchTasksStart,
  fetchTasksSuccess,
  fetchTasksFailure,
  selectTask,
  updateTaskStatus,
  updateTaskProgress,
  updateTaskResult,
  updateTaskError,
  setTaskFilters,
  clearTaskError,
} = tasksSlice.actions;

export default tasksSlice.reducer;
