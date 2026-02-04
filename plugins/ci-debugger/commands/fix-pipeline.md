# /fix-pipeline - Fix CI/CD Pipeline

Apply fixes to a broken CI/CD pipeline configuration.

## Steps

1. Read the CI/CD configuration file (.github/workflows/*.yml, .gitlab-ci.yml, etc.)
2. Identify the failing step and its configuration
3. Determine the fix based on the failure analysis
4. For dependency issues: update versions, add caching, fix lock files
5. For test failures: increase timeouts, add retry logic, fix test environment
6. For Docker issues: fix Dockerfile, update base images, fix build context
7. For credential issues: verify secret names, check expiration, update references
8. Apply the configuration fix to the pipeline file
9. Add or update caching configuration to speed up future builds
10. Add failure notification steps if not already present
11. Run a dry-run or validation of the pipeline config if the platform supports it
12. Commit the fix and report what was changed and why

## Rules

- Make minimal changes to fix the issue; do not refactor the entire pipeline
- Always validate the pipeline config syntax before committing
- Add comments explaining non-obvious configuration choices
- Do not change test expectations to make them pass; fix the underlying issue
- Preserve existing caching strategies unless they are causing the failure
- Keep pipeline execution time in mind; do not add expensive steps unnecessarily
- Test the fix on a feature branch before merging to main
