# /browserbase:setup

Install and configure the Browserbase plugin with OAuth-style browser login.

## Process

1. Check if Node.js is installed (required for the browse CLI and MCP server).
2. Check if the `browse` CLI is installed. If not, install it with `npm install -g browse@latest`.
3. Remove any deprecated CLIs that shadow `browse`.
4. Check if `BROWSERBASE_API_KEY` is already set anywhere (env, .env, MCP configs, Claude settings, shell profiles).
5. If the key is found, validate it and auto-register into any locations that are missing it.
6. If the key is NOT found, launch the OAuth login flow:
   ```bash
   node "${CLAUDE_PLUGIN_ROOT}/auth/login.js"
   ```
   This opens a browser popup where the user logs into Browserbase, copies their API key, and pastes it — the script validates and auto-saves it everywhere.
7. For headless/remote environments where a browser can't open, use:
   ```bash
   node "${CLAUDE_PLUGIN_ROOT}/auth/login.js" --headless
   ```
   This prints a URL to open manually.
8. To register a key directly without the browser flow:
   ```bash
   node "${CLAUDE_PLUGIN_ROOT}/auth/login.js" --key bb_live_...
   ```
9. After registration, run `browse cloud projects list` to verify.
10. Confirm success and list available commands.

## Rules

- Never ask for or set `BROWSERBASE_PROJECT_ID` — it is not needed.
- Leave `MODEL_API_KEY` and other LLM provider keys blank on free-tier accounts.
- The `.mcp.json` auto-registers the MCP server — no manual Claude settings edits needed.
- The login flow auto-saves the key to .env, mcp-configs, and shell profiles — notify the user where it was saved but don't ask permission.
- If running in a remote/headless environment, use --headless mode and provide the URL for the user to open.
