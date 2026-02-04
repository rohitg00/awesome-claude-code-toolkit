Run benchmarks to measure and compare performance of code implementations.

## Steps

1. Identify the target for benchmarking:
   - A specific function or module.
   - Two implementations to compare (before/after refactor).
   - An API endpoint under load.
2. Set up the benchmark:
   - Detect the runtime and available benchmarking tools.
   - Node.js: Use `vitest bench` or custom benchmark harness.
   - Python: Use `pytest-benchmark` or `timeit`.
   - Go: Use `testing.B` built-in benchmarks.
   - Rust: Use `criterion` or built-in `#[bench]`.
3. Configure benchmark parameters:
   - Warm-up iterations to stabilize JIT and caches.
   - Measurement iterations (minimum 100 for statistical significance).
   - Input data size variations (small, medium, large).
4. Run benchmarks and collect results:
   - Operations per second.
   - Average time per operation.
   - Memory allocation per operation.
   - P50, P95, P99 latencies.
5. If comparing implementations, calculate relative performance difference.
6. Generate a summary with statistical confidence.

## Format

```
Benchmark: <name>
Iterations: <N>

| Implementation | ops/sec | avg (ms) | P99 (ms) | mem (MB) |
|---------------|---------|----------|----------|----------|
| Original      | 10,000  | 0.10     | 0.25     | 2.1      |
| Optimized     | 25,000  | 0.04     | 0.08     | 1.8      |

Improvement: 2.5x faster, 14% less memory
Confidence: 95% (p < 0.05)
```

## Rules

- Always include warm-up iterations before measurement.
- Run enough iterations for statistically significant results.
- Report standard deviation alongside averages.
- Benchmark on consistent hardware; note the environment.
- Disable garbage collection pauses during benchmarks where possible.
