# Example: Setting Up a New Project with the Toolkit

A step-by-step walkthrough of configuring a new Next.js project with the
awesome-claude-code-toolkit for maximum productivity.

## 1. Initialize the Project

```bash
pnpm create next-app@latest my-saas-app --typescript --tailwind --app --src-dir
cd my-saas-app
git init && git add -A && git commit -m "Initial Next.js scaffold"
```

## 2. Create CLAUDE.md

Start with a template and customize it for your project:

```bash
cp ~/awesome-claude-code-toolkit/templates/claude-md/fullstack-app.md ./CLAUDE.md
```

Edit `CLAUDE.md` to reflect your actual stack, commands, and project structure.
This file is the single most important artifact for Claude Code productivity.

## 3. Add Rules

Copy relevant rule files into your project's `.claude/rules/` directory:

```bash
mkdir -p .claude/rules
cp ~/awesome-claude-code-toolkit/rules/coding-style.md .claude/rules/
cp ~/awesome-claude-code-toolkit/rules/testing.md .claude/rules/
cp ~/awesome-claude-code-toolkit/rules/security.md .claude/rules/
cp ~/awesome-claude-code-toolkit/rules/api-design.md .claude/rules/
cp ~/awesome-claude-code-toolkit/rules/git-workflow.md .claude/rules/
```

These rules are automatically loaded by Claude Code and applied to all interactions.

## 4. Configure MCP Servers

Copy the appropriate MCP config for your stack:

```bash
cp ~/awesome-claude-code-toolkit/mcp-configs/fullstack.json .claude/mcp.json
```

Edit the config to set your actual database connection string, API keys,
and project paths. Never commit real credentials.

## 5. Set Up Hooks

Copy the hooks configuration for automated quality checks:

```bash
cp -r ~/awesome-claude-code-toolkit/hooks/ .claude/hooks/
```

Key hooks to enable:
- `session-start.js`: Loads context and checks for pending tasks on session start.
- `post-edit-check.js`: Runs linter after file edits to catch issues immediately.
- `pre-push-check.js`: Runs tests before allowing git push.
- `stop-check.js`: Reminds you to commit and document before ending a session.

## 6. Add Contexts

Copy context files for different working modes:

```bash
mkdir -p .claude/contexts
cp ~/awesome-claude-code-toolkit/contexts/dev.md .claude/contexts/
cp ~/awesome-claude-code-toolkit/contexts/review.md .claude/contexts/
cp ~/awesome-claude-code-toolkit/contexts/debug.md .claude/contexts/
cp ~/awesome-claude-code-toolkit/contexts/deploy.md .claude/contexts/
```

Switch contexts during your session with `/context load dev` or `/context load debug`.

## 7. Install Skills (Optional)

If you use SkillKit, install relevant skills:

```bash
npx skillkit install tdd-mastery
npx skillkit install api-design-patterns
npx skillkit install security-hardening
```

## 8. Verify the Setup

Start a Claude Code session and verify everything loads correctly:

```
> What rules, hooks, and MCP servers are active in this project?
```

Claude should list the rules from `.claude/rules/`, the configured hooks,
and the available MCP servers. If anything is missing, check file paths
and permissions.

## 9. First Development Session

With the toolkit configured, start building:

```
> /context load dev
> Let's build the user authentication flow. Plan the implementation first,
  then implement it step by step with tests.
```

The rules guide code style, the hooks enforce quality gates, the MCP servers
provide tool access, and the context shapes Claude's behavior for development work.

## Project Structure After Setup

```
my-saas-app/
  .claude/
    rules/          - Coding standards and conventions
    hooks/          - Automated quality checks
    contexts/       - Working mode definitions
    mcp.json        - MCP server configuration
  src/              - Application source code
  CLAUDE.md         - Project context for Claude Code
  package.json
```
