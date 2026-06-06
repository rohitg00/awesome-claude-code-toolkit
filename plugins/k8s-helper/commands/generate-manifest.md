Generate production-ready Kubernetes manifests from application configuration.

## Steps

1. Analyze the application:
   - Read Dockerfile for container port, health check, and entrypoint.
   - Read environment variable requirements from `.env.example`.
   - Detect service dependencies from docker-compose or config files.
2. Generate manifests:
   - Namespace definition.
   - Deployment with resource limits, probes, and rolling update strategy.
   - Service (ClusterIP for internal, LoadBalancer for external).
   - ConfigMap for non-sensitive configuration.
   - Secret template for sensitive values.
   - Ingress with TLS if external access is needed.
   - HPA for auto-scaling based on CPU/memory.
3. Add Kustomize base and overlays for dev/staging/production.
4. Validate manifests: `kubectl apply --dry-run=client -f .`.
5. Write files to `k8s/` or `deploy/` directory.

## Format

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: <app>
  labels:
    app.kubernetes.io/name: <app>
    app.kubernetes.io/version: <version>
```

## Rules

- Always set CPU and memory requests and limits.
- Include readiness and liveness probes for every container.
- Use `app.kubernetes.io/` label conventions.
- Never hardcode secrets; use Secret resources or external-secrets operator.
- Set `securityContext` with non-root user and read-only filesystem where possible.
