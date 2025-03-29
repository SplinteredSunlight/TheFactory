import React, { useEffect } from 'react';
import { useDispatch, useSelector } from 'react-redux';
import {
  Box,
  Typography,
  Paper,
  Grid,
  Card,
  CardContent,
  CardHeader,
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
} from '@mui/material';
import {
  Refresh as RefreshIcon,
  Add as AddIcon,
  FilterList as FilterListIcon,
  Search as SearchIcon,
  People as PeopleIcon,
  CheckCircle as CheckCircleIcon,
  Error as ErrorIcon,
  Warning as WarningIcon,
} from '@mui/icons-material';
import { RootState } from '../store';
import { Agent, AgentStatus, AgentFramework } from '../types/agent';

const Agents: React.FC = () => {
  const dispatch = useDispatch();
  const theme = useTheme();
  
  // Get data from Redux store
  const { agents, isLoading } = useSelector((state: RootState) => state.agents);

  // Fetch data on component mount
  useEffect(() => {
    // In a real application, we would dispatch an action to fetch agents
    // dispatch(fetchAgents());
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

  // Helper function to get status icon
  const getStatusIcon = (status: AgentStatus) => {
    switch (status) {
      case AgentStatus.IDLE:
        return <CheckCircleIcon />;
      case AgentStatus.OFFLINE:
        return <ErrorIcon />;
      case AgentStatus.BUSY:
        return <WarningIcon />;
      case AgentStatus.ERROR:
        return <ErrorIcon />;
      default:
        return <PeopleIcon />;
    }
  };

  return (
    <Box sx={{ flexGrow: 1 }}>
      <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 3 }}>
        <Typography variant="h4" component="h1">
          Agents
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
            Add Agent
          </Button>
        </Box>
      </Box>

      {isLoading ? (
        <CircularProgress sx={{ display: 'block', mx: 'auto', my: 4 }} />
      ) : (
        <Grid container spacing={3}>
          {/* Agent Summary */}
          <Grid item xs={12}>
            <Paper sx={{ p: 2 }}>
              <Typography variant="h6" gutterBottom>
                Agent Summary
              </Typography>
              <Grid container spacing={2}>
                <Grid item xs={12} sm={6} md={3}>
                  <Card variant="outlined">
                    <CardContent>
                      <Typography variant="h5" component="div">
                        {agents.length}
                      </Typography>
                      <Typography color="text.secondary">
                        Total Agents
                      </Typography>
                    </CardContent>
                  </Card>
                </Grid>
                <Grid item xs={12} sm={6} md={3}>
                  <Card variant="outlined">
                    <CardContent>
                      <Typography variant="h5" component="div">
                        {agents.filter(a => a.status === AgentStatus.IDLE).length}
                      </Typography>
                      <Typography color="text.secondary">
                        Online Agents
                      </Typography>
                    </CardContent>
                  </Card>
                </Grid>
                <Grid item xs={12} sm={6} md={3}>
                  <Card variant="outlined">
                    <CardContent>
                      <Typography variant="h5" component="div">
                        {agents.filter(a => a.framework === AgentFramework.AI_ORCHESTRATOR).length}
                      </Typography>
                      <Typography color="text.secondary">
                        AI-Orchestrator Agents
                      </Typography>
                    </CardContent>
                  </Card>
                </Grid>
                <Grid item xs={12} sm={6} md={3}>
                  <Card variant="outlined">
                    <CardContent>
                      <Typography variant="h5" component="div">
                        {agents.filter(a => a.framework === AgentFramework.FAST_AGENT).length}
                      </Typography>
                      <Typography color="text.secondary">
                        Fast-Agent Agents
                      </Typography>
                    </CardContent>
                  </Card>
                </Grid>
              </Grid>
            </Paper>
          </Grid>

          {/* Agent List */}
          <Grid item xs={12}>
            <Paper sx={{ p: 2 }}>
              <Typography variant="h6" gutterBottom>
                Agent List
              </Typography>
              <List>
                {agents.length > 0 ? (
                  agents.map((agent) => (
                    <React.Fragment key={agent.id}>
                      <ListItem
                        alignItems="flex-start"
                        secondaryAction={
                          <Chip
                            label={agent.status}
                            size="small"
                            sx={{
                              bgcolor: getStatusColor(agent.status),
                              color: 'white',
                            }}
                          />
                        }
                      >
                        <ListItemAvatar>
                          <Avatar sx={{ bgcolor: getStatusColor(agent.status) }}>
                            {getStatusIcon(agent.status)}
                          </Avatar>
                        </ListItemAvatar>
                        <ListItemText
                          primary={
                            <Typography variant="subtitle1">
                              {agent.name}
                            </Typography>
                          }
                          secondary={
                            <>
                              <Typography component="span" variant="body2" color="text.primary">
                                {agent.framework}
                              </Typography>
                              <Typography variant="body2" component="div">
                                {agent.description}
                              </Typography>
                              <Box sx={{ display: 'flex', alignItems: 'center', mt: 1 }}>
                                <Typography variant="body2" color="text.secondary" sx={{ mr: 2 }}>
                                  Load: {agent.currentLoad}
                                </Typography>
                                <LinearProgress
                                  variant="determinate"
                                  value={(agent.currentLoad / 10) * 100} // Assuming max load is 10
                                  sx={{ flexGrow: 1, height: 8, borderRadius: 4 }}
                                />
                              </Box>
                              <Box sx={{ mt: 1 }}>
                                {agent.capabilities.map((capability) => (
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
                      primary="No agents found"
                      secondary="Add an agent to get started"
                    />
                  </ListItem>
                )}
              </List>
            </Paper>
          </Grid>
        </Grid>
      )}
    </Box>
  );
};

export default Agents;
