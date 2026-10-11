# GDB Microservices Platform - Monitoring and Logging Setup

## Overview

This document outlines the comprehensive monitoring and logging setup for the Global Digital Bank (GDB) microservices platform. The setup includes monitoring of application metrics, infrastructure metrics, logs, and traces to ensure reliable operation of all services.

## Monitoring Strategy

### 1. Monitoring Components

#### Application Monitoring
- **Metrics**: Application performance metrics, business metrics
- **Health Checks**: Service health and availability
- **Performance Monitoring**: Response times, throughput, error rates
- **Business Metrics**: Transaction volumes, user activity, revenue metrics

#### Infrastructure Monitoring
- **System Metrics**: CPU, memory, disk usage, network I/O
- **Container Metrics**: Container performance, resource usage
- **Service Discovery**: Service registration and discovery
- **Load Balancer Metrics**: Traffic distribution, health checks

#### Database Monitoring
- **Database Metrics**: Query performance, connection pools, lock contention
- **Backup Monitoring**: Backup success, recovery time objectives
- **Replication Monitoring**: Replication lag, consistency checks

#### Security Monitoring
- **Authentication**: Login attempts, session management
- **Authorization**: Access control, permission changes
- **Threat Detection**: Anomaly detection, intrusion detection

### 2. Logging Strategy

#### Application Logs
- **Structured Logging**: JSON-formatted logs with consistent schema
- **Correlation IDs**: Request tracing across services
- **Performance Logging**: Timing information, performance metrics
- **Error Logging**: Detailed error information, stack traces

#### Infrastructure Logs
- **System Logs**: Operating system events, service events
- **Container Logs**: Container creation, destruction, events
- **Network Logs**: Network traffic, connection events
- **Security Logs**: Authentication, authorization events

#### Database Logs
- **Query Logs**: SQL queries, execution times
- **Transaction Logs**: Transaction events, commit/rollback events
- **Backup Logs**: Backup events, recovery events

### 3. Monitoring Tools

#### Metrics Collection
- **Prometheus**: Metrics collection, storage, querying
- **Node Exporter**: System metrics collection
- **Blackbox Exporter**: External service monitoring
- **Kube State Metrics**: Kubernetes resource states

#### Log Collection
- **Fluent Bit**: Log collection, filtering, forwarding
- **Filebeat**: Log file monitoring, shipping
- **Vector**: Log collection, transformation, routing
- **Logstash**: Log processing, enrichment, storage

#### Visualization
- **Grafana**: Dashboard creation, visualization
- **Kibana**: Log analysis, visualization
- **Grafana Agent**: Metrics collection, visualization
- **Tempo**: Distributed tracing, visualization

#### Alerting
- **Alertmanager**: Alert routing, deduplication, silencing
- **PagerDuty**: Critical alert notifications
- **Slack**: Team notifications
- **Email**: Email notifications

## Monitoring Implementation

### 1. Metrics Monitoring

#### Prometheus Configuration
```yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: prometheus-config
  labels:
    app: gdb-platform
spec:
  data:
    prometheus.yml: |
      global:
        scrape_interval: 15s
        evaluation_interval: 15s
        external_labels:
          monitor: 'gdb-monitor'

      scrape_configs:
      - job_name: 'prometheus'
        static_configs:
        - targets: ['localhost:9090']

      - job_name: 'node-exporter'
        static_configs:
        - targets: ['node-exporter:9100']

      - job_name: 'auth-service'
        static_configs:
        - targets: ['auth-service:8004']
        metrics_path: '/metrics'
        scrape_interval: 30s

      - job_name: 'users-service'
        static_configs:
        - targets: ['users-service:8003']
        metrics_path: '/metrics'
        scrape_interval: 30s

      - job_name: 'accounts-service'
        static_configs:
        - targets: ['accounts-service:8001']
        metrics_path: '/metrics'
        scrape_interval: 30s

      - job_name: 'transactions-service'
        static_configs:
        - targets: ['transactions-service:8002']
        metrics_path: '/metrics'
        scrape_interval: 30s

      - job_name: 'api-gateway'
        static_configs:
        - targets: ['api-gateway:8000']
        metrics_path: '/metrics'
        scrape_interval: 30s

      - job_name: 'redis'
        static_configs:
        - targets: ['redis:6379']
        metrics_path: '/metrics'
        scrape_interval: 30s
```

