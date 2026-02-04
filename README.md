# Claude Code Toolkit

**The complete developer's toolkit for Claude Code -- plugins, agents, skills, commands, hooks, rules, templates, and setup guides.**

[![Awesome](https://cdn.rawgit.com/sindresorhus/awesome/d7305f38d29fed78fa85652e3a63e154dd8e8829/media/badge.svg)](https://github.com/sindresorhus/awesome)
[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)
[![PRs Welcome](https://img.shields.io/badge/PRs-welcome-brightgreen.svg)](CONTRIBUTING.md)
[![Last Updated](https://img.shields.io/badge/Last%20Updated-Feb%202026-orange.svg)](#)

---

## Quick Install

**Plugin marketplace** (recommended):

```bash
/plugin marketplace add rohitg00/awesome-claude-code-toolkit
```

**Manual clone:**

```bash
git clone https://github.com/rohitg00/awesome-claude-code-toolkit.git ~/.claude/plugins/claude-code-toolkit
```

**One-liner:**

```bash
curl -fsSL https://raw.githubusercontent.com/rohitg00/awesome-claude-code-toolkit/main/setup/install.sh | bash
```

---

## Table of Contents

- [Plugins](#plugins)
- [Agents](#agents)
- [Skills](#skills)
- [Commands](#commands)
- [Hooks](#hooks)
- [Rules](#rules)
- [Templates](#templates)
- [MCP Configs](#mcp-configs)
- [Setup](#setup)
- [Contributing](#contributing)
- [License](#license)

---

## Plugins

Six production-ready plugins that extend Claude Code with domain-specific capabilities.

| Plugin | Description |
|--------|-------------|
| [smart-commit](plugins/smart-commit/) | Analyzes diffs and generates conventional commit messages with scope detection, breaking change flags, and co-author attribution. |
| [code-guardian](plugins/code-guardian/) | Real-time code quality enforcement. Runs linting, complexity analysis, and security checks before every commit. |
| [deploy-pilot](plugins/deploy-pilot/) | End-to-end deployment orchestration. Supports Docker, Kubernetes, Vercel, AWS, and custom pipelines. |
| [api-architect](plugins/api-architect/) | Generates OpenAPI specs, route handlers, validation schemas, and client SDKs from natural language descriptions. |
| [perf-profiler](plugins/perf-profiler/) | Identifies performance bottlenecks. Profiles memory, CPU, bundle size, and database queries with actionable recommendations. |
| [doc-forge](plugins/doc-forge/) | Generates documentation from code. Produces READMEs, API references, changelogs, and architecture decision records. |

### Installing a Plugin

```bash
/plugin install claude-code-toolkit@smart-commit
```

Or install all plugins at once:

```bash
/plugin install claude-code-toolkit
```

---

## Agents

Twenty-two specialized agents organized into five categories. Each agent is a Markdown file that defines a persona, system instructions, and tool access patterns for Claude Code.

### Core Development

| Agent | File | Purpose |
|-------|------|---------|
| Architect | `agents/core-development/architect.md` | System design, component boundaries, dependency decisions |
| Implementer | `agents/core-development/implementer.md` | Feature implementation with best practices and error handling |
| Debugger | `agents/core-development/debugger.md` | Root cause analysis, step-through debugging, fix verification |
| Refactorer | `agents/core-development/refactorer.md` | Code restructuring while preserving behavior and test coverage |

### Language Experts

| Agent | File | Purpose |
|-------|------|---------|
| TypeScript | `agents/language-experts/typescript.md` | Type-safe patterns, generics, module design, build config |
| Python | `agents/language-experts/python.md` | Pythonic patterns, packaging, type hints, async patterns |
| Rust | `agents/language-experts/rust.md` | Ownership, lifetimes, trait design, unsafe boundaries |
| Go | `agents/language-experts/go.md` | Interfaces, goroutines, error handling, module structure |

### Infrastructure

| Agent | File | Purpose |
|-------|------|---------|
| Docker | `agents/infrastructure/docker.md` | Multi-stage builds, compose files, image optimization |
| Kubernetes | `agents/infrastructure/kubernetes.md` | Manifests, Helm charts, operators, cluster troubleshooting |
| CI/CD | `agents/infrastructure/cicd.md` | Pipeline design for GitHub Actions, GitLab CI, CircleCI |
| Cloud | `agents/infrastructure/cloud.md` | AWS, GCP, Azure resource provisioning and IaC patterns |

### Quality Assurance

| Agent | File | Purpose |
|-------|------|---------|
| Test Writer | `agents/quality-assurance/test-writer.md` | Unit, integration, and E2E test generation with high coverage |
| Code Reviewer | `agents/quality-assurance/code-reviewer.md` | PR review with security, performance, and maintainability focus |
| Security Auditor | `agents/quality-assurance/security-auditor.md` | Vulnerability scanning, dependency audit, OWASP compliance |
| Accessibility | `agents/quality-assurance/accessibility.md` | WCAG compliance, screen reader testing, ARIA patterns |

### Orchestration

| Agent | File | Purpose |
|-------|------|---------|
| Planner | `agents/orchestration/planner.md` | Breaks down tasks into subtasks with dependency ordering |
| Reviewer | `agents/orchestration/reviewer.md` | Reviews agent outputs, ensures consistency across deliverables |
| Coordinator | `agents/orchestration/coordinator.md` | Routes work between agents and manages handoffs |
| Summarizer | `agents/orchestration/summarizer.md` | Compresses context, generates session summaries, extracts learnings |

### Using Agents

Reference an agent in your `CLAUDE.md`:

```markdown
## Agents
- Use `agents/core-development/architect.md` for system design tasks
- Use `agents/quality-assurance/code-reviewer.md` for PR reviews
```

Or invoke directly:

```
/agent architect "Design a notification system with email, SMS, and push channels"
```

---

## Skills

Ten skill modules that teach Claude Code domain-specific patterns and best practices. Each skill includes rules, examples, and anti-patterns.

| Skill | Directory | What It Teaches |
|-------|-----------|-----------------|
| TDD Mastery | `skills/tdd-mastery/` | Red-green-refactor, test-first design, mocking strategies, coverage targets |
| API Design Patterns | `skills/api-design-patterns/` | RESTful conventions, versioning, pagination, error responses, HATEOAS |
| Database Optimization | `skills/database-optimization/` | Query planning, indexing strategies, N+1 prevention, connection pooling |
| Frontend Excellence | `skills/frontend-excellence/` | Component architecture, state management, accessibility, performance budgets |
| Security Hardening | `skills/security-hardening/` | Input validation, auth patterns, secrets management, CSP headers |
| DevOps Automation | `skills/devops-automation/` | Infrastructure as code, GitOps, monitoring, incident response |
| Continuous Learning | `skills/continuous-learning/` | Session summaries, learning logs, pattern extraction, memory management |
| React Patterns | `skills/react-patterns/` | Hooks, server components, suspense, error boundaries, render optimization |
| Python Best Practices | `skills/python-best-practices/` | Type hints, dataclasses, async/await, packaging, virtual environments |
| Go Idioms | `skills/golang-idioms/` | Error handling, interfaces, concurrency patterns, project layout |

### Installing a Skill

```bash
npx skillkit install claude-code-toolkit/tdd-mastery
```

---

## Commands

Twenty-one slash commands organized into seven categories. Drop these into your project's `.claude/commands/` directory.

### Git Commands

| Command | File | Description |
|---------|------|-------------|
| `/commit` | `commands/git/commit.md` | Generate conventional commit from staged changes |
| `/pr` | `commands/git/pr.md` | Create a pull request with summary, test plan, and labels |
| `/changelog` | `commands/git/changelog.md` | Generate changelog from commit history |

### Testing Commands

| Command | File | Description |
|---------|------|-------------|
| `/test` | `commands/testing/test.md` | Generate tests for the current file or function |
| `/coverage` | `commands/testing/coverage.md` | Analyze test coverage and suggest missing tests |
| `/e2e` | `commands/testing/e2e.md` | Generate end-to-end test scenarios |

### Architecture Commands

| Command | File | Description |
|---------|------|-------------|
| `/design` | `commands/architecture/design.md` | Create a system design document |
| `/adr` | `commands/architecture/adr.md` | Write an Architecture Decision Record |
| `/diagram` | `commands/architecture/diagram.md` | Generate Mermaid diagrams from code structure |

### Documentation Commands

| Command | File | Description |
|---------|------|-------------|
| `/readme` | `commands/documentation/readme.md` | Generate or update README from project analysis |
| `/api-docs` | `commands/documentation/api-docs.md` | Generate API documentation from route handlers |
| `/onboard` | `commands/documentation/onboard.md` | Create onboarding guide for new contributors |

### Security Commands

| Command | File | Description |
|---------|------|-------------|
| `/audit` | `commands/security/audit.md` | Run security audit on dependencies and code |
| `/secrets` | `commands/security/secrets.md` | Scan for leaked secrets and credentials |
| `/csp` | `commands/security/csp.md` | Generate Content Security Policy headers |

### Refactoring Commands

| Command | File | Description |
|---------|------|-------------|
| `/simplify` | `commands/refactoring/simplify.md` | Reduce complexity of the current file |
| `/extract` | `commands/refactoring/extract.md` | Extract function, component, or module |
| `/rename` | `commands/refactoring/rename.md` | Rename symbol across the codebase |

### DevOps Commands

| Command | File | Description |
|---------|------|-------------|
| `/dockerize` | `commands/devops/dockerize.md` | Generate Dockerfile and compose files |
| `/deploy` | `commands/devops/deploy.md` | Deploy to configured environment |
| `/monitor` | `commands/devops/monitor.md` | Set up monitoring and alerting |

### Using Commands

Copy to your project:

```bash
cp -r commands/ .claude/commands/
```

Then invoke in Claude Code:

```
/commit
/test src/utils/parser.ts
/audit
```

---

## Hooks

Production-ready hooks configuration with companion scripts. Hooks run automatically at specific points in the Claude Code lifecycle.

### hooks.json

Place in your project's `.claude/` directory:

```json
{
  "hooks": {
    "PreToolUse": [
      {
        "matcher": "Write|Edit",
        "command": "node hooks/scripts/quality-gate.js"
      }
    ],
    "PostToolUse": [
      {
        "matcher": "Write|Edit",
        "command": "node hooks/scripts/post-edit-check.js"
      }
    ],
    "SessionStart": [
      {
        "matcher": "",
        "command": "node hooks/scripts/session-start.js"
      }
    ],
    "SessionEnd": [
      {
        "matcher": "",
        "command": "node hooks/scripts/session-end.js"
      }
    ],
    "Stop": [
      {
        "matcher": "",
        "command": "node hooks/scripts/wrap-up.js"
      }
    ]
  }
}
```

### Hook Scripts

| Script | Trigger | Purpose |
|--------|---------|---------|
| `quality-gate.js` | PreToolUse (Write/Edit) | Validates code before file writes -- checks syntax, lint rules, complexity |
| `post-edit-check.js` | PostToolUse (Write/Edit) | Runs tests related to modified files, verifies no regressions |
| `session-start.js` | SessionStart | Loads project context, checks for pending tasks, sets up environment |
| `session-end.js` | SessionEnd | Saves session summary, updates learning log, cleans temp files |
| `wrap-up.js` | Stop | Captures learnings, suggests next steps, generates session report |

### Installing Hooks

```bash
cp hooks/hooks.json .claude/hooks.json
cp -r hooks/scripts/ .claude/hooks/scripts/
```

---

## Rules

Eight coding rules that enforce consistent patterns across your codebase. Add these to your `.claude/rules/` directory or reference them in `CLAUDE.md`.

| Rule | File | What It Enforces |
|------|------|-----------------|
| No Dead Code | `rules/no-dead-code.md` | Remove unused imports, variables, functions, and unreachable code |
| Error Handling | `rules/error-handling.md` | Always handle errors explicitly, no empty catch blocks, typed errors |
| Naming Conventions | `rules/naming-conventions.md` | Consistent naming: camelCase functions, PascalCase types, UPPER_SNAKE constants |
| File Organization | `rules/file-organization.md` | One component per file, consistent directory structure, barrel exports |
| Type Safety | `rules/type-safety.md` | No `any` types, strict null checks, exhaustive switch statements |
| Testing Standards | `rules/testing-standards.md` | Test file co-location, descriptive test names, arrange-act-assert pattern |
| Documentation | `rules/documentation.md` | JSDoc for public APIs, inline comments for complex logic only |
| Security Defaults | `rules/security-defaults.md` | Parameterized queries, input sanitization, no secrets in code |

### Using Rules

```bash
cp -r rules/ .claude/rules/
```

Or reference in `CLAUDE.md`:

```markdown
## Rules
- Follow all rules in `.claude/rules/`
```

---

## Templates

Starter templates for `CLAUDE.md` configuration and project scaffolding.

### CLAUDE.md Templates

| Template | File | Use Case |
|----------|------|----------|
| Minimal | `templates/claude-md/minimal.md` | Small projects, scripts, quick prototypes |
| Standard | `templates/claude-md/standard.md` | Most projects -- covers preferences, rules, workflows |
| Enterprise | `templates/claude-md/enterprise.md` | Large codebases with team standards, compliance, multi-repo setup |
| Monorepo | `templates/claude-md/monorepo.md` | Monorepo with multiple packages, shared configs, workspace conventions |

### Project Starters

| Starter | Directory | Stack |
|---------|-----------|-------|
| TypeScript API | `templates/project-starters/ts-api/` | Node.js + Express + TypeScript + Prisma + Jest |
| React App | `templates/project-starters/react-app/` | Vite + React + TypeScript + Tailwind + Vitest |
| Python Service | `templates/project-starters/python-service/` | FastAPI + SQLAlchemy + Pytest + Docker |
| CLI Tool | `templates/project-starters/cli-tool/` | Node.js + Commander + TypeScript + ESBuild |

### Using Templates

```bash
cp templates/claude-md/standard.md CLAUDE.md
```

---

## MCP Configs

Curated Model Context Protocol server configurations ready to drop into your `claude_desktop_config.json` or project settings.

| Config | File | Servers Included |
|--------|------|-----------------|
| Full Stack | `mcp-configs/fullstack.json` | Filesystem, GitHub, Postgres, Redis, Browser |
| Kubernetes | `mcp-configs/kubernetes.json` | kubectl-mcp-server, Helm, Docker |
| Data Science | `mcp-configs/data-science.json` | Jupyter, SQLite, Filesystem, Python REPL |
| Frontend | `mcp-configs/frontend.json` | Browser, Filesystem, Figma, Storybook |
| DevOps | `mcp-configs/devops.json` | AWS, Docker, GitHub, Terraform, Monitoring |

### Using MCP Configs

Copy the relevant config into your Claude Desktop settings:

```bash
cat mcp-configs/fullstack.json
```

Then merge into `~/.claude/claude_desktop_config.json`.

---

## Setup

Onboarding scripts for setting up Claude Code on a new machine or project.

| Script | File | Purpose |
|--------|------|---------|
| Install | `setup/install.sh` | Full toolkit installation -- clones repo, symlinks configs, installs plugins |
| Project Init | `setup/project-init.sh` | Initialize Claude Code in an existing project -- generates CLAUDE.md, hooks, rules |
| Doctor | `setup/doctor.sh` | Diagnose Claude Code setup issues -- checks paths, permissions, versions |

### Running Setup

```bash
bash setup/install.sh          # install everything
bash setup/project-init.sh     # set up current project
bash setup/doctor.sh           # check your setup
```

---

## Project Structure

```
claude-code-toolkit/
  plugins/
    smart-commit/          # Conventional commit generator
    code-guardian/          # Code quality enforcement
    deploy-pilot/          # Deployment orchestration
    api-architect/         # API design and generation
    perf-profiler/         # Performance analysis
    doc-forge/             # Documentation generator
  agents/
    core-development/      # Architect, Implementer, Debugger, Refactorer
    language-experts/      # TypeScript, Python, Rust, Go
    infrastructure/        # Docker, Kubernetes, CI/CD, Cloud
    quality-assurance/     # Test Writer, Code Reviewer, Security, A11y
    orchestration/         # Planner, Reviewer, Coordinator, Summarizer
  skills/
    tdd-mastery/           # Test-driven development
    api-design-patterns/   # REST and GraphQL patterns
    database-optimization/ # Query and schema optimization
    frontend-excellence/   # UI component patterns
    security-hardening/    # Application security
    devops-automation/     # Infrastructure automation
    continuous-learning/   # Session memory management
    react-patterns/        # React-specific patterns
    python-best-practices/ # Python-specific patterns
    golang-idioms/         # Go-specific patterns
  commands/
    git/                   # commit, pr, changelog
    testing/               # test, coverage, e2e
    architecture/          # design, adr, diagram
    documentation/         # readme, api-docs, onboard
    security/              # audit, secrets, csp
    refactoring/           # simplify, extract, rename
    devops/                # dockerize, deploy, monitor
  hooks/
    hooks.json             # Hook configuration
    scripts/               # Hook handler scripts
  rules/                   # 8 coding rules
  templates/
    claude-md/             # CLAUDE.md templates
    project-starters/      # Project scaffolding
  mcp-configs/             # MCP server configurations
  setup/                   # Installation and onboarding scripts
```

---

## Contributing

Contributions are welcome. See [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines.

## License

[MIT](LICENSE)
