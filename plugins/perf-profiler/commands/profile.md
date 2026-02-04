# /perf-profiler:profile

Analyze the codebase for performance bottlenecks, resource inefficiencies, and scalability concerns.

## Process

1. Identify the project type and performance-critical areas:
   - Read the project structure to understand the architecture (monolith, microservices, SPA, CLI)
   - Identify hot paths: API request handlers, database queries, render cycles, data processing pipelines
   - Check for existing performance tooling (profiler configs, benchmark files, load test scripts)

2. Static analysis for common performance anti-patterns:

### Database & Data Access
- Search for N+1 query patterns: loops that execute individual queries instead of batch operations
- Find missing database indexes by checking query WHERE clauses against schema definitions
- Identify unbounded queries: SELECT without LIMIT, find() without pagination
- Look for ORM eager loading where lazy loading would suffice (and vice versa)
- Check for missing connection pooling configuration

### Memory & Resource Management
- Find large object allocations inside loops or hot paths
- Search for unclosed resources: file handles, database connections, HTTP clients, streams
- Identify memory-heavy data structures where lighter alternatives exist (Map vs Object, Set vs Array for lookups)
- Look for string concatenation in loops instead of StringBuilder/join patterns
- Check for event listener leaks (addEventListener without corresponding removeEventListener)

### Concurrency & Async
- Find synchronous blocking calls on async hot paths (fs.readFileSync in request handlers)
- Identify sequential awaits that could be parallelized with Promise.all or equivalent
- Look for missing caching on repeated expensive computations
- Check for thread pool exhaustion risks (CPU-bound work on the event loop)
- Find busy-wait patterns or polling that could use event-driven approaches

### Frontend Performance (if applicable)
- Search for components re-rendering on every parent render (missing React.memo, useMemo, useCallback)
- Identify large bundle imports where tree-shaking is possible
- Find synchronous layout calculations that trigger forced reflows
- Check for unoptimized images (missing lazy loading, missing dimensions, no srcset)
- Look for blocking scripts in the document head

### Network & I/O
- Find API calls without timeout configuration
- Identify missing retry logic with exponential backoff for external service calls
- Check for uncompressed responses (missing gzip/brotli configuration)
- Look for chatty protocols where batching would reduce round trips

3. Quantify impact where possible:
   - Estimate the number of extra database queries from N+1 patterns (per request)
   - Calculate potential memory savings from data structure changes
   - Estimate latency reduction from parallelizing sequential operations
   - Note the expected bundle size reduction from tree-shaking opportunities

## Output Format

Present findings organized by impact (highest first):

For each finding:
- **Location**: File path and line range
- **Issue**: Clear description of the anti-pattern
- **Impact**: Estimated performance cost (latency, memory, CPU, bandwidth)
- **Fix**: Specific code change or approach to resolve it
- **Priority**: Critical (blocking at current scale) / High (will matter soon) / Medium (optimization opportunity)

End with a summary table: total findings by category and a recommended order of remediation.

## Rules

- Focus on measurable impact, not micro-optimizations
- An optimization that saves 1ms on a path called once per hour is not worth flagging
- Consider the project's scale: what matters for 100 users differs from 100K users
- Suggest profiling tools for findings that need runtime validation
- Do not recommend premature optimization; only flag patterns with clear cost