#### Service Metrics
```yaml
# Service metrics configuration
apiVersion: v1
kind: ConfigMap
metadata:
  name: service-metrics
  labels:
    app: gdb-platform
spec:
  data:
    metrics.yaml: |
      # Application metrics
      - name: http_requests_total
        help: Total number of HTTP requests
        type: counter
        labels: [method, route, status]

      - name: http_request_duration_seconds
        help: HTTP request duration in seconds
        type: histogram
        labels: [method, route]
        buckets: [0.005, 0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1, 2.5, 5, 10]

      - name: database_connections
        help: Number of database connections
        type: gauge
        labels: [database]

      - name: active_requests
        help: Number of active requests
        type: gauge

      - name: error_count
        help: Number of errors
        type: counter
        labels: [error_type]
```

### 2. Log Collection

#### Fluent Bit Configuration
```yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: fluent-bit-config
  labels:
    app: gdb-platform
spec:
  data:
    fluent-bit.conf: |
      [SERVICE]
        Flush        5
        Log_Level    info
        Daemon       off
        Parsers_File parsers.conf
        HTTP_Server  On
        HTTP_Listen  0.0.0.0
        HTTP_Port    2020

      [INPUT]
        Name        tail
        Path        /var/log/containers/*.log
        Mem_Buf_Len 5MB
        Skip_Long_Lines On
        DB          /var/log/flb_kube.db
        DB.Sync      Normal
        Tag         kube.*

      [FILTER]
        Name        kubernetes
        Match       kube.*
        Kube_URL    http://10.96.0.1:8080
        Kube_Token_File    /var/run/secrets/kubernetes.io/serviceaccount/token
        Kube_CA_File      /var/run/secrets/kubernetes.io/serviceaccount/ca.crt
        Kube_Labels       app
        Kube_Tag           $namespace.$pod_name
        Merge_Log        On
        Keep_Log         On
        Kubernetes_Var_Log_Path    /var/log/containers

      [OUTPUT]
        Name        es
        Match       kube.*
        Host        elasticsearch
        Port        9200
        Logstash_Format On
        Logstash_Prefix kube-
        Retry_Limit    False

      [OUTPUT]
        Name        stdout
        Match       *
        Format      json
        Output_No_Newline On
```

#### Logback Configuration
```xml
<!-- logback.xml -->
<configuration>
    <appender name="console" class="ch.qos.logback.core.console.ConsoleAppender">
        <encoder>
            <pattern>%d{yyyy-MM-dd HH:mm:ss.SSS} [%thread] %-5level %logger{36} - %msg%n</pattern>
            <outputPatternAsHeader>false</outputPatternAsHeader>
        </encoder>
    </appender>

    <appender name="file" class="ch.qos.logback.core.rolling.RollingFileAppender">
        <file>/var/log/application.log</file>
        <rollingPolicy class="ch.qos.logback.core.rolling.SizeBasedTriggeringPolicy">
            <maxFileSize>10MB</maxFileSize>
        </rollingPolicy>
        <encoder>
            <pattern>%d{yyyy-MM-dd HH:mm:ss.SSS} [%thread] %-5level %logger{36} - %msg%n</pattern>
        </encoder>
    </appender>

    <logger name="com.gdb" level="INFO" additivity="false">
        <appender-ref ref="file"/>
        <appender-ref ref="console"/>
    </logger>

    <root level="INFO">
        <appender-ref ref="console"/>
    </root>
</configuration>
```

### 3. Visualization

