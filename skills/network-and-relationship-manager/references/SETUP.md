# Rarefriend MCP — Setup Guide

## Prerequisites

1. Sign in at [rarefriend.com](https://rarefriend.com)
2. Go to **Settings → Integrations → MCP**
3. Click **copy the Client ID and Client Secret** — copy the **Client ID** and **Client Secret**

---

## Claude Code / Codex (CLI)

```bash
claude mcp add rarefriend \
  -e RAREFRIEND_CLIENT_ID=your_client_id \
  -e RAREFRIEND_CLIENT_SECRET=your_client_secret \
  -- npx -y @rarefriend-ai/mcp
```

Verify: run `/mcp` in Claude Code — `rarefriend` should appear with tools listed.

---

## OpenClaw / Gemini CLI / other agents

Run `npx -y @rarefriend-ai/mcp` with `RAREFRIEND_CLIENT_ID` and `RAREFRIEND_CLIENT_SECRET` set in the environment. See the [MCP repo](https://github.com/Whitefield-Labs/rarefriend-mcp) for client-specific config.

---

## Cursor

Edit `~/.cursor/mcp.json` (create if it doesn't exist):

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

Restart Cursor. Check Settings → MCP — rarefriend should show as connected.

---

## Claude Desktop

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

Restart Claude Desktop. The hammer icon in the input bar confirms tools are available.

---

## Connecting Google or Microsoft

Once the MCP is running, ask the assistant:

```
Connect my Google Contacts to Rarefriend
```

The assistant will call `connect_integration` and return a one-time link (valid 15 minutes). Open it in your browser to complete OAuth. No credentials are needed in the chat.

Supported integrations: `gmail`, `google_contacts`, `google_calendar`, `microsoft_contacts`, `microsoft_calendar`, `microsoft_email`
