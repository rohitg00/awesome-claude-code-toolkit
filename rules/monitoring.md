# Monitoring

## Logging Standards
- Use structured logging (JSON format) in all environments except local development.
- Include standard fields in every log entry: `timestamp`, `level`, `service`, `requestId`, `message`.
- Log levels: DEBUG (verbose development info), INFO (business events), WARN (recoverable issues), ERROR (failures requiring attention).
- Log at INFO level: request start/end, auth events, business transactions, job start/completion.
- Log at ERROR level: unhandled exceptions, failed external calls, data integrity issues.
- Never log: passwords, tokens, PII, credit card numbers, or full request bodies with sensitive data.
- Sanitize user input in log messages to prevent log injection attacks.
- Use a correlation ID (requestId) across all services for distributed tracing.

## Metrics
- Track the four golden signals: latency, traffic, errors, saturation.
- Use histograms for latency (not averages). Track p50, p95, p99 percentiles.
- Instrument: HTTP request duration, database query duration, queue depth, cache hit rate.
- Use counter metrics for: requests total, errors total, jobs processed, events emitted.
- Use gauge metrics for: active connections, queue size, memory usage, goroutine count.
- Name metrics with a namespace prefix: `myapp_http_requests_total`, `myapp_db_query_duration_seconds`.
- Export metrics in Prometheus format or push to Datadog/CloudWatch.

## Alerting Rules
- Alert on symptoms (error rate > 1%, latency p99 > 2s) not causes (CPU > 80%).
- Set severity levels: P1 (pages on-call, service down), P2 (Slack alert, degraded), P3 (ticket, non-urgent).
- P1 alerts must have a runbook linked in the alert description.
- Avoid alert fatigue: if an alert fires more than 3 times without action, tune or remove it.
- Use alerting windows: 5-minute sustained for P1, 15-minute sustained for P2.
- Test alerts quarterly by injecting controlled failures.

## Health Checks
- Expose `/health` for load balancer checks (returns 200 if the process is running).
- Expose `/ready` for dependency checks (database, cache, queue connectivity).
- Health check endpoints must respond within 1 second and not perform expensive operations.
- Return structured health: `{ status: "healthy", checks: { db: "ok", redis: "ok", queue: "ok" } }`.

## Dashboards
- Create a service dashboard with: request rate, error rate, latency percentiles, resource usage.
- Create a business dashboard with: signups, active users, transactions, revenue metrics.
- Use consistent time ranges and refresh intervals across dashboards.
- Add annotations for deployments, incidents, and configuration changes.
