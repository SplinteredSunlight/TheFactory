import { createSlice, PayloadAction } from '@reduxjs/toolkit';

interface UiState {
  sidebarOpen: boolean;
  darkMode: boolean;
  notifications: {
    id: string;
    type: 'success' | 'error' | 'info' | 'warning';
    message: string;
    timestamp: string;
    read: boolean;
  }[];
  activeTab: 'dashboard' | 'agents' | 'tasks' | 'communication' | 'settings';
  activeProjectId: string | null;
  dashboardLayout: {
    id: string;
    type: string;
    position: {
      x: number;
      y: number;
      w: number;
      h: number;
    };
    visible: boolean;
  }[];
}

const initialState: UiState = {
  sidebarOpen: true,
  darkMode: window.matchMedia && window.matchMedia('(prefers-color-scheme: dark)').matches,
  notifications: [],
  activeTab: 'dashboard',
  activeProjectId: 'project_6d186b44', // Migrated project ID
  dashboardLayout: [
    {
      id: 'system-overview',
      type: 'system-overview',
      position: { x: 0, y: 0, w: 12, h: 4 },
      visible: true,
    },
    {
      id: 'agent-status',
      type: 'agent-status',
      position: { x: 0, y: 4, w: 6, h: 8 },
      visible: true,
    },
    {
      id: 'task-status',
      type: 'task-status',
      position: { x: 6, y: 4, w: 6, h: 8 },
      visible: true,
    },
    {
      id: 'performance-metrics',
      type: 'performance-metrics',
      position: { x: 0, y: 12, w: 12, h: 8 },
      visible: true,
    },
    {
      id: 'recent-messages',
      type: 'recent-messages',
      position: { x: 0, y: 20, w: 12, h: 6 },
      visible: true,
    },
    {
      id: 'project-progress-tracker',
      type: 'project-progress-tracker',
      position: { x: 0, y: 26, w: 12, h: 12 },
      visible: true,
    },
    {
      id: 'dagger-workflow-integration',
      type: 'dagger-workflow-integration',
      position: { x: 0, y: 38, w: 12, h: 12 },
      visible: true,
    },
    {
      id: 'cross-system-config',
      type: 'cross-system-config',
      position: { x: 0, y: 50, w: 12, h: 10 },
      visible: true,
    },
  ],
};

const uiSlice = createSlice({
  name: 'ui',
  initialState,
  reducers: {
    toggleSidebar: (state) => {
      state.sidebarOpen = !state.sidebarOpen;
    },
    setSidebarOpen: (state, action: PayloadAction<boolean>) => {
      state.sidebarOpen = action.payload;
    },
    toggleDarkMode: (state) => {
      state.darkMode = !state.darkMode;
    },
    setDarkMode: (state, action: PayloadAction<boolean>) => {
      state.darkMode = action.payload;
    },
    addNotification: (state, action: PayloadAction<Omit<UiState['notifications'][0], 'timestamp' | 'read'>>) => {
      state.notifications.unshift({
        ...action.payload,
        timestamp: new Date().toISOString(),
        read: false,
      });
      
      // Keep only the last 50 notifications
      if (state.notifications.length > 50) {
        state.notifications.pop();
      }
    },
    markNotificationAsRead: (state, action: PayloadAction<string>) => {
      const notification = state.notifications.find(n => n.id === action.payload);
      if (notification) {
        notification.read = true;
      }
    },
    markAllNotificationsAsRead: (state) => {
      state.notifications.forEach(notification => {
        notification.read = true;
      });
    },
    clearNotifications: (state) => {
      state.notifications = [];
    },
    setActiveTab: (state, action: PayloadAction<UiState['activeTab']>) => {
      state.activeTab = action.payload;
    },
    setActiveProject: (state, action: PayloadAction<string | null>) => {
      state.activeProjectId = action.payload;
    },
    updateDashboardLayout: (state, action: PayloadAction<UiState['dashboardLayout']>) => {
      state.dashboardLayout = action.payload;
    },
    updateDashboardWidgetPosition: (state, action: PayloadAction<{ id: string; position: Partial<UiState['dashboardLayout'][0]['position']> }>) => {
      const widget = state.dashboardLayout.find(w => w.id === action.payload.id);
      if (widget) {
        widget.position = { ...widget.position, ...action.payload.position };
      }
    },
    toggleDashboardWidgetVisibility: (state, action: PayloadAction<string>) => {
      const widget = state.dashboardLayout.find(w => w.id === action.payload);
      if (widget) {
        widget.visible = !widget.visible;
      }
    },
  },
});

export const {
  toggleSidebar,
  setSidebarOpen,
  toggleDarkMode,
  setDarkMode,
  addNotification,
  markNotificationAsRead,
  markAllNotificationsAsRead,
  clearNotifications,
  setActiveTab,
  setActiveProject,
  updateDashboardLayout,
  updateDashboardWidgetPosition,
  toggleDashboardWidgetVisibility,
} = uiSlice.actions;

export default uiSlice.reducer;
