Set up git worktrees for parallel development on multiple branches simultaneously.

## Steps

1. Verify the current repository is not a bare clone: `git rev-parse --is-bare-repository`.
2. List existing worktrees with `git worktree list` and display them.
3. If creating a new worktree:
   - Accept a branch name argument (required) and optional base branch (defaults to `main`).
   - Determine the worktree path: `../<repo-name>-<branch-name>`.
   - Create it: `git worktree add ../<repo-name>-<branch> -b <branch> <base>`.
4. Copy essential config files that are gitignored (`.env`, `.env.local`) if they exist.
5. Run the package manager install in the new worktree directory.
6. Print the worktree path and instructions for switching to it.
7. If removing a worktree, run `git worktree remove <path>` and `git worktree prune`.

## Format

```
Worktree created:
  Path:   /absolute/path/to/worktree
  Branch: feature/my-branch
  Base:   main

Next: cd /absolute/path/to/worktree
```

## Rules

- Never create a worktree inside the current repository directory.
- Always check that the branch name does not already exist before creating.
- Warn if there are more than 5 active worktrees (potential cleanup needed).
- Do not delete worktrees that have uncommitted changes without confirmation.
