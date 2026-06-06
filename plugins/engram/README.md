# engram

Persistent memory for Claude Code, stored in your Obsidian vault.

- **SessionEnd** → archives each session to Markdown (`Sessions/` + daily index).
- **SessionStart** → injects the last 3 days of work into the new session.
- **`/recall <topic>`** → searches your whole history with citations.
- Secrets redacted before write; trivial sessions skipped. Zero dependencies.

Vault defaults to `~/claude-code-memory`; override with `ENGRAM_VAULT`.

Full project, CLI, and docs: **https://github.com/nandukmelath/engram** · MIT
