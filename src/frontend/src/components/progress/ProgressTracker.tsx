import React, { useState, useEffect, useCallback } from 'react';
import {
  Box,
  Paper,
  Typography,
  Tabs,
  Tab,
  List,
  ListItem,
  ListItemText,
  ListItemIcon,
  ListItemSecondaryAction,
  IconButton,
  Chip,
  LinearProgress,
  CircularProgress,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  Button,
  TextField,
  MenuItem,
  Select,
  FormControl,
  InputLabel,
  Grid,
  Tooltip,
  Divider,
  Card,
  CardContent,
  CardHeader,
  CardActions,
  Collapse,
  useTheme,
  alpha,
} from '@mui/material';
import {
  Assignment as AssignmentIcon,
  CheckCircle as CheckCircleIcon,
  Error as ErrorIcon,
  Warning as WarningIcon,
  Info as InfoIcon,
  Add as AddIcon,
  Edit as EditIcon,
  Delete as DeleteIcon,
  ExpandMore as ExpandMoreIcon,
  ExpandLess as ExpandLessIcon,
  Refresh as RefreshIcon,
  Timeline as TimelineIcon,
  ViewList as ViewListIcon,
  ViewModule as ViewModuleIcon,
} from '@mui/icons-material';
import { useDispatch, useSelector } from 'react-redux';
import { RootState } from '../../store';
import { api } from '../../services/api';
import { ProjectProgressBar } from '../ProjectProgressBar';

// Define the API endpoints for task management
const taskApi = api.injectEndpoints({
  endpoints: (builder) => ({
    getProject: builder.query({
      query: (projectId) => `/tasks/projects/${projectId}`,
      providesTags: ['Project'],
    }),
    getProjectProgress: builder.query({
      query: (projectId) => `/tasks/projects/${projectId}/progress`,
      providesTags: ['ProjectProgress'],
    }),
    getPhases: builder.query({
      query: (projectId) => `/tasks/projects/${projectId}/phases`,
      providesTags: ['Phases'],
    }),
    getTasks: builder.query({
      query: ({ projectId, phaseId, status }) => {
        let url = `/tasks/projects/${projectId}/tasks`;
        const params = new URLSearchParams();
        if (phaseId) params.append('phase_id', phaseId);
        if (status) params.append('status', status);
        if (params.toString()) url += `?${params.toString()}`;
        return url;
      },
      providesTags: ['Tasks'],
    }),
    getTask: builder.query({
      query: (taskId) => `/tasks/tasks/${taskId}`,
      providesTags: (result, error, taskId) => [{ type: 'Task', id: taskId }],
    }),
    createTask: builder.mutation({
      query: (task) => ({
        url: '/tasks/tasks',
        method: 'POST',
        body: task,
      }),
      invalidatesTags: ['Tasks', 'ProjectProgress'],
    }),
    updateTask: builder.mutation({
      query: ({ taskId, task }) => ({
        url: `/tasks/tasks/${taskId}`,
        method: 'PUT',
        body: task,
      }),
      invalidatesTags: (result, error, { taskId }) => [
        { type: 'Task', id: taskId },
        'Tasks',
        'ProjectProgress',
      ],
    }),
    updateTaskStatus: builder.mutation({
      query: ({ taskId, status }) => ({
        url: `/tasks/tasks/${taskId}/status`,
        method: 'PUT',
        body: { status },
      }),
      invalidatesTags: (result, error, { taskId }) => [
        { type: 'Task', id: taskId },
        'Tasks',
        'ProjectProgress',
      ],
    }),
    updateTaskProgress: builder.mutation({
      query: ({ taskId, progress }) => ({
        url: `/tasks/tasks/${taskId}/progress`,
        method: 'PUT',
        body: { progress },
      }),
      invalidatesTags: (result, error, { taskId }) => [
        { type: 'Task', id: taskId },
        'Tasks',
        'ProjectProgress',
      ],
    }),
    deleteTask: builder.mutation({
      query: (taskId) => ({
        url: `/tasks/tasks/${taskId}`,
        method: 'DELETE',
      }),
      invalidatesTags: ['Tasks', 'ProjectProgress'],
    }),
    createPhase: builder.mutation({
      query: ({ projectId, phase }) => ({
        url: `/tasks/projects/${projectId}/phases`,
        method: 'POST',
        body: phase,
      }),
      invalidatesTags: ['Phases', 'Project'],
    }),
  }),
});

