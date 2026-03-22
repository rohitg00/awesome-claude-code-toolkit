Rebase the current feature branch onto the latest upstream branch and resolve conflicts.

## Steps


1. Verify the current branch and its upstream:
2. Fetch the latest changes from remote:
3. Check for potential conflicts before rebasing:
4. Start the rebase:
5. If conflicts occur:
6. After successful rebase:
7. Report the rebase result.

## Format


```
Branch: <branch name>
Base: <upstream branch>
Commits Rebased: <count>
Conflicts: <count resolved>
```


## Rules

- Always use `--force-with-lease` instead of `--force` for safety.
- Never rebase shared branches that others are working on.
- Run the full test suite after rebasing.

