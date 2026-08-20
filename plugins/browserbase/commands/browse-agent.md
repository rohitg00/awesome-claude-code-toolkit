# /browserbase:browse-agent

Run an open-ended browsing agent that navigates the web to accomplish a user-specified task.

## Process

1. Clarify the task: what should the agent find, do, or answer?
2. Determine if a tested browse.sh skill exists: run `browse skills find "<task>"`.
3. If a skill matches, install it with `browse skills add <domain>/<task>` and use it.
4. If no skill matches, create a Stagehand agent script with `env: "BROWSERBASE"`.
5. Use `stagehand.agent()` with a clear instruction describing the goal.
6. Monitor the session on the Browserbase dashboard for live progress.
7. Surface the result and the full session replay link.

## Format

```
Task: <what the agent should accomplish>
Approach: <skill from catalog | custom Stagehand agent>
Result: <data or outcome>
Session: <full browserbase.com/sessions/<id> link>
```

## Rules

- For repeatable tasks, prefer `act`/`extract`/`observe` over `agent` — cheaper and faster.
- Use `agent` only when the steps aren't known in advance.
- Check the browse.sh skill catalog first — tested skills are more reliable than ad-hoc agents.
- Warn about bot-protected sites before running (LinkedIn, Yelp, Instagram, etc.).
- On free-tier accounts, be aware of the $5 Model Gateway token cap — agent runs consume more tokens.