#### Grafana Dashboard
```yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: grafana-dashboards
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
                },
                {
                  "expr": "up{job=\"accounts-service\"}",
                  "legendFormat": "Accounts Service"
                },
                {
                  "expr": "up{job=\"transactions-service\"}",
                  "legendFormat": "Transactions Service"
                }
              ]
            },
            {
              "title": "API Gateway Requests",
              "type": "graph",
              "targets": [
                {
                  "expr": "rate(http_requests_total{job=\"api-gateway\"}[5m])",
                  "legendFormat": "Requests per second"
                }
              ]
            },
            {
              "title": "Database Connections",
              "type": "graph",
              "targets": [
                {
                  "expr": "database_connections",
                  "legendFormat": "{{ database }}"
                }
              ]
            },
            {
              "title": "Error Rate",
              "type": "graph",
              "targets": [
                {
                  "expr": "rate(error_count[5m])",
                  "legendFormat": "Errors per second"
                }
              ]
            }
          ]
        }
      }
```

#### Kibana Dashboard
```yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: kibana-config
  labels:
    app: gdb-platform
spec:
  data:
    kibana.yml: |
      server.name: kibana
      server.host: "0.0.0.0"
      elasticsearch.hosts: ["http://elasticsearch:9200"]
      xpack.monitoring.ui.container.elasticsearch.enabled: true
      xpack.reporting.enabled: false
```

### 4. Alerting

#### Alertmanager Configuration
```yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: alertmanager-config
  labels:
    app: gdb-platform
spec:
  data:
    alertmanager.yml: |
      global:
        resolve_timeout: 5m
        slack_api_url: 'https://hooks.slack.com/services/YOUR/SLACK/WEBHOOK'
        pagerduty_api_url: 'https://api.pagerduty.com'
        pagerduty_integration_key: 'YOUR-PAGERDUTY-INTEGRATION-KEY'

      route:
        receiver: 'default'
        routes:
        - match:
            severity: critical
          receiver: 'critical-notifications'
        - match:
            severity: warning
          receiver: 'warning-notifications'

      receivers:
      - name: 'default'
        slack_configs:
        - channel: '#general'
          text: 'Alert: {{ .CommonAnnotations.summary }}'

      - name: 'critical-notifications'
        slack_configs:
        - channel: '#critical'
          text: 'CRITICAL: {{ .CommonAnnotations.summary }}'
        pagerduty_configs:
        - integration_key: 'YOUR-PAGERDUTY-INTEGRATION-KEY'
          severity: critical
          description: '{{ .CommonAnnotations.description }}'

      - name: 'warning-notifications'
        slack_configs:
        - channel: '#warnings'
          text: 'WARNING: {{ .CommonAnnotations.summary }}'

      templates:
      - '/etc/alertmanager/template/*.tmpl'
```

#### Alert Rules
```yaml
apiVersion: monitoring.coreos.com/v1
kind: PrometheusRule
metadata:
  name: gdb-alerts
  labels:
    app: gdb-platform
spec:
  groups:
  - name: gdb-alerts
    rules:
    - alert: ServiceDown
      expr: up == 0
      for: 5m
      labels:
        severity: critical
      annotations:
        summary: "Service {{ $labels.job }} is down"
        description: "Service {{ $labels.job }} has been down for more than 5 minutes."

    - alert: HighErrorRate
      expr: rate(error_count[5m]) > 0.1
      for: 2m
      labels:
        severity: warning
      annotations:
        summary: "High error rate detected"
        description: "Error rate is {{ $value }} errors per second for {{ $labels.service }}"

    - alert: HighResponseTime
      expr: histogram_quantile(0.95, rate(http_request_duration_seconds_bucket[5m])) > 1.0
      for: 5m
      labels:
        severity: warning
      annotations:
        summary: "High response time detected"
        description: "95th percentile response time is {{ $value }} seconds for {{ $labels.route }}"

    - alert: DatabaseConnectionPoolExhausted
      expr: database_connections > 0.8 * database_connections_max
      for: 5m
      labels:
        severity: critical
      annotations:
        summary: "Database connection pool exhausted"
        description: "Database connection pool is {{ $value }}% full for {{ $labels.database }}"

    - alert: HighCPUUsage
      expr: (1 - avg by (instance) (irate(node_cpu_seconds_total{mode="idle"}[5m]))) * 100 > 80
      for: 10m
      labels:
        severity: warning
      annotations:
        summary: "High CPU usage detected"
        description: "CPU usage is {{ $value }}% for {{ $labels.instance }}"

    - alert: HighMemoryUsage
      expr: (node_memory_MemTotal - node_memory_MemAvailable) / node_memory_MemTotal * 100 > 80
      for: 10m
      labels:
        severity: warning
      annotations:
        summary: "High memory usage detected"
        description: "Memory usage is {{ $value }}% for {{ $labels.instance }}"

    - alert: DiskSpaceRunningLow
      expr: (node_filesystem_size_bytes - node_filesystem_free_bytes) / node_filesystem_size_bytes * 100 > 80
      for: 5m
      labels:
        severity: critical
      annotations:
        summary: "Disk space running low"
        description: "Disk space usage is {{ $value }}% for {{ $labels.mountpoint }}"

    - alert: ServiceRestart
      expr: changes(process_start_time_total{job=\"auth-service\"}[5m]) > 0
      for: 1m
      labels:
        severity: warning
      annotations:
        summary: "Service restart detected"
        description: "Service {{ $labels.job }} has been restarted"
```

