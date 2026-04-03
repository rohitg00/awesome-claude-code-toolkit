# Claude Code Toolkit

**The most comprehensive toolkit for Claude Code -- 135 agents, 35 curated skills (+400,000 via [SkillKit](https://agenstskills.com)), 42 commands, 176+ plugins, 20 hooks, 15 rules, 7 templates, 13 MCP configs, 26 companion apps, 51 ecosystem entries, and more.**

[![Awesome](https://cdn.rawgit.com/sindresorhus/awesome/d7305f38d29fed78fa85652e3a63e154dd8e8829/media/badge.svg)](https://github.com/sindresorhus/awesome)
[![License: Apache-2.0](https://img.shields.io/badge/License-Apache%202.0-blue.svg)](LICENSE)
[![PRs Welcome](https://img.shields.io/badge/PRs-welcome-brightgreen.svg)](CONTRIBUTING.md)
[![Last Updated](https://img.shields.io/badge/Last%20Updated-Mar%202026-orange.svg)](#)
[![Files](https://img.shields.io/badge/Files-850+-blueviolet.svg)](#project-structure)

<a href="https://star-history.com/#rohitg00/awesome-claude-code-toolkit&Date">
  <picture>
    <source media="(prefers-color-scheme: dark)" srcset="https://api.star-history.com/svg?repos=rohitg00/awesome-claude-code-toolkit&type=Date&theme=dark" />
    <source media="(prefers-color-scheme: light)" srcset="https://api.star-history.com/svg?repos=rohitg00/awesome-claude-code-toolkit&type=Date" />
    <img alt="Star History Chart" src="https://api.star-history.com/svg?repos=rohitg00/awesome-claude-code-toolkit&type=Date" width="600" />
  </picture>
</a>

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

- [Plugins](#plugins) (176+)
- [Agents](#agents) (135)
- [Skills](#skills) (35 curated + 28 community)
- [Commands](#commands) (42)
- [Hooks](#hooks) (20 scripts)
- [Rules](#rules) (15)
- [Templates](#templates) (7)
- [MCP Configs](#mcp-configs) (13)
- [Contexts](#contexts) (5)
- [Examples](#examples) (3)
- [Companion Apps & GUIs](#companion-apps--guis)
- [Ecosystem](#ecosystem)
- [Setup](#setup)
- [Resources](#resources)
- [Related Awesome Lists](#related-awesome-lists)
- [Contributing](#contributing)

---

## Plugins

Over 176 production-ready plugins that extend Claude Code with domain-specific capabilities.

### Featured

| Plugin | Stars | Description |
|--------|-------|-------------|
| [pro-workflow](https://github.com/rohitg00/pro-workflow) | 1,400+ | Battle-tested Claude Code workflows from power users. Self-correcting memory, parallel worktrees, wrap-up rituals, 8 hook types, 5 agents, and the 80/20 AI coding ratio. Install: `/plugin marketplace add rohitg00/pro-workflow` |
| [everything-claude-code](https://github.com/affaan-m/everything-claude-code) | 78,600+ | The agent harness performance optimization system. Skills, instincts, memory, security, and research-first development for Claude Code, Codex, OpenCode, Cursor, and beyond. |
| [gstack](https://github.com/garrytan/gstack) | 15,000+ | Garry Tan's exact Claude Code setup: 6 opinionated tools that serve as CEO, Eng Manager, Release Manager, and QA Engineer. 15K+ stars in 5 days. |

### All Plugins

| Plugin | Description |
|--------|-------------|
| [skills-janitor](https://github.com/khendzel/skills-janitor) | Audit, deduplicate, check, fix, and track usage of your Claude Code skills. 9 slash commands, zero dependencies |
| [aws-cost-saver](https://github.com/prajapatimehul/aws-cost-saver) | AWS cost optimization scanner with 173 automated checks, ML-powered rightsizing, and Zero Hallucination Pricing - Real result: 60% cost reduction |
| [claude-agentic-coding-playbook](https://github.com/john-wilmes/claude-agentic-coding-playbook) | Evidence-based practices for LLM-assisted development -- hooks, skills, scripts, and a best-practices guide with 58 citations. Includes 19+ guard/lifecycle hooks, investigation workflow, fleet indexing, and claude-loop for autonomous task queues. |
| [claude-code-mcp](https://github.com/steipete/claude-code-mcp) | Run Claude Code as a one-shot MCP server -- an agent in your agent. Permissions bypassed automatically. By Peter Steinberger. 1,100+ stars |
| [claude-code-system-prompts](https://github.com/Piebald-AI/claude-code-system-prompts) | Extracted system prompts from Claude Code -- 18 builtin tool descriptions, sub-agent prompts, utility prompts. Updated for each release. 5,900+ stars |
| [claude-context](https://github.com/zilliztech/claude-context) | Semantic code search MCP server by Zilliz (Milvus creators). Hybrid BM25 + dense vector search. ~40% token reduction. 5,600+ stars |
| [claude-cost-optimizer](https://github.com/Sagargupta16/claude-cost-optimizer) | Save 30-60% on Claude Code costs -- 6 deep-dive guides, 15 ranked strategies, 12 CLAUDE.md templates, token estimator, usage analyzer, and copy-paste configs |
| [fractal](https://github.com/rmolines/fractal) | Recursive project management for Claude Code. Decomposes goals into predicates, works the riskiest piece first, and re-evaluates as it learns |
| [a11y-audit](plugins/a11y-audit/) | Full accessibility audit with WCAG compliance checking |
| [accessibility-checker](plugins/accessibility-checker/) | Scan for accessibility issues and fix ARIA attributes in web applications |
| [adr-writer](plugins/adr-writer/) | Architecture Decision Records authoring and management |
| [ai-prompt-lab](plugins/ai-prompt-lab/) | Improve and test AI prompts for better Claude Code interactions |
| [analytics-reporter](plugins/analytics-reporter/) | Generate analytics reports and dashboard configurations from project data |
| [android-developer](plugins/android-developer/) | Android and Kotlin development with Jetpack Compose |
| [api-architect](plugins/api-architect/) | API design, documentation, and testing with OpenAPI spec generation |
| [api-benchmarker](plugins/api-benchmarker/) | API endpoint benchmarking and performance reporting |
| [api-reference](plugins/api-reference/) | API reference documentation generation from source code |
| [api-tester](plugins/api-tester/) | Test API endpoints and run load tests against services |
| [aws-helper](plugins/aws-helper/) | AWS service configuration and deployment automation |
| [azure-helper](plugins/azure-helper/) | Azure service configuration and deployment automation |
| [backend-architect](plugins/backend-architect/) | Backend service architecture design with endpoint scaffolding |
| [bug-detective](plugins/bug-detective/) | Debug issues systematically with root cause analysis and execution tracing |
| [Bouncer](https://github.com/buildingopen/bouncer) | Independent quality gate that uses Gemini to audit Claude Code's output. Includes Stop hook (automatic), quick audit skill, and deep audit with full tool access. One-liner install. |
| [ccmanager](https://github.com/kbwo/ccmanager) | Coding agent session manager supporting Claude Code, Gemini CLI, Codex, Cursor, Copilot, Cline, OpenCode, Kimi CLI. Smart auto-approval via Haiku, devcontainer support. 940+ stars |
| [ccpm](https://github.com/automazeio/ccpm) | Project management using GitHub Issues + Git worktrees for parallel agent execution. Issue-analyze, epic-start, epic-merge commands. 7,600+ stars |
| [ccusage](https://github.com/ryoppippi/ccusage) | CLI for analyzing Claude Code/Codex usage from local JSONL files. Daily, monthly, session, billing-window reports. Offline, zero API calls. 11,500+ stars |
| [bundle-analyzer](plugins/bundle-analyzer/) | Frontend bundle size analysis and tree-shaking optimization |
| [chief](https://github.com/MiniCodeMonkey/chief) | CLI that wraps Claude Code in a loop. Define a PRD, run chief, go do anything else. Commits after each task, picks up where it left off. Homebrew installable. 380+ stars |
| [changelog-gen](plugins/changelog-gen/) | Generate changelogs from git history with conventional commit parsing |
| [changelog-writer](plugins/changelog-writer/) | Detailed changelog authoring from git history and PRs |
| [ci-debugger](plugins/ci-debugger/) | Debug CI/CD pipeline failures and fix configurations |
| [claude-hooks-mastery](https://github.com/disler/claude-code-hooks-mastery) | Complete mastery guide for Claude Code hooks -- UV single-file Python scripts, sub-agents, meta-agent, team-based validation, AI-generated audio feedback. 3,300+ stars |
| [claude-mem](https://github.com/thedotmack/claude-mem) | Automatically captures everything Claude does, compresses with AI, injects relevant context into future sessions. SQLite + full-text search. 35,900+ stars |
| [claude-notifications-go](https://github.com/777genius/claude-notifications-go) | Cross-platform smart notifications -- 6 types, click-to-focus, context analysis, webhooks. Single Go binary, zero deps. 340+ stars |
| [claude-scaffold](https://github.com/pyramidheadshark/claude-scaffold) | npx CLI that deploys CLAUDE.md, hooks, and 18 domain skills to any repository in one command. Skills auto-activate via hooks based on project context. Cross-repo sync via `update --all`. Install: `npx claude-scaffold init` |
| [claude-recap](https://github.com/hatawong/claude-recap) | Per-topic session memory using Shell hooks — archives each conversation topic as a separate Markdown summary. Two hooks, bash + Node.js, 100% local |
| [claude-rank](https://github.com/Houseofmvps/claude-rank) | SEO/GEO/AEO audit plugin — tells you why AI won't cite your site, then auto-fixes robots.txt, sitemap.xml, llms.txt, and JSON-LD. 170+ rules across 10 scanners, zero config |
| [claude-sounds](https://github.com/culminationAI/claude-sounds) | Audio feedback for Claude Code hooks — 10 events, 21 sounds, random rotation. macOS (`afplay`). |
| [claude-code-hooks](https://github.com/yurukusa/claude-code-hooks) | 15 production-tested hooks from 160+ hours of autonomous operation. Destructive command blocker, branch guard, syntax check, context monitor, permission auto-approver. Bash, zero deps |
| [cc-safe-setup](https://github.com/yurukusa/cc-safe-setup) | One command (`npx cc-safe-setup`) to install 6 essential safety hooks in 10 seconds. Zero dependencies |
| [claude-supermemory](https://github.com/supermemoryai/claude-supermemory) | Persistent memory across sessions and projects using Supermemory. User profile injection at session start, automatic conversation capture. 2,300+ stars |
| [code-architect](plugins/code-architect/) | Generate architecture diagrams and technical design documents |
| [code-explainer](plugins/code-explainer/) | Explain complex code and annotate files with inline documentation |
| [code-guardian](plugins/code-guardian/) | Automated code review, security scanning, and quality enforcement |
| [code-review-assistant](plugins/code-review-assistant/) | Automated code review with severity levels and actionable feedback |
| [eliniscan](https://github.com/AlpYenigun/eliniscan) | AI full codebase scanner. Opens a separate Claude session for every file — reads every line, misses nothing. Finds bugs, security, performance issues and auto-fixes. |
| [codebase-documenter](plugins/codebase-documenter/) | Auto-document entire codebase with inline comments and API docs |
| [color-contrast](plugins/color-contrast/) | Color contrast checking and accessible color suggestions |
| [commit-commands](plugins/commit-commands/) | Advanced commit workflows with smart staging and push automation |
| [complexity-reducer](plugins/complexity-reducer/) | Reduce cyclomatic complexity and simplify functions |
| [compliance-checker](plugins/compliance-checker/) | Regulatory compliance verification for GDPR, SOC2, and HIPAA |
| [content-creator](plugins/content-creator/) | Technical content generation for blog posts and social media |
| [context7-docs](plugins/context7-docs/) | Fetch up-to-date library documentation via Context7 for accurate coding |
| [contract-tester](plugins/contract-tester/) | API contract testing with Pact for microservice compatibility |
| [cozempic](https://github.com/Ruya-AI/cozempic) | ✨ v1.2.x — Self-updating now, atomic writes, strict session guard, zero false positives on team detection. 13 pruning strategies, Agent Team protection, MCP server, JSONL doctor. Install: `/plugin marketplace add Ruya-AI/cozempic` |
| [create-worktrees](plugins/create-worktrees/) | Git worktree management for parallel development workflows |
| [cron-scheduler](plugins/cron-scheduler/) | Cron job configuration and schedule validation |
| [css-cleaner](plugins/css-cleaner/) | Find unused CSS and consolidate stylesheets |
| [cup](https://github.com/krodak/clickup-cli) | ClickUp CLI for AI agents with task management, sprints, and time tracking |
| [data-privacy](plugins/data-privacy/) | Data privacy implementation with PII detection and anonymization |
| [database-optimizer](plugins/database-optimizer/) | Database query optimization with index recommendations and EXPLAIN analysis |
| [dead-code-finder](plugins/dead-code-finder/) | Find and remove dead code across the codebase |
| [debug-session](plugins/debug-session/) | Interactive debugging workflow with git bisect integration |
| [dependency-manager](plugins/dependency-manager/) | Audit, update, and manage project dependencies with safety checks |
| [deploy-pilot](plugins/deploy-pilot/) | Deployment automation with Dockerfile generation, CI/CD pipelines, and infrastructure as code |
| [desktop-app](plugins/desktop-app/) | Desktop application scaffolding with Electron or Tauri |
| [devops-automator](plugins/devops-automator/) | DevOps automation scripts for CI/CD, health checks, and deployments |
| [discuss](plugins/discuss/) | Debate implementation approaches with structured pros and cons analysis |
| [claw-army/claude-node](https://github.com/claw-army/claude-node) | Python subprocess bridge for Claude Code CLI, giving Python code direct access to Claude Code native capabilities via stream-json |
| [discoclaw](https://github.com/DiscoClaw/discoclaw) | Personal AI orchestrator that bridges Discord to Claude Code with durable memory, task tracking, and cron-based automation |
| [jarvis](https://github.com/Ramsbaby/jarvis) | Turns an idle Claude Max subscription into a 24/7 AI ops system — Discord bot, 76 scheduled tasks, 12 AI teams, local LanceDB RAG, 98% context compression via Nexus CIG, and 4-layer self-healing infrastructure. Uses `claude -p` headless mode at $0 extra cost. |
| [jarvis-company-board](https://github.com/Ramsbaby/jarvis-company-board) | Real-time AI agent collaboration board built on Next.js 15 and SQLite WAL — 8 named AI board members debate decisions via SSE push, with a DEV task approval workflow and Railway deploy support. |
| [dna-claude-analysis](https://github.com/shmlkv/dna-claude-analysis) | Personal genome analysis toolkit that analyzes raw DNA data across 17 categories and generates a terminal-style HTML dashboard |
| [codetape](https://github.com/888wing/codetape) | The flight recorder for AI coding — auto-records semantic traces and syncs README, CHANGELOG, CLAUDE.md. Zero deps. `npx codetape init` |
| [doc-forge](plugins/doc-forge/) | Documentation generation, API docs, and README maintenance |
| [docker-helper](plugins/docker-helper/) | Build optimized Docker images and improve Dockerfile best practices |
| [double-check](plugins/double-check/) | Verify code correctness with systematic second-pass analysis |
| [e2e-runner](plugins/e2e-runner/) | End-to-end test execution and recording for web applications |
| [embedding-manager](plugins/embedding-manager/) | Manage vector embeddings and similarity search |
| [env-manager](plugins/env-manager/) | Set up and validate environment configurations across environments |
| [env-sync](plugins/env-sync/) | Environment variable syncing and diff across environments |
| [experiment-tracker](plugins/experiment-tracker/) | ML experiment tracking with metrics logging and run comparison |
| [explore](plugins/explore/) | Smart codebase exploration with dependency mapping and structure analysis |
| [faf-skills](https://github.com/Wolfe-Jam/faf-skills) | 31 Claude Code skills for persistent project context (.faf, `application/vnd.faf+yaml`). Scoring, sync, testing, publishing, MCP server creation, architecture docs. Anthropic MCP #2759. |
| [feature-dev](plugins/feature-dev/) | Full feature development workflow from spec to completion |
| [fractal](https://github.com/rmolines/fractal) | Recursive project management plugin. Decomposes any goal into verifiable predicates, works on the riskiest unknown first. Features `/fractal:run` (idempotent state machine), `/fractal:init`, `/fractal:patch`, dry run mode, and incremental decomposition with re-evaluation. |
| [finance-tracker](plugins/finance-tracker/) | Development cost tracking with time estimates and budget reporting |
| [fix-github-issue](plugins/fix-github-issue/) | Auto-fix GitHub issues by analyzing issue details and implementing solutions |
| [fix-pr](plugins/fix-pr/) | Fix PR review comments automatically with context-aware patches |
| [flutter-mobile](plugins/flutter-mobile/) | Flutter app development with widget creation and platform channels |
| [frontend-developer](plugins/frontend-developer/) | Frontend component development with accessibility and responsive design |
| [gcp-helper](plugins/gcp-helper/) | Google Cloud Platform service configuration and deployment |
| [git-flow](plugins/git-flow/) | Git workflow management with feature branches, releases, and hotfix flows |
| [github-issue-manager](plugins/github-issue-manager/) | GitHub issue triage, creation, and management |
| [helm-charts](plugins/helm-charts/) | Helm chart generation and upgrade management |
| [import-organizer](plugins/import-organizer/) | Organize, sort, and clean import statements |
| [infrastructure-maintainer](plugins/infrastructure-maintainer/) | Infrastructure maintenance with security audits and update management |
| [ios-developer](plugins/ios-developer/) | iOS and Swift development with SwiftUI views and models |
| [k8s-helper](plugins/k8s-helper/) | Generate Kubernetes manifests and debug pod issues with kubectl |
| [license-checker](plugins/license-checker/) | License compliance checking and NOTICE file generation |
| [lighthouse-runner](plugins/lighthouse-runner/) | Run Lighthouse audits and fix performance issues |
| [lightcms](https://github.com/jonradoff/lightcms) | AI-native CMS with 41 MCP tools for managing websites through natural language — pages, templates, assets, themes, collections, redirects, and more with full content versioning |
| [linear-helper](plugins/linear-helper/) | Linear issue tracking integration and workflow management |
| [load-tester](plugins/load-tester/) | Load and stress testing for APIs and web services |
| [memory-profiler](plugins/memory-profiler/) | Memory leak detection and heap analysis |
| [migrate-tool](plugins/migrate-tool/) | Generate database migrations and code migration scripts for framework upgrades |
| [migration-generator](plugins/migration-generator/) | Database migration generation and rollback management |
| [model-context-protocol](plugins/model-context-protocol/) | MCP server development helper with tool and resource scaffolding |
| [model-evaluator](plugins/model-evaluator/) | Evaluate and compare ML model performance metrics |
| [monitoring-setup](plugins/monitoring-setup/) | Monitoring and alerting configuration with dashboard generation |
| [monorepo-manager](plugins/monorepo-manager/) | Manage monorepo packages with affected detection and version synchronization |
| [mutation-tester](plugins/mutation-tester/) | Mutation testing to measure test suite quality |
| [myclaude](https://github.com/stellarlinkco/myclaude) | Multi-agent orchestration routing tasks to Claude Code, Codex, Gemini, and OpenCode based on complexity. OmO skill for intelligent routing. 2,400+ stars |
| [nimbalyst](https://nimbalyst.com) | Visual workspace for building with Codex and Claude Code. Session and task manager. Visual editing |
| [n8n-workflow](plugins/n8n-workflow/) | Generate n8n automation workflows from natural language descriptions |
| [onboarding-guide](plugins/onboarding-guide/) | New developer onboarding documentation generator |
| [oh-my-claudecode](https://github.com/Yeachan-Heo/oh-my-claudecode) | Teams-first multi-agent orchestration. 19 specialized agents, 28 skills. Full autonomous execution, Socratic questioning, N coordinated agents. 9,900+ stars |
| [onWatch](https://github.com/onllm-dev/onwatch) | Open-source Go CLI that tracks AI API quota usage across 7 providers (Synthetic, Z.ai, Anthropic, Codex, GitHub Copilot, MiniMax, Antigravity) with a background daemon (<50 MB RAM), zero telemetry, and a Material Design 3 web dashboard |
| [obey](https://github.com/Lexxes-Projects/obey) | Rule enforcement plugin. Save rules with natural language, enforce with 17 lifecycle hooks. Three scopes (global, stack-specific, project-local), active blocking via PreToolUse, completion checklists via Stop hook, audit trail, auto-detects rule-like language. Cross-platform. |
| [opcode](https://github.com/winfunc/opcode) | Tauri 2 desktop GUI and toolkit for Claude Code. Manage sessions, create custom agents with visual editor, usage analytics, MCP integration. 21,000+ stars |
| [openapi-expert](plugins/openapi-expert/) | OpenAPI spec generation, validation, and client code scaffolding |
| [optimize](plugins/optimize/) | Code optimization for performance and bundle size reduction |
| [oss-autopilot](https://github.com/costajohnt/oss-autopilot) | Open source contribution manager — tracks PRs across repos, discovers issues, diagnoses CI failures, drafts maintainer responses. 7 agents, interactive commands, MCP server. Install: `/plugin marketplace add costajohnt/oss-autopilot` |
| [peon-ping](https://github.com/PeonPing/peon-ping) | Warcraft III Peon voice notifications (+ StarCraft, Portal, Zelda) for Claude Code and other agents. Desktop banners, auto-detects SSH/devcontainers. 3,900+ stars |
| [perf-profiler](plugins/perf-profiler/) | Performance analysis, profiling, and optimization recommendations |
| [performance-monitor](plugins/performance-monitor/) | Profile API endpoints and run benchmarks to identify performance bottlenecks |
| [plan](plugins/plan/) | Structured planning with risk assessment and time estimation |
| [preflight](https://github.com/preflight-dev/preflight) | 24-tool MCP server that catches vague prompts before they cost 2-3x in wrong→fix cycles. 12-category scorecards, correction pattern learning, cross-service contract awareness, session history search with LanceDB vectors, and cost estimation. `npx preflight-dev` |
| [pr-reviewer](plugins/pr-reviewer/) | Review pull requests with structured analysis and approve with confidence |
| [product-shipper](plugins/product-shipper/) | Ship features end-to-end with launch checklists and rollout plans |
| [production-grade](https://github.com/nagisanzenin/claude-code-production-grade-plugin) | 14-agent autonomous pipeline — PM, Architect, Backend, Frontend, QA, Security, Code Review, DevOps, SRE, Data Scientist, Technical Writer, Skill Maker, Polymath co-pilot. Two-wave parallel execution, brownfield-safe. |
| [project-scaffold](plugins/project-scaffold/) | Scaffold new projects and add features with best-practice templates |
| [prompt-optimizer](plugins/prompt-optimizer/) | Analyze and optimize AI prompts for better results |
| [pulse](https://github.com/chsm04/pulse) | Local Channel plugin — push notifications into Claude Code sessions via HTTP POST. No Discord/Slack needed, just curl. Three levels (info/warn/error), source tracking, dedup. |
| [PUIUX Pilot](https://github.com/PUIUX-Cloud/puiux-pilot) | Auto-configures Claude Code hooks, MCPs, and skills for any project. Scans 95+ project types, selects from 28+ hooks, scores quality (0-100), translates configs across AI tools. Safe: dry-run, atomic writes, backup + rollback. |
| [python-expert](plugins/python-expert/) | Python-specific development with type hints and idiomatic refactoring |
| [pulser](https://github.com/whynowlab/pulser) | Diagnostic CLI for Claude Code SKILL.md files — scans 8 rules, auto-classifies, prescribes fixes with templates, --fix with rollback |
| [query-optimizer](plugins/query-optimizer/) | SQL query optimization and execution plan analysis |
| [rag-builder](plugins/rag-builder/) | Build Retrieval-Augmented Generation pipelines |
| [rapid-prototyper](plugins/rapid-prototyper/) | Quick prototype scaffolding with minimal viable structure |
| [reporecall](https://github.com/proofofwork-agency/reporecall) | Local codebase memory for Claude Code. Tree-sitter AST indexing (22 languages), hybrid keyword + vector search, call-graph traversal, hooks + MCP. Injects relevant context in ~5ms before Claude starts thinking. npm: `@proofofwork-agency/reporecall` |
| [react-native-dev](plugins/react-native-dev/) | React Native mobile development with platform-specific optimizations |
| [readme-generator](plugins/readme-generator/) | Smart README generation from project analysis |
| [refactor-engine](plugins/refactor-engine/) | Extract functions, simplify complex code, and reduce cognitive complexity |
| [regex-builder](plugins/regex-builder/) | Build, test, and debug regular expression patterns |
| [release-manager](plugins/release-manager/) | Semantic versioning management and automated release workflows |
| [responsive-designer](plugins/responsive-designer/) | Responsive design implementation and testing |
| [schema-designer](plugins/schema-designer/) | Database schema design and ERD generation |
| [screen-reader-tester](plugins/screen-reader-tester/) | Screen reader compatibility testing and ARIA fixes |
| [security-guidance](plugins/security-guidance/) | Security best practices advisor with vulnerability detection and fixes |
| [seed-generator](plugins/seed-generator/) | Database seeding script generation with realistic data |
| [slack-notifier](plugins/slack-notifier/) | Slack integration for deployment and build notifications |
| [smart-commit](plugins/smart-commit/) | Intelligent git commits with conventional format, semantic analysis, and changelog generation |
| [sprint-prioritizer](plugins/sprint-prioritizer/) | Sprint planning with story prioritization and capacity estimation |
| [technical-sales](plugins/technical-sales/) | Technical demo creation and POC proposal writing |
| [the-pragmatic-pm](https://github.com/marfoerst/the-pragmatic-pm) | PM leadership toolkit with 43 skills, 5 agents, 4 workflows. Covers PRD generation, OKR lifecycle, pricing, AI pricing, positioning, sales enablement, and quarterly planning. |
| [terraform-helper](plugins/terraform-helper/) | Terraform module creation and infrastructure planning |
| [test-data-generator](plugins/test-data-generator/) | Generate realistic test data and seed databases |
| [test-results-analyzer](plugins/test-results-analyzer/) | Analyze test failures, identify patterns, and suggest targeted fixes |
| [test-writer](plugins/test-writer/) | Generate comprehensive unit and integration tests with full coverage |
| [tool-evaluator](plugins/tool-evaluator/) | Evaluate and compare developer tools with structured scoring criteria |
| [type-migrator](plugins/type-migrator/) | Migrate JavaScript files to TypeScript with proper types |
| [ui-designer](plugins/ui-designer/) | Implement UI designs from specs with pixel-perfect component generation |
| [ultrathink](plugins/ultrathink/) | Deep analysis mode with extended reasoning for complex problems |
| [unit-test-generator](plugins/unit-test-generator/) | Generate comprehensive unit tests for any function or module |
| [update-branch](plugins/update-branch/) | Rebase and update feature branches with conflict resolution |
| [vision-specialist](plugins/vision-specialist/) | Image and visual analysis with screenshot interpretation and text extraction |
| [vibe-kanban](https://github.com/BloopAI/vibe-kanban) | Kanban-based orchestration for 10+ coding agents (Claude Code, Codex, Gemini CLI, Copilot, Amp). Isolated git worktrees per agent, inline diff review. 23,200+ stars |
| [VibeGuard](https://github.com/majiayu000/vibeguard) | Stop AI from hallucinating code. 88 rules + 13 hooks + 14 agents for real-time interception and static scanning across 5 languages |
| [visual-regression](plugins/visual-regression/) | Visual regression testing with screenshot comparison |
| [wshobson/agents](https://github.com/wshobson/agents) | 112 specialized agents, 16 multi-agent workflow orchestrators, 146 skills, 79 tools in 72 focused plugins. 31,300+ stars |
| [web-dev](plugins/web-dev/) | Full-stack web development with app scaffolding and page generation |
| [workflow-optimizer](plugins/workflow-optimizer/) | Development workflow analysis and optimization recommendations |
| [background-timer](https://github.com/culminationAI/background-timer) | Background timer with task notifications -- set delayed checks without blocking conversation |
| [claude-sounds](https://github.com/culminationAI/claude-sounds) | Audio feedback for Claude Code hooks -- 10 events, 21 sounds, random rotation, customizable (macOS) |

| [notch-so-good](https://github.com/deepshal99/notch-so-good) | Pixel-art crab (Chawd) lives in your Mac's notch and watches Claude Code for you. Live session timers, color-coded notifications, 13 idle animations, mouse-reactive eyes, drowsiness system. Universal binary, one-line install: `npx notch-so-good`. MIT, 130+ users |

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

One hundred thirty-five specialized agents organized into ten categories. Each agent defines a persona, system instructions, and tool access patterns.

### Core Development (13 agents)

| Agent | File | Purpose |
|-------|------|---------|
| Fullstack Engineer | [`fullstack-engineer.md`](agents/core-development/fullstack-engineer.md) | End-to-end feature delivery across frontend, backend, and database |
| API Designer | [`api-designer.md`](agents/core-development/api-designer.md) | RESTful API design with OpenAPI, versioning, and pagination |
| Frontend Architect | [`frontend-architect.md`](agents/core-development/frontend-architect.md) | Component architecture, state management, performance |
| Mobile Developer | [`mobile-developer.md`](agents/core-development/mobile-developer.md) | Cross-platform mobile with React Native and Flutter |
| Backend Developer | [`backend-developer.md`](agents/core-development/backend-developer.md) | Node.js/Express/Fastify backend services |
| GraphQL Architect | [`graphql-architect.md`](agents/core-development/graphql-architect.md) | Schema design, resolvers, federation, DataLoader |
| Microservices Architect | [`microservices-architect.md`](agents/core-development/microservices-architect.md) | Distributed systems, event-driven, saga patterns |
| WebSocket Engineer | [`websocket-engineer.md`](agents/core-development/websocket-engineer.md) | Real-time communication, Socket.io, scaling |
| UI Designer | [`ui-designer.md`](agents/core-development/ui-designer.md) | UI/UX implementation, design systems, Figma-to-code |
| Electron Developer | [`electron-developer.md`](agents/core-development/electron-developer.md) | Electron desktop apps, IPC, native OS integration |
| API Gateway Engineer | [`api-gateway-engineer.md`](agents/core-development/api-gateway-engineer.md) | API gateway patterns, rate limiting, auth proxies |
| Monorepo Architect | [`monorepo-architect.md`](agents/core-development/monorepo-architect.md) | Turborepo/Nx workspace strategies, dependency graphs |
| Event-Driven Architect | [`event-driven-architect.md`](agents/core-development/event-driven-architect.md) | Event sourcing, CQRS, message queues, distributed events |

### Language Experts (25 agents)

| Agent | File | Purpose |
|-------|------|---------|
| TypeScript | [`typescript-specialist.md`](agents/language-experts/typescript-specialist.md) | Type-safe patterns, generics, module design |
| Python | [`python-engineer.md`](agents/language-experts/python-engineer.md) | Pythonic patterns, packaging, async |
| Rust | [`rust-systems.md`](agents/language-experts/rust-systems.md) | Ownership, lifetimes, trait design |
| Go | [`golang-developer.md`](agents/language-experts/golang-developer.md) | Interfaces, goroutines, error handling |
| Next.js | [`nextjs-developer.md`](agents/language-experts/nextjs-developer.md) | App Router, RSC, ISR, server actions |
| React | [`react-specialist.md`](agents/language-experts/react-specialist.md) | React 19, hooks, state management |
| Django | [`django-developer.md`](agents/language-experts/django-developer.md) | Django 5+, DRF, ORM optimization |
| Rails | [`rails-expert.md`](agents/language-experts/rails-expert.md) | Rails 7+, Hotwire, ActiveRecord |
| Java | [`java-architect.md`](agents/language-experts/java-architect.md) | Spring Boot 3+, JPA, microservices |
| Kotlin | [`kotlin-specialist.md`](agents/language-experts/kotlin-specialist.md) | Coroutines, Ktor, multiplatform |
| Flutter | [`flutter-expert.md`](agents/language-experts/flutter-expert.md) | Flutter 3+, Dart, Riverpod |
| C# | [`csharp-developer.md`](agents/language-experts/csharp-developer.md) | .NET 8+, ASP.NET Core, EF Core |
| PHP | [`php-developer.md`](agents/language-experts/php-developer.md) | PHP 8.3+, Laravel 11, Eloquent |
| Elixir | [`elixir-expert.md`](agents/language-experts/elixir-expert.md) | OTP, Phoenix LiveView, Ecto |
| Angular | [`angular-architect.md`](agents/language-experts/angular-architect.md) | Angular 17+, signals, standalone components |
| Vue | [`vue-specialist.md`](agents/language-experts/vue-specialist.md) | Vue 3, Composition API, Pinia, Nuxt |
| Svelte | [`svelte-developer.md`](agents/language-experts/svelte-developer.md) | SvelteKit, runes, form actions |
| Swift | [`swift-developer.md`](agents/language-experts/swift-developer.md) | SwiftUI, iOS 17+, Combine, structured concurrency |
| Scala | [`scala-developer.md`](agents/language-experts/scala-developer.md) | Akka actors, Play Framework, Cats Effect |
| Haskell | [`haskell-developer.md`](agents/language-experts/haskell-developer.md) | Pure FP, monads, type classes, GHC extensions |
| Lua | [`lua-developer.md`](agents/language-experts/lua-developer.md) | Game scripting, Neovim plugins, LuaJIT |
| Zig | [`zig-developer.md`](agents/language-experts/zig-developer.md) | Systems programming, comptime, allocator strategies |
| Clojure | [`clojure-developer.md`](agents/language-experts/clojure-developer.md) | REPL-driven development, Ring/Compojure, ClojureScript |
| OCaml | [`ocaml-developer.md`](agents/language-experts/ocaml-developer.md) | Type inference, pattern matching, Dream framework |
| Nim | [`nim-developer.md`](agents/language-experts/nim-developer.md) | Metaprogramming, GC strategies, C/C++ interop |

### Infrastructure (11 agents)

| Agent | File | Purpose |
|-------|------|---------|
| Cloud Architect | [`cloud-architect.md`](agents/infrastructure/cloud-architect.md) | AWS, GCP, Azure provisioning and IaC |
| DevOps Engineer | [`devops-engineer.md`](agents/infrastructure/devops-engineer.md) | CI/CD, containerization, monitoring |
| Database Admin | [`database-admin.md`](agents/infrastructure/database-admin.md) | Schema design, query tuning, replication |
| Platform Engineer | [`platform-engineer.md`](agents/infrastructure/platform-engineer.md) | Internal developer platforms, service catalogs |
| Kubernetes Specialist | [`kubernetes-specialist.md`](agents/infrastructure/kubernetes-specialist.md) | Operators, CRDs, service mesh, Istio |
| Terraform Engineer | [`terraform-engineer.md`](agents/infrastructure/terraform-engineer.md) | IaC, module design, state management, multi-cloud |
| Network Engineer | [`network-engineer.md`](agents/infrastructure/network-engineer.md) | DNS, load balancers, CDN, firewall rules |
| SRE Engineer | [`sre-engineer.md`](agents/infrastructure/sre-engineer.md) | SLOs, error budgets, incident response, postmortems |
| Deployment Engineer | [`deployment-engineer.md`](agents/infrastructure/deployment-engineer.md) | Blue-green, canary releases, rolling updates |
| Security Engineer | [`security-engineer.md`](agents/infrastructure/security-engineer.md) | IAM policies, mTLS, secrets management, Vault |
| Incident Responder | [`incident-responder.md`](agents/infrastructure/incident-responder.md) | Incident triage, runbooks, communication, recovery |

### Quality Assurance (10 agents)

| Agent | File | Purpose |
|-------|------|---------|
| Code Reviewer | [`code-reviewer.md`](agents/quality-assurance/code-reviewer.md) | PR review with security and performance focus |
| Test Architect | [`test-architect.md`](agents/quality-assurance/test-architect.md) | Test strategy, pyramid, coverage targets |
| Security Auditor | [`security-auditor.md`](agents/quality-assurance/security-auditor.md) | Vulnerability scanning, OWASP compliance |
| Performance Engineer | [`performance-engineer.md`](agents/quality-assurance/performance-engineer.md) | Load testing, profiling, optimization |
| Accessibility Specialist | [`accessibility-specialist.md`](agents/quality-assurance/accessibility-specialist.md) | WCAG compliance, ARIA, screen readers |
| Chaos Engineer | [`chaos-engineer.md`](agents/quality-assurance/chaos-engineer.md) | Chaos testing, fault injection, resilience validation |
| Penetration Tester | [`penetration-tester.md`](agents/quality-assurance/penetration-tester.md) | OWASP Top 10 assessment, vulnerability reporting |
| QA Automation | [`qa-automation.md`](agents/quality-assurance/qa-automation.md) | Test automation frameworks, CI integration |
| Compliance Auditor | [`compliance-auditor.md`](agents/quality-assurance/compliance-auditor.md) | SOC 2, GDPR, HIPAA compliance checking |
| Error Detective | [`error-detective.md`](agents/quality-assurance/error-detective.md) | Error tracking, stack trace analysis, root cause ID |

### Data & AI (15 agents)

| Agent | File | Purpose |
|-------|------|---------|
| AI Engineer | [`ai-engineer.md`](agents/data-ai/ai-engineer.md) | AI application integration, RAG, agents |
| ML Engineer | [`ml-engineer.md`](agents/data-ai/ml-engineer.md) | ML pipelines, training, evaluation |
| Data Scientist | [`data-scientist.md`](agents/data-ai/data-scientist.md) | Statistical analysis, visualization |
| Data Engineer | [`data-engineer.md`](agents/data-ai/data-engineer.md) | ETL pipelines, Spark, data warehousing |
| LLM Architect | [`llm-architect.md`](agents/data-ai/llm-architect.md) | Fine-tuning, model selection, serving |
| Prompt Engineer | [`prompt-engineer.md`](agents/data-ai/prompt-engineer.md) | Prompt optimization, structured outputs |
| MLOps Engineer | [`mlops-engineer.md`](agents/data-ai/mlops-engineer.md) | Model serving, monitoring, A/B testing |
| NLP Engineer | [`nlp-engineer.md`](agents/data-ai/nlp-engineer.md) | NLP pipelines, embeddings, classification |
| Database Optimizer | [`database-optimizer.md`](agents/data-ai/database-optimizer.md) | Query optimization, indexing, partitioning |
| Computer Vision | [`computer-vision-engineer.md`](agents/data-ai/computer-vision-engineer.md) | Image classification, object detection, PyTorch |
| Recommendation Engine | [`recommendation-engine.md`](agents/data-ai/recommendation-engine.md) | Collaborative filtering, content-based, hybrid |
| ETL Specialist | [`etl-specialist.md`](agents/data-ai/etl-specialist.md) | Data pipelines, schema evolution, data quality |
| Vector DB Engineer | [`vector-database-engineer.md`](agents/data-ai/vector-database-engineer.md) | FAISS, Pinecone, Qdrant, Weaviate, embeddings |
| Data Visualization | [`data-visualization.md`](agents/data-ai/data-visualization.md) | D3.js, Chart.js, Matplotlib, Plotly dashboards |
| Feature Engineer | [`feature-engineer.md`](agents/data-ai/feature-engineer.md) | Feature stores, pipelines, encoding strategies |
| AutoResearch Agent | [`autoresearch-agent.md`](agents/data-ai/autoresearch-agent.md) | ML experiment automation via tree search, code optimization |

### Developer Experience (15 agents)

| Agent | File | Purpose |
|-------|------|---------|
| CLI Developer | [`cli-developer.md`](agents/developer-experience/cli-developer.md) | CLI tools with Commander, yargs, clap |
| DX Optimizer | [`dx-optimizer.md`](agents/developer-experience/dx-optimizer.md) | Developer experience, tooling, ergonomics |
| Documentation Engineer | [`documentation-engineer.md`](agents/developer-experience/documentation-engineer.md) | Technical writing, API docs, guides |
| Build Engineer | [`build-engineer.md`](agents/developer-experience/build-engineer.md) | Build systems, bundlers, compilation |
| Dependency Manager | [`dependency-manager.md`](agents/developer-experience/dependency-manager.md) | Dependency audit, updates, lockfiles |
| Refactoring Specialist | [`refactoring-specialist.md`](agents/developer-experience/refactoring-specialist.md) | Code restructuring, dead code removal |
| Legacy Modernizer | [`legacy-modernizer.md`](agents/developer-experience/legacy-modernizer.md) | Legacy codebase migration strategies |
| MCP Developer | [`mcp-developer.md`](agents/developer-experience/mcp-developer.md) | MCP server and tool development |
| Tooling Engineer | [`tooling-engineer.md`](agents/developer-experience/tooling-engineer.md) | ESLint, Prettier, custom tooling |
| Git Workflow Manager | [`git-workflow-manager.md`](agents/developer-experience/git-workflow-manager.md) | Branching strategies, CI, CODEOWNERS |
| API Documentation | [`api-documentation.md`](agents/developer-experience/api-documentation.md) | OpenAPI/Swagger, Redoc, interactive examples |
| Monorepo Tooling | [`monorepo-tooling.md`](agents/developer-experience/monorepo-tooling.md) | Changesets, workspace deps, version management |
| VS Code Extension | [`vscode-extension.md`](agents/developer-experience/vscode-extension.md) | LSP integration, custom editors, webview panels |
| Testing Infrastructure | [`testing-infrastructure.md`](agents/developer-experience/testing-infrastructure.md) | Test runners, CI splitting, flaky test management |
| Developer Portal | [`developer-portal.md`](agents/developer-experience/developer-portal.md) | Backstage, service catalogs, self-service infra |

### Specialized Domains (15 agents)

| Agent | File | Purpose |
|-------|------|---------|
| Blockchain Developer | [`blockchain-developer.md`](agents/specialized-domains/blockchain-developer.md) | Smart contracts, Solidity, Web3 |
| Game Developer | [`game-developer.md`](agents/specialized-domains/game-developer.md) | Game logic, ECS, state machines |
| Embedded Systems | [`embedded-systems.md`](agents/specialized-domains/embedded-systems.md) | Firmware, RTOS, hardware interfaces |
| Fintech Engineer | [`fintech-engineer.md`](agents/specialized-domains/fintech-engineer.md) | Financial systems, compliance, precision |
| IoT Engineer | [`iot-engineer.md`](agents/specialized-domains/iot-engineer.md) | MQTT, edge computing, digital twins |
| Payment Integration | [`payment-integration.md`](agents/specialized-domains/payment-integration.md) | Stripe, PCI DSS, 3D Secure |
| SEO Specialist | [`seo-specialist.md`](agents/specialized-domains/seo-specialist.md) | Structured data, Core Web Vitals |
| E-Commerce Engineer | [`e-commerce-engineer.md`](agents/specialized-domains/e-commerce-engineer.md) | Cart, inventory, order management |
| Healthcare Engineer | [`healthcare-engineer.md`](agents/specialized-domains/healthcare-engineer.md) | HIPAA, HL7 FHIR, medical data pipelines |
| Real Estate Tech | [`real-estate-tech.md`](agents/specialized-domains/real-estate-tech.md) | MLS integration, geospatial search, valuations |
| Education Tech | [`education-tech.md`](agents/specialized-domains/education-tech.md) | LMS, SCORM/xAPI, adaptive learning, assessments |
| Media Streaming | [`media-streaming.md`](agents/specialized-domains/media-streaming.md) | HLS/DASH, transcoding, CDN, adaptive bitrate |
| Geospatial Engineer | [`geospatial-engineer.md`](agents/specialized-domains/geospatial-engineer.md) | PostGIS, spatial queries, mapping APIs, tiles |
| Robotics Engineer | [`robotics-engineer.md`](agents/specialized-domains/robotics-engineer.md) | ROS2, sensor fusion, motion planning, SLAM |
| Voice Assistant | [`voice-assistant.md`](agents/specialized-domains/voice-assistant.md) | STT, TTS, dialog management, Alexa/Google |

### Business & Product (12 agents)

| Agent | File | Purpose |
|-------|------|---------|
| Product Manager | [`product-manager.md`](agents/business-product/product-manager.md) | PRDs, user stories, RICE prioritization |
| Technical Writer | [`technical-writer.md`](agents/business-product/technical-writer.md) | Documentation, style guides |
| UX Researcher | [`ux-researcher.md`](agents/business-product/ux-researcher.md) | Usability testing, survey design |
| Project Manager | [`project-manager.md`](agents/business-product/project-manager.md) | Sprint planning, Agile, task tracking |
| Scrum Master | [`scrum-master.md`](agents/business-product/scrum-master.md) | Ceremonies, velocity, retrospectives |
| Business Analyst | [`business-analyst.md`](agents/business-product/business-analyst.md) | Requirements analysis, process mapping |
| Content Strategist | [`content-strategist.md`](agents/business-product/content-strategist.md) | SEO content, editorial calendars, topic clustering |
| Growth Engineer | [`growth-engineer.md`](agents/business-product/growth-engineer.md) | A/B testing, analytics, funnel optimization |
| Customer Success | [`customer-success.md`](agents/business-product/customer-success.md) | Ticket triage, knowledge base, health scoring |
| Sales Engineer | [`sales-engineer.md`](agents/business-product/sales-engineer.md) | Technical demos, POCs, integration guides |
| Legal Advisor | [`legal-advisor.md`](agents/business-product/legal-advisor.md) | ToS, privacy policies, software licenses |
| Marketing Analyst | [`marketing-analyst.md`](agents/business-product/marketing-analyst.md) | Campaign analysis, attribution, ROI tracking |

### Orchestration (8 agents)

| Agent | File | Purpose |
|-------|------|---------|
| Task Coordinator | [`task-coordinator.md`](agents/orchestration/task-coordinator.md) | Routes work between agents, manages handoffs |
| Context Manager | [`context-manager.md`](agents/orchestration/context-manager.md) | Context compression, session summaries |
| Workflow Director | [`workflow-director.md`](agents/orchestration/workflow-director.md) | Multi-agent pipeline orchestration |
| Agent Installer | [`agent-installer.md`](agents/orchestration/agent-installer.md) | Install and configure agent collections |
| Knowledge Synthesizer | [`knowledge-synthesizer.md`](agents/orchestration/knowledge-synthesizer.md) | Compress info, build knowledge graphs |
| Performance Monitor | [`performance-monitor.md`](agents/orchestration/performance-monitor.md) | Track token usage, measure response quality |
| Error Coordinator | [`error-coordinator.md`](agents/orchestration/error-coordinator.md) | Handle errors across multi-agent workflows |
| Multi-Agent Coordinator | [`multi-agent-coordinator.md`](agents/orchestration/multi-agent-coordinator.md) | Parallel agent execution, merge outputs |

### Research & Analysis (11 agents)

| Agent | File | Purpose |
|-------|------|---------|
| Research Analyst | [`research-analyst.md`](agents/research-analysis/research-analyst.md) | Technical research, evidence synthesis |
| Competitive Analyst | [`competitive-analyst.md`](agents/research-analysis/competitive-analyst.md) | Market positioning, feature comparison |
| Trend Analyst | [`trend-analyst.md`](agents/research-analysis/trend-analyst.md) | Technology trend forecasting |
| Data Researcher | [`data-researcher.md`](agents/research-analysis/data-researcher.md) | Data analysis, pattern recognition |
| Search Specialist | [`search-specialist.md`](agents/research-analysis/search-specialist.md) | Information retrieval, source evaluation |
| Patent Analyst | [`patent-analyst.md`](agents/research-analysis/patent-analyst.md) | Patent searches, prior art, IP landscape |
| Academic Researcher | [`academic-researcher.md`](agents/research-analysis/academic-researcher.md) | Literature reviews, citation analysis, methodology |
| Market Researcher | [`market-researcher.md`](agents/research-analysis/market-researcher.md) | Market sizing, TAM/SAM/SOM, competitive intel |
| Security Researcher | [`security-researcher.md`](agents/research-analysis/security-researcher.md) | CVE analysis, threat modeling, attack surface |
| Benchmarking Specialist | [`benchmarking-specialist.md`](agents/research-analysis/benchmarking-specialist.md) | Performance benchmarks, comparative evals |
| Technology Scout | [`technology-scout.md`](agents/research-analysis/technology-scout.md) | Emerging tech evaluation, build-vs-buy analysis |

### Using Agents

Reference an agent in your `CLAUDE.md`:

```markdown
## Agents
- Use `agents/core-development/fullstack-engineer.md` for feature development
- Use `agents/quality-assurance/code-reviewer.md` for PR reviews
- Use `agents/data-ai/prompt-engineer.md` for prompt optimization
```

---

## Skills

Thirty-five curated skill modules included in this repo, with access to **400,000+ additional skills** via the [SkillKit marketplace](https://agenstskills.com). Each included skill teaches Claude Code domain-specific patterns with code examples, anti-patterns, and checklists.

| Skill | Directory | What It Teaches |
|-------|-----------|-----------------|
| TDD Mastery | `skills/tdd-mastery/` | Red-green-refactor, test-first design, coverage targets |
| API Design Patterns | `skills/api-design-patterns/` | RESTful conventions, versioning, pagination, error responses |
| Database Optimization | `skills/database-optimization/` | Query planning, indexing, N+1 prevention, connection pooling |
| Frontend Excellence | `skills/frontend-excellence/` | Component architecture, state management, performance budgets |
| Security Hardening | `skills/security-hardening/` | Input validation, auth patterns, secrets management, CSP |
| [Prism Scanner](https://github.com/aidongise-cell/prism-scanner) | `pip install prism-scanner` | Agent skill/plugin/MCP security scanner — 39+ rules, AST taint tracking, A-F grading |
| DevOps Automation | `skills/devops-automation/` | Infrastructure as code, GitOps, monitoring, incident response |
| Continuous Learning | `skills/continuous-learning/` | Session summaries, learning logs, pattern extraction |
| React Patterns | `skills/react-patterns/` | Hooks, server components, suspense, error boundaries |
| Python Best Practices | `skills/python-best-practices/` | Type hints, dataclasses, async/await, packaging |
| Go Idioms | `skills/golang-idioms/` | Error handling, interfaces, concurrency, project layout |
| Django Patterns | `skills/django-patterns/` | DRF, ORM optimization, signals, middleware |
| Spring Boot Patterns | `skills/springboot-patterns/` | JPA, REST controllers, layered architecture |
| Next.js Mastery | `skills/nextjs-mastery/` | App Router, RSC, ISR, server actions, middleware |
| GraphQL Design | `skills/graphql-design/` | Schema design, DataLoader, subscriptions, pagination |
| Kubernetes Operations | `skills/kubernetes-operations/` | Deployments, Helm charts, HPA, troubleshooting |
| Docker Best Practices | `skills/docker-best-practices/` | Multi-stage builds, compose, image optimization |
| AWS Cloud Patterns | `skills/aws-cloud-patterns/` | Lambda, DynamoDB, CDK, S3 event processing |
| CI/CD Pipelines | `skills/ci-cd-pipelines/` | GitHub Actions, GitLab CI, matrix builds |
| Microservices Design | `skills/microservices-design/` | Event-driven architecture, saga pattern, service mesh |
| TypeScript Advanced | `skills/typescript-advanced/` | Generics, conditional types, mapped types, discriminated unions |
| Rust Systems | `skills/rust-systems/` | Ownership, traits, async patterns, error handling |
| Prompt Engineering | `skills/prompt-engineering/` | Chain-of-thought, few-shot, structured outputs |
| MCP Development | `skills/mcp-development/` | MCP server tools, resources, transport setup |
| PostgreSQL Optimization | `skills/postgres-optimization/` | EXPLAIN ANALYZE, indexes, partitioning, JSONB |
| Redis Patterns | `skills/redis-patterns/` | Caching, rate limiting, pub/sub, streams, Lua scripts |
| Monitoring & Observability | `skills/monitoring-observability/` | OpenTelemetry, Prometheus, structured logging |
| Authentication Patterns | `skills/authentication-patterns/` | JWT, OAuth2 PKCE, RBAC, session management |
| WebSocket & Realtime | `skills/websocket-realtime/` | Socket.io, SSE, reconnection, scaling |
| Testing Strategies | `skills/testing-strategies/` | Contract testing, snapshot testing, property-based testing |
| Git Advanced | `skills/git-advanced/` | Worktrees, bisect, interactive rebase, hooks |
| Accessibility (WCAG) | `skills/accessibility-wcag/` | ARIA patterns, keyboard navigation, color contrast |
| Performance Optimization | `skills/performance-optimization/` | Code splitting, image optimization, Core Web Vitals |
| Mobile Development | `skills/mobile-development/` | React Native, Flutter, responsive layouts |
| Data Engineering | `skills/data-engineering/` | ETL pipelines, Spark, star schema, data quality |
| LLM Integration | `skills/llm-integration/` | Streaming, function calling, RAG, cost optimization |

### Community Skills

| Skill | Install | What It Teaches |
|-------|---------|------------------|
| [Reepl - LinkedIn Content Creation](https://github.com/reepl-io/skills) | `npx skillkit@latest install reepl-io/skills` | 18 tools for LinkedIn content management: drafts, publishing, scheduling, voice profiles, contacts, collections, templates, and AI image generation |
| [avoid-ai-writing](https://github.com/conorbronsdon/avoid-ai-writing) | `git clone https://github.com/conorbronsdon/avoid-ai-writing ~/.claude/skills/avoid-ai-writing` | AI writing pattern detection and rewriting (21 categories, 43 replacements) |
| [CCM](https://github.com/dr5hn/ccm) | `npx skills add dr5hn/ccm@ccm` | Multi-account management, session cleanup, health checks, environment snapshots, permissions audit for Claude Code |
| [Edison](https://github.com/kilnside/edison) | `git clone https://github.com/kilnside/edison ~/.claude/skills/edison` | Design decision skill — the phase between brainstorming and building. Research-first progressive deepening with self-executing specs. Three modes: Check, Explore, Audit |
| [claude-handoff](https://github.com/REMvisual/claude-handoff) | `git clone https://github.com/REMvisual/claude-handoff ~/.claude/skills/handoff` | Cross-session handoff system with chain tracking, context summaries, and structured work continuity between Claude Code sessions |
| [ClawSec](https://clawsec.cc) | Visit [clawsec.cc](https://clawsec.cc) | Security audit platform for AI agent skills — automated 5-tier assessments, vulnerability detection, and configuration auditing for 33,000+ skills |
| [ClawSearch](https://clawsearch.cc) | `npm install -g clawsearch` | Security-first skill discovery engine with Trust Score ratings, knowledge graph, and pre-install guard (`clawsearch-guard`) to vet skills before installation |
| [MUSE](https://github.com/myths-labs/muse) | `git clone` + `./scripts/install.sh --tool claude` | Pure-Markdown memory OS with 48 skills, cross-conversation memory, 8 roles with permission isolation. Works with 6 AI coding tools. |
| [Product Manager Skills](https://github.com/Digidai/product-manager-skills) | `clawhub install product-manager-skills` | Senior PM agent with 6 knowledge domains, 12 templates, and 30+ frameworks covering discovery, strategy, delivery, SaaS metrics, PM career coaching (IC to CPO), and AI product craft |
| [OpenDivination](https://github.com/amenti-labs/opendivination) | `pipx install opendivination && npx skills add amenti-labs/opendivination --skill divination` | Tarot and I Ching skill with auditable entropy provenance, guided source setup across computer RNG, QRNG APIs, and local hardware, plus optional resonance mode |
| [pumpclaw](https://github.com/chainstacklabs/pumpclaw) | `git clone https://github.com/chainstacklabs/pumpclaw ~/.claude/skills/pumpclaw` | Agent skill for pump.fun token trading on Solana — buy, sell, launch tokens, wallet management, dry-run simulation, slippage checks, and PumpSwap AMM migrations via pumpfun-cli |
| [x-twitter-scraper](https://github.com/Xquik-dev/x-twitter-scraper) | `npx skills add Xquik-dev/x-twitter-scraper` | X API & Twitter scraper skill for AI coding agents -- tweet search, user lookup, follower extraction, engagement metrics, giveaway draws, trending topics, account monitoring, and 19 extraction tools |
| [claude-skills](https://github.com/alirezarezvani/claude-skills) | `git clone` | 192 production-ready skills across 9 domains (engineering, marketing, product, compliance, C-level advisory) with 254 Python automation tools. 5,300+ stars |
| [faf-skills](https://github.com/Wolfe-Jam/faf-skills) | `git clone` | 31 Claude Code skills for persistent project context (.faf, `application/vnd.faf+yaml`). Scoring, sync, testing, publishing, MCP server creation, architecture docs. Anthropic MCP #2759. |
| [n8n-skills](https://github.com/czlonkowski/n8n-skills) | `git clone` | 7 complementary skills for building production-ready n8n workflows. Covers 525+ nodes, 2,653+ templates. 3,400+ stars |
| [claude-code-best-practice](https://github.com/shanraisshan/claude-code-best-practice) | `git clone` | Comprehensive reference implementation for Claude Code configuration -- skills, subagents, hooks, commands with practical examples. 17,400+ stars |
| [ADHX](https://github.com/itsmemeworks/adhx) | `/plugin marketplace add itsmemeworks/adhx` or `curl -sL https://raw.githubusercontent.com/itsmemeworks/adhx/main/skills/adhx/SKILL.md -o ~/.claude/skills/adhx/SKILL.md` | Fetch any X/Twitter post as clean LLM-friendly JSON — no scraping, works with tweets and full X Articles |
| [SkillNav](https://github.com/skillnav-dev/skillnav-skill) | `clawhub install HuiW86/skillnav` | Search 3,900+ MCP servers with install commands, get daily AI brief, query arXiv papers, and discover trending tools -- all in Chinese. Curated by skillnav.dev editorial team |
| [naming](https://github.com/glacierphonk/naming) | `git clone https://github.com/glacierphonk/naming ~/.claude/skills/naming` | Metaphor-driven naming for products, SaaS, brands, bots, and open source projects. Produces memorable, meaningful names |
| [moyu](https://github.com/uucz/moyu) | `claude skill install --url https://github.com/uucz/moyu --skill moyu` | Anti-over-engineering skill that teaches AI restraint. 5 variants (standard/lite/strict/en/ja), 10 platforms. Benchmarked: 66% code reduction vs baseline |
| [Claudify](https://claudify.tech) | `npx create-claudify` | Complete operating system for Claude Code with 1,727 skills across 31 categories, 9 specialist agents with persistent memory, 21 slash commands, and automated quality checks |
| [Axiom](https://github.com/Guipetris/axiom) | `npx skills add Guipetris/axiom` | Contract-enforced autonomous pipeline: 8 stages from idea to PR with EARS requirements, ATDD (tests before implementation), RALPLAN-DR deliberation with ADR, 3 independent parallel reviewers, classified self-correction (SYNTAX/LOGIC/ARCH/AMBIGUOUS), cross-run project memory, and stage rollback. Zero dependencies beyond git and gh. |
| [StitchFlow](https://github.com/yshishenya/stitchflow) | `git clone https://github.com/yshishenya/stitchflow && cd stitchflow && bash install.sh --target all` | Cross-agent Stitch UI design bundle for turning briefs and mockups into screens, variants, Tailwind-friendly HTML, and screenshots |

| [Cost Optimizer](https://github.com/fullstackcrew-alpha/skill-cost-optimizer) | `git clone https://github.com/fullstackcrew-alpha/skill-cost-optimizer` | Save 60-80% on AI token costs with smart model routing, context compression, heartbeat tuning, usage reports, and config generation |
| [Overnight Worker](https://github.com/fullstackcrew-alpha/skill-overnight-worker) | `git clone https://github.com/fullstackcrew-alpha/skill-overnight-worker` | Autonomous overnight work agent — assign tasks before sleep, get structured results by morning with smart task decomposition, web research, and push notifications |
| [Smart PR Review](https://github.com/fullstackcrew-alpha/skill-smart-pr-review) | `git clone https://github.com/fullstackcrew-alpha/skill-smart-pr-review` | Opinionated AI code reviewer with 6-layer deep review, Devil's Advocate mode, and standardized MUST FIX / SHOULD FIX / SUGGESTION output for TS/JS, Python, Go, Rust |
| [DevOps Agent](https://github.com/fullstackcrew-alpha/skill-devops-agent) | `git clone https://github.com/fullstackcrew-alpha/skill-devops-agent` | One-click deploy, monitoring setup (Prometheus+Grafana), scheduled backups, and fault diagnosis with safety-first design including confirmation prompts, dry-run, and snapshot rollback |
| [CN Content Matrix](https://github.com/fullstackcrew-alpha/skill-cn-content-matrix) | `git clone https://github.com/fullstackcrew-alpha/skill-cn-content-matrix` | Chinese multi-platform content generator for Xiaohongshu, WeChat, Douyin, and Bilibili with true style transfer, compliance review, and sensitive word detection |
| [D3.js Visualization](https://github.com/chrisvoncsefalvay/claude-d3js-skill) | `git clone` | Generate interactive D3.js data visualizations from Claude Code |
| [iOS Simulator](https://github.com/conorluddy/ios-simulator-skill) | `git clone` | Interact with iOS Simulator for mobile testing and screenshot capture |
| [Playwright Automation](https://github.com/lackeyjb/playwright-skill) | `git clone` | Browser automation skill for end-to-end testing and web interaction |
| [threat-hunting-with-sigma-rules](https://github.com/jthack/threat-hunting-with-sigma-rules-skill) | `git clone` | Sigma-rule-based threat detection and security log analysis |
| [FFUF Web Fuzzing](https://github.com/jthack/ffuf_claude_skill) | `git clone` | Web vulnerability fuzzing and security testing via FFUF |
| [Markdown to EPUB](https://github.com/smerchek/claude-epub-skill) | `git clone` | Convert markdown files into EPUB ebooks |
| [CSV Data Summarizer](https://github.com/coffeefuelbump/csv-data-summarizer-claude-skill) | `git clone` | Generate insights and summaries from CSV data files |
| [tapestry](https://github.com/michalparkola/tapestry-skills-for-claude-code) | `git clone` | Knowledge networks, iterative learning, article extraction, and YouTube transcript processing |

### Installing Skills

**Browse and install via SkillKit** (recommended):

```bash
npx skillkit@latest install claude-code-toolkit/tdd-mastery
```

### 15,000+ Skills via SkillKit Marketplace

This toolkit includes 35 curated skills. For access to **400,000+ additional skills** across every domain, use [SkillKit](https://agenstskills.com):

```bash
npx skillkit@latest                    # Launch interactive TUI
npx skillkit@latest search "react"     # Search 400,000+ skills
npx skillkit@latest recommend          # AI-powered skill recommendations
```

Browse the full marketplace at [agenstskills.com](https://agenstskills.com). SkillKit supports 32+ AI coding agents including Claude Code, Cursor, Codex, Gemini CLI, and more.

---

## Commands

Forty-two slash commands organized into eight categories. Drop these into your project's `.claude/commands/` directory.

### Git (7 commands)

| Command | File | Description |
|---------|------|-------------|
| `/commit` | [`commit.md`](commands/git/commit.md) | Generate conventional commit from staged changes |
| `/pr-create` | [`pr-create.md`](commands/git/pr-create.md) | Create PR with summary, test plan, and labels |
| `/changelog` | [`changelog.md`](commands/git/changelog.md) | Generate changelog from commit history |
| `/release` | [`release.md`](commands/git/release.md) | Create tagged release with auto-generated notes |
| `/worktree` | [`worktree.md`](commands/git/worktree.md) | Set up git worktrees for parallel development |
| `/fix-issue` | [`fix-issue.md`](commands/git/fix-issue.md) | Fix a GitHub issue by number |
| `/pr-review` | [`pr-review.md`](commands/git/pr-review.md) | Review a pull request with structured feedback |

### Testing (6 commands)

| Command | File | Description |
|---------|------|-------------|
| `/tdd` | [`tdd.md`](commands/testing/tdd.md) | Test-driven development workflow |
| `/test-coverage` | [`test-coverage.md`](commands/testing/test-coverage.md) | Analyze coverage and suggest missing tests |
| `/e2e` | [`e2e.md`](commands/testing/e2e.md) | Generate end-to-end test scenarios |
| `/integration-test` | [`integration-test.md`](commands/testing/integration-test.md) | Generate integration tests for API endpoints |
| `/snapshot-test` | [`snapshot-test.md`](commands/testing/snapshot-test.md) | Generate snapshot/golden file tests |
| `/test-fix` | [`test-fix.md`](commands/testing/test-fix.md) | Diagnose and fix failing tests |

### Architecture (6 commands)

| Command | File | Description |
|---------|------|-------------|
| `/plan` | [`plan.md`](commands/architecture/plan.md) | Create implementation plan with risk assessment |
| `/refactor` | [`refactor.md`](commands/architecture/refactor.md) | Structured code refactoring workflow |
| `/migrate` | [`migrate.md`](commands/architecture/migrate.md) | Framework or library migration |
| `/adr` | [`adr.md`](commands/architecture/adr.md) | Write Architecture Decision Record |
| `/diagram` | [`diagram.md`](commands/architecture/diagram.md) | Generate Mermaid diagrams from code |
| `/design-review` | [`design-review.md`](commands/architecture/design-review.md) | Conduct structured design review |

### Documentation (5 commands)

| Command | File | Description |
|---------|------|-------------|
| `/doc-gen` | [`doc-gen.md`](commands/documentation/doc-gen.md) | Generate documentation from code |
| `/update-codemap` | [`update-codemap.md`](commands/documentation/update-codemap.md) | Update project code map |
| `/api-docs` | [`api-docs.md`](commands/documentation/api-docs.md) | Generate API docs from route handlers |
| `/onboard` | [`onboard.md`](commands/documentation/onboard.md) | Create onboarding guide for new devs |
| `/memory-bank` | [`memory-bank.md`](commands/documentation/memory-bank.md) | Update CLAUDE.md memory bank |

### Security (5 commands)

| Command | File | Description |
|---------|------|-------------|
| `/audit` | [`audit.md`](commands/security/audit.md) | Run security audit on code and dependencies |
| `/hardening` | [`hardening.md`](commands/security/hardening.md) | Apply security hardening measures |
| `/secrets-scan` | [`secrets-scan.md`](commands/security/secrets-scan.md) | Scan for leaked secrets and credentials |
| `/csp` | [`csp.md`](commands/security/csp.md) | Generate Content Security Policy headers |
| `/dependency-audit` | [`dependency-audit.md`](commands/security/dependency-audit.md) | Audit dependencies for vulnerabilities |

### Refactoring (5 commands)

| Command | File | Description |
|---------|------|-------------|
| `/dead-code` | [`dead-code.md`](commands/refactoring/dead-code.md) | Find and remove dead code |
| `/simplify` | [`simplify.md`](commands/refactoring/simplify.md) | Reduce complexity of current file |
| `/extract` | [`extract.md`](commands/refactoring/extract.md) | Extract function, component, or module |
| `/rename` | [`rename.md`](commands/refactoring/rename.md) | Rename symbol across the codebase |
| `/cleanup` | [`cleanup.md`](commands/refactoring/cleanup.md) | Remove dead code and unused imports |

### DevOps (5 commands)

| Command | File | Description |
|---------|------|-------------|
| `/dockerfile` | [`dockerfile.md`](commands/devops/dockerfile.md) | Generate optimized Dockerfile |
| `/ci-pipeline` | [`ci-pipeline.md`](commands/devops/ci-pipeline.md) | Generate CI/CD pipeline config |
| `/k8s-manifest` | [`k8s-manifest.md`](commands/devops/k8s-manifest.md) | Generate Kubernetes manifests |
| `/deploy` | [`deploy.md`](commands/devops/deploy.md) | Deploy to configured environment |
| `/monitor` | [`monitor.md`](commands/devops/monitor.md) | Set up monitoring and alerting |

### Workflow (3 commands)

| Command | File | Description |
|---------|------|-------------|
| `/checkpoint` | [`checkpoint.md`](commands/workflow/checkpoint.md) | Save session progress and context |
| `/wrap-up` | [`wrap-up.md`](commands/workflow/wrap-up.md) | End session with summary and learnings |
| `/orchestrate` | [`orchestrate.md`](commands/workflow/orchestrate.md) | Run multi-agent workflow pipeline |

### Using Commands

Copy to your project:

```bash
cp -r commands/ .claude/commands/
```

Then invoke in Claude Code:

```
/commit
/tdd src/utils/parser.ts
/audit
/orchestrate feature "Add user authentication"
```

---

## Hooks

Twenty hook scripts covering all eight Claude Code lifecycle events. Place `hooks.json` in your `.claude/` directory.

### Hook Scripts

| Script | Trigger | Purpose |
|--------|---------|---------|
| `session-start.js` | SessionStart | Load project context, detect package manager |
| `session-end.js` | SessionEnd | Save session state for next session |
| `context-loader.js` | SessionStart | Load CLAUDE.md, git status, pending todos |
| `learning-log.js` | SessionEnd | Extract and save session learnings |
| `pre-compact.js` | PreCompact | Save important context before compaction |
| [`smart-approve.py`](https://github.com/liberzon/claude-hooks) | PreToolUse (Bash) | Decompose compound bash commands (&&, \|\|, ;, \|, $()) into sub-commands and check each against allow/deny patterns |
| `block-dev-server.js` | PreToolUse (Bash) | Block dev server commands outside tmux |
| `pre-push-check.js` | PreToolUse (Bash) | Verify branch and remote before push |
| `block-md-creation.js` | PreToolUse (Write) | Block unnecessary .md file creation |
| `commit-guard.js` | PreToolUse (Bash) | Validate conventional commit messages |
| `secret-scanner.js` | PreToolUse (Write/Edit) | Block files containing secrets |
| `post-edit-check.js` | PostToolUse (Write/Edit) | Run linter after file edits |
| `auto-test.js` | PostToolUse (Write/Edit) | Run related tests after edits |
| `type-check.js` | PostToolUse (Write/Edit) | TypeScript type checking after edits |
| `lint-fix.js` | PostToolUse (Write/Edit) | Auto-fix lint issues |
| `bundle-check.js` | PostToolUse (Bash) | Check bundle size after builds |
| `suggest-compact.js` | PostToolUse (Bash) | Suggest compaction at edit intervals |
| `stop-check.js` | Stop | Remind to run tests if code was modified |
| `notification-log.js` | Notification | Log notifications for later review |
| `prompt-check.js` | UserPromptSubmit | Detect vague prompts, suggest clarification |

### Related SDKs

If you prefer a typed, npm-installable foundation for writing hooks rather than raw scripts:

- [claude-code-hooks](https://github.com/Payshak/claude-code-hooks) — TypeScript SDK with `defineHook()`, typed event payloads for all 5 hook events, response builders, and unit-testable `.handle()` method. Zero dependencies.

### Installing Hooks

```bash
cp hooks/hooks.json .claude/hooks.json
cp -r hooks/scripts/ .claude/hooks/scripts/
```

### Quick Setup with cc-safe-setup

Install 8 production-tested safety hooks in one command — destructive command blocker, branch push protection, secret leak prevention, syntax validation, and more:

```bash
npx cc-safe-setup
```

Includes `--audit` (score your setup 0-100), `--scan` (detect tech stack, recommend hooks), and `--verify` (test each hook). See [cc-safe-setup](https://github.com/yurukusa/cc-safe-setup) for details.

---

## Rules

Fifteen coding rules that enforce consistent patterns. Add to `.claude/rules/` or reference in `CLAUDE.md`.

| Rule | File | What It Enforces |
|------|------|-----------------|
| Coding Style | [`coding-style.md`](rules/coding-style.md) | Naming conventions, file organization, import ordering |
| Git Workflow | [`git-workflow.md`](rules/git-workflow.md) | Branching, commit format, PR process |
| Testing | [`testing.md`](rules/testing.md) | Test structure, coverage targets, mocking guidelines |
| Security | [`security.md`](rules/security.md) | Input validation, secrets, parameterized queries |
| Performance | [`performance.md`](rules/performance.md) | Lazy loading, caching, bundle optimization |
| Documentation | [`documentation.md`](rules/documentation.md) | JSDoc for public APIs, inline comments policy |
| Error Handling | [`error-handling.md`](rules/error-handling.md) | Explicit handling, typed errors, no empty catch |
| Agents | [`agents.md`](rules/agents.md) | Agent design patterns, handoff protocols |
| API Design | [`api-design.md`](rules/api-design.md) | REST conventions, status codes, versioning |
| Accessibility | [`accessibility.md`](rules/accessibility.md) | WCAG 2.2, ARIA, semantic HTML |
| Database | [`database.md`](rules/database.md) | Query patterns, migrations, N+1 prevention |
| Dependency Management | [`dependency-management.md`](rules/dependency-management.md) | Version pinning, audit, update policies |
| Code Review | [`code-review.md`](rules/code-review.md) | Review checklist, approval criteria |
| Monitoring | [`monitoring.md`](rules/monitoring.md) | Logging standards, metrics, alerting |
| Naming | [`naming.md`](rules/naming.md) | Naming conventions per language |

---

## Templates

- **[claude-code-blueprint](https://github.com/faizkhairi/claude-code-blueprint)** - Battle-tested reference architecture for Claude Code power users. Specialized agents with model hhtiering, natural-language skills, lifecycle hooks, path-scoped rules, starter presets, benchmarks, battle stories, and cross-tool mapping. Zero dependencies, MIT licensed.
- **[The CLAUDE.md Bible](https://echochime3.gumroad.com/l/claudemd-bible)** - 25 stack-specific CLAUDE.md configs covering React, Next.js, FastAPI, Django, Svelte, Chrome Extensions, CLI tools, MCP servers, and more. Each config is 80-150 lines of tested rules for the specific patterns and pitfalls of each stack, plus a masterclass guide.


Seven CLAUDE.md templates for different project types.

| Template | File | Use Case |
|----------|------|----------|
| Minimal | [`minimal.md`](templates/claude-md/minimal.md) | Small projects, scripts, quick prototypes |
| Standard | [`standard.md`](templates/claude-md/standard.md) | Most projects -- covers preferences, rules, workflows |
| Comprehensive | [`comprehensive.md`](templates/claude-md/comprehensive.md) | Large codebases with detailed conventions |
| Monorepo | [`monorepo.md`](templates/claude-md/monorepo.md) | Turborepo/Nx monorepo with multiple packages |
| Enterprise | [`enterprise.md`](templates/claude-md/enterprise.md) | Large teams with compliance and SSO |
| Python Project | [`python-project.md`](templates/claude-md/python-project.md) | FastAPI/Django Python projects |
| Fullstack App | [`fullstack-app.md`](templates/claude-md/fullstack-app.md) | Next.js + API fullstack applications |

```bash
cp templates/claude-md/standard.md CLAUDE.md
```

---

## MCP Configs

Thirteen curated Model Context Protocol server configurations.

| Config | File | Servers Included |
|--------|------|-----------------|
| Recommended | [`recommended.json`](mcp-configs/recommended.json) | 14 essential servers for general development |
| Full Stack | [`fullstack.json`](mcp-configs/fullstack.json) | Filesystem, GitHub, Postgres, Redis, Puppeteer |
| Kubernetes | [`kubernetes.json`](mcp-configs/kubernetes.json) | kubectl-mcp-server, Docker, GitHub |
| Data Science | [`data-science.json`](mcp-configs/data-science.json) | Jupyter, SQLite, PostgreSQL, Filesystem |
| Frontend | [`frontend.json`](mcp-configs/frontend.json) | Puppeteer, Figma, Storybook |
| Crypto / DeFi | [`crypto-defi.json`](mcp-configs/crypto-defi.json) | defi-mcp, Filesystem, Fetch, Memory |
| DevOps | [`devops.json`](mcp-configs/devops.json) | AWS, Docker, GitHub, Terraform, Sentry |
| Research | [`research.json`](mcp-configs/research.json) | BGPT scientific papers, Brave Search, Fetch, Memory, Filesystem |
| Observability | [`observability.json`](mcp-configs/observability.json) | Iris eval & observability for agent tracing, quality evaluation, and cost tracking |
| Security | [`security.json`](mcp-configs/security.json) | Ghidra reverse engineering, Snyk vulnerability scanning |
| Design | [`design.json`](mcp-configs/design.json) | Figma design context, Blender 3D automation |
| Workflow Automation | [`workflow-automation.json`](mcp-configs/workflow-automation.json) | n8n workflow builder, Pipedream integration |
| Mobile | [`mobile.json`](mcp-configs/mobile.json) | Android ADB automation, Xcode build tools |

---

## Contexts

Five context modes that configure Claude Code's behavior for different tasks.

| Context | File | Focus |
|---------|------|-------|
| Development | [`dev.md`](contexts/dev.md) | Iterate fast, follow patterns, test alongside code |
| Code Review | [`review.md`](contexts/review.md) | Check logic, security, edge cases |
| Research | [`research.md`](contexts/research.md) | Evaluate tools, compare alternatives, document findings |
| Debug | [`debug.md`](contexts/debug.md) | Reproduce, hypothesize, fix root cause, regression test |
| Deploy | [`deploy.md`](contexts/deploy.md) | Pre-deploy checklist, staging-first, rollback criteria |

---

## Examples

Three walkthrough examples demonstrating real toolkit usage.

| Example | File | Description |
|---------|------|-------------|
| Session Workflow | [`session-workflow.md`](examples/session-workflow.md) | End-to-end productive development session |
| Multi-Agent Pipeline | [`multi-agent-pipeline.md`](examples/multi-agent-pipeline.md) | Chaining agents for a Stripe billing feature |
| Project Setup | [`project-setup.md`](examples/project-setup.md) | Setting up a new project with the full toolkit |

---

## Setup

```bash
bash setup/install.sh
```

The interactive installer clones the repo, symlinks configs, and installs plugins.

---

## Project Structure

```
claude-code-toolkit/               850+ files
  plugins/                         150+ plugins (220 command files + external)
  agents/                          135 agents across 10 categories
    core-development/              13 agents
    language-experts/              25 agents
    infrastructure/                11 agents
    quality-assurance/             10 agents
    data-ai/                       15 agents
    developer-experience/          15 agents
    specialized-domains/           15 agents
    business-product/              12 agents
    orchestration/                 8 agents
    research-analysis/             11 agents
  skills/                          35 SKILL.md files
  commands/                        42 commands across 8 categories
  hooks/
    hooks.json                     25 hook entries
    scripts/                       19 Node.js scripts
  rules/                           15 coding rules
  templates/claude-md/             7 CLAUDE.md templates
  mcp-configs/                     8 server configurations
  contexts/                        5 context modes
  examples/                        3 walkthrough examples
  setup/                           Interactive installer
```

---

## Companion Apps & GUIs

| Name | Stars | Description |
|------|-------|-------------|
| [ctrl](https://ctrl.bulletproof.sh) | - | Pixel-art office that visualizes AI coding agents (Claude Code, Codex, Gemini) working in real time. Standalone web app + daemon, relay sharing for remote access, multi-agent support |
| [Opcode](https://github.com/winfunc/opcode) | 21,000+ | Tauri 2 desktop GUI and toolkit for Claude Code -- create custom agents with visual editor, usage analytics, MCP integration |
| [CloudCLI](https://github.com/siteboon/claudecodeui) | 8,400+ | Free open-source web/mobile UI for Claude Code, Cursor CLI, and Codex. Responsive design, integrated shell, file explorer, git explorer |
| [Companion](https://github.com/The-Vibe-Company/companion) | 2,200+ | Web & mobile UI for Claude Code & Codex. Launch parallel sessions, stream responses, approve tools, session recovery |
| [Ruflo](https://github.com/ruvnet/ruflo) | 21,200+ | Agent orchestration platform -- deploy multi-agent swarms, coordinate autonomous workflows, distributed swarm intelligence, RAG integration |
| [Vibe Kanban](https://github.com/BloopAI/vibe-kanban) | 23,200+ | Kanban-based orchestration for 10+ coding agents with isolated git worktrees per agent |
| [Claude-Code-Workflow](https://github.com/catlog22/Claude-Code-Workflow) | 1,400+ | JSON-driven multi-agent cadence-team framework with intelligent CLI orchestration (Gemini/Qwen/Codex) |
| [ccswarm](https://github.com/nwiizo/ccswarm) | 127 | Rust-based multi-agent orchestration with specialized agent pools, Git worktree isolation, 93% token reduction |
| [parallel-code](https://github.com/johannesjo/parallel-code) | 370+ | Run Claude Code, Codex, and Gemini side by side -- each in its own git worktree |
| [Bernstein](https://github.com/chernistry/bernstein) | 5+ | Python multi-agent orchestrator — spawns Claude Code, Codex CLI, and Gemini CLI in parallel on isolated git worktrees, verifies with tests, auto-commits. Zero LLM tokens on coordination |
| [Poirot](https://github.com/LeonardoCardoso/Poirot) | 96 | macOS app for browsing Claude Code sessions, viewing diffs, and re-running commands. Reads local transcripts, runs offline |
| [TokenEater](https://github.com/AThevon/TokenEater) | 179 | Native macOS menu bar app for monitoring Claude AI usage limits and watching coding sessions live |
| [Claw](https://github.com/jamesrochabrun/Claw) | 86 | Native macOS app wrapping Claude Code SDK in Swift. Plan Mode, MCP Integration, Custom System Prompts |
| [The Claude Protocol](https://github.com/AvivK5498/The-Claude-Protocol) | 149 | Enforcement layer wrapping Claude Code with 13 hooks -- blocks unsafe operations, enforces worktree isolation |
| [Notch So Good](https://github.com/deepshal99/notch-so-good) | new | macOS notch-based session monitor with pixel-art companion, 13 animations, smart notifications, multi-session support |
| [crit](https://github.com/tomasz-tomczyk/crit) | 105 | Local browser UI for inline code review of any file or agent output; integrates with Claude Code via plan-hook to review and approve plans before execution, outputs structured .crit.json for agent consumption. |
| [Untether](https://github.com/littlebearapps/untether) | 12 | Telegram bridge for Claude Code (and 5 other AI agents). Send tasks by voice or text, stream progress, approve changes with inline buttons from your phone |
| [OctoAlly](https://github.com/ai-genius-automations/octoally) | 18 | AI coding session orchestration dashboard -- multi-agent hive-mind via RuFlo, Whisper voice dictation, tmux session persistence, built-in git source control, Electron desktop app |
| [tokburn](https://github.com/lsvishaal/tokburn) | 3 | Local analytics dashboard for Claude Code -- calculates API-equivalent costs, detects waste patterns (repeated reads, floundering, cost outliers), serves web UI + REST API. Zero network calls, zero accounts, zero telemetry. `uvx tokburn serve`. |
| [skill-builder](https://github.com/Scottpedia0/skill-builder) | new | Analyzes your activity (shell history, git, browser, Claude threads) and generates working skills via LLM. 15 built-in skills + unlimited AI-generated. React UI with MCP server builder |
| [claude-workspace-snapshot](https://github.com/REMvisual/claude-workspace-snapshot) | new | Snapshot and restore live Claude Code sessions as named, color-coded Windows Terminal tabs. Detects running sessions via process inspection and .jsonl file activity. Windows only |
| [KANBAII](https://github.com/martinmsaavedra/kanbaii) | new | AI-native kanban board for Claude Code — plan visually, track progress, let AI execute. Sequential engine (Ralph), parallel multi-agent (Teams), cost tracking, real-time dashboard. `npx kanbaii start` |
| [Claude Session Visualizer](https://github.com/anaypaul/claude-session-visualizer) | new | Live visualization dashboard for Claude Code sessions with execution trees, token cost tracking, thinking trace exploration, and error debugging |
| [CCHub](https://github.com/Moresl/cchub) | New | Tauri 2.0 desktop app for managing the full Claude Code ecosystem -- MCP servers, skills, hooks, config profiles. Auto-scans Claude Code, Claude Desktop, Cursor configs |
| [AionUI](https://github.com/iOfficeAI/AionUi) | 20,500+ | Free local open-source 24/7 Cowork app for Gemini CLI, Claude Code, Codex, and OpenCode |
| [chops](https://github.com/Shpigford/chops) | 1,000+ | macOS app to browse, edit, and manage skills across Claude Code, Cursor, Codex, Windsurf, and Amp |

---

## Ecosystem

Notable projects, directories, and resources across the Claude Code ecosystem.

| Name | Stars | Description |
|------|-------|-------------|
| [claude-mem](https://github.com/thedotmack/claude-mem) | 35,900+ | Auto-captures everything Claude does, compresses with AI, injects context into future sessions. #1 trending GitHub Feb 2026 |
| [wshobson/agents](https://github.com/wshobson/agents) | 31,300+ | 112 specialized agents, 16 orchestrators, 146 skills, 79 tools in 72 focused plugins |
| [oh-my-claudecode](https://github.com/Yeachan-Heo/oh-my-claudecode) | 9,900+ | Teams-first multi-agent orchestration with 19 specialized agents and 28 skills |
| [ccusage](https://github.com/ryoppippi/ccusage) | 11,500+ | CLI for analyzing Claude Code usage from local JSONL files. Offline mode, zero API calls needed |
| [cc-statistics](https://github.com/androidZzT/cc-statistics) | 270+ | Three-in-one Claude Code stats: CLI + Web + native macOS SwiftUI panel. Token costs, code changes by language, efficiency scoring, weekly reports. Supports Codex and Cursor too |
| [ccpm](https://github.com/automazeio/ccpm) | 7,600+ | Project management with GitHub Issues + Git worktrees for parallel agent execution |
| [claude-code-system-prompts](https://github.com/Piebald-AI/claude-code-system-prompts) | 5,900+ | Extracted system prompts from Claude Code, updated for each release |
| [claude-context](https://github.com/zilliztech/claude-context) | 5,600+ | Semantic code search MCP by Zilliz -- hybrid BM25 + vector search, ~40% token reduction |
| [claude-skills](https://github.com/alirezarezvani/claude-skills) | 5,300+ | 192 skills across 9 domains with 254 Python automation tools |
| [peon-ping](https://github.com/PeonPing/peon-ping) | 3,900+ | Warcraft III Peon voice notifications for Claude Code and other agents |
| [n8n-skills](https://github.com/czlonkowski/n8n-skills) | 3,400+ | Skills for building production-ready n8n workflows |
| [claude-hooks-mastery](https://github.com/disler/claude-code-hooks-mastery) | 3,300+ | Complete mastery guide for Claude Code hooks with production-ready scripts |
| [claude-supermemory](https://github.com/supermemoryai/claude-supermemory) | 2,300+ | Persistent memory across sessions using Supermemory |
| [myclaude](https://github.com/stellarlinkco/myclaude) | 2,400+ | Multi-agent orchestration routing to Claude Code, Codex, Gemini, and OpenCode |
| [claude-code-mcp](https://github.com/steipete/claude-code-mcp) | 1,100+ | Run Claude Code as a one-shot MCP server -- an agent in your agent |
| [ccmanager](https://github.com/kbwo/ccmanager) | 940+ | Session manager supporting 8 coding agents with smart auto-approval |
| [cog](https://github.com/marciopuga/cog) | 240+ | Cognitive architecture for Claude Code -- persistent memory, self-reflection, and foresight via plain-text conventions. Zero dependencies, just CLAUDE.md + markdown files |
| [Cortex](https://github.com/SKULLFIRE07/cortex-memory) | -- | Persistent AI memory for coding assistants. Auto-captures decisions, patterns, and context across sessions. VSCode extension + CLI + MCP server. Free |
| [openclaw-self-healing](https://github.com/Ramsbaby/openclaw-self-healing) | 32+ | 4-tier autonomous crash recovery for Claude Code and any service — 64% auto-resolved, LLM-agnostic (Claude/GPT-4/Gemini/Ollama), Prometheus metrics |
| [CCM](https://github.com/dr5hn/ccm) | 8+ | Power-user toolkit for Claude Code — multi-account management with project bindings, session cleanup, environment snapshots, permissions audit, health diagnostics. Single bash script, no runtime dependencies beyond bash 4.4+ and jq. |
| [openclaw-memorybox](https://github.com/Ramsbaby/openclaw-memorybox) | 8+ | Memory hygiene CLI for Claude Code — prevents context overflow crashes, 83% MEMORY.md size reduction, zero dependencies |
| [openclaw-self-evolving](https://github.com/Ramsbaby/openclaw-self-evolving) | 2+ | Weekly self-improvement pipeline — scans Claude Code logs, proposes CLAUDE.md/AGENTS.md rule changes, zero API cost |
| [caliber](https://github.com/caliber-ai-org/ai-setup) | -- | CLI that fingerprints projects and generates AI agent configs (CLAUDE.md, skills, AGENTS.md). Scores quality, auto-refreshes, supports Claude Code + Cursor + Codex |
| [claude-starter-kit](https://github.com/awrshift/claude-starter-kit) | new | Ready-to-use project structure with persistent memory, session continuity, hooks, and 3 bundled skills (Gemini, Brainstorm, Design) |
| [claude-code-kickstart](https://github.com/ypollak2/claude-code-kickstart) | New | Opinionated starter kit — one command to install curated MCP servers, hooks, agents, and profiles. Includes auto-detect, 12 agents, 10 profiles, and 20+ shell commands |
| [claude-code-power-stack](https://github.com/bluzername/claude-code-power-stack) | new | Ghost memory, conversation search, session naming, and Manus-style planning in a single install with cheat sheet PDF |
| [toolpipe-mcp-server](https://github.com/COSAI-Labs/toolpipe-mcp-server) | -- | MCP server with 135+ developer utility tools (JSON formatter, hash generator, QR codes, PDF tools, regex tester, JWT decoder, UUID generator, SSL checker). npm: `@cosai-labs/toolpipe-mcp-server` |
| [clooks](https://github.com/mauribadnights/clooks) | new | Persistent hook daemon that replaces per-invocation spawning -- 112x faster hooks with batching, dependency resolution, metrics |
| [AIRIS MCP Gateway](https://github.com/agiletec-inc/airis-mcp-gateway) | new | Docker-based MCP multiplexer that aggregates 60+ tools behind 7 meta-tools, reducing context token usage by 97%. One command to start, auto-enables servers on demand |
| [gemini-claude-bridge](https://github.com/weijiafu14/gemini-claude-bridge) | new | Gemini-to-Claude protocol converter for using Gemini models as Claude Code backend. Fixes 3 LiteLLM bugs |
| [spartan-ai-toolkit](https://github.com/spartan-stratos/spartan-ai-toolkit) | new | Engineering discipline layer for Claude Code -- 67 slash commands, 20 coding rules, 27 skills, 9 agents, quality gates between every step. 8 stack profiles (Go, Python, Java, Kotlin, React, etc.), agent memory across sessions. Install: `npx @c0x12c/spartan-ai-toolkit@latest --local` |
| [AgenTopology](https://github.com/agentopology/agentopology) | New | Declarative language and CLI for multi-agent orchestration -- define agents, flows, gates, hooks, group chats in one `.at` file, scaffold to 7 platforms, interactive visualizer. Apache 2.0 |
| [brood-box](https://github.com/stacklok/brood-box) | 10+ | Run AI coding agents (Claude Code, Codex, OpenCode) inside hardware-isolated microVMs with snapshot isolation, egress control, and MCP authorization |
| [claude-kit](https://github.com/luiseiman/claude-kit) | 1 | Configuration factory for Claude Code -- 13 composable stacks, 6 agents, audit scoring, practices pipeline. Bootstraps and maintains .claude/ across projects |
| [Global Chat](https://github.com/pumanitro/global-chat) | -- | Cross-protocol MCP server discovery -- search 18K+ servers across 6+ registries. Also supports A2A and agents.txt. Free agents.txt validator. npm: `@global-chat/mcp-server` |
| [GAAI Framework](https://github.com/Fr-e-d/GAAI-framework) | 95+ | Drop-in governance layer (.gaai/ folder) -- backlog authorization, cross-session memory, decision tracking, QA gates, autonomous delivery daemon. Claude Code + Cursor + Codex CLI + Gemini CLI |
| [Claude Command Center](https://github.com/tuning-labs-oss/claude-command-center) | -- | Production-tested workspace template with session hooks, structured memory (4 types), multi-domain routing, daily task tracking, and interactive /setup onboarding. 6 domain templates, pre-commit safety, example skills |
| [Code Insights](https://github.com/melagiri/code-insights) | 8 | Local-first CLI and dashboard for analyzing AI coding sessions from Claude Code, Cursor, Codex CLI, Copilot CLI, and VS Code Copilot. SQLite-backed with terminal analytics, browser dashboard, and LLM-powered insights |
| [claude-code-cheat-sheet](https://cc.storyfox.cz/) | new | Complete one-page printable reference — all shortcuts, commands, CLI flags, MCP config, memory, skills, agents. Auto-updated daily from official docs. [EN](https://cc.storyfox.cz/) · [ZH](https://cc.storyfox.cz/zh/) · [JA](https://cc.storyfox.cz/jp/) · [KO](https://cc.storyfox.cz/kr/) |
| [agent-dotfiles](https://github.com/saqibameen/agent-dotfiles) | new | Write AI coding rules once, sync to every agent. Supports Command Code, Claude Code, Cursor, Copilot, Codex, OpenCode. |
| [zclean](https://github.com/whynowlab/zclean) | 19+ | Kills orphaned processes left behind by Claude Code and Codex. Stops zombie node/python/esbuild from eating your RAM |
| [Hindsight](https://github.com/vectorize-io/hindsight) | -- | State-of-the-art long-term memory for AI agents by Vectorize. Biomimetic retain/recall/reflect with 4 parallel retrieval strategies. Self-hosted or cloud, MIT-licensed. [Claude Code integration](https://hindsight.vectorize.io/integrations) |
| [healthcare-agents](https://github.com/ajhcs/healthcare-agents) | New | 51 specialized healthcare administration agents with MHA-level expertise across 10 divisions -- revenue cycle, compliance, quality, clinical ops, payer relations, health IT, and more |
| [cc-switch](https://github.com/farion1231/cc-switch) | 35,500+ | Cross-platform desktop All-in-One assistant for Claude Code, Codex, OpenCode, and Gemini CLI |
| [claude-code-router](https://github.com/musistudio/claude-code-router) | 30,700+ | Use Claude Code as coding infrastructure foundation with custom model routing and interaction |
| [SuperClaude](https://github.com/SuperClaude-Org/SuperClaude_Framework) | 22,000+ | Config framework with specialized commands, cognitive personas, and dev methodologies |
| [claude-code-templates](https://github.com/davila7/claude-code-templates) | 23,800+ | CLI tool for configuring and monitoring Claude Code projects and workflows |
| [planning-with-files](https://github.com/OthmanAdi/planning-with-files) | 17,600+ | Manus-style persistent markdown planning skill for structured project management |
| [claude-hud](https://github.com/jarrodwatts/claude-hud) | 15,200+ | Plugin showing context usage, active tools, running agents, todo progress in a HUD overlay |
| [awesome-claude-code-subagents](https://github.com/VoltAgent/awesome-claude-code-subagents) | 15,600+ | 100+ specialized Claude Code subagents organized by domain |
| [serena](https://github.com/oraios/serena) | 22,200+ | Semantic retrieval and editing MCP server for coding agents -- code-aware search and navigation |
| [Understand-Anything](https://github.com/Lum1104/Understand-Anything) | 7,000+ | Turns any codebase into an interactive knowledge graph for exploration |
| [n8n-mcp](https://github.com/czlonkowski/n8n-mcp) | 17,000+ | MCP for Claude Code to build and manage n8n automation workflows |

---

## XVARY Stock Research

- [XVARY Stock Research](https://github.com/xvary-research/claude-code-stock-analysis-skill) — Claude Code skill for public SEC EDGAR + market data: `/analyze`, `/score`, `/compare`. MIT.

---

## Resources

Tutorials, guides, and deep-dives on Claude Code.

| Resource | Type | Description |
|----------|------|-------------|
| [Claude Code Official Docs](https://docs.anthropic.com/en/docs/claude-code) | Docs | Official Anthropic documentation for Claude Code |
| [Context Engineering Guide](https://www.anthropic.com/research/long-running-Claude) | Guide | Anthropic's guide to long-running Claude Code sessions and scientific computing |
| [Auto Mode Engineering](https://www.anthropic.com/engineering/claude-code-auto-mode) | Blog | How Auto Mode's two-layer safety system works under the hood |
| [Claude Code Hooks Mastery](https://github.com/disler/claude-code-hooks-mastery) | Tutorial | Complete mastery guide with production-ready hook scripts |
| [Skills vs MCP vs Plugins](https://www.morphllm.com/context-engineering) | Guide | When to use which extension mechanism in Claude Code |
| [Context Engineering 101](https://newsletter.victordibia.com/p/context-engineering-101-how-agents) | Article | Three core strategies: compaction, isolation, agentic memory |
| [Agent Teams Explained](https://www.turingcollege.com/blog/claude-agent-teams-explained) | Guide | How multiple Claude Code instances coordinate as an AI engineering team |
| [84 Best Practices](https://discuss.huggingface.co/t/10-essential-claude-code-best-practices-you-need-to-know/174731) | Collection | Community-compiled Claude Code best practices from Hugging Face |
| [Computer Use from CLI](https://code.claude.com/docs/en/computer-use) | Docs | Let Claude control your desktop — open apps, click, type, screenshot. macOS, Pro/Max, v2.1.85+. Per-app approval, tiered access, Esc abort |
| [Dispatch & Remote Control](https://claude.com/blog/dispatch-and-computer-use) | Blog | Run Claude Code from phone/web, schedule recurring tasks, remote session control |
| [Claude Code Cheat Sheet](https://cc.storyfox.cz/) | Reference | One-page printable reference, auto-updated daily, 4 languages |
| [Multi-Agent Orchestra](https://addyosmani.com/blog/code-agent-orchestra/) | Blog | Addy Osmani's survey of multi-agent coding patterns |

## Related Awesome Lists

| List | Stars | Focus |
|------|-------|-------|
| [awesome-mcp-servers](https://github.com/appcypher/awesome-mcp-servers) | 5,300+ | Curated MCP servers across 30 categories |
| [awesome-ai-agents](https://github.com/e2b-dev/awesome-ai-agents) | 27,000+ | Open-source and closed-source AI agents |
| [awesome-llm-apps](https://github.com/Shubhamsaboo/awesome-llm-apps) | 104,000+ | LLM-powered applications and multi-agent systems |
| [awesome-claude-code (hesreallyhim)](https://github.com/hesreallyhim/awesome-claude-code) | 34,000+ | Skills, hooks, slash-commands, and orchestrators |
| [antigravity-awesome-skills](https://github.com/sickn33/antigravity-awesome-skills) | 28,700+ | 1,326+ installable agentic skills with CLI |
| [awesome-claude-code-subagents](https://github.com/VoltAgent/awesome-claude-code-subagents) | 15,600+ | 100+ specialized Claude Code subagents |
| [claude-code-best-practice](https://github.com/shanraisshan/claude-code-best-practice) | 25,000+ | Comprehensive reference implementation for Claude Code config |
| [awesome-claude-skills (Composio)](https://github.com/ComposioHQ/awesome-claude-skills) | 49,300+ | 30 curated skills + 832 SaaS automation templates via Composio. Strong on document processing, creative, and business skills |

## Contributing

Contributions are welcome. See [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines.

## License

[Apache-2.0](LICENSE)
