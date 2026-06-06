Add database indexes to improve query performance with migration safety.

## Steps


1. Identify the query patterns that need indexing:
2. Choose the index type:
3. Design the index:
4. Create the migration:
5. Estimate the impact:
6. Deploy safely:

## Format


```
Table: <table name>
Index: <index name>
Columns: <column list>
Type: <B-tree|Hash|GIN|GiST>
```


## Rules

- Always use CONCURRENTLY for production index creation.
- Name indexes descriptively: idx_table_column1_column2.
- Do not create redundant indexes (check existing indexes first).

