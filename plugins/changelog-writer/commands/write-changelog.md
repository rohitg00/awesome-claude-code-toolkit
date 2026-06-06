# /write-changelog - Write Changelog

Generate a detailed changelog entry from git history and merged PRs.

## Steps

1. Determine the version range: from the last release tag to HEAD
2. Fetch all commits in the range with their messages and authors
3. Fetch merged pull requests in the range using the git hosting API
4. Classify changes into categories: Added, Changed, Deprecated, Removed, Fixed, Security
5. Parse conventional commit prefixes (feat, fix, chore, docs, refactor, perf, test)
6. Extract breaking changes from commit messages and PR descriptions
7. Group changes by category and sort by significance
8. Write clear, user-facing descriptions for each change (not raw commit messages)
9. Include PR numbers and links for traceability
10. Credit contributors with their names or usernames
11. Add the date and version number to the changelog entry
12. Prepend the new entry to CHANGELOG.md following Keep a Changelog format

## Rules

- Follow the Keep a Changelog format (keepachangelog.com)
- Write descriptions from the user's perspective, not the developer's
- Highlight breaking changes prominently at the top of the entry
- Do not include internal refactoring unless it affects the public API
- Combine related commits into single changelog entries
- Include migration instructions for breaking changes
- Keep entries concise: one line per change with PR link
