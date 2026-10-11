# GDB Microservices Platform - Deployment Plan

## Overview

This deployment plan outlines the comprehensive deployment strategy for the Global Digital Bank (GDB) microservices platform, which consists of **8 FastAPI microservices** + a **React (Vite) frontend**, runnable against **five database providers** (SQLite, In-Memory, PostgreSQL, MySQL, Supabase) with **zero code changes** via a provider/factory abstraction.

## Architecture Overview

### Current Architecture
- **Frontend**: React/Vite application (port 3000)
- **API Gateway**: Central gateway service (port 8000) - single public entry point
- **Service Registry**: Discovery service (port 8010) - service registration and discovery
- **Backend Services**: 8 microservices (ports 8001-8008)
  - auth-service (8004) - authentication, JWT issuance
  - users-service (8003) - platform users, RBAC
  - accounts-service (8001) - account lifecycle, balances, PIN
  - transactions-service (8002) - transfers, deposits, limits, idempotency
  - aadhar-service (8005) - KYC verification stub
  - company-service (8006) - company registration stub
  - notification-service (8007) - notifications stub
  - payment-gateway-service (8008) - payment rail stub

### Deployment Targets
1. **Local Development** - Docker Compose with in-memory provider
2. **Production** - Kubernetes with cloud databases
3. **CI/CD Pipeline** - GitHub Actions for automated testing and deployment

## Deployment Strategy

### Multi-Provider Support
The platform supports five database providers with zero code changes:
- **In-Memory**: Zero setup, data resets on stop
- **SQLite**: Local .db files inside each container
- **PostgreSQL**: Bundled PostgreSQL container
- **MySQL**: Bundled MySQL container
- **Supabase**: Cloud PostgreSQL (requires external configuration)

### Container Strategy
- **Single-Container Services**: Each microservice runs in its own container
- **Multi-Container Stack**: Docker Compose for local development
- **Kubernetes**: Individual deployments for each service

## Deployment Phases

### Phase 1: GitHub Repository Setup
- Repository structure and configuration
- CI/CD pipeline setup
- Docker image building

### Phase 2: Docker Deployment
- Local development with Docker Compose
- Multi-provider support
- Service discovery and configuration

### Phase 3: Kubernetes Deployment
- Container orchestration
- Scaling and resilience
- Monitoring and logging integration

## Apps to be Setup

### Backend Services (8 microservices)
1. **auth-service** - Authentication and JWT management
2. **users-service** - User management and RBAC
3. **accounts-service** - Account operations and balances
4. **transactions-service** - Financial transactions and transfers
5. **aadhar-service** - KYC verification (mock)
6. **company-service** - Company registration (mock)
7. **notification-service** - Notification system (mock)
8. **payment-gateway-service** - Payment processing (mock)

### Infrastructure Services
9. **registry-service** - Service discovery and registration
10. **central-gateway-service** - API gateway and routing

### Frontend
11. **frontend** - React web application

## Technology Stack

### Backend
- Python 3.12
- FastAPI
- PostgreSQL/MySQL/SQLite
- Docker
- Kubernetes

### Frontend
- React 18
- Vite
- Node.js 18
- Docker

### DevOps
- GitHub Actions
- Docker
- Kubernetes
- Helm (planned)
- Prometheus/Grafana (planned)

## Current CI/CD Pipeline

### GitHub Actions Workflow
1. **Backend Testing**: Parallel testing of all 8 services
2. **Secret Scanning**: Security vulnerability detection
3. **Frontend Build**: Linting and building
4. **Docker Build**: Image building for all services

### Pipeline Stages
1. **Build**: Compile and package all services
2. **Test**: Unit and integration testing
3. **Security**: Vulnerability scanning
4. **Deploy**: Container orchestration

## Deployment Procedures

### Local Development
```bash
# Setup dependencies
python setup_all.py

# Setup database provider
python setup_provider.py sqlite

# Run all services
python run_all.py
```

### Docker Deployment
```bash
# Run with in-memory provider (default)
python docker_up.py inmemory

# Run with PostgreSQL
python docker_up.py postgres

# Run with MySQL
python docker_up.py mysql

# Run with Supabase (requires .env setup)
python docker_up.py supabase
```

### Kubernetes Deployment
```bash
# Apply Kubernetes manifests
kubectl apply -f k8s/

# Scale services
kubectl scale deployment auth-service --replicas=3

# Service discovery
kubectl get services
```

## Environment Configuration

### Database Providers
Each service reads a local `.env` file (see `.env.example`). Database provider is selected with:
```
DATABASE_PROVIDER=sqlite|inmemory|postgres|mysql|supabase
```

### Service Communication
Services communicate via container names and environment variables:
- AUTH_SERVICE_URL: http://auth-service:8004
- USERS_SERVICE_URL: http://users-service:8003
- etc.

## Monitoring and Logging

### Planned Monitoring
- **Prometheus**: Metrics collection
- **Grafana**: Visualization and dashboards
- **ELK Stack**: Log aggregation and analysis

### Service Health Checks
- Database connectivity checks
- Service-to-service communication tests
- Resource utilization monitoring

## Security Considerations

### Production Security
- JWT secrets in secrets manager
- Internal API keys in Kubernetes Secrets
- Database credentials in secure storage
- Network policies for service-to-service communication

### Development Security
- Development placeholders in .env.example
- Secret scanning in CI/CD pipeline
- Local development with in-memory provider

## Rollback and Disaster Recovery

### Rollback Procedures
1. **Version Control**: Git tags for deployment versions
2. **Container Images**: Docker image versioning
3. **Database Migrations**: Backward-compatible migrations
4. **Configuration Management**: Environment-specific configurations

### Disaster Recovery
1. **Backup Strategy**: Database backups
2. **Recovery Procedures**: Service restoration
3. **Testing**: DR drills and validation
4. **Documentation**: Recovery runbooks

## Next Steps

### Immediate Actions
1. Complete CI/CD pipeline setup
2. Implement Docker deployment strategy
3. Create Kubernetes manifests
4. Set up monitoring and logging

### Medium-term Goals
1. Implement Helm charts for service deployment
2. Add automated testing and validation
3. Set up cloud infrastructure
4. Implement advanced monitoring

### Long-term Goals
1. Multi-cluster deployment
2. Advanced observability
3. Automated scaling and self-healing
4. Disaster recovery automation

## Conclusion

This deployment plan provides a comprehensive strategy for deploying the GDB microservices platform across multiple environments. The modular architecture and provider abstraction ensure flexibility and scalability while maintaining operational simplicity.

The deployment strategy balances local development convenience with production-grade reliability, providing clear paths for progression from development to production environments.