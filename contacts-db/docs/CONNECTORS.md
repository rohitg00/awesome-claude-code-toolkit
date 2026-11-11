# Connector middle-layer (F2c)

A whitelisted, Zapier-style layer so users securely connect their accounts and
pull/sync contacts into the canonical store — without any account secret ever
touching this repo.

## Security model

- **Allowlist.** Only services in `connectors.base.ALLOWED_SERVICES()` can be
  ingested; override with `NTXP_CONNECTOR_ALLOWLIST` (comma-separated). A
  disallowed service raises `PermissionError`.
- **No secrets here.** Auth lives in the broker (Zapier) or the service's own
  OAuth. This layer only ever receives **already-fetched** contact rows.
- **Idempotent + graded.** Ingested contacts flow through the normal resolver/
  dedup pipeline (source `connector:<service>`), then the grader's exposure gate
  and the sync fan-out apply as usual.

## Zapier as the broker

Zapier connects 9,000+ apps and its MCP (`mcp__Zapier__*`) is available in-session.
Flow:

1. User authorizes their account(s) in Zapier.
2. Agent: `discover_zapier_actions(app="<service> find contact")` →
   `inspect_zapier_actions(...)` → `execute_zapier_read_action(...)` to pull contacts.
3. Hand the rows to `connector_import(service, contacts)` (MCP) or
   `ntxp connector-import --service <s> rows.json` — mapped + ingested.
4. Push-back (adding/syncing a contact into a connected service) uses
   `execute_zapier_write_action` and is **approval-gated** (outward-facing).

## Field mapping

`map_contact` reads common aliases across platforms (name/first/last, email(s),
phone(s), company, title) so most services map with no per-service code. Add a
dedicated `Connector` only when a service needs special shaping.

```bash
ntxp connector-import --service hubspot contacts.json
```
