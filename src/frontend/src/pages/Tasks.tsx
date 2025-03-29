import React, { useEffect } from 'react';
import { useDispatch, useSelector } from 'react-redux';
import {
  Box,
  Typography,
  Paper,
  Grid,
  Card,
  CardContent,
  Avatar,
  Chip,
  List,
  ListItem,
  ListItemText,
  ListItemAvatar,
  Divider,
  Button,
  IconButton,
  Tooltip,
  CircularProgress,
  LinearProgress,
  useTheme,
  Tab,
  Tabs,
} from '@mui/material';
import {
  Refresh as RefreshIcon,
  Add as AddIcon,
  FilterList as FilterListIcon,
  Search as SearchIcon,
  Assignment as AssignmentIcon,
  CheckCircle as CheckCircleIcon,
  Error as ErrorIcon,
  Pending as PendingIcon,
  PlayArrow as PlayArrowIcon,
} from '@mui/icons-material';
import { RootState } from '../store';
import { Task } from '../store/slices/tasksSlice';

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
      id={`task-tabpanel-${index}`}
      aria-labelledby={`task-tab-${index}`}
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
    id: `task-tab-${index}`,
    'aria-controls': `task-tabpanel-${index}`,
  };
}

const Tasks: React.FC = () => {
  const dispatch = useDispatch();
  const theme = useTheme();
  const [tabValue, setTabValue] = React.useState(0);
  
  // Get data from Redux store
  const { tasks, isLoading, filters } = useSelector((state: RootState) => state.tasks);

  // Fetch data on component mount
  useEffect(() => {
    // In a real application, we would dispatch an action to fetch tasks
    // dispatch(fetchTasks());
  }, [dispatch]);

  // Handle tab change
  const handleTabChange = (event: React.SyntheticEvent, newValue: number) => {
    setTabValue(newValue);
  };

  // Helper function to get status color
  const getStatusColor = (status: Task['status']) => {
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

  // Helper function to get status icon
  const getStatusIcon = (status: Task['status']) => {
    switch (status) {
      case 'completed':
        return <CheckCircleIcon />;
      case 'failed':
        return <ErrorIcon />;
      case 'in_progress':
        return <PlayArrowIcon />;
      case 'created':
      case 'assigned':
      default:
        return <PendingIcon />;
    }
  };

  // Filter tasks based on status
  const getFilteredTasks = (status: Task['status'] | 'all') => {
    if (status === 'all') {
      return tasks;
    }
    return tasks.filter(task => task.status === status);
  };

  return (
    <Box sx={{ flexGrow: 1 }}>
      <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 3 }}>
        <Typography variant="h4" component="h1">
          Tasks
        </Typography>
        <Box>
          <Tooltip title="Filter">
            <IconButton>
              <FilterListIcon />
            </IconButton>
          </Tooltip>
          <Tooltip title="Search">
            <IconButton>
              <SearchIcon />
            </IconButton>
          </Tooltip>
          <Tooltip title="Refresh">
            <IconButton>
              <RefreshIcon />
            </IconButton>
          </Tooltip>
          <Button
            variant="contained"
            startIcon={<AddIcon />}
            sx={{ ml: 2 }}
          >
            Create Task
          </Button>
        </Box>
      </Box>

      {isLoading ? (
        <CircularProgress sx={{ display: 'block', mx: 'auto', my: 4 }} />
      ) : (
        <Grid container spacing={3}>
          {/* Task Summary */}
          <Grid item xs={12}>
            <Paper sx={{ p: 2 }}>
              <Typography variant="h6" gutterBottom>
                Task Summary
              </Typography>
              <Grid container spacing={2}>
                <Grid item xs={12} sm={6} md={3}>
                  <Card variant="outlined">
                    <CardContent>
                      <Typography variant="h5" component="div">
                        {tasks.length}
                      </Typography>
                      <Typography color="text.secondary">
                        Total Tasks
                      </Typography>
                    </CardContent>
                  </Card>
                </Grid>
                <Grid item xs={12} sm={6} md={3}>
                  <Card variant="outlined">
                    <CardContent>
                      <Typography variant="h5" component="div">
                        {tasks.filter(t => t.status === 'in_progress').length}
                      </Typography>
                      <Typography color="text.secondary">
                        Active Tasks
                      </Typography>
                    </CardContent>
                  </Card>
                </Grid>
                <Grid item xs={12} sm={6} md={3}>
                  <Card variant="outlined">
                    <CardContent>
                      <Typography variant="h5" component="div">
                        {tasks.filter(t => t.status === 'completed').length}
                      </Typography>
                      <Typography color="text.secondary">
                        Completed Tasks
                      </Typography>
                    </CardContent>
                  </Card>
                </Grid>
                <Grid item xs={12} sm={6} md={3}>
                  <Card variant="outlined">
                    <CardContent>
                      <Typography variant="h5" component="div">
                        {tasks.filter(t => t.status === 'failed').length}
                      </Typography>
                      <Typography color="text.secondary">
                        Failed Tasks
                      </Typography>
                    </CardContent>
                  </Card>
                </Grid>
              </Grid>
            </Paper>
          </Grid>

          {/* Task List */}
          <Grid item xs={12}>
            <Paper sx={{ width: '100%' }}>
              <Box sx={{ borderBottom: 1, borderColor: 'divider' }}>
                <Tabs value={tabValue} onChange={handleTabChange} aria-label="task tabs">
                  <Tab label="All Tasks" {...a11yProps(0)} />
                  <Tab label="In Progress" {...a11yProps(1)} />
                  <Tab label="Completed" {...a11yProps(2)} />
                  <Tab label="Failed" {...a11yProps(3)} />
                </Tabs>
              </Box>
              <TabPanel value={tabValue} index={0}>
                <TaskList tasks={getFilteredTasks('all')} getStatusColor={getStatusColor} getStatusIcon={getStatusIcon} />
              </TabPanel>
              <TabPanel value={tabValue} index={1}>
                <TaskList tasks={getFilteredTasks('in_progress')} getStatusColor={getStatusColor} getStatusIcon={getStatusIcon} />
              </TabPanel>
              <TabPanel value={tabValue} index={2}>
                <TaskList tasks={getFilteredTasks('completed')} getStatusColor={getStatusColor} getStatusIcon={getStatusIcon} />
              </TabPanel>
              <TabPanel value={tabValue} index={3}>
                <TaskList tasks={getFilteredTasks('failed')} getStatusColor={getStatusColor} getStatusIcon={getStatusIcon} />
              </TabPanel>
            </Paper>
          </Grid>
        </Grid>
      )}
    </Box>
  );
};

