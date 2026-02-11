# Claude Code Toolkit

**The most comprehensive toolkit for Claude Code -- 135 agents, 35 curated skills (+15,000 via [SkillKit](https://agenstskills.com)), 42 commands, 120 plugins, 19 hooks, 15 rules, 7 templates, 6 MCP configs, and more.**

[![Awesome](https://cdn.rawgit.com/sindresorhus/awesome/d7305f38d29fed78fa85652e3a63e154dd8e8829/media/badge.svg)](https://github.com/sindresorhus/awesome)
[![License: Apache-2.0](https://img.shields.io/badge/License-Apache%202.0-blue.svg)](LICENSE)
[![PRs Welcome](https://img.shields.io/badge/PRs-welcome-brightgreen.svg)](CONTRIBUTING.md)
[![Last Updated](https://img.shields.io/badge/Last%20Updated-Feb%202026-orange.svg)](#)
[![Files](https://img.shields.io/badge/Files-796-blueviolet.svg)](#project-structure)

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

- [Plugins](#plugins) (120)
- [Agents](#agents) (135)
- [Skills](#skills) (35)
- [Commands](#commands) (42)
- [Hooks](#hooks) (19 scripts)
- [Rules](#rules) (15)
- [Templates](#templates) (7)
- [MCP Configs](#mcp-configs) (6)
- [Contexts](#contexts) (5)
- [Examples](#examples) (3)
- [Setup](#setup)
- [Contributing](#contributing)

---

## Plugins

One hundred twenty production-ready plugins that extend Claude Code with domain-specific capabilities.

| Plugin | Description |
|--------|-------------|
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
| [bundle-analyzer](plugins/bundle-analyzer/) | Frontend bundle size analysis and tree-shaking optimization |
| [changelog-gen](plugins/changelog-gen/) | Generate changelogs from git history with conventional commit parsing |
| [changelog-writer](plugins/changelog-writer/) | Detailed changelog authoring from git history and PRs |
| [ci-debugger](plugins/ci-debugger/) | Debug CI/CD pipeline failures and fix configurations |
| [code-architect](plugins/code-architect/) | Generate architecture diagrams and technical design documents |
| [code-explainer](plugins/code-explainer/) | Explain complex code and annotate files with inline documentation |
| [code-guardian](plugins/code-guardian/) | Automated code review, security scanning, and quality enforcement |
| [code-review-assistant](plugins/code-review-assistant/) | Automated code review with severity levels and actionable feedback |
| [codebase-documenter](plugins/codebase-documenter/) | Auto-document entire codebase with inline comments and API docs |
| [color-contrast](plugins/color-contrast/) | Color contrast checking and accessible color suggestions |
| [commit-commands](plugins/commit-commands/) | Advanced commit workflows with smart staging and push automation |
| [complexity-reducer](plugins/complexity-reducer/) | Reduce cyclomatic complexity and simplify functions |
| [compliance-checker](plugins/compliance-checker/) | Regulatory compliance verification for GDPR, SOC2, and HIPAA |
| [content-creator](plugins/content-creator/) | Technical content generation for blog posts and social media |
| [context7-docs](plugins/context7-docs/) | Fetch up-to-date library documentation via Context7 for accurate coding |
| [contract-tester](plugins/contract-tester/) | API contract testing with Pact for microservice compatibility |
| [create-worktrees](plugins/create-worktrees/) | Git worktree management for parallel development workflows |
| [cron-scheduler](plugins/cron-scheduler/) | Cron job configuration and schedule validation |
| [css-cleaner](plugins/css-cleaner/) | Find unused CSS and consolidate stylesheets |
| [data-privacy](plugins/data-privacy/) | Data privacy implementation with PII detection and anonymization |
| [database-optimizer](plugins/database-optimizer/) | Database query optimization with index recommendations and EXPLAIN analysis |
| [dead-code-finder](plugins/dead-code-finder/) | Find and remove dead code across the codebase |
| [debug-session](plugins/debug-session/) | Interactive debugging workflow with git bisect integration |
| [dependency-manager](plugins/dependency-manager/) | Audit, update, and manage project dependencies with safety checks |
| [deploy-pilot](plugins/deploy-pilot/) | Deployment automation with Dockerfile generation, CI/CD pipelines, and infrastructure as code |
| [desktop-app](plugins/desktop-app/) | Desktop application scaffolding with Electron or Tauri |
| [devops-automator](plugins/devops-automator/) | DevOps automation scripts for CI/CD, health checks, and deployments |
| [discuss](plugins/discuss/) | Debate implementation approaches with structured pros and cons analysis |
| [doc-forge](plugins/doc-forge/) | Documentation generation, API docs, and README maintenance |
| [docker-helper](plugins/docker-helper/) | Build optimized Docker images and improve Dockerfile best practices |
| [double-check](plugins/double-check/) | Verify code correctness with systematic second-pass analysis |
| [e2e-runner](plugins/e2e-runner/) | End-to-end test execution and recording for web applications |
| [embedding-manager](plugins/embedding-manager/) | Manage vector embeddings and similarity search |
| [env-manager](plugins/env-manager/) | Set up and validate environment configurations across environments |
| [env-sync](plugins/env-sync/) | Environment variable syncing and diff across environments |
| [experiment-tracker](plugins/experiment-tracker/) | ML experiment tracking with metrics logging and run comparison |
| [explore](plugins/explore/) | Smart codebase exploration with dependency mapping and structure analysis |
| [feature-dev](plugins/feature-dev/) | Full feature development workflow from spec to completion |
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
| [n8n-workflow](plugins/n8n-workflow/) | Generate n8n automation workflows from natural language descriptions |
| [onboarding-guide](plugins/onboarding-guide/) | New developer onboarding documentation generator |
| [openapi-expert](plugins/openapi-expert/) | OpenAPI spec generation, validation, and client code scaffolding |
| [optimize](plugins/optimize/) | Code optimization for performance and bundle size reduction |
| [perf-profiler](plugins/perf-profiler/) | Performance analysis, profiling, and optimization recommendations |
| [performance-monitor](plugins/performance-monitor/) | Profile API endpoints and run benchmarks to identify performance bottlenecks |
| [plan](plugins/plan/) | Structured planning with risk assessment and time estimation |
| [pr-reviewer](plugins/pr-reviewer/) | Review pull requests with structured analysis and approve with confidence |
| [product-shipper](plugins/product-shipper/) | Ship features end-to-end with launch checklists and rollout plans |
| [project-scaffold](plugins/project-scaffold/) | Scaffold new projects and add features with best-practice templates |
| [prompt-optimizer](plugins/prompt-optimizer/) | Analyze and optimize AI prompts for better results |
| [python-expert](plugins/python-expert/) | Python-specific development with type hints and idiomatic refactoring |
| [query-optimizer](plugins/query-optimizer/) | SQL query optimization and execution plan analysis |
| [rag-builder](plugins/rag-builder/) | Build Retrieval-Augmented Generation pipelines |
| [rapid-prototyper](plugins/rapid-prototyper/) | Quick prototype scaffolding with minimal viable structure |
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
| [visual-regression](plugins/visual-regression/) | Visual regression testing with screenshot comparison |
| [web-dev](plugins/web-dev/) | Full-stack web development with app scaffolding and page generation |
| [workflow-optimizer](plugins/workflow-optimizer/) | Development workflow analysis and optimization recommendations |

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

Thirty-five curated skill modules included in this repo, with access to **15,000+ additional skills** via the [SkillKit marketplace](https://agenstskills.com). Each included skill teaches Claude Code domain-specific patterns with code examples, anti-patterns, and checklists.

| Skill | Directory | What It Teaches |
|-------|-----------|-----------------|
| TDD Mastery | `skills/tdd-mastery/` | Red-green-refactor, test-first design, coverage targets |
| API Design Patterns | `skills/api-design-patterns/` | RESTful conventions, versioning, pagination, error responses |
| Database Optimization | `skills/database-optimization/` | Query planning, indexing, N+1 prevention, connection pooling |
| Frontend Excellence | `skills/frontend-excellence/` | Component architecture, state management, performance budgets |
| Security Hardening | `skills/security-hardening/` | Input validation, auth patterns, secrets management, CSP |
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
| [Reepl - LinkedIn Content Creation](https://github.com/reepl-io/skills) | `npx skills add reepl-io/skills` | 18 tools for LinkedIn content management: drafts, publishing, scheduling, voice profiles, contacts, collections, templates, and AI image generation |

### Installing Skills

**Browse and install via SkillKit** (recommended):

```bash
npx skillkit@latest install claude-code-toolkit/tdd-mastery
```

### 15,000+ Skills via SkillKit Marketplace

This toolkit includes 35 curated skills. For access to **15,000+ additional skills** across every domain, use [SkillKit](https://agenstskills.com):

```bash
npx skillkit@latest                    # Launch interactive TUI
npx skillkit@latest search "react"     # Search 15,000+ skills
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

Nineteen hook scripts covering all eight Claude Code lifecycle events. Place `hooks.json` in your `.claude/` directory.

### Hook Scripts

| Script | Trigger | Purpose |
|--------|---------|---------|
| `session-start.js` | SessionStart | Load project context, detect package manager |
| `session-end.js` | SessionEnd | Save session state for next session |
| `context-loader.js` | SessionStart | Load CLAUDE.md, git status, pending todos |
| `learning-log.js` | SessionEnd | Extract and save session learnings |
| `pre-compact.js` | PreCompact | Save important context before compaction |
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

### Installing Hooks

```bash
cp hooks/hooks.json .claude/hooks.json
cp -r hooks/scripts/ .claude/hooks/scripts/
```

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

Six curated Model Context Protocol server configurations.

| Config | File | Servers Included |
|--------|------|-----------------|
| Recommended | [`recommended.json`](mcp-configs/recommended.json) | 14 essential servers for general development |
| Full Stack | [`fullstack.json`](mcp-configs/fullstack.json) | Filesystem, GitHub, Postgres, Redis, Puppeteer |
| Kubernetes | [`kubernetes.json`](mcp-configs/kubernetes.json) | kubectl-mcp-server, Docker, GitHub |
| Data Science | [`data-science.json`](mcp-configs/data-science.json) | Jupyter, SQLite, PostgreSQL, Filesystem |
| Frontend | [`frontend.json`](mcp-configs/frontend.json) | Puppeteer, Figma, Storybook |
| DevOps | [`devops.json`](mcp-configs/devops.json) | AWS, Docker, GitHub, Terraform, Sentry |

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
claude-code-toolkit/               796 files
  plugins/                         120 plugins (220 command files)
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
    hooks.json                     24 hook entries
    scripts/                       19 Node.js scripts
  rules/                           15 coding rules
  templates/claude-md/             7 CLAUDE.md templates
  mcp-configs/                     6 server configurations
  contexts/                        5 context modes
  examples/                        3 walkthrough examples
  setup/                           Interactive installer
```

---

## Contributing

Contributions are welcome. See [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines.

## License

[Apache-2.0](LICENSE)
