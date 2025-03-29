import React, { useState, useEffect } from 'react';
import {
  Box,
  Typography,
  Button,
  Tabs,
  Tab,
  Paper,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  TextField,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  Grid,
  Alert,
  CircularProgress,
  Snackbar,
} from '@mui/material';
import { Add as AddIcon, Dashboard as DashboardIcon } from '@mui/icons-material';
import { v4 as uuidv4 } from 'uuid';
import { useSelector, useDispatch } from 'react-redux';
import { RootState } from '../../store';
import {
  SystemEndpoint,
  SystemConnection,
  addSystem,
  updateSystem,
  removeSystem,
  toggleSystemEnabled,
  addConnection,
  updateConnection,
  removeConnection,
  toggleConnectionEnabled,
  useGetSystemsQuery,
  useAddSystemMutation,
  useUpdateSystemMutation,
  useDeleteSystemMutation,
  useGetConnectionsQuery,
  useAddConnectionMutation,
  useUpdateConnectionMutation,
  useDeleteConnectionMutation,
  useTestConnectionMutation,
  useSyncNowMutation,
} from '../../store/slices/configurationSlice';
import SystemEndpointCard from './SystemEndpointCard';
import ConnectionCard from './ConnectionCard';
import ConfigurationDashboard from './ConfigurationDashboard';

interface TabPanelProps {
  children?: React.ReactNode;
  index: number;
  value: number;
}

function TabPanel(props: TabPanelProps) {
  const { children, value, index, ...other } = props;

  return (
    <div
      role="tabpanel"
      hidden={value !== index}
      id={`config-tabpanel-${index}`}
      aria-labelledby={`config-tab-${index}`}
      {...other}
    >
      {value === index && <Box sx={{ p: 3 }}>{children}</Box>}
    </div>
  );
}

function a11yProps(index: number) {
  return {
    id: `config-tab-${index}`,
    'aria-controls': `config-tabpanel-${index}`,
  };
}

