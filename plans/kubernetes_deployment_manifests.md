# GDB Microservices Platform - Kubernetes Deployment Manifests

## Overview

This document provides comprehensive Kubernetes deployment manifests for the Global Digital Bank (GDB) microservices platform. The manifests include deployments, services, configmaps, secrets, and other resources required for deploying all 8 microservices plus the API gateway, registry service, and frontend in a Kubernetes cluster.

## Kubernetes Architecture

### Cluster Configuration
- **API Version**: apps/v1, v1, networking.k8s.io/v1, core/v1
- **Namespace**: gdb (default)
- **Storage Classes**: standard (for local storage), gp2 (for cloud storage)
- **Ingress Controller**: NGINX Ingress Controller
- **Service Mesh**: Istio (optional, for advanced traffic management)

### Resource Management
- **CPU Requests**: 250m for most services, 100m for infrastructure services
- **Memory Requests**: 256Mi for most services, 128Mi for infrastructure services
- **CPU Limits**: 500m for most services, 200m for infrastructure services
- **Memory Limits**: 512Mi for most services, 256Mi for infrastructure services

## Core Services Deployment

### 1. Auth Service

#### Deployment Manifest
```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: auth-service
  labels:
    app: auth-service
    version: v1.0.0
spec:
  replicas: 3
  selector:
    matchLabels:
      app: auth-service
  template:
    metadata:
      labels:
        app: auth-service
        version: v1.0.0
    spec:
      containers:
      - name: auth-service
        image: ghcr.io/your-org/gdb-auth-service:v1.0.0
        ports:
        - containerPort: 8004
          name: http
        env:
        - name: DATABASE_PROVIDER
          valueFrom:
            configMapKeyRef:
              name: app-config
              key: DATABASE_PROVIDER
        - name: DATABASE_URL
          valueFrom:
            secretKeyRef:
              name: db-credentials
              key: AUTH_DATABASE_URL
        - name: JWT_SECRET
          valueFrom:
            secretKeyRef:
              name: app-secrets
              key: JWT_SECRET
        - name: INTERNAL_API_KEY
          valueFrom:
            secretKeyRef:
              name: app-secrets
              key: INTERNAL_API_KEY
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
            port: http
          initialDelaySeconds: 30
          periodSeconds: 10
          timeoutSeconds: 5
          failureThreshold: 3
        readinessProbe:
          httpGet:
            path: /ready
            port: http
          initialDelaySeconds: 5
          periodSeconds: 5
          timeoutSeconds: 3
          failureThreshold: 3
        lifecycle:
          preStop:
            exec:
              command: ["sh", "-c", "sleep 10"]
        volumeMounts:
        - name: temp-storage
          mountPath: /tmp
      volumes:
      - name: temp-storage
        emptyDir:
          medium: Memory
          sizeLimit: "1Gi"
      imagePullSecrets:
      - name: regcred
```

#### Service Manifest
```yaml
apiVersion: v1
kind: Service
metadata:
  name: auth-service
  labels:
    app: auth-service
spec:
  selector:
    app: auth-service
  ports:
  - protocol: TCP
    port: 8004
    targetPort: http
    name: http
  type: ClusterIP
  sessionAffinity: None
```

### 2. Users Service

#### Deployment Manifest
```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: users-service
  labels:
    app: users-service
    version: v1.0.0
spec:
  replicas: 3
  selector:
    matchLabels:
      app: users-service
  template:
    metadata:
      labels:
        app: users-service
        version: v1.0.0
    spec:
      containers:
      - name: users-service
        image: ghcr.io/your-org/gdb-users-service:v1.0.0
        ports:
        - containerPort: 8003
          name: http
        env:
        - name: DATABASE_PROVIDER
          valueFrom:
            configMapKeyRef:
              name: app-config
              key: DATABASE_PROVIDER
        - name: DATABASE_URL
          valueFrom:
            secretKeyRef:
              name: db-credentials
              key: USERS_DATABASE_URL
        - name: JWT_SECRET
          valueFrom:
            secretKeyRef:
              name: app-secrets
              key: JWT_SECRET
        - name: INTERNAL_API_KEY
          valueFrom:
            secretKeyRef:
              name: app-secrets
              key: INTERNAL_API_KEY
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
            port: http
          initialDelaySeconds: 30
          periodSeconds: 10
        readinessProbe:
          httpGet:
            path: /ready
            port: http
          initialDelaySeconds: 5
          periodSeconds: 5
        volumeMounts:
        - name: temp-storage
          mountPath: /tmp
      volumes:
      - name: temp-storage
        emptyDir:
          medium: Memory
          sizeLimit: "1Gi"
      imagePullSecrets:
      - name: regcred
```

