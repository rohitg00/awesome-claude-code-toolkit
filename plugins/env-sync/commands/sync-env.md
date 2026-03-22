# /sync-env - Sync Environment Variables

Synchronize environment variables across development, staging, and production.

## Steps

1. Read the current .env file and .env.example for the project
2. Identify all environment variables used in the codebase (process.env, os.environ)
3. Compare variables across environments: development, staging, production
4. Identify missing variables in each environment
5. Identify variables present in code but missing from all .env files
6. Detect variables in .env files that are no longer used in code
7. Verify variable naming conventions are consistent (UPPER_SNAKE_CASE)
8. Check for sensitive variables that should use secrets management
9. Generate an updated .env.example with all required variables and descriptions
10. Sync missing variables to target environments (with placeholder values for secrets)
11. Report: variables added, removed, mismatched across environments
12. Update documentation with the current environment variable inventory

## Rules

- Never copy secret values between environments; use placeholders
- Always update .env.example when adding new variables
- Do not commit .env files to version control; verify .gitignore includes them
- Flag variables with default values that look like real credentials
- Group related variables together in .env files (database, API keys, feature flags)
- Validate variable values against expected formats (URLs, numbers, booleans)
- Include comments in .env.example explaining each variable's purpose
