import React, { useEffect } from 'react';
import { useDispatch, useSelector } from 'react-redux';
import {
  Box,
  Grid,
  Paper,
  Typography,
  Card,
  CardContent,
  CardHeader,
  Divider,
  List,
  ListItem,
  ListItemText,
  ListItemAvatar,
  Avatar,
  Chip,
  CircularProgress,
  LinearProgress,
  IconButton,
  Tooltip,
  Button,
  useTheme,
} from '@mui/material';
import DaggerDashboard from '../components/dashboard/DaggerDashboard';
import {
  Refresh as RefreshIcon,
  Error as ErrorIcon,
  CheckCircle as CheckCircleIcon,
  Warning as WarningIcon,
  Info as InfoIcon,
  Memory as MemoryIcon,
  Speed as SpeedIcon,
  Storage as StorageIcon,
  People as PeopleIcon,
  Assignment as AssignmentIcon,
  SyncAlt as SyncAltIcon,
  Settings as SettingsIcon,
} from '@mui/icons-material';
import { Link } from 'react-router-dom';
import { RootState } from '../store';
import CrossSystemConfiguration from '../components/configuration/CrossSystemConfiguration';
import ProgressTracker from '../components/progress/ProgressTracker';
import { Line, Bar, Pie, Doughnut } from 'react-chartjs-2';
import {
  Chart as ChartJS,
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  BarElement,
  ArcElement,
  Title,
  Tooltip as ChartTooltip,
  Legend,
  Filler,
} from 'chart.js';
import { Agent, AgentStatus, AgentFramework } from '../types/agent';
import { Task } from '../store/slices/tasksSlice';
import { Message } from '../store/slices/communicationSlice';

// Register ChartJS components
ChartJS.register(
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  BarElement,
  ArcElement,
  Title,
  ChartTooltip,
  Legend,
  Filler
);

