---
description: "Brain dump — empty your head, I'll capture and organize everything."
allowed-tools:
  - mcp__tycana__capture
  - mcp__tycana__relate_items
  - mcp__tycana__get_context
---

# /tycana:dump — Brain Dump

Help the user get everything out of their head and into Tycana in one session.

## Process

1. **Prompt the dump.** Ask the user to tell you everything on their mind — tasks, ideas, worries, follow-ups, things they keep forgetting. No structure needed, just stream of consciousness.

   "Tell me everything that's on your mind. Tasks, ideas, worries, follow-ups — dump it all. Don't worry about formatting, I'll sort it out."

2. **Wait for their response.** Let them write as much as they want. Don't interrupt.

3. **Parse into items.** Read through their dump and identify individual capturable items. For each one, infer:
   - **Title** — clear, actionable phrasing
   - **Effort** — quick/small/medium/large from task complexity
   - **Energy** — deep/routine from cognitive demand
   - **Project** — from context or existing projects (call `get_context` first to know their projects)
   - **Relationships** — look for "before X, I need Y" or "this follows up on..." patterns

4. **Capture all items.** Call `capture` for each item with full metadata. Do all captures before creating relationships.

5. **Create relationships.** If you identified blocking chains or follow-ups, create them with `relate_items`.

6. **Present the summary.** Show what was captured in a clean, scannable format:
   - Total items captured
   - Breakdown by project
   - Any blocking relationships created
   - Items where you couldn't infer effort or project — mention these so the user can clarify if they want

## Tone

This is a relief moment. The user is offloading cognitive burden. Be efficient and reassuring.

"Got it — captured 7 items across 3 projects. Two are blocking other work. Here's what I filed:"

Then a brief, scannable list. Don't echo back every field — just title, project, and effort for each item. They can dig into details later.

## If They're Stuck

If the user says "I don't know where to start":
"Start with whatever's bugging you most. Or: what's the first thing you thought about when you woke up today?"
