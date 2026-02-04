# /smart-commit:changelog

Parse the git history since the last release tag and generate a structured markdown changelog.

## Process

1. Identify the latest release tag by running `git tag --sort=-v:refname | head -20`.
   - Look for semver-formatted tags (v1.2.3, 1.2.3, etc.)
   - If no tags exist, use the initial commit as the starting point

2. Retrieve all commits since the last tag:
   ```
   git log <last-tag>..HEAD --pretty=format:"%H|%s|%an|%ad" --date=short
   ```

3. Parse each commit message and categorize by conventional commit type:
   - **Added** - `feat` commits introducing new functionality
   - **Fixed** - `fix` commits correcting bugs or errors
   - **Changed** - `refactor`, `perf`, `style` commits modifying existing behavior
   - **Deprecated** - commits mentioning deprecation in subject or body
   - **Removed** - commits removing features, files, or dead code
   - **Security** - commits addressing vulnerabilities or security concerns
   - **Documentation** - `docs` commits
   - **Internal** - `chore`, `ci`, `test`, `build` commits

4. For each commit entry, format as:
   - Concise description derived from the commit subject
   - Scope in parentheses if present
   - Shortened commit hash as a reference

5. Suggest the next version number based on changes:
   - MAJOR bump if any `BREAKING CHANGE` footers are present
   - MINOR bump if any `feat` commits are present
   - PATCH bump if only `fix`, `refactor`, `perf`, `docs`, `chore` commits

6. Generate the changelog in Keep a Changelog format.

## Output Format

```markdown
## [X.Y.Z] - YYYY-MM-DD

### Added
- Description of new feature (scope) [`abc1234`]

### Fixed
- Description of bug fix (scope) [`def5678`]

### Changed
- Description of modification (scope) [`ghi9012`]

### Internal
- Description of internal change [`jkl3456`]
```

## Rules

- Group entries by category, not chronologically
- Omit empty categories entirely
- Keep descriptions user-facing: translate technical commits into impact statements
- If a commit message is unclear, read the diff with `git show <hash> --stat` for context
- Merge commits and revert-of-reverts should be excluded
- Present the changelog for review before writing to CHANGELOG.md
- Prepend to existing CHANGELOG.md if one exists, do not overwrite history
