# /generate-seeds - Generate Database Seeds

Generate database seed scripts with realistic data for development.

## Steps

1. Read the database schema from ORM models, migrations, or schema files
2. Determine table dependencies from foreign key relationships
3. Calculate insertion order to satisfy all foreign key constraints
4. Generate realistic data for each table using contextual patterns:
   - User tables: realistic names, emails, hashed passwords
   - Product tables: real-sounding names, descriptions, prices
   - Address tables: valid-format addresses with real city/state combinations
5. Create referential data: link orders to users, reviews to products, etc.
6. Generate lookup/reference data: categories, statuses, roles, permissions
7. Include edge cases: users with no orders, products with no reviews
8. Write the seed script in the project's ORM format (Prisma seed, Knex seed, etc.)
9. Add a reset function to clear and re-seed the database
10. Make seeds idempotent: running twice produces the same result
11. Save seed files to the standard seed directory (db/seeds, prisma/seed.ts, etc.)

## Rules

- Generate at least 50 records for main entities to test pagination and search
- Use deterministic faker seeds for reproducible data across environments
- Never include real personal data or valid credentials in seeds
- Respect unique constraints by generating unique values
- Include the full range of enum values to test all UI states
- Generate timestamps that span a realistic time range (past 6 months)
- Include the seed execution in package.json scripts or Makefile
