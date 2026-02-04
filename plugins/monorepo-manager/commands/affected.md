Detect which packages in a monorepo are affected by recent changes.

## Steps

1. Detect the monorepo tool in use (Turborepo, Nx, Lerna, pnpm workspaces, Cargo workspace).
2. Get the list of changed files since the comparison point:
   - Default: `git diff --name-only origin/main...HEAD`.
   - Or since a specific commit/tag if provided.
3. Map changed files to packages:
   - Read workspace configuration to map directories to packages.
   - For each changed file, determine which package it belongs to.
4. Build the dependency graph:
   - Parse `package.json` (or equivalent) for each package.
   - Map inter-package dependencies.
5. Calculate the full affected set:
   - Direct: packages with changed files.
   - Transitive: packages that depend on directly affected packages.
6. Determine which tasks need to run:
   - Build: affected packages and their dependents.
   - Test: affected packages.
   - Lint: only directly changed packages.
7. Output the affected package list with recommended actions.

## Format

```
Affected Packages (since <comparison>)

Changed files: <N>

Directly affected:
  - @scope/pkg-a (3 files changed)
  - @scope/pkg-b (1 file changed)

Transitively affected:
  - @scope/pkg-c (depends on pkg-a)

Recommended:
  build: @scope/pkg-a @scope/pkg-b @scope/pkg-c
  test:  @scope/pkg-a @scope/pkg-b
  lint:  @scope/pkg-a @scope/pkg-b
```

## Rules

- Always include transitive dependents in the build affected set.
- Changes to shared config files (tsconfig, eslint) affect all packages.
- Changes to root `package.json` or lock files affect all packages.
- Use the native monorepo tool's affected detection if available.
- Support filtering by task type (build, test, lint, deploy).
