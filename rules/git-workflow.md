# Git Workflow

## Commit Messages
- Follow conventional commits: `type(scope): subject`.
- Types: feat, fix, refactor, docs, test, chore, perf, style, ci.
- Subject line: imperative mood, lowercase, no period, max 72 characters.
- Body: explain why, not what. Wrap at 80 characters.
- Reference issues: `Closes #123` or `Relates to #456`.

## Branching
- Create feature branches from main: `feature/short-description`.
- Use prefixes: `feature/`, `fix/`, `chore/`, `refactor/`, `docs/`.
- Keep branches short-lived. Merge within 1-3 days.
- Delete branches after merging.

## Pull Requests
- One logical change per PR. Do not bundle unrelated changes.
- Keep PRs under 400 lines of diff when possible.
- Write a description explaining the motivation, not just the changes.
- Include a test plan describing how to verify the change.
- Request review from at least one person.
- Address all review comments before merging.

## Merge Strategy
- Squash merge for feature branches (clean history).
- Merge commit for release branches (preserve history).
- Never force push to main or shared branches.
- Rebase feature branches on main before merging to resolve conflicts.

## Safety Rules
- Never commit secrets, credentials, or API keys.
- Never commit large binary files. Use Git LFS if needed.
- Never commit generated files (dist/, build/, node_modules/).
- Always review `git diff --cached` before committing.
- Run tests before pushing. If CI fails, fix before merging.

## Tags and Releases
- Use semantic versioning: MAJOR.MINOR.PATCH.
- Tag releases on main: `git tag -a v1.2.3 -m "Release 1.2.3"`.
- Write release notes summarizing changes since last release.
