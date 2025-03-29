# AI-Orchestration-Platform

## Overview

The AI-Orchestration-Platform is an integration project that combines the capabilities of AI-Orchestrator and Fast-Agent frameworks to create a powerful, unified platform for AI workflow management and execution. This platform streamlines the development, deployment, and monitoring of AI applications by providing a comprehensive set of tools and services.

## Features

- **Unified Workflow Management**: Seamlessly integrate AI-Orchestrator and Fast-Agent capabilities
- **Containerized Workflows**: Execute workflows in isolated containers using Dagger
- **Self-Healing System**: Automatically recover from failures with retry mechanisms and circuit breakers
- **Comprehensive Visualization**: Monitor and visualize workflows, tasks, and system performance
- **Intelligent Task Routing**: Automatically direct tasks to the most appropriate AI agents
- **Scalable Architecture**: Designed to handle varying workloads efficiently
- **Security-First Design**: Built with robust security measures to protect sensitive data
- **Cross-Platform Compatibility**: Works across different environments and infrastructures

## Project Structure

The project is organized into the following directories:

```
AI-Orchestration-Platform/
├── archive/                  # Archived files and legacy components
├── config/                   # Configuration files and templates
├── dashboard/                # Dashboard frontend code
├── docs/                     # Documentation
│   ├── planning/             # Project planning documents
│   ├── architecture/         # Architecture documentation
│   └── user_guides/          # User guides and tutorials
├── src/                      # Source code
│   ├── agent_manager/        # Agent management code
│   ├── api/                  # API definitions
│   ├── fast_agent_integration/ # Fast-Agent integration
│   ├── orchestrator/         # Orchestration logic
│   └── task_manager/         # Task management
├── tasks/                    # Project tasks
│   ├── active/               # Active tasks
│   ├── backlog/              # Backlog tasks
│   └── completed/            # Completed tasks (for reference)
└── tests/                    # Tests
    ├── unit/                 # Unit tests
    ├── integration/          # Integration tests
    └── performance/          # Performance tests
```

## Architecture

The AI-Orchestration-Platform follows a modular, microservices-based architecture that enables flexibility and scalability:

```
AI-Orchestration-Platform
├── Core Services
│   ├── Orchestration Engine
│   ├── Agent Manager
│   └── Task Scheduler
├── Integration Layer
│   ├── AI-Orchestrator Connector
│   ├── Fast-Agent Connector
│   └── External API Gateway
├── Data Management
│   ├── Context Store
│   ├── Model Registry
│   └── Results Cache
└── User Interfaces
    ├── Admin Dashboard
    ├── Developer Console
    ├── Monitoring Tools
    └── Cross-System Configuration UI
```

## Components

### Orchestration Engine

The Orchestration Engine is responsible for managing workflows and tasks. It coordinates the execution of tasks across different agents and ensures that dependencies are satisfied. It now includes Dagger integration for containerized workflow execution.

### Agent Manager

The Agent Manager is responsible for registering, discovering, and executing AI agents. It provides a unified interface for working with different types of agents, including Fast-Agent and AI-Orchestrator agents.

### Fast-Agent Integration

The Fast-Agent Integration module provides a bridge between the AI-Orchestration-Platform and the Fast-Agent framework. It allows the platform to create, manage, and execute Fast-Agent agents through a standardized adapter interface.

### Dashboard

The Dashboard provides a unified interface for monitoring and managing the AI-Orchestration-Platform. It includes real-time visualization of workflows, task status, and system performance.

### Dagger Integration

The Dagger Integration module provides support for containerized workflow execution using Dagger.io. It enables reliable, reproducible, and isolated execution of workflows in containers.

## Setup

### Prerequisites

- Docker and Docker Compose
- Python 3.9+
- Node.js 16+
- Git

### Installation

1. Clone the repository:
   ```bash
   git clone https://github.com/SplinteredSunlight/AI-Orchestration-Platform.git
   cd AI-Orchestration-Platform
   ```

2. Set up the environment:
   ```bash
   # Copy example environment files
   cp config/example.env config/.env
   
   # Install dependencies
   pip install -r requirements.txt
   cd dashboard && npm install && cd ..
   ```

3. Start the services:
   ```bash
   docker-compose up -d
   ```

4. Access the platform:
   - Admin Dashboard: http://localhost:8080
   - API Endpoint: http://localhost:8000/api/v1

## Development

### Running Tests

```bash
# Run unit tests
python -m pytest tests/unit

# Run integration tests
python -m pytest tests/integration

# Run performance tests
python -m pytest tests/performance
```

### Building Documentation

```bash
# Generate documentation
cd docs
python -m sphinx.cmd.build -b html source build/html
```

## Roadmap

See [Project Roadmap](docs/planning/project-roadmap.md) for the current development plan and status.

## Contributing

We welcome contributions to the AI-Orchestration-Platform! Please see our [Contributing Guide](CONTRIBUTING.md) for more information.

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.
