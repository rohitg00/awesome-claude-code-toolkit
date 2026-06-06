Synchronize package versions across a monorepo for consistent releases.

## Steps

1. Read all package manifests in the monorepo workspace.
2. Analyze current version state:
   - List each package and its current version.
   - Check for version mismatches in inter-package dependencies.
   - Identify packages with unreleased changes since last version bump.
3. Determine the versioning strategy:
   - **Fixed**: All packages share the same version (e.g., Angular).
   - **Independent**: Each package versions independently (e.g., Babel).
   - **Grouped**: Packages in groups share versions.
4. For each package with changes, determine version bump:
   - Parse commit messages since last release for that package.
   - Apply semver rules: breaking=major, feature=minor, fix=patch.
5. Update versions:
   - Bump package version in its manifest.
   - Update inter-package dependency versions to match.
   - Update lock file.
6. Generate changelog entries for each bumped package.
7. Commit version bumps and tags.

## Format

```
Version Sync: <strategy>

| Package | Current | New | Changes | Bump |
|---------|---------|-----|---------|------|
| @scope/core | 1.2.0 | 1.3.0 | 5 commits | minor |
| @scope/cli | 1.2.0 | 1.2.1 | 2 commits | patch |
| @scope/ui | 1.2.0 | 1.2.0 | 0 commits | none |

Dependency updates:
  - @scope/cli: @scope/core ^1.2.0 -> ^1.3.0

Commands:
  git tag @scope/core@1.3.0
  git tag @scope/cli@1.2.1
```

## Rules

- Never publish packages with mismatched inter-package dependency versions.
- Workspace protocol versions (workspace:*) must resolve to actual versions before publishing.
- Tag each package release individually for independent versioning.
- Run the full test suite after version bumps before publishing.
- Include version bump commits in the changelog.
