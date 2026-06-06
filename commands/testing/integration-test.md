Generate integration tests for a module, testing real interactions between components.

## Steps

1. Identify the target module or file from the argument or current context.
2. Analyze imports and dependencies to determine what external systems are involved (database, API, filesystem, message queue).
3. Detect the test framework in use (Jest, Vitest, pytest, Go testing, etc.) from project config.
4. For each public function or endpoint in the module:
   - Write a test that exercises the real integration path.
   - Set up required test fixtures (seed data, mock servers, temp files).
   - Test the happy path with realistic input data.
   - Test at least one error/failure scenario per integration point.
   - Add proper teardown to clean up test state.
5. Group tests logically using `describe`/`context` blocks.
6. Add setup and teardown hooks (`beforeAll`/`afterAll`) for shared resources.
7. Run the generated tests to verify they pass.

## Format

```
Generated: <N> integration tests in <file>

Tests:
  - <TestName>: <what it verifies>
  - <TestName>: <what it verifies>

Coverage: <modules/functions covered>
```

## Rules

- Integration tests must use real dependencies where possible; mock only external services.
- Each test must be independent and not rely on execution order.
- Use realistic test data, not trivial values like "test" or "foo".
- Include timeout configuration for async operations.
- Name test files with `.integration.test` or `_integration_test` suffix.
