# NTXP Platform — one codebase, many viewpoints

Each self-hosted NTXP app keeps **its own subdomain**; all of them are **views of the same codebase**.

| View | Subdomain | Inputs | Outputs | Reaches |
|---|---|---|---|---|
| **contacts** | contacts.ntxpllc.cloud | imports, CRM/Workspace sync, inline edits | live table, reports, vCard/CardDAV, hotlinks, signed webhooks | contacts, contracts (read), links |
| **contracts** | contracts.ntxpllc.cloud | contract log, job sync, inline edits | reference lookups, profiles, vCard/ICS, change feed | contracts, contacts (read), links |
| **apilog** | api.ntxpllc.cloud | API registrations, usage/cost | masked registry, audited secret reveals, spend | **itself only** |
| **all** | MCP gateway | — | combined non-sensitive surface | everything except secrets |

## Pieces
* **Registry** (`registry.py`, `apps/*.py`) — every app's data fields (derived from its own dataclasses, so they
  cannot drift) and functions, merged into one **combined profile**. Shared concepts (`org_name`, `email`, `phone`,
  `address`, `website`, `contract_no`) are *join keys* listing every field across apps that carries them.
  `ntxp-platform profile` prints it; `GET /_ntxp/profile` serves it. It never contains data.
* **Links** (`apps/links.py`) — cross-app functions built on the join keys: `contract_contacts`, `org_contracts`,
  `entity_dossier`.
* **Dispatch** (`hub.dispatch`) — the single tool-call path (MCP, CLI, HTTP). Enforces view scoping, blocks
  `sensitive` functions everywhere, and blocks writes unless the hub is started with writes enabled.
* **Hub** (`hub.py`) — stdlib HTTP. Routes by `Host` header to each app's own server (`NTXP_UPSTREAMS`), serves
  `/_ntxp/profile` and `/_ntxp/call` behind `NTXP_HUB_TOKEN` (no token ⇒ every call refused).
* **MCP** (`mcp_server.py`) — `ntxp-platform mcp --view <v>` exposes `profile` and `call`, scoped by view.

## Security rules (enforced + tested)
* **Credentials never cross apps.** apilog's view reaches only apilog; nothing else reaches apilog;
  `get_credentials` is `sensitive` and denied by `dispatch` in every view.
* Unknown `Host` → 404. Missing/incorrect hub token → 401. Cross-app calls are read-only by default.

## Not covered / honest limits
* Contacts' own ASGI server, contracts' and apilog's own servers still run as separate processes (the hub proxies to
  them); they are not merged into one process.
* Schedules and Form Fill code is not in this repo; add an `apps/<name>.py` `AppSpec` for each and they join the profile.
* `contracts.ntxpllc.cloud` / `api.ntxpllc.cloud` DNS + deploy are not done (needs Hostinger access).

## Adding an app
Create `apps/<name>.py` with an `AppSpec` (fields via `dataclass_fields`, functions with handlers), add it to
`registry.load_registry()` and `views.VIEWS`.