#### Service Manifest
```yaml
apiVersion: v1
kind: Service
metadata:
  name: users-service
  labels:
    app: users-service
spec:
  selector:
    app: users-service
  ports:
  - protocol: TCP
    port: 8003
    targetPort: http
    name: http
  type: ClusterIP
```

### 3. Accounts Service

#### Deployment Manifest
```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: accounts-service
  labels:
    app: accounts-service
    version: v1.0.0
spec:
  replicas: 3
  selector:
    matchLabels:
      app: accounts-service
  template:
    metadata:
      labels:
        app: accounts-service
        version: v1.0.0
    spec:
      containers:
      - name: accounts-service
        image: ghcr.io/your-org/gdb-accounts-service:v1.0.0
        ports:
        - containerPort: 8001
          name: http
        env:
        - name: DATABASE_PROVIDER
          valueFrom:
            configMapKeyRef:
              name: app-config
              key: DATABASE_PROVIDER
        - name: DATABASE_URL
          valueFrom:
            secretKeyRef:
              name: db-credentials
              key: ACCOUNTS_DATABASE_URL
        - name: JWT_SECRET
          valueFrom:
            secretKeyRef:
              name: app-secrets
              key: JWT_SECRET
        - name: INTERNAL_API_KEY
          valueFrom:
            secretKeyRef:
              name: app-secrets
              key: INTERNAL_API_KEY
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
            port: http
          initialDelaySeconds: 30
          periodSeconds: 10
        readinessProbe:
          httpGet:
            path: /ready
            port: http
          initialDelaySeconds: 5
          periodSeconds: 5
        volumeMounts:
        - name: temp-storage
          mountPath: /tmp
      volumes:
      - name: temp-storage
        emptyDir:
          medium: Memory
          sizeLimit: "1Gi"
      imagePullSecrets:
      - name: regcred
```

#### Service Manifest
```yaml
apiVersion: v1
kind: Service
metadata:
  name: accounts-service
  labels:
    app: accounts-service
spec:
  selector:
    app: accounts-service
  ports:
  - protocol: TCP
    port: 8001
    targetPort: http
    name: http
  type: ClusterIP
```

### 4. Transactions Service

#### Deployment Manifest
```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: transactions-service
  labels:
    app: transactions-service
    version: v1.0.0
spec:
  replicas: 3
  selector:
    matchLabels:
      app: transactions-service
  template:
    metadata:
      labels:
        app: transactions-service
        version: v1.0.0
    spec:
      containers:
      - name: transactions-service
        image: ghcr.io/your-org/gdb-transactions-service:v1.0.0
        ports:
        - containerPort: 8002
          name: http
        env:
        - name: DATABASE_PROVIDER
          valueFrom:
            configMapKeyRef:
              name: app-config
              key: DATABASE_PROVIDER
        - name: DB_HOST
          valueFrom:
            secretKeyRef:
              name: db-credentials
              key: TRANSACTIONS_DB_HOST
        - name: DB_PORT
          valueFrom:
            secretKeyRef:
              name: db-credentials
              key: TRANSACTIONS_DB_PORT
        - name: DB_USER
          valueFrom:
            secretKeyRef:
              name: db-credentials
              key: TRANSACTIONS_DB_USER
        - name: DB_PASSWORD
          valueFrom:
            secretKeyRef:
              name: db-credentials
              key: TRANSACTIONS_DB_PASSWORD
        - name: DB_NAME
          valueFrom:
            secretKeyRef:
              name: db-credentials
              key: TRANSACTIONS_DB_NAME
        - name: JWT_SECRET
          valueFrom:
            secretKeyRef:
              name: app-secrets
              key: JWT_SECRET
        - name: INTERNAL_API_KEY
          valueFrom:
            secretKeyRef:
              name: app-secrets
              key: INTERNAL_API_KEY
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
            port: http
          initialDelaySeconds: 30
          periodSeconds: 10
        readinessProbe:
          httpGet:
            path: /ready
            port: http
          initialDelaySeconds: 5
          periodSeconds: 5
        volumeMounts:
        - name: temp-storage
          mountPath: /tmp
      volumes:
      - name: temp-storage
        emptyDir:
          medium: Memory
          sizeLimit: "1Gi"
      imagePullSecrets:
      - name: regcred
```

