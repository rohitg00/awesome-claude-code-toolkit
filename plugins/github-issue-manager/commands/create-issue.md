# /create-issue - Create GitHub Issue

Create a well-structured GitHub issue with proper metadata.

## Steps

1. Ask the user for the issue type: bug report, feature request, or task
2. For bugs: gather steps to reproduce, expected vs actual behavior, environment details
3. For features: gather the use case, proposed solution, and alternatives considered
4. For tasks: gather the description, acceptance criteria, and dependencies
5. Select the appropriate issue template if the repository has them configured
6. Add relevant labels: bug/feature/task, priority, component area
7. Set the milestone if applicable to the current release cycle
8. Add the issue to a project board if one is configured
9. Link related issues using GitHub keywords (relates to, depends on, blocks)
10. Assign to the appropriate team member if known
11. Create the issue using the GitHub API with all metadata
12. Report: issue number, URL, labels, assignee, project board

## Rules

- Use the repository's issue template when available
- Include reproducible steps for every bug report
- Add code snippets or screenshots when they clarify the issue
- Do not create duplicate issues; search existing issues first
- Keep the title concise and descriptive (under 80 characters)
- Use task lists (checkboxes) for issues with multiple deliverables
- Include acceptance criteria for features and tasks
