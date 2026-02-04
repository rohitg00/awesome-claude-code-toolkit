# /diff-env - Diff Environment Variables

Compare environment variables between two environments.

## Steps

1. Ask the user for the two environments to compare (e.g., dev vs staging)
2. Load environment variables from both sources (.env files, vault, cloud config)
3. Create a unified list of all variables across both environments
4. Categorize each variable: present in both, only in source, only in target
5. For variables present in both, compare values (without showing secret values)
6. Identify value mismatches: different URLs, ports, feature flags
7. Flag variables that are empty or have placeholder values
8. Check for variables that should differ (DATABASE_URL) vs should match (API_VERSION)
9. Generate a diff table: variable name, source value, target value, status
10. Highlight security concerns: secrets in plaintext, default credentials
11. Suggest which missing variables need to be added to which environment
12. Save the diff report for reference

## Rules

- Never display the actual values of secret variables (mask with ****)
- Identify secrets by naming patterns: *_KEY, *_SECRET, *_PASSWORD, *_TOKEN
- Show whether values match without revealing the actual values for sensitive vars
- Flag environment-specific variables that accidentally have the same value
- Detect URL differences that indicate wrong environment configuration
- Report variables that exist in code but are missing from both environments
- Include the diff timestamp and environments compared in the report
