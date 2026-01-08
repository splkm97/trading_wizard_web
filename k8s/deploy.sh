#!/bin/bash
# Trading Wizard Web - Kubernetes Deployment Script

set -e

# Configuration
REGISTRY="${REGISTRY:-}"  # e.g., "docker.io/username" or "ghcr.io/username"
TAG="${TAG:-latest}"
NAMESPACE="trading-wizard"

echo "=== Trading Wizard Web - Kubernetes Deployment ==="

# Check prerequisites
command -v kubectl >/dev/null 2>&1 || { echo "kubectl is required but not installed."; exit 1; }
command -v docker >/dev/null 2>&1 || { echo "docker is required but not installed."; exit 1; }

# Get script directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"

# Build images
echo ""
echo "=== Building Docker images ==="

if [ -n "$REGISTRY" ]; then
    BACKEND_IMAGE="${REGISTRY}/trading-wizard-backend:${TAG}"
    FRONTEND_IMAGE="${REGISTRY}/trading-wizard-frontend:${TAG}"
else
    BACKEND_IMAGE="trading-wizard-backend:${TAG}"
    FRONTEND_IMAGE="trading-wizard-frontend:${TAG}"
fi

echo "Building backend image: ${BACKEND_IMAGE}"
docker build -t "${BACKEND_IMAGE}" "${PROJECT_DIR}/backend"

echo "Building frontend image: ${FRONTEND_IMAGE}"
docker build -t "${FRONTEND_IMAGE}" "${PROJECT_DIR}/frontend"

# Push images if registry is specified
if [ -n "$REGISTRY" ]; then
    echo ""
    echo "=== Pushing images to registry ==="
    docker push "${BACKEND_IMAGE}"
    docker push "${FRONTEND_IMAGE}"

    # Update image references in deployments
    echo "Updating image references in manifests..."
    sed -i.bak "s|image: trading-wizard-backend:.*|image: ${BACKEND_IMAGE}|g" "${SCRIPT_DIR}/backend-deployment.yaml"
    sed -i.bak "s|image: trading-wizard-frontend:.*|image: ${FRONTEND_IMAGE}|g" "${SCRIPT_DIR}/frontend-deployment.yaml"
    rm -f "${SCRIPT_DIR}"/*.bak
fi

# Deploy to Kubernetes
echo ""
echo "=== Deploying to Kubernetes ==="

# Apply using kustomize
kubectl apply -k "${SCRIPT_DIR}"

# Wait for deployments
echo ""
echo "=== Waiting for deployments ==="
kubectl -n ${NAMESPACE} rollout status deployment/backend --timeout=120s
kubectl -n ${NAMESPACE} rollout status deployment/frontend --timeout=120s

# Show status
echo ""
echo "=== Deployment Status ==="
kubectl -n ${NAMESPACE} get pods
kubectl -n ${NAMESPACE} get services
kubectl -n ${NAMESPACE} get pvc

echo ""
echo "=== Deployment Complete ==="
echo ""
echo "To access the application:"
echo "  - Port forward: kubectl -n ${NAMESPACE} port-forward svc/frontend 8080:80"
echo "  - Then open: http://localhost:8080"
echo ""
echo "To check logs:"
echo "  - Backend:  kubectl -n ${NAMESPACE} logs -f deployment/backend"
echo "  - Frontend: kubectl -n ${NAMESPACE} logs -f deployment/frontend"
