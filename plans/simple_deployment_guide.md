# GDB Microservices Platform - Simple Deployment Guide

## Overview

This is a beginner-friendly guide for deploying the GDB microservices platform. It focuses on the essential CI/CD pipeline and deployment steps, removing complex monitoring and extensive testing.

## What You'll Need

### Prerequisites
- GitHub account with repository access
- Docker installed on your machine
- Basic understanding of Docker and Git

### Tools
- Git (for version control)
- Docker (for containerization)
- Docker Compose (for local deployment)

## Step 1: Setup Repository

### 1.1 Clone the Repository
```bash
# Clone the GDB microservices platform repository
git clone https://github.com/your-org/gdb-service-python-fullstack-sol-v1.git
cd gdb-service-python-fullstack-sol-v1
```

### 1.2 Setup Environment
```bash
# Check the current directory
ls -la

# Look at the README for initial setup
cat README.md
```

## Step 2: Install Dependencies

### 2.1 Install Python Dependencies
```bash
# Install Python dependencies for all services
python setup_all.py
```

### 2.2 Install Frontend Dependencies
```bash
# Navigate to frontend directory
cd frontend

# Install npm dependencies
npm install

# Go back to root directory
cd ..
```

## Step 3: Setup Database Provider

### 3.1 Choose Your Database
You can use one of these database providers:

#### Option A: In-Memory (Easiest for beginners)
```bash
# Setup in-memory provider
python setup_provider.py inmemory
```

#### Option B: SQLite (Local files)
```bash
# Setup SQLite provider
python setup_provider.py sqlite
```

#### Option C: PostgreSQL (More features)
```bash
# Setup PostgreSQL provider
python setup_provider.py postgres
```

#### Option D: MySQL (Alternative)
```bash
# Setup MySQL provider
python setup_provider.py mysql
```

#### Option E: Supabase (Cloud)
```bash
# For Supabase, first copy the example file
cp supabase.env.example .env

# Edit .env file with your Supabase credentials
# Then setup Supabase provider
python setup_provider.py supabase
```

## Step 4: Run Services Locally

### 4.1 Run All Services
```bash
# Run all services with Docker Compose
python docker_up.py inmemory

# This will start all 8 microservices + frontend
# Open http://localhost:3000 in your browser
# Login with: admin / Welcome@1
```

### 4.2 Run with Different Databases
```bash
# Run with SQLite
python docker_up.py sqlite

# Run with PostgreSQL
python docker_up.py postgres

# Run with MySQL
python docker_up.py mysql

# Run with Supabase
python docker_up.py supabase
```

### 4.3 Stop Services
```bash
# Stop all services
python docker_up.py down

# Stop and remove volumes (wipes data)
python docker_up.py down -v
```

## Step 5: Basic Testing

### 5.1 Test Individual Services
```bash
# Test auth service
cd auth_service
DATABASE_PROVIDER=inmemory python -m pytest tests/ -v
cd ..

# Test users service
cd users_service
DATABASE_PROVIDER=inmemory python -m pytest tests/ -v
cd ..

# Test accounts service
cd accounts_service
DATABASE_PROVIDER=inmemory python -m pytest tests/ -v
cd ..

# Test transactions service
cd transactions_service
DATABASE_PROVIDER=inmemory python -m pytest tests/ -v
cd ..
```

### 5.2 Test Frontend
```bash
# Navigate to frontend directory
cd frontend

# Run frontend tests
npm test

# Build frontend for production
npm run build

# Go back to root directory
cd ..
```

## Step 6: Basic CI/CD Setup (Optional)

### 6.1 Create GitHub Repository
1. Go to GitHub.com
2. Click "New repository"
3. Create a new repository
4. Push your code

### 6.2 Setup GitHub Actions
```yaml
# Create .github/workflows/ci.yml
name: CI

on:
  push:
    branches: [main]
  pull_request:
    branches: [main]

jobs:
  test:
    runs-on: ubuntu-latest
    strategy:
      matrix:
        service: [auth_service, users_service, accounts_service, transactions_service]
    steps:
    - uses: actions/checkout@v3
    - uses: actions/setup-python@v3
      with:
        python-version: "3.12"
    - name: Install dependencies
      run: |
        pip install -r ${{ matrix.service }}/requirements.txt
        pip install pytest
    - name: Run tests
      run: |
        cd ${{ matrix.service }}
        DATABASE_PROVIDER=inmemory python -m pytest -v
        cd ..
```

