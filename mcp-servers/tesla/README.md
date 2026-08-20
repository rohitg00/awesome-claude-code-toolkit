# Tesla Connector — MCP server + dashboard + Siri/ChatGPT bridge

A portable Tesla connector. Point it at your Tesla auth and you get:

- **72 MCP tools** covering the entire vehicle API surface — every data endpoint
  (charge, climate, drive, config, GUI, nearby Superchargers, release notes,
  service data) and every remote command (lock/unlock, honk, flash, climate,
  seat/wheel heaters, defrost, dog/camp mode, charging + scheduling, trunk/frunk,
  windows, sunroof, sentry, valet, speed limit, HomeLink, navigation share,
  media, boombox, software updates, guest mode, rename, …).
- **High-level convenience tools** for the flows that matter day to day:
  - `tesla_find_my_tesla` — where is the car? GPS + street address + map links + a speakable answer
  - `tesla_drop_pin` — a ready-to-text message with Apple/Google Maps links so family can navigate to the car
  - `tesla_navigate_to_tesla` — walking/driving deep links **to** the parked car
  - `tesla_lock_doors` / `tesla_unlock_doors` — let family in while you're away
  - `tesla_status` — one composite snapshot (battery, range, charging, climate, locks, location)
- **A Tesla-themed dashboard GUI** (dark theme, stat tiles, battery gauge,
  one-tap controls, find-my-car, charging & climate panels, and a runner that
  can invoke *any* of the 72 tools).
- **An HTTP bridge** with Siri-Shortcut-friendly endpoints and an OpenAPI spec
  for ChatGPT Actions — so "Hey Siri, find my Tesla" works end to end.

