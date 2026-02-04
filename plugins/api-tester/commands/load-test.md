Run a load test against an API endpoint to measure throughput and identify breaking points.

## Steps

1. Define load test parameters:
   - Target URL and HTTP method.
   - Concurrent connections (start low, ramp up).
   - Duration of the test.
   - Request payload and headers.
2. Select the load testing tool:
   - `wrk` or `wrk2` for HTTP benchmarking.
   - `k6` for scripted load tests.
   - `ab` (Apache Bench) for simple tests.
   - `hey` for quick Go-based load tests.
3. Run a warm-up phase with low concurrency (10 connections, 10 seconds).
4. Execute the main load test in stages:
   - Stage 1: Normal load (expected concurrent users).
   - Stage 2: Peak load (2x expected).
   - Stage 3: Stress test (increase until error rate > 5%).
5. Collect metrics at each stage:
   - Requests per second (throughput).
   - Latency distribution (P50, P95, P99).
   - Error rate and error types.
   - Resource utilization (CPU, memory) if accessible.
6. Identify the breaking point and bottleneck.
7. Generate a report with recommendations.

## Format

```
Load Test: <METHOD> <endpoint>

| Stage | Concurrency | RPS | P50 (ms) | P99 (ms) | Errors |
|-------|-------------|-----|----------|----------|--------|
| Normal | 10 | 500 | 20 | 85 | 0% |
| Peak | 50 | 1200 | 45 | 200 | 0.1% |
| Stress | 200 | 800 | 500 | 2000 | 5.2% |

Breaking point: ~150 concurrent connections
Bottleneck: Database connection pool exhaustion

Recommendations:
  1. Increase connection pool size from 10 to 50
  2. Add connection queuing with backpressure
```

## Rules

- Never run load tests against production without explicit permission.
- Always include a warm-up phase before measuring.
- Ramp up gradually; do not jump to maximum load immediately.
- Record baseline metrics before the test for comparison.
- Stop the test if error rate exceeds 10% to avoid cascading failures.
