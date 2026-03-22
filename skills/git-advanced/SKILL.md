---
name: git-advanced
description: Advanced git workflows including worktrees, bisect, interactive rebase, hooks, and recovery techniques
---

# Git Advanced

## Worktrees

```bash
# Create a worktree for a feature branch (avoids stashing)
git worktree add ../feature-auth feature/auth

# Create a worktree with a new branch
git worktree add ../hotfix-123 -b hotfix/123 origin/main

# List all worktrees
git worktree list

# Remove a worktree after merging
git worktree remove ../feature-auth
```

Worktrees let you work on multiple branches simultaneously without stashing or committing WIP. Each worktree has its own working directory but shares the same `.git` repository.

## Bisect

```bash
# Start bisect, mark current as bad and known good commit
git bisect start
git bisect bad HEAD
git bisect good v1.5.0

# Git checks out a midpoint commit. Test it, then mark:
git bisect good   # if this commit works
git bisect bad    # if this commit is broken

# Automate with a test script
git bisect start HEAD v1.5.0
git bisect run npm test

# When done, reset
git bisect reset
```

Bisect performs binary search across commits to find which commit introduced a bug. Automated bisect with `run` is the fastest approach.

## Interactive Rebase

```bash
# Rebase last 5 commits interactively
git rebase -i HEAD~5

# Common operations in the editor:
# pick   - keep commit as-is
# reword - change commit message
# edit   - stop to amend the commit
# squash - merge into previous commit, keep both messages
# fixup  - merge into previous commit, discard this message
# drop   - remove the commit entirely

# Rebase feature branch onto latest main
git fetch origin
git rebase origin/main

# Continue after resolving conflicts
git rebase --continue

# Abort if things go wrong
git rebase --abort
```

## Git Hooks

```bash
#!/bin/sh
# .git/hooks/pre-commit

# Run linter on staged files only
STAGED_FILES=$(git diff --cached --name-only --diff-filter=d | grep -E '\.(ts|tsx|js|jsx)$')
if [ -n "$STAGED_FILES" ]; then
  npx eslint $STAGED_FILES --fix
  git add $STAGED_FILES
fi
```

```bash
#!/bin/sh
# .git/hooks/commit-msg

# Enforce conventional commit format
COMMIT_MSG=$(cat "$1")
PATTERN="^(feat|fix|docs|style|refactor|test|chore)(\(.+\))?: .{1,72}$"

if ! echo "$COMMIT_MSG" | head -1 | grep -qE "$PATTERN"; then
  echo "Error: Commit message must follow Conventional Commits format"
  echo "Example: feat(auth): add OAuth2 login flow"
  exit 1
fi
```

```bash
#!/bin/sh
# .git/hooks/pre-push

# Run tests before pushing
npm test
if [ $? -ne 0 ]; then
  echo "Tests failed. Push aborted."
  exit 1
fi
```

## Recovery Techniques

```bash
# Undo last commit but keep changes staged
git reset --soft HEAD~1

# Recover a deleted branch using reflog
git reflog
git checkout -b recovered-branch HEAD@{3}

# Recover a file from a specific commit
git checkout abc1234 -- path/to/file.ts

# Find lost commits (dangling after reset or rebase)
git fsck --lost-found
git show <dangling-commit-sha>

# Undo a rebase
git reflog
git reset --hard HEAD@{5}  # point before rebase started
```

## Useful Aliases

```bash
# ~/.gitconfig
[alias]
  lg = log --graph --oneline --decorate --all
  st = status -sb
  co = checkout
  unstage = reset HEAD --
  last = log -1 HEAD --stat
  branches = branch -a --sort=-committerdate
  stash-all = stash push --include-untracked
  conflicts = diff --name-only --diff-filter=U
```

## Anti-Patterns

- Force-pushing to shared branches without `--force-with-lease`
- Rebasing commits that have already been pushed and shared
- Committing large binary files without Git LFS
- Using `git add .` without reviewing `git diff --staged`
- Not using `.gitignore` for build artifacts, dependencies, and secrets
- Keeping long-lived feature branches instead of merging frequently

## Checklist

- [ ] Worktrees used for parallel branch work instead of stashing
- [ ] `git bisect run` automates bug-finding with a test command
- [ ] Interactive rebase cleans up commits before merging to main
- [ ] Pre-commit hooks run linting on staged files
- [ ] Commit message format enforced via commit-msg hook
- [ ] `--force-with-lease` used instead of `--force` when force-pushing
- [ ] Reflog consulted before any destructive operation
- [ ] `.gitignore` covers build outputs, dependencies, and environment files
