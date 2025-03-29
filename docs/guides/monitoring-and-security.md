# Monitoring and Security Guide

This guide provides information on how to use the monitoring and security features of the AI-Orchestration-Platform.

## Table of Contents

- [Monitoring](#monitoring)
  - [Metrics](#metrics)
  - [Dashboards](#dashboards)
  - [Alerting](#alerting)
  - [Tracing](#tracing)
  - [Progress Tracking](#progress-tracking)
- [Security](#security)
  - [Authentication](#authentication)
  - [Role-Based Access Control (RBAC)](#role-based-access-control-rbac)
  - [API Security](#api-security)

## Monitoring

The AI-Orchestration-Platform provides comprehensive monitoring capabilities to help you track the performance and health of your workflows and the platform itself.

### Metrics

The platform collects various metrics using Prometheus. These metrics include:

- **Workflow Metrics**: Execution rate, duration, success rate, etc.
- **Step Metrics**: Execution rate, duration, success rate, etc.
- **System Metrics**: CPU usage, memory usage, disk usage, etc.
- **Circuit Breaker Metrics**: State, failure rate, etc.

You can access these metrics through the following endpoints:

- `/monitoring/metrics`: All Prometheus metrics
- `/monitoring/metrics/{metric_name}`: Specific Prometheus metric
- `/monitoring/dagger/metrics`: Dagger-specific Prometheus metrics
- `/monitoring/dagger/metrics/{metric_name}`: Specific Dagger Prometheus metric

Example:

```bash
# Get all metrics
curl http://localhost:8000/monitoring/metrics

# Get a specific metric
curl http://localhost:8000/monitoring/metrics/dagger_workflow_executions_total
```

### Dashboards

The platform provides Grafana dashboards for visualizing metrics. The following dashboards are available:

- **Dagger Dashboard**: Overview of Dagger workflows and steps
- **Dagger Advanced Dashboard**: Detailed metrics for Dagger workflows and steps

To access these dashboards, you need to have Grafana installed and configured to use the Prometheus data source. The dashboard JSON files are located in the `monitoring` directory:

- `monitoring/grafana-dagger-dashboard.json`
- `monitoring/grafana-dagger-advanced-dashboard.json`

You can import these dashboards into Grafana using the Grafana UI or the Grafana API.

### Alerting

The platform provides alerting capabilities using Prometheus Alertmanager. The alerting rules are defined in the `monitoring/alerting_rules.yml` file. The Alertmanager configuration is defined in the `monitoring/alertmanager.yml` file.

You can access the current alerts through the following endpoint:

- `/monitoring/alerts`: Current alerts

Example:

```bash
# Get current alerts
curl http://localhost:8000/monitoring/alerts
```

### Tracing

The platform provides distributed tracing capabilities using OpenTelemetry. Tracing is used to track the execution of workflows and steps across the platform.

Tracing is enabled by default. You can configure tracing using the following environment variables:

- `DAGGER_TRACING_ENABLED`: Enable or disable tracing (default: `true`)
- `DAGGER_OTLP_ENDPOINT`: OpenTelemetry collector endpoint (default: `localhost:4317`)

You can use the `@trace_function`, `@trace_workflow`, and `@trace_step` decorators to add tracing to your functions, workflows, and steps.

Example:

```python
from src.monitoring.dagger_tracing import trace_function

@trace_function(name="my_function")
async def my_function():
    # Function code
    pass
```

### Progress Tracking

The platform provides real-time progress tracking for workflows and steps. Progress updates are available through both REST API endpoints and WebSocket connections.

REST API endpoints:

- `/progress/{workflow_id}`: Get progress for a workflow
- `/progress/{workflow_id}/history`: Get progress history for a workflow
- `/progress/{workflow_id}/estimate`: Estimate completion time for a workflow
- `/progress/update`: Update progress for a workflow or step

WebSocket endpoint:

- `/progress/ws`: WebSocket endpoint for real-time progress updates

Example:

```bash
# Get progress for a workflow
curl http://localhost:8000/progress/workflow-123

# Update progress for a workflow
curl -X POST http://localhost:8000/progress/update \
  -H "Content-Type: application/json" \
  -d '{
    "workflow_id": "workflow-123",
    "percent_complete": 50.0,
    "status": "in_progress",
    "message": "Processing data"
  }'
```

WebSocket example:

```javascript
// Connect to WebSocket
const socket = new WebSocket('ws://localhost:8000/progress/ws?workflow_id=workflow-123');

// Listen for messages
socket.onmessage = (event) => {
  const data = JSON.parse(event.data);
  console.log('Progress update:', data);
};
```

## Security

The AI-Orchestration-Platform provides comprehensive security features to protect your workflows and data.

### Authentication

The platform uses JWT (JSON Web Token) based authentication. To authenticate, you need to obtain an access token by providing your username and password.

Endpoints:

- `/auth/token`: Get an access token
- `/auth/refresh`: Refresh an access token

Example:

```bash
# Get an access token
curl -X POST http://localhost:8000/auth/token \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=admin&password=admin"

# Refresh an access token
curl -X POST http://localhost:8000/auth/refresh \
  -H "Content-Type: application/json" \
  -d '{"refresh_token": "your-refresh-token"}'
```

### Role-Based Access Control (RBAC)

The platform uses role-based access control (RBAC) to control access to resources. Each user has one or more roles, and each role has a set of permissions.

The following roles are available:

- `admin`: Full access to all resources
- `user`: Limited access to resources
- `agent`: Access to agent-related resources
- `system`: Access to system-related resources
- `guest`: Read-only access to resources

The following permissions are available:

- Workflow permissions: `workflow:create`, `workflow:read`, `workflow:update`, `workflow:delete`, `workflow:execute`
- Task permissions: `task:create`, `task:read`, `task:update`, `task:delete`, `task:execute`
- Agent permissions: `agent:create`, `agent:read`, `agent:update`, `agent:delete`, `agent:execute`
- System permissions: `system:admin`, `system:read`, `system:update`
- Monitoring permissions: `monitoring:read`, `monitoring:update`
- Progress permissions: `progress:read`, `progress:update`

You can use the `@has_permission` and `@has_role` decorators to protect your endpoints.

Example:

```python
from fastapi import Depends
from src.security.rbac import has_permission, Permission, get_current_active_user

@app.get("/workflows")
@has_permission(Permission.WORKFLOW_READ)
async def get_workflows(current_user = Depends(get_current_active_user)):
    # Endpoint code
    pass
```

### API Security

The platform provides the following API security features:

- **CORS**: Cross-Origin Resource Sharing is configured to allow requests from specific origins
- **Rate Limiting**: API rate limiting is implemented to prevent abuse
- **Input Validation**: All API inputs are validated to prevent injection attacks
- **Output Sanitization**: All API outputs are sanitized to prevent data leakage
- **Error Handling**: Proper error handling is implemented to prevent information disclosure

These features are enabled by default and can be configured in the `src/api/main.py` file.