## Monitoring Implementation

### 1. Metrics Monitoring

#### Prometheus Deployment
```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: prometheus
  labels:
    app: gdb-platform
spec:
  replicas: 1
  selector:
    matchLabels:
      app: prometheus
  template:
    metadata:
      labels:
        app: prometheus
    spec:
      containers:
      - name: prometheus
        image: prom/prometheus:latest
        ports:
        - containerPort: 9090
        volumeMounts:
        - name: prometheus-config
          mountPath: /etc/prometheus
        - name: prometheus-data
          mountPath: /prometheus
      volumes:
      - name: prometheus-config
        configMap:
          name: prometheus-config
      - name: prometheus-data
        persistentVolumeClaim:
          claimName: prometheus-pvc
```

#### Node Exporter Deployment
```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: node-exporter
  labels:
    app: gdb-platform
spec:
  replicas: 3
  selector:
    matchLabels:
      app: node-exporter
  template:
    metadata:
      labels:
        app: node-exporter
    spec:
      containers:
      - name: node-exporter
        image: prom/node-exporter:latest
        ports:
        - containerPort: 9100
        resources:
          requests:
            memory: "32Mi"
            cpu: "50m"
          limits:
            memory: "128Mi"
            cpu: "200m"
```

### 2. Log Collection

#### Fluent Bit Deployment
```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: fluent-bit
  labels:
    app: gdb-platform
spec:
  replicas: 3
  selector:
    matchLabels:
      app: fluent-bit
  template:
    metadata:
      labels:
        app: fluent-bit
    spec:
      containers:
      - name: fluent-bit
        image: fluent/fluent-bit:latest
        ports:
        - containerPort: 2020
        volumeMounts:
        - name: var-log
          mountPath: /var/log
        - name: fluent-bit-config
          mountPath: /etc/fluent-bit
      volumes:
      - name: var-log
        hostPath:
          path: /var/log
      - name: fluent-bit-config
        configMap:
          name: fluent-bit-config
```

#### Elasticsearch Deployment
```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: elasticsearch
  labels:
    app: gdb-platform
spec:
  replicas: 3
  selector:
    matchLabels:
      app: elasticsearch
  template:
    metadata:
      labels:
        app: elasticsearch
    spec:
      containers:
      - name: elasticsearch
        image: docker.elastic.co/elasticsearch/elasticsearch:7.17.0
        ports:
        - containerPort: 9200
        env:
        - name: discovery.type
          value: "single-node"
        - name: xpack.security.enabled
          value: "true"
        - name: ELASTIC_PASSWORD
          valueFrom:
            secretKeyRef:
              name: elastic-secret
              key: password
        resources:
          requests:
            memory: "512Mi"
            cpu: "500m"
          limits:
            memory: "1Gi"
            cpu: "1000m"
        volumeMounts:
        - name: elasticsearch-data
          mountPath: /usr/share/elasticsearch/data
      volumes:
      - name: elasticsearch-data
        persistentVolumeClaim:
          claimName: elasticsearch-pvc
```

