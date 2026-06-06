# /record-test - Record New E2E Test

Record user interactions to generate an end-to-end test file.

## Steps

1. Ask the user for the test name and the user flow to record (e.g., "login flow", "checkout process")
2. Determine the e2e framework in use from the project configuration
3. Identify the base URL and starting page for the recording session
4. For Playwright: use `npx playwright codegen` with the target URL
5. For Cypress: set up Cypress Studio or guide manual recording
6. Capture the generated test code from the recording session
7. Clean up the recorded code: add proper assertions, remove redundant waits
8. Add descriptive test names and group related interactions into logical steps
9. Add page object references if the project uses the Page Object Model pattern
10. Save the test file to the appropriate directory with the correct naming convention
11. Run the newly created test to verify it passes
12. Report the result and suggest additional assertions to strengthen the test

## Rules

- Follow the project's existing test naming conventions
- Use data-testid selectors over CSS selectors when available
- Add at least one assertion per user interaction step
- Include setup and teardown hooks if the test requires authentication
- Do not hardcode test data; use fixtures or environment variables
- Keep recorded tests under 50 lines; split longer flows into separate tests
