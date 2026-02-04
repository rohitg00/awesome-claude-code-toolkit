Save a session checkpoint capturing current progress, decisions, and next steps.

## Steps

1. Gather current session state:
   - Run `git diff --stat` to see uncommitted changes.
   - Run `git log --oneline -5` to see recent commits.
   - Check for any running background processes or servers.
2. Summarize work completed in this session:
   - Files created, modified, or deleted.
   - Features implemented or bugs fixed.
   - Tests added or modified.
   - Dependencies installed or updated.
3. Document open questions and decisions pending:
   - Architectural choices that need team input.
   - Unclear requirements that need clarification.
   - Trade-offs being considered.
4. List concrete next steps in priority order.
5. Save the checkpoint to `.claude/checkpoints/<timestamp>.md`.
6. Update `CLAUDE.md` session notes with a brief summary.
7. Stage and commit if there are meaningful uncommitted changes.

## Format

```markdown
# Checkpoint: <timestamp>

## Completed
- <what was accomplished>

## Current State
- Branch: <branch-name>
- Uncommitted changes: <count>
- Tests: <pass/fail status>

## Open Questions
- <question needing resolution>

## Next Steps
1. <highest priority task>
2. <second priority task>
3. <third priority task>

## Context for Next Session
<anything the next session needs to know>
```

## Rules

- Save checkpoints before switching tasks, ending sessions, or before risky operations.
- Keep checkpoint files under 50 lines for quick scanning.
- Include enough context that a new session can resume without re-reading the codebase.
- Never include secrets or credentials in checkpoint files.
- Clean up checkpoint files older than 30 days.