// Export hooks for usage in components
export const {
  useGetProjectQuery,
  useGetProjectProgressQuery,
  useGetPhasesQuery,
  useGetTasksQuery,
  useGetTaskQuery,
  useCreateTaskMutation,
  useUpdateTaskMutation,
  useUpdateTaskStatusMutation,
  useUpdateTaskProgressMutation,
  useDeleteTaskMutation,
  useCreatePhaseMutation,
} = taskApi;

// Define the component props
interface ProgressTrackerProps {
  projectId: string;
  mode?: 'embedded' | 'popup';
  showTitle?: boolean;
  height?: number;
}

// Task status type
type TaskStatus = 'planned' | 'in_progress' | 'completed' | 'failed' | 'blocked';

// Task priority type
type TaskPriority = 'low' | 'medium' | 'high' | 'critical';

// Task interface
interface Task {
  id: string;
  name: string;
  description: string;
  project_id: string;
  phase_id: string | null;
  parent_id: string | null;
  status: TaskStatus;
  priority: TaskPriority;
  progress: number;
  assignee_id: string | null;
  assignee_type: string | null;
  metadata: Record<string, any>;
  created_at: string;
  updated_at: string;
  started_at: string | null;
  completed_at: string | null;
  children: string[];
  status_history: Array<{
    status: string;
    timestamp: string;
    previous_status: string | null;
  }>;
  result: any | null;
  error: string | null;
}

// Phase interface
interface Phase {
  id: string;
  name: string;
  project_id: string;
  description: string;
  order: number;
  metadata: Record<string, any>;
  created_at: string;
  updated_at: string;
  tasks: string[];
}

// Project interface
interface Project {
  id: string;
  name: string;
  description: string;
  metadata: Record<string, any>;
  created_at: string;
  updated_at: string;
  phases: Record<string, Phase>;
  tasks: Record<string, Task>;
}

