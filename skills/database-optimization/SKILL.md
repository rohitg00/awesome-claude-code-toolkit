---
name: database-optimization
description: Query optimization, indexing strategies, and database performance tuning for PostgreSQL and MySQL
---

# Database Optimization

## EXPLAIN Analysis

Always run `EXPLAIN ANALYZE` before optimizing. Read the output bottom-up.

```sql
-- PostgreSQL
EXPLAIN (ANALYZE, BUFFERS, FORMAT TEXT) SELECT ...;

-- MySQL
EXPLAIN ANALYZE SELECT ...;
```

Key metrics to watch:
- **Seq Scan** on large tables = missing index
- **Nested Loop** with high row count = consider hash/merge join
- **Sort** without index = add index on sort column
- **Rows estimated vs actual** divergence = stale statistics, run `ANALYZE`

## Index Strategies

### B-tree (default, most cases)
```sql
CREATE INDEX idx_users_email ON users (email);
CREATE INDEX idx_orders_user_date ON orders (user_id, created_at DESC);
```
Use for: equality, range queries, sorting. Column order matters in composite indexes: put equality columns first, then range/sort columns.

### Partial Index (PostgreSQL)
```sql
CREATE INDEX idx_orders_pending ON orders (created_at)
  WHERE status = 'pending';
```
Use when queries always filter on a specific condition. Dramatically smaller than full indexes.

### GIN (PostgreSQL - arrays, JSONB, full-text)
```sql
CREATE INDEX idx_products_tags ON products USING GIN (tags);
CREATE INDEX idx_docs_search ON documents USING GIN (to_tsvector('english', content));
```

### GiST (PostgreSQL - spatial, range types)
```sql
CREATE INDEX idx_locations_point ON locations USING GiST (coordinates);
CREATE INDEX idx_events_period ON events USING GiST (tsrange(start_at, end_at));
```

### Covering Index (index-only scans)
```sql
-- PostgreSQL
CREATE INDEX idx_users_email_name ON users (email) INCLUDE (name);

-- MySQL
CREATE INDEX idx_users_email_name ON users (email, name);
```

## N+1 Query Detection

Symptom: 1 query to fetch parent + N queries for each child.

```python
# BAD: N+1
users = db.query(User).all()
for user in users:
    print(user.orders)  # triggers query per user

# GOOD: eager load
users = db.query(User).options(joinedload(User.orders)).all()
```

```javascript
// BAD: N+1
const users = await User.findAll();
for (const user of users) {
  const orders = await Order.findAll({ where: { userId: user.id } });
}

// GOOD: batch load
const users = await User.findAll({ include: [Order] });
```

Detection: enable query logging, count queries per request. More than 10 queries for a single endpoint is a red flag.

## Connection Pooling

```
Rule of thumb: pool_size = (core_count * 2) + disk_count
Typical web app: 10-20 connections per app instance
```

PostgreSQL:
- Use PgBouncer in transaction mode for serverless/high-connection scenarios
- Set `idle_in_transaction_session_timeout = '30s'`
- Monitor with `pg_stat_activity`

MySQL:
- Set `max_connections` based on available RAM (each connection uses ~10MB)
- Use ProxySQL for connection multiplexing
- Monitor with `SHOW PROCESSLIST`

## Read Replicas

- Route all `SELECT` queries to replicas
- Route all writes to primary
- Account for replication lag (typically 10-100ms)
- Never read-after-write from a replica; use primary for consistency-critical reads
- Use connection-level routing, not query-level

```python
# SQLAlchemy read replica routing
class RoutingSession(Session):
    def get_bind(self, mapper=None, clause=None):
        if self._flushing or self.is_modified():
            return engines["primary"]
        return engines["replica"]
```

## Partition Strategies

### Range Partitioning (time-series data)
```sql
-- PostgreSQL
CREATE TABLE events (
    id bigint GENERATED ALWAYS AS IDENTITY,
    created_at timestamptz NOT NULL,
    data jsonb
) PARTITION BY RANGE (created_at);

CREATE TABLE events_2025_q1 PARTITION OF events
    FOR VALUES FROM ('2025-01-01') TO ('2025-04-01');
CREATE TABLE events_2025_q2 PARTITION OF events
    FOR VALUES FROM ('2025-04-01') TO ('2025-07-01');
```

### Hash Partitioning (even distribution)
```sql
CREATE TABLE sessions (
    id uuid PRIMARY KEY,
    user_id bigint NOT NULL
) PARTITION BY HASH (user_id);

CREATE TABLE sessions_0 PARTITION OF sessions FOR VALUES WITH (MODULUS 4, REMAINDER 0);
CREATE TABLE sessions_1 PARTITION OF sessions FOR VALUES WITH (MODULUS 4, REMAINDER 1);
```

Partition when tables exceed 50-100GB or when you need to drop old data quickly.

## Query Optimization Checklist

1. Run `EXPLAIN ANALYZE` and read the plan
2. Check for sequential scans on tables with >10K rows
3. Verify index usage (check `idx_scan` in `pg_stat_user_indexes`)
4. Look for implicit type casts that prevent index use
5. Replace `SELECT *` with specific columns
6. Add `LIMIT` to queries that only need a subset
7. Use `EXISTS` instead of `COUNT(*) > 0`
8. Batch `INSERT`/`UPDATE` operations (500-1000 rows per batch)
9. Avoid functions on indexed columns in `WHERE` clauses
10. Monitor slow query log (pg: `log_min_duration_statement = 100`)

## Dangerous Patterns

- `LIKE '%term%'` on unindexed columns (use full-text search instead)
- `ORDER BY RANDOM()` (use `TABLESAMPLE` or application-level randomization)
- `SELECT DISTINCT` masking a join problem
- Missing `WHERE` on `UPDATE`/`DELETE` (always verify with `SELECT` first)
- Long-running transactions holding locks
- Using `OFFSET` for deep pagination (use keyset/cursor pagination instead)
