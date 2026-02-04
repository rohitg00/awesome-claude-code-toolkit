# Project Name

One-line description.

## Stack
- **Language**: TypeScript 5.x
- **Framework**: Next.js 15 (App Router)
- **Database**: PostgreSQL 16 with Prisma ORM
- **Cache**: Redis 7 for sessions and query caching
- **Queue**: BullMQ for background jobs
- **Testing**: Vitest (unit), Playwright (e2e)
- **CI/CD**: GitHub Actions
- **Deployment**: Docker on AWS ECS
- **Package Manager**: pnpm

## Commands
- `pnpm install` - Install all dependencies
- `pnpm dev` - Start dev server (localhost:3000)
- `pnpm build` - Production build
- `pnpm start` - Start production server
- `pnpm test` - Unit tests
- `pnpm test:e2e` - End-to-end tests
- `pnpm test:coverage` - Coverage report
- `pnpm lint` - ESLint check
- `pnpm typecheck` - TypeScript compiler check
- `pnpm db:migrate` - Apply pending migrations
- `pnpm db:seed` - Seed database with test data
- `pnpm db:studio` - Open Prisma Studio
- `pnpm docker:build` - Build Docker image
- `pnpm docker:run` - Run Docker container locally

## Project Structure
```
src/
  app/              - Next.js pages, layouts, API routes
  components/
    ui/             - Primitive UI components (Button, Input, Modal)
    features/       - Feature-specific composed components
  lib/
    auth/           - Authentication logic and middleware
    db/             - Database client, repositories, queries
    cache/          - Redis client and caching utilities
    queue/          - Background job definitions and processors
    utils/          - Pure utility functions
  server/
    api/            - API route handlers
    middleware/     - Express-style middleware (auth, rate-limit, validation)
    services/       - Business logic layer (orchestrates repositories)
  types/            - Shared TypeScript interfaces and enums
prisma/
  schema.prisma     - Database schema
  migrations/       - Migration files
tests/
  unit/             - Unit tests mirroring src/ structure
  e2e/              - Playwright test specs
  fixtures/         - Shared test data and factories
scripts/            - Build, deploy, and maintenance scripts
```

## Architecture
- **Layered architecture**: Handler -> Service -> Repository -> Database
- **Dependency injection** via constructor parameters, no DI container
- **Repository pattern** for all data access (no raw Prisma calls in services)
- **Result type** for error handling in services (no thrown exceptions in business logic)
- **Event-driven** background processing via BullMQ for emails, notifications, reports

## Conventions

### Code Style
- No `any` types. Use `unknown` + type guards or generics.
- Maximum 40 lines per function. Extract helpers with descriptive names.
- Maximum 3 parameters per function. Use options object for more.
- No magic numbers. Extract named constants.
- No nested ternaries. Use if/else or early returns.
- Import order: stdlib, external, internal absolute, relative, types.

### API Design
- RESTful: plural nouns, standard HTTP methods and status codes.
- Response shape: `{ data, error, meta }` for all endpoints.
- Cursor-based pagination: `?cursor=abc&limit=20`.
- Rate limiting: 100 req/min for public, 1000 req/min for authenticated.
- All inputs validated with Zod at the handler level.

### Database
- All queries go through repositories. Services never import Prisma directly.
- Migrations are forward-only and reversible.
- Indexes on all foreign keys and columns used in WHERE/ORDER BY.
- Soft delete (`deletedAt` timestamp) for user-facing entities.

### Testing
- 80% line coverage, 75% branch coverage minimum.
- Unit tests for services and utilities.
- Integration tests for repositories (against test database).
- E2E tests for critical user flows (auth, core CRUD, payment).
- No skipped tests in CI. Fix or remove.

### Git
- Conventional commits: `type(scope): subject`.
- Feature branches from main. Squash merge PRs.
- No force push to main. No direct commits to main.
- All PRs require one approval and passing CI.

## Environment Variables
- `DATABASE_URL` - PostgreSQL connection string
- `REDIS_URL` - Redis connection string
- `NEXTAUTH_SECRET` - Auth encryption key
- `NEXTAUTH_URL` - Base URL for auth
- `AWS_REGION` - AWS region for services
- `S3_BUCKET` - File upload bucket
- `SMTP_HOST` / `SMTP_PORT` / `SMTP_USER` / `SMTP_PASS` - Email config
- `SENTRY_DSN` - Error tracking

## Subagent Instructions
- **Security audit**: Focus on OWASP Top 10, check auth middleware, input validation, SQL injection.
- **Performance review**: Check N+1 queries, missing indexes, unbounded queries, large payloads.
- **Test generation**: Follow existing patterns in tests/ directory, use factories from fixtures/.
- **Documentation**: Update this file when architecture or conventions change.

## Memory Bank
- Track decisions made during the session in a `## Session Notes` section.
- Before compaction, save the current task state and any pending items.
- On session start, check `## Session Notes` for context from previous sessions.

## Key Decisions Log
| Date | Decision | Rationale |
|------|----------|-----------|
| YYYY-MM-DD | Chose Prisma over Drizzle | Team familiarity, migration tooling |
| YYYY-MM-DD | Cursor pagination over offset | Performance at scale, no skipped rows |
| YYYY-MM-DD | BullMQ over Temporal | Simpler for current scale, lower ops overhead |