const Dashboard: React.FC = () => {
  const dispatch = useDispatch();
  const theme = useTheme();
  
  // Get data from Redux store
  const { agents, isLoading: agentsLoading } = useSelector((state: RootState) => state.agents);
  const { tasks, isLoading: tasksLoading } = useSelector((state: RootState) => state.tasks);
  const { system: metrics, timeSeriesData, isLoading: metricsLoading } = useSelector((state: RootState) => state.metrics);
  const { messages, isLoading: messagesLoading } = useSelector((state: RootState) => state.communication);
  const { dashboardLayout, activeProjectId } = useSelector((state: RootState) => state.ui);

  // Fetch data on component mount
  useEffect(() => {
    // In a real application, we would dispatch actions to fetch data
    // dispatch(fetchAgents());
    // dispatch(fetchTasks());
    // dispatch(fetchMetrics());
    // dispatch(fetchMessages());
  }, [dispatch]);

  // Helper function to get status color
  const getStatusColor = (status: AgentStatus) => {
    switch (status) {
      case AgentStatus.IDLE:
        return theme.palette.success.main;
      case AgentStatus.OFFLINE:
        return theme.palette.error.main;
      case AgentStatus.BUSY:
        return theme.palette.warning.main;
      case AgentStatus.ERROR:
        return theme.palette.error.main;
      default:
        return theme.palette.info.main;
    }
  };

  // Helper function to get task status color
  const getTaskStatusColor = (status: Task['status']) => {
    switch (status) {
      case 'completed':
        return theme.palette.success.main;
      case 'failed':
        return theme.palette.error.main;
      case 'in_progress':
        return theme.palette.warning.main;
      case 'created':
      case 'assigned':
      default:
        return theme.palette.info.main;
    }
  };

  // Helper function to get message type icon
  const getMessageTypeIcon = (type: Message['messageType']) => {
    switch (type) {
      case 'error':
        return <ErrorIcon color="error" />;
      case 'task_response':
        return <CheckCircleIcon color="success" />;
      case 'task_request':
        return <AssignmentIcon color="primary" />;
      case 'status_update':
        return <InfoIcon color="info" />;
      case 'broadcast':
        return <WarningIcon color="warning" />;
      default:
        return <InfoIcon color="info" />;
    }
  };

  // Prepare chart data for CPU usage
  const cpuUsageChartData = {
    labels: timeSeriesData.cpuUsage.map((d: any) => new Date(d.timestamp).toLocaleTimeString()),
    datasets: [
      {
        label: 'CPU Usage (%)',
        data: timeSeriesData.cpuUsage.map((d: any) => d.value),
        borderColor: theme.palette.primary.main,
        backgroundColor: `${theme.palette.primary.main}33`,
        fill: true,
        tension: 0.4,
      },
    ],
  };

  // Prepare chart data for memory usage
  const memoryUsageChartData = {
    labels: timeSeriesData.memoryUsage.map((d: any) => new Date(d.timestamp).toLocaleTimeString()),
    datasets: [
      {
        label: 'Memory Usage (MB)',
        data: timeSeriesData.memoryUsage.map((d: any) => d.value),
        borderColor: theme.palette.secondary.main,
        backgroundColor: `${theme.palette.secondary.main}33`,
        fill: true,
        tension: 0.4,
      },
    ],
  };

  // Prepare chart data for active agents
  const activeAgentsChartData = {
    labels: timeSeriesData.activeAgents.map((d: any) => new Date(d.timestamp).toLocaleTimeString()),
    datasets: [
      {
        label: 'Active Agents',
        data: timeSeriesData.activeAgents.map((d: any) => d.value),
        borderColor: theme.palette.success.main,
        backgroundColor: `${theme.palette.success.main}33`,
        fill: true,
        tension: 0.4,
      },
    ],
  };

  // Prepare chart data for active tasks
  const activeTasksChartData = {
    labels: timeSeriesData.activeTasks.map((d: any) => new Date(d.timestamp).toLocaleTimeString()),
    datasets: [
      {
        label: 'Active Tasks',
        data: timeSeriesData.activeTasks.map((d: any) => d.value),
        borderColor: theme.palette.warning.main,
        backgroundColor: `${theme.palette.warning.main}33`,
        fill: true,
        tension: 0.4,
      },
    ],
  };

  // Prepare chart data for task completion rate
  const taskCompletionRateChartData = {
    labels: timeSeriesData.taskCompletionRate.map((d: any) => new Date(d.timestamp).toLocaleTimeString()),
    datasets: [
      {
        label: 'Task Completion Rate',
        data: timeSeriesData.taskCompletionRate.map((d: any) => d.value),
        borderColor: theme.palette.info.main,
        backgroundColor: `${theme.palette.info.main}33`,
        fill: true,
        tension: 0.4,
      },
    ],
  };

  // Prepare chart data for task status distribution
  const taskStatusDistributionChartData = {
    labels: ['Completed', 'Failed', 'In Progress', 'Created/Assigned'],
    datasets: [
      {
        data: [
          metrics.completedTasks,
          metrics.failedTasks,
          metrics.activeTasks,
          tasks.filter((t: any) => t.status === 'created' || t.status === 'assigned').length,
        ],
        backgroundColor: [
          theme.palette.success.main,
          theme.palette.error.main,
          theme.palette.warning.main,
          theme.palette.info.main,
        ],
        borderColor: [
          theme.palette.success.dark,
          theme.palette.error.dark,
          theme.palette.warning.dark,
          theme.palette.info.dark,
        ],
        borderWidth: 1,
      },
    ],
  };

  // Prepare chart data for agent type distribution
  const agentTypeDistributionChartData = {
    labels: ['AI-Orchestrator', 'Fast-Agent'],
    datasets: [
      {
        data: [
          agents.filter((a: any) => a.framework === AgentFramework.AI_ORCHESTRATOR).length,
          agents.filter((a: any) => a.framework === AgentFramework.FAST_AGENT).length,
        ],
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

  // Chart options
  const lineChartOptions = {
    responsive: true,
    maintainAspectRatio: false,
    plugins: {
      legend: {
        position: 'top' as const,
      },
    },
    scales: {
      y: {
        beginAtZero: true,
      },
    },
  };

  const pieChartOptions = {
    responsive: true,
    maintainAspectRatio: false,
    plugins: {
      legend: {
        position: 'right' as const,
      },
    },
  };

  // Get widget by ID
  const getWidgetById = (id: string) => {
    return dashboardLayout.find((widget: any) => widget.id === id);
  };

  // Check if widget is visible
  const isWidgetVisible = (id: string) => {
    const widget = getWidgetById(id);
    return widget ? widget.visible : true;
  };

  return (
    <Box sx={{ flexGrow: 1 }}>
      <Typography variant="h4" gutterBottom>
        Unified Dashboard
      </Typography>
      <Typography variant="subtitle1" color="text.secondary" paragraph>
        Monitor and manage AI-Orchestrator and Fast-Agent integration
      </Typography>

      <Grid container spacing={3}>
        {/* System Overview */}
        {isWidgetVisible('system-overview') && (
          <Grid item xs={12}>
            <Paper
              elevation={2}
              sx={{
                p: 2,
                display: 'flex',
                flexDirection: 'column',
              }}
            >
              <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 2 }}>
                <Typography variant="h6" component="h2">
                  System Overview
                </Typography>
                <Tooltip title="Refresh">
                  <IconButton size="small">
                    <RefreshIcon />
                  </IconButton>
                </Tooltip>
              </Box>
              
              {metricsLoading ? (
                <CircularProgress sx={{ alignSelf: 'center', my: 2 }} />
              ) : (
                <Grid container spacing={2}>
                  <Grid item xs={12} sm={6} md={3}>
                    <Card variant="outlined">
                      <CardContent sx={{ textAlign: 'center' }}>
                        <Avatar sx={{ bgcolor: theme.palette.primary.main, mx: 'auto', mb: 1 }}>
                          <MemoryIcon />
                        </Avatar>
                        <Typography variant="h5" component="div">
                          {metrics.cpuUsage}%
                        </Typography>
                        <Typography color="text.secondary">
                          CPU Usage
                        </Typography>
                      </CardContent>
                    </Card>
                  </Grid>
                  
                  <Grid item xs={12} sm={6} md={3}>
                    <Card variant="outlined">
                      <CardContent sx={{ textAlign: 'center' }}>
                        <Avatar sx={{ bgcolor: theme.palette.secondary.main, mx: 'auto', mb: 1 }}>
                          <StorageIcon />
                        </Avatar>
                        <Typography variant="h5" component="div">
                          {metrics.memoryUsage} MB
                        </Typography>
                        <Typography color="text.secondary">
                          Memory Usage
                        </Typography>
                      </CardContent>
                    </Card>
                  </Grid>
                  
                  <Grid item xs={12} sm={6} md={3}>
                    <Card variant="outlined">
                      <CardContent sx={{ textAlign: 'center' }}>
                        <Avatar sx={{ bgcolor: theme.palette.success.main, mx: 'auto', mb: 1 }}>
                          <PeopleIcon />
                        </Avatar>
                        <Typography variant="h5" component="div">
                          {metrics.activeAgents}/{metrics.totalAgents}
                        </Typography>
                        <Typography color="text.secondary">
                          Active/Total Agents
                        </Typography>
                      </CardContent>
                    </Card>
                  </Grid>
                  
                  <Grid item xs={12} sm={6} md={3}>
                    <Card variant="outlined">
                      <CardContent sx={{ textAlign: 'center' }}>
                        <Avatar sx={{ bgcolor: theme.palette.warning.main, mx: 'auto', mb: 1 }}>
                          <AssignmentIcon />
                        </Avatar>
                        <Typography variant="h5" component="div">
                          {metrics.activeTasks}
                        </Typography>
                        <Typography color="text.secondary">
                          Active Tasks
                        </Typography>
                      </CardContent>
                    </Card>
                  </Grid>
                </Grid>
              )}
            </Paper>
          </Grid>
        )}

        {/* Agent Status */}
        {isWidgetVisible('agent-status') && (
          <Grid item xs={12} md={6}>
            <Paper
              elevation={2}
              sx={{
                p: 2,
                display: 'flex',
                flexDirection: 'column',
                height: 400,
              }}
            >
              <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 2 }}>
                <Typography variant="h6" component="h2">
                  Agent Status
                </Typography>
                <Tooltip title="Refresh">
                  <IconButton size="small">
                    <RefreshIcon />
                  </IconButton>
                </Tooltip>
              </Box>
              
              {agentsLoading ? (
                <CircularProgress sx={{ alignSelf: 'center', my: 2 }} />
              ) : (
                <Box sx={{ display: 'flex', flexDirection: 'column', height: '100%' }}>
                  <Box sx={{ display: 'flex', justifyContent: 'space-between', mb: 1 }}>
                    <Typography variant="subtitle2" color="text.secondary">
                      Agent Distribution
                    </Typography>
                  </Box>
                  
                  <Box sx={{ height: 200, mb: 2 }}>
                    <Doughnut data={agentTypeDistributionChartData} options={pieChartOptions} />
                  </Box>
                  
                  <Divider sx={{ my: 1 }} />
                  
                  <Typography variant="subtitle2" color="text.secondary" sx={{ mb: 1 }}>
                    Recent Agents
                  </Typography>
                  
                  <List sx={{ overflow: 'auto', flexGrow: 1 }}>
                    {agents.slice(0, 5).map((agent: any) => (
                      <ListItem key={agent.id} divider>
                        <ListItemAvatar>
                          <Avatar sx={{ bgcolor: getStatusColor(agent.status) }}>
                            <PeopleIcon />
                          </Avatar>
                        </ListItemAvatar>
                        <ListItemText
                          primary={agent.name}
                          secondary={
                            <>
                              <Typography component="span" variant="body2" color="text.primary">
                                {agent.framework}
                              </Typography>
                              {` — Load: ${agent.currentLoad}`}
                            </>
                          }
                        />
                        <Chip
                          label={agent.status}
                          size="small"
                          sx={{
                            bgcolor: getStatusColor(agent.status),
                            color: 'white',
                          }}
                        />
                      </ListItem>
                    ))}
                  </List>
                </Box>
              )}
            </Paper>
          </Grid>
        )}

        {/* Task Status */}
        {isWidgetVisible('task-status') && (
          <Grid item xs={12} md={6}>
            <Paper
              elevation={2}
              sx={{
                p: 2,
                display: 'flex',
                flexDirection: 'column',
                height: 400,
              }}
            >
              <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 2 }}>
                <Typography variant="h6" component="h2">
                  Task Status
                </Typography>
                <Tooltip title="Refresh">
                  <IconButton size="small">
                    <RefreshIcon />
                  </IconButton>
                </Tooltip>
              </Box>
              
              {tasksLoading ? (
                <CircularProgress sx={{ alignSelf: 'center', my: 2 }} />
              ) : (
                <Box sx={{ display: 'flex', flexDirection: 'column', height: '100%' }}>
                  <Box sx={{ display: 'flex', justifyContent: 'space-between', mb: 1 }}>
                    <Typography variant="subtitle2" color="text.secondary">
                      Task Distribution
                    </Typography>
                  </Box>
                  
                  <Box sx={{ height: 200, mb: 2 }}>
                    <Pie data={taskStatusDistributionChartData} options={pieChartOptions} />
                  </Box>
                  
                  <Divider sx={{ my: 1 }} />
                  
                  <Typography variant="subtitle2" color="text.secondary" sx={{ mb: 1 }}>
                    Recent Tasks
                  </Typography>
                  
                  <List sx={{ overflow: 'auto', flexGrow: 1 }}>
                    {tasks.slice(0, 5).map((task: any) => (
                      <ListItem key={task.id} divider>
                        <ListItemAvatar>
                          <Avatar sx={{ bgcolor: getTaskStatusColor(task.status) }}>
                            <AssignmentIcon />
                          </Avatar>
                        </ListItemAvatar>
                        <ListItemText
                          primary={task.name}
                          secondary={
                            <>
                              <Typography component="span" variant="body2" color="text.primary">
                                {task.type}
                              </Typography>
                              {task.progress < 100 && task.status === 'in_progress' && (
                                <LinearProgress
                                  variant="determinate"
                                  value={task.progress}
                                  sx={{ mt: 1 }}
                                />
                              )}
                            </>
                          }
                        />
                        <Chip
                          label={task.status.replace('_', ' ')}
                          size="small"
                          sx={{
                            bgcolor: getTaskStatusColor(task.status),
                            color: 'white',
                          }}
                        />
                      </ListItem>
                    ))}
                  </List>
                </Box>
              )}
            </Paper>
          </Grid>
        )}

        {/* Performance Metrics */}
        {isWidgetVisible('performance-metrics') && (
          <Grid item xs={12}>
            <Paper
              elevation={2}
              sx={{
                p: 2,
                display: 'flex',
                flexDirection: 'column',
                height: 400,
              }}
            >
              <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 2 }}>
                <Typography variant="h6" component="h2">
                  Performance Metrics
                </Typography>
                <Tooltip title="Refresh">
                  <IconButton size="small">
                    <RefreshIcon />
                  </IconButton>
                </Tooltip>
              </Box>
              
              {metricsLoading ? (
                <CircularProgress sx={{ alignSelf: 'center', my: 2 }} />
              ) : (
                <Grid container spacing={2} sx={{ flexGrow: 1 }}>
                  <Grid item xs={12} md={6}>
                    <Typography variant="subtitle2" color="text.secondary" align="center">
                      CPU & Memory Usage
                    </Typography>
                    <Box sx={{ height: 150 }}>
                      <Line data={cpuUsageChartData} options={lineChartOptions} />
                    </Box>
                    <Box sx={{ height: 150, mt: 2 }}>
                      <Line data={memoryUsageChartData} options={lineChartOptions} />
                    </Box>
                  </Grid>
                  
                  <Grid item xs={12} md={6}>
                    <Typography variant="subtitle2" color="text.secondary" align="center">
                      Agent & Task Activity
                    </Typography>
                    <Box sx={{ height: 150 }}>
                      <Line data={activeAgentsChartData} options={lineChartOptions} />
                    </Box>
                    <Box sx={{ height: 150, mt: 2 }}>
                      <Line data={activeTasksChartData} options={lineChartOptions} />
                    </Box>
                  </Grid>
                </Grid>
              )}
            </Paper>
          </Grid>
        )}

        {/* Recent Messages */}
        {isWidgetVisible('recent-messages') && (
          <Grid item xs={12}>
            <Paper
              elevation={2}
              sx={{
                p: 2,
                display: 'flex',
                flexDirection: 'column',
                height: 300,
              }}
            >
              <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 2 }}>
                <Typography variant="h6" component="h2">
                  Recent Messages
                </Typography>
                <Tooltip title="Refresh">
                  <IconButton size="small">
                    <RefreshIcon />
                  </IconButton>
                </Tooltip>
              </Box>
              
              {messagesLoading ? (
                <CircularProgress sx={{ alignSelf: 'center', my: 2 }} />
              ) : (
                <List sx={{ overflow: 'auto', flexGrow: 1 }}>
                  {messages.slice(0, 10).map((message: any) => (
                    <ListItem key={message.id} divider>
                      <ListItemAvatar>
                        <Avatar>
                          {getMessageTypeIcon(message.messageType)}
                        </Avatar>
                      </ListItemAvatar>
                      <ListItemText
                        primary={
                          <Typography variant="body1">
                            {message.messageType === 'direct' ? 'Direct Message' : 
                             message.messageType === 'broadcast' ? 'Broadcast' :
                             message.messageType === 'task_request' ? 'Task Request' :
                             message.messageType === 'task_response' ? 'Task Response' :
                             message.messageType === 'status_update' ? 'Status Update' :
                             message.messageType === 'error' ? 'Error' : 'System Message'}
                          </Typography>
                        }
                        secondary={
                          <>
                            <Typography component="span" variant="body2" color="text.primary">
                              From: {message.senderId} {message.recipientId ? `To: ${message.recipientId}` : '(Broadcast)'}
                            </Typography>
                            <Typography variant="body2" color="text.secondary">
                              {new Date(message.timestamp).toLocaleString()}
                            </Typography>
                          </>
                        }
                      />
                      <Chip
                        label={message.priority}
                        size="small"
                        color={
                          message.priority === 'high' ? 'error' :
                          message.priority === 'medium' ? 'warning' : 'info'
                        }
                      />
                    </ListItem>
                  ))}
                </List>
              )}
            </Paper>
          </Grid>
        )}

        {/* Project Progress Tracker */}
        {isWidgetVisible('project-progress-tracker') && activeProjectId && (
          <Grid item xs={12}>
            <Paper
              elevation={2}
              sx={{
                display: 'flex',
                flexDirection: 'column',
                height: 600,
              }}
            >
              <ProgressTracker 
                projectId={activeProjectId} 
                mode="embedded" 
                showTitle={true}
                height={600}
              />
            </Paper>
          </Grid>
        )}

        {/* Dagger Workflow Integration Dashboard */}
        {isWidgetVisible('dagger-workflow-integration') && (
          <Grid item xs={12}>
            <Paper
              elevation={2}
              sx={{
                display: 'flex',
                flexDirection: 'column',
                height: 600,
              }}
            >
              <DaggerDashboard />
            </Paper>
          </Grid>
        )}

        {/* Cross-System Configuration */}
        {isWidgetVisible('cross-system-config') && (
          <Grid item xs={12}>
            <Paper
              elevation={2}
              sx={{
                p: 2,
                display: 'flex',
                flexDirection: 'column',
              }}
            >
              <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 2 }}>
                <Typography variant="h6" component="h2">
                  Cross-System Configuration
                </Typography>
                <Box>
                  <Tooltip title="Refresh">
                    <IconButton size="small" sx={{ mr: 1 }}>
                      <RefreshIcon />
                    </IconButton>
                  </Tooltip>
                  <Button
                    component={Link}
                    to="/settings"
                    variant="outlined"
                    size="small"
                    startIcon={<SettingsIcon />}
                  >
                    Full Configuration
                  </Button>
                </Box>
              </Box>
              
              <CrossSystemConfiguration />
            </Paper>
          </Grid>
        )}
      </Grid>
    </Box>
  );
};

export default Dashboard;