#### Service Manifest
```yaml
apiVersion: v1
kind: Service
metadata:
  name: transactions-service
  labels:
    app: transactions-service
spec:
  selector:
    app: transactions-service
  ports:
  - protocol: TCP
    port: 8002
    targetPort: http
    name: http
  type: ClusterIP
```

### 5. Aadhar Service

#### Deployment Manifest
```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: aadhar-service
  labels:
    app: aadhar-service
    version: v1.0.0
spec:
  replicas: 2
  selector:
    matchLabels:
      app: aadhar-service
  template:
    metadata:
      labels:
        app: aadhar-service
        version: v1.0.0
    spec:
      containers:
      - name: aadhar-service
        image: ghcr.io/your-org/gdb-aadhar-service:v1.0.0
        ports:
        - containerPort: 8005
          name: http
        env:
        - name: DATABASE_PROVIDER
          valueFrom:
            configMapKeyRef:
              name: app-config
              key: DATABASE_PROVIDER
        - name: DATABASE_URL
          valueFrom:
            secretKeyRef:
              name: db-credentials
              key: AADHAR_DATABASE_URL
        - name: JWT_SECRET
          valueFrom:
            secretKeyRef:
              name: app-secrets
              key: JWT_SECRET
        - name: INTERNAL_API_KEY
          valueFrom:
            secretKeyRef:
              name: app-secrets
              key: INTERNAL_API_KEY
        resources:
          requests:
            memory: "128Mi"
            cpu: "100m"
          limits:
            memory: "256Mi"
            cpu: "200m"
        livenessProbe:
          httpGet:
            path: /health
            port: http
          initialDelaySeconds: 30
          periodSeconds: 10
        readinessProbe:
          httpGet:
            path: /ready
            port: http
          initialDelaySeconds: 5
          periodSeconds: 5
        volumeMounts:
        - name: temp-storage
          mountPath: /tmp
      volumes:
      - name: temp-storage
        emptyDir:
          medium: Memory
          sizeLimit: "512Mi"
      imagePullSecrets:
      - name: regcred
```

#### Service Manifest
```yaml
apiVersion: v1
kind: Service
metadata:
  name: aadhar-service
  labels:
    app: aadhar-service
spec:
  selector:
    app: aadhar-service
  ports:
  - protocol: TCP
    port: 8005
    targetPort: http
    name: http
  type: ClusterIP
```

### 6. Company Service

#### Deployment Manifest
```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: company-service
  labels:
    app: company-service
    version: v1.0.0
spec:
  replicas: 2
  selector:
    matchLabels:
      app: company-service
  template:
    metadata:
      labels:
        app: company-service
        version: v1.0.0
    spec:
      containers:
      - name: company-service
        image: ghcr.io/your-org/gdb-company-service:v1.0.0
        ports:
        - containerPort: 8006
          name: http
        env:
        - name: DATABASE_PROVIDER
          valueFrom:
            configMapKeyRef:
              name: app-config
              key: DATABASE_PROVIDER
        - name: DATABASE_URL
          valueFrom:
            secretKeyRef:
              name: db-credentials
              key: COMPANY_DATABASE_URL
        - name: JWT_SECRET
          valueFrom:
            secretKeyRef:
              name: app-secrets
              key: JWT_SECRET
        - name: INTERNAL_API_KEY
          valueFrom:
            secretKeyRef:
              name: app-secrets
              key: INTERNAL_API_KEY
        resources:
          requests:
            memory: "128Mi"
            cpu: "100m"
          limits:
            memory: "256Mi"
            cpu: "200m"
        livenessProbe:
          httpGet:
            path: /health
            port: http
          initialDelaySeconds: 30
          periodSeconds: 10
        readinessProbe:
          httpGet:
            path: /ready
            port: http
          initialDelaySeconds: 5
          periodSeconds: 5
        volumeMounts:
        - name: temp-storage
          mountPath: /tmp
      volumes:
      - name: temp-storage
        emptyDir:
          medium: Memory
          sizeLimit: "512Mi"
      imagePullSecrets:
      - name: regcred
```

