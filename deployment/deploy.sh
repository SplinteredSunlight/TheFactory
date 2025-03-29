#!/bin/bash
set -e

# Get the script directory
SCRIPT_DIR=$(dirname "$(readlink -f "$0")")
cd "$SCRIPT_DIR/.."

# Read environment variables from .env file
if [ -f .env ]; then
    echo "Loading environment variables from .env"
    set -a
    source .env
    set +a
fi

# Parse command line arguments
ENVIRONMENT=${1:-"staging"}
VERSION=${2:-$(git rev-parse --short HEAD)}
IMAGE_NAME=${IMAGE_NAME:-"ai-orchestration-platform/dagger"}
REGISTRY=${REGISTRY:-"docker.io"}

# Set environment-specific variables
case "$ENVIRONMENT" in
    production)
        K8S_NAMESPACE="ai-orchestration-prod"
        REPLICAS=3
        ;;
    staging)
        K8S_NAMESPACE="ai-orchestration-staging"
        REPLICAS=1
        ;;
    development)
        K8S_NAMESPACE="ai-orchestration-dev"
        REPLICAS=1
        ;;
    *)
        echo "Invalid environment: $ENVIRONMENT"
        echo "Usage: $0 [environment] [version]"
        echo "Environment must be one of: production, staging, development"
        exit 1
        ;;
esac

# Build Docker image
echo "Building Docker image: $REGISTRY/$IMAGE_NAME:$VERSION"
docker build -t "$REGISTRY/$IMAGE_NAME:$VERSION" -f deploy/Dockerfile .
docker tag "$REGISTRY/$IMAGE_NAME:$VERSION" "$REGISTRY/$IMAGE_NAME:latest"

# Push Docker image to registry
echo "Pushing Docker image to registry: $REGISTRY/$IMAGE_NAME:$VERSION"
docker push "$REGISTRY/$IMAGE_NAME:$VERSION"
docker push "$REGISTRY/$IMAGE_NAME:latest"

# Check if kubectl is available
if ! command -v kubectl >/dev/null 2>&1; then
    echo "kubectl not found, please install it first"
    exit 1
fi

# Apply Kubernetes configuration
echo "Deploying to Kubernetes namespace: $K8S_NAMESPACE"

# Create namespace if it doesn't exist
kubectl create namespace "$K8S_NAMESPACE" --dry-run=client -o yaml | kubectl apply -f -

# Create or update Kubernetes resources
sed -e "s|ai-orchestration-platform/dagger:latest|$REGISTRY/$IMAGE_NAME:$VERSION|g" \
    -e "s|replicas: 3|replicas: $REPLICAS|g" \
    deploy/dagger-deployment.yaml | kubectl apply -n "$K8S_NAMESPACE" -f -

# Create Dagger configuration
if [ ! -z "$CONTAINER_REGISTRY" ] && [ ! -z "$CONTAINER_REGISTRY_USERNAME" ] && [ ! -z "$CONTAINER_REGISTRY_PASSWORD" ]; then
    echo "Creating Dagger credentials secret"
    kubectl create secret generic dagger-credentials \
        --from-literal=registry_username="$CONTAINER_REGISTRY_USERNAME" \
        --from-literal=registry_password="$CONTAINER_REGISTRY_PASSWORD" \
        --namespace "$K8S_NAMESPACE" \
        --dry-run=client -o yaml | kubectl apply -f -
fi

echo "Deployment completed successfully!"