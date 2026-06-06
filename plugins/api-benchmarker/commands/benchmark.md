# /benchmark - Benchmark API Endpoints

Run performance benchmarks against API endpoints.

## Steps

1. Ask the user for the target endpoint URL and HTTP method
2. Configure the request: headers, authentication, request body, query parameters
3. Run a warmup phase: 10 requests to prime caches and connections
4. Execute the benchmark with configurable parameters:
   - Concurrent connections (default: 10)
   - Total requests (default: 1000)
   - Duration-based (alternative to request count)
5. Capture per-request metrics: response time, status code, response size
6. Calculate statistics: min, max, mean, median, p95, p99 response times
7. Calculate throughput: requests per second, bytes per second
8. Record error rate and categorize errors by status code
9. Detect performance degradation over the benchmark duration
10. Compare against SLA targets if defined
11. Save raw results in JSON format for further analysis
12. Present a formatted summary with key metrics and pass/fail status

## Rules

- Always include a warmup phase before measuring
- Use keep-alive connections to simulate realistic client behavior
- Record and report all HTTP status codes, not just 200s
- Include connection time separately from response time
- Do not benchmark production endpoints without explicit permission
- Run from a network location representative of actual users
- Report the server and client environment for reproducibility