#### Service Manifest
```yaml
apiVersion: v1
kind: Service
metadata:
  name: company-service
  labels:
    app: company-service
spec:
  selector:
    app: company-service
  ports:
  - protocol: TCP
    port: 8006
    targetPort: http
    name: http
  type: ClusterIP
```

### 7. Notification Service

#### Deployment Manifest
```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: notification-service
  labels:
    app: notification-service
    version: v1.0.0
spec:
  replicas: 2
  selector:
    matchLabels:
      app: notification-service
  template:
    metadata:
      labels:
        app: notification-service
        version: v1.0.0
    spec:
      containers:
      - name: notification-service
        image: ghcr.io/your-org/gdb-notification-service:v1.0.0
        ports:
        - containerPort: 8007
          name: http
        env:
        - name: DATABASE_PROVIDER
          valueFrom:
            configMapKeyRef:
              name: app-config
              key: DATABASE_PROVIDER
        - name: DATABASE_URL
          valueFrom:
            secretKeyRef:
              name: db-credentials
              key: NOTIFICATION_DATABASE_URL
        - name: JWT_SECRET
          valueFrom:
            secretKeyRef:
              name: app-secrets
              key: JWT_SECRET
        - name: INTERNAL_API_KEY
          valueFrom:
            secretKeyRef:
              name: app-secrets
              key: INTERNAL_API_KEY
        resources:
          requests:
            memory: "128Mi"
            cpu: "100m"
          limits:
            memory: "256Mi"
            cpu: "200m"
        livenessProbe:
          httpGet:
            path: /health
            port: http
          initialDelaySeconds: 30
          periodSeconds: 10
        readinessProbe:
          httpGet:
            path: /ready
            port: http
          initialDelaySeconds: 5
          periodSeconds: 5
        volumeMounts:
        - name: temp-storage
          mountPath: /tmp
      volumes:
      - name: temp-storage
        emptyDir:
          medium: Memory
          sizeLimit: "512Mi"
      imagePullSecrets:
      - name: regcred
```

#### Service Manifest
```yaml
apiVersion: v1
kind: Service
metadata:
  name: notification-service
  labels:
    app: notification-service
spec:
  selector:
    app: notification-service
  ports:
  - protocol: TCP
    port: 8007
    targetPort: http
    name: http
  type: ClusterIP
```

### 8. Payment Gateway Service

#### Deployment Manifest
```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: payment-gateway-service
  labels:
    app: payment-gateway-service
    version: v1.0.0
spec:
  replicas: 2
  selector:
    matchLabels:
      app: payment-gateway-service
  template:
    metadata:
      labels:
        app: payment-gateway-service
        version: v1.0.0
    spec:
      containers:
      - name: payment-gateway-service
        image: ghcr.io/your-org/gdb-payment-gateway-service:v1.0.0
        ports:
        - containerPort: 8008
          name: http
        env:
        - name: DATABASE_PROVIDER
          valueFrom:
            configMapKeyRef:
              name: app-config
              key: DATABASE_PROVIDER
        - name: DATABASE_URL
          valueFrom:
            secretKeyRef:
              name: db-credentials
              key: PAYMENT_GATEWAY_DATABASE_URL
        - name: JWT_SECRET
          valueFrom:
            secretKeyRef:
              name: app-secrets
              key: JWT_SECRET
        - name: INTERNAL_API_KEY
          valueFrom:
            secretKeyRef:
              name: app-secrets
              key: INTERNAL_API_KEY
        resources:
          requests:
            memory: "128Mi"
            cpu: "100m"
          limits:
            memory: "256Mi"
            cpu: "200m"
        livenessProbe:
          httpGet:
            path: /health
            port: http
          initialDelaySeconds: 30
          periodSeconds: 10
        readinessProbe:
          httpGet:
            path: /ready
            port: http
          initialDelaySeconds: 5
          periodSeconds: 5
        volumeMounts:
        - name: temp-storage
          mountPath: /tmp
      volumes:
      - name: temp-storage
        emptyDir:
          medium: Memory
          sizeLimit: "512Mi"
      imagePullSecrets:
      - name: regcred
```

