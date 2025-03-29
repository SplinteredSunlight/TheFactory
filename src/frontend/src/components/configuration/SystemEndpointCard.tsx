import React, { useState } from 'react';
import {
  Card,
  CardHeader,
  CardContent,
  Typography,
  Switch,
  FormControlLabel,
  TextField,
  Button,
  Box,
  IconButton,
  Collapse,
  Select,
  MenuItem,
  FormControl,
  InputLabel,
  Grid,
  Divider,
  Chip,
  Tooltip,
} from '@mui/material';
import {
  Edit as EditIcon,
  Delete as DeleteIcon,
  ExpandMore as ExpandMoreIcon,
  Check as CheckIcon,
  Close as CloseIcon,
  Code as CodeIcon,
  Api as ApiIcon,
  Settings as SettingsIcon,
} from '@mui/icons-material';
import { styled } from '@mui/material/styles';
import { SystemEndpoint } from '../../store/slices/configurationSlice';
import { AgentFramework } from '../../types/agent';

interface ExpandMoreProps {
  expand: boolean;
  onClick: () => void;
  'aria-expanded': boolean;
  'aria-label': string;
}

const ExpandMore = styled((props: ExpandMoreProps) => {
  const { expand, ...other } = props;
  return <IconButton {...other} />;
})(({ theme, expand }) => ({
  transform: !expand ? 'rotate(0deg)' : 'rotate(180deg)',
  marginLeft: 'auto',
  transition: theme.transitions.create('transform', {
    duration: theme.transitions.duration.shortest,
  }),
}));

interface SystemEndpointCardProps {
  system: SystemEndpoint;
  onToggleEnabled: (id: string) => void;
  onUpdate: (system: SystemEndpoint) => void;
  onDelete: (id: string) => void;
  onTestConnection: (id: string) => void;
}