const ProgressTracker: React.FC<ProgressTrackerProps> = ({
  projectId,
  mode = 'embedded',
  showTitle = true,
  height = 600,
}) => {
  const theme = useTheme();
  const [selectedPhaseId, setSelectedPhaseId] = useState<string | null>(null);
  const [selectedTaskId, setSelectedTaskId] = useState<string | null>(null);
  const [viewMode, setViewMode] = useState<'list' | 'card'>('list');
  const [taskDialogOpen, setTaskDialogOpen] = useState(false);
  const [phaseDialogOpen, setPhaseDialogOpen] = useState(false);
  const [expandedTasks, setExpandedTasks] = useState<Record<string, boolean>>({});
  const [newTask, setNewTask] = useState<Partial<Task>>({
    name: '',
    description: '',
    status: 'planned',
    priority: 'medium',
    progress: 0,
  });
  const [newPhase, setNewPhase] = useState<Partial<Phase>>({
    name: '',
    description: '',
    order: 0,
  });

  // Get project data
  const { data: project, isLoading: projectLoading, error: projectError } = useGetProjectQuery(projectId);
  
  // Get phases
  const { data: phases, isLoading: phasesLoading } = useGetPhasesQuery(projectId);
  
  // Get tasks for the selected phase
  const { data: tasks, isLoading: tasksLoading } = useGetTasksQuery(
    { projectId, phaseId: selectedPhaseId || undefined },
    { skip: !projectId }
  );

  // Get project progress
  const { data: progress, isLoading: progressLoading } = useGetProjectProgressQuery(projectId);

  // Mutations
  const [createTask, { isLoading: isCreatingTask }] = useCreateTaskMutation();
  const [updateTask, { isLoading: isUpdatingTask }] = useUpdateTaskMutation();
  const [updateTaskStatus, { isLoading: isUpdatingTaskStatus }] = useUpdateTaskStatusMutation();
  const [updateTaskProgress, { isLoading: isUpdatingTaskProgress }] = useUpdateTaskProgressMutation();
  const [deleteTask, { isLoading: isDeletingTask }] = useDeleteTaskMutation();
  const [createPhase, { isLoading: isCreatingPhase }] = useCreatePhaseMutation();

  // Set the first phase as selected when phases are loaded
  useEffect(() => {
    if (phases && phases.length > 0 && !selectedPhaseId) {
      setSelectedPhaseId(phases[0].id);
    }
  }, [phases, selectedPhaseId]);

  // Handle task expansion toggle
  const handleTaskExpand = (taskId: string) => {
    setExpandedTasks((prev) => ({
      ...prev,
      [taskId]: !prev[taskId],
    }));
  };

  // Handle phase selection
  const handlePhaseChange = (event: React.SyntheticEvent, newValue: string) => {
    setSelectedPhaseId(newValue);
  };

  // Handle task selection
  const handleTaskSelect = (taskId: string) => {
    setSelectedTaskId(taskId);
  };

  // Handle view mode change
  const handleViewModeChange = (mode: 'list' | 'card') => {
    setViewMode(mode);
  };

  // Handle task dialog open
  const handleTaskDialogOpen = () => {
    setNewTask({
      name: '',
      description: '',
      status: 'planned',
      priority: 'medium',
      progress: 0,
      phase_id: selectedPhaseId,
      project_id: projectId,
    });
    setTaskDialogOpen(true);
  };

  // Handle task dialog close
  const handleTaskDialogClose = () => {
    setTaskDialogOpen(false);
  };

  // Handle phase dialog open
  const handlePhaseDialogOpen = () => {
    setNewPhase({
      name: '',
      description: '',
      order: phases ? phases.length + 1 : 1,
      phase_id: `phase_${Date.now()}`,
    });
    setPhaseDialogOpen(true);
  };

  // Handle phase dialog close
  const handlePhaseDialogClose = () => {
    setPhaseDialogOpen(false);
  };

  // Handle task creation
  const handleCreateTask = async () => {
    try {
      await createTask({
        ...newTask,
        project_id: projectId,
      }).unwrap();
      setTaskDialogOpen(false);
    } catch (error) {
      console.error('Failed to create task:', error);
    }
  };

  // Handle phase creation
  const handleCreatePhase = async () => {
    try {
      await createPhase({
        projectId,
        phase: newPhase as any,
      }).unwrap();
      setPhaseDialogOpen(false);
    } catch (error) {
      console.error('Failed to create phase:', error);
    }
  };

  // Handle task status update
  const handleUpdateTaskStatus = async (taskId: string, status: TaskStatus) => {
    try {
      await updateTaskStatus({ taskId, status }).unwrap();
    } catch (error) {
      console.error('Failed to update task status:', error);
    }
  };

  // Handle task progress update
  const handleUpdateTaskProgress = async (taskId: string, progress: number) => {
    try {
      await updateTaskProgress({ taskId, progress }).unwrap();
    } catch (error) {
      console.error('Failed to update task progress:', error);
    }
  };

  // Handle task deletion
  const handleDeleteTask = async (taskId: string) => {
    try {
      await deleteTask(taskId).unwrap();
    } catch (error) {
      console.error('Failed to delete task:', error);
    }
  };

  // Get status color
  const getStatusColor = (status: TaskStatus) => {
    switch (status) {
      case 'completed':
        return theme.palette.success.main;
      case 'in_progress':
        return theme.palette.warning.main;
      case 'failed':
        return theme.palette.error.main;
      case 'blocked':
        return theme.palette.error.light;
      default:
        return theme.palette.info.main;
    }
  };

  // Get priority color
  const getPriorityColor = (priority: TaskPriority) => {
    switch (priority) {
      case 'critical':
        return theme.palette.error.main;
      case 'high':
        return theme.palette.warning.main;
      case 'medium':
        return theme.palette.info.main;
      default:
        return theme.palette.success.main;
    }
  };

  // Render loading state
  if (projectLoading || phasesLoading) {
    return (
      <Box sx={{ display: 'flex', justifyContent: 'center', alignItems: 'center', height: '100%' }}>
        <CircularProgress />
      </Box>
    );
  }

  // Render error state
  if (projectError) {
    return (
      <Box sx={{ p: 2, color: 'error.main' }}>
        <Typography variant="body1">Error loading project data. Please try again.</Typography>
      </Box>
    );
  }

  // Render task list view
  const renderTaskList = (tasks: Task[]) => {
    return (
      <List>
        {tasks.map((task) => (
          <React.Fragment key={task.id}>
            <ListItem
              button
              selected={selectedTaskId === task.id}
              onClick={() => handleTaskSelect(task.id)}
              sx={{
                borderLeft: `4px solid ${getStatusColor(task.status)}`,
                mb: 1,
                bgcolor: 'background.paper',
                borderRadius: 1,
                '&:hover': {
                  bgcolor: alpha(theme.palette.primary.main, 0.1),
                },
              }}
            >
              <ListItemIcon>
                <AssignmentIcon color="primary" />
              </ListItemIcon>
              <ListItemText
                primary={task.name}
                secondary={
                  <React.Fragment>
                    <Typography variant="body2" color="text.secondary" noWrap>
                      {task.description}
                    </Typography>
                    <LinearProgress
                      variant="determinate"
                      value={task.progress}
                      sx={{
                        mt: 1,
                        height: 6,
                        borderRadius: 3,
                        bgcolor: alpha(theme.palette.primary.main, 0.1),
                      }}
                    />
                  </React.Fragment>
                }
              />
              <Box sx={{ display: 'flex', alignItems: 'center' }}>
                <Chip
                  label={task.priority}
                  size="small"
                  sx={{
                    bgcolor: getPriorityColor(task.priority),
                    color: 'white',
                    mr: 1,
                  }}
                />
                <Chip
                  label={task.status.replace('_', ' ')}
                  size="small"
                  sx={{
                    bgcolor: getStatusColor(task.status),
                    color: 'white',
                    mr: 1,
                  }}
                />
                <IconButton
                  size="small"
                  onClick={(e) => {
                    e.stopPropagation();
                    handleTaskExpand(task.id);
                  }}
                >
                  {expandedTasks[task.id] ? <ExpandLessIcon /> : <ExpandMoreIcon />}
                </IconButton>
              </Box>
            </ListItem>
            <Collapse in={expandedTasks[task.id]} timeout="auto" unmountOnExit>
              <Paper
                sx={{
                  p: 2,
                  ml: 4,
                  mb: 2,
                  bgcolor: alpha(theme.palette.background.paper, 0.7),
                }}
              >
                <Typography variant="body1" gutterBottom>
                  {task.description}
                </Typography>
                <Grid container spacing={2} sx={{ mt: 1 }}>
                  <Grid item xs={6}>
                    <Typography variant="body2" color="text.secondary">
                      Created: {new Date(task.created_at).toLocaleString()}
                    </Typography>
                  </Grid>
                  <Grid item xs={6}>
                    <Typography variant="body2" color="text.secondary">
                      Updated: {new Date(task.updated_at).toLocaleString()}
                    </Typography>
                  </Grid>
                  {task.started_at && (
                    <Grid item xs={6}>
                      <Typography variant="body2" color="text.secondary">
                        Started: {new Date(task.started_at).toLocaleString()}
                      </Typography>
                    </Grid>
                  )}
                  {task.completed_at && (
                    <Grid item xs={6}>
                      <Typography variant="body2" color="text.secondary">
                        Completed: {new Date(task.completed_at).toLocaleString()}
                      </Typography>
                    </Grid>
                  )}
                </Grid>
                <Box sx={{ mt: 2, display: 'flex', justifyContent: 'space-between' }}>
                  <Box>
                    <Button
                      size="small"
                      variant="outlined"
                      color="primary"
                      onClick={() => {
                        // Edit task logic
                      }}
                      startIcon={<EditIcon />}
                      sx={{ mr: 1 }}
                    >
                      Edit
                    </Button>
                    <Button
                      size="small"
                      variant="outlined"
                      color="error"
                      onClick={() => handleDeleteTask(task.id)}
                      startIcon={<DeleteIcon />}
                    >
                      Delete
                    </Button>
                  </Box>
                  <Box>
                    {task.status !== 'completed' && (
                      <Button
                        size="small"
                        variant="contained"
                        color="success"
                        onClick={() => handleUpdateTaskStatus(task.id, 'completed')}
                        startIcon={<CheckCircleIcon />}
                        sx={{ mr: 1 }}
                      >
                        Complete
                      </Button>
                    )}
                    {task.status === 'planned' && (
                      <Button
                        size="small"
                        variant="contained"
                        color="primary"
                        onClick={() => handleUpdateTaskStatus(task.id, 'in_progress')}
                        startIcon={<TimelineIcon />}
                      >
                        Start
                      </Button>
                    )}
                  </Box>
                </Box>
              </Paper>
            </Collapse>
          </React.Fragment>
        ))}
      </List>
    );
  };

  // Render task card view
  const renderTaskCards = (tasks: Task[]) => {
    return (
      <Grid container spacing={2}>
        {tasks.map((task) => (
          <Grid item xs={12} sm={6} md={4} key={task.id}>
            <Card
              sx={{
                borderTop: `4px solid ${getStatusColor(task.status)}`,
                height: '100%',
                display: 'flex',
                flexDirection: 'column',
              }}
            >
              <CardHeader
                title={task.name}
                subheader={`Priority: ${task.priority}`}
                action={
                  <Box sx={{ display: 'flex' }}>
                    <Chip
                      label={task.status.replace('_', ' ')}
                      size="small"
                      sx={{
                        bgcolor: getStatusColor(task.status),
                        color: 'white',
                        mr: 1,
                      }}
                    />
                  </Box>
                }
              />
              <CardContent sx={{ flexGrow: 1 }}>
                <Typography variant="body2" color="text.secondary" paragraph>
                  {task.description}
                </Typography>
                <Box sx={{ mt: 2 }}>
                  <Typography variant="body2" color="text.secondary" gutterBottom>
                    Progress: {task.progress}%
                  </Typography>
                  <LinearProgress
                    variant="determinate"
                    value={task.progress}
                    sx={{
                      height: 8,
                      borderRadius: 4,
                      bgcolor: alpha(theme.palette.primary.main, 0.1),
                    }}
                  />
                </Box>
              </CardContent>
              <CardActions sx={{ justifyContent: 'space-between' }}>
                <Button
                  size="small"
                  color="primary"
                  onClick={() => {
                    // Edit task logic
                  }}
                  startIcon={<EditIcon />}
                >
                  Edit
                </Button>
                {task.status !== 'completed' && (
                  <Button
                    size="small"
                    color="success"
                    onClick={() => handleUpdateTaskStatus(task.id, 'completed')}
                    startIcon={<CheckCircleIcon />}
                  >
                    Complete
                  </Button>
                )}
              </CardActions>
            </Card>
          </Grid>
        ))}
      </Grid>
    );
  };

  return (
    <Paper
      elevation={3}
      sx={{
        height: mode === 'embedded' ? height : '100vh',
        display: 'flex',
        flexDirection: 'column',
        overflow: 'hidden',
      }}
    >
      {/* Header */}
      {showTitle && (
        <Box sx={{ p: 2, borderBottom: 1, borderColor: 'divider' }}>
          <Typography variant="h5" gutterBottom>
            {project?.name || 'Project Progress'}
          </Typography>
          <Typography variant="body2" color="text.secondary">
            {project?.description}
          </Typography>
        </Box>
      )}

      {/* Progress Bar */}
      <Box sx={{ p: 2, borderBottom: 1, borderColor: 'divider' }}>
        <ProjectProgressBar projectId={projectId} showDetails />
      </Box>

      {/* Phases Tabs */}
      <Box sx={{ borderBottom: 1, borderColor: 'divider' }}>
        <Box sx={{ display: 'flex', alignItems: 'center' }}>
          <Tabs
            value={selectedPhaseId || ''}
            onChange={handlePhaseChange}
            variant="scrollable"
            scrollButtons="auto"
            sx={{ flexGrow: 1 }}
          >
            {phases?.map((phase) => (
              <Tab
                key={phase.id}
                label={phase.name}
                value={phase.id}
                sx={{ textTransform: 'none' }}
              />
            ))}
          </Tabs>
          <Tooltip title="Add Phase">
            <IconButton onClick={handlePhaseDialogOpen} sx={{ mr: 1 }}>
              <AddIcon />
            </IconButton>
          </Tooltip>
        </Box>
      </Box>

      {/* Content */}
      <Box sx={{ p: 2, flexGrow: 1, overflow: 'auto' }}>
        {/* Toolbar */}
        <Box
          sx={{
            display: 'flex',
            justifyContent: 'space-between',
            alignItems: 'center',
            mb: 2,
          }}
        >
          <Typography variant="h6">
            {selectedPhaseId && phases
              ? phases.find((p) => p.id === selectedPhaseId)?.name
              : 'All Tasks'}
          </Typography>
          <Box>
            <Tooltip title="List View">
              <IconButton
                color={viewMode === 'list' ? 'primary' : 'default'}
                onClick={() => handleViewModeChange('list')}
              >
                <ViewListIcon />
              </IconButton>
            </Tooltip>
            <Tooltip title="Card View">
              <IconButton
                color={viewMode === 'card' ? 'primary' : 'default'}
                onClick={() => handleViewModeChange('card')}
              >
                <ViewModuleIcon />
              </IconButton>
            </Tooltip>
            <Tooltip title="Refresh">
              <IconButton>
                <RefreshIcon />
              </IconButton>
            </Tooltip>
            <Button
              variant="contained"
              color="primary"
              startIcon={<AddIcon />}
              onClick={handleTaskDialogOpen}
              sx={{ ml: 1 }}
            >
              Add Task
            </Button>
          </Box>
        </Box>

        {/* Tasks */}
        {tasksLoading ? (
          <Box sx={{ display: 'flex', justifyContent: 'center', p: 4 }}>
            <CircularProgress />
          </Box>
        ) : tasks && tasks.length > 0 ? (
          viewMode === 'list' ? renderTaskList(tasks) : renderTaskCards(tasks)
        ) : (
          <Box sx={{ p: 4, textAlign: 'center' }}>
            <Typography variant="body1" color="text.secondary">
              No tasks found in this phase.
            </Typography>
            <Button
              variant="outlined"
              color="primary"
              startIcon={<AddIcon />}
              onClick={handleTaskDialogOpen}
              sx={{ mt: 2 }}
            >
              Add Task
            </Button>
          </Box>
        )}
      </Box>

      {/* Task Dialog */}
      <Dialog open={taskDialogOpen} onClose={handleTaskDialogClose} maxWidth="sm" fullWidth>
        <DialogTitle>Add New Task</DialogTitle>
        <DialogContent>
          <TextField
            autoFocus
            margin="dense"
            label="Task Name"
            fullWidth
            value={newTask.name}
            onChange={(e) => setNewTask({ ...newTask, name: e.target.value })}
            sx={{ mb: 2 }}
          />
          <TextField
            margin="dense"
            label="Description"
            fullWidth
            multiline
            rows={4}
            value={newTask.description}
            onChange={(e) => setNewTask({ ...newTask, description: e.target.value })}
            sx={{ mb: 2 }}
          />
          <Grid container spacing={2}>
            <Grid item xs={6}>
              <FormControl fullWidth>
                <InputLabel>Status</InputLabel>
                <Select
                  value={newTask.status}
                  label="Status"
                  onChange={(e) => setNewTask({ ...newTask, status: e.target.value as TaskStatus })}
                >
                  <MenuItem value="planned">Planned</MenuItem>
                  <MenuItem value="in_progress">In Progress</MenuItem>
                  <MenuItem value="completed">Completed</MenuItem>
                  <MenuItem value="blocked">Blocked</MenuItem>
                </Select>
              </FormControl>
            </Grid>
            <Grid item xs={6}>
              <FormControl fullWidth>
                <InputLabel>Priority</InputLabel>
                <Select
                  value={newTask.priority}
                  label="Priority"
                  onChange={(e) => setNewTask({ ...newTask, priority: e.target.value as TaskPriority })}
                >
                  <MenuItem value="low">Low</MenuItem>
                  <MenuItem value="medium">Medium</MenuItem>
                  <MenuItem value="high">High</MenuItem>
                  <MenuItem value="critical">Critical</MenuItem>
                </Select>
              </FormControl>
            </Grid>
          </Grid>
        </DialogContent>
        <DialogActions>
          <Button onClick={handleTaskDialogClose}>Cancel</Button>
          <Button
            onClick={handleCreateTask}
            variant="contained"
            color="primary"
            disabled={!newTask.name || isCreatingTask}
          >
            {isCreatingTask ? <CircularProgress size={24} /> : 'Create'}
          </Button>
        </DialogActions>
      </Dialog>

      {/* Phase Dialog */}
      <Dialog open={phaseDialogOpen} onClose={handlePhaseDialogClose} maxWidth="sm" fullWidth>
        <DialogTitle>Add New Phase</DialogTitle>
        <DialogContent>
          <TextField
            autoFocus
            margin="dense"
            label="Phase Name"
            fullWidth
            value={newPhase.name}
            onChange={(e) => setNewPhase({ ...newPhase, name: e.target.value })}
            sx={{ mb: 2 }}
          />
          <TextField
            margin="dense"
            label="Description"
            fullWidth
            multiline
            rows={4}
            value={newPhase.description}
            onChange={(e) => setNewPhase({ ...newPhase, description: e.target.value })}
            sx={{ mb: 2 }}
          />
          <TextField
            margin="dense"
            label="Order"
            type="number"
            fullWidth
            value={newPhase.order}
            onChange={(e) => setNewPhase({ ...newPhase, order: parseInt(e.target.value) })}
          />
        </DialogContent>
        <DialogActions>
          <Button onClick={handlePhaseDialogClose}>Cancel</Button>
          <Button
            onClick={handleCreatePhase}
            variant="contained"
            color="primary"
            disabled={!newPhase.name || isCreatingPhase}
          >
            {isCreatingPhase ? <CircularProgress size={24} /> : 'Create'}
          </Button>
        </DialogActions>
      </Dialog>
    </Paper>
  );
};

export default ProgressTracker;
