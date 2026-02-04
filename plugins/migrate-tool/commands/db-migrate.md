Generate a database migration file for schema changes.

## Steps

1. Detect the ORM or migration tool in use (Prisma, Drizzle, Knex, Alembic, Django, GORM).
2. Analyze the requested schema change:
   - Add/remove tables or columns.
   - Modify column types, constraints, or defaults.
   - Add/remove indexes or foreign keys.
3. Generate the migration file in the correct format for the tool.
4. Include both `up` and `down` migration functions for reversibility.
5. Handle data migrations if column types change:
   - Add new column, copy data, drop old column, rename new column.
6. Validate the migration against the current schema state.
7. Run the migration in dry-run mode if the tool supports it.

## Format

```
Migration: <YYYYMMDDHHMMSS>_<description>
Tool: <ORM/migration tool>

Up:
  - <change description>

Down:
  - <reverse change>

Data migration required: <yes/no>
```

## Rules

- Every migration must be reversible with a down function.
- Never drop columns or tables without a data backup step.
- Use transactions for multi-step migrations when supported.
- Test migrations against a copy of production data structure.
- Name migrations with timestamps to prevent ordering conflicts.
