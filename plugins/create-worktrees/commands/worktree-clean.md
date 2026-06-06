Clean up finished git worktrees by removing directories and pruning references.

## Steps


1. List all active worktrees with `git worktree list`.
2. For each worktree, check its status:
3. Identify worktrees safe to remove:
4. For each worktree to clean:
5. Prune stale worktree references: `git worktree prune`.
6. Report what was cleaned and what was kept.

## Format


```
Worktree Cleanup Report:
  Removed:
    - <path> (branch: <name>, reason: merged)
  Kept:
```


## Rules

- Never remove a worktree with uncommitted changes without user confirmation.
- Always check if the branch is merged before deleting it.
- Use `git branch -d` (not -D) to prevent deleting unmerged branches.