### 3. Visualization

#### Grafana Deployment
```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: grafana
  labels:
    app: gdb-platform
spec:
  replicas: 2
  selector:
    matchLabels:
      app: grafana
  template:
    metadata:
      labels:
        app: grafana
    spec:
      containers:
      - name: grafana
        image: grafana/grafana:latest
        ports:
        - containerPort: 3000
        env:
        - name: GF_SECURITY_ADMIN_PASSWORD
          valueFrom:
            secretKeyRef:
              name: grafana-secret
              key: admin-password
        - name: GF_DATABASE_URL
          value: "postgresql://postgres:postgres@postgres:5432/grafana"
        resources:
          requests:
            memory: "256Mi"
            cpu: "250m"
          limits:
            memory: "512Mi"
            cpu: "500m"
        volumeMounts:
        - name: grafana-data
          mountPath: /var/lib/grafana
      volumes:
      - name: grafana-data
        persistentVolumeClaim:
          claimName: grafana-pvc
```

#### Alertmanager Deployment
```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: alertmanager
  labels:
    app: gdb-platform
spec:
  replicas: 2
  selector:
    matchLabels:
      app: alertmanager
  template:
    metadata:
      labels:
        app: alertmanager
    spec:
      containers:
      - name: alertmanager
        image: prom/alertmanager:latest
        ports:
        - containerPort: 9093
        args:
        - "--config.file=/etc/alertmanager/config.yml"
        - "--storage.path=/alertmanager"
        volumeMounts:
        - name: alertmanager-config
          mountPath: /etc/alertmanager
        - name: alertmanager-data
          mountPath: /alertmanager
      volumes:
      - name: alertmanager-config
        configMap:
          name: alertmanager-config
      - name: alertmanager-data
        persistentVolumeClaim:
          claimName: alertmanager-pvc
```

### 4. Tracing

#### Jaeger Deployment
```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: jaeger
  labels:
    app: gdb-platform
spec:
  replicas: 1
  selector:
    matchLabels:
      app: jaeger
  template:
    metadata:
      labels:
        app: jaeger
    spec:
      containers:
      - name: jaeger
        image: jaegertracing/all-in-one:latest
        ports:
        - containerPort: 5775
        - containerPort: 6831
        - containerPort: 6832
        - containerPort: 5778
        - containerPort: 16686
        - containerPort: 14268
        - containerPort: 14250
        resources:
          requests:
            memory: "512Mi"
            cpu: "500m"
          limits:
            memory: "1Gi"
            cpu: "1000m"
```

## Monitoring Setup

### 1. Metrics Monitoring Setup
```bash
# Setup metrics monitoring
kubectl apply -f monitoring/prometheus.yaml
kubectl apply -f monitoring/node-exporter.yaml
kubectl apply -f monitoring/service-metrics.yaml

# Verify metrics collection
kubectl get pods -l app=prometheus
kubectl get pods -l app=node-exporter
```

### 2. Log Collection Setup
```bash
# Setup log collection
kubectl apply -f monitoring/fluent-bit.yaml
kubectl apply -f monitoring/elasticsearch.yaml
kubectl apply -f monitoring/kibana.yaml

# Verify log collection
kubectl get pods -l app=fluent-bit
kubectl get pods -l app=elasticsearch
kubectl get pods -l app=kibana
```

### 3. Visualization Setup
```bash
# Setup visualization
kubectl apply -f monitoring/grafana.yaml
kubectl apply -f monitoring/alertmanager.yaml
kubectl apply -f monitoring/jaeger.yaml

# Verify visualization
kubectl get pods -l app=grafana
kubectl get pods -l app=alertmanager
kubectl get pods -l app=jaeger
```

### 4. Alerting Setup
```bash
# Setup alerting
kubectl apply -f monitoring/alert-rules.yaml
kubectl apply -f monitoring/alertmanager-config.yaml

# Verify alerting
kubectl get prometheusrule
kubectl get configmap alertmanager-config
```

