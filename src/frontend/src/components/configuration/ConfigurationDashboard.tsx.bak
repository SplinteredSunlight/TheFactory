import React, { useState, useEffect } from 'react';
import {
  Box,
  Typography,
  Grid,
  Card,
  CardContent,
  CardHeader,
  Avatar,
  Chip,
  Button,
  IconButton,
  Tooltip,
  Divider,
  Paper,
  useTheme,
  CircularProgress,
  FormControlLabel,
  Switch,
  Tab,
  Tabs,
  Badge,
  LinearProgress,
  Alert,
  Menu,
  MenuItem,
  TextField,
  InputAdornment,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  TablePagination,
} from '@mui/material';
import {
  Storage as StorageIcon,
  SyncAlt as SyncAltIcon,
  Add as AddIcon,
  Refresh as RefreshIcon,
  Check as CheckIcon,
  Close as CloseIcon,
  Timeline as TimelineIcon,
  Speed as SpeedIcon,
  HealthAndSafety as HealthIcon,
  FilterList as FilterIcon,
  CompareArrows as CompareArrowsIcon,
  Search as SearchIcon,
  Sort as SortIcon,
  Dashboard as DashboardIcon,
  Edit as EditIcon,
  Sync as SyncIcon,
  PieChart as PieChartIcon,
  BarChart as BarChartIcon,
  Error as ErrorIcon,
  Warning as WarningIcon,
  Code as CodeIcon,
  Api as ApiIcon,
  Settings as SettingsIcon,
  Memory as MemoryIcon,
  Psychology as PsychologyIcon,
  DataObject as DataObjectIcon,
} from '@mui/icons-material';
import { Line, Doughnut, Bar } from 'react-chartjs-2';
import {
  Chart as ChartJS,
  ArcElement,
  Tooltip as ChartTooltip,
  Legend,
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  Title,
  BarElement,
} from 'chart.js';

// Register ChartJS components
ChartJS.register(
  ArcElement,
  ChartTooltip,
  Legend,
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  BarElement,
  Title
);
import { SystemEndpoint, SystemConnection } from '../../store/slices/configurationSlice';
import { AgentFramework } from '../../types/agent';

interface ConfigurationDashboardProps {
  systems: SystemEndpoint[];
  connections: SystemConnection[];
  isLoadingSystems: boolean;
  isLoadingConnections: boolean;
  onAddSystem: () => void;
  onAddConnection: () => void;
  onTestConnection: (id: string) => void;
  onSyncNow: (id: string) => void;
  onEditSystem: (id: string) => void;
  onEditConnection: (id: string) => void;
}

// Mock sync history data for demonstration
interface SyncHistoryItem {
  id: string;
  connectionId: string;
  timestamp: string;
  status: 'success' | 'partial' | 'failed';
  recordsProcessed: number;
  recordsSucceeded: number;
  recordsFailed: number;
  duration: number; // in seconds
}

// Mock agent data for demonstration
interface AgentData {
  id: string;
  name: string;
  framework: AgentFramework;
  status: 'idle' | 'busy' | 'offline' | 'error';
  capabilities: string[];
  lastActive: string;
  currentLoad: number;
}

