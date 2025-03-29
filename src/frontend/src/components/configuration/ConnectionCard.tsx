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
  List,
  ListItem,
  ListItemText,
  ListItemSecondaryAction,
  Tooltip,
  Alert,
} from '@mui/material';
import {
  Edit as EditIcon,
  Delete as DeleteIcon,
  ExpandMore as ExpandMoreIcon,
  Check as CheckIcon,
  Close as CloseIcon,
  Add as AddIcon,
  Sync as SyncIcon,
  Code as CodeIcon,
  Api as ApiIcon,
  Settings as SettingsIcon,
  ArrowForward as ArrowForwardIcon,
  SwapHoriz as SwapHorizIcon,
} from '@mui/icons-material';
import { styled } from '@mui/material/styles';
import { SystemConnection, SystemEndpoint } from '../../store/slices/configurationSlice';
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

interface ConnectionCardProps {
  connection: SystemConnection;
  systems: SystemEndpoint[];
  onToggleEnabled: (id: string) => void;
  onUpdate: (connection: SystemConnection) => void;
  onDelete: (id: string) => void;
  onTestConnection: (id: string) => void;
  onSyncNow: (id: string) => void;
}

const ConnectionCard: React.FC<ConnectionCardProps> = ({
  connection,
  systems,
  onToggleEnabled,
  onUpdate,
  onDelete,
  onTestConnection,
  onSyncNow,
}) => {
  const [expanded, setExpanded] = useState(false);
  const [editing, setEditing] = useState(false);
  const [editedConnection, setEditedConnection] = useState<SystemConnection>({ ...connection });
  const [newMapping, setNewMapping] = useState({ sourceField: '', targetField: '', transformationType: 'none' as const });

  const sourceSystem = systems.find(system => system.id === connection.sourceSystemId);
  const targetSystem = systems.find(system => system.id === connection.targetSystemId);

  // Determine if this is an AI-Orchestrator to Fast-Agent connection
  const isOrchestratorToFastAgent = 
    (sourceSystem?.id === 'orchestrator' || sourceSystem?.name.toLowerCase().includes('orchestrator')) &&
    (targetSystem?.id === 'fast-agent' || targetSystem?.name.toLowerCase().includes('fast-agent'));
  
  // Determine if this is a Fast-Agent to AI-Orchestrator connection
  const isFastAgentToOrchestrator = 
    (sourceSystem?.id === 'fast-agent' || sourceSystem?.name.toLowerCase().includes('fast-agent')) &&
    (targetSystem?.id === 'orchestrator' || targetSystem?.name.toLowerCase().includes('orchestrator'));
  
  // Determine if this is a cross-system connection between our main systems
  const isCrossSystemConnection = isOrchestratorToFastAgent || isFastAgentToOrchestrator;

  const handleExpandClick = () => {
    setExpanded(!expanded);
  };

  const handleEditClick = () => {
    setEditedConnection({ ...connection });
    setEditing(true);
    setExpanded(true);
  };

  const handleCancelEdit = () => {
    setEditing(false);
  };

  const handleSaveEdit = () => {
    onUpdate(editedConnection);
    setEditing(false);
  };

  const handleChange = (e: React.ChangeEvent<HTMLInputElement | { name?: string; value: unknown }>) => {
    const { name, value } = e.target;
    if (name) {
      if (name.startsWith('metadata.')) {
        const metadataField = name.split('.')[1];
        setEditedConnection({
          ...editedConnection,
          metadata: {
            ...editedConnection.metadata,
            [metadataField]: value,
          },
        });
      } else {
        setEditedConnection({
          ...editedConnection,
          [name]: value,
        });
      }
    }
  };

  const handleAddMapping = () => {
    if (newMapping.sourceField && newMapping.targetField) {
      const newMappingWithId = {
        ...newMapping,
        id: `mapping-${Date.now()}`,
      };
      setEditedConnection({
        ...editedConnection,
        dataMapping: [...editedConnection.dataMapping, newMappingWithId],
      });
      setNewMapping({ sourceField: '', targetField: '', transformationType: 'none' });
    }
  };

  const handleRemoveMapping = (id: string) => {
    setEditedConnection({
      ...editedConnection,
      dataMapping: editedConnection.dataMapping.filter(mapping => mapping.id !== id),
    });
  };

  const handleMappingChange = (e: React.ChangeEvent<HTMLInputElement | { name?: string; value: unknown }>, index: number) => {
    const { name, value } = e.target;
    if (name) {
      const updatedMappings = [...editedConnection.dataMapping];
      updatedMappings[index] = {
        ...updatedMappings[index],
        [name.split('.')[1]]: value,
      };
      setEditedConnection({
        ...editedConnection,
        dataMapping: updatedMappings,
      });
    }
  };

  const handleNewMappingChange = (e: React.ChangeEvent<HTMLInputElement | { name?: string; value: unknown }>) => {
    const { name, value } = e.target;
    if (name) {
      setNewMapping({
        ...newMapping,
        [name.split('.')[1]]: value,
      });
    }
  };

  // Add predefined mappings for AI-Orchestrator and Fast-Agent
  const addPredefinedMappings = () => {
    const predefinedMappings = [
      {
        id: `mapping-${Date.now()}-1`,
        sourceField: 'task',
        targetField: 'task',
        transformationType: 'none' as const,
      },
      {
        id: `mapping-${Date.now()}-2`,
        sourceField: 'result',
        targetField: 'result',
        transformationType: 'none' as const,
      },
      {
        id: `mapping-${Date.now()}-3`,
        sourceField: 'agent',
        targetField: 'agent',
        transformationType: 'none' as const,
      },
    ];
    
    setEditedConnection({
      ...editedConnection,
      dataMapping: [...editedConnection.dataMapping, ...predefinedMappings],
    });
  };

  return (
    <Card variant="outlined" sx={{ mb: 2 }}>
      <CardHeader
        title={
          <Box display="flex" alignItems="center">
            <Typography variant="h6" component="div">
              {sourceSystem?.name} {connection.connectionType === 'one-way' ? 
                <ArrowForwardIcon fontSize="small" sx={{ verticalAlign: 'middle' }} /> : 
                <SwapHorizIcon fontSize="small" sx={{ verticalAlign: 'middle' }} />
              } {targetSystem?.name}
            </Typography>
            <FormControlLabel
              control={
                <Switch
                  checked={connection.enabled}
                  onChange={() => onToggleEnabled(connection.id)}
                  color="primary"
                  disabled={editing}
                />
              }
              label={connection.enabled ? 'Enabled' : 'Disabled'}
              sx={{ ml: 2 }}
            />
            <Chip
              label={connection.connectionType === 'one-way' ? 'One-way' : 'Two-way'}
              color="primary"
              size="small"
              sx={{ ml: 2 }}
            />
            {isCrossSystemConnection && (
              <Tooltip title="AI-Orchestration Platform Integration">
                <Chip
                  icon={<ApiIcon fontSize="small" />}
                  label="Cross-System"
                  color="secondary"
                  size="small"
                  sx={{ ml: 2 }}
                />
              </Tooltip>
            )}
          </Box>
        }
        action={
          <Box>
            {!editing && (
              <>
                <IconButton aria-label="sync now" onClick={() => onSyncNow(connection.id)} color="primary">
                  <SyncIcon />
                </IconButton>
                <IconButton aria-label="edit" onClick={handleEditClick}>
                  <EditIcon />
                </IconButton>
                <IconButton aria-label="delete" onClick={() => onDelete(connection.id)}>
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
            Sync interval: {connection.syncInterval} minutes
          </Typography>
        }
      />
      <Collapse in={expanded} timeout="auto" unmountOnExit>
        <CardContent>
          {editing ? (
            <Grid container spacing={2}>
              <Grid item xs={12} md={6}>
                <FormControl fullWidth margin="normal">
                  <InputLabel id="source-system-label">Source System</InputLabel>
                  <Select
                    labelId="source-system-label"
                    id="source-system"
                    name="sourceSystemId"
                    value={editedConnection.sourceSystemId}
                    onChange={handleChange}
                    label="Source System"
                  >
                    {systems.map(system => (
                      <MenuItem key={system.id} value={system.id}>
                        {system.name}
                      </MenuItem>
                    ))}
                  </Select>
                </FormControl>
                <FormControl fullWidth margin="normal">
                  <InputLabel id="target-system-label">Target System</InputLabel>
                  <Select
                    labelId="target-system-label"
                    id="target-system"
                    name="targetSystemId"
                    value={editedConnection.targetSystemId}
                    onChange={handleChange}
                    label="Target System"
                  >
                    {systems.map(system => (
                      <MenuItem key={system.id} value={system.id}>
                        {system.name}
                      </MenuItem>
                    ))}
                  </Select>
                </FormControl>
                <FormControl fullWidth margin="normal">
                  <InputLabel id="connection-type-label">Connection Type</InputLabel>
                  <Select
                    labelId="connection-type-label"
                    id="connection-type"
                    name="connectionType"
                    value={editedConnection.connectionType}
                    onChange={handleChange}
                    label="Connection Type"
                  >
                    <MenuItem value="one-way">One-way</MenuItem>
                    <MenuItem value="two-way">Two-way</MenuItem>
                  </Select>
                </FormControl>
                <TextField
                  fullWidth
                  label="Sync Interval (minutes)"
                  name="syncInterval"
                  type="number"
                  value={editedConnection.syncInterval}
                  onChange={handleChange}
                  margin="normal"
                  inputProps={{ min: 1 }}
                />
                
                {/* Cross-system specific fields */}
                {isCrossSystemConnection && (
                  <>
                    <Divider sx={{ my: 2 }} />
                    <Typography variant="subtitle1" gutterBottom>
                      Cross-System Configuration
                    </Typography>
                    
                    <FormControl fullWidth margin="normal">
                      <InputLabel id="sync-strategy-label">Sync Strategy</InputLabel>
                      <Select
                        labelId="sync-strategy-label"
                        id="sync-strategy"
                        name="metadata.syncStrategy"
                        value={editedConnection.metadata?.syncStrategy || 'incremental'}
                        onChange={handleChange}
                        label="Sync Strategy"
                      >
                        <MenuItem value="incremental">Incremental</MenuItem>
                        <MenuItem value="full">Full</MenuItem>
                        <MenuItem value="delta">Delta</MenuItem>
                      </Select>
                    </FormControl>
                    
                    <FormControl fullWidth margin="normal">
                      <InputLabel id="conflict-resolution-label">Conflict Resolution</InputLabel>
                      <Select
                        labelId="conflict-resolution-label"
                        id="conflict-resolution"
                        name="metadata.conflictResolution"
                        value={editedConnection.metadata?.conflictResolution || 'source-wins'}
                        onChange={handleChange}
                        label="Conflict Resolution"
                      >
                        <MenuItem value="source-wins">Source Wins</MenuItem>
                        <MenuItem value="target-wins">Target Wins</MenuItem>
                        <MenuItem value="newest-wins">Newest Wins</MenuItem>
                        <MenuItem value="manual">Manual Resolution</MenuItem>
                      </Select>
                    </FormControl>
                    
                    <Button
                      variant="outlined"
                      startIcon={<AddIcon />}
                      onClick={addPredefinedMappings}
                      sx={{ mt: 2 }}
                    >
                      Add Predefined Mappings
                    </Button>
                  </>
                )}
              </Grid>
              <Grid item xs={12} md={6}>
                <Typography variant="subtitle1" gutterBottom>
                  Data Mapping
                </Typography>
                <List>
                  {editedConnection.dataMapping.map((mapping, index) => (
                    <ListItem key={mapping.id}>
                      <Grid container spacing={1}>
                        <Grid item xs={5}>
                          <TextField
                            fullWidth
                            label="Source Field"
                            name={`mapping.sourceField`}
                            value={mapping.sourceField}
                            onChange={(e) => handleMappingChange(e, index)}
                            size="small"
                          />
                        </Grid>
                        <Grid item xs={5}>
                          <TextField
                            fullWidth
                            label="Target Field"
                            name={`mapping.targetField`}
                            value={mapping.targetField}
                            onChange={(e) => handleMappingChange(e, index)}
                            size="small"
                          />
                        </Grid>
                        <Grid item xs={2}>
                          <IconButton
                            edge="end"
                            aria-label="delete"
                            onClick={() => handleRemoveMapping(mapping.id)}
                          >
                            <DeleteIcon />
                          </IconButton>
                        </Grid>
                      </Grid>
                    </ListItem>
                  ))}
                  <ListItem>
                    <Grid container spacing={1}>
                      <Grid item xs={5}>
                        <TextField
                          fullWidth
                          label="Source Field"
                          name="mapping.sourceField"
                          value={newMapping.sourceField}
                          onChange={handleNewMappingChange}
                          size="small"
                        />
                      </Grid>
                      <Grid item xs={5}>
                        <TextField
                          fullWidth
                          label="Target Field"
                          name="mapping.targetField"
                          value={newMapping.targetField}
                          onChange={handleNewMappingChange}
                          size="small"
                        />
                      </Grid>
                      <Grid item xs={2}>
                        <IconButton
                          edge="end"
                          aria-label="add"
                          onClick={handleAddMapping}
                          color="primary"
                        >
                          <AddIcon />
                        </IconButton>
                      </Grid>
                    </Grid>
                  </ListItem>
                </List>
                
                {isCrossSystemConnection && (
                  <Alert severity="info" sx={{ mt: 2 }}>
                    This is a cross-system connection between AI-Orchestrator and Fast-Agent. 
                    Predefined mappings are available for common fields.
                  </Alert>
                )}
              </Grid>
            </Grid>
          ) : (
            <Box>
              <Typography variant="subtitle1">Connection Details</Typography>
              <Typography variant="body2">
                <strong>Source System:</strong> {sourceSystem?.name}
              </Typography>
              <Typography variant="body2">
                <strong>Target System:</strong> {targetSystem?.name}
              </Typography>
              <Typography variant="body2">
                <strong>Connection Type:</strong> {connection.connectionType === 'one-way' ? 'One-way' : 'Two-way'}
              </Typography>
              <Typography variant="body2">
                <strong>Sync Interval:</strong> {connection.syncInterval} minutes
              </Typography>
              
              {/* Cross-system specific details */}
              {isCrossSystemConnection && (
                <>
                  <Divider sx={{ my: 2 }} />
                  <Typography variant="subtitle1">Cross-System Configuration</Typography>
                  <Typography variant="body2">
                    <strong>Sync Strategy:</strong> {connection.metadata?.syncStrategy || 'Incremental'}
                  </Typography>
                  <Typography variant="body2">
                    <strong>Conflict Resolution:</strong> {connection.metadata?.conflictResolution || 'Source Wins'}
                  </Typography>
                  <Alert severity="info" sx={{ mt: 2, mb: 2 }}>
                    This connection enables seamless integration between AI-Orchestrator and Fast-Agent systems.
                  </Alert>
                </>
              )}
              
              <Divider sx={{ my: 2 }} />
              
              <Typography variant="subtitle1">Data Mapping</Typography>
              <List dense>
                {connection.dataMapping.map(mapping => (
                  <ListItem key={mapping.id}>
                    <ListItemText
                      primary={`${mapping.sourceField} → ${mapping.targetField}`}
                      secondary={`Transformation: ${mapping.transformationType}`}
                    />
                  </ListItem>
                ))}
              </List>
              
              <Divider sx={{ my: 2 }} />
              
              <Box sx={{ display: 'flex', gap: 2 }}>
                <Button
                  variant="outlined"
                  color="primary"
                  onClick={() => onTestConnection(connection.id)}
                >
                  Test Connection
                </Button>
                <Button
                  variant="contained"
                  color="primary"
                  startIcon={<SyncIcon />}
                  onClick={() => onSyncNow(connection.id)}
                >
                  Sync Now
                </Button>
              </Box>
            </Box>
          )}
        </CardContent>
      </Collapse>
    </Card>
  );
};

export default ConnectionCard;
