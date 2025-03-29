import React, { useEffect, useState } from 'react';
import { Box, Card, CardContent, Container, Grid, LinearProgress, Typography, List, ListItem, ListItemIcon, ListItemText, Divider, Paper, Theme } from '@mui/material';
import { makeStyles } from '@mui/styles';
import CheckCircleIcon from '@mui/icons-material/CheckCircle';
import LoopIcon from '@mui/icons-material/Loop';
import HourglassEmptyIcon from '@mui/icons-material/HourglassEmpty';
import { useTheme } from '@mui/material/styles';

// Define styles
const useStyles = makeStyles((theme: Theme) => ({
  root: {
    flexGrow: 1,
    padding: theme.spacing(3),
  },
  title: {
    marginBottom: theme.spacing(3),
  },
  card: {
    height: '100%',
    display: 'flex',
    flexDirection: 'column',
  },
  cardTitle: {
    borderBottom: `1px solid ${theme.palette.divider}`,
    paddingBottom: theme.spacing(1),
    marginBottom: theme.spacing(2),
  },
  progressContainer: {
    margin: theme.spacing(2, 0),
  },
  progressLabel: {
    display: 'flex',
    justifyContent: 'space-between',
    marginTop: theme.spacing(0.5),
  },
  taskList: {
    width: '100%',
    backgroundColor: theme.palette.background.paper,
  },
  taskItem: {
    borderBottom: `1px solid ${theme.palette.divider}`,
  },
  taskProgress: {
    fontWeight: 'bold',
    marginLeft: theme.spacing(1),
  },
  completed: {
    color: theme.palette.success.main,
  },
  inProgress: {
    color: theme.palette.warning.main,
  },
  planned: {
    color: theme.palette.text.secondary,
  },
  phaseList: {
    width: '100%',
    marginTop: theme.spacing(2),
  },
  phaseItem: {
    marginBottom: theme.spacing(2),
  },
  phaseHeader: {
    display: 'flex',
    justifyContent: 'space-between',
    marginBottom: theme.spacing(0.5),
  },
  phaseName: {
    fontWeight: 'bold',
  },
  phaseProgress: {
    color: theme.palette.text.secondary,
  },
}));

// Define types
interface Phase {
  id: string;
  name: string;
  order: number;
  taskCount: number;
  completedTasks: number;
  progress: number;
}

interface Project {
  id: string;
  name: string;
  description: string;
  taskCount: number;
  completedTasks: number;
  progress: number;
  phases: Phase[];
  createdAt: string;
  updatedAt: string;
}

interface Task {
  id: string;
  name: string;
  description: string;
  status: 'completed' | 'in_progress' | 'planned';
  progress: number;
  phase_id: string;
}

interface WorkflowExecution {
  id: string;
  name: string;
  status: 'completed' | 'in_progress' | 'planned';
  progress: number;
}

// Mock data
const mockProjects: Project[] = [
  {
    id: 'project-1',
    name: 'AI Orchestration Platform',
    description: 'A platform for orchestrating AI agents',
    taskCount: 7,
    completedTasks: 2,
    progress: 28.6,
    phases: [
      {
        id: 'phase-1',
        name: 'Planning',
        order: 0,
        taskCount: 2,
        completedTasks: 2,
        progress: 100,
      },
      {
        id: 'phase-2',
        name: 'Implementation',
        order: 1,
        taskCount: 3,
        completedTasks: 0,
        progress: 0,
      },
      {
        id: 'phase-3',
        name: 'Testing',
        order: 2,
        taskCount: 2,
        completedTasks: 0,
        progress: 0,
      },
    ],
    createdAt: '2025-03-01T00:00:00Z',
    updatedAt: '2025-03-10T00:00:00Z',
  },
];

const mockTasks: Task[] = [
  {
    id: 'task-1',
    name: 'Define requirements',
    description: 'Define the requirements for the AI Orchestration Platform',
    status: 'completed',
    progress: 100,
    phase_id: 'phase-1',
  },
  {
    id: 'task-2',
    name: 'Create architecture diagram',
    description: 'Create an architecture diagram for the AI Orchestration Platform',
    status: 'completed',
    progress: 100,
    phase_id: 'phase-1',
  },
  {
    id: 'task-3',
    name: 'Implement core components',
    description: 'Implement the core components of the AI Orchestration Platform',
    status: 'in_progress',
    progress: 75,
    phase_id: 'phase-2',
  },
  {
    id: 'task-4',
    name: 'Implement Dagger integration',
    description: 'Implement the Dagger workflow integration for the Task Management MCP Server',
    status: 'in_progress',
    progress: 90,
    phase_id: 'phase-2',
  },
  {
    id: 'task-5',
    name: 'Implement dashboard',
    description: 'Implement the dashboard UI for the AI Orchestration Platform',
    status: 'planned',
    progress: 0,
    phase_id: 'phase-2',
  },
  {
    id: 'task-6',
    name: 'Write tests',
    description: 'Write tests for the AI Orchestration Platform',
    status: 'planned',
    progress: 0,
    phase_id: 'phase-3',
  },
  {
    id: 'task-7',
    name: 'Run integration tests',
    description: 'Run integration tests for the AI Orchestration Platform',
    status: 'planned',
    progress: 0,
    phase_id: 'phase-3',
  },
];

