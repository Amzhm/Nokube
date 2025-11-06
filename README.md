# NoKube - Simplified Kubernetes Deployment Platform

##  About the Project

**NoKube** is a project that explores how to simplify application deployment on Kubernetes for developers without deep DevOps expertise.

The idea is simple: you provide your GitHub code, describe your architecture (frontend, backend, database...), and the platform automatically handles the build, deployment on a Kubernetes cluster, and monitoring.

## Project Motivation

### The Problem
I noticed that deploying an application on Kubernetes typically requires:
- ✗ A good understanding of Kubernetes (pods, deployments, services, ingress...)
- ✗ Manual cluster management
- ✗ Writing numerous YAML configuration files
- ✗ Setting up CI/CD pipelines
- ✗ Managing Docker registries
- ✗ Infrastructure monitoring and maintenance

### NoKube's Goal
I wanted to create a solution where you only need to:
- ✓ Provide a GitHub link
- ✓ Describe your application architecture
- ✓ Fill out a simple form
- ✓ Click "Deploy"

Everything else is handled automatically by the platform.

##  Implemented Features

-  **Secure Authentication** - Complete user management system with JWT
-  **Automatic Build** - Docker images are built via GitHub Actions (no local build)
-  **Kubernetes Deployment** - Automatic creation of K8s resources (Deployments, Services, Ingress)
-  **Monitoring** - Track the status of deployed applications
-  **Automatic Routing** - Each application receives a URL via Ingress Controller (wildcard DNS)
-  **Multi-service Architecture** - Support for projects with multiple components (frontend + backend + database)

##  Architecture

I designed NoKube with a **microservices architecture** to ensure modularity and scalability:

SCHEMA TO ADD

##  Microservices

### 1. **Frontend** 
- Responsive web user interface
- Forms to define application architecture
- Deployment tracking dashboard
- Project and service management

### 2. **Gateway Service** 
- Single entry point for all APIs
- Intelligent routing to microservices
- Security and authentication management
- Load balancing

### 3. **Auth Service** 
- User management (registration, login, logout)
- JWT authentication
- Permission and role management
- Resource access security

### 4. **Project Service** 
- Project creation and management
- Service organization per project (frontend, backend, database...)
- Complete CRUD on projects and their configurations
- Deployment history

### 5. **Build Service** 
- Build process coordination
- GitHub Actions triggering
- Automatic Dockerfile generation
- Build status tracking
- Registry image management

### 6. **Monitor Service** 
- Automatic deployment on Kubernetes
- Creation of K8s resources (Deployments, Services, Ingress)
- Application status monitoring
- Log and metrics management
- Automatic scaling

##  Installation
NoKube can be deployed on any Kubernetes cluster.
### Prerequisites

- A working Kubernetes cluster (kind, minikube, EKS, GKE, AKS, etc.)
- `kubectl` configured to access your cluster
- Docker installed to build images

### Installation Steps
#### 1. Clone the repository

```bash
git clone https://github.com/Amzhm/Nokube.git
cd Nokube
```

#### 2. Build Docker images

Each microservice must be built as a Docker image:

```bash
# Auth Service
cd backend/auth-service
docker build -t nokube/auth-service:latest .

# Project Service
cd ../project-service
docker build -t nokube/project-service:latest .

# Build Service
cd ../build-service
docker build -t nokube/build-service:latest .

# Monitor Service
cd ../monitor-service
docker build -t nokube/monitor-service:latest .

# Gateway Service
cd ../gateway-service
docker build -t nokube/gateway-service:latest .

# Frontend
cd ../../frontend
docker build -t nokube/frontend:latest .
```
#### 4. Apply Kubernetes manifests

Kubernetes manifests are located in the `/k8s` folder:

```bash
# Apply all manifests
kubectl apply -f k8s/

# Or apply service by service
kubectl apply -f k8s/auth-service/
kubectl apply -f k8s/project-service/
kubectl apply -f k8s/build-service/
kubectl apply -f k8s/monitor-service/
kubectl apply -f k8s/gateway-service/
kubectl apply -f k8s/frontend/
kubectl apply -f k8s/ingress/
```

#### 5. Verify the deployment

```bash
# Check that all pods are running
kubectl get pods

# Check services
kubectl get services

# Check ingress
kubectl get ingress
```
### Configuration

#### Environment Variables

Configure the necessary environment variables in the Kubernetes manifests:
- PostgreSQL database connection
- JWT secrets for authentication
- Kubernetes cluster configuration for the Monitor Service
#### GitHub Configuration for Build

NoKube uses GitHub Actions to build Docker images. You need to:

1. **Create a GitHub repository** to store your Dockerfiles and trigger builds

2. **Enable GitHub Container Registry (GHCR)**
3. **Configure GitHub Secrets**: To create a Personal Access Token (PAT)
4. **Update Kubernetes manifests**

##  Expected User Flow

1. **Registration/Login** → Account creation
2. **Create a project** → Name your project
3. **Define architecture** → Add required services (e.g., React frontend + FastAPI backend + PostgreSQL)
4. **Configure each service**:
   - GitHub code link
   - Language and framework
   - Listening port
   - Build/execution commands
5. **Deploy** → Platform launches build via GitHub Actions then deploys on K8s
6. **Access application** → Automatic URL generated via Ingress (e.g., `my-project.nokube.fr`)
7. **Monitor** → Status tracking via Monitor Service

##  Technologies Used

### Backend
- **FastAPI** - Modern and high-performance Python framework
- **PostgreSQL** - Relational database
- **JWT** - Secure authentication

### Build & Deployment
- **GitHub Actions** - Automated CI/CD
- **Docker** - Containerization
- **Kubernetes** - Container orchestration
- **Ingress Controller** - HTTP/HTTPS traffic management

### Infrastructure
- **kind** (development) - Local Kubernetes cluster
- **AWS/Cloud** (production) - Scalable cloud infrastructure
- **Wildcard DNS** - Automatic application routing

##  Envisioned Use Cases

This project could be useful for:
-  **Developers** who want to focus on code rather than infrastructure
-  **Students** who want to deploy their projects without DevOps expertise
-  **Rapid prototyping** to test ideas without complex configuration
-  **Learning** microservices architecture and Kubernetes

##  Demonstrated Skills

This project implements:
- **Microservices architecture** with inter-service communication
- **Containerization** and Kubernetes orchestration
- **CI/CD** with GitHub Actions
- **REST API** with FastAPI (Python)
- **JWT authentication** and security
- **Database management** PostgreSQL
- **Infrastructure as Code** (Kubernetes manifests)
- **Ingress Controller** and HTTP/HTTPS routing management

---

**NoKube** - *Personal project exploring cloud-native architectures*
