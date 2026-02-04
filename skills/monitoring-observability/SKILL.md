---
name: monitoring-observability
description: Monitoring and observability with OpenTelemetry, Prometheus, Grafana dashboards, and structured logging
---

# Monitoring & Observability

## OpenTelemetry Setup

```typescript
import { NodeSDK } from "@opentelemetry/sdk-node";
import { OTLPTraceExporter } from "@opentelemetry/exporter-trace-otlp-http";
import { OTLPMetricExporter } from "@opentelemetry/exporter-metrics-otlp-http";
import { HttpInstrumentation } from "@opentelemetry/instrumentation-http";
import { PgInstrumentation } from "@opentelemetry/instrumentation-pg";
import { PeriodicExportingMetricReader } from "@opentelemetry/sdk-metrics";

const sdk = new NodeSDK({
  serviceName: "order-service",
  traceExporter: new OTLPTraceExporter({
    url: "http://otel-collector:4318/v1/traces",
  }),
  metricReader: new PeriodicExportingMetricReader({
    exporter: new OTLPMetricExporter({
      url: "http://otel-collector:4318/v1/metrics",
    }),
    exportIntervalMillis: 15000,
  }),
  instrumentations: [
    new HttpInstrumentation(),
    new PgInstrumentation(),
  ],
});

sdk.start();
process.on("SIGTERM", () => sdk.shutdown());
```

## Custom Spans and Metrics

```typescript
import { trace, metrics, SpanStatusCode } from "@opentelemetry/api";

const tracer = trace.getTracer("order-service");
const meter = metrics.getMeter("order-service");

const orderCounter = meter.createCounter("orders.created", {
  description: "Number of orders created",
});

const orderDuration = meter.createHistogram("orders.processing_duration_ms", {
  description: "Order processing duration in milliseconds",
  unit: "ms",
});

async function createOrder(input: CreateOrderInput) {
  return tracer.startActiveSpan("createOrder", async (span) => {
    try {
      span.setAttributes({
        "order.customer_id": input.customerId,
        "order.item_count": input.items.length,
      });

      const start = performance.now();
      const order = await db.order.create({ data: input });

      orderCounter.add(1, { status: "success" });
      orderDuration.record(performance.now() - start);

      span.setStatus({ code: SpanStatusCode.OK });
      return order;
    } catch (error) {
      span.setStatus({ code: SpanStatusCode.ERROR, message: error.message });
      orderCounter.add(1, { status: "error" });
      throw error;
    } finally {
      span.end();
    }
  });
}
```

## Prometheus Metrics

```yaml
# prometheus.yml
global:
  scrape_interval: 15s

scrape_configs:
  - job_name: "api-servers"
    static_configs:
      - targets: ["api-1:9090", "api-2:9090"]
    metrics_path: /metrics

  - job_name: "node-exporter"
    static_configs:
      - targets: ["node-exporter:9100"]
```

```typescript
import { collectDefaultMetrics, Counter, Histogram, Registry } from "prom-client";

const registry = new Registry();
collectDefaultMetrics({ register: registry });

const httpRequestDuration = new Histogram({
  name: "http_request_duration_seconds",
  help: "HTTP request duration in seconds",
  labelNames: ["method", "route", "status"],
  buckets: [0.01, 0.05, 0.1, 0.5, 1, 5],
  registers: [registry],
});

app.use((req, res, next) => {
  const end = httpRequestDuration.startTimer();
  res.on("finish", () => {
    end({ method: req.method, route: req.route?.path ?? req.path, status: res.statusCode });
  });
  next();
});

app.get("/metrics", async (req, res) => {
  res.set("Content-Type", registry.contentType);
  res.end(await registry.metrics());
});
```

## Structured Logging

```typescript
import pino from "pino";

const logger = pino({
  level: process.env.LOG_LEVEL ?? "info",
  formatters: {
    level: (label) => ({ level: label }),
  },
  redact: ["req.headers.authorization", "password", "token"],
});

function requestLogger(req, res, next) {
  const start = Date.now();
  res.on("finish", () => {
    logger.info({
      method: req.method,
      url: req.url,
      status: res.statusCode,
      duration_ms: Date.now() - start,
      trace_id: req.headers["x-trace-id"],
    });
  });
  next();
}
```

## Alerting Rules

```yaml
groups:
  - name: api-alerts
    rules:
      - alert: HighErrorRate
        expr: rate(http_request_duration_seconds_count{status=~"5.."}[5m]) / rate(http_request_duration_seconds_count[5m]) > 0.05
        for: 5m
        labels:
          severity: critical
        annotations:
          summary: "Error rate above 5% for {{ $labels.route }}"

      - alert: HighLatency
        expr: histogram_quantile(0.99, rate(http_request_duration_seconds_bucket[5m])) > 2
        for: 10m
        labels:
          severity: warning
```

## Anti-Patterns

- Logging sensitive data (passwords, tokens, PII) without redaction
- Using string interpolation in log messages instead of structured fields
- Creating unbounded cardinality in metric labels (e.g., user IDs as labels)
- Not correlating logs and traces with a shared trace ID
- Alerting on symptoms (high CPU) without understanding root cause
- Missing SLO definitions before building dashboards

## Checklist

- [ ] OpenTelemetry SDK initialized with auto-instrumentation for HTTP, DB, and messaging
- [ ] Custom spans added for business-critical operations
- [ ] Metrics use bounded label cardinality
- [ ] Structured logging with JSON output and secret redaction
- [ ] Trace context propagated across service boundaries
- [ ] Alerting rules based on SLOs (error rate, latency percentiles)
- [ ] Dashboards show RED metrics (Rate, Errors, Duration) per service
- [ ] Log retention and rotation policies configured
