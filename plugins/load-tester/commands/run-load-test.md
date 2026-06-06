# /run-load-test - Execute Load Test

Run load and stress tests against API endpoints or web pages.

## Steps

1. Ask the user for the target URL or endpoint to test
2. Determine load testing parameters: concurrent users (default 50), duration (default 60s), ramp-up period (default 10s)
3. Check if a load testing tool is installed (k6, Artillery, or autocannon); recommend k6 if none found
4. Create or locate the load test script for the target endpoint
5. Configure request headers, authentication tokens, and payload if needed
6. Execute the load test with the specified parameters
7. Monitor real-time metrics: requests/sec, latency percentiles (p50, p95, p99), error rate
8. Capture the full results including response time distribution
9. Identify performance bottlenecks: slow endpoints, high error rates, timeout patterns
10. Present results in a formatted table with pass/fail thresholds
11. Save the results to a timestamped report file

## Rules

- Never run load tests against production without explicit user confirmation
- Default to a conservative load profile (50 VUs, 60s duration) unless specified
- Always include a ramp-up period to avoid sudden spikes
- Monitor system resources if testing locally (CPU, memory)
- Stop the test immediately if error rate exceeds 50%
- Include response time percentiles, not just averages
- Warn if the target appears to be a third-party service
