---
name: postgres-optimization
description: PostgreSQL optimization including indexes, query plans, partitioning, JSONB operations, and connection pooling
---

# PostgreSQL Optimization

## Index Strategies

```sql
-- B-tree index for equality and range queries (default)
CREATE INDEX idx_orders_customer_id ON orders (customer_id);

-- Composite index (column order matters: equality columns first, range last)
CREATE INDEX idx_orders_status_created ON orders (status, created_at DESC);

-- Partial index (smaller, faster for filtered queries)
CREATE INDEX idx_orders_pending ON orders (created_at)
  WHERE status = 'pending';

-- Covering index (avoids table lookup entirely)
CREATE INDEX idx_users_email_name ON users (email) INCLUDE (name, avatar_url);

-- GIN index for JSONB containment queries
CREATE INDEX idx_products_metadata ON products USING GIN (metadata);

-- GiST index for full-text search
CREATE INDEX idx_articles_search ON articles USING GiST (
  to_tsvector('english', title || ' ' || body)
);

-- Concurrent index creation (no table lock)
CREATE INDEX CONCURRENTLY idx_large_table_col ON large_table (col);
```

## Reading Query Plans

```sql
EXPLAIN (ANALYZE, BUFFERS, FORMAT TEXT)
SELECT o.id, o.total, u.name
FROM orders o
JOIN users u ON o.user_id = u.id
WHERE o.status = 'shipped'
  AND o.created_at > NOW() - INTERVAL '30 days'
ORDER BY o.created_at DESC
LIMIT 20;
```

Key things to look for in the plan:
- `Seq Scan` on large tables indicates a missing index
- `Nested Loop` with high row estimates suggests missing join index
- `Sort` without `Index Scan` means the sort is happening in memory/disk
- `Buffers: shared hit` vs `shared read` shows cache efficiency

## Partitioning

```sql
CREATE TABLE events (
    id          BIGINT GENERATED ALWAYS AS IDENTITY,
    event_type  TEXT NOT NULL,
    payload     JSONB NOT NULL,
    created_at  TIMESTAMPTZ NOT NULL DEFAULT NOW()
) PARTITION BY RANGE (created_at);

CREATE TABLE events_2024_q1 PARTITION OF events
    FOR VALUES FROM ('2024-01-01') TO ('2024-04-01');
CREATE TABLE events_2024_q2 PARTITION OF events
    FOR VALUES FROM ('2024-04-01') TO ('2024-07-01');

-- Index on each partition (inherited automatically in PG 11+)
CREATE INDEX ON events (created_at, event_type);
```

Partition tables with more than 10M rows when queries consistently filter on the partition key.

## JSONB Operations

```sql
-- Query nested JSONB fields
SELECT * FROM products
WHERE metadata @> '{"category": "electronics"}'
  AND (metadata ->> 'price')::numeric < 500;

-- Update nested JSONB
UPDATE products
SET metadata = jsonb_set(metadata, '{stock}', to_jsonb(stock - 1))
WHERE id = 'abc';

-- Aggregate JSONB arrays
SELECT id, jsonb_array_elements_text(metadata -> 'tags') AS tag
FROM products
WHERE metadata ? 'tags';
```

## Connection Pooling

```ini
# pgbouncer.ini
[databases]
app = host=localhost port=5432 dbname=app

[pgbouncer]
pool_mode = transaction
max_client_conn = 1000
default_pool_size = 25
min_pool_size = 5
reserve_pool_size = 5
server_idle_timeout = 300
```

Use transaction-level pooling for web applications. Session-level pooling for apps that use prepared statements or temp tables.

## Common Tuning Parameters

```sql
-- Check for slow queries
SELECT query, calls, mean_exec_time, total_exec_time
FROM pg_stat_statements
ORDER BY total_exec_time DESC
LIMIT 10;

-- Find unused indexes
SELECT indexrelname, idx_scan, pg_size_pretty(pg_relation_size(indexrelid))
FROM pg_stat_user_indexes
WHERE idx_scan = 0
ORDER BY pg_relation_size(indexrelid) DESC;
```

## Anti-Patterns

- Creating indexes on every column instead of analyzing actual query patterns
- Using `SELECT *` when only a few columns are needed
- Not using `EXPLAIN ANALYZE` to verify index usage
- Storing large blobs in JSONB when a separate table with proper types is better
- Missing connection pooling (each connection uses ~10MB of server memory)
- Running `VACUUM FULL` during peak hours (locks the entire table)

## Checklist

- [ ] Indexes match actual query patterns (check `pg_stat_statements`)
- [ ] Composite indexes ordered: equality, then sort, then range columns
- [ ] `EXPLAIN ANALYZE` run on all critical queries
- [ ] Partial indexes used for frequently filtered subsets
- [ ] Connection pooler (PgBouncer/pgcat) in front of PostgreSQL
- [ ] Table partitioning considered for tables over 10M rows
- [ ] Unused indexes identified and dropped
- [ ] `pg_stat_statements` enabled for query performance monitoring
