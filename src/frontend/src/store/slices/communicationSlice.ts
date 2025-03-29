import { createSlice, PayloadAction } from '@reduxjs/toolkit';

export interface Message {
  id: string;
  senderId: string;
  recipientId: string | null;
  messageType: 'direct' | 'broadcast' | 'task_request' | 'task_response' | 'status_update' | 'error' | 'system';
  content: any;
  priority: 'high' | 'medium' | 'low';
  timestamp: string;
  correlationId: string | null;
  isRead: boolean;
}

interface CommunicationState {
  messages: Message[];
  selectedMessageId: string | null;
  isLoading: boolean;
  error: string | null;
  filters: {
    messageType: Message['messageType'] | 'all';
    senderId: string | 'all';
    recipientId: string | 'all';
    priority: Message['priority'] | 'all';
  };
}

const initialState: CommunicationState = {
  messages: [],
  selectedMessageId: null,
  isLoading: false,
  error: null,
  filters: {
    messageType: 'all',
    senderId: 'all',
    recipientId: 'all',
    priority: 'all',
  },
};

const communicationSlice = createSlice({
  name: 'communication',
  initialState,
  reducers: {
    fetchMessagesStart: (state) => {
      state.isLoading = true;
      state.error = null;
    },
    fetchMessagesSuccess: (state, action: PayloadAction<Message[]>) => {
      state.isLoading = false;
      state.messages = action.payload;
    },
    fetchMessagesFailure: (state, action: PayloadAction<string>) => {
      state.isLoading = false;
      state.error = action.payload;
    },
    selectMessage: (state, action: PayloadAction<string>) => {
      state.selectedMessageId = action.payload;
      
      // Mark the message as read
      const message = state.messages.find(m => m.id === action.payload);
      if (message) {
        message.isRead = true;
      }
    },
    addMessage: (state, action: PayloadAction<Message>) => {
      state.messages.unshift(action.payload);
    },
    markMessageAsRead: (state, action: PayloadAction<string>) => {
      const message = state.messages.find(m => m.id === action.payload);
      if (message) {
        message.isRead = true;
      }
    },
    markAllMessagesAsRead: (state) => {
      state.messages.forEach(message => {
        message.isRead = true;
      });
    },
    setMessageFilters: (state, action: PayloadAction<Partial<CommunicationState['filters']>>) => {
      state.filters = { ...state.filters, ...action.payload };
    },
    clearCommunicationError: (state) => {
      state.error = null;
    },
  },
});

export const {
  fetchMessagesStart,
  fetchMessagesSuccess,
  fetchMessagesFailure,
  selectMessage,
  addMessage,
  markMessageAsRead,
  markAllMessagesAsRead,
  setMessageFilters,
  clearCommunicationError,
} = communicationSlice.actions;

export default communicationSlice.reducer;
