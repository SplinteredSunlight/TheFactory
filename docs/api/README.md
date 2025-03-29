# API Documentation

This directory contains documentation for the API endpoints provided by the AI Orchestration Platform.

## API Overview

The AI Orchestration Platform provides a RESTful API for interacting with the platform. The API enables:

- Managing tasks and workflows
- Monitoring agent status and performance
- Configuring platform settings
- Executing workflows
- Retrieving results and logs

## API Endpoints

### Task Management

- `GET /api/tasks`: List all tasks
- `GET /api/tasks/{task_id}`: Get details of a specific task
- `POST /api/tasks`: Create a new task
- `PUT /api/tasks/{task_id}`: Update a task
- `DELETE /api/tasks/{task_id}`: Delete a task
- `GET /api/tasks/{task_id}/status`: Get the status of a task
- `POST /api/tasks/{task_id}/execute`: Execute a task

### Workflow Management

- `GET /api/workflows`: List all workflows
- `GET /api/workflows/{workflow_id}`: Get details of a specific workflow
- `POST /api/workflows`: Create a new workflow
- `PUT /api/workflows/{workflow_id}`: Update a workflow
- `DELETE /api/workflows/{workflow_id}`: Delete a workflow
- `GET /api/workflows/{workflow_id}/status`: Get the status of a workflow
- `POST /api/workflows/{workflow_id}/execute`: Execute a workflow

### Agent Management

- `GET /api/agents`: List all agents
- `GET /api/agents/{agent_id}`: Get details of a specific agent
- `POST /api/agents`: Register a new agent
- `PUT /api/agents/{agent_id}`: Update an agent
- `DELETE /api/agents/{agent_id}`: Unregister an agent
- `GET /api/agents/{agent_id}/status`: Get the status of an agent

### Dagger Integration

- `GET /api/dagger/workflows`: List all Dagger workflows
- `POST /api/dagger/workflows`: Create a new Dagger workflow
- `GET /api/dagger/workflows/{workflow_id}`: Get details of a specific Dagger workflow
- `POST /api/dagger/workflows/{workflow_id}/execute`: Execute a Dagger workflow

### Monitoring

- `GET /api/monitoring/metrics`: Get platform metrics
- `GET /api/monitoring/health`: Get platform health status
- `GET /api/monitoring/logs`: Get platform logs
- `GET /api/monitoring/progress`: Get progress of running tasks and workflows

### Authentication

- `POST /api/auth/login`: Authenticate and get a token
- `POST /api/auth/logout`: Invalidate a token
- `GET /api/auth/user`: Get information about the authenticated user
- `PUT /api/auth/user`: Update user information

## API Contracts

The API contracts are defined using the OpenAPI Specification (formerly Swagger). The full API specification is available in:

- `docs/api-contracts/dagger-api.yaml`: OpenAPI specification for the Dagger API
- `docs/api-contracts/error-handling.md`: Documentation for error handling in the API

## Authentication

The API uses token-based authentication. To authenticate:

1. Call the `/api/auth/login` endpoint with valid credentials
2. Receive a token in the response
3. Include the token in the `Authorization` header of subsequent requests

Example:

```
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
```

## Error Handling

The API follows a consistent error handling pattern. All errors return:

- An appropriate HTTP status code
- A JSON response with error details

Example error response:

```json
{
  "error": {
    "code": "INVALID_INPUT",
    "message": "Invalid input parameters",
    "details": {
      "field": "task_name",
      "reason": "Task name is required"
    }
  }
}
```

For more details, see `docs/api-contracts/error-handling.md`.

## Rate Limiting

The API implements rate limiting to prevent abuse. The rate limits are:

- 100 requests per minute for authenticated users
- 10 requests per minute for unauthenticated users

Rate limit information is included in the response headers:

```
X-RateLimit-Limit: 100
X-RateLimit-Remaining: 95
X-RateLimit-Reset: 1616161616
```

## Versioning

The API is versioned to ensure backward compatibility. The current version is v1.

To specify a version, include it in the URL:

```
/api/v1/tasks
```

## Examples

Example API requests and responses are available in the `examples/` directory.
