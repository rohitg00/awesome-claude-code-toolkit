# /update-status - Update Linear Status

Update the status and progress of Linear tickets.

## Steps

1. Ask the user for the ticket identifier or search by title
2. Fetch the current ticket status and details from Linear
3. Determine the new status: backlog, todo, in progress, in review, done, cancelled
4. Update the ticket status in Linear
5. Add a comment explaining the status change and any relevant context
6. Update the estimate if the scope has changed
7. Link any related PRs or commits to the ticket
8. Move sub-tasks to appropriate statuses based on the parent update
9. Notify relevant team members if the status change requires their action
10. Update the cycle progress if the ticket is in an active cycle
11. Check for blocked tickets that may now be unblocked
12. Report: ticket ID, previous status, new status, updated fields

## Rules

- Always add a comment when changing status to explain why
- Do not skip status transitions (e.g., backlog directly to done)
- Link the PR when moving to "in review" status
- Update sub-task statuses consistently with parent status
- Notify the reviewer when moving to "in review"
- Capture the actual completion time when moving to "done"
- Do not reopen closed tickets; create a new ticket referencing the original
