# /paperclip-ai:delegate - Create a Paperclip issue and assign it to an agent

Convert the current task or conversation into a tracked Paperclip issue assigned to an appropriate agent.

## Steps

1. Verify Paperclip is running:
   ```bash
   curl -s http://127.0.0.1:3100/api/health
   ```
2. Identify the task from the current conversation context:
   - Summarize what needs to be done
   - Determine the project and goal it relates to
   - Assess priority and any blockers
3. List available agents:
   ```bash
   npx paperclipai agent list
   ```
4. Select the best-fit agent based on the task requirements
5. Create the issue:
   ```bash
   npx paperclipai issue create --title "<title>" --body "<description>" --assignee <agent-id>
   ```
6. Confirm creation and provide the issue identifier
7. Offer to set a budget limit for this task if it involves costly operations

## Rules

- Always confirm the task summary with the user before creating the issue
- Include enough context in the issue body that the assigned agent can work autonomously
- Link to parent goals or projects when they exist
- If no suitable agent exists, suggest hiring one with `npx paperclipai agent`
- Report the issue ID so the user can track progress via dashboard or CLI
