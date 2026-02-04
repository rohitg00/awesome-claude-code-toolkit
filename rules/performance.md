# Performance Rules

## Loading Strategy
- Lazy load routes and heavy components. Only load what the user needs right now.
- Use code splitting at route boundaries.
- Defer non-critical scripts and stylesheets.
- Preload critical resources: fonts, above-the-fold images, key API data.
- Use dynamic imports for features behind user interaction (modals, drawers, editors).

## Caching
- Cache expensive computations with memoization. Invalidate when inputs change.
- Set appropriate HTTP cache headers: immutable for hashed assets, short TTL for API responses.
- Use CDN caching for static assets.
- Implement application-level caching (Redis, in-memory) for repeated database queries.
- Always define a cache invalidation strategy before adding a cache.

## Database Performance
- Add indexes on columns used in WHERE, JOIN, and ORDER BY clauses.
- Avoid N+1 queries. Use eager loading, joins, or batch queries.
- Use pagination for list endpoints. Prefer cursor-based over offset-based for large datasets.
- Profile slow queries with EXPLAIN ANALYZE and optimize them.
- Use connection pooling. Never open a new connection per request.
- Keep transactions short. Do not hold locks during I/O operations.

## API Performance
- Minimize payload size. Return only the fields the client needs.
- Use compression (gzip/brotli) for API responses.
- Implement request batching for clients that need multiple resources.
- Add request timeouts on both client and server sides.
- Use streaming for large responses instead of buffering everything in memory.

## Frontend Performance
- Optimize images: use WebP/AVIF, responsive sizes, lazy loading for below-the-fold.
- Minimize JavaScript bundle size. Track it in CI with bundle analyzer.
- Avoid layout shifts: set explicit dimensions on images and dynamic content.
- Debounce user input handlers (search, resize, scroll).
- Use `requestAnimationFrame` for visual updates, not `setTimeout`.

## Monitoring
- Measure before optimizing. Use profiling tools, not intuition.
- Set performance budgets: bundle size, Time to Interactive, API response time.
- Alert on P95/P99 latency, not just averages.
- Log slow queries and slow API responses for investigation.
