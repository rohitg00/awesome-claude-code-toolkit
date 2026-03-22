# /generate-data - Generate Test Data

Generate realistic test data based on schema definitions or models.

## Steps

1. Ask the user for the data model or schema to generate test data for
2. Analyze the model: field names, types, constraints, and relationships
3. Determine data generation strategy based on field semantics (name, email, address, etc.)
4. Use faker-compatible libraries to generate realistic values for each field
5. Respect field constraints: min/max length, required fields, unique values, regex patterns
6. Handle relationships: generate parent records before children, maintain referential integrity
7. Generate the specified number of records (default 10, max 10000)
8. Validate generated data against the schema constraints
9. Output data in the requested format: JSON, CSV, SQL INSERT statements, or fixture files
10. Save the generated data to the test/fixtures directory
11. Report: total records generated, format, file size, and any constraint warnings

## Rules

- Generate deterministic data using a seed value for reproducibility
- Respect unique constraints by tracking generated values
- Use locale-appropriate data when the project specifies a locale
- Handle nullable fields by including a mix of null and non-null values
- Generate edge cases: empty strings, max-length strings, boundary numbers
- Do not generate sensitive data patterns (real SSNs, credit card numbers)
- Include both valid and intentionally invalid records when requested
