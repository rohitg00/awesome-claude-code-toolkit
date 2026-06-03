---
name: release-notes-generator
description: Use when creating git tags, releases, or version bumps, or when user wants to generate changelogs and release notes from git history
---

# Release Notes Generator

Automatically compare git history between tags and generate standardized release notes with conventional commit categorization.

## When to Use

- User wants to create a git tag or release
- User wants to summarize version changes
- User mentions changelog, release notes, version notes

## Core Pattern

### Step 1: Detect version

```bash
PREV_TAG=$(git describe --tags --abbrev=0)
```

Suggest version: breaking changes → major, new features → minor, bugfix only → patch.

### Step 2: Compare changes

```bash
git log ${PREV_TAG}..HEAD --oneline
git diff ${PREV_TAG}..HEAD --stat
```

### Step 3: Categorize

| Category | Prefix |
|----------|--------|
| 🚀 Features | `feat:` |
| 🐛 Bug Fixes | `fix:` |
| 📝 Documentation | `docs:` |
| ♻️ Refactor | `refactor:` |
| 🔧 Chores | `chore:` |
| 💥 Breaking Changes | `BREAKING CHANGE` |

### Step 4: Generate notes

Output formatted markdown with categorized changes and diff link.

### Step 5: Create tag/release (optional)

```bash
git tag -a ${VERSION} -m "${RELEASE_NOTES}"
gh release create ${VERSION} --notes "${RELEASE_NOTES}"
```

## Quick Reference

```bash
/release-notes              # Auto-suggest version
/release-notes v1.1.0       # Specify version
/release-notes --dry-run    # Generate only, no tag
```

## Full Version

For complete template: [wu529778790/shenzjd-skills](https://github.com/wu529778790/shenzjd-skills/tree/main/release-notes-generator)

Install with: `npx skills add wu529778790/shenzjd-skills -s release-notes-generator`
