# Web Agent Router

A gate, not another tool. This plugin sits in front of the web/browser tools
already installed in this toolkit — Fetch, Firecrawl, Playwright/Puppeteer,
Browserbase — and makes sure the right one gets picked instead of whichever
one happens to be top of mind.

## How it works

1. A `UserPromptSubmit` hook (`detect-remote-work-intent.js`) watches for any
   prompt that references browsing, scraping, crawling, form-filling, or site
   testing — across all four tools, not just one.
2. If a specific tool was already named in the prompt, the hook says so and
   skips the gate.
3. Otherwise it nudges Claude to run the routing gate: **one**
   `AskUserQuestion` card with four options (single page read / multi-page
   crawl / automate my own app / interact with a third-party site). This
   renders as a real clickable card in the conversation — not a text
   back-and-forth.
4. Your answer maps directly to a tool per `skills/web-agent-router/SKILL.md`,
   which Claude then uses for the task.

## Why a gate instead of a smarter hook

Hooks can only inject text context — they can't render UI or force a tool
choice themselves. The actual "graphical popup" here is Claude's built-in
`AskUserQuestion` tool, which the hook tells Claude to invoke. This means the
gate genuinely blocks progress until you click an answer (Claude waits for
the tool result before continuing), unlike a hook hint alone which Claude
could just ignore.

## Install

```
/plugin marketplace add rohitg00/awesome-claude-code-toolkit
/plugin install web-agent-router
```

You'll also want at least one of the routed-to tools installed —
`plugins/browserbase/` for interactive/third-party sites, plus whichever of
Fetch/Firecrawl/Playwright MCP configs from `mcp-configs/` fit your other
use cases.

## Explicit invocation

Run `/web-agent-router:route` to trigger the gate directly for a task you
describe, instead of waiting for the hook.

## Commands

| Command | What it does |
|---------|-------------|
| `/web-agent-router:route` | Explicitly run the routing gate for a described task |

## Keeping this current

Package names, maintenance status, and capabilities of the underlying tools
change. `skills/web-agent-router/SKILL.md` has a "Capability & version
notes" section flagging what to re-verify — check it periodically (or before
depending on a specific version/flag) rather than trusting it indefinitely.