#### Service Manifest
```yaml
apiVersion: v1
kind: Service
metadata:
  name: payment-gateway-service
  labels:
    app: payment-gateway-service
spec:
  selector:
    app: payment-gateway-service
  ports:
  - protocol: TCP
    port: 8008
    targetPort: http
    name: http
  type: ClusterIP
```

### 9. Registry Service

#### Deployment Manifest
```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: registry-service
  labels:
    app: registry-service
    version: v1.0.0
spec:
  replicas: 1
  selector:
    matchLabels:
      app: registry-service
  template:
    metadata:
      labels:
        app: registry-service
        version: v1.0.0
    spec:
      containers:
      - name: registry-service
        image: ghcr.io/your-org/gdb-registry-service:v1.0.0
        ports:
        - containerPort: 8010
          name: http
        env:
        - name: DATABASE_PROVIDER
          valueFrom:
            configMapKeyRef:
              name: app-config
              key: DATABASE_PROVIDER
        - name: DATABASE_URL
          valueFrom:
            secretKeyRef:
              name: db-credentials
              key: REGISTRY_DATABASE_URL
        - name: JWT_SECRET
          valueFrom:
            secretKeyRef:
              name: app-secrets
              key: JWT_SECRET
        - name: INTERNAL_API_KEY
          valueFrom:
            secretKeyRef:
              name: app-secrets
              key: INTERNAL_API_KEY
        resources:
          requests:
            memory: "128Mi"
            cpu: "100m"
          limits:
            memory: "256Mi"
            cpu: "200m"
        livenessProbe:
          httpGet:
            path: /health
            port: http
          initialDelaySeconds: 30
          periodSeconds: 10
        readinessProbe:
          httpGet:
            path: /ready
            port: http
          initialDelaySeconds: 5
          periodSeconds: 5
        volumeMounts:
        - name: temp-storage
          mountPath: /tmp
      volumes:
      - name: temp-storage
        emptyDir:
          medium: Memory
          sizeLimit: "512Mi"
      imagePullSecrets:
      - name: regcred
```

#### Service Manifest
```yaml
apiVersion: v1
kind: Service
metadata:
  name: registry-service
  labels:
    app: registry-service
spec:
  selector:
    app: registry-service
  ports:
  - protocol: TCP
    port: 8010
    targetPort: http
    name: http
  type: ClusterIP
```

### 10. API Gateway Service

#### Deployment Manifest
```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: api-gateway
  labels:
    app: api-gateway
    version: v1.0.0
spec:
  replicas: 2
  selector:
    matchLabels:
      app: api-gateway
  template:
    metadata:
      labels:
        app: api-gateway
        version: v1.0.0
    spec:
      containers:
      - name: api-gateway
        image: ghcr.io/your-org/gdb-api-gateway:v1.0.0
        ports:
        - containerPort: 8000
          name: http
        env:
        - name: GATEWAY_ACCOUNTS_URL
          value: "http://accounts-service:8001"
        - name: GATEWAY_TRANSACTIONS_URL
          value: "http://transactions-service:8002"
        - name: GATEWAY_USERS_URL
          value: "http://users-service:8003"
        - name: GATEWAY_AUTH_URL
          value: "http://auth-service:8004"
        - name: GATEWAY_AADHAR_URL
          value: "http://aadhar-service:8005"
        - name: GATEWAY_COMPANY_URL
          value: "http://company-service:8006"
        - name: GATEWAY_NOTIFICATION_URL
          value: "http://notification-service:8007"
        - name: GATEWAY_PAYMENT_URL
          value: "http://payment-gateway-service:8008"
        - name: GATEWAY_RATE_LIMIT_PER_MIN
          value: "600"
        - name: JWT_SECRET
          valueFrom:
            secretKeyRef:
              name: app-secrets
              key: JWT_SECRET
        - name: INTERNAL_API_KEY
          valueFrom:
            secretKeyRef:
              name: app-secrets
              key: INTERNAL_API_KEY
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
            port: http
          initialDelaySeconds: 30
          periodSeconds: 10
        readinessProbe:
          httpGet:
            path: /ready
            port: http
          initialDelaySeconds: 5
          periodSeconds: 5
        volumeMounts:
        - name: temp-storage
          mountPath: /tmp
      volumes:
      - name: temp-storage
        emptyDir:
          medium: Memory
          sizeLimit: "1Gi"
      imagePullSecrets:
      - name: regcred
```

