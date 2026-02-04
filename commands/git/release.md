Create a tagged release with auto-generated release notes from recent commits.

## Steps

1. Run `git log --oneline $(git describe --tags --abbrev=0 2>/dev/null || git rev-list --max-parents=0 HEAD)..HEAD` to list commits since last tag.
2. Determine the next version number:
   - If `--major`, `--minor`, or `--patch` is specified, use that increment.
   - Otherwise, infer from commit types: `feat` = minor, `fix` = patch, breaking changes = major.
3. Group commits by type (features, fixes, chores, etc.) for the release notes.
4. Check for a `package.json`, `pyproject.toml`, or `Cargo.toml` and update the version field if present.
5. Stage version file changes and commit with `chore: bump version to vX.Y.Z`.
6. Create an annotated tag: `git tag -a vX.Y.Z -m "Release vX.Y.Z"`.
7. If `gh` CLI is available, create a GitHub release: `gh release create vX.Y.Z --generate-notes`.
8. Push the tag and commit: `git push origin HEAD --follow-tags`.

## Format

```
## vX.Y.Z (YYYY-MM-DD)

### Features
- feat(scope): description

### Bug Fixes
- fix(scope): description

### Other Changes
- chore/refactor/docs entries
```

## Rules

- Never create a release on a dirty working tree; abort if uncommitted changes exist.
- Always use semantic versioning (semver).
- Confirm the version bump with the user before tagging.
- Do not include merge commits or CI-only changes in release notes.
