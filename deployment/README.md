# Deployment Configuration

This directory contains configuration files and scripts for deploying the AI Orchestration Platform to various environments.

## Files

- **dagger-deployment.yaml**: Kubernetes deployment configuration for Dagger
- **deploy.sh**: Main deployment script
- **Dockerfile**: Docker image definition for the platform
- **entrypoint.sh**: Container entrypoint script
- **init_dagger_config.py**: Script to initialize Dagger configuration
- **wait_for_dependencies.py**: Script to wait for dependencies to be ready

## Deployment Options

The AI Orchestration Platform can be deployed in several ways:

### Docker Deployment

To deploy using Docker:

```bash
# Build the Docker image
docker build -t ai-orchestration-platform -f deployment/Dockerfile .

# Run the container
docker run -p 8000:8000 -p 8080:8080 ai-orchestration-platform
```

### Kubernetes Deployment

To deploy to Kubernetes:

```bash
# Apply the deployment configuration
kubectl apply -f deployment/dagger-deployment.yaml

# Check the deployment status
kubectl get deployments
```

### Manual Deployment

To deploy manually:

```bash
# Run the deployment script
./deployment/deploy.sh
```

## Configuration

The deployment can be configured through environment variables:

- **API_PORT**: Port for the API server (default: 8000)
- **DASHBOARD_PORT**: Port for the dashboard (default: 8080)
- **LOG_LEVEL**: Logging level (default: info)
- **ENVIRONMENT**: Deployment environment (development, staging, production)
- **DATABASE_URL**: URL for the database
- **REDIS_URL**: URL for Redis
- **DAGGER_ENDPOINT**: Endpoint for Dagger

## Dependencies

The AI Orchestration Platform depends on:

- **Database**: PostgreSQL or SQLite
- **Cache**: Redis (optional)
- **Dagger**: For containerized workflow execution
- **MCP Server**: For tool integration

The `wait_for_dependencies.py` script ensures that all dependencies are available before starting the platform.

## Customization

To customize the deployment:

1. Copy the relevant configuration files
2. Modify them according to your requirements
3. Use the modified files for deployment

For example, to customize the Kubernetes deployment:

```bash
cp deployment/dagger-deployment.yaml my-deployment.yaml
# Edit my-deployment.yaml
kubectl apply -f my-deployment.yaml
