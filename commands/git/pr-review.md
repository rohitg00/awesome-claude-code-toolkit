Review a pull request by number: fetch the diff, analyze changes, and post review comments.

## Steps

1. Fetch PR details: `gh pr view <number> --json title,body,files,additions,deletions,commits`.
2. Get the full diff: `gh pr diff <number>`.
3. Read the PR description and any linked issues for context.
4. Analyze each changed file across dimensions:
   - **Correctness**: Logic errors, edge cases, missing error handling.
   - **Security**: Input validation, credential exposure, injection risks.
   - **Performance**: N+1 queries, unnecessary allocations, missing caching.
   - **Design**: Coupling, naming, abstraction level, API surface.
   - **Tests**: Coverage of new code paths, edge case testing.
5. Check that CI checks are passing: `gh pr checks <number>`.
6. Classify findings as CRITICAL, WARNING, or SUGGESTION.
7. Present the review summary and offer to post it as a PR review comment.
8. If approved, submit: `gh pr review <number> --approve --body "<summary>"`.

## Format

```
## PR Review: #<number> - <title>

### Critical
- [ ] file.ts:L42 - Description of critical issue

### Warnings
- [ ] file.ts:L15 - Description of warning

### Suggestions
- [ ] file.ts:L88 - Description of suggestion

### Summary
Overall assessment and recommendation (approve/request-changes).
```

## Rules

- Review the full diff, not just the latest commit.
- Be specific with line references and provide concrete fix suggestions.
- Limit findings to the 15 most impactful to reduce noise.
- Acknowledge well-written code sections briefly.
- Never auto-approve PRs with critical findings.
