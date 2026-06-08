# Setup — Rarefriend Microsoft Email

## Step 1 — Get API credentials

1. Sign in at [rarefriend.com](https://rarefriend.com)
2. Go to **Settings → Integrations → MCP**
3. Click **Manage → Generate OAuth Client** — copy the Client ID and Client Secret (shown once)

## Step 2 — Connect MCP

### Claude Code / Codex

```bash
claude mcp add rarefriend \
  -e RAREFRIEND_CLIENT_ID=your_client_id \
  -e RAREFRIEND_CLIENT_SECRET=your_client_secret \
  -- npx -y @rarefriend-ai/mcp
```

### Cursor (`~/.cursor/mcp.json`)

```json
{
  "mcpServers": {
    "rarefriend": {
      "command": "npx",
      "args": ["-y", "@rarefriend-ai/mcp"],
      "env": {
        "RAREFRIEND_CLIENT_ID": "your_client_id",
        "RAREFRIEND_CLIENT_SECRET": "your_client_secret"
      }
    }
  }
}
```

### Claude Desktop

Edit `~/Library/Application Support/Claude/claude_desktop_config.json` (macOS)
or `~/.config/Claude/claude_desktop_config.json` (Linux):

```json
{
  "mcpServers": {
    "rarefriend": {
      "command": "npx",
      "args": ["-y", "@rarefriend-ai/mcp"],
      "env": {
        "RAREFRIEND_CLIENT_ID": "your_client_id",
        "RAREFRIEND_CLIENT_SECRET": "your_client_secret"
      }
    }
  }
}
```

## Step 3 — Connect Microsoft Email

Once MCP is running, ask the assistant:

```
Connect my Outlook email to Rarefriend
```

The assistant will call `connect_integration("microsoft_email")` and return a link. Open it in your browser and sign in with your Microsoft/Office 365 account. Sync takes a few minutes — ask the assistant to check when it's done.