## Monitoring Configuration

### 1. Metrics Configuration
```yaml
# metrics-config.yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: metrics-config
  labels:
    app: gdb-platform
spec:
  data:
    metrics.yaml: |
      # Metrics configuration
      scrape_interval: 15s
      evaluation_interval: 15s

      rule_files:
      - /etc/prometheus/rules/*.yaml

      remote_write:
      - url: http://thanos-query:9090/api/v1/write

      external_labels:
        monitor: 'gdb-monitor'
        environment: 'production'
```

### 2. Log Configuration
```yaml
# log-config.yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: log-config
  labels:
    app: gdb-platform
spec:
  data:
    logback.xml: |
      <configuration>
          <appender name="console" class="ch.qos.logback.core.console.ConsoleAppender">
              <encoder>
                  <pattern>%d{yyyy-MM-dd HH:mm:ss.SSS} [%thread] %-5level %logger{36} - %msg%n</pattern>
              </encoder>
          </appender>

          <appender name="file" class="ch.qos.logback.core.rolling.RollingFileAppender">
              <file>/var/log/application.log</file>
              <rollingPolicy class="ch.qos.logback.core.rolling.SizeBasedTriggeringPolicy">
                  <maxFileSize>10MB</maxFileSize>
              </rollingPolicy>
              <encoder>
                  <pattern>%d{yyyy-MM-dd HH:mm:ss.SSS} [%thread] %-5level %logger{36} - %msg%n</pattern>
              </encoder>
          </appender>

          <logger name="com.gdb" level="INFO" additivity="false">
              <appender-ref ref="file"/>
              <appender-ref ref="console"/>
          </logger>

          <root level="INFO">
              <appender-ref ref="console"/>
          </root>
      </configuration>
```

### 3. Visualization Configuration
```yaml
# grafana-config.yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: grafana-config
  labels:
    app: gdb-platform
spec:
  data:
    grafana.ini: |
      [server]
      domain = grafana.gdb.local
      enforce_domain = true
      root_url = %(protocol)s://%(domain)s/%(app_subpath)s

      [database]
      type = postgres
      host = postgres:5432
      name = grafana
      user = postgres
      password = ${GRAFANA_DB_PASSWORD}

      [security]
      admin_user = admin
      admin_password = ${GRAFANA_ADMIN_PASSWORD}
      secret_key = ${GRAFANA_SECRET_KEY}

      [log]
      mode = console
      level = info
```

## Monitoring Maintenance

### 1. Metrics Maintenance
```bash
# Metrics maintenance
# Backup metrics
kubectl exec -it prometheus-0 -- /bin/sh -c "pg_dumpall > /tmp/prometheus_backup.sql"

# Restore metrics
kubectl exec -it prometheus-0 -- /bin/sh -c "pg_restore -d prometheus < /tmp/prometheus_backup.sql"

# Clean up old metrics
kubectl exec -it prometheus-0 -- /bin/sh -c "prometheus --web.enable-admin-api --web.enable-lifecycle --web.cleanup-teardown-duration=24h"
```

### 2. Log Maintenance
```bash
# Log maintenance
# Rotate logs
kubectl exec -it fluent-bit-0 -- /bin/sh -c "logrotate /etc/logrotate.conf"

# Clean up old logs
kubectl exec -it elasticsearch-0 -- /bin/sh -c "curl -X DELETE \"http://localhost:9200/_all/_settings?pretty\" -H 'Content-Type: application/json' -d '{\"index\" : {\"max_size\" : \"1gb\",\"max_age\" : \"30d\"}}'
```

### 3. Visualization Maintenance
```bash
# Visualization maintenance
# Backup dashboards
kubectl exec -it grafana-0 -- /bin/sh -c "grafana-cli --homepath=/usr/share/grafana dashboards export \"GDB Services Dashboard\" /tmp/dashboard_backup.json"

# Restore dashboards
kubectl exec -it grafana-0 -- /bin/sh -c "grafana-cli --homepath=/usr/share/grafana dashboards load /tmp/dashboard_backup.json"

# Clean up old dashboards
kubectl exec -it grafana-0 -- /bin/sh -c "grafana-cli --homepath=/usr/share/grafana dashboards list | grep -v \"GDB Services Dashboard\" | xargs -I {} grafana-cli --homepath=/usr/share/grafana dashboards delete {}"
```

