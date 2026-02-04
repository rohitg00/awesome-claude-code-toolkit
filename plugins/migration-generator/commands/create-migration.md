# /create-migration - Create Database Migration

Generate a database migration file for schema changes.

## Steps

1. Ask the user for the migration description (e.g., "add users table", "add email index")
2. Detect the database and migration tool: Prisma, Knex, TypeORM, Alembic, Django, Rails
3. Analyze the requested schema change: new table, alter column, add index, etc.
4. Generate the up migration with the schema change SQL or ORM commands
5. Generate the corresponding down migration to reverse the change
6. Add proper column types, constraints, defaults, and nullability
7. Include index creation for foreign keys and frequently queried columns
8. Add data migration logic if the schema change requires data transformation
9. Validate the migration SQL syntax for the target database engine
10. Name the migration file with timestamp prefix and descriptive slug
11. Save the migration to the correct migrations directory
12. Report the created migration path and provide a preview of the SQL

## Rules

- Always include both up and down migration logic
- Use the ORM's migration generator when available instead of raw SQL
- Add NOT NULL constraints with DEFAULT values to avoid breaking existing rows
- Create indexes for all foreign key columns
- Use transactional migrations when the database supports DDL transactions
- Test the migration against a local development database before committing
- Include a comment explaining the purpose of the migration
