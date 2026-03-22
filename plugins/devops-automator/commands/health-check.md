Create health check scripts to verify service and infrastructure availability.

## Steps


1. Identify what needs to be checked:
2. Design the health check suite:
3. Implement each check:
4. Set up response format:
5. Configure alerting thresholds:
6. Schedule periodic execution (cron, Kubernetes probe, monitoring tool).
7. Document the health check endpoints and their meanings.

## Format


```
Health Check: <service name>
Status: <healthy|degraded|unhealthy>
Checks:
  - <check name>: <pass|fail> (<latency>ms)
```


## Rules

- Health checks must complete within 5 seconds.
- Do not perform destructive operations in health checks.
- Cache results for short periods to avoid overloading dependencies.

