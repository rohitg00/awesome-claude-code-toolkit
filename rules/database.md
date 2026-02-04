# Database

## Query Patterns
- Use parameterized queries for all database operations. Never interpolate user input into SQL.
- Select only needed columns. Avoid `SELECT *` in production queries.
- Use CTEs (Common Table Expressions) for complex queries instead of nested subqueries.
- Batch inserts and updates using `INSERT INTO ... VALUES (...), (...)` or `unnest` patterns.
- Use database-level constraints (NOT NULL, UNIQUE, CHECK, FK) as the source of truth for data integrity.

## N+1 Prevention
- Detect N+1 queries by enabling query logging in development.
- Use eager loading or `JOIN` when fetching parent-child relationships.
- In ORMs, use `include`/`with`/`joinedload` rather than lazy loading in loops.
- For GraphQL, use DataLoader or equivalent batching to collapse repeated queries.
- Add automated N+1 detection in tests using query counting assertions.

## Indexing
- Create indexes on all foreign key columns.
- Create indexes on columns used in `WHERE`, `ORDER BY`, and `JOIN` clauses.
- Use composite indexes for queries that filter on multiple columns. Column order matters.
- Use partial indexes for queries that filter on a fixed condition (e.g., `WHERE deleted_at IS NULL`).
- Monitor slow query logs and add indexes for queries exceeding 100ms.
- Remove unused indexes. They slow down writes and waste storage.

## Migrations
- Migrations are forward-only in production. Never edit a deployed migration.
- Each migration must be reversible with a corresponding down migration.
- Use non-locking migration strategies for large tables (add column, backfill, then add constraint).
- Test migrations against a copy of production data before deploying.
- Name migrations descriptively: `20260115_add_orders_status_index.sql`.

## Schema Design
- Use UUIDs (v7 for sortability) as primary keys for public-facing entities.
- Add `created_at` and `updated_at` timestamps to all tables with database-level defaults.
- Use soft deletes (`deleted_at` timestamp) for user-facing data. Hard delete only for system data.
- Normalize to third normal form by default. Denormalize intentionally with a documented reason.
- Use `ENUM` types or reference tables for fixed value sets, not free-text columns.

## Connection Management
- Use connection pooling (PgBouncer, HikariCP, or ORM-level pooling).
- Set pool size to `(2 * CPU cores) + number of disks` as a starting point.
- Set query timeouts: 5 seconds for web requests, 30 seconds for background jobs.
- Handle connection failures with retry logic and exponential backoff.
