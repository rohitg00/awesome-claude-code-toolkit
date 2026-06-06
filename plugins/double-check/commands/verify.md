Perform a systematic second-pass verification of code changes to catch errors before commit.

## Steps


1. Identify all files changed in the current working tree using `git diff --name-only`.
2. For each changed file, perform these checks:
3. Check for common mistakes:
4. Verify logic correctness:
5. Check for security issues:
6. Summarize findings with severity ratings.

## Format


```
File: <filename>
Issues Found: <count>
- [CRITICAL] <description>
- [WARNING] <description>
```


## Rules

- Review every changed file, not just the ones that seem important.
- Flag issues by severity: CRITICAL (must fix), WARNING (should fix), INFO (consider).
- Never approve code with CRITICAL issues.

