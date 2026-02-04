Set up monitoring, alerting, and observability for the application.

## Steps

1. Analyze the application to determine monitoring needs:
   - Web server: response times, error rates, request volume.
   - Database: query performance, connection pool, replication lag.
   - Queue: message throughput, consumer lag, dead letters.
   - Background jobs: execution time, failure rate, queue depth.
2. Generate monitoring configuration for the detected stack:
   - **Prometheus**: Scrape config, recording rules, alert rules.
   - **Grafana**: Dashboard JSON with key panels.
   - **Datadog**: `datadog.yaml` or agent configuration.
   - **Health endpoint**: `/health` or `/healthz` implementation.
3. Define alerts for critical metrics:
   - Error rate > 1% over 5 minutes.
   - P99 latency > 2 seconds.
   - Disk usage > 80%.
   - Memory usage > 90%.
   - Certificate expiry < 14 days.
4. Add structured logging configuration:
   - JSON log format with timestamp, level, message, trace ID.
   - Log levels: ERROR for failures, WARN for degradation, INFO for operations.
5. Set up distributed tracing if applicable:
   - OpenTelemetry SDK initialization.
   - Trace context propagation headers.
6. Write all configuration files to `monitoring/` or `deploy/monitoring/`.

## Format

```yaml
groups:
  - name: <app-name>-alerts
    rules:
      - alert: HighErrorRate
        expr: rate(http_requests_total{status=~"5.."}[5m]) > 0.01
        for: 5m
        labels:
          severity: critical
        annotations:
          summary: "High error rate detected"
```

## Rules

- Every production service must have health checks, error rate alerts, and latency monitoring.
- Use percentile-based latency metrics (P50, P95, P99), not averages.
- Set alert thresholds based on SLO targets, not arbitrary values.
- Include runbook links in alert annotations.
- Log at appropriate levels; never log sensitive data (passwords, tokens, PII).
