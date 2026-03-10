---
description: "When the user has the Tycana plugin installed but appears to be new (no items, empty context, or MCP connection issues) — guide them through getting started."
---

# Getting Started with Tycana

This skill activates when a user is new to Tycana or hasn't set up their connection yet.

## Detecting New Users

You'll know a user is new when:
- `get_context` returns empty results or a "No active items found" note
- Tycana MCP tools return connection errors (no account or token not configured)
- The user explicitly says they just installed the plugin or are new to Tycana

## If Tycana Tools Work (account exists, no items)

The user has an account but hasn't captured anything yet. Help them get started:

1. **Don't explain the system.** Don't list features or describe the architecture. Just start using it.

2. **Ask what they're working on.** Simple and direct:
   "What are you working on right now? I'll start tracking it so I can help you plan and prioritize."

3. **Capture 3-5 items from conversation.** As they describe their work, capture items with full metadata — effort, energy, project, relationships. Use the same rich capture behavior as the tycana-productivity skill.

4. **Show them what Tycana does with data.** After capturing a few items:
   "Now that I know what's on your plate, try `/tycana:morning` tomorrow for a daily briefing, or `/tycana:next` when you're not sure what to tackle."

5. **Store any preferences they mention.** If they say things like "I do deep work in the morning" or "I'm off on Fridays," use `remember` to save it.

## If Tycana Tools Don't Work (no account or connection issue)

Guide them to set up their connection:

"Looks like Tycana isn't connected yet. You'll need a Tycana account to use these features."

- **Sign up:** "Head to tycana.com to create an account — there's a free trial."
- **Connect:** "Once you have an account, visit tycana.com/getting-started for connection instructions. If you're using Claude.ai, the connection happens automatically through OAuth. For Claude Code, you can configure it manually with a bearer token."

Don't troubleshoot connection issues beyond this. Point them to the getting-started page.

## Tone

Practical and low-pressure. The user just installed something new — don't overwhelm them with features or philosophy. Just help them capture their first few items and let the value speak for itself.

"I'll remember this across our conversations. Next time you ask what to work on, I'll know."
