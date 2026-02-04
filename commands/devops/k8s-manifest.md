Generate Kubernetes manifests for deploying the current application.

## Steps

1. Analyze the project to determine deployment requirements:
   - Read `Dockerfile` for container configuration, exposed ports, health checks.
   - Read `docker-compose.yml` for service dependencies.
   - Read `.env.example` for required environment variables.
2. Generate core manifests:
   - **Deployment**: Container spec, resource limits, readiness/liveness probes, replicas.
   - **Service**: ClusterIP, NodePort, or LoadBalancer based on access pattern.
   - **ConfigMap**: Non-sensitive configuration values.
   - **Secret**: Sensitive values (templated, not with real values).
   - **Ingress**: If the service needs external access, with TLS config.
3. Add operational manifests as needed:
   - **HorizontalPodAutoscaler**: CPU/memory-based scaling rules.
   - **PodDisruptionBudget**: Minimum availability during updates.
   - **NetworkPolicy**: Restrict traffic to necessary paths.
   - **ServiceAccount**: With minimal RBAC permissions.
4. Set resource requests and limits based on the application type.
5. Write manifests to `k8s/` or `deploy/k8s/` directory.
6. Validate with `kubectl --dry-run=client -f <file>` if kubectl is available.

## Format

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: <app-name>
  namespace: <namespace>
  labels:
    app: <app-name>
spec:
  replicas: <count>
  selector:
    matchLabels:
      app: <app-name>
  template:
    spec:
      containers:
        - name: <app-name>
          image: <registry>/<image>:<tag>
          ports:
            - containerPort: <port>
          resources:
            requests:
              cpu: "100m"
              memory: "128Mi"
            limits:
              cpu: "500m"
              memory: "512Mi"
```

## Rules

- Always set resource requests and limits on every container.
- Never hardcode secrets in manifests; use Secret references or external secret managers.
- Include readiness and liveness probes for every service container.
- Use `RollingUpdate` strategy with `maxSurge: 1` and `maxUnavailable: 0` by default.
- Add namespace to every resource manifest.
