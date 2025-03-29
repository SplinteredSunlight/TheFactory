import { configureStore } from '@reduxjs/toolkit';
import { setupListeners } from '@reduxjs/toolkit/query';
import { api } from '../services/api';
import authReducer from './slices/authSlice';
import agentsReducer from './slices/agentsSlice';
import tasksReducer from './slices/tasksSlice';
import metricsReducer from './slices/metricsSlice';
import communicationReducer from './slices/communicationSlice';
import uiReducer from './slices/uiSlice';
import configurationReducer from './slices/configurationSlice';

export const store = configureStore({
  reducer: {
    [api.reducerPath]: api.reducer,
    auth: authReducer,
    agents: agentsReducer,
    tasks: tasksReducer,
    metrics: metricsReducer,
    communication: communicationReducer,
    ui: uiReducer,
    configuration: configurationReducer,
  },
  middleware: (getDefaultMiddleware) =>
    getDefaultMiddleware().concat(api.middleware),
});

setupListeners(store.dispatch);

export type RootState = ReturnType<typeof store.getState>;
export type AppDispatch = typeof store.dispatch;
