Create a pull request with a structured description based on the current branch's changes.

## Steps

1. Run `git log main..HEAD --oneline` to see all commits on this branch.
2. Run `git diff main...HEAD --stat` to see all changed files.
3. Run `git diff main...HEAD` to read the actual changes.
4. Determine the base branch (main or master).
5. Generate a PR title (max 70 chars) summarizing the change.
6. Generate a structured PR body.
7. Create the PR using `gh pr create`.

## PR Body Template

```markdown
## Summary
- Bullet point summary of the change and its motivation.

## Changes
- List of significant changes grouped by area.

## Test Plan
- [ ] How to verify this change works correctly.
- [ ] Edge cases considered.

## Notes
- Any migration steps, config changes, or deployment considerations.
```

## Rules

- Keep the title short and descriptive. Use imperative mood.
- The summary should explain **why** this change exists, not just what it does.
- Link related issues with `Closes #N` or `Relates to #N`.
- If there are visual changes, note where screenshots should be added.
- Always push the branch before creating the PR.