const mockSyncHistory: SyncHistoryItem[] = [
  {
    id: 'sync-1',
    connectionId: 'connection-1',
    timestamp: '2025-03-09T12:00:00Z',
    status: 'success',
    recordsProcessed: 120,
    recordsSucceeded: 120,
    recordsFailed: 0,
    duration: 3.2,
  },
  {
    id: 'sync-2',
    connectionId: 'connection-1',
    timestamp: '2025-03-09T11:00:00Z',
    status: 'success',
    recordsProcessed: 115,
    recordsSucceeded: 115,
    recordsFailed: 0,
    duration: 3.1,
  },
  {
    id: 'sync-3',
    connectionId: 'connection-1',
    timestamp: '2025-03-09T10:00:00Z',
    status: 'partial',
    recordsProcessed: 118,
    recordsSucceeded: 110,
    recordsFailed: 8,
    duration: 3.5,
  },
  {
    id: 'sync-4',
    connectionId: 'connection-1',
    timestamp: '2025-03-09T09:00:00Z',
    status: 'success',
    recordsProcessed: 105,
    recordsSucceeded: 105,
    recordsFailed: 0,
    duration: 2.9,
  },
  {
    id: 'sync-5',
    connectionId: 'connection-1',
    timestamp: '2025-03-09T08:00:00Z',
    status: 'failed',
    recordsProcessed: 112,
    recordsSucceeded: 0,
    recordsFailed: 112,
    duration: 4.2,
  },
  {
    id: 'sync-6',
    connectionId: 'connection-2',
    timestamp: '2025-03-09T12:00:00Z',
    status: 'success',
    recordsProcessed: 85,
    recordsSucceeded: 85,
    recordsFailed: 0,
    duration: 2.8,
  },
  {
    id: 'sync-7',
    connectionId: 'connection-2',
    timestamp: '2025-03-09T11:00:00Z',
    status: 'success',
    recordsProcessed: 92,
    recordsSucceeded: 92,
    recordsFailed: 0,
    duration: 3.0,
  },
];

// Mock agent data
const mockAgents: AgentData[] = [
  {
    id: 'agent-1',
    name: 'Text Processing Agent',
    framework: AgentFramework.AI_ORCHESTRATOR,
    status: 'idle',
    capabilities: ['text_processing', 'data_extraction'],
    lastActive: '2025-03-09T11:45:00Z',
    currentLoad: 0,
  },
  {
    id: 'agent-2',
    name: 'Code Generation Agent',
    framework: AgentFramework.FAST_AGENT,
    status: 'busy',
    capabilities: ['code_generation', 'reasoning'],
    lastActive: '2025-03-09T12:05:00Z',
    currentLoad: 2,
  },
  {
    id: 'agent-3',
    name: 'Image Analysis Agent',
    framework: AgentFramework.AI_ORCHESTRATOR,
    status: 'idle',
    capabilities: ['image_analysis'],
    lastActive: '2025-03-09T10:30:00Z',
    currentLoad: 0,
  },
  {
    id: 'agent-4',
    name: 'Conversation Agent',
    framework: AgentFramework.FAST_AGENT,
    status: 'busy',
    capabilities: ['conversation', 'text_generation'],
    lastActive: '2025-03-09T12:10:00Z',
    currentLoad: 1,
  },
  {
    id: 'agent-5',
    name: 'Data Analysis Agent',
    framework: AgentFramework.AI_ORCHESTRATOR,
    status: 'offline',
    capabilities: ['data_extraction', 'reasoning'],
    lastActive: '2025-03-09T09:15:00Z',
    currentLoad: 0,
  },
];

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
      id={`dashboard-tabpanel-${index}`}
      aria-labelledby={`dashboard-tab-${index}`}
      {...other}
    >
      {value === index && <Box sx={{ p: 2 }}>{children}</Box>}
    </div>
  );
}

function a11yProps(index: number) {
  return {
    id: `dashboard-tab-${index}`,
    'aria-controls': `dashboard-tabpanel-${index}`,
  };
}

