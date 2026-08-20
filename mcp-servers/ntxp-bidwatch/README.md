# NTXP BidWatch MCP Server

A single MCP server that unifies opportunity search across public procurement /
bidding sources — federal, Texas state, local, and university. Built around a
**platform-adapter** design: most targets share a handful of underlying
platforms (Bonfire, Jaggaer, Ionwave), so named sources map onto reusable
adapters.

## Sources

| Source name | Covers | Platform | Auth | Reliability |
|-------------|--------|----------|------|-------------|
| `samgov` | US federal opportunities | SAM.gov API | API key (free) | requires-key |
| `highergov` | Gov contracting intelligence | HigherGov API | API key (paid) | requires-key |
| `bidbanana` | 50-state bid aggregator | BidBanana API | API key (paid) | requires-key |
| `opengov` | OpenGov Procurement (ProcureNow) | OpenGov API gateway | OAuth2 | requires-key |
| `esbd` / `txsmartbuy` | Texas state solicitations | TxSmartBuy NetSuite JSON | none | **verified** |
| `utd` | UT Dallas | Bonfire RSS | none | **verified** |
| `unt` | University of North Texas | Jaggaer | none | requires-browser |
| `texas-am` | Texas A&M System | Jaggaer | none | requires-browser |
| `denton-tx` | City of Denton, TX | Ionwave | none | best-effort |
| `lewisville-tx` | City of Lewisville, TX | Bonfire RSS | none | **verified** |
| `bonfire` | Any Bonfire agency (`org`) | Bonfire RSS | none | **verified** |
| `ionwave` | Any Ionwave agency (`org`) | Ionwave | none | best-effort |
| `demandstar` | DemandStar marketplace | portal | none | requires-browser |
| `planetbids` | PlanetBids portals | portal | none | requires-browser |

**Reliability legend** — `verified`: tested against the live endpoint;
`best-effort`: works but depends on undocumented HTML/JSON that may drift;
`requires-key`: documented API needing a credential; `requires-browser`: the
list is rendered client-side, so the connector returns a verified portal link
instead of fabricating rows; `requires-config`: generic adapter needing a base
URL.

> **On OpenGov:** the public vendor portal (`procurement.opengov.com/portal/<slug>`)
> is a Cloudflare-protected SPA with no clean anonymous JSON. The supported path
> is the official API gateway at `api.procurement.opengov.com/gateway` using
> OAuth2 client-credentials (register an app at developer.opengov.com). Exact
> endpoint paths/scopes live behind the logged-in developer docs, so the token
> URL and search path are configurable (`OPENGOV_SEARCH_PATH`) with sensible
> defaults — confirm them against your OpenGov account.

> **On Jaggaer (UNT, Texas A&M):** their public event lists are rendered
> client-side and can't be read over plain HTTP. Those sources return the portal
> URL; for a machine-readable feed, query `esbd` (Texas institutions cross-post
> formal solicitations there).

## Tools

- `bidwatch_list_sources` — list sources with platform, auth, reliability, and whether each is ready now.
- `bidwatch_search` — search one source: `{ source, keywords?, state?, org?, limit?, verbose? }`.
- `bidwatch_search_all` — aggregate across many sources (defaults to all configured/keyless); per-source errors are reported, not fatal.
- `bidwatch_get_opportunity` — fetch one opportunity by id (currently `esbd`).

All results are normalized to: `source, id, title, agency, status, postedDate, dueDate, url, description, naics, category`.

## Configuration (environment variables)

| Var | Source | Required |
|-----|--------|----------|
| `SAM_GOV_API_KEY` | samgov | for samgov |
| `HIGHERGOV_API_KEY`, `HIGHERGOV_BASE_URL` | highergov | key for highergov |
| `BIDBANANA_API_KEY` | bidbanana | for bidbanana |
| `OPENGOV_CLIENT_ID`, `OPENGOV_CLIENT_SECRET` | opengov | for opengov |
| `OPENGOV_API_BASE`, `OPENGOV_TOKEN_URL`, `OPENGOV_SEARCH_PATH`, `OPENGOV_AUDIENCE` | opengov | optional overrides |
| `PLANETBIDS_BASE_URL` | planetbids | optional |
| `BIDWATCH_TIMEOUT_MS` | all | optional (default 30000) |

## Install & build

```bash
cd mcp-servers/ntxp-bidwatch
npm install
npm run build
```

## Use with Claude Code

```bash
claude mcp add ntxp-bidwatch -e SAM_GOV_API_KEY=<key> -- node ./mcp-servers/ntxp-bidwatch/dist/index.js
```

Keyless sources (`esbd`, `utd`, `lewisville-tx`, generic `bonfire`) work with no
env vars at all.

## Installable bundle (.mcpb)

```bash
bash scripts/pack-mcpb.sh    # produces ntxp-bidwatch.mcpb
```

Open the `.mcpb` in Claude Desktop (it prompts for the optional API keys), or
`npx @anthropic-ai/mcpb install ntxp-bidwatch.mcpb`.

## Notes & caveats

- Undocumented endpoints (ESBD `/api/items`, Ionwave grid) may change shape; the ESBD index mixes open solicitations with awarded contracts and catalog items.
- Respect each source's terms of use and rate limits — SAM.gov enforces daily caps; BidBanana/HigherGov are paid and may restrict redistribution.
