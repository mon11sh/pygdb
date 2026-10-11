# GDB Microservices Platform - Docker Deployment Strategy

## Overview

This document outlines the Docker deployment strategy for the Global Digital Bank (GDB) microservices platform. The strategy covers both single-container and multi-container deployment approaches, providing clear guidance on when to use each approach and how to implement them effectively.

## Deployment Approaches

### 1. Single-Container Deployment

#### Definition
Each microservice runs in its own Docker container, with shared infrastructure services (databases, message queues, etc.) running in separate containers.

#### When to Use
- **Local Development**: For development and testing environments
- **Production**: For scalable, isolated service deployment
- **Complex Dependencies**: When services have different runtime requirements
- **Resource Management**: When fine-grained resource control is needed

#### Advantages
- **Isolation**: Each service is isolated from others
- **Scalability**: Services can be scaled independently
- **Resource Management**: Fine-grained resource allocation
- **Dependency Management**: Each service manages its own dependencies
- **Rollback**: Easy to rollback individual services

#### Disadvantages
- **Complexity**: More containers to manage
- **Network Overhead**: More inter-container communication
- **Resource Overhead**: Higher resource consumption
- **Configuration**: More complex configuration management

#### Implementation
```dockerfile
# Example Dockerfile for auth-service
FROM python:3.12-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 8004

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8004"]
```

### 2. Multi-Container Deployment

#### Definition
Multiple services share a single Docker container, reducing the number of containers and simplifying deployment.

#### When to Use
- **Simple Applications**: When services have minimal dependencies
- **Resource Constraints**: When resource efficiency is critical
- **Development**: For rapid development and testing
- **Small Scale**: For small deployments with limited resources

#### Advantages
- **Simplicity**: Fewer containers to manage
- **Resource Efficiency**: Lower resource consumption
- **Speed**: Faster startup times
- **Simplicity**: Simpler configuration and deployment

#### Disadvantages
- **Coupling**: Services are tightly coupled
- **Scalability**: Difficult to scale individual services
- **Resource Management**: Limited resource control
- **Isolation**: Less isolation between services

#### Implementation
```dockerfile
# Example multi-container Dockerfile
FROM python:3.12-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 8000 8001 8002 8003 8004 8005 8006 8007 8008

CMD ["sh", "-c", "
    # Start all services
    uvicorn auth_service.main:app --host 0.0.0.0 --port 8004 &
    uvicorn users_service.main:app --host 0.0.0.0 --port 8003 &
    uvicorn accounts_service.main:app --host 0.0.0.0 --port 8001 &
    uvicorn transactions_service.main:app --host 0.0.0.0 --port 8002 &
    uvicorn aadhar_service.main:app --host 0.0.0.0 --port 8005 &
    uvicorn company_service.main:app --host 0.0.0.0 --port 8006 &
    uvicorn notification_service.main:app --host 0.0.0.0 --port 8007 &
    uvicorn payment_gateway_service.main:app --host 0.0.0.0 --port 8008 &
    wait
"]
```

## Current Docker Setup Analysis

### Existing Configuration
The current GDB platform uses a hybrid approach:

#### Base Configuration (`docker-compose.yml`)
- **Single-Container Services**: Each microservice runs in its own container
- **Shared Infrastructure**: API gateway, registry service, frontend
- **Database Providers**: Separate configurations for different databases

#### Database Provider Configurations
- **In-Memory**: Zero setup, data resets on stop
- **SQLite**: Local .db files inside each container
- **PostgreSQL**: Bundled PostgreSQL container
- **MySQL**: Bundled MySQL container
- **Supabase**: Cloud PostgreSQL (requires external configuration)

### Service Matrix
```yaml
# Current service configuration
services:
  # Core services (single-container)
  auth-service:
    build: auth_service/Dockerfile
    ports: ["8004:8004"]
    environment: *service-env
    DATABASE_PROVIDER: inmemory

  users-service:
    build: users_service/Dockerfile
    ports: ["8003:8003"]
    environment: *service-env
    DATABASE_PROVIDER: inmemory

  accounts-service:
    build: accounts_service/Dockerfile
    ports: ["8001:8001"]
    environment: *service-env
    DATABASE_PROVIDER: inmemory

  transactions-service:
    build: transactions_service/Dockerfile
    ports: ["8002:8002"]
    environment: *service-env
    DATABASE_PROVIDER: inmemory

  # Mock/helper services (single-container)
  aadhar-service:
    build: aadhar_service/Dockerfile
    ports: ["8005:8005"]
    environment: *service-env

  company-service:
    build: company_crv_service/Dockerfile
    ports: ["8006:8006"]
    environment: *service-env

  notification-service:
    build: notification_service/Dockerfile
    ports: ["8007:8007"]
    environment: *service-env

  payment-gateway-service:
    build: central_payment_gateway_service/Dockerfile
    ports: ["8008:8008"]
    environment: *service-env

  # Infrastructure services (multi-container)
  registry-service:
    build: registry_service/Dockerfile
    ports: ["8010:8010"]

  api-gateway:
    build: central_gateway_service/Dockerfile
    ports: ["8000:8000"]
    environment: *gateway-env

  frontend:
    build: ./frontend
    ports: ["3000:80"]
```

