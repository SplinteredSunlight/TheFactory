/**
 * Agent Configuration Examples
 * 
 * This component demonstrates how to use the unified agent configuration schema
 * to create and manage agents from both AI-Orchestrator and Fast-Agent frameworks.
 */

import React, { useState } from 'react';
import { 
  Box, 
  Typography, 
  Paper, 
  Divider, 
  Button, 
  TextField, 
  FormControl, 
  InputLabel, 
  Select, 
  MenuItem, 
  Chip, 
  Grid,
  Card,
  CardContent,
  CardHeader,
  List,
  ListItem,
  ListItemText
} from '@mui/material';

import { 
  Agent, 
  AgentConfig, 
  AgentFramework, 
  AgentStatus, 
  AgentCapability,
  AIOrchestrationConfig,
  FastAgentConfig,
  createAIOrchestrationAgent,
  createFastAgentAgent,
  configToAgent,
  agentToConfig
} from '../types/agent';

const AgentConfigExamples: React.FC = () => {
  // State for the selected example
  const [selectedExample, setSelectedExample] = useState<string>('create-ai-orchestrator');
  const [agentConfig, setAgentConfig] = useState<AgentConfig | null>(null);
  const [agent, setAgent] = useState<Agent | null>(null);
  const [jsonOutput, setJsonOutput] = useState<string>('');

  // Example 1: Create an AI-Orchestrator agent
  const createAIOrchestrationAgentExample = () => {
    const config = createAIOrchestrationAgent(
      "Data Analyzer",
      "An agent that specializes in data analysis and visualization",
      "http://localhost:8000/api/v1",
      [
        AgentCapability.TEXT_PROCESSING,
        AgentCapability.DATA_EXTRACTION,
        AgentCapability.IMAGE_ANALYSIS
      ]
    );

    // Add additional metadata
    config.config.metadata = {
      specialization: "data_analysis",
      supported_formats: ["csv", "json", "xlsx"],
      max_file_size_mb: 10
    };

    setAgentConfig(config);
    setAgent(configToAgent(config));
    setJsonOutput(JSON.stringify(config, null, 2));
  };

  // Example 2: Create a Fast-Agent agent
  const createFastAgentAgentExample = () => {
    const config = createFastAgentAgent(
      "Code Assistant",
      "An agent that helps with code generation and review",
      "You are a helpful coding assistant that specializes in generating and reviewing code. Focus on best practices, readability, and performance.",
      "gpt-4",
      false,
      ["fetch", "filesystem", "github"]
    );

    // Add additional metadata
    config.config.metadata = {
      specialization: "code_assistance",
      supported_languages: ["python", "javascript", "typescript", "java"],
      context_window: 16000
    };

    setAgentConfig(config);
    setAgent(configToAgent(config));
    setJsonOutput(JSON.stringify(config, null, 2));
  };

  // Example 3: Convert between Agent and AgentConfig
  const convertBetweenAgentAndConfigExample = () => {
    // Create an agent
    const agent: Agent = {
      id: "fast-agent-qa-001",
      name: "QA Tester",
      description: "An agent that specializes in testing and quality assurance",
      framework: AgentFramework.FAST_AGENT,
      status: AgentStatus.IDLE,
      capabilities: [
        AgentCapability.TEXT_GENERATION,
        AgentCapability.REASONING
      ],
      createdAt: new Date().toISOString(),
      currentLoad: 0,
      priority: 2,
      metadata: {
        model: "gpt-4",
        useAnthropic: false,
        servers: ["fetch", "filesystem"],
        instruction: "You are a QA tester. Your job is to find bugs and issues in software.",
        specialization: "testing"
      }
    };

    // Convert to config
    const config = agentToConfig(agent);
    
    // Convert back to agent
    const reconvertedAgent = configToAgent(config);

    setAgent(agent);
    setAgentConfig(config);
    setJsonOutput(
      "Original Agent:\n" + 
      JSON.stringify(agent, null, 2) + 
      "\n\nConverted Config:\n" + 
      JSON.stringify(config, null, 2) + 
      "\n\nReconverted Agent:\n" + 
      JSON.stringify(reconvertedAgent, null, 2)
    );
  };

  // Example 4: Update agent status and metrics
  const updateAgentStatusAndMetricsExample = () => {
    // Create a Fast-Agent agent
    const config = createFastAgentAgent(
      "Language Translator",
      "An agent that specializes in language translation",
      "You are a language translation assistant. Translate text accurately between languages.",
      "gpt-4",
      false,
      ["fetch"]
    );

    // Update status and add metrics
    config.status = AgentStatus.BUSY;
    config.lastActive = new Date().toISOString();
    config.metrics = {
      memoryUsage: 256.5,
      cpuUsage: 12.3,
      requestsProcessed: 42,
      averageResponseTime: 0.85,
      lastUpdated: new Date().toISOString()
    };

    // Convert to agent
    const agent = configToAgent(config);

    setAgentConfig(config);
    setAgent(agent);
    setJsonOutput(JSON.stringify(config, null, 2));
  };

  // Run the selected example
  const runExample = () => {
    switch (selectedExample) {
      case 'create-ai-orchestrator':
        createAIOrchestrationAgentExample();
        break;
      case 'create-fast-agent':
        createFastAgentAgentExample();
        break;
      case 'convert-between':
        convertBetweenAgentAndConfigExample();
        break;
      case 'update-status-metrics':
        updateAgentStatusAndMetricsExample();
        break;
      default:
        break;
    }
  };

  return (
    <Box sx={{ p: 3 }}>
      <Typography variant="h4" gutterBottom>
        Agent Configuration Examples
      </Typography>
      <Typography variant="subtitle1" paragraph>
        This page demonstrates how to use the unified agent configuration schema in the frontend.
      </Typography>

      <Grid container spacing={3}>
        <Grid item xs={12} md={4}>
          <Paper sx={{ p: 2, mb: 3 }}>
            <Typography variant="h6" gutterBottom>
              Select an Example
            </Typography>
            <FormControl fullWidth sx={{ mb: 2 }}>
              <InputLabel id="example-select-label">Example</InputLabel>
              <Select
                labelId="example-select-label"
                id="example-select"
                value={selectedExample}
                label="Example"
                onChange={(e) => setSelectedExample(e.target.value)}
              >
                <MenuItem value="create-ai-orchestrator">Create AI-Orchestrator Agent</MenuItem>
                <MenuItem value="create-fast-agent">Create Fast-Agent Agent</MenuItem>
                <MenuItem value="convert-between">Convert Between Agent and Config</MenuItem>
                <MenuItem value="update-status-metrics">Update Status and Metrics</MenuItem>
              </Select>
            </FormControl>
            <Button 
              variant="contained" 
              fullWidth 
              onClick={runExample}
            >
              Run Example
            </Button>
          </Paper>

          {agent && (
            <Paper sx={{ p: 2 }}>
              <Typography variant="h6" gutterBottom>
                Agent Details
              </Typography>
              <List dense>
                <ListItem>
                  <ListItemText 
                    primary="ID" 
                    secondary={agent.id} 
                  />
                </ListItem>
                <ListItem>
                  <ListItemText 
                    primary="Name" 
                    secondary={agent.name} 
                  />
                </ListItem>
                <ListItem>
                  <ListItemText 
                    primary="Framework" 
                    secondary={agent.framework} 
                  />
                </ListItem>
                <ListItem>
                  <ListItemText 
                    primary="Status" 
                    secondary={agent.status} 
                  />
                </ListItem>
                <ListItem>
                  <ListItemText 
                    primary="Created At" 
                    secondary={new Date(agent.createdAt).toLocaleString()} 
                  />
                </ListItem>
                {agent.lastActive && (
                  <ListItem>
                    <ListItemText 
                      primary="Last Active" 
                      secondary={new Date(agent.lastActive).toLocaleString()} 
                    />
                  </ListItem>
                )}
                <ListItem>
                  <ListItemText 
                    primary="Priority" 
                    secondary={agent.priority} 
                  />
                </ListItem>
                <ListItem>
                  <ListItemText 
                    primary="Current Load" 
                    secondary={agent.currentLoad} 
                  />
                </ListItem>
                <ListItem>
                  <ListItemText 
                    primary="Capabilities" 
                    secondary={
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
                    } 
                  />
                </ListItem>
                {agent.metrics && (
                  <ListItem>
                    <ListItemText 
                      primary="Metrics" 
                      secondary={
                        <>
                          <Typography variant="body2">
                            Memory: {agent.metrics.memoryUsage} MB
                          </Typography>
                          <Typography variant="body2">
                            CPU: {agent.metrics.cpuUsage}%
                          </Typography>
                          <Typography variant="body2">
                            Requests: {agent.metrics.requestsProcessed}
                          </Typography>
                          <Typography variant="body2">
                            Avg Response: {agent.metrics.averageResponseTime}s
                          </Typography>
                        </>
                      } 
                    />
                  </ListItem>
                )}
              </List>
            </Paper>
          )}
        </Grid>

        <Grid item xs={12} md={8}>
          <Paper sx={{ p: 2, height: '100%' }}>
            <Typography variant="h6" gutterBottom>
              JSON Output
            </Typography>
            <Box 
              component="pre" 
              sx={{ 
                p: 2, 
                bgcolor: 'background.default', 
                borderRadius: 1,
                overflow: 'auto',
                maxHeight: '600px',
                '&::-webkit-scrollbar': {
                  width: '0.4em'
                },
                '&::-webkit-scrollbar-track': {
                  boxShadow: 'inset 0 0 6px rgba(0,0,0,0.00)',
                  webkitBoxShadow: 'inset 0 0 6px rgba(0,0,0,0.00)'
                },
                '&::-webkit-scrollbar-thumb': {
                  backgroundColor: 'rgba(0,0,0,.1)',
                  outline: '1px solid slategrey'
                }
              }}
            >
              {jsonOutput || 'Select an example and click "Run Example" to see the output.'}
            </Box>
          </Paper>
        </Grid>
      </Grid>
    </Box>
  );
};

export default AgentConfigExamples;
