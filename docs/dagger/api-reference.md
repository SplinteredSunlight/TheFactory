# Dagger API Reference

This document provides a reference for the Dagger integration API in the AI-Orchestration-Platform.

## Base URL

All API endpoints are relative to the base URL of the API server:

```
http://localhost:8000
```

## Authentication

All API endpoints require authentication using a bearer token:

```
Authorization: Bearer <token>
```

You can obtain a token by authenticating with the API server.

## Endpoints

### Workflows

#### List Workflows

```
GET /dagger/workflows
```

**Query Parameters**:

- `status` (optional): Filter workflows by status (`pending`, `running`, `completed`, `failed`)
- `limit` (optional): Maximum number of workflows to return (default: 20)
- `offset` (optional): Number of workflows to skip (default: 0)

**Response**:

```json
{
  "workflows": [
    {
      "id": "123e4567-e89b-12d3-a456-426614174000",
      "name": "Example Workflow",
      "description": "A simple example workflow",
      "status": "pending",
      "created_at": "2025-03-01T12:00:00Z",
      "updated_at": null
    }
  ],
  "total": 1,
  "limit": 20,
  "offset": 0
}
```

#### Create Workflow

```
POST /dagger/workflows
```

**Request Body**:

```json
{
  "name": "Example Workflow",
  "description": "A simple example workflow",
  "steps": [
    {
      "id": "step1",
      "name": "Step 1",
      "container": {
        "image": "python:3.9-slim",
        "command": ["python", "script.py"],
        "environment": {
          "ENV_VAR": "value"
        },
        "volumes": [
          {
            "source": "/tmp",
            "target": "/data"
          }
        ]
      }
    },
    {
      "id": "step2",
      "name": "Step 2",
      "container": {
        "image": "node:18-alpine",
        "command": ["node", "script.js"]
      },
      "depends_on": ["step1"]
    }
  ],
  "container_config": {
    "image": "python:3.9-slim",
    "environment": {
      "DEBUG": "true"
    }
  }
}
```

**Response**:

```json
{
  "id": "123e4567-e89b-12d3-a456-426614174000",
  "name": "Example Workflow",
  "description": "A simple example workflow",
  "steps": [
    {
      "id": "step1",
      "name": "Step 1",
      "container": {
        "image": "python:3.9-slim",
        "command": ["python", "script.py"],
        "environment": {
          "ENV_VAR": "value"
        },
        "volumes": [
          {
            "source": "/tmp",
            "target": "/data"
          }
        ]
      }
    },
    {
      "id": "step2",
      "name": "Step 2",
      "container": {
        "image": "node:18-alpine",
        "command": ["node", "script.js"]
      },
      "depends_on": ["step1"]
    }
  ],
  "container_config": {
    "image": "python:3.9-slim",
    "environment": {
      "DEBUG": "true"
    }
  },
  "status": "pending",
  "created_at": "2025-03-01T12:00:00Z",
  "updated_at": null
}
```

#### Get Workflow

```
GET /dagger/workflows/{workflowId}
```

**Path Parameters**:

- `workflowId`: ID of the workflow to retrieve

**Response**:

```json
{
  "id": "123e4567-e89b-12d3-a456-426614174000",
  "name": "Example Workflow",
  "description": "A simple example workflow",
  "steps": [
    {
      "id": "step1",
      "name": "Step 1",
      "container": {
        "image": "python:3.9-slim",
        "command": ["python", "script.py"],
        "environment": {
          "ENV_VAR": "value"
        },
        "volumes": [
          {
            "source": "/tmp",
            "target": "/data"
          }
        ]
      }
    },
    {
      "id": "step2",
      "name": "Step 2",
      "container": {
        "image": "node:18-alpine",
        "command": ["node", "script.js"]
      },
      "depends_on": ["step1"]
    }
  ],
  "container_config": {
    "image": "python:3.9-slim",
    "environment": {
      "DEBUG": "true"
    }
  },
  "status": "pending",
  "created_at": "2025-03-01T12:00:00Z",
  "updated_at": null
}
```

#### Update Workflow

```
PATCH /dagger/workflows/{workflowId}
```

**Path Parameters**:

- `workflowId`: ID of the workflow to update

**Request Body**:

```json
{
  "name": "Updated Workflow",
  "description": "Updated description",
  "steps": [
    {
      "id": "step1",
      "name": "Updated Step 1",
      "container": {
        "image": "python:3.9-slim",
        "command": ["python", "updated.py"]
      }
    }
  ]
}
```

**Response**:

```json
{
  "id": "123e4567-e89b-12d3-a456-426614174000",
  "name": "Updated Workflow",
  "description": "Updated description",
  "steps": [
    {
      "id": "step1",
      "name": "Updated Step 1",
      "container": {
        "image": "python:3.9-slim",
        "command": ["python", "updated.py"]
      }
    }
  ],
  "container_config": {
    "image": "python:3.9-slim",
    "environment": {
      "DEBUG": "true"
    }
  },
  "status": "pending",
  "created_at": "2025-03-01T12:00:00Z",
  "updated_at": "2025-03-01T13:00:00Z"
}
```