const SystemEndpointCard: React.FC<SystemEndpointCardProps> = ({
  system,
  onToggleEnabled,
  onUpdate,
  onDelete,
  onTestConnection,
}) => {
  const [expanded, setExpanded] = useState(false);
  const [editing, setEditing] = useState(false);
  const [editedSystem, setEditedSystem] = useState<SystemEndpoint>({ ...system });

  const handleExpandClick = () => {
    setExpanded(!expanded);
  };

  const handleEditClick = () => {
    setEditedSystem({ ...system });
    setEditing(true);
    setExpanded(true);
  };

  const handleCancelEdit = () => {
    setEditing(false);
  };

  const handleSaveEdit = () => {
    onUpdate(editedSystem);
    setEditing(false);
  };

  const handleChange = (e: React.ChangeEvent<HTMLInputElement | { name?: string; value: unknown }>) => {
    const { name, value } = e.target;
    if (name) {
      if (name.startsWith('credentials.')) {
        const credentialField = name.split('.')[1];
        setEditedSystem({
          ...editedSystem,
          credentials: {
            ...editedSystem.credentials,
            [credentialField]: value,
          },
        });
      } else if (name.startsWith('metadata.')) {
        const metadataField = name.split('.')[1];
        setEditedSystem({
          ...editedSystem,
          metadata: {
            ...editedSystem.metadata,
            [metadataField]: value,
          },
        });
      } else {
        setEditedSystem({
          ...editedSystem,
          [name]: value,
        });
      }
    }
  };

  const handleAuthTypeChange = (e: React.ChangeEvent<{ name?: string; value: unknown }>) => {
    const authType = e.target.value as SystemEndpoint['authType'];
    setEditedSystem({
      ...editedSystem,
      authType,
      credentials: getDefaultCredentials(authType),
    });
  };

  const getDefaultCredentials = (authType: SystemEndpoint['authType']) => {
    switch (authType) {
      case 'basic':
        return { username: '', password: '' };
      case 'token':
        return { token: '' };
      case 'oauth':
        return { clientId: '', clientSecret: '' };
      default:
        return {};
    }
  };

  // Determine if this is an AI-Orchestrator or Fast-Agent system
  const isAIOrchestrator = system.id === 'orchestrator' || system.name.toLowerCase().includes('orchestrator');
  const isFastAgent = system.id === 'fast-agent' || system.name.toLowerCase().includes('fast-agent');
  
  // Get system type label
  const getSystemTypeLabel = () => {
    if (isAIOrchestrator) return 'AI-Orchestrator';
    if (isFastAgent) return 'Fast-Agent';
    return 'External System';
  };
  
  // Get system type icon
  const getSystemTypeIcon = () => {
    if (isAIOrchestrator) return <ApiIcon fontSize="small" />;
    if (isFastAgent) return <CodeIcon fontSize="small" />;
    return <SettingsIcon fontSize="small" />;
  };

  return (
    <Card variant="outlined" sx={{ mb: 2 }}>
      <CardHeader
        title={
          <Box display="flex" alignItems="center">
            <Typography variant="h6" component="div">
              {system.name}
            </Typography>
            <FormControlLabel
              control={
                <Switch
                  checked={system.enabled}
                  onChange={() => onToggleEnabled(system.id)}
                  color="primary"
                  disabled={editing}
                />
              }
              label={system.enabled ? 'Enabled' : 'Disabled'}
              sx={{ ml: 2 }}
            />
            <Tooltip title={getSystemTypeLabel()}>
              <Chip
                icon={getSystemTypeIcon()}
                label={getSystemTypeLabel()}
                size="small"
                color={isAIOrchestrator ? "primary" : isFastAgent ? "secondary" : "default"}
                sx={{ ml: 2 }}
              />
            </Tooltip>
          </Box>
        }
        action={
          <Box>
            {!editing && (
              <>
                <IconButton aria-label="edit" onClick={handleEditClick}>
                  <EditIcon />
                </IconButton>
                <IconButton aria-label="delete" onClick={() => onDelete(system.id)}>
                  <DeleteIcon />
                </IconButton>
                <ExpandMore
                  expand={expanded}
                  onClick={handleExpandClick}
                  aria-expanded={expanded}
                  aria-label="show more"
                >
                  <ExpandMoreIcon />
                </ExpandMore>
              </>
            )}
            {editing && (
              <>
                <IconButton aria-label="save" onClick={handleSaveEdit} color="primary">
                  <CheckIcon />
                </IconButton>
                <IconButton aria-label="cancel" onClick={handleCancelEdit} color="error">
                  <CloseIcon />
                </IconButton>
              </>
            )}
          </Box>
        }
        subheader={
          <Typography variant="body2" color="text.secondary">
            {system.url}
          </Typography>
        }
      />
      <Collapse in={expanded} timeout="auto" unmountOnExit>
        <CardContent>
          {editing ? (
            <Grid container spacing={2}>
              <Grid item xs={12} md={6}>
                <TextField
                  fullWidth
                  label="System Name"
                  name="name"
                  value={editedSystem.name}
                  onChange={handleChange}
                  margin="normal"
                />
                <TextField
                  fullWidth
                  label="URL"
                  name="url"
                  value={editedSystem.url}
                  onChange={handleChange}
                  margin="normal"
                />
                <FormControl fullWidth margin="normal">
                  <InputLabel id="auth-type-label">Authentication Type</InputLabel>
                  <Select
                    labelId="auth-type-label"
                    id="auth-type"
                    name="authType"
                    value={editedSystem.authType}
                    onChange={handleAuthTypeChange}
                    label="Authentication Type"
                  >
                    <MenuItem value="none">None</MenuItem>
                    <MenuItem value="basic">Basic Auth</MenuItem>
                    <MenuItem value="token">Token</MenuItem>
                    <MenuItem value="oauth">OAuth</MenuItem>
                  </Select>
                </FormControl>
                
                {/* System-specific fields */}
                {isAIOrchestrator && (
                  <FormControl fullWidth margin="normal">
                    <InputLabel id="orchestrator-mode-label">Orchestrator Mode</InputLabel>
                    <Select
                      labelId="orchestrator-mode-label"
                      id="orchestrator-mode"
                      name="metadata.orchestratorMode"
                      value={editedSystem.metadata?.orchestratorMode || 'standard'}
                      onChange={handleChange}
                      label="Orchestrator Mode"
                    >
                      <MenuItem value="standard">Standard</MenuItem>
                      <MenuItem value="distributed">Distributed</MenuItem>
                      <MenuItem value="high-availability">High Availability</MenuItem>
                    </Select>
                  </FormControl>
                )}
                
                {isFastAgent && (
                  <FormControl fullWidth margin="normal">
                    <InputLabel id="default-model-label">Default Model</InputLabel>
                    <Select
                      labelId="default-model-label"
                      id="default-model"
                      name="metadata.defaultModel"
                      value={editedSystem.metadata?.defaultModel || 'gpt-4'}
                      onChange={handleChange}
                      label="Default Model"
                    >
                      <MenuItem value="gpt-4">GPT-4</MenuItem>
                      <MenuItem value="gpt-4-turbo">GPT-4 Turbo</MenuItem>
                      <MenuItem value="claude-3">Claude 3</MenuItem>
                      <MenuItem value="llama-3">Llama 3</MenuItem>
                    </Select>
                  </FormControl>
                )}
              </Grid>
              <Grid item xs={12} md={6}>
                {editedSystem.authType === 'basic' && (
                  <>
                    <TextField
                      fullWidth
                      label="Username"
                      name="credentials.username"
                      value={editedSystem.credentials?.username || ''}
                      onChange={handleChange}
                      margin="normal"
                    />
                    <TextField
                      fullWidth
                      label="Password"
                      name="credentials.password"
                      type="password"
                      value={editedSystem.credentials?.password || ''}
                      onChange={handleChange}
                      margin="normal"
                    />
                  </>
                )}
                {editedSystem.authType === 'token' && (
                  <TextField
                    fullWidth
                    label="Token"
                    name="credentials.token"
                    value={editedSystem.credentials?.token || ''}
                    onChange={handleChange}
                    margin="normal"
                  />
                )}
                {editedSystem.authType === 'oauth' && (
                  <>
                    <TextField
                      fullWidth
                      label="Client ID"
                      name="credentials.clientId"
                      value={editedSystem.credentials?.clientId || ''}
                      onChange={handleChange}
                      margin="normal"
                    />
                    <TextField
                      fullWidth
                      label="Client Secret"
                      name="credentials.clientSecret"
                      type="password"
                      value={editedSystem.credentials?.clientSecret || ''}
                      onChange={handleChange}
                      margin="normal"
                    />
                  </>
                )}
                
                {/* Additional system-specific fields */}
                {isAIOrchestrator && (
                  <>
                    <TextField
                      fullWidth
                      label="Max Agents"
                      name="metadata.maxAgents"
                      type="number"
                      value={editedSystem.metadata?.maxAgents || 10}
                      onChange={handleChange}
                      margin="normal"
                      inputProps={{ min: 1 }}
                    />
                    <FormControl fullWidth margin="normal">
                      <InputLabel id="task-distribution-strategy-label">Task Distribution</InputLabel>
                      <Select
                        labelId="task-distribution-strategy-label"
                        id="task-distribution-strategy"
                        name="metadata.taskDistributionStrategy"
                        value={editedSystem.metadata?.taskDistributionStrategy || 'round-robin'}
                        onChange={handleChange}
                        label="Task Distribution"
                      >
                        <MenuItem value="round-robin">Round Robin</MenuItem>
                        <MenuItem value="capability-based">Capability Based</MenuItem>
                        <MenuItem value="load-balanced">Load Balanced</MenuItem>
                        <MenuItem value="priority-based">Priority Based</MenuItem>
                      </Select>
                    </FormControl>
                  </>
                )}
                
                {isFastAgent && (
                  <>
                    <FormControl fullWidth margin="normal">
                      <InputLabel id="provider-label">Provider</InputLabel>
                      <Select
                        labelId="provider-label"
                        id="provider"
                        name="metadata.provider"
                        value={editedSystem.metadata?.provider || 'openai'}
                        onChange={handleChange}
                        label="Provider"
                      >
                        <MenuItem value="openai">OpenAI</MenuItem>
                        <MenuItem value="anthropic">Anthropic</MenuItem>
                        <MenuItem value="meta">Meta</MenuItem>
                        <MenuItem value="custom">Custom</MenuItem>
                      </Select>
                    </FormControl>
                    <TextField
                      fullWidth
                      label="MCP Servers"
                      name="metadata.mcpServers"
                      value={editedSystem.metadata?.mcpServers || ''}
                      onChange={handleChange}
                      margin="normal"
                      helperText="Comma-separated list of MCP server names"
                    />
                  </>
                )}
              </Grid>
            </Grid>
          ) : (
            <Box>
              <Typography variant="subtitle1">Connection Details</Typography>
              <Typography variant="body2">
                <strong>URL:</strong> {system.url}
              </Typography>
              <Typography variant="body2">
                <strong>Authentication:</strong> {system.authType}
              </Typography>
              
              {/* System-specific details */}
              {isAIOrchestrator && (
                <>
                  <Divider sx={{ my: 2 }} />
                  <Typography variant="subtitle1">Orchestrator Configuration</Typography>
                  <Typography variant="body2">
                    <strong>Mode:</strong> {system.metadata?.orchestratorMode || 'Standard'}
                  </Typography>
                  <Typography variant="body2">
                    <strong>Task Distribution:</strong> {system.metadata?.taskDistributionStrategy || 'Round Robin'}
                  </Typography>
                  <Typography variant="body2">
                    <strong>Max Agents:</strong> {system.metadata?.maxAgents || 10}
                  </Typography>
                </>
              )}
              
              {isFastAgent && (
                <>
                  <Divider sx={{ my: 2 }} />
                  <Typography variant="subtitle1">Fast-Agent Configuration</Typography>
                  <Typography variant="body2">
                    <strong>Default Model:</strong> {system.metadata?.defaultModel || 'GPT-4'}
                  </Typography>
                  <Typography variant="body2">
                    <strong>Provider:</strong> {system.metadata?.provider || 'OpenAI'}
                  </Typography>
                  {system.metadata?.mcpServers && (
                    <Typography variant="body2">
                      <strong>MCP Servers:</strong> {system.metadata.mcpServers}
                    </Typography>
                  )}
                </>
              )}
              
              <Divider sx={{ my: 2 }} />
              <Button
                variant="outlined"
                color="primary"
                onClick={() => onTestConnection(system.id)}
                sx={{ mt: 1 }}
              >
                Test Connection
              </Button>
            </Box>
          )}
        </CardContent>
      </Collapse>
    </Card>
  );
};

export default SystemEndpointCard;