const CrossSystemConfiguration: React.FC = () => {
  const dispatch = useDispatch();
  const [tabValue, setTabValue] = useState(0); // Start with Dashboard view
  const [addSystemDialogOpen, setAddSystemDialogOpen] = useState(false);
  const [addConnectionDialogOpen, setAddConnectionDialogOpen] = useState(false);
  const [editing, setEditing] = useState(false);
  const [editedSystem, setEditedSystem] = useState<SystemEndpoint | null>(null);
  const [editedConnection, setEditedConnection] = useState<SystemConnection | null>(null);
  const [newSystem, setNewSystem] = useState<Omit<SystemEndpoint, 'id'>>({
    name: '',
    url: '',
    enabled: true,
    authType: 'none',
  });
  const [newConnection, setNewConnection] = useState<Omit<SystemConnection, 'id'>>({
    sourceSystemId: '',
    targetSystemId: '',
    connectionType: 'two-way',
    enabled: true,
    syncInterval: 5,
    dataMapping: [],
  });
  const [snackbar, setSnackbar] = useState<{
    open: boolean;
    message: string;
    severity: 'success' | 'error' | 'info' | 'warning';
  }>({
    open: false,
    message: '',
    severity: 'info',
  });

  // Use Redux state for local operations
  const { systems, connections } = useSelector((state: RootState) => state.configuration);

  // Use RTK Query for API operations
  const {
    data: systemsData,
    isLoading: isLoadingSystems,
    isError: isSystemsError,
    refetch: refetchSystems,
  } = useGetSystemsQuery();

  const {
    data: connectionsData,
    isLoading: isLoadingConnections,
    isError: isConnectionsError,
    refetch: refetchConnections,
  } = useGetConnectionsQuery();

  const [addSystemMutation] = useAddSystemMutation();
  const [updateSystemMutation] = useUpdateSystemMutation();
  const [deleteSystemMutation] = useDeleteSystemMutation();
  const [addConnectionMutation] = useAddConnectionMutation();
  const [updateConnectionMutation] = useUpdateConnectionMutation();
  const [deleteConnectionMutation] = useDeleteConnectionMutation();
  const [testConnectionMutation] = useTestConnectionMutation();
  const [syncNowMutation] = useSyncNowMutation();

  const handleTabChange = (event: React.SyntheticEvent, newValue: number) => {
    setTabValue(newValue);
  };

  const handleAddSystemDialogOpen = () => {
    setNewSystem({
      name: '',
      url: '',
      enabled: true,
      authType: 'none',
    });
    setAddSystemDialogOpen(true);
  };

  const handleAddSystemDialogClose = () => {
    setAddSystemDialogOpen(false);
  };

  const handleAddConnectionDialogOpen = () => {
    setNewConnection({
      sourceSystemId: systems.length > 0 ? systems[0].id : '',
      targetSystemId: systems.length > 1 ? systems[1].id : '',
      connectionType: 'two-way',
      enabled: true,
      syncInterval: 5,
      dataMapping: [],
    });
    setAddConnectionDialogOpen(true);
  };

  const handleAddConnectionDialogClose = () => {
    setAddConnectionDialogOpen(false);
  };

  const handleSystemChange = (e: React.ChangeEvent<HTMLInputElement | { name?: string; value: unknown }>) => {
    const { name, value } = e.target;
    if (name) {
      setNewSystem({
        ...newSystem,
        [name]: value,
      });
    }
  };

  const handleConnectionChange = (e: React.ChangeEvent<HTMLInputElement | { name?: string; value: unknown }>) => {
    const { name, value } = e.target;
    if (name) {
      setNewConnection({
        ...newConnection,
        [name]: value,
      });
    }
  };

  const handleAddSystem = async () => {
    try {
      const systemWithId = {
        ...newSystem,
        id: uuidv4(),
      };
      
      // Update local state
      dispatch(addSystem(systemWithId));
      
      // Call API
      await addSystemMutation(newSystem);
      
      setAddSystemDialogOpen(false);
      setSnackbar({
        open: true,
        message: 'System added successfully',
        severity: 'success',
      });
    } catch (error) {
      setSnackbar({
        open: true,
        message: `Failed to add system: ${error}`,
        severity: 'error',
      });
    }
  };

  const handleAddConnection = async () => {
    try {
      const connectionWithId = {
        ...newConnection,
        id: uuidv4(),
      };
      
      // Update local state
      dispatch(addConnection(connectionWithId));
      
      // Call API
      await addConnectionMutation(newConnection);
      
      setAddConnectionDialogOpen(false);
      setSnackbar({
        open: true,
        message: 'Connection added successfully',
        severity: 'success',
      });
    } catch (error) {
      setSnackbar({
        open: true,
        message: `Failed to add connection: ${error}`,
        severity: 'error',
      });
    }
  };

  const handleUpdateSystem = async (system: SystemEndpoint) => {
    try {
      // Update local state
      dispatch(updateSystem(system));
      
      // Call API
      await updateSystemMutation(system);
      
      setSnackbar({
        open: true,
        message: 'System updated successfully',
        severity: 'success',
      });
    } catch (error) {
      setSnackbar({
        open: true,
        message: `Failed to update system: ${error}`,
        severity: 'error',
      });
    }
  };

  const handleDeleteSystem = async (id: string) => {
    try {
      // Update local state
      dispatch(removeSystem(id));
      
      // Call API
      await deleteSystemMutation(id);
      
      setSnackbar({
        open: true,
        message: 'System deleted successfully',
        severity: 'success',
      });
    } catch (error) {
      setSnackbar({
        open: true,
        message: `Failed to delete system: ${error}`,
        severity: 'error',
      });
    }
  };

  const handleToggleSystemEnabled = async (id: string) => {
    try {
      // Update local state
      dispatch(toggleSystemEnabled(id));
      
      // Get the updated system
      const system = systems.find(s => s.id === id);
      if (system) {
        // Call API
        await updateSystemMutation(system);
      }
    } catch (error) {
      setSnackbar({
        open: true,
        message: `Failed to toggle system: ${error}`,
        severity: 'error',
      });
    }
  };

  const handleUpdateConnection = async (connection: SystemConnection) => {
    try {
      // Update local state
      dispatch(updateConnection(connection));
      
      // Call API
      await updateConnectionMutation(connection);
      
      setSnackbar({
        open: true,
        message: 'Connection updated successfully',
        severity: 'success',
      });
    } catch (error) {
      setSnackbar({
        open: true,
        message: `Failed to update connection: ${error}`,
        severity: 'error',
      });
    }
  };

  const handleDeleteConnection = async (id: string) => {
    try {
      // Update local state
      dispatch(removeConnection(id));
      
      // Call API
      await deleteConnectionMutation(id);
      
      setSnackbar({
        open: true,
        message: 'Connection deleted successfully',
        severity: 'success',
      });
    } catch (error) {
      setSnackbar({
        open: true,
        message: `Failed to delete connection: ${error}`,
        severity: 'error',
      });
    }
  };

  const handleToggleConnectionEnabled = async (id: string) => {
    try {
      // Update local state
      dispatch(toggleConnectionEnabled(id));
      
      // Get the updated connection
      const connection = connections.find(c => c.id === id);
      if (connection) {
        // Call API
        await updateConnectionMutation(connection);
      }
    } catch (error) {
      setSnackbar({
        open: true,
        message: `Failed to toggle connection: ${error}`,
        severity: 'error',
      });
    }
  };

  const handleTestConnection = async (id: string) => {
    try {
      const result = await testConnectionMutation(id).unwrap();
      setSnackbar({
        open: true,
        message: result.message,
        severity: result.success ? 'success' : 'error',
      });
    } catch (error) {
      setSnackbar({
        open: true,
        message: `Failed to test connection: ${error}`,
        severity: 'error',
      });
    }
  };

  const handleSyncNow = async (id: string) => {
    try {
      await syncNowMutation(id);
      setSnackbar({
        open: true,
        message: 'Sync started successfully',
        severity: 'success',
      });
    } catch (error) {
      setSnackbar({
        open: true,
        message: `Failed to start sync: ${error}`,
        severity: 'error',
      });
    }
  };

  const handleCloseSnackbar = () => {
    setSnackbar({
      ...snackbar,
      open: false,
    });
  };

  return (
    <Box sx={{ width: '100%' }}>
      <Paper sx={{ width: '100%', mb: 2 }}>
        <Tabs
          value={tabValue}
          onChange={handleTabChange}
          aria-label="configuration tabs"
          sx={{ borderBottom: 1, borderColor: 'divider' }}
        >
          <Tab icon={<DashboardIcon />} label="Dashboard" {...a11yProps(0)} />
          <Tab label="Systems" {...a11yProps(1)} />
          <Tab label="Connections" {...a11yProps(2)} />
          <Tab label="Sync History" {...a11yProps(3)} />
        </Tabs>

        {/* Dashboard Tab */}
        <TabPanel value={tabValue} index={0}>
          <ConfigurationDashboard
            systems={systems}
            connections={connections}
            isLoadingSystems={isLoadingSystems}
            isLoadingConnections={isLoadingConnections}
            onAddSystem={handleAddSystemDialogOpen}
            onAddConnection={handleAddConnectionDialogOpen}
            onTestConnection={handleTestConnection}
            onSyncNow={handleSyncNow}
            onEditSystem={(id: string) => {
              const system = systems.find((s: SystemEndpoint) => s.id === id);
              if (system) {
                setEditedSystem({ ...system });
                setEditing(true);
                setTabValue(1); // Switch to Systems tab
              }
            }}
            onEditConnection={(id: string) => {
              const connection = connections.find((c: SystemConnection) => c.id === id);
              if (connection) {
                setEditedConnection({ ...connection });
                setEditing(true);
                setTabValue(2); // Switch to Connections tab
              }
            }}
          />
        </TabPanel>

        {/* Systems Tab */}
        <TabPanel value={tabValue} index={1}>
          <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 2 }}>
            <Typography variant="h6">System Endpoints</Typography>
            <Button
              variant="contained"
              startIcon={<AddIcon />}
              onClick={handleAddSystemDialogOpen}
            >
              Add System
            </Button>
          </Box>

          {isLoadingSystems ? (
            <Box sx={{ display: 'flex', justifyContent: 'center', p: 3 }}>
              <CircularProgress />
            </Box>
          ) : isSystemsError ? (
            <Alert severity="error" sx={{ mb: 2 }}>
              Error loading systems. Please try again.
            </Alert>
          ) : systems.length === 0 ? (
            <Alert severity="info" sx={{ mb: 2 }}>
              No systems configured. Add a system to get started.
            </Alert>
          ) : (
            systems.map(system => (
              <SystemEndpointCard
                key={system.id}
                system={system}
                onToggleEnabled={handleToggleSystemEnabled}
                onUpdate={handleUpdateSystem}
                onDelete={handleDeleteSystem}
                onTestConnection={handleTestConnection}
              />
            ))
          )}
        </TabPanel>

        {/* Connections Tab */}
        <TabPanel value={tabValue} index={2}>
          <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 2 }}>
            <Typography variant="h6">System Connections</Typography>
            <Button
              variant="contained"
              startIcon={<AddIcon />}
              onClick={handleAddConnectionDialogOpen}
              disabled={systems.length < 2}
            >
              Add Connection
            </Button>
          </Box>

          {isLoadingConnections ? (
            <Box sx={{ display: 'flex', justifyContent: 'center', p: 3 }}>
              <CircularProgress />
            </Box>
          ) : isConnectionsError ? (
            <Alert severity="error" sx={{ mb: 2 }}>
              Error loading connections. Please try again.
            </Alert>
          ) : systems.length < 2 ? (
            <Alert severity="info" sx={{ mb: 2 }}>
              You need at least two systems to create a connection.
            </Alert>
          ) : connections.length === 0 ? (
            <Alert severity="info" sx={{ mb: 2 }}>
              No connections configured. Add a connection to get started.
            </Alert>
          ) : (
            connections.map(connection => (
              <ConnectionCard
                key={connection.id}
                connection={connection}
                systems={systems}
                onToggleEnabled={handleToggleConnectionEnabled}
                onUpdate={handleUpdateConnection}
                onDelete={handleDeleteConnection}
                onTestConnection={handleTestConnection}
                onSyncNow={handleSyncNow}
              />
            ))
          )}
        </TabPanel>

        {/* Sync History Tab */}
        <TabPanel value={tabValue} index={3}>
          <Typography variant="h6" gutterBottom>
            Sync History
          </Typography>
          <Alert severity="info">
            Sync history will be displayed here. This feature is coming soon.
          </Alert>
        </TabPanel>
      </Paper>

      {/* Add System Dialog */}
      <Dialog open={addSystemDialogOpen} onClose={handleAddSystemDialogClose}>
        <DialogTitle>Add System</DialogTitle>
        <DialogContent>
          <Grid container spacing={2} sx={{ mt: 1 }}>
            <Grid item xs={12}>
              <TextField
                fullWidth
                label="System Name"
                name="name"
                value={newSystem.name}
                onChange={handleSystemChange}
              />
            </Grid>
            <Grid item xs={12}>
              <TextField
                fullWidth
                label="URL"
                name="url"
                value={newSystem.url}
                onChange={handleSystemChange}
              />
            </Grid>
            <Grid item xs={12}>
              <FormControl fullWidth>
                <InputLabel id="auth-type-label">Authentication Type</InputLabel>
                <Select
                  labelId="auth-type-label"
                  id="auth-type"
                  name="authType"
                  value={newSystem.authType}
                  onChange={handleSystemChange}
                  label="Authentication Type"
                >
                  <MenuItem value="none">None</MenuItem>
                  <MenuItem value="basic">Basic Auth</MenuItem>
                  <MenuItem value="token">Token</MenuItem>
                  <MenuItem value="oauth">OAuth</MenuItem>
                </Select>
              </FormControl>
            </Grid>
          </Grid>
        </DialogContent>
        <DialogActions>
          <Button onClick={handleAddSystemDialogClose}>Cancel</Button>
          <Button
            onClick={handleAddSystem}
            variant="contained"
            disabled={!newSystem.name || !newSystem.url}
          >
            Add
          </Button>
        </DialogActions>
      </Dialog>

      {/* Add Connection Dialog */}
      <Dialog open={addConnectionDialogOpen} onClose={handleAddConnectionDialogClose}>
        <DialogTitle>Add Connection</DialogTitle>
        <DialogContent>
          <Grid container spacing={2} sx={{ mt: 1 }}>
            <Grid item xs={12}>
              <FormControl fullWidth>
                <InputLabel id="source-system-label">Source System</InputLabel>
                <Select
                  labelId="source-system-label"
                  id="source-system"
                  name="sourceSystemId"
                  value={newConnection.sourceSystemId}
                  onChange={handleConnectionChange}
                  label="Source System"
                >
                  {systems.map(system => (
                    <MenuItem key={system.id} value={system.id}>
                      {system.name}
                    </MenuItem>
                  ))}
                </Select>
              </FormControl>
            </Grid>
            <Grid item xs={12}>
              <FormControl fullWidth>
                <InputLabel id="target-system-label">Target System</InputLabel>
                <Select
                  labelId="target-system-label"
                  id="target-system"
                  name="targetSystemId"
                  value={newConnection.targetSystemId}
                  onChange={handleConnectionChange}
                  label="Target System"
                >
                  {systems.map(system => (
                    <MenuItem key={system.id} value={system.id}>
                      {system.name}
                    </MenuItem>
                  ))}
                </Select>
              </FormControl>
            </Grid>
            <Grid item xs={12}>
              <FormControl fullWidth>
                <InputLabel id="connection-type-label">Connection Type</InputLabel>
                <Select
                  labelId="connection-type-label"
                  id="connection-type"
                  name="connectionType"
                  value={newConnection.connectionType}
                  onChange={handleConnectionChange}
                  label="Connection Type"
                >
                  <MenuItem value="one-way">One-way</MenuItem>
                  <MenuItem value="two-way">Two-way</MenuItem>
                </Select>
              </FormControl>
            </Grid>
            <Grid item xs={12}>
              <TextField
                fullWidth
                label="Sync Interval (minutes)"
                name="syncInterval"
                type="number"
                value={newConnection.syncInterval}
                onChange={handleConnectionChange}
                inputProps={{ min: 1 }}
              />
            </Grid>
          </Grid>
        </DialogContent>
        <DialogActions>
          <Button onClick={handleAddConnectionDialogClose}>Cancel</Button>
          <Button
            onClick={handleAddConnection}
            variant="contained"
            disabled={
              !newConnection.sourceSystemId ||
              !newConnection.targetSystemId ||
              newConnection.sourceSystemId === newConnection.targetSystemId
            }
          >
            Add
          </Button>
        </DialogActions>
      </Dialog>

      {/* Snackbar for notifications */}
      <Snackbar
        open={snackbar.open}
        autoHideDuration={6000}
        onClose={handleCloseSnackbar}
        anchorOrigin={{ vertical: 'bottom', horizontal: 'center' }}
      >
        <Alert onClose={handleCloseSnackbar} severity={snackbar.severity} sx={{ width: '100%' }}>
          {snackbar.message}
        </Alert>
      </Snackbar>
    </Box>
  );
};

export default CrossSystemConfiguration;
