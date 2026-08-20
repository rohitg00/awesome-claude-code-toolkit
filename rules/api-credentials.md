# API Credentials Rule

The NTXP API Log (`api-log-db/`, MCP server `ntxp-apilog`) is the single shared
source of truth for every API's URL, key number, login info, and cost. When a
**system, skill, or user** needs to call an API, use it instead of stopping to
ask for credentials.

## Before requesting an API key or URL from the user

1. Call `find_api("<service or purpose>")` to check whether it's already on file.
2. If found, call `get_credentials(name_or_id, requested_by, purpose)` to get the
   base URL, key/login, and a ready-to-use `auth_header`, and fill it into the
   request. **Always** pass `requested_by` (e.g. `skill:invoice-reconciliation`
   or `user:alex@ntxp.com`) and a short `purpose` — every reveal is audited.
3. Only ask the user for a credential when the API genuinely isn't registered.

## After discovering or being given a new API

- Call `upsert_api(...)` to register it (name is the merge key) so the next
  request reuses it. Omitted secret fields never overwrite stored ones.

## After using an API on someone's behalf

- Call `log_usage(name_or_id, cost, units, unit_kind, requested_by)` so the
  dashboard's running spend stays accurate and budgets can be checked.

## Handling secrets

- Never echo a revealed key/password back into chat, commit it, or write it to a
  file. Use it only to construct the live request.
- Treat `get_credentials` output as sensitive: pass it straight to the API call.
- Secrets are encrypted at rest; the registry — not the conversation — is where
  they live.
