Add inline documentation (JSDoc, docstrings, comments) to under-documented code.

## Steps

1. Read the target file and assess current documentation level.
2. Identify what needs documentation:
   - Public functions and methods lacking doc comments.
   - Complex logic blocks without explanatory comments.
   - Non-obvious parameter types or return values.
   - Module-level overview missing.
3. Generate documentation in the appropriate format:
   - TypeScript/JavaScript: JSDoc with `@param`, `@returns`, `@throws`, `@example`.
   - Python: Google-style or NumPy-style docstrings.
   - Go: Godoc comments above exported functions.
   - Rust: `///` doc comments with examples.
4. For each function, document:
   - What it does (one-sentence summary).
   - Parameters with types and descriptions.
   - Return value description.
   - Thrown exceptions or error conditions.
   - Usage example for complex functions.
5. Add a module-level doc comment explaining the file's purpose.
6. Verify the documentation does not break the build or linter.

## Format

```typescript
/**
 * Creates a new user account with the given credentials.
 *
 * @param email - The user's email address (must be unique)
 * @param password - Plain text password (will be hashed)
 * @returns The created user object with generated ID
 * @throws {ConflictError} If a user with this email already exists
 * @example
 * const user = await createUser("alice@example.com", "securePass123");
 */
```

## Rules

- Document intent and contracts, not implementation details.
- Every public function must have at minimum a summary and parameter descriptions.
- Do not add comments that merely restate the code.
- Use the project's existing documentation style if one is established.
- Include `@example` for functions with non-obvious usage patterns.
