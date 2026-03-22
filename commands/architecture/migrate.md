Plan and execute a framework or library migration incrementally.

## Steps

### 1. Dependency Audit
- List the current version and target version.
- Read the migration guide or changelog for the target version.
- Run `npm outdated`, `pip list --outdated`, or equivalent to see the full dependency picture.
- Identify transitive dependencies that may also need updating.

### 2. Breaking Changes Analysis
- List every breaking change between current and target versions.
- For each breaking change, search the codebase for affected code:
  - Deprecated APIs that are removed.
  - Changed function signatures or return types.
  - Renamed or moved modules.
  - Changed default behavior.
- Categorize each as: trivial (find-and-replace), moderate (logic change), complex (architecture change).

### 3. Migration Plan
- Order changes to minimize risk:
  1. Update configuration and build tooling first.
  2. Address breaking changes in shared utilities and core modules.
  3. Update feature code from least to most complex.
  4. Update tests last (they may need new patterns).
- Identify code that can be made compatible with both old and new versions during transition.
- Plan for a parallel-run period if the migration spans multiple PRs.

### 4. Execute Incrementally
- Create a feature branch for the migration.
- Apply changes one module at a time.
- Run tests after each module migration.
- Keep the build passing at every commit.

### 5. Verify
- Run the full test suite with the new version.
- Test critical user flows manually or with e2e tests.
- Check bundle size, build time, and runtime performance for regressions.
- Document any behavioral differences that are intentional.

## Rules

- Never do a big-bang migration. Each PR should be reviewable independently.
- If a dependency has its own migration tool (codemods), use it first.
- Pin the exact target version during migration. Do not use ranges.
- Keep a rollback plan: know how to revert to the old version at every step.
- Update lock files in a dedicated commit for cleaner diffs.
