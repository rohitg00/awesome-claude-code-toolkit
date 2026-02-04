---
name: devops-automation
description: CI/CD pipeline design with GitHub Actions, Docker, Kubernetes, Helm, and GitOps patterns
---

# DevOps Automation

## GitHub Actions Workflow Structure

```yaml
name: CI/CD
on:
  push:
    branches: [main]
  pull_request:
    branches: [main]

concurrency:
  group: ${{ github.workflow }}-${{ github.ref }}
  cancel-in-progress: true

jobs:
  lint:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-node@v4
        with:
          node-version: 22
          cache: 'npm'
      - run: npm ci
      - run: npm run lint

  test:
    runs-on: ubuntu-latest
    needs: lint
    strategy:
      matrix:
        node-version: [20, 22]
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-node@v4
        with:
          node-version: ${{ matrix.node-version }}
          cache: 'npm'
      - run: npm ci
      - run: npm test -- --coverage
      - uses: actions/upload-artifact@v4
        with:
          name: coverage-${{ matrix.node-version }}
          path: coverage/

  deploy:
    runs-on: ubuntu-latest
    needs: test
    if: github.ref == 'refs/heads/main'
    environment: production
    steps:
      - uses: actions/checkout@v4
      - run: ./deploy.sh
```

Key patterns:
- Use `concurrency` to cancel outdated runs
- Cache dependencies with setup action's `cache` option
- Use `needs` for job dependencies
- Gate deploys with `environment` protection rules
- Use matrix for cross-version testing

## Docker Multi-Stage Builds

```dockerfile
FROM node:22-alpine AS deps
WORKDIR /app
COPY package.json package-lock.json ./
RUN npm ci --production

FROM node:22-alpine AS builder
WORKDIR /app
COPY package.json package-lock.json ./
RUN npm ci
COPY . .
RUN npm run build

FROM node:22-alpine AS runner
WORKDIR /app
RUN addgroup -g 1001 appgroup && adduser -u 1001 -G appgroup -S appuser
COPY --from=deps /app/node_modules ./node_modules
COPY --from=builder /app/dist ./dist
COPY --from=builder /app/package.json ./
USER appuser
EXPOSE 3000
HEALTHCHECK --interval=30s --timeout=3s CMD wget -qO- http://localhost:3000/health || exit 1
CMD ["node", "dist/server.js"]
```

Rules:
- Use specific image tags, never `latest`
- Run as non-root user
- Copy only necessary files into final stage
- Add `HEALTHCHECK` for orchestrator integration
- Use `.dockerignore` to exclude `node_modules`, `.git`, tests

## Kubernetes Deployment Manifest

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: api-server
  labels:
    app: api-server
spec:
  replicas: 3
  selector:
    matchLabels:
      app: api-server
  strategy:
    type: RollingUpdate
    rollingUpdate:
      maxSurge: 1
      maxUnavailable: 0
  template:
    metadata:
      labels:
        app: api-server
    spec:
      containers:
        - name: api
          image: registry.example.com/api:v1.2.3
          ports:
            - containerPort: 3000
          resources:
            requests:
              cpu: 100m
              memory: 128Mi
            limits:
              cpu: 500m
              memory: 512Mi
          readinessProbe:
            httpGet:
              path: /health
              port: 3000
            initialDelaySeconds: 5
            periodSeconds: 10
          livenessProbe:
            httpGet:
              path: /health
              port: 3000
            initialDelaySeconds: 15
            periodSeconds: 20
          env:
            - name: DATABASE_URL
              valueFrom:
                secretKeyRef:
                  name: api-secrets
                  key: database-url
```

Always set resource requests and limits. Always define readiness and liveness probes. Use `maxUnavailable: 0` for zero-downtime deploys.

## Helm Chart Structure

```
chart/
  Chart.yaml
  values.yaml
  values-staging.yaml
  values-production.yaml
  templates/
    deployment.yaml
    service.yaml
    ingress.yaml
    hpa.yaml
    _helpers.tpl
```

```yaml
# values.yaml
replicaCount: 2
image:
  repository: registry.example.com/api
  tag: latest
  pullPolicy: IfNotPresent
resources:
  requests:
    cpu: 100m
    memory: 128Mi
  limits:
    cpu: 500m
    memory: 512Mi
ingress:
  enabled: true
  host: api.example.com
autoscaling:
  enabled: true
  minReplicas: 2
  maxReplicas: 10
  targetCPUUtilization: 70
```

Use `values-{env}.yaml` overrides per environment. Lint charts with `helm lint`. Test with `helm template` before deploying.

## ArgoCD GitOps Pattern

```yaml
apiVersion: argoproj.io/v1alpha1
kind: Application
metadata:
  name: api-server
  namespace: argocd
spec:
  project: default
  source:
    repoURL: https://github.com/org/k8s-manifests
    targetRevision: main
    path: apps/api-server
  destination:
    server: https://kubernetes.default.svc
    namespace: production
  syncPolicy:
    automated:
      prune: true
      selfHeal: true
    syncOptions:
      - CreateNamespace=true
```

GitOps principles:
- Git is the single source of truth for cluster state
- All changes go through PRs (no `kubectl apply` in production)
- ArgoCD auto-syncs from Git to cluster
- Enable `selfHeal` to revert manual cluster changes
- Separate app code repos from deployment manifest repos

## Monitoring Stack

```yaml
# Prometheus ServiceMonitor
apiVersion: monitoring.coreos.com/v1
kind: ServiceMonitor
metadata:
  name: api-server
spec:
  selector:
    matchLabels:
      app: api-server
  endpoints:
    - port: metrics
      interval: 15s
      path: /metrics
```

Key metrics to expose:
- `http_request_duration_seconds` (histogram) - request latency by route and status
- `http_requests_total` (counter) - request count by route and status
- `process_resident_memory_bytes` (gauge) - memory usage
- `db_query_duration_seconds` (histogram) - database query latency

Alert on: error rate >1%, P99 latency >2s, memory >80% of limit, pod restarts >3 in 10 minutes.

## Pipeline Best Practices

1. Keep CI under 10 minutes (parallelize jobs, cache aggressively)
2. Run linting and type checking before tests
3. Use ephemeral environments for PR previews
4. Pin all action versions to SHA, not tags
5. Store secrets in GitHub Secrets, never in workflow files
6. Use OIDC for cloud provider authentication (no long-lived keys)
7. Tag images with git SHA, not `latest`
8. Run security scans (Trivy, Snyk) on container images in CI
