Generate comprehensive unit tests for a specified function, class, or module.

## Steps


1. Read the target function or module to understand its behavior:
2. Identify test cases by category:
3. Identify dependencies that need mocking:
4. Write tests using the project's testing framework:
5. Add setup and teardown for shared test state.
6. Run the tests to verify they pass.
7. Check coverage: does the new test cover all branches?

## Format


```
Target: <function/class name>
Tests Generated: <count>
Coverage: <lines/branches covered>
Framework: <jest|pytest|cargo test|etc>
```


## Rules

- Follow the existing test conventions in the project.
- Test behavior, not implementation details.
- Mock external dependencies, never make real network calls.

