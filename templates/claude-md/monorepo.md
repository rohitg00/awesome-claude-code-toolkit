# Acme Platform

Monorepo for the Acme SaaS platform: web app, API server, shared libraries, and infrastructure.

## Stack
- **Build System**: Turborepo 2.x
- **Package Manager**: pnpm 9.x with workspaces
- **Languages**: TypeScript 5.x (apps), Go 1.22 (services)
- **Frontend**: Next.js 15 (App Router), Tailwind CSS 4, Radix UI
- **Backend**: Hono (API gateway), tRPC (internal RPC)
- **Database**: PostgreSQL 16, Prisma ORM (shared schema)
- **Cache**: Redis 7 (sessions, rate limiting, pub/sub)
- **Queue**: BullMQ (email, notifications, reports)
- **Testing**: Vitest (unit), Playwright (e2e), k6 (load)
- **CI/CD**: GitHub Actions, Docker, AWS ECS
- **Observability**: OpenTelemetry, Grafana, Sentry

## Commands
- `pnpm install` - Install all workspace dependencies
- `pnpm dev` - Start all apps in development mode
- `pnpm dev --filter=@acme/web` - Start only the web app
- `pnpm dev --filter=@acme/api` - Start only the API server
- `pnpm build` - Build all packages and apps
- `pnpm test` - Run tests across all packages
- `pnpm test --filter=@acme/core` - Run tests for a specific package
- `pnpm lint` - Lint all packages
- `pnpm typecheck` - Type check all packages
- `pnpm db:migrate` - Run database migrations
- `pnpm db:seed` - Seed database with test data
- `turbo run build --graph` - Visualize the dependency graph
- `pnpm changeset` - Create a changeset for versioning

## Workspace Structure
```
apps/
  web/              - Next.js customer-facing web app (port 3000)
  admin/            - Next.js internal admin dashboard (port 3001)
  api/              - Hono API gateway (port 4000)
  worker/           - BullMQ background job processor
packages/
  core/             - Shared business logic, validators, constants
  db/               - Prisma client, repositories, migrations
  ui/               - Shared React component library (Radix + Tailwind)
  config-eslint/    - Shared ESLint configuration
  config-ts/        - Shared TypeScript configuration
  email/            - Email templates (React Email)
  logger/           - Structured logging (Pino)
services/
  billing/          - Go billing microservice (Stripe integration)
  search/           - Go search service (Meilisearch proxy)
infra/
  terraform/        - AWS infrastructure as code
  docker/           - Dockerfiles for all services
  k8s/              - Kubernetes manifests
```

## Package Dependencies
- `@acme/core` has zero external dependencies (pure business logic).
- `@acme/db` depends on `@acme/core` for types and validators.
- `@acme/ui` depends on `@acme/core` for constants and types.
- Apps depend on packages but packages never depend on apps.
- Use `workspace:*` for all internal package references.

## Conventions
- Changes spanning multiple packages require a changeset (`pnpm changeset`).
- Each package has its own `tsconfig.json` extending `@acme/config-ts`.
- Each package has its own test suite. No cross-package test imports.
- Shared types live in `@acme/core/types`. App-specific types stay in the app.
- Database access only through `@acme/db` repositories. No raw Prisma in apps.
- Feature flags managed through LaunchDarkly SDK in `@acme/core/flags`.

## Environment Variables
- `DATABASE_URL` - PostgreSQL connection (used by `@acme/db`)
- `REDIS_URL` - Redis connection (used by API and worker)
- `STRIPE_SECRET_KEY` - Stripe API key (used by billing service)
- `MEILISEARCH_HOST` - Search service URL
- `SENTRY_DSN` - Error tracking (per-app DSN)
- `LAUNCHDARKLY_SDK_KEY` - Feature flags

## Key Decisions
| Date | Decision | Rationale |
|------|----------|-----------|
| 2025-08-01 | Turborepo over Nx | Simpler config, native pnpm support |
| 2025-09-15 | Go for billing/search | Performance-critical, team has Go experience |
| 2025-10-01 | Prisma shared schema | Single source of truth, type-safe queries |
| 2025-11-20 | React Email over MJML | Component reuse, TypeScript support |
