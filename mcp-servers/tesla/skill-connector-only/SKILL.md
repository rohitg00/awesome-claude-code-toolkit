---
name: tesla-connector
description: Control and locate the user's Tesla with the tesla_* MCP tools. Use when the user says "find my Tesla/car", "where is my car parked", "drop a pin to my car", "unlock/lock the car", "warm up / cool the car", "set charge limit", "is my car charging", "open the trunk/frunk", "turn on sentry", "send this address to the car", or anything about their Tesla vehicle.
---

# Tesla Connector

This skill is instructions only — it has no bundled code. It requires the
**Tesla connector** to already be connected (Settings → Connectors, or the
Desktop extension), which exposes 72 tools prefixed `tesla_`. If those tools
aren't available in this conversation, tell the user to add the Tesla
connector first and don't attempt to fabricate vehicle data.

Prefer the high-level tools below; fall back to a more specific `tesla_*`
tool for anything not listed.

## Tool selection

| User intent | Tool |
| --- | --- |
| "Where's my car?" / "find my Tesla" | `tesla_find_my_tesla` — returns address, coordinates, map links, and a `speak` line. Answer with the `speak` line and give the Apple/Google Maps links. |
| "Send/drop a pin (to family)" | `tesla_drop_pin` — returns `share_message` ready to text; offer to relay it. |
| "Take me to my car" | `tesla_navigate_to_tesla` — give `open_walking` (or driving) link. |
| "Unlock the car" (family needs in) | `tesla_unlock_doors`, confirm success plainly. Lock again with `tesla_lock_doors` if asked. |
| "How's the car?" / battery / range | `tesla_status` — one composite snapshot; summarize, don't dump JSON. |
| Climate ("warm it up to 72") | `tesla_climate_on`, then `tesla_set_temperature` with `unit:"F"` when the user speaks Fahrenheit. Dog/camp: `tesla_set_climate_keeper`. |
| Charging | `tesla_charge_start`/`tesla_charge_stop`, `tesla_set_charge_limit`, `tesla_set_charging_amps`, `tesla_nearby_charging_sites`. |
| Trunk/frunk/windows | `tesla_actuate_trunk` (`which: front|rear`), `tesla_window_control` (`action: vent|close`). |
| Security | `tesla_set_sentry_mode`, `tesla_set_valet_mode`, `tesla_speed_limit_*`. |
| "Send this address to the car" | `tesla_send_destination`. |

## Behavior rules

- **Asleep cars**: commands auto-wake, but data may report `asleep: true` —
  call `tesla_wake_up` (or retry with `wake: true`) rather than telling the
  user it failed.
- **Multiple vehicles**: if a tool errors listing several cars, ask which one
  once, then pass `vehicle` (VIN) on subsequent calls.
- **Mock/demo mode**: results with VIN `7SAYGDEE9PF000000` or a reason like
  `mock:*` are the demo car, not the user's real Tesla — say so plainly.
- **Destructive/irreversible actions** (`tesla_erase_user_data`,
  `tesla_remote_start_drive`, unlocking when nobody expects it): confirm with
  the user first unless they just asked for exactly that.
- **Secrets**: never print refresh tokens, config contents, or bridge tokens
  into chat.
- Speak results, don't dump raw JSON; the `speak` fields exist for that.
- If no `tesla_*` tools are available at all, say the Tesla connector isn't
  connected yet and point the user at Settings → Connectors, rather than
  guessing or fabricating a response.