#### Service Manifest
```yaml
apiVersion: v1
kind: Service
metadata:
  name: api-gateway
  labels:
    app: api-gateway
spec:
  selector:
    app: api-gateway
  ports:
  - protocol: TCP
    port: 8000
    targetPort: http
    name: http
  type: ClusterIP
```

### 11. Frontend Service

#### Deployment Manifest
```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: frontend
  labels:
    app: frontend
    version: v1.0.0
spec:
  replicas: 2
  selector:
    matchLabels:
      app: frontend
  template:
    metadata:
      labels:
        app: frontend
        version: v1.0.0
    spec:
      containers:
      - name: frontend
        image: ghcr.io/your-org/gdb-frontend:v1.0.0
        ports:
        - containerPort: 3000
          name: http
        env:
        - name: REACT_APP_API_URL
          value: "http://localhost:8000"
        - name: REACT_APP_INTERNAL_API_KEY
          valueFrom:
            secretKeyRef:
              name: app-secrets
              key: INTERNAL_API_KEY
        resources:
          requests:
            memory: "128Mi"
            cpu: "100m"
          limits:
            memory: "256Mi"
            cpu: "200m"
        livenessProbe:
          httpGet:
            path: /
            port: http
          initialDelaySeconds: 30
          periodSeconds: 10
        readinessProbe:
          httpGet:
            path: /
            port: http
          initialDelaySeconds: 5
          periodSeconds: 5
        volumeMounts:
        - name: frontend-cache
          mountPath: /app/node_modules
      volumes:
      - name: frontend-cache
        emptyDir:
          medium: Memory
          sizeLimit: "512Mi"
      imagePullSecrets:
      - name: regcred
```

#### Service Manifest
```yaml
apiVersion: v1
kind: Service
metadata:
  name: frontend
spec:
  selector:
    app: frontend
  ports:
  - protocol: TCP
    port: 3000
    targetPort: http
    name: http
  type: ClusterIP
```

## Supporting Resources

### 1. ConfigMap

```yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: app-config
  labels:
    app: gdb-platform
spec:
  data:
    DATABASE_PROVIDER: "postgres"
    LOG_LEVEL: "INFO"
    REDIS_URL: "redis://redis:6379"
    KAFKA_BOOTSTRAP_SERVERS: "kafka:9092"
    ELASTICSEARCH_URL: "http://elasticsearch:9200"
```

### 2. Secrets

