# Contributing

Thanks for your interest in contributing to Claude Code Toolkit.

## How to Contribute

1. Fork the repository
2. Create a feature branch: `git checkout -b feature/your-feature`
3. Make your changes
4. Test your changes locally
5. Commit with a clear message: `git commit -m "Add new-skill: description"`
6. Push to your fork: `git push origin feature/your-feature`
7. Open a Pull Request

## What to Contribute

- **Plugins** -- New plugins go in `plugins/<plugin-name>/` with a `.claude-plugin/plugin.json` manifest.
- **Agents** -- Agent Markdown files go in the appropriate `agents/<category>/` directory.
- **Skills** -- Skill modules go in `skills/<skill-name>/` with a `SKILL.md` and optional examples.
- **Commands** -- Slash command Markdown files go in `commands/<category>/`.
- **Rules** -- Rule files go in `rules/` as standalone Markdown.
- **Templates** -- CLAUDE.md templates go in `templates/claude-md/`, project starters in `templates/project-starters/`.
- **MCP Configs** -- Configuration files go in `mcp-configs/` as JSON.
- **Hook Scripts** -- Scripts go in `hooks/scripts/` with an update to `hooks/hooks.json`.

## Guidelines

- Keep files focused and single-purpose.
- Use clear, descriptive names.
- Remove code comments that are obvious or redundant.
- Test plugins and hooks before submitting.
- Update the README table if adding a new item to any category.
- No generated attribution footers in files.

## File Naming

- Agents: `kebab-case.md` (e.g., `code-reviewer.md`)
- Commands: `kebab-case.md` matching the slash command name
- Skills: directory name in `kebab-case`
- Rules: `kebab-case.md` describing the rule

## Code of Conduct

Be respectful, constructive, and collaborative. We follow the [Contributor Covenant](https://www.contributor-covenant.org/version/2/1/code_of_conduct/).
