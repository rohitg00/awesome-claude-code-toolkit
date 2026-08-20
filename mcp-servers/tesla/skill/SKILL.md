---
name: tesla-connector
description: Locate and control the user's Tesla via the bundled CLI (no MCP setup needed). Use when the user says "find my Tesla/car", "where is my car parked", "drop a pin to my car", "lock/unlock the car", "warm up / cool the car", "set charge limit", "is my car charging", "open the trunk/frunk", "turn on sentry", "send this address to the car", or anything about their Tesla vehicle.
---

# Tesla Connector (prepackaged skill)

This skill bundles a compiled Tesla client. Every capability is invoked
through one CLI (paths are relative to this skill's directory):

```bash
node server/dist/cli.js <tool_name> '{"json":"args"}'
node server/dist/cli.js list        # all 72 tools with params
```

Output is JSON on stdout. No build step is required — `server/` ships
compiled with its dependencies.

## Credentials

Resolution order: environment (`TESLA_REFRESH_TOKEN` etc.) →
`~/.config/tesla-mcp/config.json` → **demo mock mode** (canned Model Y,
VIN `7SAYGDEE9PF000000`). If results are mock, tell the user and offer to
link the real car:

1. `node server/scripts/get-refresh-token.mjs --print-url` — show the user
   the URL; they sign in to Tesla and paste back the full
   `https://auth.tesla.com/void/callback?code=...` redirect URL. NEVER ask
   for their Tesla password.
2. `node server/scripts/get-refresh-token.mjs --exchange "<pasted URL>" --write-config`
   — stores the token in `~/.config/tesla-mcp/config.json` (mode 600).
   Do not echo the token.

## Tool selection

| User intent | Invocation |
| --- | --- |
| "Where's my car?" | `cli.js tesla_find_my_tesla` → answer with the `speak` field + map links |
| "Drop/send a pin (to family)" | `cli.js tesla_drop_pin` → relay `share_message` |
| "Take me to my car" | `cli.js tesla_navigate_to_tesla` → give `open_walking`/`open_driving` |
| "Unlock/lock the car" | `cli.js tesla_unlock_doors` / `tesla_lock_doors` |
| Battery / "how's the car" | `cli.js tesla_status` → summarize; never dump raw JSON |
| Climate ("warm it to 72") | `cli.js tesla_climate_on`, then `tesla_set_temperature '{"temp":72,"unit":"F"}'` |
| Charging | `tesla_charge_start/stop`, `tesla_set_charge_limit '{"percent":90}'`, `tesla_nearby_charging_sites` |
| Trunk / frunk / windows | `tesla_actuate_trunk '{"which":"front"}'`, `tesla_window_control '{"action":"vent"}'` |
| Sentry / valet / speed limit | `tesla_set_sentry_mode '{"on":true}'`, `tesla_set_valet_mode`, `tesla_speed_limit_*` |
| "Send this address to the car" | `tesla_send_destination '{"destination":"..."}'` |

Anything else: run `cli.js list` — media, boombox, seat heaters, defrost,
dog/camp mode, scheduled charging/departure, HomeLink, software updates,
guest mode, rename are all there.

## Behavior rules

- **Asleep cars**: commands auto-wake; if data reports `asleep: true`, run
  `tesla_wake_up` and retry rather than reporting failure.
- **Multiple vehicles**: on an ambiguity error, ask which car once, then pass
  `{"vehicle":"<VIN>"}` on subsequent calls.
- **Destructive/surprising actions** (`tesla_erase_user_data`,
  `tesla_remote_start_drive`, unlocking when nobody asked): confirm first.
- **Secrets**: never print the refresh token or config file contents.
- **Dashboard/Siri**: `node server/dist/bridge.js` starts a themed dashboard
  GUI + Siri-Shortcut endpoints on port 8321 — see `server/README.md`.
