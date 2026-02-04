# /create-chart - Create Helm Chart

Generate a Helm chart for deploying an application to Kubernetes.

## Steps

1. Ask the user for the application name, type (web app, API, worker, cronjob), and container image
2. Create the chart directory structure with `helm create`
3. Configure Chart.yaml with name, version, appVersion, and description
4. Customize the Deployment template: replicas, resources, probes, env vars
5. Configure the Service template: type (ClusterIP, LoadBalancer, NodePort), ports
6. Add Ingress template with host, path, TLS configuration
7. Create ConfigMap and Secret templates for application configuration
8. Add HorizontalPodAutoscaler template with CPU/memory scaling rules
9. Configure PodDisruptionBudget for high-availability deployments
10. Set up ServiceAccount with appropriate RBAC permissions
11. Define values.yaml with sensible defaults for all configurable parameters
12. Validate the chart with `helm lint` and `helm template`

## Rules

- Always include resource limits and requests in deployment templates
- Configure liveness and readiness probes for all containers
- Use values.yaml for all configurable parameters; do not hardcode in templates
- Include pod anti-affinity rules for high-availability deployments
- Set security context: non-root user, read-only filesystem, drop capabilities
- Use chart hooks for database migrations or pre-deployment checks
- Pin container image tags; never use 'latest' in production values
