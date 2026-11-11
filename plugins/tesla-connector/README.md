# Tesla Connector plugin

Claude Code plugin wrapping the [Tesla MCP server](../../mcp-servers/tesla/):
72 tools for locating, locking/unlocking, climate, charging, and everything
else the vehicle API exposes — plus a themed dashboard GUI and a Siri/ChatGPT
bridge.

## First run is automatic

`.mcp.json` launches `bootstrap.mjs`, which on first start:

1. finds the server source (`../../mcp-servers/tesla` in the repo, or
   `TESLA_SERVER_DIR`),
2. builds it if `dist/` is missing (one-time `npm install && npm run build`),
3. loads `~/.config/tesla-mcp/config.json` into the environment,
4. and, with no credentials anywhere, starts in **demo (mock) mode** so every
   tool works immediately.

A `SessionStart` hook notices the unlinked state and surfaces the setup
command.

## Commands

- **`/tesla-connector:setup`** — link the real car: guided Tesla login (PKCE,
  no password ever touches Claude), refresh token written to
  `~/.config/tesla-mcp/config.json` (mode 600) via
  `get-refresh-token.mjs --print-url` / `--exchange --write-config`. No env
  editing.
- **`/tesla-connector:dashboard`** — start the Tesla-themed dashboard + Siri
  bridge (`bootstrap.mjs bridge`) and hand over the URL and bridge token.

## Skill

`skills/tesla-connector/SKILL.md` maps intents ("find my Tesla", "unlock the
car", "warm it up") to the right tools and sets behavior rules (auto-wake,
multi-vehicle, mock detection, secret handling, confirm-before-destructive).

Full server docs, Siri Shortcut recipes, and ChatGPT Actions setup:
[`mcp-servers/tesla/README.md`](../../mcp-servers/tesla/README.md).
