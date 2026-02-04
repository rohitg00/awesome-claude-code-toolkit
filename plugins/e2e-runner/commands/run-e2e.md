# /run-e2e - Execute End-to-End Tests

Run end-to-end tests against the application using Playwright or Cypress.

## Steps

1. Detect the e2e framework in use (Playwright, Cypress, or Selenium) by checking package.json and config files
2. Verify the test configuration file exists (playwright.config.ts, cypress.config.js, etc.)
3. Check if the application server is running; if not, identify the start command
4. List all e2e test files matching the pattern `**/*.e2e.{ts,js}` or `**/*.spec.{ts,js}` in the e2e/test directory
5. If a specific test file or pattern is provided, filter to those tests only
6. Run the test suite with verbose output and capture results
7. Parse test output for pass/fail counts and timing information
8. For any failing tests, extract the error message, screenshot path, and stack trace
9. Present a summary table: total tests, passed, failed, skipped, duration
10. If failures exist, suggest fixes based on error patterns (timeout, selector, assertion)

## Rules

- Always run tests in headless mode unless the user explicitly requests headed mode
- Set a default timeout of 30 seconds per test unless configured otherwise
- Capture screenshots on failure automatically
- Do not modify test files without explicit permission
- Report flaky tests if a test passes on retry but failed initially
- Ensure the base URL matches the running application port
- Clean up any test artifacts older than 7 days
