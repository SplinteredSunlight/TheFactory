# AI-Orchestration-Platform System Prompt

## Project Overview

The AI-Orchestration-Platform is a comprehensive system designed to integrate and orchestrate AI agents and workflows. It provides a unified interface for managing tasks, distributing work, and monitoring results across multiple AI systems. The platform includes integration between AI-Orchestrator and Fast-Agent systems, with a focus on containerized workflows using Dagger.

## Key Documentation

### Project Planning
- [Consolidated Project Plan](../planning/consolidated-project-plan.md): The single source of truth for project status, phases, and roadmap
- [Task Templates](../planning/task-templates/): Templates for common tasks

### System Documentation
- [Architecture Overview](../system/components/architecture.md): High-level architecture of the system
- [API Documentation](../system/api/api-contracts.md): API contracts and interfaces
- [Integration Documentation](../system/integration/integration-plan.md): Integration points and strategies

### User and Developer Guides
- [Task Management Guide](../guides/TASK_MANAGER_MCP_README.md): Guide for using the Task Management MCP server
- [Dagger Integration Guide](../guides/DAGGER_WORKFLOW_INTEGRATION_README.md): Guide for Dagger workflow integration
- [Error Handling Protocol](../guides/error-handling-protocol.md): Protocol for handling errors

### Project Wiki
- [Wiki Structure](../wiki/structure.md): Structure of the project wiki
- [Architectural Decision Records](../wiki/adr/): Records of architectural decisions
- [Development Journal](../wiki/journal/): Journal of development activities

## Project Structure

The AI-Orchestration-Platform is organized into the following components:

### Core Components
- **Orchestrator**: Core orchestration system for managing tasks and workflows
- **Agent Manager**: System for managing and communicating with AI agents
- **Task Manager**: System for tracking and managing tasks
- **Frontend**: User interface for interacting with the system

### Integration Components
- **Fast Agent Integration**: Integration with the Fast-Agent system
- **Dagger Integration**: Integration with the Dagger containerized workflow system
- **MCP Servers**: Model Context Protocol servers for extending capabilities

### Support Components
- **API**: RESTful API for interacting with the system
- **Monitoring**: System for monitoring and observability
- **Testing**: Framework for testing the system

## Guidelines for Working with the Project

1. **Documentation First**: Always check the documentation before making changes
2. **Follow the Architecture**: Adhere to the established architectural patterns
3. **Test Thoroughly**: Write tests for all new functionality
4. **Document Changes**: Update documentation to reflect changes
5. **Use the Task Management System**: Track all work using the Task Management system

## Common Tasks

### Running the System
```bash
# Start the orchestrator
cd src/orchestrator
python engine.py

# Start the agent manager
cd src/agent_manager
python adapter.py

# Start the frontend
cd src/frontend
npm start
```

### Working with Tasks
```bash
# Create a new task
./task-cli create-task --name "Task Name" --description "Task Description" --project-id project_123 --phase-id phase_123

# Update task status
./task-cli update-task-status --task-id task_123 --status in_progress

# Calculate project progress
./task-cli calculate-project-progress --project-id project_123
```

### Working with Dagger
```bash
# Run a Dagger workflow
./run_dagger_workflow_example.sh

# Verify Dagger integration
./verify_dagger_workflow_integration.py
```

## Current Status

The project is currently in the "Task Management MCP Server" phase with "Dagger Workflow Integration" as the current active task. The system has completed the integration setup, orchestrator enhancements, agent integration, and frontend integration phases.

## Next Steps

1. Complete Dagger Workflow Integration
2. Implement Documentation Dashboard
3. Enhance Project Wiki
4. Implement Development Journal System

This system prompt provides context for working with the AI-Orchestration-Platform. It should be included when invoking Claude to ensure it has the necessary context to assist with the project.
