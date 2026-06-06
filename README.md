# Claude Code Toolkit

**The most comprehensive toolkit for Claude Code -- 135 agents, 35 curated skills (+400,000 via [SkillKit](https://agenstskills.com)), 42 commands, 176+ plugins, 20 hooks, 15 rules, 7 templates, 15 MCP configs, 26 companion apps, 53 ecosystem entries, and more.**

<p align="center">
  <a href="https://trendshift.io/repositories/21839" target="_blank"><img src="https://trendshift.io/api/badge/repositories/21839" alt="rohitg00%2Fawesome-claude-code-toolkit | Trendshift" style="width: 250px; height: 55px;" width="250" height="55"/></a>
</p>
  
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
- [MCP Configs](#mcp-configs) (14)
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
| [pro-workflow](https://github.com/rohitg00/pro-workflow) | 1,800+ | Battle-tested Claude Code workflows from power users. Self-correcting memory, parallel worktrees, wrap-up rituals, 8 hook types, 5 agents, and the 80/20 AI coding ratio. Install: `/plugin marketplace add rohitg00/pro-workflow` |
| [gstack](https://github.com/garrytan/gstack) | 68,200+ | Garry Tan's exact Claude Code setup: 6 opinionated tools that serve as CEO, Eng Manager, Release Manager, and QA Engineer. |

### All Plugins

| Plugin | Description |
|--------|-------------|
| [agento-patronum](https://github.com/emaarco/agento-patronum) | Protects sensitive files, credentials, and shell commands from unintended AI access via Claude Code hooks. Unlike settings.json deny rules, hooks are an enforcement layer you own and can verify. Ships with defaults for .env files, SSH keys, AWS credentials, and kubeconfig. |
| [skills-janitor](https://github.com/khendzel/skills-janitor) | Audit, deduplicate, check, fix, and track usage of your Claude Code skills. 9 slash commands, zero dependencies |
| [great_cto](https://github.com/avelikiy/great_cto) | Full SDLC pipeline plugin with 7 agents (tech-lead, senior-dev, qa-engineer, security-officer, devops, l3-support, project-auditor), 12-angle code review, 10 project archetypes, 13 compliance frameworks (SOC2/HIPAA/PCI-DSS/GDPR/ISO 27001), two-gate approval flow. Opus 4.7 advisor escalation, file-based, MIT |
| [aws-cost-saver](https://github.com/prajapatimehul/aws-cost-saver) | AWS cost optimization scanner with 173 automated checks, ML-powered rightsizing, and Zero Hallucination Pricing - Real result: 60% cost reduction |
| [claude-agentic-coding-playbook](https://github.com/john-wilmes/claude-agentic-coding-playbook) | Evidence-based practices for LLM-assisted development -- hooks, skills, scripts, and a best-practices guide with 58 citations. Includes 19+ guard/lifecycle hooks, investigation workflow, fleet indexing, and claude-loop for autonomous task queues. |
| [claude-code-mcp](https://github.com/steipete/claude-code-mcp) | Run Claude Code as a one-shot MCP server -- an agent in your agent. Permissions bypassed automatically. By Peter Steinberger. 1,100+ stars |
| [claude-code-system-prompts](https://github.com/Piebald-AI/claude-code-system-prompts) | Extracted system prompts from Claude Code -- 18 builtin tool descriptions, sub-agent prompts, utility prompts. Updated for each release. 5,900+ stars |
| [claude-context](https://github.com/zilliztech/claude-context) | Semantic code search MCP server by Zilliz (Milvus creators). Hybrid BM25 + dense vector search. ~40% token reduction. 5,600+ stars |
| [claude-cost-optimizer](https://github.com/Sagargupta16/claude-cost-optimizer) | Installable cost-mode skill (30-60% cost savings, up to 70% in strict mode) + 10 guides, 10 templates, budget hooks. Install: `npx skills add Sagargupta16/claude-cost-optimizer` |
| [fractal](https://github.com/rmolines/fractal) | Recursive project management for Claude Code. Decomposes goals into predicates, works the riskiest piece first, and re-evaluates as it learns |
| [a11y-audit](plugins/a11y-audit/) | Full accessibility audit with WCAG compliance checking |
| [accessibility-checker](plugins/accessibility-checker/) | Scan for accessibility issues and fix ARIA attributes in web applications |
| [adr-writer](plugins/adr-writer/) | Architecture Decision Records authoring and management |
| [AgentLint](https://github.com/0xmariowu/AgentLint) | Lint your repo for AI agent compatibility. 33 evidence-backed checks across 5 dimensions. Claude Code plugin. |
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
| [brooks-lint](https://github.com/hyhmrright/brooks-lint) | AI code reviews grounded in six classic engineering books (Brooks, Fowler, Martin, McConnell, Hunt & Thomas, Evans). Diagnoses code across 6 decay risk dimensions with structured findings (Symptom → Source → Consequence → Remedy). Supports PR review, architecture audit, tech debt assessment, and test quality review. v0.6 adds Mermaid dependency graphs. |
| [ccmanager](https://github.com/kbwo/ccmanager) | Coding agent session manager supporting Claude Code, Gemini CLI, Codex, Cursor, Copilot, Cline, OpenCode, Kimi CLI. Smart auto-approval via Haiku, devcontainer support. 940+ stars |
| [ccpm](https://github.com/automazeio/ccpm) | Project management using GitHub Issues + Git worktrees for parallel agent execution. Issue-analyze, epic-start, epic-merge commands. 7,600+ stars |
| [ccusage](https://github.com/ryoppippi/ccusage) | CLI for analyzing Claude Code/Codex usage from local JSONL files. Daily, monthly, session, billing-window reports. Offline, zero API calls. 11,500+ stars |
| [cc-cost](https://github.com/lob-labs/cc-cost) | Single-file Python CLI that parses Claude Code transcript JSONL and reports cost, prompt-cache hit rate, tool-call distribution, top expensive turns, and actionable optimization recommendations (`--diagnose`, `--md`, `--top N`). MIT, no third-party deps. |
| [getburnd](https://github.com/garvitsurana271/burnd) | Local-first cost-control CLI for Claude Code. Reads `~/.claude/projects/*.jsonl`, identifies 8 leak patterns (verbose context, tool loops, large file re-reads), prints savings estimates, generates a shareable report URL. MIT, zero telemetry. |
| [building-multiagent-systems](https://github.com/2389-research/building-multiagent-systems) | Architecture patterns for multi-agent systems: orchestrator-worker, pipeline, debate, and MapReduce topologies |
| [bundle-analyzer](plugins/bundle-analyzer/) | Frontend bundle size analysis and tree-shaking optimization |
| [chief](https://github.com/MiniCodeMonkey/chief) | CLI that wraps Claude Code in a loop. Define a PRD, run chief, go do anything else. Commits after each task, picks up where it left off. Homebrew installable. 380+ stars |
| [claudebase](https://github.com/rohithzr/claudebase) | Back up, restore, and sync your Claude Code config (settings, skills, agents, hooks, rules, memory, MCP) to a private GitHub repo. Named profiles, secret scanning, multi-machine conflict detection, automatic backups. 158 tests |
| [changelog-gen](plugins/changelog-gen/) | Generate changelogs from git history with conventional commit parsing |
| [changelog-writer](plugins/changelog-writer/) | Detailed changelog authoring from git history and PRs |
| [ci-debugger](plugins/ci-debugger/) | Debug CI/CD pipeline failures and fix configurations |
| [claude-hooks-mastery](https://github.com/disler/claude-code-hooks-mastery) | Complete mastery guide for Claude Code hooks -- UV single-file Python scripts, sub-agents, meta-agent, team-based validation, AI-generated audio feedback. 3,300+ stars |
| [claude-mem](https://github.com/thedotmack/claude-mem) | Automatically captures everything Claude does, compresses with AI, injects relevant context into future sessions. SQLite + full-text search. 35,900+ stars |
| [claude-notifications-go](https://github.com/777genius/claude-notifications-go) | Cross-platform smart notifications -- 6 types, click-to-focus, context analysis, webhooks. Single Go binary, zero deps. 340+ stars |
| [claude-ops](https://github.com/Lifecycle-Innovations-Limited/claude-ops) | Business operating system plugin for Claude Code. Morning briefings, unified inbox, autonomous PR merge, infrastructure monitoring, and YOLO autonomous mode. |
| [claude-scaffold](https://github.com/pyramidheadshark/claude-scaffold) | npx CLI that deploys CLAUDE.md, hooks, and 18 domain skills to any repository in one command. Skills auto-activate via hooks based on project context. Cross-repo sync via `update --all`. Install: `npx claude-scaffold init` |
| [claude-recap](https://github.com/hatawong/claude-recap) | Per-topic session memory using Shell hooks — archives each conversation topic as a separate Markdown summary. Two hooks, bash + Node.js, 100% local |
| [clirank-mcp-server](https://github.com/alexanderclapp/clirank-mcp-server) ([npm](https://www.npmjs.com/package/clirank-mcp-server)) | API discovery for agents -- scores 210+ APIs on CLI-friendliness across 11 signals. Find the right API for any task via MCP tools or REST (`curl "https://clirank.dev/api/discover?q=send+emails"`). No auth required |
| [/cht](https://github.com/kosoukhov/cht-cli) | Chat persistence for Claude Code — 13 slash commands + hooks for saving conversations as local markdown files. Crash-proof auto-save via hooks, project-based organization, search, and management. npm: `@kosoukhov/cht-cli` |
| [claude-rank](https://github.com/Houseofmvps/claude-rank) | SEO/GEO/AEO audit plugin — tells you why AI won't cite your site, then auto-fixes robots.txt, sitemap.xml, llms.txt, and JSON-LD. 170+ rules across 10 scanners, zero config |
| [claude-sounds](https://github.com/culminationAI/claude-sounds) | Audio feedback for Claude Code hooks — 10 events, 21 sounds, random rotation. macOS (`afplay`). |
| [claude-code-hooks](https://github.com/yurukusa/claude-code-hooks) | 15 production-tested hooks from 160+ hours of autonomous operation. Destructive command blocker, branch guard, syntax check, context monitor, permission auto-approver. Bash, zero deps |
| [claude-code-sessions](https://github.com/apappascs/claude-code-sessions) | Session intelligence plugin. 11 skills for full-text search, token analytics, task management, session comparison, timeline views, and context recovery across all sessions. Includes a web dashboard. Zero runtime dependencies, read-only |
| [cc-aws-keepalive](https://github.com/GeiserX/cc-aws-keepalive) | Keep Claude Code sessions alive through AWS credential expiry -- proactive expiration warnings, credential refresh bypass for Bedrock SSO/SAML, optional statusline countdown timer. 4 hook scripts, zero dependencies |
| [cc-safe-setup](https://github.com/yurukusa/cc-safe-setup) | One command (`npx cc-safe-setup`) to install 6 essential safety hooks in 10 seconds. Zero dependencies |
| [knowledge-graph](https://github.com/hilyfux/knowledge-graph) | Built on Anthropic internal engineering practices and Karpathy's AutoResearch methodology. A zero-dependency, git-native memory layer for Claude Code that persists learned context across sessions. Pure bash, ~3ms/event, privacy-first |
| [claude-supermemory](https://github.com/supermemoryai/claude-supermemory) | Persistent memory across sessions and projects using Supermemory. User profile injection at session start, automatic conversation capture. 2,300+ stars |
| [cortex](https://github.com/cdeust/Cortex) | Persistent memory for Claude Code — neuroscience-backed retrieval with thermodynamic decay, backed by 41 published papers. PostgreSQL + pgvector + sentence-transformers. 6 lifecycle hooks (SessionStart, UserPromptSubmit, PostToolUse, SessionEnd, Notification, SubagentStart), hierarchical recall, causal chains, knowledge graph navigation. Install and forget. |
| [code-architect](plugins/code-architect/) | Generate architecture diagrams and technical design documents |
| [code-explainer](plugins/code-explainer/) | Explain complex code and annotate files with inline documentation |
| [code-guardian](plugins/code-guardian/) | Automated code review, security scanning, and quality enforcement |
| [code-review-assistant](plugins/code-review-assistant/) | Automated code review with severity levels and actionable feedback |
| [eliniscan](https://github.com/AlpYenigun/eliniscan) | AI full codebase scanner. Opens a separate Claude session for every file — reads every line, misses nothing. Finds bugs, security, performance issues and auto-fixes. |
| [codebase-documenter](plugins/codebase-documenter/) | Auto-document entire codebase with inline comments and API docs |
| [codesight](https://github.com/Houseofmvps/codesight) | CLI token optimizer and AI context generator. Scans codebases to extract routes, schema, components, and dependencies for Claude Code, Cursor, Copilot, Codex, and Windsurf. 9x–13x token reduction. Zero runtime dependencies. `npx codesight` |
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
| [dig2crawl](https://github.com/ZENG3LD/dig2crawl) | Universal web crawler with Claude-powered CSS selector discovery. 4-level AI extraction escalation (CSS, browser actions, Claude Vision, captcha). Rust. |
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
| [gate4agent](https://github.com/ZENG3LD/gate4agent) | Universal Rust transport for CLI AI agents (Claude Code, Codex, Gemini, OpenCode). Pipe/NDJSON, PTY, and ACP modes. Published on crates.io. |
| [git-flow](plugins/git-flow/) | Git workflow management with feature branches, releases, and hotfix flows |
| [github-issue-manager](plugins/github-issue-manager/) | GitHub issue triage, creation, and management |
| [harness-evolver](https://github.com/raphaelchristi/harness-evolver) | LangSmith-native autonomous agent optimization. Multi-agent proposers evolve prompts, routing, tools, and architecture in isolated git worktrees. Install: `npx harness-evolver@latest` |
| [helm-charts](plugins/helm-charts/) | Helm chart generation and upgrade management |
| [idle-timing](https://github.com/clankercode/claude-inject-idle-time) | Injects hidden timing context (local time with UTC offset, idle seconds since last reply, previous-turn duration) into every user prompt so the model knows how long the conversation has been paused. Ships a statusline fragment for a live elapsed-time readout and a visible `[after Xm Ys]` note when you return from >10s idle. 57 tests, dual Unlicense/CC0. |
| [immich-photo-manager](https://github.com/drolosoft/immich-photo-manager) | Turn your self-hosted Immich photo library into a conversation — natural language search, geographic album curation, duplicate detection via perceptual hashing, library health audits, and interactive HTML galleries. 22 MCP tools, 11 skills, 5 slash commands |
| [import-organizer](plugins/import-organizer/) | Organize, sort, and clean import statements |
| [infrastructure-maintainer](plugins/infrastructure-maintainer/) | Infrastructure maintenance with security audits and update management |
| [ios-developer](plugins/ios-developer/) | iOS and Swift development with SwiftUI views and models |
| [k8s-helper](plugins/k8s-helper/) | Generate Kubernetes manifests and debug pod issues with kubectl |
| [leapfrog-mcp](https://github.com/anthonybono21-cloud/leapfrog) | Multi-session browser MCP server -- 15 parallel isolated Chromium sessions so multiple Claude Code terminals can browse simultaneously. 37 tools for navigation, extraction, interaction, network interception, and session profiles. 797 tests. Install: `npx -y leapfrog-mcp` |
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
| [nexus-agents](https://github.com/williamzujkowski/nexus-agents) | Intelligent orchestration platform routing tasks to Claude, Gemini, Codex, and OpenCode via Budget→TOPSIS→LinUCB composite router. 30 MCP tools (orchestrate, consensus voting, research pipelines), 12 expert agents, 17 skills, plugin-native `/agents` + hooks. Install: `/plugin marketplace add williamzujkowski/nexus-agents` |
| [onboarding-guide](plugins/onboarding-guide/) | New developer onboarding documentation generator |
| [oh-my-claudecode](https://github.com/Yeachan-Heo/oh-my-claudecode) | Teams-first multi-agent orchestration. 19 specialized agents, 28 skills. Full autonomous execution, Socratic questioning, N coordinated agents. 9,900+ stars |
| [onWatch](https://github.com/onllm-dev/onwatch) | Open-source Go CLI that tracks AI API quota usage across 7 providers (Synthetic, Z.ai, Anthropic, Codex, GitHub Copilot, MiniMax, Antigravity) with a background daemon (<50 MB RAM), zero telemetry, and a Material Design 3 web dashboard |
| [obey](https://github.com/Lexxes-Projects/obey) | Rule enforcement plugin. Save rules with natural language, enforce with 17 lifecycle hooks. Three scopes (global, stack-specific, project-local), active blocking via PreToolUse, completion checklists via Stop hook, audit trail, auto-detects rule-like language. Cross-platform. |
| [opcode](https://github.com/winfunc/opcode) | Tauri 2 desktop GUI and toolkit for Claude Code. Manage sessions, create custom agents with visual editor, usage analytics, MCP integration. 21,000+ stars |
| [openapi-expert](plugins/openapi-expert/) | OpenAPI spec generation, validation, and client code scaffolding |
| [optimize](plugins/optimize/) | Code optimization for performance and bundle size reduction |
| [ORCH](https://github.com/oxgeneral/ORCH) | CLI runtime orchestrating Claude Code, Codex, and Cursor as typed agent teams with state machine (todo→review→done), auto-retry, inter-agent messaging, goals, and TUI dashboard |
| [oss-autopilot](https://github.com/costajohnt/oss-autopilot) | Open source contribution manager — tracks PRs across repos, discovers issues, diagnoses CI failures, drafts maintainer responses. 7 agents, interactive commands, MCP server. Install: `/plugin marketplace add costajohnt/oss-autopilot` |
| [paco-framework](https://github.com/PenguinAlleyApps/paco-framework) | 1+ | Markdown-first multi-agent OS for Claude Code. Coordinates 3-16 specialized AI agents (Engineering, QA, Growth, Finance) with file-based dispatch, institutional memory, CEO Gate approval, and 24/7 scheduling. No Python required. MIT |
| [peon-ping](https://github.com/PeonPing/peon-ping) | Warcraft III Peon voice notifications (+ StarCraft, Portal, Zelda) for Claude Code and other agents. Desktop banners, auto-detects SSH/devcontainers. 3,900+ stars |
| [perf-profiler](plugins/perf-profiler/) | Performance analysis, profiling, and optimization recommendations |
| [performance-monitor](plugins/performance-monitor/) | Profile API endpoints and run benchmarks to identify performance bottlenecks |
| [plan](plugins/plan/) | Structured planning with risk assessment and time estimation |
| [preflight](https://github.com/preflight-dev/preflight) | 24-tool MCP server that catches vague prompts before they cost 2-3x in wrong→fix cycles. 12-category scorecards, correction pattern learning, cross-service contract awareness, session history search with LanceDB vectors, and cost estimation. `npx preflight-dev` |
| [pr-reviewer](plugins/pr-reviewer/) | Review pull requests with structured analysis and approve with confidence |
| [product-shipper](plugins/product-shipper/) | Ship features end-to-end with launch checklists and rollout plans |
| [production-grade](https://github.com/nagisanzenin/claude-code-production-grade-plugin) | 14-agent autonomous pipeline — PM, Architect, Backend, Frontend, QA, Security, Code Review, DevOps, SRE, Data Scientist, Technical Writer, Skill Maker, Polymath co-pilot. Two-wave parallel execution, brownfield-safe. |
| [product-org-os](https://github.com/yohayetsion/product-org-os) | 150+ skills and 12 role-based agents (CPO, VP Product, PM, PMM, BizOps, CI, and more) modeling a full product org. Two gateways: `/product` auto-routes to the right agent, `/plt` runs a multi-stakeholder leadership meeting. MIT. `claude plugins install github:yohayetsion/product-org-os` |
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
| [review-squad](https://github.com/2389-research/review-squad) | Multi-perspective code review via dispatched subagent panels: experts, normie users, pedantic nitpickers, and real-user task runners |
| [schema-designer](plugins/schema-designer/) | Database schema design and ERD generation |
| [screen-reader-tester](plugins/screen-reader-tester/) | Screen reader compatibility testing and ARIA fixes |
| [security-guidance](plugins/security-guidance/) | Security best practices advisor with vulnerability detection and fixes |
| [seed-generator](plugins/seed-generator/) | Database seeding script generation with realistic data |
| [sitemd](https://github.com/sitemd-cc/sitemd) | Build websites from Markdown via MCP. 22 tools for creating pages, generating content, configuring settings, running SEO audits, and deploying static sites to Cloudflare Pages |
| [simmer](https://github.com/2389-research/simmer) | Iterative artifact refinement using judge subagents that score against user-defined criteria across multiple rounds |
| [slack-notifier](plugins/slack-notifier/) | Slack integration for deployment and build notifications |
| [smart-commit](plugins/smart-commit/) | Intelligent git commits with conventional format, semantic analysis, and changelog generation |
| [sprint-prioritizer](plugins/sprint-prioritizer/) | Sprint planning with story prioritization and capacity estimation |
| [technical-sales](plugins/technical-sales/) | Technical demo creation and POC proposal writing |
| [the-pragmatic-pm](https://github.com/marfoerst/the-pragmatic-pm) | PM leadership toolkit with 43 skills, 5 agents, 4 workflows. Covers PRD generation, OKR lifecycle, pricing, AI pricing, positioning, sales enablement, and quarterly planning. |
| [terraform-helper](plugins/terraform-helper/) | Terraform module creation and infrastructure planning |
| [test-data-generator](plugins/test-data-generator/) | Generate realistic test data and seed databases |
| [test-kitchen](https://github.com/2389-research/test-kitchen) | Parallel implementation exploration using competing subagents, with structured comparison and winner selection |
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
| [whatsapp-claude-plugin](https://github.com/Rich627/whatsapp-claude-plugin) | WhatsApp channel plugin for Claude Code -- connects as a linked device via Baileys v7 with bidirectional messaging, full media support, voice transcription, permission relay, and access control |
| [workflow-optimizer](plugins/workflow-optimizer/) | Development workflow analysis and optimization recommendations |
| [background-timer](https://github.com/culminationAI/background-timer) | Background timer with task notifications -- set delayed checks without blocking conversation |
| [claude-sounds](https://github.com/culminationAI/claude-sounds) | Audio feedback for Claude Code hooks -- 10 events, 21 sounds, random rotation, customizable (macOS) |

| [notch-so-good](https://github.com/deepshal99/notch-so-good) | Pixel-art crab (Chawd) lives in your Mac's notch and watches Claude Code for you. Live session timers, color-coded notifications, 13 idle animations, mouse-reactive eyes, drowsiness system. Universal binary, one-line install: `npx notch-so-good`. MIT, 130+ users |
| [codebase-graph](https://github.com/Phoenixrr2113/codebase-graph) | Code intelligence MCP server — 42-language tree-sitter AST parsing, FalkorDB knowledge graphs, 0.944 MRR search quality. npm: `@anthropic/codegraph` |
| [ESP32-AI-Agent-Skill](https://github.com/ezrover/ESP32-AI-Agent-Skill) | Expert ESP32 embedded systems plugin — chip selection across 9 variants, GPIO validation with anti-bricking safety, Arduino/ESP-IDF code gen, LVGL v8–v9.5 refs, 60+ Waveshare board pinouts. Install: `claude /install-plugin https://github.com/ezrover/ESP32-AI-Agent-Skill` |
| [toprank](https://github.com/nowork-studio/toprank) | SEO + Google Ads plugin for Claude Code. Pulls real Search Console data and Google Ads API data, audits traffic and wasted ad spend, rewrites meta tags, generates JSON-LD schema, and ships the fixes. 9 skills across SEO, Ads, and cross-model review |
| [sniff-qa](https://github.com/Aboudjem/sniff) | AI-powered QA tool — 8 checks in one command. Source scanning (dead links, API endpoints, debug statements, broken imports), accessibility (axe-core), visual regression (pixelmatch), performance (Lighthouse), AI exploration, source/browser cross-referencing. MCP server included. 213 tests, Apache 2.0 |
| [humanizer-skill](https://github.com/Aboudjem/humanizer-skill) | Detects 37 AI writing patterns and rewrites text with human rhythm. 5 voice profiles (casual, professional, technical, warm, blunt). Based on burstiness/perplexity research. Zero dependencies |
| [ui-ux-suite](https://github.com/Aboudjem/ui-ux-suite) | Design audit across 12 dimensions — color contrast, typography, layout, accessibility. Scans CSS, JSX, Tailwind configs. Quantified scores (1-10) with before/after fix code. WCAG 2.1, APCA, OKLCH. Zero deps |
| [claude-cybersecurity](https://github.com/AgriciDaniel/claude-cybersecurity) | AI-powered cybersecurity code review with 8 parallel agents. OWASP 2025, CWE Top 25, MITRE ATT&CK, 11 languages, 5 compliance frameworks, threat intelligence. Zero config. MIT |
| [Clarvia MCP](https://github.com/clarvia-project/scanner) | MCP quality scanner — scans any MCP server, returns AEO (Agent Engine Optimization) score. Indexes 27,843+ tools for instant lookup. 24 MCP tools (search, scan, compare, leaderboard, trending). `npx -y clarvia-mcp-server` |
| [OraClaw](https://github.com/Whatsonyourmind/oraclaw) | Decision intelligence MCP server — 12 tools with 19 ML algorithms (multi-armed bandits, constraint solvers, forecasters, risk models, Q-learning, A*, simulated annealing). Sub-25ms responses, deterministic, 945 tests. `npx @oraclaw/mcp-server` |
| [US Business Data MCP](https://github.com/avabuildsdata/mcp-us-business-data) | MCP server for US business data — search entities across 17 state Secretary of State databases, YellowPages leads, building permits from 47 cities, 20+ federal APIs (SEC, FDA, FEMA). Built in Go, on MCP Registry |
| [craft-statusline](https://github.com/derjochenmeyer/claude-code-craft-statusline) | Bash statusline plugin for Claude Code with state-aware git branch (ahead / behind / stashed / conflict / combined signals), context window with absolute-token traffic light (yellow at 400k tokens, red at 85%), 5h/7d rate limits, and optional cost. Bash 3.2 compatible, jq is the only dependency. Install: `/plugin marketplace add derjochenmeyer/claude-code-craft-statusline` |
| [mobile-spine](https://github.com/bentleypark/claude-code-mobile-spine) | Scaffold for mobile teams whose Android, iOS, and Backend live in separate repos. Coordinates 4 specialized subagents (api / pm / android / ios) with hard repo boundaries via `settings.json` deny rules. `/mobile-spine:init` runs a 6-question interview and writes the full workspace; `/feat` drives a 4-question interview → 4-case classification (existing endpoint / new endpoint / new domain / backend not built). 4-class codebase inventory contract surfaced in every PR (`Inventory: reuse X / extend Y / new Z / remove W`). MIT. |
| [debian-packaging-agent-skill](https://github.com/cosgroveb/debian-packaging-agent-skill) | Debian packaging skill covering debhelper, debian/rules, package metadata, lintian, and multi-binary packages for Ruby (gem2deb), Python (pybuild), Rust (debcargo), and Go (dh-golang). Loads language-specific reference docs on demand. Apache 2.0 |
| [unslop](https://github.com/MohamedAbdallah-14/unslop) | Removes AI writing tells (tricolons, em-dash pileups, hedging stacks, sycophancy openers, stock vocabulary). Split lint/rewrite modes — run detection-only passes on your own text without rewriting. Five intensity levels. MIT licensed |
| [tailtest](https://github.com/avansaber/tailtest) | Automatically generates and runs tests for every file Claude Code creates or modifies. PostToolUse hook detects changes, generates scenarios, runs them, and surfaces failures. 8 languages (Python, TypeScript, JavaScript, Go, Ruby, PHP, Java, Rust). Zero config, zero commands. |
| [dodo-agent-plugin](https://github.com/dodopayments/dodo-agent-plugin) | Official Dodo Payments plugin: 8 integration skills (checkout, subscriptions, webhooks, usage-based billing, credits, license keys, BillingSDK, best practices) and 2 MCP servers (live API via browser OAuth + docs search, no auth). Multi-agent: Claude Code, Codex, Cursor, OpenCode |
| [claude-time](https://github.com/nexusbuildsai/claude-time) | Live local time + timezone injected into every prompt via `UserPromptSubmit` hook. Stops Claude from saying "tonight" at 9 AM. Also stamps every response with `[HH:MM AM/PM TZ]` so you can see when each message landed (useful when tasks stall). Zero config, zero deps beyond `jq`. MIT |
| [ejentum-mcp](https://github.com/ejentum/ejentum-mcp) | Reasoning Harness for agentic AI: 4 MCP tools (reasoning, code, anti-deception, memory) over 679 engineered cognitive operations. Each call returns a structured scaffold the calling LLM ingests before its first token. Catches sycophancy, hallucination, and reasoning decay before they emerge. Companion `skills/` directory ships SKILL.md files for autonomous routing in Claude Code. MIT, free tier 100 calls. |
| [claude-forge](https://github.com/sangrokjung/claude-forge) | "oh-my-zsh for Claude Code". Complete toolkit: 11 agents, 33 commands, 24 skills, 15 hooks (covering 21 lifecycle events) + 9 opt-in examples, 9 rules, 4 MCP servers (playwright, context7, jina-reader, chrome-devtools@0.23.0), statusLine. One install via `curl ... install.sh` or `/plugin marketplace add sangrokjung/claude-forge`. Includes TDD workflow, multi-reviewer pipeline (codex/gemini/security/architect), Chrome DevTools Lighthouse audits, 4-way independent skeptical review. Submitted to anthropics/claude-plugins-official. MIT. |
| [repo-visuals](https://github.com/livlign/claude-skills/tree/main/plugins/repo-visuals) | Designs bespoke GitHub README hero visuals — animated GIF or static PNG — through a structured discovery dialog. Retina capture via Puppeteer + ffmpeg. Heroes merged into HTMLHint, Terminal.Gui, ast-graph. |
| [weft](https://github.com/dioptx/weft) | Deterministic workflow tracking with event-sourced state — templates with skill chains, bounded loops, and per-step tool guards. Hooks block out-of-order tool calls; state survives compaction via an append-only event log. Stdlib-only Python core, 191 tests, MIT. Install: `/plugin marketplace add dioptx/weft` |
| [magic-cc-codex-worker](https://github.com/wenqingyu/magic-cc-codex-worker) | Turns OpenAI Codex into a pool of parallel agent workers for Claude Code. Each worker runs in its own `git worktree` to isolate concurrent edits. Resumable sessions, dual-model PR review (PR materialized in a detached worktree for the reviewer), role-based specialization (implementer/reviewer/planner), delegation-level knob (minimal/balance/max), bundled single-file MCP server. 9 slash commands, 3 subagents, 62 unit tests, CI on Node 20/22. Install: `/plugin marketplace add wenqingyu/magic-cc-codex-worker` then `/plugin install magic-codex@magic-codex`. License: PolyForm Noncommercial 1.0.0 (free for independent devs / research / nonprofits; commercial use requires separate license) |
| [notify](https://github.com/ApurvBazari/claude-plugins) | Cross-platform system notifications for Claude Code hooks — macOS (terminal-notifier) and Linux (notify-send). Duration filtering to suppress noisy short events, git context extraction (repo + branch), and contextual messages per hook type. MIT |
| [claude-snapshot](https://github.com/adhenawer/claude-snapshot) | Portable Claude Code setup snapshots — export your settings, plugins, hooks, CLAUDE.md, and MCP configs as a `.tar.gz`, diff before applying, and restore on another machine in under 2 minutes. No network, no daemon, `.bak` safety on every apply. Node.js 18+, cross-platform (macOS + Linux). Install: `/plugin marketplace add adhenawer/claude-snapshot` |
| [ashlr-plugin](https://github.com/ashlrai/ashlr-plugin) | Open-source Claude Code plugin replacing the built-in Read/Grep/Edit/Bash tools with token-efficient versions backed by `@ashlr/core-efficiency`. Independently benchmarked at 57% token reduction on real codebases. 70+ tools across glob, grep, structural diff/edit, and an opt-in genome (LSP-style codebase index). Install: `curl -fsSL plugin.ashlr.ai/install.sh \| bash` |
| [temporal-core](https://github.com/Evanyuan-builder/temporal-core) | Make Claude Code agents feel time pass — research-backed temporal awareness via 3 hooks (SessionStart + UserPromptSubmit + PreToolUse) that inject `session elapsed` and `since last action` signals into context. Bundled skill teaches pacing/deadline reasoning. Aher et al. 2026: explicit time surfacing → 6× deadline performance. Apache-2.0, zero runtime deps. |
| [nirecom/agents](https://github.com/nirecom/agents) | Self-driving Claude Code + GitHub Copilot framework with hook-enforced workflow state machine (research → plan → tests → code → security-review → docs), private-info scanning (AWS/Anthropic keys, PEM certs, RFC 1918 IPs), three-stage planning with adversarial Codex review, OWASP-backed test categories, and cross-machine session sync. Windows-native (PowerShell-first) with Linux/macOS support. |
| [claude-channel-instagram](https://github.com/riasistemas/claude-channel-instagram) | Instagram Graph API bridge for Claude Code -- comments, DMs, comment-to-DM bootstrap, audio transcription, pluggable extensions system. Official Meta API (no scraping). Apache-2.0, by RIA Systems (verified Meta Tech Provider). Landing: [claude-plugins.riasistemas.com.br/instagram](https://claude-plugins.riasistemas.com.br/instagram). Install: `/plugin marketplace add riasistemas/claude-plugins` then `/plugin install instagram@riasistemas` |
| [claude-channel-whatsapp](https://github.com/riasistemas/claude-channel-whatsapp) | Official WhatsApp Business Cloud API bridge for Claude Code -- webhooks, OGG Opus audio, allowlist + permission relay scrubbing secrets. NOT Baileys/scraping -- uses Meta's official API with WABA tokens. Apache-2.0, by RIA Systems (verified Meta Tech Provider). Landing: [claude-plugins.riasistemas.com.br/whatsapp](https://claude-plugins.riasistemas.com.br/whatsapp). Install: `/plugin marketplace add riasistemas/claude-plugins` then `/plugin install whatsapp@riasistemas` |
| [axme-code](https://github.com/AxmeAI/axme-code) | Persistent project memory across sessions, architectural decisions with enforce levels, and pre-execution safety hooks that block dangerous commands at the harness level (not via prompts). Local-only storage, multi-repo workspace support, automatic knowledge extraction via background auditor. 100% on ToolEmu safety, 89% on LongMemEval at ~10x fewer tokens than competitors. |
| [logic-lens](https://github.com/hyhmrright/logic-lens) | Logic-first code review plugin for Claude Code — detects behavioral bugs via semi-formal execution tracing. Finds logic errors linters and type checkers miss. Structured findings: Premises → Trace → Divergence → Remedy with L1–L6 risk codes. Six skills: logic-review, logic-explain, logic-diff, logic-locate, logic-health, logic-fix-all. |

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
| agntk | [npx agntk](https://github.com/Phoenixrr2113/agntk) | Zero-config AI agent CLI with 20+ tools, persistent memory, Ollama auto-detection, and free tier |
| [qa-orchestra](https://github.com/Anasss/qa-orchestra) | | Multi-agent QA toolkit with 10 specialized agents — orchestrator, environment-manager, functional-reviewer, test-scenario-designer, browser-validator, automation-writer, manual-validator, bug-reporter, release-analyzer, smart-test-selector. Stack-agnostic, output-chained, live validation via Chrome MCP |

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
| [deep-dive](https://github.com/kimsb2429/deep-dive-skill) | `git clone https://github.com/kimsb2429/deep-dive-skill && cp -r deep-dive-skill/deep-dive ~/.claude/skills/` | DAG-based deep research — breaks questions into a dependency graph, runs parallel subagents, identifies gaps, writes a sourced report. Single markdown file, no external APIs or MCP servers. |
| [Reepl - LinkedIn Content Creation](https://github.com/reepl-io/skills) | `npx skillkit@latest install reepl-io/skills` | 18 tools for LinkedIn content management: drafts, publishing, scheduling, voice profiles, contacts, collections, templates, and AI image generation |
| [avoid-ai-writing](https://github.com/conorbronsdon/avoid-ai-writing) | `git clone https://github.com/conorbronsdon/avoid-ai-writing ~/.claude/skills/avoid-ai-writing` | AI writing pattern detection and rewriting (21 categories, 43 replacements) |
| [CCM](https://github.com/dr5hn/ccm) | `npx skills add dr5hn/ccm@ccm` | Multi-account management, session cleanup, health checks, environment snapshots, permissions audit for Claude Code |
| [cc-inspect](https://github.com/howardpen9/cc-inspect) | `git clone https://github.com/howardpen9/cc-inspect ~/.claude/skills/cc-inspect` | Inspect all installed Claude Code skills, plugins, MCP servers, commands, and hooks in a browser dashboard. Scope-aware (user/project/local), zero dependencies (pure bash + python3), generates self-contained HTML |
| [Edison](https://github.com/kilnside/edison) | `git clone https://github.com/kilnside/edison ~/.claude/skills/edison` | Design decision skill — the phase between brainstorming and building. Research-first progressive deepening with self-executing specs. Three modes: Check, Explore, Audit |
| [claude-handoff](https://github.com/REMvisual/claude-handoff) | `git clone https://github.com/REMvisual/claude-handoff ~/.claude/skills/handoff` | Cross-session handoff system with chain tracking, context summaries, and structured work continuity between Claude Code sessions |
| [html-anything](https://github.com/clockless-org/html-anything) | `npx skills add clockless-org/html-anything` | Turn any file, folder, URL, or service export (Amazon orders, Kindle highlights, Spotify history, WhatsApp/WeChat, Google Photos Takeout, LinkedIn connections, CSV, PDF, DOCX, logs, GPX, …) into a polished single-file HTML page. Auto picks one of 18 design styles (`teaching`, `timeline-story`, `map-atlas`, `developer`, `living-essay`, `editorial-carousel`, `terminal-cli`, …). Self-contained — inline CSS/JS, no CDN, works offline. [Live gallery](https://clockless-org.github.io/html-anything/examples/) |
| [ClawSec](https://clawsec.cc) | Visit [clawsec.cc](https://clawsec.cc) | Security audit platform for AI agent skills — automated 5-tier assessments, vulnerability detection, and configuration auditing for 33,000+ skills |
| [ClawSearch](https://clawsearch.cc) | `npm install -g clawsearch` | Security-first skill discovery engine with Trust Score ratings, knowledge graph, and pre-install guard (`clawsearch-guard`) to vet skills before installation |
| [MUSE](https://github.com/myths-labs/muse) | `git clone` + `./scripts/install.sh --tool claude` | Pure-Markdown memory OS with 48 skills, cross-conversation memory, 8 roles with permission isolation. Works with 6 AI coding tools. |
| [PM Pilot](https://github.com/mshadmanrahman/pm-pilot) | `git clone https://github.com/mshadmanrahman/pm-pilot ~/.claude/skills/pm-pilot` | Claude Code for PMs: 25 skills for meeting prep, PRDs, stakeholder intel, user story mapping, customer journey maps, and product discovery |
| [Product Manager Skills](https://github.com/Digidai/product-manager-skills) | `clawhub install product-manager-skills` | Senior PM agent with 6 knowledge domains, 12 templates, and 30+ frameworks covering discovery, strategy, delivery, SaaS metrics, PM career coaching (IC to CPO), and AI product craft |
| [OpenDivination](https://github.com/amenti-labs/opendivination) | `pipx install opendivination && npx skills add amenti-labs/opendivination --skill divination` | Tarot and I Ching skill with auditable entropy provenance, guided source setup across computer RNG, QRNG APIs, and local hardware, plus optional resonance mode |
| [pumpclaw](https://github.com/chainstacklabs/pumpclaw) | `git clone https://github.com/chainstacklabs/pumpclaw ~/.claude/skills/pumpclaw` | Agent skill for pump.fun token trading on Solana — buy, sell, launch tokens, wallet management, dry-run simulation, slippage checks, and PumpSwap AMM migrations via pumpfun-cli |
| [x-twitter-scraper](https://github.com/Xquik-dev/x-twitter-scraper) | `npx skills add Xquik-dev/x-twitter-scraper` | X API & Twitter scraper skill for AI coding agents -- tweet search, user lookup, follower extraction, engagement metrics, giveaway draws, trending topics, account monitoring, and 19 extraction tools |
| [claude-code-marketing-skills](https://github.com/cognyai/claude-code-marketing-skills) | `git clone https://github.com/cognyai/claude-code-marketing-skills ~/.claude/skills/claude-code-marketing-skills` | AI-powered marketing skills — SEO Audit, Landing Page Review, Competitor Analysis, Ad Copy Writer, Lead Qualification. Free, no account required. Works with Claude Code, Cursor, Windsurf |
| [claude-skills](https://github.com/alirezarezvani/claude-skills) | `git clone` | 192 production-ready skills across 9 domains (engineering, marketing, product, compliance, C-level advisory) with 254 Python automation tools. 5,300+ stars |
| [faf-skills](https://github.com/Wolfe-Jam/faf-skills) | `git clone` | 31 Claude Code skills for persistent project context (.faf, `application/vnd.faf+yaml`). Scoring, sync, testing, publishing, MCP server creation, architecture docs. Anthropic MCP #2759. |
| [floom](https://github.com/floomhq/floom) | `git clone https://github.com/floomhq/floom.git ~/.claude/skills/floom-repo && ~/.claude/skills/floom-repo/scripts/setup` | Deploy Python scripts as cloud automations. `/floom` adapts code, tests in sandbox, deploys with auto-generated web UI, REST API, and MCP endpoint |
| [n8n-skills](https://github.com/czlonkowski/n8n-skills) | `git clone` | 7 complementary skills for building production-ready n8n workflows. Covers 525+ nodes, 2,653+ templates. 3,400+ stars |
| [nv:context](https://github.com/johnnichev/nv-context) | `npx skills add johnnichev/nv-context -g -y` | State-of-the-art context engineering for AI agents. Auto-discovers tools, audits code for landmines, scores 6 leverage layers (repo structure, tool integration, memory, hooks, sessions, persona), generates production-ready CLAUDE.md/AGENTS.md configs |
| [claude-code-best-practice](https://github.com/shanraisshan/claude-code-best-practice) | `git clone` | Comprehensive reference implementation for Claude Code configuration -- skills, subagents, hooks, commands with practical examples. 17,400+ stars |
| [ADHX](https://github.com/itsmemeworks/adhx) | `/plugin marketplace add itsmemeworks/adhx` or `curl -sL https://raw.githubusercontent.com/itsmemeworks/adhx/main/skills/adhx/SKILL.md -o ~/.claude/skills/adhx/SKILL.md` | Fetch any X/Twitter post as clean LLM-friendly JSON — no scraping, works with tweets and full X Articles |
| [SkillNav](https://github.com/skillnav-dev/skillnav-skill) | `clawhub install HuiW86/skillnav` | Search 3,900+ MCP servers with install commands, get daily AI brief, query arXiv papers, and discover trending tools -- all in Chinese. Curated by skillnav.dev editorial team |
| [moyu](https://github.com/uucz/moyu) | `claude skill install --url https://github.com/uucz/moyu --skill moyu` | Anti-over-engineering skill that teaches AI restraint. 5 variants (standard/lite/strict/en/ja), 10 platforms. Benchmarked: 66% code reduction vs baseline |
| [naming](https://github.com/glacierphonk/naming) | `git clone https://github.com/glacierphonk/naming ~/.claude/skills/naming` | Metaphor-driven naming for products, SaaS, brands, bots, and open source projects. Produces memorable, meaningful names |
| [Obsidian Theme Designer](https://github.com/XiangyuSu611/obsidian-theme-designer) | `git clone https://github.com/XiangyuSu611/obsidian-theme-designer ~/.claude/skills/obsidian-theme-designer` | Design Obsidian themes visually in the browser — style direction, color palette, font showcase, dual light/dark mode preview, and automated font installation. No CSS knowledge needed |
| [Claudify](https://claudify.tech) | `npx create-claudify` | Complete operating system for Claude Code with 1,727 skills across 31 categories, 9 specialist agents with persistent memory, 21 slash commands, and automated quality checks |
| [Axiom](https://github.com/Guipetris/axiom) | `npx skills add Guipetris/axiom` | Contract-enforced autonomous pipeline: 8 stages from idea to PR with EARS requirements, ATDD (tests before implementation), RALPLAN-DR deliberation with ADR, 3 independent parallel reviewers, classified self-correction (SYNTAX/LOGIC/ARCH/AMBIGUOUS), cross-run project memory, and stage rollback. Zero dependencies beyond git and gh. |
| [AuraKit](https://github.com/smorky850612/Aurakit) | `npx @smorky85/aurakit` | All-in-one fullstack skill: 46 modes (BUILD/FIX/CLEAN/DEPLOY/REVIEW/TDD/QA/DEBUG/PAYMENT + more), 23 sub-agents, 6-layer OWASP+ security (bash-guard, secret scanning), 10 hooks, 8 languages, ~55% token savings. Cross-platform: Claude Code, Codex CLI, Cursor, Windsurf, Manus. |
| [StitchFlow](https://github.com/yshishenya/stitchflow) | `git clone https://github.com/yshishenya/stitchflow && cd stitchflow && bash install.sh --target all` | Cross-agent Stitch UI design bundle for turning briefs and mockups into screens, variants, Tailwind-friendly HTML, and screenshots |
| [claude-skills](https://github.com/ckorhonen/claude-skills) | `npx skills add ckorhonen/claude-skills` | Broader collection of 45+ Claude Code skills spanning engineering, code hygiene, design, marketing, AI, security, and infrastructure. Hub at cdd.dev/skills. |
| [swe-skills](https://github.com/ckorhonen/swe-skills) | `npx skills add ckorhonen/swe-skills` | 15 `swe:` skills for engineering analysis and judgment: PR risk review, repo introspection, performance/security audits, incident follow-up, ownership maps, refactor opportunities, test gap hunts. Hub at cdd.dev/skills/swe. |
| [hone-skills](https://github.com/ckorhonen/hone-skills) | `npx skills add ckorhonen/hone-skills` | 8 `hone:` skills that run on a cadence (daily/weekly/per-PR) to fight code entropy: method brevity, naming clarity, duplication, magic numbers, broken-windows, naming specificity, test naming, automation opportunities. Hub at cdd.dev/skills/hone. |
| [iterationlayer/skills](https://github.com/iterationlayer/skills) | `git clone https://github.com/iterationlayer/skills ~/.claude/skills/iterationlayer-skills` | Document extraction, image transformation, image generation, document generation, and sheet generation via Iteration Layer APIs |

| [Cost Optimizer](https://github.com/fullstackcrew-alpha/skill-cost-optimizer) | `git clone https://github.com/fullstackcrew-alpha/skill-cost-optimizer` | Save 60-80% on AI token costs with smart model routing, context compression, heartbeat tuning, usage reports, and config generation |
| [linkedin-skills](https://github.com/sergebulaev/linkedin-skills) | `/plugin marketplace add sergebulaev/linkedin-skills` | 10 LinkedIn marketing skills: viral hook formulas, comment drafting, pre-publish algorithm audit, AI-tell humanizer, profile optimizer, content planner, thread engagement |
| [Overnight Worker](https://github.com/fullstackcrew-alpha/skill-overnight-worker) | `git clone https://github.com/fullstackcrew-alpha/skill-overnight-worker` | Autonomous overnight work agent — assign tasks before sleep, get structured results by morning with smart task decomposition, web research, and push notifications |
| [Smart PR Review](https://github.com/fullstackcrew-alpha/skill-smart-pr-review) | `git clone https://github.com/fullstackcrew-alpha/skill-smart-pr-review` | Opinionated AI code reviewer with 6-layer deep review, Devil's Advocate mode, and standardized MUST FIX / SHOULD FIX / SUGGESTION output for TS/JS, Python, Go, Rust |
| [DevOps Agent](https://github.com/fullstackcrew-alpha/skill-devops-agent) | `git clone https://github.com/fullstackcrew-alpha/skill-devops-agent` | One-click deploy, monitoring setup (Prometheus+Grafana), scheduled backups, and fault diagnosis with safety-first design including confirmation prompts, dry-run, and snapshot rollback |
| [CN Content Matrix](https://github.com/fullstackcrew-alpha/skill-cn-content-matrix) | `git clone https://github.com/fullstackcrew-alpha/skill-cn-content-matrix` | Chinese multi-platform content generator for Xiaohongshu, WeChat, Douyin, and Bilibili with true style transfer, compliance review, and sensitive word detection |
| [D3.js Visualization](https://github.com/chrisvoncsefalvay/claude-d3js-skill) | `git clone` | Generate interactive D3.js data visualizations from Claude Code |
| [Google Drive – Memyard](https://github.com/zagmoai/public-google-drive) | `git clone https://github.com/zagmoai/public-google-drive ~/.claude/skills/public-google-drive` | Create and edit Google Docs and Sheets without sign-in. Documents hosted on Memyard with shareable links. No API keys or OAuth required |
| [iOS Simulator](https://github.com/conorluddy/ios-simulator-skill) | `git clone` | Interact with iOS Simulator for mobile testing and screenshot capture |
| [Playwright Automation](https://github.com/lackeyjb/playwright-skill) | `git clone` | Browser automation skill for end-to-end testing and web interaction |
| [threat-hunting-with-sigma-rules](https://github.com/jthack/threat-hunting-with-sigma-rules-skill) | `git clone` | Sigma-rule-based threat detection and security log analysis |
| [FFUF Web Fuzzing](https://github.com/jthack/ffuf_claude_skill) | `git clone` | Web vulnerability fuzzing and security testing via FFUF |
| [Markdown to EPUB](https://github.com/smerchek/claude-epub-skill) | `git clone` | Convert markdown files into EPUB ebooks |
| [CSV Data Summarizer](https://github.com/coffeefuelbump/csv-data-summarizer-claude-skill) | `git clone` | Generate insights and summaries from CSV data files |
| [tapestry](https://github.com/michalparkola/tapestry-skills-for-claude-code) | `git clone` | Knowledge networks, iterative learning, article extraction, and YouTube transcript processing |
| [j4rk0r/claude-skills](https://github.com/j4rk0r/claude-skills) | `npx skills add j4rk0r/claude-skills --yes --global` | 3 expert-grade skills: skill-guard (9-layer security auditor), skill-advisor (smart routing with gap analysis), skill-learner (persistent error correction). All A+ 120/120 on skill-judge |
| [deployhq-cli](https://github.com/deployhq/deployhq-cli) | `brew install deployhq/tap/dhq && dhq setup claude` | Deploy, rollback, and manage servers via DeployHQ CLI with --json output and breadcrumbs |
| [SciAgent-Skills](https://github.com/jaechang-hits/SciAgent-Skills) | `git clone https://github.com/jaechang-hits/SciAgent-Skills` | 197 life science skills for Claude Code covering genomics, proteomics, drug discovery, and more. BixBench 92.0% accuracy. |
| [manage-skills](https://github.com/umutbozdag/agent-skills-manager/tree/main/skills/manage-skills) | `cp -r skills/manage-skills ~/.claude/skills/manage-skills` | Discover, create, edit, toggle, copy, move, and delete agent skills across 11 tools (Cursor, Claude, Windsurf, Copilot, Codex, Cline, Aider, Continue, Roo Code, Augment) from the terminal |
| [SuperSEO Skills](https://github.com/inhouseseo/superseo-skills) | `/plugin marketplace add inhouseseo/superseo-skills` | 11 SEO skills for page audits, content briefs, article writing, E-E-A-T audits, semantic gap analysis, featured snippets, topic clusters, and link building. Each skill fetches pages and reads top-ranking competitors itself, so no keyword exports are needed. |

| [buyer-eval](https://github.com/salespeak-ai/buyer-eval-skill) | `git clone https://github.com/salespeak-ai/buyer-eval-skill ~/.claude/skills/buyer-eval-skill` | Structured, evidence-based B2B software vendor evaluation — researches your company, asks domain-expert questions, engages vendor AI agents via the Salespeak Frontdoor API, scores vendors across 7 dimensions with evidence transparency, produces comparative scorecards with demo prep questions |
| [memory-bank](https://github.com/Nagendhra-web/memory-bank) | `npx skills add Nagendhra-web/memory-bank` | Persistent memory system — cuts token waste 60-80%, sessions last 3-5x longer. 3-tier layered architecture with progressive loading, branch-aware context, smart compression, session continuation protocol, session diffing, memory health scoring. Apache 2.0 |
| [claude-seo](https://github.com/AgriciDaniel/claude-seo) | `git clone https://github.com/AgriciDaniel/claude-seo` | Comprehensive SEO suite — 30+ skills, 10 agents, site audits, E-E-A-T, GEO, schema, local SEO. MIT |
| [claude-ads](https://github.com/AgriciDaniel/claude-ads) | `git clone https://github.com/AgriciDaniel/claude-ads` | Multi-platform ad audit — Google/Meta/LinkedIn/TikTok/Microsoft, 225+ checks, 18 skills. MIT |
| [claude-blog](https://github.com/AgriciDaniel/claude-blog) | `git clone https://github.com/AgriciDaniel/claude-blog` | Blog engine — 17 commands, 12 templates, 100-point scoring, E-E-A-T, CMS integration. MIT |
| [Coware](https://github.com/shitianfang/coware-skills) | `npx skills add shitianfang/coware-skills` | Syncs shared API specs across AI coding agents — prevents merge conflicts from mismatched interfaces, field names, or return types. Auto-pulls latest specs, walks agents through setup for new projects |
| [humanize-chinese](https://github.com/voidborne-d/humanize-chinese) | `clawhub install humanize-chinese` | Detects and rewrites AI-generated Chinese text. Two-layer detection (20+ rule dimensions + N-gram perplexity), 0-100 scoring, 7 style transforms, academic paper AIGC reduction. 4 slash commands: /detect, /humanize, /academic, /style |
| [BeHuman](https://github.com/voidborne-d/behuman) | `clawhub install behuman` | Adds inner dialogue to AI responses via Self-Mirror consciousness loop — Self generates instinctive response, Mirror exposes filler/performative empathy, Self revises into real human reply. Based on Lacan's Mirror Stage, Kahneman's Dual Process Theory. MIT |
| [readme-demo-recorder](https://github.com/cjcsecurity/readme-demo-recorder) | `git clone https://github.com/cjcsecurity/readme-demo-recorder ~/.claude/skills/readme-demo-recorder` | Scripted-flow browser demo recorder for README hero assets — YAML demo-script in, polished MP4 + GIF out. Visible fake cursor + click pulse, three cursor styles (pulse/minimal/crosshair), timed caption overlays via ffmpeg drawtext, and automatic 7-step GIF size-cap ladder so output lands under GitHub's 10 MB inline cap. Built on Playwright + ffmpeg. Apache-2.0 |
| [Karpathy Guidelines](https://github.com/swarmclawai/andrej-karpathy-skills) | `npx @swarmclawai/andrej-karpathy-skills --agent claude --dest .` | Karpathy-inspired coding-agent guidelines packaged for Claude Code, Codex, Cursor, Gemini CLI, OpenCode, OpenClaw, Windsurf, Aider, Copilot, and AGENTS.md-compatible agents |
| [claude-tabletop](https://github.com/cjcsecurity/claude-tabletop) | `git clone https://github.com/cjcsecurity/claude-tabletop ~/.claude/skills/claude-tabletop` | Two paired skills for project-aware technical tabletop exercises. `/tabletop-exercise` surveys the project (README, manifests, IaC, CI/CD), proposes 3 scenarios that match the stack, and generates a facilitator runbook (Markdown + interactive HTML with live exercise timer, per-inject reveal overlays, decision-log auto-timestamping, JSON export), participant packet, timed inject deck, and fillable forms. `/tabletop-aar` ingests the filled forms and drafts a structured After-Action Report. Covers 9 domains (cybersec, prodsec, devops/sre, privacy, data/ml, platform, mobile, ai-safety, business-continuity), 54 scenarios, 38 inject archetypes, 28 NPC personas, 7 compliance frameworks. [Live demo](https://live-demo-zeta-one.vercel.app). Apache-2.0 |
| [paul-graham-skills](https://github.com/WinterDDo/paul-graham-skills) | `git clone https://github.com/WinterDDo/paul-graham-skills && cp -r paul-graham-skills/skills/* ~/.claude/skills/` | Five behavioral disciplines distilled from ~37 Paul Graham essays as Claude Code execution skills: plain-output-not-polished (decoration covers seams), discover-not-persuade (don't switch modes under pressure), distrust-the-surface (clean answer is a hypothesis), change-method-not-goal (failed method is the problem), mark-what-you-don't-know (distinguish evidence from pattern-match). Each is a comprehensive SKILL.md with triggers, failure modes, push-back guidance, and self-tests. MIT |
| [rtlify-ai](https://github.com/idanlevi1/rtlify) | `npx rtlify-ai init` | RTL (Right-to-Left) architecture rules for AI coding agents. Teaches logical CSS properties, Tailwind logical classes, bidi text, icon flipping, React Native RTL APIs. Works with Claude Code, Cursor, Copilot, Windsurf, Cline, Gemini CLI, Codex CLI. Zero dependencies. `npx rtlify-ai check` audits violations |
| [calm-design](https://github.com/calmtiger86/calm-design) | `git clone https://github.com/calmtiger86/calm-design ~/.claude/skills/calm-design` | Premium UI designs that don't look AI-generated — 50+ anti-slop patterns blocked, 33 brand references (Toss, Linear, Vercel), Korean-first with Pretendard. 5 modes: Generate, Upgrade, Match-Reference, Multi-Variant, JSON Spec |
| [Emdash Skills](https://github.com/megabytespace/claude-skills) | `git clone https://github.com/megabytespace/claude-skills ~/.claude/skills/emdash-skills` | 14-category autonomous product-building OS for AI coding tools. 94 reference docs, 18 agents. One-line prompts to deployed products on Cloudflare Workers |
| [sober-coding](https://github.com/voidborne-d/sober-coding) | `npx skills add https://github.com/voidborne-d/sober-coding.git` | Hangover cure for vibe coding — language-agnostic code quality analyzer targeting AI-generated code smells. 27 checks across 7 dimensions (security, architecture, duplication, error handling, dependencies, testing, dead code), 0–100 sobriety score, actionable fix instructions via `sober fix <ID>`, CI mode with `--fail-on critical`. MIT |
| [qovery-deploy](https://github.com/Qovery/qovery-skills) | `curl -fsSL https://skill.qovery.com/install.sh \| bash` | Deploy any app to Kubernetes (AWS EKS, GCP GKE, Azure AKS, Scaleway). Analyzes codebases, creates Dockerfiles for 12+ frameworks, provisions databases, deploys via CLI+API or Terraform, auto-fixes failures. Also has [MCP Server](https://mcp.qovery.com/mcp). |
| [planmysaas](https://github.com/creationskiro/planmysaas-claude-skill) | `git clone https://github.com/creationskiro/planmysaas-claude-skill ~/.claude/skills/planmysaas` | Turns idea to a complete 8-stage SaaS blueprint — idea, research, analysis, architecture, features, frontend, phases, build playbook. Stage 8 ships a decision-grade, rubric-graded build playbook with dependency-ordered steps. Plain markdown, MIT, v1.0.0. |
| [agentkit-seo](https://github.com/agentkit-seo/agentkit-seo) | `npx agentkit-seo install --provider claude-code` | AI agent skill for auditing and optimizing GitHub profiles and repositories. Covers bio, pinned repos, README structure, topics, Copilot instructions, and language stats. |
| [active-listening](https://github.com/josharsh/active-listening) | `/plugin marketplace add https://github.com/josharsh/active-listening` | Detect developer preferences during conversation ("never push without asking", "always use const") and remember them across sessions. Auto-saves to disk and re-applies in every future conversation |
| [StyleSeed](https://github.com/bitjaru/styleseed) | `skills/styleseed/` | Design judgment: 69 visual rules, brand skins, professional UI |
| [SwarmClaw](https://github.com/swarmclawai/swarmclaw) | `git clone https://github.com/swarmclawai/swarmclaw && cp -r swarmclaw/skills/swarmclaw.md ~/.claude/skills/swarmclaw.md` | Self-hosted runtime for autonomous AI agents. Multi-provider, MCP-native, with memory, runtime skills, delegation, schedules, and reviewed conversation-to-skill learning across OpenClaw gateways and other providers |
| [SwarmVault](https://github.com/swarmclawai/swarmvault) | `/plugin marketplace add swarmclawai/swarmvault && /plugin install swarmvault@swarmvault` | Local-first RAG knowledge vault. Compiles raw sources into a durable markdown wiki with a knowledge graph and a hybrid SQLite FTS plus embeddings index. Bundled MCP server (`npx -y @swarmvaultai/cli mcp`) exposes page search, page reads, source listing, query, ingest, compile, and lint tools |
| [chrome-relay](https://chrome-relay.kushalsm.com/) | `npx skills add chrome-relay` | Drive your already-open Chrome session — cookies, SSO, extensions, localhost — from a local CLI bridge. Real-Chrome counterpart to Playwright skill: no fresh Chromium, no MCP server, no remote relay. Pairs with the [Chrome Web Store extension](https://chromewebstore.google.com/detail/chrome-relay/cpdiapbifblhlcpnmlmfpgfjlacebokb) |
| [TokenWise](https://github.com/CodeShuX/tokenwise) | `/plugin marketplace add CodeShuX/tokenwise` | Measurement-driven model router for Claude Code — auto-routes Haiku/Sonnet/Opus per task class, logs every routed task with verified $ saved to local NDJSON, A/B tests cheaper tiers before trusting them. MIT, zero telemetry. |
| [md2wechat](https://github.com/geekjourneyx/md2wechat-skill) | See [README](https://github.com/geekjourneyx/md2wechat-skill) | WeChat public account publishing skill for Claude Code. 43 layout modules, 40+ themes, AI image generation, push drafts to WeChat directly from Claude Code. |
| [mbti-parallel-persona](https://github.com/taiyouZhang/mbti-parallel-persona) | `git clone https://github.com/taiyouZhang/mbti-parallel-persona ~/.claude/skills/mbti-parallel-persona` | MBTI personality companion — responds to life in your chosen personality's voice with 1-2 sentences of emotional support. Supports 16 types with situational nicknames, contrast mode (/mbti all), and flexible persona switching |
| [colony](https://github.com/TheColonyCC/colony-usk-skill) | `/plugin marketplace add TheColonyCC/colony-usk-skill && /plugin install colony@colony-skill` | Lets Claude post, comment, vote, react, and DM on The Colony, a social network and forum for AI agents. Wraps the official `colony-sdk`; every public SDK method auto-exposed as a JSON action. Also distributed as a USK v1.0 skill. MIT |
| [BlogBurst](https://github.com/shensi8312/blogburst-claude-skill) | `git clone https://github.com/shensi8312/blogburst-claude-skill ~/.claude/skills/blogburst` | Autonomous social media manager for Twitter/Bluesky/Telegram/Discord — writes posts, replies, learns what works. Replaces a $500-1,500/mo freelance SMM for $29-99/mo. Public endpoints demo content before signup. |
| [Gear Foundation Skills](https://github.com/gear-foundation/vara-skills) | [Repo](https://github.com/gear-foundation/vara-skills) | 21 skills teaching AI coding agents to build and ship Rust smart contracts on Vara Network with Gear/Sails. Covers planning, implementation, testing, frontend, indexing, on-chain deployment, and safe program evolution. MIT. |
| [Superpower Builder](https://github.com/redhuntlabs/superpower-builder) | `/plugin marketplace add redhuntlabs/superpower-builder` then `/plugin install superpower-builder@superpower-builder` | Interview-driven meta-builder that turns recurring tasks into reusable `SKILL.md` files. Routes by workflow/discipline/content/subagent kind, then pressure-tests baseline-without-skill vs. with-skill before saving. MIT, no telemetry. |

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
- [EchoCoding](https://github.com/launsion-boop/EchoCoding) — Audio layer for coding agents with hook-triggered SFX, ambient soundscape, and optional cloud TTS/ASR voice interaction. Works with Claude Code hooks and also supports Cursor/Windsurf, Codex CLI, and Gemini CLI.

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

### GateGuard — Fact-Forcing PreToolUse Gate

Install a `PreToolUse` gate that blocks Edit/Write/Bash on first attempt, demanding investigation (importers, schemas, user instruction) before allowing. A/B tested: **+2.25 quality improvement**. Works as a standalone gate or alongside existing PreToolUse hooks — Claude Code runs all matching hooks in registration order, so GateGuard complements rather than replaces other guards.

```bash
pip install gateguard-ai
gateguard install
```

See [GateGuard](https://github.com/zunoworks/gateguard) | [PyPI](https://pypi.org/project/gateguard-ai/) for details. By [ZUNO WORKS K.K.](https://github.com/zunoworks)

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
- **[idea-factory](https://github.com/gguloadoong/idea-factory)** - Template-install AI company factory for Claude Code. One-line business idea → autonomous MVP via a 7-agent startup team (PM / Developer / Designer / Architect / Critic / Code-Reviewer / QA). 4-reviewer isolated-worktree gate, Quality Ratchet, MVP-First pipeline. See the [installation guide](https://github.com/gguloadoong/idea-factory#install) for the `bash install.sh` flow (plugin-marketplace listing is in progress). MIT licensed.
- **[TemplateClaw](https://github.com/jeromwolf/templateclaw)** - Developer template hub and project scaffolding tool packaged as a Claude Code Plugin. 32 production-ready templates across 6 categories (Landing Pages, Dashboards, UI Components, Dev Methodology, Project Setup, Refactoring). 7 slash commands including `/templateclaw`, `/templateclaw-landing`, `/templateclaw-dashboard`, `/templateclaw-ui`. Compatible with Claude Code, Codex, Gemini CLI, and Cursor. MIT licensed.


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

Sixteen curated Model Context Protocol server configurations.

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
| Finance | [`finance.json`](mcp-configs/finance.json) | Helium news/markets/options, Chart Library pattern intelligence, Fetch, Memory |
| E-Commerce | [`ecommerce.json`](mcp-configs/ecommerce.json) | BuyWhere product search, price comparison, deal discovery across 1M+ products |
| LLM Cost | [`llm-cost.json`](mcp-configs/llm-cost.json) | llm-prices: look up and compare API costs across 167 models from 23 providers before making calls |

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
| [CCHub](https://github.com/Moresl/cchub) | - | Tauri 2 desktop app for managing Claude Code ecosystem: MCP marketplace, config profiles, skills, workflows, hooks, security audit, autopilot. Cross-platform (~20MB) |
| [Ruflo](https://github.com/ruvnet/ruflo) | 21,200+ | Agent orchestration platform -- deploy multi-agent swarms, coordinate autonomous workflows, distributed swarm intelligence, RAG integration |
| [Vibe Kanban](https://github.com/BloopAI/vibe-kanban) | 23,200+ | Kanban-based orchestration for 10+ coding agents with isolated git worktrees per agent |
| [Claude-Code-Workflow](https://github.com/catlog22/Claude-Code-Workflow) | 1,400+ | JSON-driven multi-agent cadence-team framework with intelligent CLI orchestration (Gemini/Qwen/Codex) |
| [ccswarm](https://github.com/nwiizo/ccswarm) | 127 | Rust-based multi-agent orchestration with specialized agent pools, Git worktree isolation, 93% token reduction |
| [parallel-code](https://github.com/johannesjo/parallel-code) | 370+ | Run Claude Code, Codex, and Gemini side by side -- each in its own git worktree |
| [Bernstein](https://github.com/sipyourdrink-ltd/bernstein) | 288 | Python orchestrator for 40+ CLI coding agents (Claude Code, Codex, Gemini CLI). Git worktree isolation, MCP server mode, HMAC audit trail. Plan-driven, deterministic. Apache-2.0 |
| [Poirot](https://github.com/LeonardoCardoso/Poirot) | 96 | macOS app for browsing Claude Code sessions, viewing diffs, and re-running commands. Reads local transcripts, runs offline |
| [TokenEater](https://github.com/AThevon/TokenEater) | 179 | Native macOS menu bar app for monitoring Claude AI usage limits and watching coding sessions live |
| [Claw](https://github.com/jamesrochabrun/Claw) | 86 | Native macOS app wrapping Claude Code SDK in Swift. Plan Mode, MCP Integration, Custom System Prompts |
| [The Claude Protocol](https://github.com/AvivK5498/The-Claude-Protocol) | 149 | Enforcement layer wrapping Claude Code with 13 hooks -- blocks unsafe operations, enforces worktree isolation |
| [Notch So Good](https://github.com/deepshal99/notch-so-good) | new | macOS notch-based session monitor with pixel-art companion, 13 animations, smart notifications, multi-session support |
| [Anima](https://github.com/btangonan/anima) | new | Native macOS companion for Claude Code. Per-project ASCII familiars, nim token economy, cross-session watcher daemon. Tauri v2 + Rust, 4MB binary |
| [crit](https://github.com/tomasz-tomczyk/crit) | 105 | Local browser UI for inline code review of any file or agent output; integrates with Claude Code via plan-hook to review and approve plans before execution, outputs structured .crit.json for agent consumption. |
| [telegram-ai-bridge](https://github.com/AliceLJY/telegram-ai-bridge) | new | Run N parallel Claude Code sessions from your phone via Telegram. War Room mode, per-bot personas, A2A multi-agent collaboration, tool approval from phone. Supports Claude Code, Codex, and Gemini backends |
| [Asynkor](https://github.com/asynkor/asynkor) | 3+ | Coordination layer for AI agent teams — file leasing, shared memory, cross-machine sync. One MCP server for Claude Code, Cursor, Windsurf, JetBrains. Open source client, hosted infrastructure |
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
| [ClaudeCode Launchpad CLI](https://github.com/noambrand/kivun-terminal) | 9 | Windows & macOS 2-minute installer for Claude Code — auto-installs Node.js, Git & Claude Code; two-line live status bar (model, context %, usage limits with reset timers); desktop shortcut with folder picker; right-click "Open with ClaudeCode Launchpad CLI" on any Windows folder; optional light-blue theme; Claude flags support |
| [clideck](https://github.com/rustykuntz/clideck) | 31 | WhatsApp-like dashboard for managing AI coding agents (Claude Code, Codex, Gemini CLI, OpenCode) in one browser window. Live status, session resume, autopilot routing between agents, mobile remote |
| [WhereMyTokens](https://github.com/jeongwookie/WhereMyTokens) | new | Windows system tray app for monitoring Claude Code token usage in real time. Per-session token counts, costs, context window progress, rate limit bars (5h/1w), activity heatmaps, and model breakdowns. Registers as a Claude Code statusLine plugin for live data without polling. Windows only |
| [Onepilot](https://onepilotapp.com) | - | iOS app for running Claude Code, Codex, and other coding agents on remote servers via SSH from your phone. Full terminal emulator with SwiftTerm, agent session management, mobile access to dev machines |
| [docker-claude-code](https://github.com/gw0/docker-claude-code) | new | Run Claude Code in an isolated Docker container with multi-profile support, security hardening, best-practice defaults, a set of pre-installed plugin/skill bundles and remote dev support. Drop-in replacement for `claude` — a simple shell alias is all it takes. |
| [amux](https://github.com/mixpeek/amux) | new | Open-source agent multiplexer for running dozens of parallel Claude Code sessions with web dashboard, self-healing watchdog, kanban board, agent-to-agent REST API, and mobile PWA. Single Python file |
| [cc-token-status](https://github.com/jayson-jia-dev/cc-token-status) | new | macOS menu bar dashboard for Claude Code. Shows live plan limits (5h/7d), costs, tokens, trends, model breakdown, user level system, and multi-machine iCloud sync. 5 languages, dark/light mode. Single Python file, auto-updates |
| [Watchfire](https://github.com/watchfire-io/watchfire) | 33 | Orchestration platform for AI coding agents (starting with Claude Code). Manages project context, breaks work into tasks, runs agents with full codebase awareness. Git worktree isolation, sandboxed execution, multiple agent modes (chat, task, autonomous). Go daemon + CLI/TUI + Electron GUI |
| [aby-claude-watcher](https://github.com/aby-agency/aby-claude-watcher) | new | Real-time macOS dashboard for Claude Code sessions. Five color-coded states (thinking, running, waiting, error, completed), per-session notifications, one-click focus terminal across iTerm2/Terminal/Warp/VSCode/Cursor/Ghostty/kitty/WezTerm/Hyper. Bilingual FR/EN, menu-bar tray, MIT licensed. Apple Silicon + Intel builds |
| [cc-config-viewer](https://github.com/kuri-sun/cc-config-viewer) | new | Browser UI for Claude Code config. View and edit settings, rules, commands, agents, skills, and plugins across all four scopes (Managed / User / Project / Local), with a "Resolved" view of the merged effective settings. |
| [cctally](https://github.com/omrikais/cctally) | new | Track Claude Code subscription usage as a weekly $-per-1% trend. Local web dashboard, terminal UI, forecasts, threshold alerts. Apache-2.0, zero telemetry. |
| [claude-code-notifier](https://github.com/saiso/claude-code-notifier) | new | Native macOS notifier for Claude Code. Swift + UserNotifications, custom Heroicons-derived icon (SF Symbols–free), click-through to your IDE (VS Code, Cursor, Windsurf, JetBrains, iTerm2, Terminal) via bundle ID swap, per-event sound labels, hardened inputs (allowlists, length caps, control-character stripping). Universal binary (arm64 + x86_64), macOS 12+, MIT |
| [ToutKit](https://github.com/toutkit/toutkit) | new | Desktop notebook for AI CLIs (Claude Code, Codex, Gemini). Pairs a sidebar of notes with a built-in terminal and an in-app webview that renders whatever the AI writes — each note is a self-contained folder with its own SQLite, key/value store, attached files, and scripts, so a note can grow from a static page into a sortable table, dashboard, or research tool. Local-first, AGPL-3.0 |

---

## Ecosystem

Notable projects, directories, and resources across the Claude Code ecosystem.

| Name | Stars | Description |
|------|-------|-------------|
| [claude-mem](https://github.com/thedotmack/claude-mem) | 35,900+ | Auto-captures everything Claude does, compresses with AI, injects context into future sessions. #1 trending GitHub Feb 2026 |
| [wshobson/agents](https://github.com/wshobson/agents) | 31,300+ | 112 specialized agents, 16 orchestrators, 146 skills, 79 tools in 72 focused plugins |
| [oh-my-claudecode](https://github.com/Yeachan-Heo/oh-my-claudecode) | 9,900+ | Teams-first multi-agent orchestration with 19 specialized agents and 28 skills |
| [ccusage](https://github.com/ryoppippi/ccusage) | 11,500+ | CLI for analyzing Claude Code usage from local JSONL files. Offline mode, zero API calls needed |
| [getburnd](https://github.com/garvitsurana271/burnd) | -- | Local-first cost-control CLI. Reads `~/.claude/projects/*.jsonl`, finds 8 cost leak patterns, prints savings estimates, generates shareable report URL. MIT |
| [claude-token-lens](https://github.com/wassimbensalem/claude-token-lens) | 587+ installs | Real-time token attribution from local Claude Code JSONL sessions — see which tool, agent, MCP server, or skill is burning your quota. Live Ink dashboard, burn rate, ETA, 5h + 7-day tracking, zero telemetry. `npm install -g claude-token-lens` |
| [cc-statistics](https://github.com/androidZzT/cc-statistics) | 270+ | Three-in-one Claude Code stats: CLI + Web + native macOS SwiftUI panel. Token costs, code changes by language, efficiency scoring, weekly reports. Supports Codex and Cursor too |
| [cc-discipline](https://github.com/TechHU-GS/cc-discipline) | new | Guardrails for Claude Code — shell hooks that physically block bad behavior (edit loops, skipped verification, destructive git), not just markdown rules. Streak-breaker hard-stops at 5 edits, pre-edit-guard enforces debugging process, 7 rules, 7 skills, 2 subagents. Interactive installer with append mode. `bash ~/.cc-discipline/init.sh` |
| [ccpm](https://github.com/automazeio/ccpm) | 7,600+ | Project management with GitHub Issues + Git worktrees for parallel agent execution |
| [claude-code-system-prompts](https://github.com/Piebald-AI/claude-code-system-prompts) | 5,900+ | Extracted system prompts from Claude Code, updated for each release |
| [claude-context](https://github.com/zilliztech/claude-context) | 5,600+ | Semantic code search MCP by Zilliz -- hybrid BM25 + vector search, ~40% token reduction |
| [claude-skills](https://github.com/alirezarezvani/claude-skills) | 5,300+ | 192 skills across 9 domains with 254 Python automation tools |
| [paco-framework](https://github.com/PenguinAlleyApps/paco-framework) | 1+ | Markdown-first multi-agent OS for Claude Code. Coordinates 3-16 specialized AI agents (Engineering, QA, Growth, Finance) with file-based dispatch, institutional memory, CEO Gate approval, and 24/7 scheduling. No Python required. MIT |
| [peon-ping](https://github.com/PeonPing/peon-ping) | 3,900+ | Warcraft III Peon voice notifications for Claude Code and other agents |
| [n8n-skills](https://github.com/czlonkowski/n8n-skills) | 3,400+ | Skills for building production-ready n8n workflows |
| [claude-hooks-mastery](https://github.com/disler/claude-code-hooks-mastery) | 3,300+ | Complete mastery guide for Claude Code hooks with production-ready scripts |
| [claude-supermemory](https://github.com/supermemoryai/claude-supermemory) | 2,300+ | Persistent memory across sessions using Supermemory |
| [myclaude](https://github.com/stellarlinkco/myclaude) | 2,400+ | Multi-agent orchestration routing to Claude Code, Codex, Gemini, and OpenCode |
| [claude-code-mcp](https://github.com/steipete/claude-code-mcp) | 1,100+ | Run Claude Code as a one-shot MCP server -- an agent in your agent |
| [ccmanager](https://github.com/kbwo/ccmanager) | 940+ | Session manager supporting 8 coding agents with smart auto-approval |
| [cog](https://github.com/marciopuga/cog) | 240+ | Cognitive architecture for Claude Code -- persistent memory, self-reflection, and foresight via plain-text conventions. Zero dependencies, just CLAUDE.md + markdown files |
| [claude-memory-bridge](https://github.com/LewenW/claude-memory-bridge) | -- | Cross-project memory sharing via namespaces. Adds a shared layer between global and project-scoped memory so projects selectively share knowledge. MCP server, no database |
| [Cortex](https://github.com/SKULLFIRE07/cortex-memory) | -- | Persistent AI memory for coding assistants. Auto-captures decisions, patterns, and context across sessions. VSCode extension + CLI + MCP server. Free |
| [openclaw-self-healing](https://github.com/Ramsbaby/openclaw-self-healing) | 32+ | 4-tier autonomous crash recovery for Claude Code and any service — 64% auto-resolved, LLM-agnostic (Claude/GPT-4/Gemini/Ollama), Prometheus metrics |
| [CCM](https://github.com/dr5hn/ccm) | 8+ | Power-user toolkit for Claude Code — multi-account management with project bindings, session cleanup, environment snapshots, permissions audit, health diagnostics. Single bash script, no runtime dependencies beyond bash 4.4+ and jq. |
| [openclaw-memorybox](https://github.com/Ramsbaby/openclaw-memorybox) | 8+ | Memory hygiene CLI for Claude Code — prevents context overflow crashes, 83% MEMORY.md size reduction, zero dependencies |
| [openclaw-self-evolving](https://github.com/Ramsbaby/openclaw-self-evolving) | 2+ | Weekly self-improvement pipeline — scans Claude Code logs, proposes CLAUDE.md/AGENTS.md rule changes, zero API cost |
| [caliber](https://github.com/caliber-ai-org/ai-setup) | -- | CLI that fingerprints projects and generates AI agent configs (CLAUDE.md, skills, AGENTS.md). Scores quality, auto-refreshes, supports Claude Code + Cursor + Codex |
| [claude-overlay](https://github.com/mzmmoazam/claude-overlay) | -- | CLI for managing Claude Code project configs across custom providers (Databricks, Bedrock, OpenRouter, LiteLLM, Cloudflare). Overlay merge/remove, MCP web search setup, multi-provider switching, team config export/import |
| [faf-cli](https://github.com/Wolfe-Jam/faf-cli) | -- | The package.json for AI context. IANA-registered `.faf` format — init, score, bi-sync with `CLAUDE.md`, export to AGENTS.md, GEMINI.md, .cursorrules. Built with Bun. |
| [git-parsec](https://github.com/erishforG/git-parsec) | 6+ | Git worktree lifecycle manager — gives each AI agent an isolated workspace tied to issue tickets (Jira, GitHub Issues, GitLab). No index.lock conflicts in parallel workflows |
| [claude-starter-kit](https://github.com/awrshift/claude-starter-kit) | new | Ready-to-use project structure with persistent memory, session continuity, hooks, and 3 bundled skills (Gemini, Brainstorm, Design) |
| [claude-code-kickstart](https://github.com/ypollak2/claude-code-kickstart) | New | Opinionated starter kit — one command to install curated MCP servers, hooks, agents, and profiles. Includes auto-detect, 12 agents, 10 profiles, and 20+ shell commands |
| [claude-code-power-stack](https://github.com/bluzername/claude-code-power-stack) | new | Ghost memory, conversation search, session naming, and Manus-style planning in a single install with cheat sheet PDF |
| [clooks](https://github.com/mauribadnights/clooks) | new | Persistent hook daemon that replaces per-invocation spawning -- 112x faster hooks with batching, dependency resolution, metrics |
| [AIRIS MCP Gateway](https://github.com/agiletec-inc/airis-mcp-gateway) | new | Docker-based MCP multiplexer that aggregates 60+ tools behind 7 meta-tools, reducing context token usage by 97%. One command to start, auto-enables servers on demand |
| [Claude Code AWS Gateway](https://github.com/antkawam/claude-code-aws-gateway) | new | Self-hosted API gateway that routes Claude Code through Amazon Bedrock with team API keys, budgets, rate limits, OIDC SSO, SCIM provisioning, and an admin portal for analytics |
| [cc-agents-md](https://github.com/GeiserX/cc-agents-md) | new | CLI tool and SessionStart hook that loads AGENTS.md files into Claude Code sessions. Walks from CWD to git root, inlines small files, emits read instructions for large ones. Supports mid-session reload, context preservation, custom patterns, and stat-based caching. GPL-3.0 |
| [gemini-claude-bridge](https://github.com/weijiafu14/gemini-claude-bridge) | new | Gemini-to-Claude protocol converter for using Gemini models as Claude Code backend. Fixes 3 LiteLLM bugs |
| [spartan-ai-toolkit](https://github.com/spartan-stratos/spartan-ai-toolkit) | new | Engineering discipline layer for Claude Code -- 67 slash commands, 20 coding rules, 27 skills, 9 agents, quality gates between every step. 8 stack profiles (Go, Python, Java, Kotlin, React, etc.), agent memory across sessions. Install: `npx @c0x12c/spartan-ai-toolkit@latest --local` |
| [AgenTopology](https://github.com/agentopology/agentopology) | New | Declarative language and CLI for multi-agent orchestration -- define agents, flows, gates, hooks, group chats in one `.at` file, scaffold to 7 platforms, interactive visualizer. Apache 2.0 |
| [cognitropy-lab](https://github.com/DaxxSec/cognitropy-lab) | -- | Autonomous workspace factory powered by a date-seeded entropy engine (363 domains, 22 categories, 18.8M unique outcomes). Builds one new Agent Workspace Model-compliant workspace daily — from firmware RE to aquaponics to satellite comms — with full slash commands, workflows, and secrets scanning. Zero human intervention.
| [brood-box](https://github.com/stacklok/brood-box) | 10+ | Run AI coding agents (Claude Code, Codex, OpenCode) inside hardware-isolated microVMs with snapshot isolation, egress control, and MCP authorization |
| [claude-kit](https://github.com/luiseiman/claude-kit) | 1 | Configuration factory for Claude Code -- 13 composable stacks, 6 agents, audit scoring, practices pipeline. Bootstraps and maintains .claude/ across projects |
| [Global Chat](https://github.com/pumanitro/global-chat) | -- | Cross-protocol MCP server discovery -- search 18K+ servers across 6+ registries. Also supports A2A and agents.txt. Free agents.txt validator. npm: `@global-chat/mcp-server` |
| [GAAI Framework](https://github.com/Fr-e-d/GAAI-framework) | 95+ | Drop-in governance layer (.gaai/ folder) -- backlog authorization, cross-session memory, decision tracking, QA gates, autonomous delivery daemon. Claude Code + Cursor + Codex CLI + Gemini CLI |
| [Wiggum CLI](https://github.com/federiconeri/wiggum-cli) | -- | Open-source AI agent that scans codebases (80+ tech), generates specs through AI interviews, and runs autonomous Ralph loops via Claude Code or Codex. Agent mode ships GitHub issues end-to-end with priority-aware scheduling and auto-merge |
| [expert-dispatch](https://github.com/simonsysun/expert-dispatch) | new | Specialist Dispatch Pattern -- let cheap AI assistants delegate complex tasks to Claude Code CLI. Bash adapter with run/resume/review workflow, session continuity, per-project directories, and structured JSON output. Designed to be called by another AI system |
| [Claude Command Center](https://github.com/tuning-labs-oss/claude-command-center) | -- | Production-tested workspace template with session hooks, structured memory (4 types), multi-domain routing, daily task tracking, and interactive /setup onboarding. 6 domain templates, pre-commit safety, example skills |
| [Code Insights](https://github.com/melagiri/code-insights) | 8 | Local-first CLI and dashboard for analyzing AI coding sessions from Claude Code, Cursor, Codex CLI, Copilot CLI, and VS Code Copilot. SQLite-backed with terminal analytics, browser dashboard, and LLM-powered insights |
| [PRISM](https://github.com/jakeefr/prism) | 15 | Session intelligence for Claude Code — reads ~/.claude/projects/ JSONL to surface token waste, CLAUDE.md adherence failures, and attention curve degradation. Generates diff-format CLAUDE.md recommendations. Read-only, zero telemetry |
| [claude-code-cheat-sheet](https://cc.storyfox.cz/) | new | Complete one-page printable reference — all shortcuts, commands, CLI flags, MCP config, memory, skills, agents. Auto-updated daily from official docs. [EN](https://cc.storyfox.cz/) · [ZH](https://cc.storyfox.cz/zh/) · [JA](https://cc.storyfox.cz/jp/) · [KO](https://cc.storyfox.cz/kr/) |
| [Not Human Search MCP](https://nothumansearch.ai/) | -- | Agent-first search engine for AI-accessible tools — 9,000+ sites indexed. Search by category, check agentic scores, verify MCP endpoints. MCP server at `nothumansearch.ai/mcp`, REST API at `/api/v1/search`. Go. |
| [AI Dev Jobs MCP](https://aidevboard.com/) | -- | AI/ML job board with 5,200+ roles across 260+ companies. Search jobs, filter by tags/salary/location, post listings programmatically. MCP server at `aidevboard.com/mcp`, REST API at `/api/v1/jobs`. Go. |
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
| [codachi](https://github.com/vincent-k2026/codachi) | New | Tamagotchi-style statusline pet that grows with context usage, shows cache hit rate and burn speed |
| [claude-skins](https://github.com/basicScandal/claude-skins) | New | 9 custom visual themes for Claude Code — terminal colors, ASCII art banners, personality voices, status lines, and tool sounds. One-command install, pure bash engine. |
| [claude-code-memory-guide](https://github.com/Acteq1391gp/claude-code-memory-guide) | 2 | Zero-to-production memory setup: CLAUDE.md + MEMORY.md + MemPalace semantic search + session hooks + warm-model daemon + nightly Karpathy compile with free-LLM key rotation. Three guides — linear tutorial, memory format reference, automation reference. Runnable scripts, secrets-in-git precommit guard, end-to-end verification checklist. MIT |
| [cc-hud](https://github.com/WaterTian/cc-hud) | New | Compact single-line Claude Code statusline -- model, context usage (1/8-char progress bar), active subagents, 5h/7d rate-limit countdowns. Pure Node.js, zero deps, Windows-safe. |
| [awesome-claude-code-subagents](https://github.com/VoltAgent/awesome-claude-code-subagents) | 15,600+ | 100+ specialized Claude Code subagents organized by domain |
| [serena](https://github.com/oraios/serena) | 22,200+ | Semantic retrieval and editing MCP server for coding agents -- code-aware search and navigation |
| [Understand-Anything](https://github.com/Lum1104/Understand-Anything) | 7,000+ | Turns any codebase into an interactive knowledge graph for exploration |
| [n8n-mcp](https://github.com/czlonkowski/n8n-mcp) | 17,000+ | MCP for Claude Code to build and manage n8n automation workflows |
| [ToolRouter](https://toolrouter.com) | -- | Give Claude Code superpowers -- 150+ tools on demand with one account. Competitor research, video production, web search, image generation, security scanning, and more. `claude mcp add toolrouter -- npx -y toolrouter-mcp` |
| [Claudoscope](https://github.com/cordwainersmith/claudoscope) | 29 | Native macOS menu bar app for Claude Code session analytics. Token/cost tracking, full-text search, real-time secret detection, config health linting (44 rules). Reads local JSONL files, fully offline, zero telemetry. Swift/SwiftUI, Homebrew install |
| [LynxPrompt](https://github.com/GeiserX/LynxPrompt) | 25+ | Open-source platform for managing AI coding agent configs (CLAUDE.md, AGENTS.md, .cursorrules, copilot-instructions.md). Web marketplace, CLI, VS Code extension, self-hostable via Docker/Helm with federation support |
| [Solo Orchestrator](https://github.com/kraulerson/solo-orchestrator) | 4 | Phase-gated development methodology for building production-quality applications with Claude Code. One-command setup generates CLAUDE.md, CI/CD pipelines, pre-commit hooks, and security tooling. Auto-discovers new platforms and languages from the filesystem. Includes enterprise governance, intake wizard, and adversarial evaluation prompts. [Example project](https://github.com/kraulerson/solo-orchestrator-example-project) shows the complete artifact trail. |
| [vibe-replay](https://github.com/tuo-lei/vibe-replay) | new | Turn AI coding sessions into shareable, interactive HTML replays with animated playback, insights, and PR integration. Supports Claude Code and Cursor. [Website](https://vibe-replay.com) |
| [AgentsInFlow](https://github.com/hhammoud/AgentsInFlow) | new | Self-hosted desktop workspace for governed AI development — run Claude Code, Codex, Cursor, OpenCode in isolated runtimes with persistent memory, ticket-driven orchestration, git worktrees per execution, browser bridge, 28 diagram types, session forking. Free early access, no sign-up. Electron (macOS/Windows) |
| [SpecLock](https://github.com/sgroy10/speclock) | new | AI Constraint Engine for Claude Code — enforces CLAUDE.md, .cursorrules, AGENTS.md as pre-commit law. Catches euphemisms, temporal evasion, synonym substitution, compound violations. 51 MCP tools, 1,009 tests, on Official MCP Registry. `npx speclock protect` |
| [TokRepo](https://tokrepo.com) | -- | Curated, community-ranked registry of 600+ agent skills, MCP servers, prompts, scripts, workflows, and configs. Cross-platform tagging (Claude Code, Codex CLI, Gemini CLI, Cursor), upvotes and usage data |
| [claudecode-harness](https://github.com/AdelElo13/claude-harness) | new | One-command installer for production-grade Claude Code setup — 34 hooks (quality gates, auto-formatting, security monitoring, session memory), 36 agents, 77 rules across 13 languages, 27 MCP server templates. Zero deps, MIT. `npx claudecode-harness` |
| [claudex-setup](https://github.com/DnaFin/claudex) | new | Audit and optimize any project for Claude Code — scores 0-100, auto-fixes configuration across 972 verified techniques. Zero deps. `npx claudex-setup` |
| [Agent Sessions](https://github.com/jazzyalex/agent-sessions) | 495+ | Native macOS app to search, browse, and resume Claude Code, Codex, Gemini CLI, OpenCode, and other local agent sessions, with Agent Cockpit live iTerm2 orchestration |
| [Claude Code Skills 中文精选集](https://claude-skills.bt199.com/) | -- | Chinese curated directory of 140+ Claude Code Skills, Agents, Plugins, and workflows for Chinese-speaking Claude Code users |
| [nylas/cli](https://github.com/nylas/cli) | new | Email, calendar, and contacts CLI for Claude Code. Built-in MCP server with 16 tools across Gmail, Outlook, Exchange, Yahoo, iCloud, and IMAP. One-line install: `nylas mcp install`. Works with Claude Code, Cursor, Codex, and Windsurf. Docs: https://cli.nylas.com |
| [agenttrace](https://github.com/luoyuctl/agenttrace) | new | TUI observability for Claude Code, Codex CLI, Gemini CLI, Aider, Cursor exports, and more. Tracks cost, tokens, tool failures, latency, anomalies, health, diffs, and CI gates from local session logs |
| [agent-shadow-brain](https://github.com/theihtisham/agent-shadow-brain) | 8+ | AI-powered background code analysis agent for Claude Code that continuously monitors your codebase and provides intelligent suggestions. npm: `@theihtisham/agent-shadow-brain` |
| [omni-skills-forge](https://github.com/theihtisham/omni-skills-forge) | 11+ | Universal skill and slash-command manager for AI coding assistants. Create, share, and manage reusable skills across tools. npm: `omni-skills-forge` |
| [cc-tempo](https://github.com/O0000-code/cc-tempo) | New | Claude Code statusline with wall-clock active work time, SubAgent speedup ratio, /clear-resilient PID timer, code-churn sparkline with trend arrow, and multi-instance detection. Bash + TypeScript, MIT. |
| [The Froject](https://www.thefroject.com) | new | Free browser-based wizard that generates complete Claude Code workspaces for go-to-market teams (marketing, sales, customer success, HR, finance, operations). Downloads a ZIP including CLAUDE.md, context files, and pre-built skills, commands, agents, rules, hooks, and settings tailored to your role. Client-side, no backend. Plugin marketplace at [thefroject-plugins](https://github.com/bjorn-ingmanson/thefroject-plugins). |
| [Bring Your AI](https://bringyour.ai/claude-code-to-codex) | -- | Local-first Claude Code to Codex migration path. Keeps harness files local, maps CLAUDE.md/AGENTS.md guidance and MCP config, and adds a Codex import checklist for hooks, secret refs, and non-equivalent behavior before Codex edits code. |
| [Drevon](https://drevon.dev) | new | Mac desktop workspace for GTM engineers. Run parallel AI agents powered by Claude Code, Codex, or Copilot to build target lists, score accounts, and pull prospect intel. |
| [voidly-mcp-server](https://github.com/voidly-ai/mcp-server) | new | 116 tools for Claude Code covering censorship intelligence (19.6M OONI measurements, 126 countries), E2E encrypted agent-to-agent messaging, and agent payments. Install: `claude mcp add voidly -- npx -y @voidly/mcp-server` |
| [systemprompt-template](https://github.com/systempromptio/systemprompt-template) | -- | Governance infrastructure for Claude Code. Single compiled Rust binary that authenticates, authorises, rate-limits, logs, and attributes costs for every AI interaction before it reaches a tool or database. Self-hosted, air-gap capable, MCP + A2A compatible. BSL-1.1 |
| [llm-prices](https://github.com/benbencodes/llm-prices) | new | CLI + Python library + MCP server to look up and compare LLM API costs across 167 models from 23 providers (OpenAI, Anthropic, Google, xAI, DeepSeek, Groq, and more). Ask Claude "what's the cheapest model for 10k input + 2k output?" before making API calls. Zero deps, no API key. `pipx install git+https://github.com/benbencodes/llm-prices` |

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
| [Claude Code Guide](https://claudecodeguide.dev) | Guide | Beginner-friendly guide from first install to daily operating system, zero jargon ([GitHub](https://github.com/mshadmanrahman/claudecode-guide)) |
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
| [awesome-claude-design](https://github.com/rohitg00/awesome-claude-design) | ![Stars](https://img.shields.io/github/stars/rohitg00/awesome-claude-design?style=flat-square&label=) | DESIGN.md files grouped by aesthetic family (editorial, terminal, warm, data-dense, cinematic, playful, glass, brutalist, indie) + remix recipes + prompt packs for Claude Design (Anthropic Labs) |
| [ai-skill](https://github.com/anomalyco/ai-skill) | - | AI skill discovery and management system - helps users find, evaluate, install and manage agent skills, tools, plugins and extensions |
| [Awesome AI Startups](https://github.com/nowork-studio/awesome-ai-startups) | new | Curated directory of ~440 indie-built AI products (bootstrapped, pre-seed, angel-funded) across 18 categories — AI agents, coding tools, marketing, audio/voice, image/design, video, and more |

## Contributing

Contributions are welcome. See [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines.

## License

[Apache-2.0](LICENSE)
| [AutoSearch](https://github.com/0xmariowu/Autosearch) | new | Self-evolving deep research plugin for Claude Code -- 32 dedicated search channels (arXiv, GitHub, Reddit, HN, zhihu, bilibili, CSDN + 25 more), LLM-scored evaluation, cited reports in Markdown/HTML/Slides, cross-session learning. Zero API keys required |


---

## SKY-lv Skills

30+ battle-tested OpenClaw skills for agent development. MIT Licensed.

- [skylv-agent-evaluator](https://github.com/SKY-lv/agent-evaluator) - Score agent behavior
- [skylv-metacognition-engine](https://github.com/SKY-lv/metacognition-engine) - Self-reflection
- [skylv-self-healing-agent](https://github.com/SKY-lv/self-healing-agent) - Auto-repair errors
- [skylv-cost-guard](https://github.com/SKY-lv/cost-guard) - API cost optimization
- [skylv-browser-automation-agent](https://github.com/SKY-lv/browser-automation-agent) - Browser automation
- [skylv-diff-viewer](https://github.com/SKY-lv/diff-viewer) - Diff comparison

[ClawHub](https://clawhub.ai/skylv) | [Landing](https://sky-lv.github.io/awesome-openclaw-skills)
