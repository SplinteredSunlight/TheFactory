import React, { useState } from 'react';
import { useDispatch, useSelector } from 'react-redux';
import {
  Box,
  Typography,
  Paper,
  Grid,
  Card,
  CardContent,
  CardHeader,
  Switch,
  FormControlLabel,
  Button,
  TextField,
  Divider,
  List,
  ListItem,
  ListItemText,
  ListItemSecondaryAction,
  IconButton,
  Tooltip,
  Alert,
  Snackbar,
  useTheme,
  Tabs,
  Tab,
} from '@mui/material';
import {
  Save as SaveIcon,
  Delete as DeleteIcon,
  Add as AddIcon,
  Refresh as RefreshIcon,
  Settings as SettingsIcon,
  Security as SecurityIcon,
  Notifications as NotificationsIcon,
  Palette as PaletteIcon,
  Storage as StorageIcon,
  SyncAlt as SyncAltIcon,
} from '@mui/icons-material';
import CrossSystemConfiguration from '../components/configuration/CrossSystemConfiguration';
import { RootState } from '../store';
import { toggleDarkMode } from '../store/slices/uiSlice';

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
      id={`settings-tabpanel-${index}`}
      aria-labelledby={`settings-tab-${index}`}
      {...other}
    >
      {value === index && (
        <Box sx={{ p: 3 }}>
          {children}
        </Box>
      )}
    </div>
  );
}

function a11yProps(index: number) {
  return {
    id: `settings-tab-${index}`,
    'aria-controls': `settings-tabpanel-${index}`,
  };
}

