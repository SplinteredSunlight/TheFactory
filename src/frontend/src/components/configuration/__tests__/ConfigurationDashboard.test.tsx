import React from 'react';
import { render, screen, fireEvent } from '@testing-library/react';
import { ThemeProvider, createTheme } from '@mui/material';
import ConfigurationDashboard from '../ConfigurationDashboard';

// Mock chart.js to avoid errors in tests
jest.mock('chart.js');
jest.mock('react-chartjs-2', () => ({
  Line: () => <div data-testid="line-chart" />,
  Doughnut: () => <div data-testid="doughnut-chart" />,
}));

describe('ConfigurationDashboard', () => {
  // Mock props
  const mockSystems = [
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
    {
      id: 'system-3',
      name: 'External API',
      url: 'https://api.example.com',
      enabled: false,
      authType: 'basic',
    },
  ];

  const mockConnections = [
    {
      id: 'connection-1',
      sourceSystemId: 'system-1',
      targetSystemId: 'system-2',
      connectionType: 'two-way',
      enabled: true,
      syncInterval: 5,
      dataMapping: [],
    },
    {
      id: 'connection-2',
      sourceSystemId: 'system-1',
      targetSystemId: 'system-3',
      connectionType: 'one-way',
      enabled: false,
      syncInterval: 10,
      dataMapping: [],
    },
  ];

  const mockProps = {
    systems: mockSystems,
    connections: mockConnections,
    isLoadingSystems: false,
    isLoadingConnections: false,
    onAddSystem: jest.fn(),
    onAddConnection: jest.fn(),
    onTestConnection: jest.fn(),
    onSyncNow: jest.fn(),
    onEditSystem: jest.fn(),
    onEditConnection: jest.fn(),
  };

  const theme = createTheme();

  it('renders the dashboard with system overview', () => {
    render(
      <ThemeProvider theme={theme}>
        <ConfigurationDashboard {...mockProps} />
      </ThemeProvider>
    );

    // Check that the dashboard title is rendered
    expect(screen.getByText('Cross-System Configuration Dashboard')).toBeInTheDocument();
    
    // Check that system overview is rendered
    expect(screen.getByText('System Overview')).toBeInTheDocument();
    
    // Check that system counts are displayed
    expect(screen.getByText('3')).toBeInTheDocument(); // Total Systems
    expect(screen.getByText('2')).toBeInTheDocument(); // Enabled Systems
    
    // Check that the dashboard tabs are rendered
    expect(screen.getByText('Overview')).toBeInTheDocument();
    expect(screen.getByText('Health Status')).toBeInTheDocument();
    expect(screen.getByText('Data Flow')).toBeInTheDocument();
    expect(screen.getByText('Performance')).toBeInTheDocument();
  });

  it('renders system distribution chart', () => {
    render(
      <ThemeProvider theme={theme}>
        <ConfigurationDashboard {...mockProps} />
      </ThemeProvider>
    );

    // Check that system distribution section is rendered
    expect(screen.getByText('System Distribution')).toBeInTheDocument();
    
    // Check that the chart is rendered
    expect(screen.getByTestId('doughnut-chart')).toBeInTheDocument();
  });

  it('renders sync history chart', () => {
    render(
      <ThemeProvider theme={theme}>
        <ConfigurationDashboard {...mockProps} />
      </ThemeProvider>
    );

    // Check that sync history section is rendered
    expect(screen.getByText('Sync History')).toBeInTheDocument();
    
    // Check that the chart is rendered
    expect(screen.getByTestId('line-chart')).toBeInTheDocument();
  });

  it('renders active systems section', () => {
    render(
      <ThemeProvider theme={theme}>
        <ConfigurationDashboard {...mockProps} />
      </ThemeProvider>
    );

    // Check that active systems section is rendered
    expect(screen.getByText('Active Systems')).toBeInTheDocument();
    
    // Check that enabled systems are displayed
    expect(screen.getAllByText('AI-Orchestrator')).toBeTruthy();
    expect(screen.getAllByText('Fast-Agent')).toBeTruthy();
    
    // Check that disabled systems are not displayed in active systems
    const activeSystemsSection = screen.getByText('Active Systems').closest('div');
    expect(activeSystemsSection).not.toContainElement(screen.queryByText('External API'));
  });

  it('renders active connections section', () => {
    render(
      <ThemeProvider theme={theme}>
        <ConfigurationDashboard {...mockProps} />
      </ThemeProvider>
    );

    // Check that active connections section is rendered
    expect(screen.getByText('Active Connections')).toBeInTheDocument();
    
    // Check that enabled connections are displayed
    expect(screen.getByText('Sync: 5 min')).toBeInTheDocument();
    
    // Check that disabled connections are not displayed
    expect(screen.queryByText('Sync: 10 min')).not.toBeInTheDocument();
  });

  it('calls onAddSystem when Add System button is clicked', () => {
    render(
      <ThemeProvider theme={theme}>
        <ConfigurationDashboard {...mockProps} />
      </ThemeProvider>
    );

    // Find and click the Add System button
    const addSystemButton = screen.getAllByText('Add System')[0];
    fireEvent.click(addSystemButton);
    
    // Check that onAddSystem was called
    expect(mockProps.onAddSystem).toHaveBeenCalled();
  });
  
  it('toggles between dashboard tabs when clicked', () => {
    render(
      <ThemeProvider theme={theme}>
        <ConfigurationDashboard {...mockProps} />
      </ThemeProvider>
    );

    // Check that Overview tab is active by default
    expect(screen.getByText('System Overview')).toBeInTheDocument();
    
    // Click on Health Status tab
    fireEvent.click(screen.getByText('Health Status'));
    
    // Check that Health Status content is displayed
    expect(screen.getByText('System Health Status')).toBeInTheDocument();
    
    // Click on Data Flow tab
    fireEvent.click(screen.getByText('Data Flow'));
    
    // Check that Data Flow content is displayed
    expect(screen.getByText('Data Flow Visualization')).toBeInTheDocument();
    
    // Click on Performance tab
    fireEvent.click(screen.getByText('Performance'));
    
    // Check that Performance content is displayed
    expect(screen.getByText('Sync History Details')).toBeInTheDocument();
  });
  
  it('filters systems and connections when Show only active is toggled', () => {
    render(
      <ThemeProvider theme={theme}>
        <ConfigurationDashboard {...mockProps} />
      </ThemeProvider>
    );

    // Check that Show only active switch exists
    const activeSwitch = screen.getByLabelText('Show only active');
    expect(activeSwitch).toBeInTheDocument();
    
    // Check that it's checked by default
    expect(activeSwitch).toBeChecked();
    
    // Click on Health Status tab to see filtered systems
    fireEvent.click(screen.getByText('Health Status'));
    
    // Toggle the switch
    fireEvent.click(activeSwitch);
    
    // Check that it's unchecked now
    expect(activeSwitch).not.toBeChecked();
  });

  it('calls onAddConnection when Add Connection button is clicked', () => {
    render(
      <ThemeProvider theme={theme}>
        <ConfigurationDashboard {...mockProps} />
      </ThemeProvider>
    );

    // Find and click the Add Connection button
    const addConnectionButton = screen.getByText('Add Connection');
    fireEvent.click(addConnectionButton);
    
    // Check that onAddConnection was called
    expect(mockProps.onAddConnection).toHaveBeenCalled();
  });

  it('shows loading indicators when data is loading', () => {
    render(
      <ThemeProvider theme={theme}>
        <ConfigurationDashboard 
          {...mockProps} 
          isLoadingSystems={true}
          isLoadingConnections={true}
        />
      </ThemeProvider>
    );

    // Check that loading indicators are displayed
    const loadingIndicators = screen.getAllByRole('progressbar');
    expect(loadingIndicators.length).toBeGreaterThan(0);
  });

  it('calls onTestConnection when Test Connection button is clicked', () => {
    render(
      <ThemeProvider theme={theme}>
        <ConfigurationDashboard {...mockProps} />
      </ThemeProvider>
    );

    // Find and click the Test Connection button
    const testConnectionButtons = screen.getAllByText('Test Connection');
    fireEvent.click(testConnectionButtons[0]);
    
    // Check that onTestConnection was called
    expect(mockProps.onTestConnection).toHaveBeenCalled();
  });

  it('calls onSyncNow when Sync Now button is clicked', () => {
    render(
      <ThemeProvider theme={theme}>
        <ConfigurationDashboard {...mockProps} />
      </ThemeProvider>
    );

    // Find and click the Sync Now button
    const syncNowButton = screen.getByText('Sync Now');
    fireEvent.click(syncNowButton);
    
    // Check that onSyncNow was called
    expect(mockProps.onSyncNow).toHaveBeenCalled();
  });
});
