Diagnose and fix failing tests in the project.

## Steps

1. Run the test suite and capture output: detect the test runner from project config.
2. Parse the failure output to extract:
   - Test name and file location.
   - Expected vs actual values.
   - Stack trace and error message.
3. For each failing test, determine the root cause category:
   - **Stale snapshot**: Output changed intentionally; update snapshot.
   - **Logic change**: Source code changed but test was not updated.
   - **Environment issue**: Missing env var, port conflict, timing issue.
   - **Flaky test**: Race condition, non-deterministic ordering.
   - **Dependency update**: Breaking change in a library.
4. Read the relevant source code and test code side by side.
5. Apply the fix:
   - Update assertions to match new behavior if the change was intentional.
   - Fix the source code if the test caught a real bug.
   - Add retry logic or increase timeouts for flaky tests.
   - Update mocks if dependency interfaces changed.
6. Re-run only the fixed tests to verify: `<runner> --testPathPattern <file>`.
7. Run the full suite to check for regressions.

## Format

```
Failing tests: <N>

| Test | File | Cause | Fix |
|------|------|-------|-----|
| test name | path | category | what was done |

Result: <N>/<N> now passing
```

## Rules

- Never delete a failing test without understanding why it fails.
- If a test failure reveals a real bug, fix the source code, not the test.
- Distinguish between intentional behavior changes and regressions.
- Run the full suite after fixes to catch cascading failures.
