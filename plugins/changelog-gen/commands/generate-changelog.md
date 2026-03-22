Generate a changelog from git history, grouping commits by type and version.

## Steps

1. Determine the version range:
   - If `--from` and `--to` are specified, use those tags.
   - Otherwise, generate from the last tag to HEAD.
   - For initial changelog, process all commits.
2. Parse commits using conventional commit format:
   - `feat`: Features section.
   - `fix`: Bug Fixes section.
   - `perf`: Performance section.
   - `docs`: Documentation section.
   - `refactor`: Code Refactoring section.
   - `test`: Tests section.
   - `chore`/`ci`/`build`: Maintenance section.
   - `BREAKING CHANGE`: Breaking Changes section (always first).
3. For each entry, include:
   - Commit subject line.
   - Scope in parentheses if present.
   - PR number or commit hash as reference.
   - Author attribution.
4. Sort sections by importance: Breaking > Features > Fixes > Performance > Others.
5. Write or update `CHANGELOG.md` with the new version at the top.
6. If existing `CHANGELOG.md` exists, prepend the new version section.

## Format

```markdown
# Changelog

## [1.2.0] - 2026-02-04

### Breaking Changes
- **api**: Removed deprecated `/v1/users` endpoint (#123)

### Features
- **auth**: Add OAuth2 PKCE flow support (#120)

### Bug Fixes
- **db**: Fix connection pool leak under high concurrency (#118)

### Performance
- **cache**: Reduce Redis round-trips by 40% with pipelining (#115)
```

## Rules

- Follow Keep a Changelog format (keepachangelog.com).
- Always include the date in each version header.
- Group by type, then sort by scope within each group.
- Skip merge commits and CI-only changes.
- Link version headers to git comparison URLs when possible.