## Deployment Strategy Recommendations

### Development Environment
**Recommendation**: Single-container deployment

**Rationale**:
- **Rapid Iteration**: Fast feedback loops for development
- **Isolation**: Easy to test individual services
- **Debugging**: Easier to debug and troubleshoot
- **Resource Management**: Fine-grained resource control

**Implementation**:
```bash
# Development deployment
python docker_up.py inmemory
python docker_up.py sqlite
python docker_up.py postgres
```

### Staging Environment
**Recommendation**: Single-container deployment

**Rationale**:
- **Realistic Testing**: Production-like environment
- **Service Isolation**: Test each service independently
- **Resource Management**: Ensure proper resource allocation
- **Rollback**: Easy to rollback problematic services

**Implementation**:
```bash
# Staging deployment with PostgreSQL
python docker_up.py postgres
```

### Production Environment
**Recommendation**: Single-container deployment with Kubernetes

**Rationale**:
- **Scalability**: Independent scaling of services
- **Resilience**: Isolation prevents cascading failures
- **Resource Management**: Fine-grained resource control
- **Maintenance**: Easier maintenance and updates

**Implementation**:
```bash
# Production deployment with Kubernetes
kubectl apply -f k8s/
kubectl scale deployment auth-service --replicas=3
kubectl scale deployment users-service --replicas=2
```

## Docker Deployment Implementation

### 1. Local Development with Docker Compose

#### Configuration
```yaml
# docker-compose.yml (base configuration)
services:
  auth-service:
    build:
      context: .
      dockerfile: auth_service/Dockerfile
    ports:
      - "8004:8004"
    environment:
      <<: *service-env
      DATABASE_PROVIDER: inmemory
    restart: unless-stopped
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8004/health"]
      interval: 30s
      timeout: 10s
      retries: 3

  users-service:
    build:
      context: .
      dockerfile: users_service/Dockerfile
    ports:
      - "8003:8003"
    environment:
      <<: *service-env
      DATABASE_PROVIDER: inmemory
    restart: unless-stopped
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8003/health"]
      interval: 30s
      timeout: 10s
      retries: 3
```

#### Database Provider Configurations
```yaml
# docker-compose.postgres.yml
version: '3.8'

services:
  postgres:
    image: postgres:16-alpine
    environment:
      POSTGRES_USER: postgres
      POSTGRES_PASSWORD: postgres
      POSTGRES_DB: postgres
    ports:
      - "5433:5432"
    volumes:
      - pgdata:/var/lib/postgresql/data
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U postgres"]
      interval: 5s
      timeout: 3s
      retries: 20

  auth-service:
    environment:
      DATABASE_PROVIDER: postgres
      DATABASE_URL: postgresql://postgres:postgres@postgres:5432/gdb_auth_db
    depends_on:
      postgres: { condition: service_healthy }
```

### 2. Production Deployment with Kubernetes

#### Deployment Manifests
```yaml
# k8s/auth-service-deployment.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: auth-service
  labels:
    app: auth-service
spec:
  replicas: 3
  selector:
    matchLabels:
      app: auth-service
  template:
    metadata:
      labels:
        app: auth-service
    spec:
      containers:
      - name: auth-service
        image: ghcr.io/your-org/gdb-auth-service:latest
        ports:
        - containerPort: 8004
        env:
        - name: DATABASE_PROVIDER
          value: "postgres"
        - name: DATABASE_URL
          valueFrom:
            secretKeyRef:
              name: db-credentials
              key: auth-database-url
        resources:
          requests:
            memory: "256Mi"
            cpu: "250m"
          limits:
            memory: "512Mi"
            cpu: "500m"
        livenessProbe:
          httpGet:
            path: /health
            port: 8004
          initialDelaySeconds: 30
          periodSeconds: 10
        readinessProbe:
          httpGet:
            path: /ready
            port: 8004
          initialDelaySeconds: 5
          periodSeconds: 5
---
apiVersion: v1
kind: Service
metadata:
  name: auth-service
spec:
  selector:
    app: auth-service
  ports:
  - protocol: TCP
    port: 8004
    targetPort: 8004
  type: ClusterIP
```

#### Service Discovery
```yaml
# k8s/registry-service.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: registry-service
  labels:
    app: registry-service
spec:
  replicas: 1
  selector:
    matchLabels:
      app: registry-service
  template:
    metadata:
      labels:
        app: registry-service
    spec:
      containers:
      - name: registry-service
        image: ghcr.io/your-org/gdb-registry-service:latest
        ports:
        - containerPort: 8010
        env:
        - name: DATABASE_PROVIDER
          value: "postgres"
        resources:
          requests:
            memory: "128Mi"
            cpu: "100m"
          limits:
            memory: "256Mi"
            cpu: "200m"
---
apiVersion: v1
kind: Service
metadata:
  name: registry-service
spec:
  selector:
    app: registry-service
  ports:
  - protocol: TCP
    port: 8010
    targetPort: 8010
  type: ClusterIP
```

