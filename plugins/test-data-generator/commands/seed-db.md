# /seed-db - Seed Database

Seed a database with generated test data.

## Steps

1. Detect the database type and ORM from project configuration (Prisma, TypeORM, Sequelize, Django, etc.)
2. Read the database schema to understand tables, columns, and relationships
3. Determine the correct insertion order based on foreign key dependencies
4. Generate appropriate test data for each table using realistic values
5. Create the seed script in the project's preferred format and language
6. Handle auto-increment IDs and UUID generation appropriately
7. Include data for lookup tables and enum-like reference data
8. Add transaction wrapping to ensure atomic seeding (all or nothing)
9. Include a cleanup step to truncate tables before seeding
10. Run the seed script against the development database
11. Verify seed data by querying record counts for each table
12. Report: tables seeded, total records inserted, execution time

## Rules

- Never run seed scripts against production databases
- Always wrap seed operations in transactions for rollback safety
- Respect foreign key constraints by inserting parent records first
- Use the ORM's built-in seeding mechanism when available
- Include idempotent checks so seeds can be re-run safely
- Generate enough data to test pagination (at least 25 records for list endpoints)
- Store seed scripts in a dedicated seeds or fixtures directory
