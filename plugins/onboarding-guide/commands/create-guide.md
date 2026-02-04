# /create-guide - Create Onboarding Guide

Create a comprehensive onboarding guide for new developers joining the project.

## Steps

1. Analyze the project structure: languages, frameworks, build tools, and architecture
2. Read existing documentation (README, CONTRIBUTING, wiki) for context
3. Identify prerequisites: language versions, tools, database engines, cloud accounts
4. Document the local development setup: clone, install, configure, run
5. List required environment variables and how to obtain their values
6. Describe the project architecture: directory structure, key modules, data flow
7. Document the development workflow: branching strategy, PR process, code review
8. List available commands: build, test, lint, format, deploy
9. Identify common gotchas and troubleshooting steps from git history and issues
10. Include links to important resources: design docs, API docs, Figma, Slack channels
11. Add a first-task checklist for new developers to complete in their first week
12. Save the guide to docs/onboarding.md

## Rules

- Write for someone with general development experience but no project knowledge
- Include exact commands, not vague instructions like "set up the database"
- Test all setup commands to verify they work on a fresh clone
- Include both macOS and Linux setup instructions when they differ
- Keep the guide under 500 lines; link to detailed docs for deep dives
- Update version numbers and tool requirements to match current project state
- Include contact information for the team lead or onboarding buddy
