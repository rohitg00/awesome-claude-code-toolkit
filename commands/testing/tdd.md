Start a TDD (Test-Driven Development) cycle for the requested feature or function.

## Process

### 1. Red Phase - Write a Failing Test
- Ask what behavior to implement if not specified.
- Identify the test framework in use (Jest, Vitest, pytest, Go testing).
- Write a single focused test that describes the desired behavior.
- Run the test to confirm it fails for the right reason.
- The test should fail because the feature does not exist yet, not because of a syntax error.

### 2. Green Phase - Make It Pass
- Write the minimum code necessary to make the test pass.
- Do not optimize or generalize yet. Just make it work.
- Run the test to confirm it passes.
- If it fails, fix the implementation, not the test.

### 3. Refactor Phase - Clean Up
- Look for duplication, unclear naming, or unnecessary complexity.
- Extract helper functions if logic is repeated.
- Improve variable and function names for clarity.
- Run the full test suite to verify nothing broke.

### 4. Repeat
- Ask what the next behavior to implement is.
- Start another Red-Green-Refactor cycle.

## Rules

- Each cycle targets exactly one behavior. Do not batch multiple behaviors.
- Tests must be independent and not depend on execution order.
- Use descriptive test names: `should <expected behavior> when <condition>`.
- Mock external dependencies (HTTP, database, filesystem) at boundaries.
- Keep each cycle under 5 minutes of implementation time.
- If a cycle takes longer, the scope is too large. Break it down.
