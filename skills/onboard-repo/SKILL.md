---
name: onboard-repo
description: Use at the start of work in an unfamiliar repository — produces a fast, accurate mental model (stack, architecture, entry points, conventions, risks) before any code changes.
user-invocable: true
argument: Optional focus area (e.g. "the payment flow") — defaults to the whole repo
---

# Onboard a repository

Goal: in one pass, understand a repo well enough to make safe changes — without reading every file.

## Steps
1. **Shape.** Read README*, CLAUDE.md/AGENTS.md, package.json/pyproject.toml/go.mod, and any /docs. Note stack, scripts, conventions.
2. **Entry points.** Find where execution starts (main, server.*, index.*, CLI bin, route registration). Trace one request/command end to end.
3. **Map layers.** entry → routing/handlers → business logic → storage/external. Write a 5-line map.
4. **Conventions.** Skim 3–4 representative files. Capture naming, error handling, test style, module org — match these later.
5. **Risks.** Note fragile/critical paths (payments, auth, data writes, deploys) and anything TODO/FIXME/HACK.
6. **Verify how.** Find test/build/lint commands and the *smallest relevant gate* for a typical change.

## Output
A short brief: STACK / RUN-TEST-BUILD / ARCHITECTURE (5 lines) / CONVENTIONS / DO-NOT-TOUCH / SMALLEST GATE.
Stop here — do not change code during onboarding. The brief is the deliverable.

## Anti-patterns this prevents
- Editing before understanding (confident-but-wrong changes)
- Reading the whole repo file by file (slow, no synthesis)
- Skipping the "how do I verify" question until after the change

> Maintained at [frohsinnllc/claude-code-onboard-repo](https://github.com/frohsinnllc/claude-code-onboard-repo) — improvements land there first.
