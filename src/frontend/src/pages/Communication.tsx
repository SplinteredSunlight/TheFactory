import React, { useEffect, useState } from 'react';
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
  TextField,
  MenuItem,
  Select,
  FormControl,
  InputLabel,
  SelectChangeEvent,
  useTheme,
} from '@mui/material';
import {
  Refresh as RefreshIcon,
  Send as SendIcon,
  FilterList as FilterListIcon,
  Search as SearchIcon,
  Message as MessageIcon,
  CheckCircle as CheckCircleIcon,
  Error as ErrorIcon,
  Warning as WarningIcon,
  Info as InfoIcon,
  Broadcast as BroadcastIcon,
  Assignment as AssignmentIcon,
} from '@mui/icons-material';
import { RootState } from '../store';
import { Message } from '../store/slices/communicationSlice';
import { Agent } from '../types/agent';

const Communication: React.FC = () => {
  const dispatch = useDispatch();
  const theme = useTheme();
  
  // Get data from Redux store
  const { messages, isLoading } = useSelector((state: RootState) => state.communication);
  const { agents } = useSelector((state: RootState) => state.agents);

  // Local state for new message
  const [messageText, setMessageText] = useState('');
  const [messageType, setMessageType] = useState<Message['messageType']>('direct');
  const [recipientId, setRecipientId] = useState('');
  const [priority, setPriority] = useState<Message['priority']>('medium');

  // Fetch data on component mount
  useEffect(() => {
    // In a real application, we would dispatch actions to fetch messages and agents
    // dispatch(fetchMessages());
    // dispatch(fetchAgents());
  }, [dispatch]);

  // Handle message type change
  const handleMessageTypeChange = (event: SelectChangeEvent) => {
    setMessageType(event.target.value as Message['messageType']);
    // If changing to broadcast, clear recipient
    if (event.target.value === 'broadcast') {
      setRecipientId('');
    }
  };

  // Handle recipient change
  const handleRecipientChange = (event: SelectChangeEvent) => {
    setRecipientId(event.target.value);
  };

  // Handle priority change
  const handlePriorityChange = (event: SelectChangeEvent) => {
    setPriority(event.target.value as Message['priority']);
  };

  // Handle message text change
  const handleMessageTextChange = (event: React.ChangeEvent<HTMLInputElement>) => {
    setMessageText(event.target.value);
  };

  // Handle send message
  const handleSendMessage = () => {
    if (!messageText) return;

    // In a real application, we would dispatch an action to send the message
    // dispatch(sendMessage({
    //   messageType,
    //   content: messageText,
    //   recipientId: messageType === 'broadcast' ? null : recipientId,
    //   priority,
    // }));

    // Clear the message text
    setMessageText('');
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
      case 'direct':
        return <MessageIcon color="primary" />;
      default:
        return <MessageIcon color="primary" />;
    }
  };

  // Helper function to get message type color
  const getMessageTypeColor = (type: Message['messageType']) => {
    switch (type) {
      case 'error':
        return theme.palette.error.main;
      case 'task_response':
        return theme.palette.success.main;
      case 'task_request':
        return theme.palette.primary.main;
      case 'status_update':
        return theme.palette.info.main;
      case 'broadcast':
        return theme.palette.warning.main;
      case 'direct':
        return theme.palette.primary.main;
      default:
        return theme.palette.primary.main;
    }
  };

  return (
    <Box sx={{ flexGrow: 1 }}>
      <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 3 }}>
        <Typography variant="h4" component="h1">
          Communication
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
        </Box>
      </Box>

      <Grid container spacing={3}>
        {/* Message Composer */}
        <Grid item xs={12}>
          <Paper sx={{ p: 2 }}>
            <Typography variant="h6" gutterBottom>
              Send Message
            </Typography>
            <Grid container spacing={2}>
              <Grid item xs={12} sm={6} md={3}>
                <FormControl fullWidth>
                  <InputLabel id="message-type-label">Message Type</InputLabel>
                  <Select
                    labelId="message-type-label"
                    id="message-type"
                    value={messageType}
                    label="Message Type"
                    onChange={handleMessageTypeChange}
                  >
                    <MenuItem value="direct">Direct Message</MenuItem>
                    <MenuItem value="broadcast">Broadcast</MenuItem>
                    <MenuItem value="task_request">Task Request</MenuItem>
                    <MenuItem value="status_update">Status Update</MenuItem>
                  </Select>
                </FormControl>
              </Grid>
              {messageType !== 'broadcast' && (
                <Grid item xs={12} sm={6} md={3}>
                  <FormControl fullWidth>
                    <InputLabel id="recipient-label">Recipient</InputLabel>
                    <Select
                      labelId="recipient-label"
                      id="recipient"
                      value={recipientId}
                      label="Recipient"
                      onChange={handleRecipientChange}
                    >
                      {agents.map((agent) => (
                        <MenuItem key={agent.id} value={agent.id}>
                          {agent.name}
                        </MenuItem>
                      ))}
                    </Select>
                  </FormControl>
                </Grid>
              )}
              <Grid item xs={12} sm={6} md={3}>
                <FormControl fullWidth>
                  <InputLabel id="priority-label">Priority</InputLabel>
                  <Select
                    labelId="priority-label"
                    id="priority"
                    value={priority}
                    label="Priority"
                    onChange={handlePriorityChange}
                  >
                    <MenuItem value="high">High</MenuItem>
                    <MenuItem value="medium">Medium</MenuItem>
                    <MenuItem value="low">Low</MenuItem>
                  </Select>
                </FormControl>
              </Grid>
              <Grid item xs={12}>
                <TextField
                  fullWidth
                  id="message"
                  label="Message"
                  multiline
                  rows={4}
                  value={messageText}
                  onChange={handleMessageTextChange}
                />
              </Grid>
              <Grid item xs={12}>
                <Button
                  variant="contained"
                  endIcon={<SendIcon />}
                  onClick={handleSendMessage}
                  disabled={!messageText || (messageType !== 'broadcast' && !recipientId)}
                >
                  Send
                </Button>
              </Grid>
            </Grid>
          </Paper>
        </Grid>

        {/* Message List */}
        <Grid item xs={12}>
          <Paper sx={{ p: 2 }}>
            <Typography variant="h6" gutterBottom>
              Message History
            </Typography>
            {isLoading ? (
              <CircularProgress sx={{ display: 'block', mx: 'auto', my: 4 }} />
            ) : (
              <List>
                {messages.length > 0 ? (
                  messages.map((message) => (
                    <React.Fragment key={message.id}>
                      <ListItem
                        alignItems="flex-start"
                        secondaryAction={
                          <Chip
                            label={message.priority}
                            size="small"
                            color={
                              message.priority === 'high' ? 'error' :
                              message.priority === 'medium' ? 'warning' : 'info'
                            }
                          />
                        }
                      >
                        <ListItemAvatar>
                          <Avatar sx={{ bgcolor: getMessageTypeColor(message.messageType) }}>
                            {getMessageTypeIcon(message.messageType)}
                          </Avatar>
                        </ListItemAvatar>
                        <ListItemText
                          primary={
                            <Typography variant="subtitle1">
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
                              <Typography variant="body2" sx={{ mt: 1 }}>
                                {typeof message.content === 'string' 
                                  ? message.content 
                                  : JSON.stringify(message.content, null, 2)}
                              </Typography>
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
                      primary="No messages found"
                      secondary="Send a message to get started"
                    />
                  </ListItem>
                )}
              </List>
            )}
          </Paper>
        </Grid>
      </Grid>
    </Box>
  );
};

export default Communication;
