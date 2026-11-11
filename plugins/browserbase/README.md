# Browserbase Plugin

Cloud browser automation for Claude Code — scrape pages, fill forms, extract structured data, and drive browsers with natural language via [Browserbase](https://browserbase.com) and [Stagehand](https://docs.browserbase.com/welcome/quickstarts/stagehand).

## Quick Install

1. Copy or symlink this plugin folder into your project's `plugins/` directory
2. Run `/browserbase:setup` — it opens a browser popup to log in to Browserbase, validates your key, and auto-saves it everywhere. No manual env var copying.
3. That's it. The plugin auto-configures everything else:
   - **OAuth login** — browser popup to sign in and obtain API key automatically
   - **MCP server** registers via `.mcp.json` (no manual settings edit)
   - **SessionStart hook** finds your API key across env vars, .env files, MCP configs, Claude settings, and shell profiles — propagates it wherever it's missing
   - **UserPromptSubmit hook** detects browser/scraping intent and routes to the plugin

## Login Modes

```bash
# Interactive — opens browser popup (default)
node plugins/browserbase/auth/login.js

# Headless — prints URL to open manually (for remote/SSH sessions)
node plugins/browserbase/auth/login.js --headless

# Direct — skip the popup, register a known key
node plugins/browserbase/auth/login.js --key bb_live_...
```

## Commands

| Command | What it does |
|---------|-------------|
| `/browserbase:setup` | OAuth login + CLI install + credential auto-registration |
| `/browserbase:scrape-page` | Scrape and extract structured data from a web page |
| `/browserbase:fill-form` | Fill out and submit a web form |
| `/browserbase:browse-agent` | Run an open-ended browsing agent |
| `/browserbase:capture-design` | Screenshot a site and generate a reusable design.md scaffold |

## What's Inside

```
browserbase/
├── .claude-plugin/plugin.json   # Plugin manifest
├── .mcp.json                    # Auto-registers Browserbase MCP server
├── README.md
├── auth/
│   └── login.js                 # OAuth-style browser login flow
├── agents/
│   └── browser-automation-engineer.md
├── agent-skill/
│   └── SKILL.md                 # Stagehand API reference + patterns
├── commands/
│   ├── setup.md                 # Login + install + verify
│   ├── scrape-page.md
│   ├── fill-form.md
│   ├── browse-agent.md
│   └── capture-design.md
├── hooks/
│   ├── hooks.json               # SessionStart + UserPromptSubmit hooks
│   └── scripts/
│       ├── detect-browser-intent.js
│       ├── screenshot-on-error.js
│       ├── data-validator.js
│       ├── multi-page-crawler.js
│       ├── capture-design.js
│       ├── verify-setup.sh
│       └── lib/prompt-hook.js       # shared stdin/JSON parsing for the hooks above
└── setup/
    └── install.sh               # Full automated setup script
```

## How Credential Auto-Discovery Works

The plugin searches these locations (in order) for `BROWSERBASE_API_KEY`:

1. `BROWSERBASE_API_KEY` environment variable
2. `.env`, `.env.local`, `.env.development`, `.env.production`
3. `mcp-configs/browserbase.json`, `.mcp.json` (read-only — see note below)
4. `.claude/settings.local.json`, `.claude/settings.json`, `~/.claude/settings.json`
5. `~/.bashrc`, `~/.zshrc`, `~/.bash_profile`, `~/.profile`

When found, the key is auto-registered into `.env` (gitignored) and your shell profile if missing there. When not found, the OAuth login flow is triggered. The user is always notified of what changed but never asked for permission.

**Note:** `mcp-configs/browserbase.json` and `.mcp.json` reference the key as `${BROWSERBASE_API_KEY}` (env-var expansion), so they resolve automatically once `.env`/the environment is set. The plugin never writes a literal key into either file — both are tracked in git, and writing a live secret there would risk it getting committed.

## Requirements

- Node.js 18+
- No `BROWSERBASE_PROJECT_ID` needed — the API key resolves it automatically

## Free-Tier Notes

- Model Gateway includes $5 of LLM tokens — leave `MODEL_API_KEY` blank to use it
- No Proxies or Verified sessions — bot-protected sites may block
- If LLM calls fail on a working script, the $5 cap is likely the cause

## Packaging

`scripts/export.sh` builds two self-contained artifacts under `build/`:

- `browserbase.mcpb` — one-click install in Claude Desktop
  (`npx @anthropic-ai/mcpb install build/browserbase.mcpb`)
- `browserbase-plugin.zip` — this plugin with `@browserbasehq/mcp` vendored
  into `vendor/node_modules`, so the MCP server starts with no npx/network
  fetch on the target machine (the OAuth login flow, hooks, and commands
  still run from source as usual — only the MCP server binary is vendored)
