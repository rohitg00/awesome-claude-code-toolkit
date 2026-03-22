# /triage-issues - Triage GitHub Issues

Analyze and triage open GitHub issues for prioritization.

## Steps

1. Fetch all open issues from the repository using the GitHub API
2. Filter issues by: unlabeled, unassigned, or stale (no activity in 30 days)
3. Analyze each issue for: completeness, reproducibility, severity, and impact
4. Suggest labels based on issue content: bug, feature, enhancement, documentation, question
5. Assess priority based on: user impact, frequency of reports, component affected
6. Identify duplicate issues by comparing titles and descriptions with existing issues
7. Flag issues that need more information from the reporter
8. Group related issues that could be addressed together
9. Suggest assignees based on the component or area affected
10. Create a triage summary: total open, by priority, by label, stale issues
11. Recommend which issues to close (duplicates, won't fix, cannot reproduce)
12. Generate a prioritized backlog view for the next sprint

## Rules

- Do not close issues without user confirmation
- Respect existing labels and assignments; suggest changes, do not override
- Mark issues as stale only if truly inactive (no comments, no linked PRs)
- Prioritize bugs over features, security issues over all others
- Consider the number of thumbs-up reactions as a popularity signal
- Do not auto-assign issues; suggest assignees for human decision
- Keep triage notes factual and neutral in tone
