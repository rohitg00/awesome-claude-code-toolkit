Generate unit tests for a module, covering all public functions and edge cases.

## Steps

1. Read the target file and identify all exported functions, classes, and methods.
2. Detect the testing framework from project configuration.
3. For each public function:
   - Analyze parameters, return types, and side effects.
   - Generate tests for the happy path with typical inputs.
   - Generate tests for edge cases: empty inputs, null/undefined, boundary values.
   - Generate tests for error conditions: invalid inputs, thrown exceptions.
   - Mock external dependencies (database, API calls, filesystem).
4. For classes, test:
   - Constructor with valid and invalid arguments.
   - Each public method independently.
   - State transitions and method interactions.
5. Use descriptive test names following the pattern: "should <expected behavior> when <condition>".
6. Run the tests to verify they pass.

## Format

```
Generated: <N> unit tests in <file>
Coverage: <functions covered>/<total functions>

Tests:
  - <function>: <N> tests (happy path, edge cases, errors)
```

## Rules

- Test behavior, not implementation details.
- Each test should have exactly one assertion focus (single reason to fail).
- Use realistic test data, not trivial values.
- Mock at module boundaries, not internal functions.
- Keep tests independent; no shared mutable state between tests.
