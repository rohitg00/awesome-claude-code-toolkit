Debug a failing or unhealthy Kubernetes pod by analyzing events, logs, and configuration.

## Steps

1. Get pod status: `kubectl get pod <name> -n <namespace> -o wide`.
2. Describe the pod for events and conditions: `kubectl describe pod <name> -n <namespace>`.
3. Analyze the pod state:
   - **Pending**: Check node resources, scheduling constraints, PVC binding.
   - **CrashLoopBackOff**: Check container logs for startup errors.
   - **ImagePullBackOff**: Verify image name, tag, and registry credentials.
   - **OOMKilled**: Check memory limits vs actual usage.
   - **Running but unhealthy**: Check probe configuration and endpoints.
4. Fetch container logs: `kubectl logs <pod> -n <ns> --previous` for crash logs.
5. Check resource usage: `kubectl top pod <name> -n <namespace>`.
6. Verify configuration:
   - ConfigMaps and Secrets are mounted correctly.
   - Environment variables are set.
   - Service account has required permissions.
7. Suggest fixes based on the diagnosis.

## Format

```
Pod: <name> in <namespace>
Status: <status>
Restarts: <count>
Node: <node-name>

Diagnosis:
  Root cause: <description>
  Evidence: <log lines or events>

Fix:
  1. <action to take>
  2. <verification command>
```

## Rules

- Always check events first; they often reveal the root cause immediately.
- Fetch logs from the previous container instance for crash analysis.
- Check node-level issues if multiple pods on the same node are affected.
- Verify DNS resolution if the pod cannot reach other services.
- Check RBAC permissions if the pod gets authorization errors.