## Step 7: Production Deployment (Optional)

### 7.1 Docker Deployment
```bash
# Build Docker images
for service in auth_service users_service accounts_service transactions_service; do
  docker build -f $service/Dockerfile -t gdb/$service:latest .
done

# Run with Docker Compose
python docker_up.py postgres
```

### 7.2 Kubernetes Deployment (Optional)
```bash
# Install kubectl
# Create Kubernetes cluster
# Apply deployment manifests
kubectl apply -f k8s/

# Scale services
kubectl scale deployment auth-service --replicas=3
```

## Step 8: Monitor and Maintain

### 8.1 Check Service Health
```bash
# Check if services are running
ps aux | grep python

# Check Docker containers
docker ps

# Check logs
docker logs auth-service
```

### 8.2 Update Services
```bash
# Update a service
python docker_up.py postgres --build

# Or update individual service
docker-compose up --build auth-service
```

### 8.3 Backup Data
```bash
# Backup PostgreSQL data
docker exec postgres pg_dump -U postgres gdb_auth_db > backup.sql

# Backup MySQL data
docker exec mysql mysqldump -u root -p gdb_auth_db > backup.sql
```

## Quick Reference Commands

### Common Commands
```bash
# Setup everything
python setup_all.py
python setup_provider.py sqlite
python docker_up.py sqlite

# Test a service
cd auth_service
DATABASE_PROVIDER=inmemory python -m pytest tests/ -v
cd ..

# Stop services
python docker_up.py down

# Update services
python docker_up.py sqlite --build
```

### Service-Specific Commands
```bash
# Auth service
python docker_up.py sqlite --build
# Open http://localhost:8004

# Users service
python docker_up.py sqlite --build
# Open http://localhost:8003

# Accounts service
python docker_up.py sqlite --build
# Open http://localhost:8001

# Transactions service
python docker_up.py sqlite --build
# Open http://localhost:8002

# Frontend
python docker_up.py sqlite --build
# Open http://localhost:3000
```

## Troubleshooting

### Common Issues

#### Issue: Services won't start
**Solution:**
```bash
# Check Docker is running
docker ps

# Check for port conflicts
netstat -tlnp | grep 8000

# Try with different ports
python docker_up.py sqlite
```

#### Issue: Database connection failed
**Solution:**
```bash
# Check database setup
python setup_provider.py sqlite

# Try with in-memory provider
python docker_up.py inmemory
```

#### Issue: Frontend won't load
**Solution:**
```bash
# Check frontend build
cd frontend
npm run build
cd ..

# Try with in-memory provider
python docker_up.py inmemory
```

### Get Help
- **GitHub Repository**: Check the repository for issues and documentation
- **Docker Community**: Docker documentation and forums
- **Stack Overflow**: Search for solutions to common problems
- **GitHub Discussions**: Ask questions and get help from the community

## Next Steps

### Beginner Path
1. **Complete Step 1-4**: Get the basic setup working
2. **Test Step 5**: Run basic tests
3. **Try Step 6**: Setup CI/CD (optional)
4. **Explore Step 7**: Try production deployment (optional)

### Intermediate Path
1. **Complete all steps**: Get everything working
2. **Customize configuration**: Modify settings to fit your needs
3. **Add monitoring**: Setup basic monitoring
4. **Implement backups**: Setup backup procedures

### Advanced Path
1. **Complete all steps**: Master the deployment
2. **Optimize performance**: Tune for better performance
3. **Implement security**: Add security measures
4. **Scale horizontally**: Scale for production

## Conclusion

This simple deployment guide provides a step-by-step approach to deploying the GDB microservices platform. It focuses on the essential steps and removes complex details, making it beginner-friendly.

The guide covers:
- Repository setup
- Dependency installation
- Database provider setup
- Service deployment
- Basic testing
- CI/CD setup (optional)
- Production deployment (optional)
- Monitoring and maintenance

Follow the steps in order, and you'll have a working GDB microservices platform in no time!