interface TaskListProps {
  tasks: Task[];
  getStatusColor: (status: Task['status']) => string;
  getStatusIcon: (status: Task['status']) => JSX.Element;
}

const TaskList: React.FC<TaskListProps> = ({ tasks, getStatusColor, getStatusIcon }) => {
  return (
    <List>
      {tasks.length > 0 ? (
        tasks.map((task) => (
          <React.Fragment key={task.id}>
            <ListItem
              alignItems="flex-start"
              secondaryAction={
                <Chip
                  label={task.status.replace('_', ' ')}
                  size="small"
                  sx={{
                    bgcolor: getStatusColor(task.status),
                    color: 'white',
                  }}
                />
              }
            >
              <ListItemAvatar>
                <Avatar sx={{ bgcolor: getStatusColor(task.status) }}>
                  {getStatusIcon(task.status)}
                </Avatar>
              </ListItemAvatar>
              <ListItemText
                primary={
                  <Typography variant="subtitle1">
                    {task.name}
                  </Typography>
                }
                secondary={
                  <>
                    <Typography component="span" variant="body2" color="text.primary">
                      {task.type}
                    </Typography>
                    <Typography variant="body2" component="div">
                      {task.description}
                    </Typography>
                    {task.agentId && (
                      <Typography variant="body2" color="text.secondary">
                        Assigned to: {task.agentId}
                      </Typography>
                    )}
                    {task.progress < 100 && task.status === 'in_progress' && (
                      <Box sx={{ display: 'flex', alignItems: 'center', mt: 1 }}>
                        <Typography variant="body2" color="text.secondary" sx={{ mr: 2 }}>
                          Progress: {task.progress}%
                        </Typography>
                        <LinearProgress
                          variant="determinate"
                          value={task.progress}
                          sx={{ flexGrow: 1, height: 8, borderRadius: 4 }}
                        />
                      </Box>
                    )}
                    <Box sx={{ mt: 1 }}>
                      {task.requiredCapabilities.map((capability) => (
                        <Chip
                          key={capability}
                          label={capability}
                          size="small"
                          sx={{ mr: 0.5, mb: 0.5 }}
                        />
                      ))}
                    </Box>
                  </>
                }
              />
            </ListItem>
            <Divider variant="inset" component="li" />
          </React.Fragment>
        ))
      ) : (
        <ListItem>
          <ListItemText
            primary="No tasks found"
            secondary="Create a task to get started"
          />
        </ListItem>
      )}
    </List>
  );
};

export default Tasks;
