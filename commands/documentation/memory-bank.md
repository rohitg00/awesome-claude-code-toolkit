Update the project's CLAUDE.md memory bank with current session learnings.

## Steps

1. Read the existing `CLAUDE.md` (project root) or create one if it does not exist.
2. Analyze the current session to extract:
   - **Decisions made**: Architecture choices, library selections, pattern adoptions.
   - **Problems solved**: Bugs fixed, workarounds discovered, gotchas identified.
   - **Patterns established**: Naming conventions, file organization, coding standards.
   - **Commands discovered**: Useful CLI commands, build steps, debug techniques.
   - **Dependencies**: New packages added and why, version constraints.
3. Categorize learnings into the appropriate CLAUDE.md sections:
   - Project overview and key paths.
   - Build and test commands.
   - Architecture notes.
   - Known issues and workarounds.
   - Session-specific notes.
4. Merge new information without duplicating existing entries.
5. Update the "Last updated" timestamp.
6. Keep the file concise: each entry should be one to two lines.

## Format

```markdown
# Project Memory

## Overview
- Description, key paths, tech stack

## Commands
- `<command>` - what it does

## Architecture
- Key design decisions and patterns

## Known Issues
- Issue description and workaround

## Session Notes
- Last updated: YYYY-MM-DD
- <new learnings from this session>
```

## Rules

- Never remove existing entries unless they are explicitly outdated.
- Keep each entry factual and actionable, not narrative.
- Limit the file to 200 lines; archive old session notes if it grows beyond that.
- Use bullet points for scanability, not paragraphs.
- Store project-specific memory in project root, personal memory in `~/.claude/CLAUDE.md`.
