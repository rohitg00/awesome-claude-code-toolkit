# /perf-profiler:optimize

Apply targeted performance optimizations to a specified file, function, or module.

## Process

1. Determine the optimization target:
   - If a file path is provided, focus on that file
   - If a function name is provided, locate it with Grep and analyze it in context
   - If no target is specified, run the profile command first and pick the highest-impact finding

2. Read the target code and its surrounding context:
   - Understand the call sites: how often is this code invoked and under what conditions
   - Read the tests to understand expected behavior and edge cases
   - Check if the code is in a hot path (request handler, render loop, event processor)

3. Apply appropriate optimization techniques:

### Caching
- Add memoization for pure functions called with the same arguments repeatedly
- Implement request-scoped caching for database lookups used multiple times per request
- Add HTTP caching headers for responses that can be cached (ETag, Cache-Control)
- Use compute-once patterns for expensive initialization (lazy singletons, module-level cache)

### Batching & Deduplication
- Replace N individual queries with a single batch query using IN clauses or DataLoader patterns
- Deduplicate redundant API calls within the same execution context
- Aggregate multiple small writes into fewer large writes (bulk insert, batch update)
- Use write-behind patterns for non-critical data persistence

### Algorithmic Improvements
- Replace O(n^2) nested loops with hash-based lookups (Map/Set) for O(n) performance
- Use binary search on sorted data instead of linear scan
- Replace repeated array filtering with a single pass that partitions the data
- Use streaming/iterators for large datasets instead of loading everything into memory

### Async & Concurrency
- Parallelize independent operations with Promise.all, asyncio.gather, or goroutine groups
- Move CPU-intensive work off the main thread (Web Workers, worker_threads, background jobs)
- Add connection pooling for database and HTTP clients
- Implement circuit breakers for external service calls to fail fast

### Data Structure Selection
- Use Map instead of Object for frequent key-value lookups with dynamic keys
- Use Set instead of Array for membership testing
- Use typed arrays (Uint8Array, Float64Array) for numeric data processing
- Consider struct-of-arrays layout for batch processing of homogeneous data

### Bundle & Load Optimization (Frontend)
- Split large imports into dynamic imports for code splitting
- Replace heavy libraries with lighter alternatives (date-fns vs moment, preact vs react for widgets)
- Move non-critical scripts to defer or async loading
- Implement virtual scrolling for long lists

4. After applying changes:
   - Verify that all existing tests still pass
   - Add a brief inline note explaining why the optimization was applied (if not self-evident)
   - Measure the improvement if benchmarking tools are available (`time`, `console.time`, `perf_hooks`)

## Output

Present each optimization as:
- **Before**: The original code (relevant snippet)
- **After**: The optimized code
- **Rationale**: Why this is faster and by approximately how much
- **Trade-offs**: Any complexity or memory trade-offs introduced

## Rules

- Never sacrifice correctness for performance
- Every optimization must preserve the exact observable behavior (same inputs produce same outputs)
- Prefer standard library solutions over custom implementations
- Do not optimize code that is not in a hot path unless specifically asked
- If an optimization introduces complexity, it must deliver at least a 2x improvement to justify it
- Always run existing tests after applying changes to verify correctness
- Document any new dependencies or memory requirements introduced by the optimization
