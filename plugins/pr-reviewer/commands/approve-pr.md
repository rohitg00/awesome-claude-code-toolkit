Approve a pull request after verifying it meets quality standards.

## Steps

1. Fetch PR details and verify it has been reviewed: `gh pr view <number>`.
2. Run the approval checklist:
   - [ ] PR description is clear and explains the motivation.
   - [ ] All CI checks are passing: `gh pr checks <number>`.
   - [ ] Tests are included for new functionality.
   - [ ] No secrets or credentials in the diff.
   - [ ] No critical code review findings unresolved.
   - [ ] Branch is up to date with base.
3. If all checks pass, submit approval:
   - `gh pr review <number> --approve --body "<summary>"`.
4. If checks fail, report which items need attention.
5. Optionally enable auto-merge if configured:
   - `gh pr merge <number> --auto --squash`.

## Format

```
PR #<number>: <title>

Checklist:
  [x] Description clear
  [x] CI passing
  [x] Tests included
  [x] No secrets
  [x] No critical issues
  [x] Branch up to date

Status: Approved
Review comment: <summary of assessment>
```

## Rules

- Never approve without reviewing the full diff.
- Verify CI checks are passing at the time of approval.
- If the PR has outstanding review comments, ensure they are resolved.
- Add a brief summary of what was reviewed in the approval comment.
- Do not approve PRs that increase test failures or reduce coverage significantly.
