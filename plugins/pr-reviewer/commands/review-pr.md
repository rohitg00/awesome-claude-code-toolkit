Perform a thorough code review of a pull request with actionable feedback.

## Steps

1. Fetch PR metadata: `gh pr view <number> --json title,body,files,additions,deletions,labels`.
2. Read linked issues to understand the motivation for changes.
3. Fetch the full diff: `gh pr diff <number>`.
4. Review each file across quality dimensions:
   - **Correctness**: Logic errors, missing edge cases, race conditions.
   - **Security**: Input validation, auth checks, secret exposure.
   - **Performance**: Query patterns, caching, resource management.
   - **Maintainability**: Naming, complexity, documentation.
   - **Testing**: Coverage of new code paths, edge case tests.
5. Verify:
   - PR description explains what and why.
   - Changes are focused on the stated goal (no scope creep).
   - Tests are included for new functionality.
   - No unintended files (build artifacts, config changes).
6. Rate each finding by severity (critical, warning, suggestion).
7. Compile the review with specific line references and fix suggestions.
8. Offer to post the review as a GitHub PR comment.

## Format

```
## PR Review: #<number> - <title>

**Verdict**: Approve / Request Changes / Comment

### Findings
| Severity | File | Line | Issue |
|----------|------|------|-------|
| CRITICAL | src/auth.ts | 42 | SQL injection via unescaped input |
| WARNING | src/api.ts | 88 | Missing pagination on list endpoint |

### Summary
<overall assessment>

### What's Good
- <positive observation>
```

## Rules

- Review all commits in the PR, not just the latest.
- Be specific: include file, line, and a concrete fix suggestion.
- Limit to 15 findings maximum; prioritize by impact.
- Request changes only for critical issues; approve with suggestions otherwise.
- Never approve a PR with known security vulnerabilities.
