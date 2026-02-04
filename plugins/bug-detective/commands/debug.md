Systematically debug an issue by analyzing symptoms, forming hypotheses, and testing them.

## Steps

1. Gather the bug report: error message, stack trace, reproduction steps, expected vs actual behavior.
2. Identify the entry point where the issue manifests (endpoint, UI action, CLI command).
3. Trace the execution path from entry to error:
   - Read the code path that handles the triggering action.
   - Check for recent changes in the affected files: `git log --oneline -10 -- <file>`.
   - Look for related error handling or edge cases.
4. Form hypotheses ranked by likelihood:
   - Data issue: unexpected null, wrong type, missing field.
   - Logic error: incorrect condition, off-by-one, wrong operator.
   - State issue: race condition, stale cache, missing initialization.
   - Environment: missing config, version mismatch, network failure.
5. Test each hypothesis:
   - Add targeted logging or breakpoints.
   - Write a minimal reproduction test case.
   - Check edge cases around the failure point.
6. Implement the fix and verify it resolves the issue.
7. Add a regression test that would catch the bug if reintroduced.

## Format

```
Bug: <description>
Root Cause: <what actually went wrong>
Fix: <what was changed>
Files: <list of modified files>
Test: <regression test added>
```

## Rules

- Start with the simplest hypothesis before investigating complex causes.
- Never fix a bug without understanding the root cause.
- Always add a regression test for the fix.
- Check if the same bug pattern exists elsewhere in the codebase.
