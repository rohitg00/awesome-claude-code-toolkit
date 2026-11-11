# /paperclip-ai:setup - Initialize or verify Paperclip AI instance

Set up Paperclip AI for agent orchestration in the current environment.

## Steps

1. Check if Paperclip is already running:
   ```bash
   curl -s http://127.0.0.1:3100/api/health
   ```
2. If not running, check if onboarded:
   ```bash
   ls ~/.paperclip/instances/default/config.json
   ```
3. If not onboarded, run quickstart:
   ```bash
   npx paperclipai onboard --yes
   ```
4. Fix embedded PostgreSQL permissions if needed (common in containerized environments):
   ```bash
   chmod +x ~/.npm/_npx/*/node_modules/@embedded-postgres/linux-x64/native/bin/*
   chmod o+x ~
   ```
5. Start the server:
   ```bash
   npx paperclipai run
   ```
6. Verify health and report the dashboard URL

## Rules

- Always run `paperclipai doctor` after setup to verify all checks pass
- Never expose the server beyond loopback unless the user explicitly requests LAN/tailnet binding
- If embedded PostgreSQL fails with EACCES, fix permissions on the initdb binary and ensure the postgres user (UID 102) can traverse the path to the data directory
- Report the API URL, UI URL, and deployment mode to the user when setup completes
