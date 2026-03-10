---
description: "Honest progress review — what got done, what slipped, patterns worth noting."
argument-hint: "[scope: today | week | month | project:name]"
allowed-tools:
  - mcp__tycana__review
  - mcp__tycana__get_context
---

# /tycana:review — Progress Review

Give the user an honest, conversational assessment of how their work is going.

## Process

1. **Determine scope.** Parse the argument:
   - No argument or "week" → `scope="this_week", focus="full"`
   - "today" → `scope="today", focus="full"`
   - "month" → `scope="this_month", focus="full"`
   - "project:name" → `scope="project:{name}", focus="full"`

2. **Get the review.** Call `review` with the determined scope and `focus="full"`. **Determine today's date and day of week** from the `period.until` timestamp — reference the correct day throughout the review.

3. **Get current context.** Call `get_context(scope="this_week")` for stale items and project health.

4. **Present the narrative review:**

   - **What got done** — celebrate completions. Be specific: "You closed out 6 items this week including the cert renewal that was dragging."
   - **What slipped** — honest, not punitive. "The API docs slipped past their due date. Want to reschedule or drop it?"
   - **Patterns worth noting** — velocity trends, productive days, slip rate. Weave in naturally: "You tend to knock out the most on Tuesdays. This week was no exception."
   - **Stale items** — things that haven't moved. "The capacity planning task hasn't been touched in 2 weeks. Still relevant?"
   - **One forward-looking thought** — something useful for next week. "You've got a clear Monday — good time to tackle the architecture doc while nothing else is pressing."

## Tone

Honest self-assessment is hard. Most people either ignore their task list or feel guilty about it. Be the colleague who gives a judgment-free "here's how it's actually going" with real data.

**Good:** "Solid week. You cleared 8 items, mostly in infrastructure. The platform project is quiet though — nothing moved there since last Monday."

**Bad:** "Weekly Performance Summary: Total completed: 8. Completion rate: 72%. Projects with activity: 1/3."

## Empty State

If there's not enough data:
"Not enough activity yet to give a meaningful review. Use Tycana for a few days and I'll have real patterns to share."
