# Live view — architecture

```
 Google Workspace users ──OAuth (hd=ntxpllc.com)──► contacts.ntxpllc.com  (the APP: single source of interaction)
                                                      │  /            live page, NTXP-DOC-STANDARD 2.1
                                                      │  /api/*       filters · proximity · inline edit · labels · reports · CSV
                                                      │  /mcp        stateless MCP        /carddav  one-way iOS
                                                      ▼
                                   Supabase Postgres (canonical DB; RLS deny-all; council_answers)
                                                      ▲
 Google Sheet (read-only mirror, Apps Script) ────────┘  same /api, same domain-OAuth, 5-min refresh
```
- **Reports** are specs generated server-side (`/api/report`) and rendered by the NTXP document engine
  (`/api/report/render` → PDF/DOCX). Portrait 8.5×11 is the default; the engine's own audit must exit 0 or the render is refused.
- **Consensus of effectiveness**: every council decision is persisted to `council_answers`; `ntxp council-report`,
  the `council_report` MCP tool and the page's Settings panel show decisions, % resolved free by JEV, cost and confidence.
- **UI audit**: `python tools/ui_audit.py <url> <out>` — NTXP-standard conformance, palette, contrast across every
  theme × palette, alignment doctrine, mid-string wraps, 24px targets, responsive overflow, keyboard focus, axe-core.
