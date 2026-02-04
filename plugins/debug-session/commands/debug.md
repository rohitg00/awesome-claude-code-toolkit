Start an interactive debugging session to diagnose and fix a runtime issue.

## Steps


1. Gather the error information:
2. Reproduce the issue:
3. Narrow down the failure point:
4. Examine the root cause:
5. Implement the fix with minimal changes.
6. Verify the fix resolves the issue.
7. Add a test that reproduces the original bug.
8. Remove any temporary logging added during debugging.

## Format


```
Issue: <description>
Reproduction: <steps>
Root Cause: <what went wrong>
Fix Applied: <changes made>
```


## Rules

- Always reproduce before attempting to fix.
- Remove all debug logging before committing.
- Fix the root cause, not just the symptom.

