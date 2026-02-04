# Debug Context

You are diagnosing and fixing a bug. Be systematic and methodical.

## Approach
- Reproduce the issue first. Confirm you can trigger the bug consistently.
- Gather information: error messages, stack traces, logs, request/response data.
- Form a hypothesis before changing code. Identify the most likely root cause.
- Verify the hypothesis with logging, breakpoints, or targeted tests.
- Fix the root cause, not the symptom. Avoid band-aid patches.

## Diagnostic Steps
1. Read the error message and stack trace carefully. Identify the failing line.
2. Check recent changes: `git log --oneline -10` and `git diff HEAD~3`.
3. Search the codebase for related logic using grep or find.
4. Add targeted logging at the boundaries (input, output, error paths).
5. Simplify the reproduction case to the minimum triggering inputs.
6. Check external dependencies: database state, API responses, config values.

## Fix Validation
- Write a failing test that reproduces the bug before writing the fix.
- Verify the fix resolves the original reproduction case.
- Run the full test suite to check for regressions.
- Check related code paths for the same class of bug.
- Document the root cause in the commit message.

## Avoid
- Do not change multiple things at once. Isolate variables.
- Do not add workarounds without understanding the root cause.
- Do not remove error handling to make tests pass.
- Do not assume the bug is in a dependency without evidence.
- Do not skip writing a regression test for the fixed bug.