```yaml
apiVersion: v1
kind: Secret
metadata:
  name: db-credentials
  labels:
    app: gdb-platform
type: Opaque
spec:
  data:
    AUTH_DATABASE_URL: cG9zdGdyZXM6cG9zdGdyZXAxMjM0QHRlc3QwMA==
    USERS_DATABASE_URL: cG9zdGdyZXM6cG9zdGdyZXAxMjM0QHRlc3QwMQ==
    ACCOUNTS_DATABASE_URL: cG9zdGdyZXM6cG9zdGdyZXAxMjM0QHRlc3QwMg==
    TRANSACTIONS_DATABASE_URL: cG9zdGdyZXM6cG9zdGdyZXAxMjM0QHRlc3QwMw==
    AADHAR_DATABASE_URL: cG9zdGdyZXM6cG9zdGdyZXAxMjM0QHRlc3QwNA==
    COMPANY_DATABASE_URL: cG9zdGdyZXM6cG9zdGdyZXAxMjM0QHRlc3QwNQ==
    NOTIFICATION_DATABASE_URL: cG9zdGdyZXM6cG9zdGdyZXAxMjM0QHRlc3QwNg==
    PAYMENT_GATEWAY_DATABASE_URL: cG9zdGdyZXM6cG9zdGdyZXAxMjM0QHRlc3QwNw==
    REGISTRY_DATABASE_URL: cG9zdGdyZXM6cG9zdGdyZXAxMjM0QHRlc3QwOA==
    TRANSACTIONS_DB_HOST: cG9zdGdyZXMK
    TRANSACTIONS_DB_PORT: "5432"
    TRANSACTIONS_DB_USER: cG9zdGdyZXMK
    TRANSACTIONS_DB_PASSWORD: cG9zdGdyZXAxMjM0NQ==
    TRANSACTIONS_DB_NAME: Z2RiX3RyYW5zYWN0aW9ucw==
  stringData:
    AUTH_DATABASE_URL: postgresql://postgres:postgres@postgres:5432/gdb_auth_db
    USERS_DATABASE_URL: postgresql://postgres:postgres@postgres:5432/gdb_users_db
    ACCOUNTS_DATABASE_URL: postgresql://postgres:postgres@postgres:5432/gdb_accounts_db
    TRANSACTIONS_DATABASE_URL: postgresql://postgres:postgres@postgres:5432/gdb_transactions_db
    AADHAR_DATABASE_URL: postgresql://postgres:postgres@postgres:5432/gdb_aadhar_db
    COMPANY_DATABASE_URL: postgresql://postgres:postgres@postgres:5432/gdb_company_db
    NOTIFICATION_DATABASE_URL: postgresql://postgres:postgres@postgres:5432/gdb_notification_db
    PAYMENT_GATEWAY_DATABASE_URL: postgresql://postgres:postgres@postgres:5432/gdb_payment_gateway_db
    REGISTRY_DATABASE_URL: postgresql://postgres:postgres@postgres:5432/gdb_registry_db
```

```yaml
apiVersion: v1
kind: Secret
metadata:
  name: app-secrets
  labels:
    app: gdb-platform
type: Opaque
spec:
  data:
    JWT_SECRET: c2VjcmV0LWtleS1mb3Itand0LXNpZ25pbmctc2hhMjU2
    INTERNAL_API_KEY: aW5uZXJuYWwtYXBpLWtleS0xMjM0NTY3ODkw
    ENCRYPTION_KEY: eW91ci1zdXBlci1lbmNyeXB0aW9uLWtleQ==
  stringData:
    JWT_SECRET: your-super-secret-jwt-key-for-signing
    INTERNAL_API_KEY: internal-api-key-1234567890
    ENCRYPTION_KEY: your-super-encryption-key
```

### 3. Persistent Volume Claims

```yaml
apiVersion: v1
kind: PersistentVolumeClaim
metadata:
  name: pgdata
  labels:
    app: gdb-platform
spec:
  accessModes:
  - ReadWriteOnce
  resources:
    requests:
      storage: 1Gi
  storageClassName: standard
```

```yaml
apiVersion: v1
kind: PersistentVolumeClaim
metadata:
  name: mysqldata
  labels:
    app: gdb-platform
spec:
  accessModes:
  - ReadWriteOnce
  resources:
    requests:
      storage: 1Gi
  storageClassName: standard
```

### 4. Ingress

```yaml
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: gdb-ingress
  labels:
    app: gdb-platform
  annotations:
    nginx.ingress.kubernetes.io/rewrite-target: /$1
    nginx.ingress.kubernetes.io/use-regex: "true"
spec:
  ingressClassName: nginx
  rules:
  - host: localhost
    http:
      paths:
      - path: /api/(.*)
        pathType: ImplementationSpecific
        backend:
          service:
            name: api-gateway
            port:
              number: 8000
      - path: /(.*)
        pathType: ImplementationSpecific
        backend:
          service:
            name: frontend
            port:
              number: 3000
```

