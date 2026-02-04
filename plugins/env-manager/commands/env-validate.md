Validate environment configuration against the template and runtime requirements.

## Steps

1. Read `.env.example` to get the expected variable list.
2. Read `.env` (or the active environment) to get actual values.
3. Check for missing variables:
   - Required variables without values.
   - Variables in `.env.example` not present in `.env`.
4. Check for extra variables:
   - Variables in `.env` not documented in `.env.example`.
5. Validate variable formats:
   - URLs: Valid URL format with expected scheme.
   - Ports: Numeric, in valid range (1-65535).
   - Booleans: `true`/`false`, not `yes`/`no` or `1`/`0`.
   - Emails: Valid email format.
6. Check for common issues:
   - Trailing whitespace in values.
   - Unquoted values with special characters.
   - Duplicate variable definitions.
7. Verify connectivity for database URLs and API endpoints if `--live` flag is set.

## Format

```
Environment Validation: <environment>

Missing (required):
  - DATABASE_URL: No value set

Missing (optional):
  - LOG_LEVEL: Using default "info"

Format issues:
  - PORT: "abc" is not a valid port number

Extra (undocumented):
  - LEGACY_MODE: Not in .env.example

Status: <valid/invalid>
```

## Rules

- Fail on any missing required variable.
- Warn on undocumented variables (may be leftover from old code).
- Do not print actual secret values in validation output.
- Support multiple environment files (.env.development, .env.production).
- Exit with non-zero code if validation fails (for CI integration).
