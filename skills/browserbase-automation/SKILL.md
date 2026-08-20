---
name: browserbase-automation
description: Cloud browser automation with Browserbase and Stagehand — scraping, form filling, agentic browsing, and session management
---

# Browserbase Automation

## Core Concepts

Browserbase runs real Chrome browsers in the cloud. Your code connects to them remotely and drives them — no local browser needed. Stagehand is the automation framework that sits on top, letting you control the browser with natural language instead of CSS selectors.

| Concept | What it does |
|---------|-------------|
| Session | One cloud browser run — watchable live, replayable afterward |
| Stagehand | Natural-language browser control: `act` / `extract` / `observe` / `agent` |
| Fetch | Grab a page's content without spinning up a full browser |
| Search | Find URLs for a query without browsing |
| Contexts | Saved cookies/login state reused across sessions |
| Functions | Deploy automations to run on a schedule or webhook |
| Model Gateway | Call LLMs through the Browserbase key — one key, one bill |
| Proxies | Residential IPs for bot-protected sites (paid, Developer plan+) |
| Verified | Highest-trust anti-bot mode (paid, Scale plan) |

## Stagehand API

### Constructor

```typescript
import { Stagehand } from "@browserbasehq/stagehand";

const stagehand = new Stagehand({
  env: "BROWSERBASE",
  cacheDir: "./stagehand-cache",
});
await stagehand.init();
const page = stagehand.page;
```

- `env: "BROWSERBASE"` routes through cloud browsers
- `cacheDir` persists cached actions across runs for speed
- No `projectId` needed — the API key resolves it

### act — Perform an action

```typescript
await page.act("Click the Search button");
await page.act({
  action: "Type %query% into the search box",
  variables: { query: "cloud browsers" },
});
```

- Keep instructions atomic: one action per call
- Use `%variables%` for dynamic values — string interpolation breaks the cache key

### extract — Pull structured data

```typescript
import { z } from "zod";

const ProductSchema = z.object({
  name: z.string(),
  price: z.string(),
  rating: z.number().optional(),
});

const product = await page.extract({
  instruction: "Extract the product details from this page",
  schema: ProductSchema,
});
```

- Always define a Zod schema for typed, validated output
- The instruction tells Stagehand what to look for; the schema defines the shape

### observe — Discover available actions

```typescript
const actions = await page.observe();
// Returns a list of possible actions on the current page
// Cache these and replay them with act() for speed
```

- Use `observe()` to discover, then replay the cached result on subsequent runs
- Replaying skips LLM inference — 2-3x faster than a fresh `act()` prompt

### agent — Open-ended browsing

```typescript
const result = await stagehand.agent({
  instruction: "Find the cheapest flight from NYC to London next Friday",
});
```

- For tasks where the steps aren't known in advance
- More expensive (more LLM calls) but handles novel workflows

## Speed Optimization

1. **observe → cache → act(cached)**: discover once, replay forever
2. **Set `cacheDir`**: without it, cache never persists across runs
3. **Stable instructions + `%variables%`**: changing the prompt text invalidates the cache
4. **`waitUntil: "domcontentloaded"`**: don't wait for all images/fonts to load
5. **Wait for elements, never `setTimeout`**: use `observe()` to confirm readiness
6. **Reuse sessions during development**: avoid cold starts on every tweak

## Capability Selection

```
Need a full browser? ─── No ──→ Fetch (static content) or Search (URL discovery)
        │
       Yes
        │
Repeatable task? ─── Yes ──→ Stagehand act/extract/observe
        │
       No (open-ended)
        │
        └──→ Stagehand agent (or expose act/extract as tools to your own agent)
```

Layer on: **Contexts** for auth persistence, **Proxies/Verified** for bot-protected sites, **Functions** to deploy, **Model Gateway** for LLM calls.

## Free-Tier Limits

- Model Gateway: $5 of tokens included, then upgrade or bring your own LLM key
- No Proxies or Verified sessions — bot-protected sites may block
- Limited browser time, sessions, and Search/Fetch calls
- If LLM calls start failing on a working script, the $5 cap is likely the cause

## CLI Reference

```bash
browse cloud sessions list          # List recent sessions
browse cloud projects list          # Verify API key / list projects
browse cloud fetch <url>            # Fetch page content without a browser
browse cloud search "<query>"       # Search the web
browse skills find "<task>"         # Search the skill catalog
browse skills add <domain>/<task>   # Install a catalog skill
browse templates list               # List available templates
browse templates clone <slug> <dir> # Clone a template
```

## Docs

- Stagehand: https://docs.browserbase.com/welcome/quickstarts/stagehand
- Sessions: https://docs.browserbase.com/platform/browser/getting-started/create-browser-session
- Fetch: https://docs.browserbase.com/platform/fetch/overview
- Search: https://docs.browserbase.com/platform/search/overview
- Contexts: https://docs.browserbase.com/platform/browser/core-features/contexts
- Functions: https://docs.browserbase.com/platform/runtime/overview
- Model Gateway: https://docs.browserbase.com/platform/model-gateway/overview
- Dashboard: https://www.browserbase.com/sessions
