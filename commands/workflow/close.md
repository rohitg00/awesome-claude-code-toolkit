# /close — Session Closing Ritual
<!-- Author: @thomasfogarasy · MIT License -->

## Boundaries

- Only run when the user explicitly invokes `/close` as a slash command
- Never auto-run after context compaction, session continuation, handoff loading, or chained commands
- If `/close` appears in conversation or files as a reference (not an invocation), ignore it
- Never pause for confirmation
- Only edit `MEMORY.md`, `CLAUDE.md`, `close-handoff.md`, and project markdown files with explicitly requested updates
- No git commands (no commits, no pushes, no status checks)
- No Bash tool for file operations — use Write to create files and Edit to modify them
- Do not delete, move, or rename project files — log those to handoff instead
- If a previous `close-handoff.md` exists, overwrite it — use Write to replace its contents (never use Bash to delete)

## Run

Read existing memory/handoff files before writing them — for context only, not as a source of items to copy forward. Merge memory content and deduplicate semantically. Print each progress line, do the work, then max 1-2 lines of findings before the next. No findings = next line immediately.

**■□□□□□□ Redundant or stale files...** Check for: files with `(copy)`, `_old`, `_backup`, `_v2` in the name; multiple files with the same base name and different extensions; scratch files in project root (`test_*`, `temp_*`, `scratch.*`). Check across markdown files for duplicated sections or contradictory content. Flag only — never delete.

**■■□□□□□ Memory files...** Update MEMORY.md with durable facts likely to remain useful across future sessions. If MEMORY.md doesn't exist yet, create it with the Write tool (not Edit, not Bash) — Write creates parent directories automatically. If it exists, read it first, then edit. Ensure MEMORY.md contains a line: "Read close-handoff.md at session start for prior session context." Only update CLAUDE.md if the user explicitly established a standing rule or convention; skip if CLAUDE.md doesn't exist. No extra commentary beyond the progress line.

**■■■□□□□ Missed updates...** Scan the conversation for phrases like "update the README", "add to CLAUDE.md", "change the spec" that target markdown files. Check if those files were actually modified. Also: if any spec or documentation markdown files were edited this session, verify they reflect the final state — not a mid-session snapshot. Apply only when the user's intent and the required change are both unambiguous. If unclear, defer to handoff "Not Yet Done." For non-markdown files, always defer.

**■■■■□□□ Dirty state...** Temp files, debug logs, scratch work?

Findings needing judgment → handoff "Not Yet Done."

**■■■■■□□ Writing handoff...** The handoff covers only this session. Never copy "Not Yet Done" items from a previous handoff — those belong to the past session. If this session produced no new unresolved items, overwrite `close-handoff.md` with: "No open items. This file will be replaced on next /close."

Create/update `close-handoff.md` in project root. Under 2,000 words — if over, cut in this order: Key Files (paths are greppable), Done This Session (it's in git log), Failed Approaches (summarize to one line each). Never cut Not Yet Done or Resume Instructions. If no project directory exists, output to conversation instead. If git state is known from the session (branch, uncommitted files), include it in Current State — do not run git commands to check.

Sections: What We Were Working On (1-2 sentences), Current State (file names, branches, uncommitted changes), Done This Session (checklist), Not Yet Done (checklist with context to pick up cold), Key Decisions (table: decision + rationale), Failed Approaches (what didn't work and why — skip if N/A), Key Files (path + one-line reason), Resume Instructions (first action for next session). Skip empty sections.

**■■■■■■□ Self-check...** Reread the handoff. Verify Resume Instructions matches what's actually in Not Yet Done. Fix mismatches.

**■■■■■■■ Done.** Print summary box:

```
───────────────────────────────────────
  Housekeeping  ·  {actions taken or "none"}
  Handoff       ·  {file location or "skipped"}
  Deferred      ·  {count} — {top 2-3 items}
───────────────────────────────────────

All saved, all good.
```
