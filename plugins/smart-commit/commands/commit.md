# /smart-commit:commit

Analyze all staged git changes and generate an intelligent conventional commit message.

## Process

1. Run `git diff --cached --stat` to identify all staged files and their change magnitudes.
2. Run `git diff --cached` to read the full diff of staged changes.
3. Determine the primary commit type based on the nature of changes:
   - `feat` - New functionality, new files introducing features, new endpoints or UI components
   - `fix` - Bug corrections, error handling improvements, null checks, edge case fixes
   - `refactor` - Code restructuring without behavior change, renaming, extraction of functions
   - `docs` - Documentation-only changes, comments, README updates, docstrings
   - `test` - Adding or modifying tests, test fixtures, test utilities
   - `chore` - Build config, dependency updates, CI changes, tooling, linting rules
   - `perf` - Performance improvements, caching, query optimization, lazy loading
   - `style` - Formatting, whitespace, semicolons, code style (no logic change)
   - `ci` - CI/CD pipeline changes, workflow files, deployment configs

4. Derive the scope from the most affected directory or module:
   - Use the top-level directory name if changes span one area (e.g., `auth`, `api`, `ui`)
   - Use a broader scope if changes span multiple areas (e.g., `core`, `app`)
   - Omit scope if changes are truly cross-cutting or trivial

5. Write the commit subject line (max 72 characters):
   - Use imperative mood ("add" not "added", "fix" not "fixes")
   - Focus on WHY the change was made, not WHAT files changed
   - Be specific: "fix race condition in websocket reconnect" not "fix bug"
   - Do not end with a period

6. Determine if a body is needed (skip for obvious single-line changes):
   - Explain the motivation behind the change
   - Describe the approach taken and why alternatives were rejected
   - Keep each line under 80 characters

7. Add footers when applicable:
   - `BREAKING CHANGE: <description>` if the change breaks existing APIs or behavior
   - `Closes #<number>` if the change resolves a tracked issue
   - `Refs: <context>` for related PRs, issues, or discussions

8. Present the commit message for review, then execute `git commit` with the approved message.

## Output Format

```
type(scope): concise imperative description

Optional body explaining the motivation and approach.

Optional footers.
```

## Rules

- Never fabricate issue numbers or references
- If multiple types apply equally, prefer the one with the largest behavioral impact
- When in doubt between `feat` and `refactor`, ask: does the user-visible behavior change?
- Run `git log --oneline -10` first to match the repository's existing commit style
- If nothing is staged, inform the user and suggest what to stage
