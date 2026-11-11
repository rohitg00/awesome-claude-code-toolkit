# /tesla-connector:setup

Link the user's real Tesla to the connector. This walks the whole first-run
setup — build, auth, config — with zero manual env editing. The connector
already works in demo (mock) mode before this; setup switches it to the real
car.

The server lives at `mcp-servers/tesla/` relative to the toolkit repo; the
plugin bootstrap (`${CLAUDE_PLUGIN_ROOT}/bootstrap.mjs`) finds it the same way
(env `TESLA_SERVER_DIR` → config `TESLA_SERVER_DIR` → `../../mcp-servers/tesla`
from the plugin). Config lives at `~/.config/tesla-mcp/config.json` (chmod 600).

## Steps

1. **Locate & build the server.** Resolve the server directory as above. If
   `dist/index.js` is missing, run `npm install && npm run build` in it. If the
   directory can't be found (plugin installed without the repo), ask the user
   where they cloned `awesome-claude-code-toolkit`, then record it by adding
   `"TESLA_SERVER_DIR": "<path>"` to `~/.config/tesla-mcp/config.json`.

2. **Check for existing auth.** If `~/.config/tesla-mcp/config.json` already
   has a `TESLA_REFRESH_TOKEN` (or the env does), confirm with the user before
   replacing it — they may just want to change VIN/region settings (step 4).

3. **Run the auth flow** (owner mode — works for any Tesla account, no
   developer app needed):
   1. Run: `node <server-dir>/scripts/get-refresh-token.mjs --print-url`
   2. Show the user the printed URL. Ask them to open it, sign in to Tesla
      (MFA is fine), and paste back the full "Page Not Found" redirect URL
      (`https://auth.tesla.com/void/callback?code=...`). NEVER ask for their
      Tesla password — only for that redirect URL.
   3. Run: `node <server-dir>/scripts/get-refresh-token.mjs --exchange "<pasted URL>" --write-config`
      This stores the refresh token in the config file (mode 600) and prints a
      masked confirmation. Do not echo the token itself anywhere.

   If the user instead has Fleet API developer credentials, skip the helper and
   write `TESLA_AUTH_MODE: "fleet"`, `TESLA_CLIENT_ID`, `TESLA_CLIENT_SECRET`,
   `TESLA_REFRESH_TOKEN`, `TESLA_REGION` into the config file yourself (ask for
   the values; treat them as secrets — write, don't repeat back).

4. **Optional preferences.** Ask (briefly, one question) whether to set a
   default vehicle. If the account has several cars, add `"TESLA_VIN": "..."`.
   Other honored keys: `TESLA_REGION`, `TESLA_COMMAND_PROXY_URL`,
   `TESLA_BRIDGE_TOKEN`, `TESLA_BRIDGE_PORT`.

5. **Verify.** The MCP server was launched before the token existed, so it may
   still be in mock mode — tell the user to run `/mcp` → reconnect `tesla` (or
   restart the session). Then call the `tesla_list_vehicles` tool: real VINs
   confirm the link. If it errors, re-check the token exchange output.

6. **Offer next steps.** Point at `/tesla-connector:dashboard` for the GUI and
   the README's Siri Shortcuts + ChatGPT Actions recipes
   (`mcp-servers/tesla/README.md`).

## Safety

- The refresh token is literally a key to the car: only ever store it in
  `~/.config/tesla-mcp/config.json` (mode 600) or the env — never in the repo,
  never in chat output, never in logs.
- If the user wants demo mode back, set `"TESLA_MOCK": "1"` in the config file.
