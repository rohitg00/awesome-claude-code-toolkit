Migrate code from one framework version, library, or pattern to another.

## Steps

1. Identify the migration scope:
   - Framework upgrade (React 17 to 18, Next.js 13 to 14, Django 4 to 5).
   - Library replacement (Moment to Day.js, Express to Fastify).
   - Pattern change (class components to hooks, callbacks to async/await).
2. Research breaking changes and migration guides for the target version.
3. Scan the codebase for affected patterns:
   - Deprecated API usage.
   - Changed import paths.
   - Removed features needing alternatives.
4. Generate a migration plan with ordered steps.
5. Apply changes file by file:
   - Update imports and require statements.
   - Refactor deprecated patterns to new equivalents.
   - Update configuration files.
   - Update type definitions if applicable.
6. Update `package.json` or equivalent with new versions.
7. Run tests after each major change to catch regressions early.

## Format

```
Migration: <from> -> <to>
Files affected: <N>

Changes:
  - <pattern>: <N> occurrences updated
  - <import>: <N> files updated

Breaking changes handled:
  - <change>: <how it was resolved>

Verification: tests <pass/fail>
```

## Rules

- Apply changes incrementally, not all at once.
- Run tests after each change category to isolate regressions.
- Keep a log of all changes for review.
- Do not upgrade transitive dependencies without testing compatibility.
- Preserve existing functionality; migration should be behavior-preserving.
