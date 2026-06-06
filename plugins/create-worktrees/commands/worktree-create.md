Create a git worktree for parallel development on a separate branch without stashing.

## Steps


1. Verify the current repository supports worktrees:
2. Determine the worktree configuration:
3. Create the worktree:
4. Set up the worktree environment:
5. List active worktrees with `git worktree list`.
6. Provide the path and instructions to switch to the new worktree.

## Format


```
Worktree Created:
  Path: <absolute path>
  Branch: <branch name>
  Base: <parent branch>
```


## Rules

- Always create worktrees outside the main repository directory.
- Use descriptive branch names following project conventions.
- Do not copy .env files with secrets to worktrees.

