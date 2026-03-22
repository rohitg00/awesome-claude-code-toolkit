Run a multi-step workflow by breaking a complex task into coordinated sub-tasks.

## Steps

1. Parse the workflow specification from the argument:
   - Accept a natural language description of the end goal.
   - Or accept a structured plan with explicit steps.
2. Decompose into ordered sub-tasks:
   - Identify dependencies between tasks (which must complete before others start).
   - Determine which tasks can run in parallel.
   - Estimate complexity of each task (small, medium, large).
3. For each sub-task, define:
   - Clear objective and success criteria.
   - Input requirements (files, data, prior task outputs).
   - Expected output (files created, changes made, results).
   - Verification method (test, manual check, build success).
4. Execute tasks in dependency order:
   - Mark each task as pending, in-progress, or complete.
   - Capture output and errors from each step.
   - If a task fails, determine if downstream tasks should be skipped or can proceed.
5. After all tasks complete, run a final verification:
   - Build passes.
   - Tests pass.
   - No regressions introduced.
6. Report the full execution summary.

## Format

```
Workflow: <description>
Tasks: <total> (<completed>/<total>)

| # | Task | Status | Duration | Notes |
|---|------|--------|----------|-------|
| 1 | <task> | done | 2m | <notes> |
| 2 | <task> | done | 5m | <notes> |
| 3 | <task> | failed | 1m | <error> |

Overall: <success/partial/failed>
Duration: <total time>
```

## Rules

- Never execute destructive operations (delete, force push) without explicit confirmation.
- If a critical task fails, stop and report rather than continuing blindly.
- Keep each sub-task focused and independently verifiable.
- Save progress after each completed task so work is not lost on failure.
- Limit workflow to 10 tasks maximum; break larger workflows into phases.
