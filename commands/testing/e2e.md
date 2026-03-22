Generate end-to-end tests using Playwright for critical user flows.

## Steps

### 1. Identify Critical Flows
- Ask which user flow to test if not specified.
- Common critical flows:
  - Authentication (sign up, log in, log out, password reset)
  - Core CRUD operations (create, read, update, delete)
  - Payment/checkout flows
  - Search and filtering
  - Navigation between key pages

### 2. Set Up Test Structure
```typescript
import { test, expect } from "@playwright/test";

test.describe("Feature Name", () => {
  test.beforeEach(async ({ page }) => {
    // Navigate to starting point
    // Set up required auth state if needed
  });

  test("should complete the happy path", async ({ page }) => {
    // Steps matching real user behavior
  });

  test("should handle error state gracefully", async ({ page }) => {
    // Verify error messages, recovery options
  });
});
```

### 3. Write Tests Following Best Practices
- Use user-visible selectors: `getByRole`, `getByText`, `getByLabel`.
- Avoid CSS selectors and XPaths unless absolutely necessary.
- Add `data-testid` attributes only when semantic selectors are insufficient.
- Wait for network requests to complete before asserting: `page.waitForResponse`.
- Use `test.step` to document multi-step flows for readable reports.

### 4. Handle Test Data
- Use API calls in `beforeEach` to set up test data (faster than UI).
- Clean up test data in `afterEach` or use isolated test databases.
- Never depend on data created by other tests.

### 5. Run and Verify
- Run with `npx playwright test --headed` to watch execution.
- Verify tests pass in headless mode for CI.
- Check that tests are not flaky by running 3 times.

## Rules

- Test user-visible behavior, not implementation details.
- Each test should be independent and runnable in isolation.
- Keep tests under 30 seconds each.
- Use Playwright's auto-waiting instead of manual `page.waitForTimeout`.
- Configure retries in CI but fix flaky tests rather than relying on retries.
- Take screenshots on failure for debugging: `use: { screenshot: "only-on-failure" }`.