const mockWorkflowExecutions: WorkflowExecution[] = [
  {
    id: 'workflow-1',
    name: 'Task CLI Integration',
    status: 'completed',
    progress: 100,
  },
  {
    id: 'workflow-2',
    name: 'Dashboard Integration',
    status: 'completed',
    progress: 100,
  },
  {
    id: 'workflow-3',
    name: 'Dagger Workflow Integration',
    status: 'in_progress',
    progress: 90,
  },
];

const DaggerDashboard: React.FC = () => {
  const classes = useStyles();
  const theme = useTheme();
  const [projects, setProjects] = useState<Project[]>([]);
  const [tasks, setTasks] = useState<Task[]>([]);
  const [workflowExecutions, setWorkflowExecutions] = useState<WorkflowExecution[]>([]);
  const [loading, setLoading] = useState<boolean>(true);

  useEffect(() => {
    // In a real application, you would fetch data from an API
    // For now, we'll use mock data
    setProjects(mockProjects);
    setTasks(mockTasks);
    setWorkflowExecutions(mockWorkflowExecutions);
    setLoading(false);
  }, []);

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'completed':
        return <CheckCircleIcon className={classes.completed} />;
      case 'in_progress':
        return <LoopIcon className={classes.inProgress} />;
      case 'planned':
        return <HourglassEmptyIcon className={classes.planned} />;
      default:
        return null;
    }
  };

  if (loading) {
    return (
      <Container>
        <Box mt={4}>
          <LinearProgress />
          <Typography variant="h6" align="center">
            Loading dashboard...
          </Typography>
        </Box>
      </Container>
    );
  }

  return (
    <div className={classes.root}>
      <Container maxWidth="lg">
        <Typography variant="h4" className={classes.title}>
          AI Orchestration Platform Dashboard
        </Typography>

        <Grid container spacing={3}>
          {/* Project Overview Card */}
          <Grid item xs={12} md={4}>
            <Card className={classes.card}>
              <CardContent>
                <Typography variant="h6" className={classes.cardTitle}>
                  Project Overview
                </Typography>

                {projects.map((project) => (
                  <Box key={project.id}>
                    <div className={classes.progressContainer}>
                      <LinearProgress
                        variant="determinate"
                        value={project.progress}
                        color="primary"
                      />
                      <div className={classes.progressLabel}>
                        <Typography variant="body2">
                          Progress: {project.progress.toFixed(1)}%
                        </Typography>
                        <Typography variant="body2">
                          {project.completedTasks}/{project.taskCount} tasks completed
                        </Typography>
                      </div>
                    </div>

                    <Typography variant="subtitle1" gutterBottom>
                      Phases
                    </Typography>
                    <List className={classes.phaseList}>
                      {project.phases.map((phase) => (
                        <Box key={phase.id} className={classes.phaseItem}>
                          <div className={classes.phaseHeader}>
                            <Typography variant="body2" className={classes.phaseName}>
                              {phase.name}
                            </Typography>
                            <Typography variant="body2" className={classes.phaseProgress}>
                              {phase.progress.toFixed(0)}% ({phase.completedTasks}/{phase.taskCount} tasks)
                            </Typography>
                          </div>
                          <LinearProgress
                            variant="determinate"
                            value={phase.progress}
                            color="primary"
                          />
                        </Box>
                      ))}
                    </List>
                  </Box>
                ))}
              </CardContent>
            </Card>
          </Grid>

          {/* Tasks Card */}
          <Grid item xs={12} md={4}>
            <Card className={classes.card}>
              <CardContent>
                <Typography variant="h6" className={classes.cardTitle}>
                  Tasks
                </Typography>
                <List className={classes.taskList}>
                  {tasks.map((task) => (
                    <ListItem key={task.id} className={classes.taskItem}>
                      <ListItemIcon>{getStatusIcon(task.status)}</ListItemIcon>
                      <ListItemText primary={task.name} />
                      <Typography variant="body2" className={classes.taskProgress}>
                        {task.progress}%
                      </Typography>
                    </ListItem>
                  ))}
                </List>
              </CardContent>
            </Card>
          </Grid>

          {/* Dagger Workflow Integration Card */}
          <Grid item xs={12} md={4}>
            <Card className={classes.card}>
              <CardContent>
                <Typography variant="h6" className={classes.cardTitle}>
                  Dagger Workflow Integration
                </Typography>

                <div className={classes.progressContainer}>
                  <LinearProgress
                    variant="determinate"
                    value={90}
                    color="primary"
                  />
                  <div className={classes.progressLabel}>
                    <Typography variant="body2">
                      Progress: 90%
                    </Typography>
                    <Typography variant="body2">
                      In Progress
                    </Typography>
                  </div>
                </div>

                <Typography variant="subtitle1" gutterBottom>
                  Recent Workflow Executions
                </Typography>
                <List className={classes.taskList}>
                  {workflowExecutions.map((workflow) => (
                    <ListItem key={workflow.id} className={classes.taskItem}>
                      <ListItemIcon>{getStatusIcon(workflow.status)}</ListItemIcon>
                      <ListItemText primary={workflow.name} />
                      <Typography variant="body2" className={classes.taskProgress}>
                        {workflow.progress}%
                      </Typography>
                    </ListItem>
                  ))}
                </List>
              </CardContent>
            </Card>
          </Grid>
        </Grid>
      </Container>
    </div>
  );
};

export default DaggerDashboard;
