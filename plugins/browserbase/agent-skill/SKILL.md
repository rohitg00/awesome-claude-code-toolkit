---
name: browserbase-automation
description: Cloud browser automation with Browserbase and Stagehand — scraping, form filling, agentic browsing, and session management. Use when a task requires interacting with web pages, extracting data from sites, or driving a browser programmatically. Requires BROWSERBASE_API_KEY.
---

# Browserbase Automation Skill

Browserbase runs real Chrome browsers in the cloud. Stagehand drives them with natural
language instead of CSS selectors. This skill covers the API, capability selection,
speed optimization, and free-tier constraints.

## Prerequisites

- `BROWSERBASE_API_KEY` must be set. If missing, tell the user to get one at
  https://browserbase.com/settings or run `/browserbase:setup`.
- No `BROWSERBASE_PROJECT_ID` needed — the API key resolves it automatically.

## Stagehand Quick Reference

### Constructor

```typescript
import { Stagehand } from "@browserbasehq/stagehand";

const stagehand = new Stagehand({
  env: "BROWSERBASE",
  cacheDir: "./stagehand-cache",  // persist cached actions across runs
});
await stagehand.init();
const page = stagehand.page;
```

### act — Perform an action

```typescript
await page.act("Click the Search button");
await page.act({
  action: "Type %query% into the search box",
  variables: { query: "cloud browsers" },
});
```

Keep instructions atomic. Use `%variables%` for dynamic values (string interpolation
breaks the cache key).

### extract — Pull structured data

```typescript
import { z } from "zod";

const product = await page.extract({
  instruction: "Extract the product details",
  schema: z.object({
    name: z.string(),
    price: z.string(),
    rating: z.number().optional(),
  }),
});
```

Always define a Zod schema for typed output.

### observe — Discover available actions

```typescript
const actions = await page.observe();
// Cache these, then replay with act() on subsequent runs — 2-3x faster
```

### agent — Open-ended browsing

```typescript
const result = await stagehand.agent({
  instruction: "Find the cheapest flight from NYC to London next Friday",
});
```

More expensive (more LLM calls), but handles novel workflows where steps aren't
known in advance.

## Speed Optimization

1. **observe → cache → act(cached)** — discover once, replay forever
2. **Set `cacheDir`** — without it cache doesn't persist across runs
3. **Stable instructions + `%variables%`** — changing prompt text invalidates the cache
4. **`waitUntil: "domcontentloaded"`** — don't wait for images/fonts
5. **Wait for elements, never `setTimeout`** — use `observe()` to confirm readiness

## Capability Selection

```
Need a full browser? ─── No ──→ Fetch (static) or Search (URL discovery)
        │
       Yes
        │
Repeatable task? ─── Yes ──→ Stagehand act/extract/observe
        │
       No (open-ended)
        │
        └──→ Stagehand agent (or expose act/extract as tools to your own agent)
```

Layer on: **Contexts** for auth, **Proxies/Verified** for bot-protected sites,
**Functions** to deploy, **Model Gateway** for LLM calls.

## Free-Tier Constraints

- Model Gateway: **$5 of tokens** included, then upgrade or bring your own LLM key
- No Proxies or Verified — bot-protected sites may block
- Limited browser time, sessions, and Search/Fetch calls
- If LLM calls start failing on a working script, the $5 cap is the likely cause
- Leave `MODEL_API_KEY` blank so calls route through Model Gateway on the Browserbase key

## CLI Reference

```bash
browse cloud sessions list          # List recent sessions
browse cloud projects list          # Verify API key
browse cloud fetch <url>            # Fetch page without a browser
browse cloud search "<query>"       # Web search
browse skills find "<task>"         # Search the skill catalog
browse skills add <domain>/<task>   # Install a catalog skill
browse templates list               # List templates
browse templates clone <slug> <dir> # Clone a template
```

## Docs

- Stagehand: https://docs.browserbase.com/welcome/quickstarts/stagehand
- Fetch: https://docs.browserbase.com/platform/fetch/overview
- Search: https://docs.browserbase.com/platform/search/overview
- Contexts: https://docs.browserbase.com/platform/browser/core-features/contexts
- Functions: https://docs.browserbase.com/platform/runtime/overview
- Model Gateway: https://docs.browserbase.com/platform/model-gateway/overview
- Dashboard: https://www.browserbase.com/sessions
