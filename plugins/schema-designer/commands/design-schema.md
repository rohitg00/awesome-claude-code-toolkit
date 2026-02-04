# /design-schema - Design Database Schema

Design a database schema based on application requirements.

## Steps

1. Ask the user about the domain: entities, relationships, and business rules
2. Identify the core entities and their attributes with data types
3. Define primary keys: prefer UUIDs for distributed systems, auto-increment for simple apps
4. Map relationships: one-to-one, one-to-many, many-to-many with junction tables
5. Add foreign key constraints with appropriate ON DELETE behavior (CASCADE, SET NULL, RESTRICT)
6. Design indexes for primary access patterns and common query filters
7. Add unique constraints for business-unique fields (email, username, slug)
8. Include audit columns: created_at, updated_at, deleted_at (soft delete)
9. Consider normalization: aim for 3NF, denormalize only with clear performance justification
10. Add check constraints for data validation (positive amounts, valid status values)
11. Generate the schema as SQL DDL statements for the target database
12. Create a visual representation of the schema as a text-based ERD

## Rules

- Use consistent naming: snake_case for columns, plural for table names
- Every table must have a primary key
- Add indexes for all foreign keys and common WHERE clause columns
- Use appropriate column types (do not use VARCHAR for everything)
- Include created_at and updated_at timestamps on all tables
- Design for the most common queries, not edge cases
- Document each table's purpose with a comment
