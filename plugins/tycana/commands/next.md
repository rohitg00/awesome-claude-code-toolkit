---
description: "What should I do next? Energy-aware recommendation based on your available time."
argument-hint: "[time: quick | hour | deep] [energy: deep | routine]"
allowed-tools:
  - mcp__tycana__what_next
---

# /tycana:next — What Should I Do Next

Eliminate decision fatigue. Give the user a clear, reasoned recommendation for what to work on right now.

## Process

1. **Parse arguments.** Accept optional time and energy:
   - `/tycana:next` → `available_time="hour", energy="deep"` (defaults)
   - `/tycana:next quick` → `available_time="quick", energy="deep"`
   - `/tycana:next deep routine` → `available_time="deep", energy="routine"`
   - `/tycana:next 30min` → map to `available_time="hour"`
   - `/tycana:next routine` → `available_time="hour", energy="routine"`

   Be flexible with natural language: "quick", "15 min", "30 min" → quick or hour. "couple hours", "afternoon" → deep. "tired", "low energy" → routine.

2. **Get recommendations.** Call `what_next` with parsed parameters.

3. **Present the top recommendation.** Lead with the single best option:
   - What it is and why it's the top pick
   - How long it should take
   - What completing it would unblock (if anything)

4. **Mention alternatives.** Briefly note the other 1-2 options: "If you'd rather do something lighter, the DNS update is a quick routine task."

## Tone

Quick and decisive. The user asked because they don't want to think about it.

**Good:** "The API migration doc — it's medium effort, deep work, and it unblocks the architecture review. Probably 2-3 hours. If you want something lighter, the staging config update is a quick win."

**Bad:** "Based on your current energy level and available time, I have analyzed your task list and generated the following prioritized recommendations..."

## Empty State

If no recommendations:
"Nothing matches your time and energy right now. Want to capture what you're working on, or adjust the filters?"
