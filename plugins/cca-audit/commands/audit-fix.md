---
description: "6-layer CCA audit+fixing pipeline. Runs 6 parallel auditors on changed files, consolidates findings, implements P1+P2 fixes, re-verifies, and runs architect-reviewer final gate."
---

# CCA Audit + Fix Pipeline

Run the full code audit and auto-fix pipeline on changed files.

## Usage

```
/audit-fix              # audit + fix P1+P2, defer P3 cosmetic
/audit-fix deferred     # second pass to close out P3 items
/audit-fix no-fix       # report only
/audit-fix p1-only      # fix only critical findings
/audit-fix commit 3     # audit last 3 commits
```

## Pipeline

1. Detect changed files + auto-detect language (Python, TS, Go, Rust, Java, Ruby)
2. Launch 6 auditors in parallel (code quality, bugs, security, performance, docs, config)
3. Deduplicate across auditors (same file:line → merge, keep highest severity)
4. Prioritize: P1 Critical → P2 High → P3 cosmetic
5. Auto-fix P1+P2, defer P3 to a second pass
6. Re-verify (runs your test suite + linter)
7. Architect review gate: APPROVED / REVISE / BLOCKED
8. Commit with structured message

## Full Documentation

See the full pipeline at [github.com/GiulioDER/cca-audit](https://github.com/GiulioDER/cca-audit) for:
- 10 agent definitions (code-auditor, bug-auditor, security-auditor, perf-auditor, doc-auditor, env-validator, dep-auditor, fix-planner, architect-reviewer, pr-writer)
- Codex CLI and OpenRouter Python CLI variants
- Non-overlapping scope matrix documentation
