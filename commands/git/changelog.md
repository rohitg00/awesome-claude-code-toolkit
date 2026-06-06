Generate a changelog from git history since the last tag or a specified reference point.

## Steps

1. Find the latest tag: `git describe --tags --abbrev=0 2>/dev/null || echo "initial"`.
2. Get all commits since that tag: `git log <tag>..HEAD --oneline --no-merges`.
3. Parse each commit message to extract type, scope, and subject.
4. Group commits by type with these categories:
   - **Features** (`feat`)
   - **Bug Fixes** (`fix`)
   - **Performance** (`perf`)
   - **Refactoring** (`refactor`)
   - **Documentation** (`docs`)
   - **Tests** (`test`)
   - **Chores** (`chore`)
5. Within each group, sort by scope alphabetically.
6. Highlight breaking changes in a separate section at the top.
7. Output the changelog in Keep a Changelog format.

## Output Format

```markdown
## [Unreleased] - YYYY-MM-DD

### Breaking Changes
- scope: description of breaking change

### Features
- scope: description of new feature

### Bug Fixes
- scope: description of fix

### Performance
- scope: description of improvement
```

## Rules

- Only include types that have entries. Skip empty sections.
- If commits do not follow conventional commit format, group them under "Other Changes".
- Include commit hashes as references for traceability.
- Suggest a version bump: patch (fixes only), minor (features), major (breaking changes).