#### Delete Workflow

```
DELETE /dagger/workflows/{workflowId}
```

**Path Parameters**:

- `workflowId`: ID of the workflow to delete

**Response**:

```
204 No Content
```

#### Execute Workflow

```
POST /dagger/workflows/{workflowId}/execute
```

**Path Parameters**:

- `workflowId`: ID of the workflow to execute

**Request Body**:

```json
{
  "inputs": {
    "param1": "value1",
    "param2": "value2"
  },
  "container_registry": "docker.io",
  "container_credentials": {
    "username": "user",
    "password": "pass"
  },
  "workflow_defaults": {
    "inputs": {
      "default_timeout": 300
    }
  }
}
```

**Response**:

```json
{
  "execution_id": "123e4567-e89b-12d3-a456-426614174001",
  "status": "pending",
  "workflow_id": "123e4567-e89b-12d3-a456-426614174000"
}
```

### Executions

#### List Workflow Executions

```
GET /dagger/workflows/{workflowId}/executions
```

**Path Parameters**:

- `workflowId`: ID of the workflow

**Query Parameters**:

- `status` (optional): Filter executions by status (`pending`, `running`, `completed`, `failed`)
- `limit` (optional): Maximum number of executions to return (default: 20)
- `offset` (optional): Number of executions to skip (default: 0)

**Response**:

```json
{
  "executions": [
    {
      "id": "123e4567-e89b-12d3-a456-426614174001",
      "workflow_id": "123e4567-e89b-12d3-a456-426614174000",
      "status": "completed",
      "steps": {
        "step1": {
          "id": "step1",
          "name": "Step 1",
          "status": "completed",
          "started_at": "2025-03-01T12:00:00Z",
          "completed_at": "2025-03-01T12:01:00Z"
        },
        "step2": {
          "id": "step2",
          "name": "Step 2",
          "status": "completed",
          "started_at": "2025-03-01T12:01:00Z",
          "completed_at": "2025-03-01T12:02:00Z"
        }
      },
      "inputs": {
        "param1": "value1",
        "param2": "value2"
      },
      "outputs": {
        "result": "success"
      },
      "started_at": "2025-03-01T12:00:00Z",
      "completed_at": "2025-03-01T12:02:00Z"
    }
  ],
  "total": 1,
  "limit": 20,
  "offset": 0
}
```

#### Get Execution

```
GET /dagger/executions/{executionId}
```

**Path Parameters**:

- `executionId`: ID of the execution to retrieve

**Response**:

```json
{
  "id": "123e4567-e89b-12d3-a456-426614174001",
  "workflow_id": "123e4567-e89b-12d3-a456-426614174000",
  "status": "completed",
  "steps": {
    "step1": {
      "id": "step1",
      "name": "Step 1",
      "status": "completed",
      "started_at": "2025-03-01T12:00:00Z",
      "completed_at": "2025-03-01T12:01:00Z",
      "inputs": {
        "param1": "value1"
      },
      "outputs": {
        "result": "step1 result"
      }
    },
    "step2": {
      "id": "step2",
      "name": "Step 2",
      "status": "completed",
      "started_at": "2025-03-01T12:01:00Z",
      "completed_at": "2025-03-01T12:02:00Z",
      "inputs": {
        "param2": "value2"
      },
      "outputs": {
        "result": "step2 result"
      }
    }
  },
  "inputs": {
    "param1": "value1",
    "param2": "value2"
  },
  "outputs": {
    "result": "success"
  },
  "started_at": "2025-03-01T12:00:00Z",
  "completed_at": "2025-03-01T12:02:00Z",
  "logs": "Execution logs..."
}
```

#### Cancel Execution

```
DELETE /dagger/executions/{executionId}
```

**Path Parameters**:

- `executionId`: ID of the execution to cancel

**Response**:

```
204 No Content
```

### Agents

#### List Agents

```
GET /dagger/agents
```

**Query Parameters**:

- `status` (optional): Filter agents by status (`idle`, `busy`, `offline`, `error`)
- `capability` (optional): Filter agents by capability
- `limit` (optional): Maximum number of agents to return (default: 20)
- `offset` (optional): Number of agents to skip (default: 0)

**Response**:

```json
{
  "agents": [
    {
      "id": "123e4567-e89b-12d3-a456-426614174002",
      "name": "Dagger Agent",
      "description": "Agent for Dagger workflows",
      "capabilities": ["containerized_workflow", "dagger_pipeline"],
      "status": "idle",
      "current_load": 0,
      "max_load": 10,
      "container_registry": "docker.io",
      "workflow_directory": "/workflows",
      "created_at": "2025-03-01T12:00:00Z",
      "updated_at": null
    }
  ],
  "total": 1,
  "limit": 20,
  "offset": 0
}
```

#### Create Agent

```
POST /dagger/agents
```

**Request Body**:

```json
{
  "name": "Dagger Agent",
  "description": "Agent for Dagger workflows",
  "capabilities": ["containerized_workflow", "dagger_pipeline"],
  "container_registry": "docker.io",
  "workflow_directory": "/workflows",
  "max_concurrent_executions": 10,
  "timeout_seconds": 600
}
```

**Response**:

```json
{
  "id": "123e4567-e89b-12d3-a456-426614174002",
  "name": "Dagger Agent",
  "description": "Agent for Dagger workflows",
  "capabilities": ["containerized_workflow", "dagger_pipeline"],
  "status": "idle",
  "current_load": 0,
  "max_load": 10,
  "container_registry": "docker.io",
  "workflow_directory": "/workflows",
  "created_at": "2025-03-01T12:00:00Z",
  "updated_at": null
}
```

### Pipelines

#### List Pipelines

```
GET /dagger/pipelines
```

**Query Parameters**:

- `limit` (optional): Maximum number of pipelines to return (default: 20)
- `offset` (optional): Number of pipelines to skip (default: 0)

**Response**:

```json
{
  "pipelines": [
    {
      "id": "123e4567-e89b-12d3-a456-426614174003",
      "name": "Example Pipeline",
      "description": "A simple example pipeline",
      "source_directory": "/src",
      "pipeline_definition": "example.yaml",
      "caching_enabled": true,
      "timeout_seconds": 1800,
      "created_at": "2025-03-01T12:00:00Z",
      "updated_at": null
    }
  ],
  "total": 1,
  "limit": 20,
  "offset": 0
}
```

#### Create Pipeline

```
POST /dagger/pipelines
```

**Request Body**:

```json
{
  "name": "Example Pipeline",
  "description": "A simple example pipeline",
  "source_directory": "/src",
  "pipeline_definition": "example.yaml",
  "caching_enabled": true,
  "timeout_seconds": 1800
}
```

**Response**:

```json
{
  "id": "123e4567-e89b-12d3-a456-426614174003",
  "name": "Example Pipeline",
  "description": "A simple example pipeline",
  "source_directory": "/src",
  "pipeline_definition": "example.yaml",
  "caching_enabled": true,
  "timeout_seconds": 1800,
  "created_at": "2025-03-01T12:00:00Z",
  "updated_at": null
}
```

#### Execute Pipeline

```
POST /dagger/pipelines/{pipelineId}/execute
```

**Path Parameters**:

- `pipelineId`: ID of the pipeline to execute

**Request Body**:

```json
{
  "inputs": {
    "param1": "value1",
    "param2": "value2"
  },
  "source_directory": "/src"
}
```

**Response**:

```json
{
  "execution_id": "123e4567-e89b-12d3-a456-426614174004",
  "status": "pending",
  "pipeline_id": "123e4567-e89b-12d3-a456-426614174003"
}
```

### Monitoring

#### Get Dagger Status

```
GET /monitoring/dagger/status
```

**Response**:

```json
{
  "status": "healthy",
  "version": "0.8.1",
  "active_workflows": 0,
  "active_steps": 0,
  "memory_usage_mb": 0,
  "cpu_usage_percent": 0
}
```

#### Get Dagger Metrics

```
GET /monitoring/dagger/metrics
```

**Response**:

```
# HELP dagger_workflow_executions_total Total number of Dagger workflow executions
# TYPE dagger_workflow_executions_total counter
dagger_workflow_executions_total{workflow_id="123e4567-e89b-12d3-a456-426614174000",status="completed"} 1
...
```

## Error Handling

All API endpoints return standard HTTP status codes to indicate success or failure:

- `200 OK`: The request was successful
- `201 Created`: The resource was created successfully
- `204 No Content`: The request was successful, but there is no content to return
- `400 Bad Request`: The request was invalid
- `401 Unauthorized`: Authentication is required
- `403 Forbidden`: The client does not have permission to access the resource
- `404 Not Found`: The resource was not found
- `500 Internal Server Error`: An error occurred on the server

Error responses include details about the error:

```json
{
  "status": 400,
  "code": "invalid_request",
  "message": "Invalid request body",
  "details": {
    "errors": [
      {
        "field": "name",
        "message": "Field is required"
      }
    ]
  }
}
```

## Pagination

List endpoints support pagination using the `limit` and `offset` query parameters. The response includes pagination information:

```json
{
  "workflows": [...],
  "total": 100,
  "limit": 20,
  "offset": 0
}
```

To get the next page, increment the `offset` by the `limit`:

```
GET /dagger/workflows?limit=20&offset=20
```

## Filtering

List endpoints support filtering using query parameters. The available filters depend on the endpoint. For example, the `/dagger/workflows` endpoint supports filtering by `status`:

```
GET /dagger/workflows?status=completed
```

## Sorting

List endpoints support sorting using the `sort` query parameter:

```
GET /dagger/workflows?sort=created_at:desc
```

The format is `field:direction`, where `direction` is either `asc` or `desc`. If the direction is not specified, it defaults to `asc`.