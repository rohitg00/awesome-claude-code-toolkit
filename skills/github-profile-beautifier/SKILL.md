---
name: github-profile-beautifier
description: Use when user wants to create or improve their GitHub profile README, generate a new profile page, or beautify their existing GitHub homepage with stats, projects, and tech stack badges
---

# GitHub Profile Beautifier

One-click generation of beautiful GitHub profile READMEs. Auto-detects repos, analyzes tech stack, and recommends projects and themes.

## When to Use

- User wants to create a GitHub profile page
- User wants to beautify their existing README
- User wants to showcase projects and tech stack

## Core Pattern

### Step 1: Get user info

```bash
# Check gh CLI
command -v gh || echo "Install gh CLI: brew install gh" && exit 1

# Get user info and repos
gh api users/$USERNAME --jq '.login,.name,.bio'
gh repo list $USERNAME --limit 50 --json name,description,primaryLanguage,url,updatedAt,stargazerCount,isFork
```

### Step 2: Analyze repos

- Filter non-fork repos
- Sort by: `stars` (by stars), `updated` (by update time), `smart` (combined score)
- Stats language distribution

### Step 3: Generate README

Output a complete README.md with:
- Profile header with typing animation
- GitHub stats cards (via github-readme-stats)
- Top 5 project table
- Tech stack badges (via shields.io)
- Contact section

**5 themes**: Radical, Tokyo Night, Dracula, Minimalist, Professional

## Quick Reference

```bash
/github-profile-beautifier username
/github-profile-beautifier username --sort stars --theme tokyonight
```

## Full Version

For complete templates and themes, see: [wu529778790/shenzjd-skills](https://github.com/wu529778790/shenzjd-skills/tree/main/github-profile-beautifier)

Install with: `npx skills add wu529778790/shenzjd-skills -s github-profile-beautifier`