Not affiliated with Tesla, Inc. Use at your own risk; remote unlock of a real
car is a real security decision — read [Security](#security) below.

---

## Quick start (no credentials — demo mode)

```bash
cd mcp-servers/tesla
npm install && npm run build

# MCP server with canned data:
TESLA_MOCK=1 node dist/index.js

# Dashboard + Siri bridge with canned data:
TESLA_MOCK=1 TESLA_BRIDGE_TOKEN=demo node dist/bridge.js
# open http://127.0.0.1:8321 and enter token "demo"
```

## Getting your Tesla auth

Two supported modes — pick one:

### Option A — app-style refresh token (fastest, "owner" mode)

The same OAuth tokens the Tesla mobile app uses. Run the bundled helper:

```bash
node scripts/get-refresh-token.mjs
```

It prints a `auth.tesla.com` login URL; sign in (MFA supported), paste the
"Page Not Found" redirect URL back, and it prints your `TESLA_REFRESH_TOKEN`.
Trusted third-party token apps ("Auth for Tesla" on iOS, `tesla_auth` CLI)
produce the same token if you prefer.

```bash
export TESLA_REFRESH_TOKEN="eyJ..."   # this IS your car key — keep it secret
```

### Option B — official Fleet API ("fleet" mode)

Create an app at [developer.tesla.com](https://developer.tesla.com), grant it
`vehicle_device_data vehicle_location vehicle_cmds vehicle_charging_cmds`,
complete the third-party OAuth flow for your own account, then:

```bash
export TESLA_AUTH_MODE=fleet
export TESLA_CLIENT_ID=...
export TESLA_CLIENT_SECRET=...
export TESLA_REFRESH_TOKEN=...
export TESLA_REGION=na            # na | eu | cn
```

#### Signed commands (2021+ vehicles on the Fleet API)

Newer vehicles only accept commands via Tesla's signed Vehicle Command
Protocol. Run Tesla's
[vehicle-command](https://github.com/teslamotors/vehicle-command)
`tesla-http-proxy` with your enrolled key and point this server at it:

```bash
export TESLA_COMMAND_PROXY_URL=https://localhost:4443
# the proxy uses a self-signed cert:
export NODE_EXTRA_CA_CERTS=/path/to/tls-cert.pem
```

Data endpoints never need the proxy; owner mode (Option A) does not either.

### All environment variables

| Variable | Purpose |
| --- | --- |
| `TESLA_REFRESH_TOKEN` | Long-lived credential (either mode). |
| `TESLA_ACCESS_TOKEN` | Optional short-lived token (skips refresh). |
| `TESLA_AUTH_MODE` | `owner` (default) or `fleet`. |
| `TESLA_CLIENT_ID` / `TESLA_CLIENT_SECRET` | Fleet app credentials (fleet mode). |
| `TESLA_REGION` | `na` (default) / `eu` / `cn` — Fleet API region. |
| `TESLA_API_BASE`, `TESLA_AUTH_BASE` | Endpoint overrides (rarely needed). |
| `TESLA_VIN` | Default vehicle when the account has several. |
| `TESLA_COMMAND_PROXY_URL` | tesla-http-proxy URL for signed commands. |
| `TESLA_TOKEN_CACHE` | Token cache file (default `.tesla-tokens.json`, mode 600). |
| `TESLA_MOCK` | `1` = demo mode, no credentials or network. |
| `TESLA_BRIDGE_PORT` / `TESLA_BRIDGE_HOST` | Bridge bind (default `127.0.0.1:8321`). |
| `TESLA_BRIDGE_TOKEN` | Bridge auth token (auto-generated + printed if unset). |
| `TESLA_BRIDGE_PUBLIC_URL` | Public URL advertised in `/openapi.json`. |

## Using it as an MCP server

Claude Code:

```bash
claude mcp add tesla --env TESLA_REFRESH_TOKEN=... \
  -- node /path/to/mcp-servers/tesla/dist/index.js
```

Claude Desktop / any MCP client — see `../../mcp-configs/tesla.json`.

### Prepackaged exports

`scripts/export.sh` builds three self-contained artifacts into `build/`
(compiled server + production dependencies embedded — no repo clone or
`npm install` on the target machine):

| Artifact | Install |
| --- | --- |
| `tesla.mcpb` | MCP Bundle: open in Claude Desktop, or `npx @anthropic-ai/mcpb install tesla.mcpb` |
| `tesla-connector-plugin.zip` | Claude Code plugin (MCP server + `/setup` + `/dashboard` commands + skill + first-run hook): unzip into `~/.claude/plugins/` |
| `tesla-connector-skill.zip` | Prepackaged Agent Skill (SKILL.md + bundled `tesla-cli`, no MCP needed): unzip into `~/.claude/skills/` or upload to claude.ai |

There is also a direct CLI over the same registry:
`node dist/cli.js tesla_find_my_tesla` / `node dist/cli.js list`.
(`scripts/pack-mcpb.sh` remains for building just the `.mcpb`.)

Then just ask: *"where's my Tesla?"*, *"unlock the car for my wife"*,
*"set the charge limit to 90 and warm the cabin to 72"*.

## The dashboard

```bash
TESLA_BRIDGE_TOKEN=$(openssl rand -base64 24) node dist/bridge.js
```

Open `http://127.0.0.1:8321`, paste the token once (stored in that browser
only). You get live battery/range/temperature tiles, a battery gauge with the
charge-limit marker, one-tap Lock/Unlock/Flash/Honk/Climate/Frunk/Trunk/
Windows/Sentry, find-my-car with copyable pin, send-destination-to-car,
charging and climate sliders — and an "All tools" panel that can call every
one of the 72 tools with raw JSON args.

## Siri: "find my Tesla", "drop a pin", "unlock the car"

The bridge exposes speakable plain-text endpoints made for Apple Shortcuts:

| Endpoint | Says / does |
| --- | --- |
| `/siri/find` | "Your Tesla is parked facing south near …" + Apple Maps link |
| `/siri/pin` | Shareable pin message (text it to family) |
| `/siri/navigate` | Maps deep link with directions **to** the car |
| `/siri/lock` · `/siri/unlock` | Locks/unlocks, confirms in one sentence |
| `/siri/status` | "Battery 72%, 213 miles of range, doors locked." |

Add `?format=json` for structured output; pass `?vehicle=VIN` with several cars.

### Make it reachable from your phone

Run the bridge somewhere always-on (home server, Pi, NAS) and expose it over
HTTPS **with the token**. Easiest options:

- **Tailscale**: `tailscale funnel 8321` (or keep it tailnet-only with `tailscale serve`)
- **Cloudflare Tunnel**: `cloudflared tunnel --url http://localhost:8321`

Set `TESLA_BRIDGE_HOST=0.0.0.0` only if something in front terminates TLS.

### Build the Shortcuts (once, ~2 minutes each)

1. Shortcuts app → **+** → name it **Find My Tesla** (the name is the Siri phrase).
2. Add **Get Contents of URL** → `https://<your-host>/siri/find` →
   Method GET → Headers: `Authorization: Bearer <TESLA_BRIDGE_TOKEN>`.
3. Add **Speak Text** (or **Show Result**) with the output.
4. Optional: add **Open URLs** with the last line of the result to jump straight into Maps.

Repeat with `/siri/navigate` as **"Take me to my Tesla"** (use **Open URLs** —
it launches turn-by-turn walking directions), `/siri/pin` as **"Drop a pin to
my Tesla"** (add **Share** to text it to family), and `/siri/unlock` as
**"Unlock my Tesla for the family"**. Then: *"Hey Siri, find my Tesla."*

## Show it in your Connectors

Two surfaces, both supported:

- **Claude Desktop (Extensions/Connectors)** — build or grab `tesla.mcpb`
  (`scripts/export.sh`) and open the file in Claude Desktop. It installs under
  Settings → Extensions with a config screen for your token/VIN/region, and the
  `tesla` tools appear in every chat.
- **claude.ai / Claude mobile (custom connector)** — the bridge speaks MCP over
  streamable HTTP at `/mcp`. Expose the bridge over HTTPS (Tailscale funnel /
  Cloudflare tunnel, see above), then in claude.ai → Settings → Connectors →
  **Add custom connector**, use:

  ```
  https://<your-host>/mcp?token=<TESLA_BRIDGE_TOKEN>
  ```

  The Tesla connector then shows in your connectors list on web and mobile,
  with all 72 tools. (The token rides in the URL because custom connectors
  don't send custom headers — use HTTPS and a long random token.)

## ChatGPT integration

Two ways, both first-class:

1. **MCP connector (recommended)** — ChatGPT supports remote MCP connectors;
   any MCP-capable client can run `dist/index.js` directly, or front the
   bridge with your MCP-over-HTTP gateway of choice.
2. **Custom GPT Action** — the bridge publishes `GET /openapi.json`. In
   ChatGPT → Create a GPT → Actions → import from URL
   `https://<your-host>/openapi.json`, set auth to **API Key / Bearer** with
   your `TESLA_BRIDGE_TOKEN`. The GPT can then call `findMyTesla`,
   `dropPin`, `navigateToTesla`, `lockTesla`, `unlockTesla`, `teslaStatus`,
   and the generic `invokeTeslaTool` for everything else. Invoke it from Siri
   via the ChatGPT app: *"Hey Siri, ask ChatGPT to navigate to my Tesla."*

## Security

- Your **refresh token is a key to the car**. It lives only in your
  environment / the token cache file (created with mode 600). Never commit it.
- The bridge **requires a bearer token on every control route** and binds to
  `127.0.0.1` by default. If you expose it to the internet, use HTTPS
  (Tailscale/Cloudflare above), a long random token, and rotate it if shared.
- `tesla_erase_user_data` refuses to run without `confirm="ERASE"`.
- Mock mode (`TESLA_MOCK=1`) is completely offline — use it for demos.

## Development

```bash
npm run dev          # tsc --watch
TESLA_MOCK=1 node dist/index.js    # stdio MCP smoke test
TESLA_MOCK=1 TESLA_BRIDGE_TOKEN=demo node dist/bridge.js
```

Layout: `src/config.ts` (env), `src/auth.ts` (token refresh + cache),
`src/client.ts` (REST + wake/retry + command proxy), `src/mock.ts` (demo
state), `src/tools.ts` (the whole registry — add tools here, both surfaces
pick them up), `src/index.ts` (MCP stdio), `src/bridge.ts` (HTTP),
`public/dashboard.html` (GUI).
