# NTXP Contacts — Google Sheet live mirror

A **read-only**, auto-refreshing Sheet mirror of the canonical contacts. The hosted app
(`https://contacts.ntxpllc.cloud`) is the product — the Sheet is for people who want a spreadsheet.

## What you get
- **Live data**: pulls `/api/contacts` (exposed contacts only) every 5 min (opt-in trigger) or on demand.
- **NTXP doc-standard look**: navy title bar, navy-mid header row, two-tone rows (`#F6F3EF`), centred cells with
  paragraph columns left, link-ink emails/phones/LinkedIn, native column filters, frozen header.
- **Buttons / reports** (menu **NTXP Contacts**): *Refresh now*, *Filters & reports…* (sidebar: search, project, role,
  trade, state, label, **proximity in miles**), *Render PDF* of any of the five reports through the **NTXP document engine**
  and save it into the project's folder under **`!Active Projects`** in Drive, *Live auto-refresh*, *Open the live app*.
- **Read-only**: the data range is protected (warning on edit) — edit in the app so changes sync correctly.

## Domain OAuth, enforced twice
1. **This script** refuses to run unless both the effective user and the active user are `@ntxpllc.com`.
2. **The server** accepts only a Google Workspace access token whose `hd` claim is `ntxpllc.com`
   (`remote/auth.py`). The script sends `ScriptApp.getOAuthToken()` as the Bearer token.
3. Share the Sheet **only with the ntxpllc.com domain** (Drive › Share › *Restricted to NTXP LLC*).

## Install (≈5 min, needs a Workspace account)
1. Create a Sheet named **NTXP Contacts — Live Mirror** (domain-restricted sharing).
2. **Extensions › Apps Script**; show `appsscript.json` (Project Settings › *Show manifest file*).
3. Paste `Code.gs`, `Sidebar.html` (File › + › HTML, name it `Sidebar`) and `appsscript.json`.
   *(Or with `clasp`: `clasp create --type sheets --parentId <sheetId> && clasp push` from this folder.)*
4. Optional: Project Settings › Script properties › `NTXP_API` = your server URL (default `https://contacts.ntxpllc.cloud`;
   also update `urlFetchWhitelist` in the manifest if you change it).
5. Reload the Sheet → **NTXP Contacts › Refresh now** → authorize once → **Turn on live auto-refresh**.

## Verified vs. not
- ✅ Logic is unit-tested under Node with stubbed Google services (`node sheets/test/test_code.js`, 11 tests, mutation-checked):
  query building, formula-injection safety, validated hyperlinks, exact domain gate, paging, Drive routing.
- ✅ The endpoints it calls are tested in `tests/test_api.py` on SQLite and PostgreSQL.
- ⚠️ **Not run inside Google's runtime** (needs a real Workspace account). First-run checklist: authorize scopes,
  confirm the server accepts the script's token (`userinfo.email`/`profile` scopes are declared so the `hd` claim is present),
  and confirm `!Active Projects` is visible to the running user.
- The `drive` scope is broad because finding *existing* project folders needs it; narrow it if you only use *NTXP Reports*.
