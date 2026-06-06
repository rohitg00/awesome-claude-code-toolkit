# /generate-erd - Generate Entity Relationship Diagram

Generate a visual ERD from the existing database schema.

## Steps

1. Detect the database schema source: ORM models, migration files, or live database
2. Extract all tables with their columns, types, and constraints
3. Identify all relationships from foreign keys and junction tables
4. Map relationship cardinality: one-to-one, one-to-many, many-to-many
5. Generate a Mermaid diagram definition with all entities and relationships
6. Include column names and types in each entity box
7. Mark primary keys (PK), foreign keys (FK), and unique constraints (UK)
8. Group related tables visually (users/auth, products/orders, etc.)
9. Add relationship labels describing the business meaning
10. Save the Mermaid diagram to docs/erd.md
11. If dbdiagram.io format is preferred, generate DBML syntax as well
12. Report: total tables, relationships, and diagram output path

## Rules

- Include all tables including junction tables for many-to-many relationships
- Show column types in a readable format (not database-specific syntax)
- Highlight primary and foreign keys visually
- Group related entities close together in the diagram
- Use crow's foot notation for relationship cardinality
- Do not include migration history tables or framework internal tables
- Keep the diagram readable; split into sub-diagrams if more than 20 tables
