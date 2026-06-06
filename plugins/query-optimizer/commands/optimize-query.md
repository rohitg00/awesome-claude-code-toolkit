# /optimize-query - Optimize SQL Query

Analyze and optimize a slow SQL query for better performance.

## Steps

1. Read the SQL query provided by the user or from a slow query log
2. Parse the query to understand: tables, joins, conditions, aggregations, sorting
3. Run EXPLAIN ANALYZE to get the current execution plan
4. Identify performance bottlenecks: full table scans, nested loops, sort operations
5. Check if appropriate indexes exist for WHERE, JOIN, and ORDER BY columns
6. Suggest index additions that would improve the query execution plan
7. Rewrite the query to eliminate N+1 patterns, unnecessary subqueries, or redundant joins
8. Replace correlated subqueries with JOINs or CTEs where beneficial
9. Add query hints or optimizer directives if needed for the specific database
10. Run EXPLAIN ANALYZE on the optimized query and compare execution times
11. Present a before/after comparison: execution plan, estimated rows, actual time
12. Provide the optimized query with inline comments explaining each change

## Rules

- Always show the EXPLAIN output before and after optimization
- Prefer index-based solutions over query rewrites when possible
- Do not add indexes without considering write performance impact
- Consider the data distribution when recommending indexes
- Test optimizations with production-like data volumes
- Preserve the exact result set; optimization must not change query results
- Warn about queries that may perform differently with larger datasets
