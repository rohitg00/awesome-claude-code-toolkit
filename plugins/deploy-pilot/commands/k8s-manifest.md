# /deploy-pilot:k8s-manifest

Generate production-ready Kubernetes manifests for the current application.

## Process

1. Gather application details:
   - Read the Dockerfile or build config to determine the container image and port
   - Check for existing k8s manifests in `k8s/`, `deploy/`, `manifests/`, or `kubernetes/` directories
   - Identify environment variables from `.env.example` or the application config
   - Determine resource requirements based on the application type

2. Generate a Deployment manifest:
   - Set `replicas: 2` as the default for high availability
   - Configure rolling update strategy with `maxSurge: 1` and `maxUnavailable: 0`
   - Set resource requests and limits:
     - Web apps: 128Mi memory request, 256Mi limit, 100m CPU request, 500m limit
     - APIs: 256Mi memory request, 512Mi limit, 200m CPU request, 1000m limit
     - Workers: 512Mi memory request, 1Gi limit, 250m CPU request, 1000m limit
   - Add liveness and readiness probes:
     - HTTP probe for web services (GET /healthz)
     - TCP probe for non-HTTP services
     - Set initialDelaySeconds, periodSeconds, and failureThreshold appropriately
   - Mount environment variables from ConfigMap and secrets from Secret
   - Set security context: runAsNonRoot, readOnlyRootFilesystem, drop all capabilities
   - Add pod disruption budget for graceful scaling

3. Generate a Service manifest:
   - ClusterIP service for internal communication
   - Match the deployment selector labels
   - Map the container port to the service port

4. Generate an Ingress manifest (if the app is externally accessible):
   - Use the `networking.k8s.io/v1` API version
   - Configure TLS with a placeholder for cert-manager cluster issuer annotation
   - Set appropriate path type (Prefix for SPAs, Exact for APIs)
   - Include a placeholder hostname that the user should customize

5. Generate supporting resources:
   - ConfigMap for non-sensitive environment variables
   - Secret manifest (with placeholder values) for sensitive configuration
   - HorizontalPodAutoscaler targeting 70% CPU utilization, scaling 2-10 replicas
   - NetworkPolicy restricting ingress to only the necessary ports

6. Add namespace and label conventions:
   - Use `app.kubernetes.io/name`, `app.kubernetes.io/version`, `app.kubernetes.io/component` labels
   - Include a namespace definition or note that one should be created

## Output

Write manifests to a `k8s/` directory with separate files:
- `k8s/deployment.yaml`
- `k8s/service.yaml`
- `k8s/ingress.yaml`
- `k8s/configmap.yaml`
- `k8s/hpa.yaml`
- `k8s/networkpolicy.yaml`

Alternatively, offer a single `k8s/app.yaml` with all resources separated by `---`.

## Rules

- Always use specific image tags, never `latest`
- Set resource limits on every container to prevent noisy neighbor issues
- Include comments explaining each non-obvious configuration choice
- Validate manifests with `kubectl apply --dry-run=client -f` if kubectl is available
- Use `kustomize`-friendly structure if the project already uses kustomize
- Never include actual secret values; use placeholders with instructions to populate from a secret manager
