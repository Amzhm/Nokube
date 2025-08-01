# Kubernetes Manifests - Development Environment (Kind)

## Directory Structure

```
k8s/dev/
├── namespaces.yaml          # Namespaces nokube-dev and nokube-system
├── database/                # PostgreSQL database resources
├── services/                # Microservices manifests (auth, api-gateway, etc.)
├── ingress/                 # Ingress rules for service exposure
└── README.md               # This file
```

## Namespaces

- **nokube-dev**: Business applications (microservices, frontend)
- **nokube-system**: Infrastructure components (PostgreSQL, monitoring)

## Deployment

```bash
# Apply all manifests
kubectl apply -f k8s/dev/

# Or by category
kubectl apply -f k8s/dev/database/
kubectl apply -f k8s/dev/services/
kubectl apply -f k8s/dev/ingress/
```