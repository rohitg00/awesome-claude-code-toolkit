Fix a GitHub issue by number: read the issue, create a branch, implement the fix, and open a PR.

## Steps

1. Fetch the issue details using `gh issue view <number> --json title,body,labels,assignees`.
2. Parse the issue body to understand the problem, expected behavior, and reproduction steps.
3. Create a feature branch: `git checkout -b fix/<number>-<slug>` where slug is derived from the title.
4. Analyze the codebase to locate relevant files mentioned in or related to the issue.
5. Implement the fix:
   - Make minimal, focused changes that address only the reported problem.
   - Add or update tests that cover the fixed behavior.
6. Run the project test suite to verify the fix does not introduce regressions.
7. Commit changes with `fix: <title> (closes #<number>)`.
8. Push the branch and create a PR: `gh pr create --title "Fix #<number>: <title>" --body "Closes #<number>"`.

## Format

```
Issue #<number>: <title>
Status: <Open/Closed>
Labels: <label1>, <label2>

Analysis:
- Root cause: <description>
- Files affected: <list>

Changes made:
- <file>: <what changed>

Tests: <pass/fail summary>
PR: <url>
```

## Rules

- Always read the full issue including comments before starting.
- Never modify files unrelated to the issue.
- If the issue is unclear or lacks reproduction steps, ask for clarification before proceeding.
- Reference the issue number in commit messages and PR description.
