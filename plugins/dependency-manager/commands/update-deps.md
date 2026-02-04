Safely update project dependencies with compatibility verification.

## Steps

1. List all outdated dependencies: `npm outdated`, `pip list --outdated`.
2. Categorize updates by risk:
   - **Patch**: Bug fixes, safe to auto-update.
   - **Minor**: New features, backward compatible.
   - **Major**: Breaking changes, requires review.
3. For each update candidate:
   - Read the changelog for breaking changes.
   - Check peer dependency compatibility.
   - Verify TypeScript type compatibility if applicable.
4. Apply updates in order: patch first, then minor, then major.
5. After each batch, run the test suite.
6. If tests fail, identify the breaking dependency and provide fix guidance.
7. Update lock file and commit changes.

## Format

```
Dependency Updates Applied:

Patch (safe):
  - <pkg> 1.0.0 -> 1.0.1

Minor (compatible):
  - <pkg> 1.0.0 -> 1.1.0

Major (breaking - review required):
  - <pkg> 1.0.0 -> 2.0.0: <breaking change summary>

Tests: <pass/fail after updates>
```

## Rules

- Never update major versions without reading the changelog first.
- Run tests after each update category, not just at the end.
- Commit patch and minor updates separately from major updates.
- Do not update dev dependencies and production dependencies in the same batch.
- Keep a rollback plan: note the exact versions before updating.
