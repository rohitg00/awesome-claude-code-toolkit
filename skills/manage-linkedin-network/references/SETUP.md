# Setup — Rarefriend LinkedIn CRM

## Step 1 — Get API credentials

1. Sign in at [rarefriend.com](https://rarefriend.com)
2. Go to **Settings → Integrations → MCP**
3. Click **copy the Client ID and Client Secret** — copy the Client ID and Client Secret

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

## Step 3 — Import LinkedIn connections

No OAuth needed for LinkedIn. Export your connections from LinkedIn and paste the rows into the assistant. See [LINKEDIN_IMPORT.md](LINKEDIN_IMPORT.md) for the full export guide.
