# /profile-memory - Profile Memory Usage

Capture and analyze memory usage of the application.

## Steps

1. Detect the application runtime: Node.js, Python, Java, Go, or browser
2. Configure the profiling tool: Node.js --inspect, Python tracemalloc, Java VisualVM
3. Start the application with memory profiling enabled
4. Capture an initial heap snapshot as the baseline
5. Execute the workload or user scenario to profile
6. Capture a second heap snapshot after the workload completes
7. Compare the two snapshots to identify memory growth
8. Analyze retained objects: which objects are keeping memory alive
9. Identify the top 20 memory consumers by retained size
10. Check for common leak patterns: growing arrays, event listeners, closures, caches
11. Calculate total memory usage: heap used, heap total, RSS, external
12. Generate a memory profile report with growth analysis and object counts

## Rules

- Take multiple snapshots at intervals to detect gradual memory growth
- Run the profiled scenario multiple times to distinguish leaks from normal allocation
- Focus on retained size, not shallow size, for identifying actual memory impact
- Include GC metrics: frequency, pause time, reclaimed memory
- Profile under realistic load conditions, not idle state
- Do not profile with debugger attached in production
- Report memory in human-readable units (KB, MB, GB)
