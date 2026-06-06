# Development Context

You are in active development mode. Prioritize speed and iteration.

## Behavior
- Write working code first, optimize later.
- Run tests after each meaningful change to catch regressions early.
- Use the dev server and hot reload. Do not rebuild from scratch for small changes.
- Create feature branches for all work. Commit frequently with descriptive messages.
- Use TODO comments sparingly and only for follow-up items within the current session.

## Coding
- Follow existing patterns in the codebase. Match the style of surrounding code.
- Add type annotations to all new functions and variables.
- Write unit tests alongside the implementation, not as an afterthought.
- Handle error cases explicitly. Do not leave empty catch blocks.
- Prefer small, focused functions over long procedural blocks.

## Tools
- Start the dev server before making UI changes to verify visually.
- Use the database client to inspect data when debugging queries.
- Check `git diff` before committing to review your own changes.
- Run the linter before pushing to avoid CI failures.

## Avoid
- Do not refactor unrelated code while building a feature.
- Do not add dependencies without checking for existing alternatives in the project.
- Do not skip tests to save time. Broken tests compound quickly.
- Do not push directly to main. Always use a feature branch and PR.
