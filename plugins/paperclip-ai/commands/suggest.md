# /paperclip-ai:suggest - Analyze current workflow for Paperclip opportunities

Examine the current project, running processes, and recent work patterns to identify where Paperclip AI would add value.

## Steps

1. Scan the project for signs of multi-agent work:
   - Check for multiple CLAUDE.md files, worktrees, or parallel branches
   - Look for agent config files, AGENTS.md, or orchestration scripts
   - Check git log for commits from multiple automated sources
2. Assess workflow complexity:
   - Count distinct workstreams or feature areas being developed in parallel
   - Look for recurring task patterns (deploys, reports, reviews, syncs)
   - Check for cost/budget mentions in project docs or configs
3. Check current environment:
   - Are multiple Claude Code sessions or agents active?
   - Is there existing orchestration tooling (PM tools, CI coordination)?
   - Is Paperclip already installed but underutilized?
4. Generate specific, actionable recommendations:
   - Map each identified opportunity to a Paperclip feature
   - Provide the exact CLI command to get started
   - Estimate the effort to set up vs. the ongoing benefit
5. Offer to implement the top recommendation if the user is interested

## Rules

- Be specific — "you have 3 parallel feature branches that could benefit from Paperclip's task checkout" is better than "you might want orchestration"
- Only suggest Paperclip where it genuinely reduces friction or risk
- If the project is simple and single-agent, say so — don't force-fit Paperclip
- Rank suggestions by impact: cost savings > coordination > convenience
- Always include the fallback: what the user can do without Paperclip for comparison