const Settings: React.FC = () => {
  const dispatch = useDispatch();
  const theme = useTheme();
  const [tabValue, setTabValue] = useState(0);
  const [saveSuccess, setSaveSuccess] = useState(false);
  
  // Get data from Redux store
  const { darkMode } = useSelector((state: RootState) => state.ui);

  // Local state for form values
  const [apiEndpoint, setApiEndpoint] = useState('https://api.example.com');
  const [refreshInterval, setRefreshInterval] = useState('30');
  const [enableNotifications, setEnableNotifications] = useState(true);
  const [enableSounds, setEnableSounds] = useState(false);
  const [logLevel, setLogLevel] = useState('info');
  const [maxLogSize, setMaxLogSize] = useState('100');

  // Handle tab change
  const handleTabChange = (event: React.SyntheticEvent, newValue: number) => {
    setTabValue(newValue);
  };

  // Handle save settings
  const handleSaveSettings = () => {
    // In a real application, we would dispatch actions to save the settings
    // dispatch(saveSettings({
    //   apiEndpoint,
    //   refreshInterval: parseInt(refreshInterval),
    //   enableNotifications,
    //   enableSounds,
    //   logLevel,
    //   maxLogSize: parseInt(maxLogSize),
    // }));

    // Show success message
    setSaveSuccess(true);
  };

  // Handle close snackbar
  const handleCloseSnackbar = () => {
    setSaveSuccess(false);
  };

  return (
    <Box sx={{ flexGrow: 1 }}>
      <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 3 }}>
        <Typography variant="h4" component="h1">
          Settings
        </Typography>
        <Button
          variant="contained"
          startIcon={<SaveIcon />}
          onClick={handleSaveSettings}
        >
          Save Settings
        </Button>
      </Box>

      <Paper sx={{ width: '100%' }}>
        <Box sx={{ borderBottom: 1, borderColor: 'divider' }}>
          <Tabs value={tabValue} onChange={handleTabChange} aria-label="settings tabs">
            <Tab icon={<SettingsIcon />} label="General" {...a11yProps(0)} />
            <Tab icon={<SecurityIcon />} label="Security" {...a11yProps(1)} />
            <Tab icon={<NotificationsIcon />} label="Notifications" {...a11yProps(2)} />
            <Tab icon={<PaletteIcon />} label="Appearance" {...a11yProps(3)} />
            <Tab icon={<SyncAltIcon />} label="Cross-System" {...a11yProps(4)} />
            <Tab icon={<StorageIcon />} label="Advanced" {...a11yProps(5)} />
          </Tabs>
        </Box>

        {/* General Settings */}
        <TabPanel value={tabValue} index={0}>
          <Grid container spacing={3}>
            <Grid item xs={12} md={6}>
              <Card variant="outlined">
                <CardHeader title="API Settings" />
                <CardContent>
                  <TextField
                    fullWidth
                    label="API Endpoint"
                    value={apiEndpoint}
                    onChange={(e) => setApiEndpoint(e.target.value)}
                    margin="normal"
                  />
                  <TextField
                    fullWidth
                    label="Refresh Interval (seconds)"
                    type="number"
                    value={refreshInterval}
                    onChange={(e) => setRefreshInterval(e.target.value)}
                    margin="normal"
                    inputProps={{ min: 5, max: 3600 }}
                  />
                </CardContent>
              </Card>
            </Grid>
            <Grid item xs={12} md={6}>
              <Card variant="outlined">
                <CardHeader title="Integration Settings" />
                <CardContent>
                  <Typography variant="body1" paragraph>
                    Configure integration settings for AI-Orchestrator and Fast-Agent.
                  </Typography>
                  <Button variant="outlined" startIcon={<RefreshIcon />}>
                    Test Connection
                  </Button>
                </CardContent>
              </Card>
            </Grid>
          </Grid>
        </TabPanel>

        {/* Security Settings */}
        <TabPanel value={tabValue} index={1}>
          <Grid container spacing={3}>
            <Grid item xs={12} md={6}>
              <Card variant="outlined">
                <CardHeader title="Authentication" />
                <CardContent>
                  <Typography variant="body1" paragraph>
                    Configure authentication settings for the platform.
                  </Typography>
                  <Button variant="outlined" color="primary">
                    Change Password
                  </Button>
                </CardContent>
              </Card>
            </Grid>
            <Grid item xs={12} md={6}>
              <Card variant="outlined">
                <CardHeader title="API Keys" />
                <CardContent>
                  <Typography variant="body1" paragraph>
                    Manage API keys for external integrations.
                  </Typography>
                  <List>
                    <ListItem>
                      <ListItemText
                        primary="Production API Key"
                        secondary="Created: 2025-01-15"
                      />
                      <ListItemSecondaryAction>
                        <Tooltip title="Delete">
                          <IconButton edge="end" aria-label="delete">
                            <DeleteIcon />
                          </IconButton>
                        </Tooltip>
                      </ListItemSecondaryAction>
                    </ListItem>
                    <Divider />
                    <ListItem>
                      <ListItemText
                        primary="Development API Key"
                        secondary="Created: 2025-02-20"
                      />
                      <ListItemSecondaryAction>
                        <Tooltip title="Delete">
                          <IconButton edge="end" aria-label="delete">
                            <DeleteIcon />
                          </IconButton>
                        </Tooltip>
                      </ListItemSecondaryAction>
                    </ListItem>
                  </List>
                  <Button
                    variant="outlined"
                    startIcon={<AddIcon />}
                    sx={{ mt: 2 }}
                  >
                    Generate New API Key
                  </Button>
                </CardContent>
              </Card>
            </Grid>
          </Grid>
        </TabPanel>

        {/* Notification Settings */}
        <TabPanel value={tabValue} index={2}>
          <Grid container spacing={3}>
            <Grid item xs={12} md={6}>
              <Card variant="outlined">
                <CardHeader title="Notification Preferences" />
                <CardContent>
                  <FormControlLabel
                    control={
                      <Switch
                        checked={enableNotifications}
                        onChange={(e) => setEnableNotifications(e.target.checked)}
                        color="primary"
                      />
                    }
                    label="Enable Notifications"
                  />
                  <FormControlLabel
                    control={
                      <Switch
                        checked={enableSounds}
                        onChange={(e) => setEnableSounds(e.target.checked)}
                        color="primary"
                      />
                    }
                    label="Enable Notification Sounds"
                  />
                </CardContent>
              </Card>
            </Grid>
            <Grid item xs={12} md={6}>
              <Card variant="outlined">
                <CardHeader title="Notification Types" />
                <CardContent>
                  <FormControlLabel
                    control={<Switch defaultChecked color="primary" />}
                    label="Agent Status Changes"
                  />
                  <FormControlLabel
                    control={<Switch defaultChecked color="primary" />}
                    label="Task Completions"
                  />
                  <FormControlLabel
                    control={<Switch defaultChecked color="primary" />}
                    label="Task Failures"
                  />
                  <FormControlLabel
                    control={<Switch defaultChecked color="primary" />}
                    label="System Alerts"
                  />
                </CardContent>
              </Card>
            </Grid>
          </Grid>
        </TabPanel>

        {/* Appearance Settings */}
        <TabPanel value={tabValue} index={3}>
          <Grid container spacing={3}>
            <Grid item xs={12} md={6}>
              <Card variant="outlined">
                <CardHeader title="Theme" />
                <CardContent>
                  <FormControlLabel
                    control={
                      <Switch
                        checked={darkMode}
                        onChange={() => dispatch(toggleDarkMode())}
                        color="primary"
                      />
                    }
                    label="Dark Mode"
                  />
                </CardContent>
              </Card>
            </Grid>
            <Grid item xs={12} md={6}>
              <Card variant="outlined">
                <CardHeader title="Dashboard Layout" />
                <CardContent>
                  <Typography variant="body1" paragraph>
                    Configure the layout of the dashboard widgets.
                  </Typography>
                  <Button variant="outlined">
                    Reset to Default Layout
                  </Button>
                </CardContent>
              </Card>
            </Grid>
          </Grid>
        </TabPanel>

        {/* Cross-System Configuration */}
        <TabPanel value={tabValue} index={4}>
          <CrossSystemConfiguration />
        </TabPanel>

        {/* Advanced Settings */}
        <TabPanel value={tabValue} index={5}>
          <Grid container spacing={3}>
            <Grid item xs={12} md={6}>
              <Card variant="outlined">
                <CardHeader title="Logging" />
                <CardContent>
                  <TextField
                    select
                    fullWidth
                    label="Log Level"
                    value={logLevel}
                    onChange={(e) => setLogLevel(e.target.value)}
                    margin="normal"
                    SelectProps={{
                      native: true,
                    }}
                  >
                    <option value="debug">Debug</option>
                    <option value="info">Info</option>
                    <option value="warn">Warning</option>
                    <option value="error">Error</option>
                  </TextField>
                  <TextField
                    fullWidth
                    label="Max Log Size (MB)"
                    type="number"
                    value={maxLogSize}
                    onChange={(e) => setMaxLogSize(e.target.value)}
                    margin="normal"
                    inputProps={{ min: 10, max: 1000 }}
                  />
                </CardContent>
              </Card>
            </Grid>
            <Grid item xs={12} md={6}>
              <Card variant="outlined">
                <CardHeader title="Data Management" />
                <CardContent>
                  <Typography variant="body1" paragraph>
                    Manage application data and cache.
                  </Typography>
                  <Button
                    variant="outlined"
                    color="error"
                    sx={{ mr: 2 }}
                  >
                    Clear Cache
                  </Button>
                  <Button
                    variant="outlined"
                    color="error"
                  >
                    Reset All Settings
                  </Button>
                </CardContent>
              </Card>
            </Grid>
          </Grid>
        </TabPanel>
      </Paper>

      <Snackbar
        open={saveSuccess}
        autoHideDuration={6000}
        onClose={handleCloseSnackbar}
        anchorOrigin={{ vertical: 'bottom', horizontal: 'center' }}
      >
        <Alert onClose={handleCloseSnackbar} severity="success" sx={{ width: '100%' }}>
          Settings saved successfully!
        </Alert>
      </Snackbar>
    </Box>
  );
};

export default Settings;
