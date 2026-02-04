Start a new feature, bugfix, or hotfix branch following git-flow conventions.

## Steps

1. Determine the flow type from the argument:
   - `feature/<name>` for new features (branches from `develop` or `main`).
   - `bugfix/<name>` for non-critical fixes (branches from `develop`).
   - `hotfix/<name>` for critical production fixes (branches from `main`).
2. Verify the working tree is clean: `git status --porcelain`.
3. Fetch latest from remote: `git fetch origin`.
4. Create the branch from the appropriate base:
   - `git checkout -b <type>/<name> origin/<base>`.
5. Set up branch tracking: `git push -u origin <type>/<name>`.
6. If a GitHub issue is referenced, link it:
   - Name the branch `<type>/<issue-number>-<description>`.
7. Display the branch info and next steps.

## Format

```
Flow started:
  Type: <feature|bugfix|hotfix>
  Branch: <branch-name>
  Base: <base-branch>
  Tracking: origin/<branch-name>

Next steps:
  1. Make your changes
  2. Commit with conventional messages
  3. Run: /git-flow:flow-release to merge
```

## Rules

- Always branch from a clean, up-to-date base branch.
- Use lowercase kebab-case for branch names.
- Include issue number in branch name when applicable.
- Hotfix branches must always branch from the production branch.
- Verify no branch with the same name already exists.
