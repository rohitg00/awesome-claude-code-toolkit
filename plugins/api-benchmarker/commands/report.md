# /report - Generate Benchmark Report

Generate a comprehensive performance report from benchmark results.

## Steps

1. Load benchmark results from the most recent run or specified file
2. Calculate aggregate statistics across all benchmarked endpoints
3. Create a response time distribution histogram (text-based)
4. Rank endpoints by performance: fastest to slowest (p99 latency)
5. Identify endpoints that fail SLA requirements
6. Calculate throughput capacity: maximum sustainable requests per second
7. Analyze error patterns: which endpoints fail and at what concurrency level
8. Compare against previous benchmark results if available
9. Calculate performance regression or improvement percentages
10. Generate recommendations: caching candidates, scaling needs, optimization targets
11. Create an executive summary with overall system performance health
12. Save the report as markdown with embedded tables and charts

## Rules

- Present latency in milliseconds for fast endpoints, seconds for slow ones
- Always include both average and percentile metrics (averages hide outliers)
- Show error rates alongside performance metrics
- Include the test configuration in the report for reproducibility
- Flag any endpoint with p99 latency over 1 second as requiring attention
- Compare against industry benchmarks for the endpoint type (REST, GraphQL)
- Include a recommendations section prioritized by impact
