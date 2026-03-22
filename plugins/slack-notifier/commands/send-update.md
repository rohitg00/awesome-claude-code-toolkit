# /send-update - Send Slack Update

Send a formatted status update to a Slack channel.

## Steps

1. Ask the user for the update type: deployment, build, release, incident, or custom
2. Determine the target Slack channel from project configuration or user input
3. Gather the update details: status (success/failure/in-progress), summary, relevant links
4. Format the message using Slack Block Kit for rich formatting
5. Add contextual metadata: project name, environment, version, timestamp
6. Include action buttons for common follow-ups (view logs, rollback, approve)
7. Set the appropriate emoji and color based on status (green/red/yellow)
8. Add mentions (@here, @channel, or specific users) based on severity
9. Send the message via Slack webhook or API
10. Capture the message timestamp for threading follow-up messages
11. Log the notification for audit and delivery confirmation
12. Report: message sent, channel, timestamp, delivery status

## Rules

- Never send @channel or @here mentions for non-critical updates
- Use thread replies for follow-up messages to reduce channel noise
- Include direct links to relevant resources (PR, pipeline, dashboard)
- Format code blocks and logs properly using Slack markdown
- Respect channel notification preferences and quiet hours
- Do not include sensitive data (credentials, tokens) in messages
- Rate-limit notifications to prevent spam (max 1 per minute per channel)
