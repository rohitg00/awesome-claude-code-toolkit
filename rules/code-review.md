# Code Review

## Review Checklist
- Does the code do what the PR description says? Read the diff against the stated goal.
- Are there adequate tests? New logic needs new tests. Changed logic needs updated tests.
- Are error cases handled? Check for missing try/catch, unhandled promise rejections, and null checks.
- Is input validated at the boundary? API inputs, form data, and CLI args must be validated.
- Are there security concerns? SQL injection, XSS, hardcoded secrets, excessive permissions.
- Is the code readable without comments? Variable names, function names, and structure should be self-documenting.
- Are there performance concerns? N+1 queries, unbounded loops, missing pagination, large payloads.
- Does it follow project conventions? Naming, file structure, import order, error handling patterns.

## Approval Criteria
- All CI checks must pass before review.
- At least one approval from a code owner for the changed area.
- Two approvals required for: database migrations, auth changes, payment logic, infrastructure changes.
- No unresolved comments. Author must respond to every comment (resolve or discuss).
- Diff must be under 400 lines. If larger, split into smaller PRs.

## Reviewer Guidelines
- Review within 4 business hours of being tagged.
- Start with the PR description and linked issue to understand context.
- Read the full diff before leaving comments. Avoid reviewing file-by-file without context.
- Prefix comments with intent: `nit:`, `question:`, `suggestion:`, `blocker:`.
- Only `blocker:` comments prevent approval. Everything else is optional for the author.
- Suggest specific alternatives when requesting changes, not just "this is wrong."

## Author Guidelines
- Write a clear PR description: what changed, why, how to test, and any risks.
- Self-review the diff before requesting reviews. Catch obvious issues yourself.
- Keep PRs focused on one concern. Do not mix refactoring with feature work.
- Add screenshots or recordings for UI changes.
- Link the related issue or ticket in the PR description.
- Respond to all review comments within one business day.

## Automated Checks
- Lint and format checks in CI (ESLint, Prettier, Ruff, Clippy).
- Type checking in CI (TypeScript, mypy, pyright).
- Test suite with minimum coverage thresholds.
- Bundle size check for frontend changes.
- Migration safety check (no locking operations on large tables).
