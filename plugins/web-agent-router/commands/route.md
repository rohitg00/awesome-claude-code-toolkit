# /web-agent-router:route

Explicitly run the remote-work tool routing gate for a task the user describes,
instead of waiting for the `UserPromptSubmit` hook to nudge toward it. Use this
when the user asks to route/pick a tool directly, or when you want to confirm
routing before a large/expensive job (a big crawl, a paid cloud browser
session).

Full decision logic, the exact question card, and the tool capability/version
table live in `skills/web-agent-router/SKILL.md` — read it before running this
command if it isn't already loaded.

## Steps

1. If the user already named a specific tool (Firecrawl, Browserbase,
   Playwright/Puppeteer, Fetch) in their request, skip the gate — use that
   tool directly and say why you're skipping.
2. Otherwise, ask **one** `AskUserQuestion` call with the 4-way task-shape
   question from the skill (single page read / multi-page crawl / automate my
   own app / interact with a third-party site).
3. Map the answer to a tool per the skill's table, and note any escalation
   path (e.g. a "single page read" that turns out to be a JS-rendered shell
   escalates to Browserbase's `extract`, not a second popup).
4. Before running, check the skill's capability/version notes for anything
   that's changed since it was last verified — if something about the task
   depends on a specific version or capability you're unsure is still
   current, say so and verify (WebSearch/WebFetch the tool's docs or npm
   page) rather than assuming.
5. Run the task with the selected tool and report which tool was used and why,
   so the user can correct the routing if it picked wrong.

## Rules

- The gate is a single click, not an interrogation — never ask more than one
  follow-up question, and only when the first answer is genuinely ambiguous
  (e.g. "third-party site" + known bot-protection needs a proxies/verified
  follow-up).
- Never silently fall back to a different tool without telling the user which
  one you ended up using and why.
