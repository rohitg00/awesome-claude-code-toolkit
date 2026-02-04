# /create-ticket - Create Linear Ticket

Create a structured Linear issue with proper workflow configuration.

## Steps

1. Ask the user for the ticket type: feature, bug, improvement, or task
2. Determine the team and project from the user's context or ask
3. Write a clear title following the team's naming convention
4. Compose the description with: context, requirements, acceptance criteria
5. Set priority: urgent, high, medium, low, or no priority
6. Assign the appropriate label(s): frontend, backend, infrastructure, design
7. Set the estimate (story points or time) based on complexity
8. Link to related tickets if this is part of a larger epic
9. Assign to a team member or leave unassigned for backlog
10. Set the cycle/sprint if the ticket should be worked on immediately
11. Create the ticket using the Linear API
12. Report: ticket identifier, URL, priority, assignee, cycle

## Rules

- Follow the team's ticket title conventions (e.g., "[Component] Description")
- Include acceptance criteria as a checklist in the description
- Set priority based on user impact and urgency, not developer preference
- Link parent issues for sub-tasks to maintain hierarchy
- Do not assign to a cycle without team lead approval
- Include relevant context links: design files, API docs, related PRs
- Keep descriptions scannable with headers, bullets, and code blocks
