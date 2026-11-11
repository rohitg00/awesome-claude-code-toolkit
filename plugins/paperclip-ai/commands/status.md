# /paperclip-ai:status - Check Paperclip AI health and dashboard summary

Show current Paperclip instance status, agent activity, and cost summary.

## Steps

1. Check server health:
   ```bash
   curl -s http://127.0.0.1:3100/api/health | python3 -m json.tool
   ```
2. If healthy, gather dashboard data:
   ```bash
   npx paperclipai dashboard
   ```
3. Show cost summary:
   ```bash
   npx paperclipai cost
   ```
4. Check for pending approvals:
   ```bash
   npx paperclipai approval
   ```
5. List active agents and their states:
   ```bash
   npx paperclipai agent list
   ```
6. Report a concise summary: server status, active agents, pending work, recent costs, and any alerts

## Rules

- If the server is not running, suggest `/paperclip-ai:setup`
- Highlight any budget warnings or overspend incidents
- Flag agents that haven't heartbeated recently — they may need attention
- Keep the summary concise — link to the UI at http://127.0.0.1:3100 for full details
