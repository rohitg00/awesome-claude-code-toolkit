# /tesla-connector:dashboard

Start the Tesla-themed dashboard GUI (and Siri bridge) and hand the user the
URL + token.

## Steps

1. **Ensure a bridge token exists.** Read `~/.config/tesla-mcp/config.json`.
   If it has no `TESLA_BRIDGE_TOKEN`, generate one
   (`openssl rand -base64 24` or Node `crypto.randomBytes(24).toString('base64url')`)
   and add it to the config file. This keeps the token stable across restarts
   so the user's browser and Siri Shortcuts keep working.

2. **Start the bridge** in the background:

   ```bash
   node ${CLAUDE_PLUGIN_ROOT}/bootstrap.mjs bridge
   ```

   The bootstrap handles first-run building, config loading, and mock-mode
   fallback exactly like the MCP server. Default bind is `127.0.0.1:8321`
   (`TESLA_BRIDGE_PORT` / `TESLA_BRIDGE_HOST` in the config file to change).

3. **Confirm it's up**: `curl -s localhost:8321/healthz` should return
   `{"ok":true,...}`.

4. **Tell the user**:
   - Dashboard: `http://127.0.0.1:8321` — paste the bridge token once
     (tell them the token value; it's theirs, and it is NOT the Tesla token).
   - If the connector is still in mock mode, the dashboard shows the demo car;
     run `/tesla-connector:setup` to link the real one.
   - Siri endpoints live at `/siri/find`, `/siri/pin`, `/siri/navigate`,
     `/siri/lock`, `/siri/unlock`, `/siri/status` — see
     `mcp-servers/tesla/README.md` for the 2-minute Shortcut recipes and how to
     expose the bridge via Tailscale/Cloudflare for phone access, plus the
     ChatGPT Actions setup via `/openapi.json`.
