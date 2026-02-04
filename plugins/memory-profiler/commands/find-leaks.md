# /find-leaks - Find Memory Leaks

Detect and diagnose memory leaks in the application.

## Steps

1. Configure the application for leak detection with appropriate tooling
2. Establish a baseline memory measurement at application startup
3. Run a repetitive workload: process N requests, render N times, or execute N iterations
4. Measure memory after each iteration to detect steady growth
5. Force garbage collection between measurements to isolate true leaks
6. Identify objects that grow in count across iterations without being released
7. Trace the retention path: what is holding references to leaked objects
8. Check common leak sources:
   - Event listeners not removed on cleanup
   - Closures capturing large scopes
   - Growing caches without eviction
   - Circular references preventing GC
   - Timers and intervals not cleared
9. For each leak, identify the source file, line, and the allocation site
10. Suggest specific fixes: removeEventListener, WeakRef, cache size limits
11. Verify the fix by re-running the leak detection scenario
12. Report: leaks found, estimated memory impact, fix suggestions

## Rules

- Run leak detection for at least 100 iterations to confirm a pattern
- Distinguish between expected memory growth and actual leaks
- Check both heap memory and native memory (buffers, file handles)
- Verify leaks are reproducible before reporting
- Consider the application lifecycle; some growth is expected during warmup
- Check for connection pool leaks (database, HTTP, WebSocket)
- Report the growth rate (bytes per iteration) for each detected leak