### 4. Alerting Maintenance
```bash
# Alerting maintenance
# Backup alerts
kubectl exec -it alertmanager-0 -- /bin/sh -c "alertmanager --config.file=/etc/alertmanager/config.yml --web.enable-admin-api --web.cleanup-teardown-duration=24h"

# Restore alerts
kubectl exec -it alertmanager-0 -- /bin/sh -c "alertmanager --config.file=/etc/alertmanager/config.yml --web.enable-admin-api --web.cleanup-teardown-duration=24h"

# Clean up old alerts
kubectl exec -it alertmanager-0 -- /bin/sh -c "alertmanager --config.file=/etc/alertmanager/config.yml --web.enable-admin-api --web.cleanup-teardown-duration=24h"
```

## Monitoring Security

### 1. Metrics Security
```yaml
# Metrics security
apiVersion: v1
kind: NetworkPolicy
metadata:
  name: metrics-network-policy
  labels:
    app: gdb-platform
spec:
  podSelector:
    matchLabels:
      app: prometheus
  policyTypes:
  - Ingress
  - Egress
  ingress:
  - from:
    - podSelector:
        matchLabels:
          app: grafana
    ports:
    - protocol: TCP
      port: 9090
  egress:
  - to: []
    ports:
    - protocol: TCP
      port: 53
    - protocol: TCP
      port: 80
    - protocol: TCP
      port: 443
```

### 2. Log Security
```yaml
# Log security
apiVersion: v1
kind: NetworkPolicy
metadata:
  name: log-network-policy
  labels:
    app: gdb-platform
spec:
  podSelector:
    matchLabels:
      app: elasticsearch
  policyTypes:
  - Ingress
  - Egress
  ingress:
  - from:
    - podSelector:
        matchLabels:
          app: fluent-bit
    ports:
    - protocol: TCP
      port: 9200
  egress:
  - to: []
    ports:
    - protocol: TCP
      port: 53
    - protocol: TCP
      port: 80
    - protocol: TCP
      port: 443
```

### 3. Visualization Security
```yaml
# Visualization security
apiVersion: v1
kind: NetworkPolicy
metadata:
  name: grafana-network-policy
  labels:
    app: gdb-platform
spec:
  podSelector:
    matchLabels:
      app: grafana
  policyTypes:
  - Ingress
  - Egress
  ingress:
  - from:
    - ipBlock:
        cidr: 10.0.0.0/8
    ports:
    - protocol: TCP
      port: 3000
  egress:
  - to: []
    ports:
    - protocol: TCP
      port: 53
    - protocol: TCP
      port: 80
    - protocol: TCP
      port: 443
```

## Conclusion

The monitoring and logging setup for the GDB microservices platform provides comprehensive monitoring of application metrics, infrastructure metrics, logs, and traces. The setup includes:

1. **Metrics Monitoring**: Prometheus for metrics collection, storage, and querying
2. **Log Collection**: Fluent Bit for log collection, filtering, and forwarding
3. **Visualization**: Grafana for dashboard creation and visualization
4. **Alerting**: Alertmanager for alert routing, deduplication, and silencing
5. **Tracing**: Jaeger for distributed tracing

The monitoring setup is designed to provide:

1. **Real-time Monitoring**: Real-time monitoring of application and infrastructure metrics
2. **Comprehensive Logging**: Comprehensive logging of application and infrastructure events
3. **Advanced Visualization**: Advanced visualization of metrics and logs
4. **Effective Alerting**: Effective alerting for critical events
5. **Security**: Security measures for monitoring and logging systems

The implementation leverages Kubernetes deployments, ConfigMaps, and Secrets to provide a flexible and scalable monitoring solution. The setup ensures that all services are monitored, logged, and alerted in a consistent and reliable manner.