### 5. Network Policies

```yaml
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: gdb-network-policy
  labels:
    app: gdb-platform
spec:
  podSelector:
    matchLabels:
      app: gdb-platform
  policyTypes:
  - Ingress
  - Egress
  ingress:
  - from:
    - podSelector:
        matchLabels:
          app: gdb-platform
    ports:
    - protocol: TCP
      port: 8000
    - protocol: TCP
      port: 8001
    - protocol: TCP
      port: 8002
    - protocol: TCP
      port: 8003
    - protocol: TCP
      port: 8004
    - protocol: TCP
      port: 8005
    - protocol: TCP
      port: 8006
    - protocol: TCP
      port: 8007
    - protocol: TCP
      port: 8008
    - protocol: TCP
      port: 8010
  egress:
  - to: []
    ports:
    - protocol: TCP
      port: 53
    - protocol: TCP
      port: 80
    - protocol: TCP
      port: 443
    - protocol: TCP
      port: 5432
    - protocol: TCP
      port: 3306
    - protocol: TCP
      port: 6379
    - protocol: TCP
      port: 9092
```

## Deployment Strategy

### Rolling Updates
```bash
# Deploy with rolling updates
kubectl apply -f k8s/

# Check deployment status
kubectl get deployments

# Rollback to previous version
kubectl rollout undo deployment/auth-service
kubectl rollout status deployment/auth-service
```

### Blue-Green Deployment
```bash
# Create blue-green deployment
kubectl apply -f k8s/blue-green.yaml

# Switch traffic to green environment
kubectl annotate deployment/auth-service environment=green

# Verify deployment
kubectl get pods -l app=auth-service
```

### Canary Deployment
```bash
# Deploy canary version
kubectl apply -f k8s/canary.yaml

# Monitor canary deployment
kubectl get pods -l app=auth-service --watch

# Promote canary to production
kubectl annotate deployment/auth-service promote=true
```

## Monitoring and Observability

### Prometheus Configuration
```yaml
apiVersion: monitoring.coreos.com/v1
kind: Prometheus
metadata:
  name: gdb-prometheus
  labels:
    app: gdb-platform
spec:
  serviceAccountName: prometheus
  jobSelector:
    matchLabels:
      app: gdb-platform
  ruleSelector:
    matchLabels:
      role: alert-rules
  storage:
    volume:
      name: prometheus-data
      persistentVolumeClaim:
        claimName: prometheus-pvc
  retention: 30d
```

### Grafana Dashboard
```yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: gdb-grafana-dashboard
  labels:
    app: gdb-platform
spec:
  data:
    gdb-services.json: |
      {
        "dashboard": {
          "title": "GDB Services Dashboard",
          "panels": [
            {
              "title": "Service Health",
              "type": "stat",
              "targets": [
                {
                  "expr": "up{job=\"auth-service\"}",
                  "legendFormat": "Auth Service"
                },
                {
                  "expr": "up{job=\"users-service\"}",
                  "legendFormat": "Users Service"
                }
              ]
            }
          ]
        }
      }
```

## Conclusion

The Kubernetes deployment manifests provide a comprehensive solution for deploying the GDB microservices platform. The manifests include:

1. **Deployments**: All services with proper resource management
2. **Services**: Internal and external service communication
3. **ConfigMaps**: Configuration management
4. **Secrets**: Secure storage of sensitive data
5. **Persistent Volume Claims**: Data persistence
6. **Ingress**: External access to services
7. **Network Policies**: Security policies for service communication
8. **Monitoring**: Comprehensive monitoring and observability

The deployment strategy supports:

1. **Scalability**: Independent scaling of services
2. **Resilience**: Fault tolerance and self-healing
3. **Security**: Network policies and secret management
4. **Observability**: Comprehensive monitoring and logging
5. **Maintainability**: Easy deployment and rollback

The manifests are designed to be production-ready, with proper resource management, health checks, and monitoring capabilities to ensure reliable operation of the GDB microservices platform.