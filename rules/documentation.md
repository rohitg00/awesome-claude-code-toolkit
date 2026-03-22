# Documentation Rules

## What to Document
- Public API functions: parameters, return types, error conditions, examples.
- Architecture decisions: why a particular approach was chosen (ADRs).
- Setup and installation: prerequisites, steps, common issues.
- Configuration: all options, defaults, environment variables.
- Non-obvious behavior: edge cases, gotchas, workarounds.

## What Not to Document
- Obvious code (getters, setters, simple wrappers).
- Implementation details that change frequently.
- Anything the type system already expresses.
- Temporary workarounds without a tracking issue.

## Keep Docs Current
- Update documentation in the same PR that changes the code.
- Review docs in code review. Stale docs are worse than no docs.
- Use CI to verify that documentation examples compile or run.
- Keep CLAUDE.md or AGENTS.md updated with current project context.

## Documentation Formats
- Inline code comments: explain **why**, not what. One line, placed above the code.
- JSDoc/docstrings: for public APIs. Include parameters, returns, throws, and an example.
- README: installation, quick start, configuration, contribution guidelines.
- CLAUDE.md: project context, conventions, build commands, key architecture decisions.
- ADRs: date, status, context, decision, consequences. Store in `docs/adr/`.

## Style Guidelines
- Use concrete examples, not abstract descriptions.
- Write for the reader who will maintain this code in 6 months.
- Use consistent terminology. Define domain terms in a glossary if needed.
- Keep sentences short. One idea per paragraph.
- Use code blocks with language tags for syntax highlighting.
- Use tables for option lists, comparison matrices, and configuration references.

## README Structure
1. Project name and one-line description.
2. Installation / quick start (copy-paste ready).
3. Usage examples (the most common use case first).
4. Configuration reference.
5. Contributing guidelines.
6. License.
