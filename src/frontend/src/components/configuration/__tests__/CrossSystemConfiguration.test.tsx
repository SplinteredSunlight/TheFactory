import React from 'react';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { Provider } from 'react-redux';
import configureStore from 'redux-mock-store';
import { rest } from 'msw';
import { setupServer } from 'msw/node';
import CrossSystemConfiguration from '../CrossSystemConfiguration';

// Mock Redux store
const mockStore = configureStore([]);

// Mock API responses
const server = setupServer(
  // Get systems
  rest.get('/api/configuration/systems', (req, res, ctx) => {
    return res(
      ctx.json([
        {
          id: 'system-1',
          name: 'AI-Orchestrator',
          url: 'http://localhost:8000',
          enabled: true,
          authType: 'token',
        },
        {
          id: 'system-2',
          name: 'Fast-Agent',
          url: 'http://localhost:8001',
          enabled: true,
          authType: 'token',
        },
      ])
    );
  }),
  
  // Get connections
  rest.get('/api/configuration/connections', (req, res, ctx) => {
    return res(
      ctx.json([
        {
          id: 'connection-1',
          sourceSystemId: 'system-1',
          targetSystemId: 'system-2',
          connectionType: 'two-way',
          enabled: true,
          syncInterval: 5,
          dataMapping: [],
        },
      ])
    );
  }),
  
  // Add system
  rest.post('/api/configuration/systems', (req, res, ctx) => {
    return res(
      ctx.json({
        id: 'new-system',
        ...req.body,
      })
    );
  }),
  
  // Add connection
  rest.post('/api/configuration/connections', (req, res, ctx) => {
    return res(
      ctx.json({
        id: 'new-connection',
        ...req.body,
      })
    );
  }),
  
  // Test connection
  rest.post('/api/configuration/connections/:id/test', (req, res, ctx) => {
    return res(
      ctx.json({
        success: true,
        message: 'Connection test successful',
      })
    );
  }),
  
  // Sync now
  rest.post('/api/configuration/connections/:id/sync', (req, res, ctx) => {
    return res(
      ctx.json({
        id: 'sync-1',
        connectionId: req.params.id,
        timestamp: new Date().toISOString(),
        status: 'success',
        recordsProcessed: 42,
        recordsSucceeded: 42,
        recordsFailed: 0,
      })
    );
  })
);

// Initial store state
const initialState = {
  configuration: {
    systems: [
      {
        id: 'system-1',
        name: 'AI-Orchestrator',
        url: 'http://localhost:8000',
        enabled: true,
        authType: 'token',
      },
      {
        id: 'system-2',
        name: 'Fast-Agent',
        url: 'http://localhost:8001',
        enabled: true,
        authType: 'token',
      },
    ],
    connections: [
      {
        id: 'connection-1',
        sourceSystemId: 'system-1',
        targetSystemId: 'system-2',
        connectionType: 'two-way',
        enabled: true,
        syncInterval: 5,
        dataMapping: [],
      },
    ],
    syncHistory: [],
    loading: false,
    error: null,
  },
};

describe('CrossSystemConfiguration', () => {
  let store: any;
  
  beforeAll(() => server.listen());
  afterEach(() => server.resetHandlers());
  afterAll(() => server.close());
  
  beforeEach(() => {
    store = mockStore(initialState);
  });
  
  it('renders the component with tabs', () => {
    render(
      <Provider store={store}>
        <CrossSystemConfiguration />
      </Provider>
    );
    
    // Check that tabs are rendered
    expect(screen.getByText('Dashboard')).toBeInTheDocument();
    expect(screen.getByText('Systems')).toBeInTheDocument();
    expect(screen.getByText('Connections')).toBeInTheDocument();
    expect(screen.getByText('Sync History')).toBeInTheDocument();
  });
  
  it('displays systems in the Systems tab', async () => {
    render(
      <Provider store={store}>
        <CrossSystemConfiguration />
      </Provider>
    );
    
    // Click on Systems tab
    fireEvent.click(screen.getByText('Systems'));
    
    // Check that systems are displayed
    expect(screen.getByText('System Endpoints')).toBeInTheDocument();
    expect(screen.getByText('AI-Orchestrator')).toBeInTheDocument();
    expect(screen.getByText('Fast-Agent')).toBeInTheDocument();
  });
  
  it('displays connections in the Connections tab', async () => {
    render(
      <Provider store={store}>
        <CrossSystemConfiguration />
      </Provider>
    );
    
    // Click on Connections tab
    fireEvent.click(screen.getByText('Connections'));
    
    // Check that connections are displayed
    expect(screen.getByText('System Connections')).toBeInTheDocument();
    // In a real test, we would check for specific connection details
  });
  
  it('opens the Add System dialog when Add System button is clicked', async () => {
    render(
      <Provider store={store}>
        <CrossSystemConfiguration />
      </Provider>
    );
    
    // Click on Systems tab
    fireEvent.click(screen.getByText('Systems'));
    
    // Click on Add System button
    fireEvent.click(screen.getByText('Add System'));
    
    // Check that dialog is displayed
    expect(screen.getByText('Add System')).toBeInTheDocument();
    expect(screen.getByText('System Name')).toBeInTheDocument();
    expect(screen.getByText('URL')).toBeInTheDocument();
    expect(screen.getByText('Authentication Type')).toBeInTheDocument();
  });
  
  it('opens the Add Connection dialog when Add Connection button is clicked', async () => {
    render(
      <Provider store={store}>
        <CrossSystemConfiguration />
      </Provider>
    );
    
    // Click on Connections tab
    fireEvent.click(screen.getByText('Connections'));
    
    // Click on Add Connection button
    fireEvent.click(screen.getByText('Add Connection'));
    
    // Check that dialog is displayed
    expect(screen.getByText('Add Connection')).toBeInTheDocument();
    expect(screen.getByText('Source System')).toBeInTheDocument();
    expect(screen.getByText('Target System')).toBeInTheDocument();
    expect(screen.getByText('Connection Type')).toBeInTheDocument();
    expect(screen.getByText('Sync Interval (minutes)')).toBeInTheDocument();
  });
  
  // Additional tests would include:
  // - Testing form submission for adding systems and connections
  // - Testing toggling system and connection enabled/disabled
  // - Testing the test connection functionality
  // - Testing the sync now functionality
  // - Testing error handling
});
