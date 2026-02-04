Analyze the currently staged changes (`git diff --cached`) and generate a conventional commit message.

## Steps

1. Run `git diff --cached --stat` to see which files changed.
2. Run `git diff --cached` to read the actual changes.
3. Determine the commit type from the changes:
   - `feat` - new functionality
   - `fix` - bug fix
   - `refactor` - code restructuring without behavior change
   - `docs` - documentation only
   - `test` - adding or updating tests
   - `chore` - build, CI, dependencies
   - `perf` - performance improvement
   - `style` - formatting, whitespace
4. Identify the scope from the most affected module/directory.
5. Write a concise imperative subject line (max 72 chars).
6. If the change is non-trivial, add a body explaining **why** the change was made, not what changed.
7. Present the commit message for approval before executing.

## Format

```
type(scope): subject line in imperative mood

Optional body explaining motivation and context.
Any breaking changes noted with BREAKING CHANGE: prefix.
```

## Rules

- Subject line: imperative mood, no period, max 72 characters.
- Body: wrap at 80 characters, blank line between subject and body.
- If multiple logical changes are staged, suggest splitting into separate commits.
- Never include generated files, lock files, or build artifacts without explicit intent.