### 3. API Gateway Configuration

#### Gateway Service
```yaml
# k8s/api-gateway.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: api-gateway
  labels:
    app: api-gateway
spec:
  replicas: 2
  selector:
    matchLabels:
      app: api-gateway
  template:
    metadata:
      labels:
        app: api-gateway
    spec:
      containers:
      - name: api-gateway
        image: ghcr.io/your-org/gdb-api-gateway:latest
        ports:
        - containerPort: 8000
        env:
        - name: GATEWAY_ACCOUNTS_URL
          value: "http://accounts-service:8001"
        - name: GATEWAY_TRANSACTIONS_URL
          value: "http://transactions-service:8002"
        - name: GATEWAY_USERS_URL
          value: "http://users-service:8003"
        - name: GATEWAY_AUTH_URL
          value: "http://auth-service:8004"
        resources:
          requests:
            memory: "256Mi"
            cpu: "250m"
          limits:
            memory: "512Mi"
            cpu: "500m"
        livenessProbe:
          httpGet:
            path: /health
            port: 8000
          initialDelaySeconds: 30
          periodSeconds: 10
        readinessProbe:
          httpGet:
            path: /ready
            port: 8000
          initialDelaySeconds: 5
          periodSeconds: 5
---
apiVersion: v1
kind: Service
metadata:
  name: api-gateway
spec:
  selector:
    app: api-gateway
  ports:
  - protocol: TCP
    port: 8000
    targetPort: 8000
  type: LoadBalancer
```

## Docker Deployment Best Practices

### 1. Image Management
```dockerfile
# Use multi-stage builds for smaller images
FROM python:3.12-slim AS base

FROM base AS builder
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

FROM base AS runtime
WORKDIR /app
COPY --from=builder /app ./
COPY . .

EXPOSE 8004
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8004"]
```

### 2. Resource Management
```yaml
# Kubernetes resource limits
resources:
  requests:
    memory: "256Mi"
    cpu: "250m"
  limits:
    memory: "512Mi"
    cpu: "500m"
```

### 3. Health Checks
```dockerfile
# Add health checks to Dockerfiles
HEALTHCHECK --interval=30s --timeout=10s --retries=3 \
  CMD curl -f http://localhost:8004/health || exit 1
```

### 4. Environment Configuration
```yaml
# Environment-specific configurations
environment:
  development:
    DATABASE_PROVIDER: inmemory
    LOG_LEVEL: DEBUG
  staging:
    DATABASE_PROVIDER: postgres
    LOG_LEVEL: INFO
  production:
    DATABASE_PROVIDER: postgres
    LOG_LEVEL: WARNING
```

## Deployment Automation

### 1. CI/CD Integration
```yaml
# GitHub Actions workflow for Docker deployment
jobs:
  deploy:
    runs-on: ubuntu-latest
    needs: [build, security]
    steps:
    - name: Deploy to Kubernetes
      run: |
        kubectl config use-context production
        kubectl apply -f k8s/
        kubectl set image deployment/auth-service ${{ env.REGISTRY }}/${{ github.repository }}/auth-service:${{ env.IMAGE_TAG }}
        kubectl set image deployment/users-service ${{ env.REGISTRY }}/${{ github.repository }}/users-service:${{ env.IMAGE_TAG }}
        # ... other services
```

### 2. Rollback Procedures
```bash
# Rollback to previous version
kubectl rollout undo deployment/auth-service
kubectl rollout status deployment/auth-service

# Manual rollback
kubectl set image deployment/auth-service ${{ env.REGISTRY }}/${{ github.repository }}/auth-service:previous-tag
```

### 3. Monitoring and Logging
```yaml
# Monitoring configuration
monitoring:
  prometheus:
    enabled: true
    retention: 30d
  grafana:
    enabled: true
    dashboards:
      - name: gdb-services
        path: dashboards/gdb-services.json
  logging:
    elasticsearch:
      enabled: true
      retention: 90d
    filebeat:
      enabled: true
      inputs:
        - type: container
          paths:
            - /var/log/containers/*.log
```

## Conclusion

The Docker deployment strategy for the GDB microservices platform combines the best practices of single-container and multi-container deployments. The strategy is designed to provide:

1. **Flexibility**: Support for different deployment scenarios
2. **Scalability**: Independent scaling of services
3. **Resilience**: Isolation and fault tolerance
4. **Simplicity**: Easy management and maintenance
5. **Security**: Proper isolation and access control

The implementation leverages Docker Compose for local development and Kubernetes for production deployments, ensuring consistency across environments while maintaining the flexibility to adapt to different requirements and constraints.