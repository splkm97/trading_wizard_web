# Trading Wizard Web - Kubernetes Deployment

## Prerequisites

- Kubernetes cluster (minikube, kind, EKS, GKE, etc.)
- kubectl configured
- Docker for building images

## Quick Start

```bash
# Deploy everything
./deploy.sh

# Or manually:
kubectl apply -k .
```

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                        Ingress                               │
│                   (trading-wizard.local)                     │
└─────────────────────┬───────────────────────────────────────┘
                      │
         ┌────────────┴────────────┐
         │                         │
         ▼                         ▼
┌─────────────────┐      ┌─────────────────┐
│    Frontend     │      │    Backend      │
│   (nginx:80)    │──────│  (uvicorn:8000) │
│   replicas: 2   │ /api │   replicas: 1   │
└─────────────────┘      └────────┬────────┘
                                  │
                         ┌────────┴────────┐
                         │  PVC (1Gi)      │
                         │  SQLite DB      │
                         └─────────────────┘
```

## Files

| File | Description |
|------|-------------|
| `namespace.yaml` | trading-wizard namespace |
| `backend-pvc.yaml` | PersistentVolumeClaim for SQLite database |
| `backend-secret.yaml` | JWT secret key (change before production!) |
| `backend-deployment.yaml` | Backend deployment + service |
| `frontend-deployment.yaml` | Frontend deployment + service |
| `ingress.yaml` | Ingress for external access |
| `kustomization.yaml` | Kustomize configuration |
| `deploy.sh` | Automated deployment script |

## Persistent Storage

The SQLite database is stored in a PersistentVolume:
- **PVC Name**: `backend-data-pvc`
- **Size**: 1Gi
- **Mount Path**: `/app/data`
- **Access Mode**: ReadWriteOnce

Data persists across pod restarts and redeployments.

## Configuration

### Backend Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `DATABASE_URL` | `sqlite:///./data/trading_wizard.db` | Database connection URL |
| `JWT_SECRET_KEY` | (from secret) | JWT signing key |
| `JWT_EXPIRE_MINUTES` | `1440` | Token expiration (24h) |
| `CORS_ORIGINS` | `http://localhost:5173` | Allowed CORS origins |
| `LOG_LEVEL` | `INFO` | Logging level |

### Frontend Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `BACKEND_URL` | `http://backend:8000` | Backend API URL |

## Deployment Options

### Local Development (minikube/kind)

```bash
# Build images locally
docker build -t trading-wizard-backend:latest ../backend
docker build -t trading-wizard-frontend:latest ../frontend

# For minikube, load images
minikube image load trading-wizard-backend:latest
minikube image load trading-wizard-frontend:latest

# Deploy
kubectl apply -k .

# Port forward
kubectl -n trading-wizard port-forward svc/frontend 8080:80
```

### Production (with registry)

```bash
# Set registry
export REGISTRY="your-registry.com/username"
export TAG="v1.0.0"

# Deploy (builds, pushes, and deploys)
./deploy.sh
```

## Security Notes

1. **Change JWT Secret**: Update `backend-secret.yaml` with a strong random key:
   ```bash
   echo -n "$(openssl rand -base64 32)" | base64
   ```

2. **TLS**: Uncomment TLS section in `ingress.yaml` for HTTPS

3. **Network Policies**: Consider adding NetworkPolicy resources for production

## Troubleshooting

```bash
# Check pod status
kubectl -n trading-wizard get pods

# Check logs
kubectl -n trading-wizard logs -f deployment/backend
kubectl -n trading-wizard logs -f deployment/frontend

# Check PVC status
kubectl -n trading-wizard get pvc

# Describe pod for events
kubectl -n trading-wizard describe pod <pod-name>

# Access backend directly
kubectl -n trading-wizard port-forward svc/backend 8000:8000
```

## Cleanup

```bash
kubectl delete -k .
# or
kubectl delete namespace trading-wizard
```
