---
name: web-agent-router
description: Gated routing between remote-work tools (Fetch, Firecrawl, Playwright/Puppeteer, Browserbase) via a single minimal-click AskUserQuestion card
---

# Web Agent Router

A decision gate for "which web tool do I use for this," triggered whenever a
prompt references browsing, scraping, crawling, form-filling, or site
testing. The gate is one `AskUserQuestion` call — a real graphical card with
clickable options — not a text negotiation.

## When to run the gate

Run it whenever a remote/web task is referenced and no specific tool was
named. Skip it when:
- The user already named a tool ("use Firecrawl to...", "scrape this with
  Browserbase") — use that tool directly.
- The task is trivially obvious and low-stakes (fetching one well-known
  static doc page) — just use Fetch, don't interrupt for a one-line read.

## The gate

Ask exactly one `AskUserQuestion` call:

```
question: "What kind of remote/web task is this?"
header: "Task shape"
options:
  - label: "Single page, just read it"
    description: "One URL, no clicking/login needed — just get the content"
  - label: "Many pages / crawl a site"
    description: "A whole site, sitemap, or many URLs at once"
  - label: "Automate my own app"
    description: "Local dev — screenshots, visual regression, UI testing"
  - label: "Interact with a third-party site"
    description: "Login, forms, multi-step navigation, or open-ended browsing"
```

## Routing table

| Answer | Tool | Why |
|---|---|---|
| Single page, just read it | **Fetch** (`@modelcontextprotocol/server-fetch`) | Cheapest, fastest, no JS execution — right default for static/docs content |
| Many pages / crawl a site | **Firecrawl** (`firecrawl-mcp`) | Built for bulk crawl → clean markdown/structured data; handles JS rendering internally without an interactive loop |
| Automate my own app | **Playwright MCP** (`@playwright/mcp`) — see version note below | Local browser control for your own app: screenshots, visual regression, a11y checks |
| Interact with a third-party site | **Browserbase** (`@browserbasehq/mcp`, this repo's `plugins/browserbase/`) | Cloud Chrome + Stagehand `act`/`extract`/`observe`/`agent` — handles auth, bot-protected sites, multi-step decisions, session replay |

## Escalation (no second popup)

If the picked tool turns out wrong mid-task, escalate automatically and tell
the user what happened and why — don't ask a second question:

- **Fetch returns an empty/JS-shell page** (React/Vue app, `<div id="root">`
  and nothing else) → escalate to Browserbase `extract` for that one page.
- **Firecrawl crawl hits a login wall or CAPTCHA on a subset of pages** →
  escalate those specific URLs to Browserbase; keep Firecrawl for the rest.
- **Playwright/Puppeteer hits a target that isn't actually your own app**
  (redirected off-domain, third-party auth) → stop and re-run the gate for
  that piece — this one *does* warrant asking again, since it's a different
  task shape than the user described.

## Optional follow-up (only when genuinely ambiguous)

If the answer is "Interact with a third-party site" and the target is a
known bot-protected domain (LinkedIn, Instagram, ticketing sites, major
retailers), ask one follow-up: whether to enable Browserbase Proxies/Verified
(paid tiers) or accept the site may block the free-tier session. This is the
only case where a second card is worth the extra click.

## Capability & version notes — verify before relying on these

Package names and capabilities drift; treat the table above as a starting
point, not gospel. Before a routing decision that hinges on a specific
capability (a tool flag, an auth requirement, whether a package is still
maintained), check the tool's current docs/npm page rather than assuming
this file is current. Last verified: see the date this file was last
updated in git history — if it's more than a few months old, re-verify
before trusting version-specific claims.

- **Fetch** (`@modelcontextprotocol/server-fetch`): official reference
  server, no JS rendering, HTML→markdown only.
- **Firecrawl** (`firecrawl-mcp`): requires `FIRECRAWL_API_KEY`; exposes
  scrape/crawl/map/search/extract-style tools (confirm exact tool names
  against the current package before scripting against them).
- **Playwright MCP** (`@playwright/mcp`): Microsoft's official browser
  automation MCP server. Prefer this over the older
  `@modelcontextprotocol/server-puppeteer` reference server for new setups —
  confirm current maintenance status of both before choosing, since the
  ecosystem here moves fast.
- **Browserbase** (`@browserbasehq/mcp`): 6 tools (`start`, `end`,
  `navigate`, `act`, `observe`, `extract`) per `plugins/browserbase/` in this
  repo, verified directly against the published package.

## Anti-patterns

- Running the gate more than once per task — it's a single click, not a
  wizard.
- Defaulting to Browserbase (or any one tool) for everything because it's
  the most capable — capability isn't free; a crawl job through Browserbase
  wastes cloud session time Firecrawl would do for less.
- Silently switching tools mid-task without telling the user which one you
  ended up using.
