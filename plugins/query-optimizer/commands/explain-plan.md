# /explain-plan - Explain Query Execution Plan

Generate and interpret a SQL query execution plan in plain language.

## Steps

1. Take the SQL query from the user input
2. Determine the database engine (PostgreSQL, MySQL, SQLite, SQL Server)
3. Run EXPLAIN or EXPLAIN ANALYZE with the appropriate syntax for the engine
4. Parse the execution plan output into structured components
5. Identify each operation: Sequential Scan, Index Scan, Nested Loop, Hash Join, Sort
6. Explain each step in plain language: what table is read, how it is filtered
7. Highlight expensive operations: full table scans, large sort operations, hash joins
8. Calculate the cost percentage of each step relative to total query cost
9. Identify the critical path (most expensive sequence of operations)
10. Suggest specific improvements for the most costly operations
11. Estimate memory usage and temporary disk usage from the plan
12. Present the explanation as a step-by-step narrative

## Rules

- Translate database-specific terminology into plain English
- Highlight operations that scan more than 1000 rows without an index
- Show estimated vs actual rows to identify cardinality estimation errors
- Explain the difference between estimated cost and actual execution time
- Identify parallel query opportunities if the database supports them
- Note when the planner chose a suboptimal plan due to stale statistics
- Recommend ANALYZE/VACUUM if statistics appear outdated