const ConfigurationDashboard: React.FC<ConfigurationDashboardProps> = ({
  systems,
  connections,
  isLoadingSystems,
  isLoadingConnections,
  onAddSystem,
  onAddConnection,
  onTestConnection,
  onSyncNow,
  onEditSystem,
  onEditConnection,
}) => {
  const theme = useTheme();
  const [dashboardTab, setDashboardTab] = useState(0);
  const [searchTerm, setSearchTerm] = useState('');
  const [showOnlyActive, setShowOnlyActive] = useState(true);
  const [systemHealthData, setSystemHealthData] = useState<{ id: string; health: number; status: 'healthy' | 'warning' | 'critical' }[]>([]);
  const [agents, setAgents] = useState<AgentData[]>(mockAgents);
  
  // Generate mock system health data
  useEffect(() => {
    const mockHealthData = systems.map(system => {
      const health = Math.floor(Math.random() * 100);
      return {
        id: system.id,
        health,
        status: health > 80 ? 'healthy' : health > 50 ? 'warning' : 'critical'
      };
    });
    setSystemHealthData(mockHealthData);
  }, [systems]);
  
  const handleDashboardTabChange = (event: React.SyntheticEvent, newValue: number) => {
    setDashboardTab(newValue);
  };
  
  const handleSearchChange = (event: React.ChangeEvent<HTMLInputElement>) => {
    setSearchTerm(event.target.value);
  };

  // Determine if we have AI-Orchestrator and Fast-Agent systems
  const hasOrchestrator = systems.some(s => s.id === 'orchestrator' || s.name.toLowerCase().includes('orchestrator'));
  const hasFastAgent = systems.some(s => s.id === 'fast-agent' || s.name.toLowerCase().includes('fast-agent'));
  const hasCrossSystemConnection = connections.some(c => {
    const sourceSystem = systems.find(s => s.id === c.sourceSystemId);
    const targetSystem = systems.find(s => s.id === c.targetSystemId);
    
    const isOrchestratorToFastAgent = 
      (sourceSystem?.id === 'orchestrator' || sourceSystem?.name.toLowerCase().includes('orchestrator')) &&
      (targetSystem?.id === 'fast-agent' || targetSystem?.name.toLowerCase().includes('fast-agent'));
    
    const isFastAgentToOrchestrator = 
      (sourceSystem?.id === 'fast-agent' || sourceSystem?.name.toLowerCase().includes('fast-agent')) &&
      (targetSystem?.id === 'orchestrator' || targetSystem?.name.toLowerCase().includes('orchestrator'));
    
    return isOrchestratorToFastAgent || isFastAgentToOrchestrator;
  });

  // Generate chart data for system distribution
  const getSystemDistributionData = () => {
    const enabledCount = systems.filter(s => s.enabled).length;
    const disabledCount = systems.length - enabledCount;
    
    return {
      labels: ['Enabled', 'Disabled'],
      datasets: [
        {
          data: [enabledCount, disabledCount],
          backgroundColor: [
            theme.palette.success.main,
            theme.palette.error.main,
          ],
          borderColor: [
            theme.palette.success.dark,
            theme.palette.error.dark,
          ],
          borderWidth: 1,
        },
      ],
    };
  };

  // Generate chart data for system health distribution
  const getSystemHealthData = () => {
    const healthyCount = systemHealthData.filter(s => s.status === 'healthy').length;
    const warningCount = systemHealthData.filter(s => s.status === 'warning').length;
    const criticalCount = systemHealthData.filter(s => s.status === 'critical').length;
    
    return {
      labels: ['Healthy', 'Warning', 'Critical'],
      datasets: [
        {
          data: [healthyCount, warningCount, criticalCount],
          backgroundColor: [
            theme.palette.success.main,
            theme.palette.warning.main,
            theme.palette.error.main,
          ],
          borderColor: [
            theme.palette.success.dark,
            theme.palette.warning.dark,
            theme.palette.error.dark,
          ],
          borderWidth: 1,
        },
      ],
    };
  };

  // Generate chart data for sync history
  const getSyncHistoryData = () => {
    // Get the last 7 sync records
    const lastSyncs = [...mockSyncHistory].sort((a, b) => 
      new Date(b.timestamp).getTime() - new Date(a.timestamp).getTime()
    ).slice(0, 7).reverse();
    
    const labels = lastSyncs.map(sync => {
      const date = new Date(sync.timestamp);
      return `${date.getHours()}:${date.getMinutes().toString().padStart(2, '0')}`;
    });
    
    const successData = lastSyncs.map(sync => 
      sync.status === 'success' ? sync.recordsSucceeded : 0
    );
    
    const partialData = lastSyncs.map(sync => 
      sync.status === 'partial' ? sync.recordsSucceeded : 0
    );
    
    const failedData = lastSyncs.map(sync => 
      sync.recordsFailed
    );
    
    return {
      labels,
      datasets: [
        {
          label: 'Success',
          data: successData,
          borderColor: theme.palette.success.main,
          backgroundColor: theme.palette.success.main + '40',
          fill: true,
          tension: 0.4,
        },
        {
          label: 'Partial',
          data: partialData,
          borderColor: theme.palette.warning.main,
          backgroundColor: theme.palette.warning.main + '40',
          fill: true,
          tension: 0.4,
        },
        {
          label: 'Failed',
          data: failedData,
          borderColor: theme.palette.error.main,
          backgroundColor: theme.palette.error.main + '40',
          fill: true,
          tension: 0.4,
        },
      ],
    };
  };

  // Generate chart data for agent distribution
  const getAgentDistributionData = () => {
    const orchestratorCount = agents.filter(a => a.framework === AgentFramework.AI_ORCHESTRATOR).length;
    const fastAgentCount = agents.filter(a => a.framework === AgentFramework.FAST_AGENT).length;
    
    return {
      labels: ['AI-Orchestrator', 'Fast-Agent'],
      datasets: [
        {
          data: [orchestratorCount, fastAgentCount],
          backgroundColor: [
            theme.palette.primary.main,
            theme.palette.secondary.main,
          ],
          borderColor: [
            theme.palette.primary.dark,
            theme.palette.secondary.dark,
          ],
          borderWidth: 1,
        },
      ],
    };
  };

  // Generate chart data for agent capabilities
  const getAgentCapabilitiesData = () => {
    const capabilities = new Map<string, number>();
    
    agents.forEach(agent => {
      agent.capabilities.forEach(capability => {
        capabilities.set(capability, (capabilities.get(capability) || 0) + 1);
      });
    });
    
    return {
      labels: Array.from(capabilities.keys()).map(cap => 
        cap.split('_').map(word => word.charAt(0).toUpperCase() + word.slice(1)).join(' ')
      ),
      datasets: [
        {
          label: 'Agents with Capability',
          data: Array.from(capabilities.values()),
          backgroundColor: theme.palette.info.main,
          borderColor: theme.palette.info.dark,
          borderWidth: 1,
        },
      ],
    };
  };

  // Chart options
  const chartOptions = {
    responsive: true,
    maintainAspectRatio: false,
    plugins: {
      legend: {
        position: 'bottom' as const,
      },
    },
  };
  
  // Helper functions
  const getHealthStatusColor = (status: 'healthy' | 'warning' | 'critical') => {
    switch (status) {
      case 'healthy':
        return theme.palette.success.main;
      case 'warning':
        return theme.palette.warning.main;
      case 'critical':
        return theme.palette.error.main;
      default:
        return theme.palette.grey[500];
    }
  };
  
  const getSystemHealth = (systemId: string) => {
    return systemHealthData.find((h) => h.id === systemId) || { 
      health: 0, 
      status: 'critical' as const
    };
  };

  const getAgentStatusColor = (status: string) => {
    switch (status) {
      case 'idle':
        return theme.palette.success.main;
      case 'busy':
        return theme.palette.warning.main;
      case 'offline':
        return theme.palette.grey[500];
      case 'error':
        return theme.palette.error.main;
      default:
        return theme.palette.grey[500];
    }
  };

  const getAgentFrameworkIcon = (framework: AgentFramework) => {
    switch (framework) {
      case AgentFramework.AI_ORCHESTRATOR:
        return <ApiIcon fontSize="small" />;
      case AgentFramework.FAST_AGENT:
        return <CodeIcon fontSize="small" />;
      default:
        return <SettingsIcon fontSize="small" />;
    }
  };

  const getCapabilityIcon = (capability: string) => {
    switch (capability) {
      case 'text_processing':
        return <DataObjectIcon fontSize="small" />;
      case 'code_generation':
        return <CodeIcon fontSize="small" />;
      case 'image_analysis':
        return <PsychologyIcon fontSize="small" />;
      case 'data_extraction':
        return <DataObjectIcon fontSize="small" />;
      case 'conversation':
        return <PsychologyIcon fontSize="small" />;
      case 'reasoning':
        return <PsychologyIcon fontSize="small" />;
      default:
        return <MemoryIcon fontSize="small" />;
    }
  };

  // Filter systems based on search
  const filteredSystems = systems
    .filter((system) => showOnlyActive ? system.enabled : true)
    .filter((system) => {
      if (searchTerm) {
        return system.name.toLowerCase().includes(searchTerm.toLowerCase()) ||
               system.url.toLowerCase().includes(searchTerm.toLowerCase());
      }
      return true;
    });
  
  // Filter connections based on search
  const filteredConnections = connections
    .filter((connection) => showOnlyActive ? connection.enabled : true)
    .filter((connection) => {
      if (searchTerm) {
        const sourceSystem = systems.find((s) => s.id === connection.sourceSystemId);
        const targetSystem = systems.find((s) => s.id === connection.targetSystemId);
        return (sourceSystem?.name.toLowerCase().includes(searchTerm.toLowerCase()) || false) ||
               (targetSystem?.name.toLowerCase().includes(searchTerm.toLowerCase()) || false);
      }
      return true;
    });

  // Filter agents based on search
  const filteredAgents = agents
    .filter((agent) => {
      if (searchTerm) {
        return agent.name.toLowerCase().includes(searchTerm.toLowerCase()) ||
               agent.capabilities.some(cap => cap.toLowerCase().includes(searchTerm.toLowerCase()));
      }
      return true;
    });

  return (
    <Box sx={{ flexGrow: 1 }}>
      {/* Dashboard Header */}
      <Box sx={{ 
        display: 'flex', 
        flexDirection: { xs: 'column', md: 'row' }, 
        justifyContent: 'space-between', 
        alignItems: { xs: 'flex-start', md: 'center' }, 
        mb: 2,
        gap: 2
      }}>
        <Box>
          <Typography variant="h5" gutterBottom>
            Cross-System Configuration Dashboard
          </Typography>
          <Typography variant="subtitle1" color="text.secondary">
            Monitor and manage system endpoints and connections
          </Typography>
          {hasCrossSystemConnection && (
            <Chip 
              icon={<CheckIcon />} 
              label="AI-Orchestrator and Fast-Agent Connected" 
              color="success" 
              size="small" 
              sx={{ mt: 1 }}
            />
          )}
        </Box>
        <Box sx={{ 
          display: 'flex', 
          flexDirection: { xs: 'column', sm: 'row' }, 
          alignItems: 'center',
          gap: 2,
          width: { xs: '100%', md: 'auto' }
        }}>
          <TextField
            placeholder="Search systems & connections"
            size="small"
            value={searchTerm}
            onChange={handleSearchChange}
            InputProps={{
              startAdornment: (
                <InputAdornment position="start">
                  <SearchIcon />
                </InputAdornment>
              ),
            }}
            sx={{ width: { xs: '100%', sm: '250px' } }}
          />
          
          <FormControlLabel
            control={
              <Switch
                checked={showOnlyActive}
                onChange={(e) => setShowOnlyActive(e.target.checked)}
                color="primary"
                size="small"
              />
            }
            label="Show only active"
          />
        </Box>
      </Box>
      
      {/* Dashboard Tabs */}
      <Paper elevation={3} sx={{ mb: 3, borderRadius: 2, overflow: 'hidden' }}>
        <Box sx={{ 
          borderBottom: 1, 
          borderColor: 'divider', 
          bgcolor: theme.palette.mode === 'dark' ? 'rgba(255,255,255,0.05)' : 'rgba(0,0,0,0.02)'
        }}>
          <Tabs 
            value={dashboardTab} 
            onChange={handleDashboardTabChange} 
            aria-label="dashboard tabs"
            variant="scrollable"
            scrollButtons="auto"
          >
            <Tab 
              label="Overview" 
              icon={<DashboardIcon />} 
              iconPosition="start" 
              {...a11yProps(0)} 
            />
            <Tab 
              label="Health Status" 
              icon={<HealthIcon />} 
              iconPosition="start" 
              {...a11yProps(1)} 
            />
            <Tab 
              label="Data Flow" 
              icon={<CompareArrowsIcon />} 
              iconPosition="start" 
              {...a11yProps(2)} 
            />
            <Tab 
              label="Performance" 
              icon={<SpeedIcon />} 
              iconPosition="start" 
              {...a11yProps(3)} 
            />
            <Tab 
              label="Agents" 
              icon={<PsychologyIcon />} 
              iconPosition="start" 
              {...a11yProps(4)} 
            />
          </Tabs>
        </Box>

        {/* Overview Tab */}
        <TabPanel value={dashboardTab} index={0}>
          <Grid container spacing={3}>
            {/* System Overview */}
            <Grid item xs={12}>
              <Paper
                elevation={2}
                sx={{
                  p: 3,
                  borderRadius: 2,
                  border: `1px solid ${theme.palette.divider}`,
                }}
              >
                <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 3 }}>
                  <Typography variant="h6" component="h2">
                    System Overview
                  </Typography>
                  <Box>
                    <Button
                      variant="contained"
                      startIcon={<AddIcon />}
                      onClick={onAddSystem}
                      size="small"
                      sx={{ mr: 1 }}
                    >
                      Add System
                    </Button>
                    <Button
                      variant="contained"
                      startIcon={<SyncAltIcon />}
                      onClick={onAddConnection}
                      size="small"
                      disabled={systems.length < 2}
                    >
                      Add Connection
                    </Button>
                  </Box>
                </Box>
                
                <Grid container spacing={2}>
                  <Grid item xs={12} sm={6} md={3}>
                    <Card variant="outlined" sx={{ borderRadius: 2 }}>
                      <CardContent sx={{ textAlign: 'center' }}>
                        <Avatar sx={{ bgcolor: theme.palette.primary.main, mx: 'auto', mb: 1 }}>
                          <StorageIcon />
                        </Avatar>
                        <Typography variant="h4" component="div" sx={{ fontWeight: 'bold' }}>
                          {systems.length}
                        </Typography>
                        <Typography color="text.secondary">
                          Total Systems
                        </Typography>
                      </CardContent>
                    </Card>
                  </Grid>
                  
                  <Grid item xs={12} sm={6} md={3}>
                    <Card variant="outlined" sx={{ borderRadius: 2 }}>
                      <CardContent sx={{ textAlign: 'center' }}>
                        <Avatar sx={{ bgcolor: theme.palette.success.main, mx: 'auto', mb: 1 }}>
                          <CheckIcon />
                        </Avatar>
                        <Typography variant="h4" component="div" sx={{ fontWeight: 'bold' }}>
                          {systems.filter(s => s.enabled).length}
                        </Typography>
                        <Typography color="text.secondary">
                          Enabled Systems
                        </Typography>
                      </CardContent>
                    </Card>
                  </Grid>
                  
                  <Grid item xs={12} sm={6} md={3}>
                    <Card variant="outlined" sx={{ borderRadius: 2 }}>
                      <CardContent sx={{ textAlign: 'center' }}>
                        <Avatar sx={{ bgcolor: theme.palette.secondary.main, mx: 'auto', mb: 1 }}>
                          <SyncAltIcon />
                        </Avatar>
                        <Typography variant="h4" component="div" sx={{ fontWeight: 'bold' }}>
                          {connections.length}
                        </Typography>
                        <Typography color="text.secondary">
                          Total Connections
                        </Typography>
                      </CardContent>
                    </Card>
                  </Grid>
                  
                  <Grid item xs={12} sm={6} md={3}>
                    <Card variant="outlined" sx={{ borderRadius: 2 }}>
                      <CardContent sx={{ textAlign: 'center' }}>
                        <Avatar sx={{ bgcolor: theme.palette.warning.main, mx: 'auto', mb: 1 }}>
                          <TimelineIcon />
                        </Avatar>
                        <Typography variant="h4" component="div" sx={{ fontWeight: 'bold' }}>
                          {connections.length * 5}
                        </Typography>
                        <Typography color="text.secondary">
                          Sync Events
                        </Typography>
                      </CardContent>
                    </Card>
                  </Grid>
                </Grid>
                
                {/* Cross-System Integration Status */}
                {(hasOrchestrator && hasFastAgent) && (
                  <Box sx={{ mt: 3 }}>
                    <Divider sx={{ my: 2 }} />
                    <Typography variant="h6" gutterBottom>
                      Cross-System Integration Status
                    </Typography>
                    <Grid container spacing={2}>
                      <Grid item xs={12} sm={6}>
                        <Alert 
                          severity={hasCrossSystemConnection ? "success" : "warning"}
                          sx={{ mb: 2 }}
                          icon={hasCrossSystemConnection ? <CheckIcon /> : <WarningIcon />}
                        >
                          {hasCrossSystemConnection 
                            ? "AI-Orchestrator and Fast-Agent are successfully connected" 
                            : "AI-Orchestrator and Fast-Agent are not connected"}
                        </Alert>
                        
                        {hasCrossSystemConnection ? (
                          <Card variant="outlined" sx={{ borderRadius: 2 }}>
                            <CardContent>
                              <Typography variant="subtitle1" gutterBottom>
                                Integration Details
                              </Typography>
                              <Typography variant="body2">
                                <strong>Connection:</strong> {
                                  connections.find(c => {
                                    const sourceSystem = systems.find(s => s.id === c.sourceSystemId);
                                    const targetSystem = systems.find(s => s.id === c.targetSystemId);
                                    
                                    return (sourceSystem?.id === 'orchestrator' || sourceSystem?.name.toLowerCase().includes('orchestrator')) &&
                                      (targetSystem?.id === 'fast-agent' || targetSystem?.name.toLowerCase().includes('fast-agent')) ||
                                      (sourceSystem?.id === 'fast-agent' || sourceSystem?.name.toLowerCase().includes('fast-agent')) &&
                                      (targetSystem?.id === 'orchestrator' || targetSystem?.name.toLowerCase().includes('orchestrator'));
                                  })?.connectionType === 'one-way' ? 'One-way' : 'Two-way'
                                }
                              </Typography>
                              <Typography variant="body2">
                                <strong>Sync Interval:</strong> {
                                  connections.find(c => {
                                    const sourceSystem = systems.find(s => s.id === c.sourceSystemId);
                                    const targetSystem = systems.find(s => s.id === c.targetSystemId);
                                    
                                    return (sourceSystem?.id === 'orchestrator' || sourceSystem?.name.toLowerCase().includes('orchestrator')) &&
                                      (targetSystem?.id === 'fast-agent' || targetSystem?.name.toLowerCase().includes('fast-agent')) ||
                                      (sourceSystem?.id === 'fast-agent' || sourceSystem?.name.toLowerCase().includes('fast-agent')) &&
                                      (targetSystem?.id === 'orchestrator' || targetSystem?.name.toLowerCase().includes('orchestrator'));
                                  })?.syncInterval
                                } minutes
                              </Typography>
                              <Typography variant="body2">
                                <strong>Data Mappings:</strong> {
                                  connections.find(c => {
                                    const sourceSystem = systems.
