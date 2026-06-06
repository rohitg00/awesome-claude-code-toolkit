# Project Name

One-line description of the project's purpose.

## Stack
- **Language**: TypeScript 5.x
- **Framework**: Next.js 15 (App Router)
- **Database**: PostgreSQL with Prisma ORM
- **Testing**: Vitest + Playwright
- **Package Manager**: pnpm

## Commands
- `pnpm install` - Install dependencies
- `pnpm dev` - Start dev server at localhost:3000
- `pnpm build` - Production build
- `pnpm test` - Run unit tests with Vitest
- `pnpm test:e2e` - Run Playwright end-to-end tests
- `pnpm lint` - Run ESLint
- `pnpm typecheck` - Run TypeScript compiler check
- `pnpm db:migrate` - Run database migrations
- `pnpm db:seed` - Seed the database

## Project Structure
```
src/
  app/           - Next.js App Router pages and layouts
  components/    - Reusable React components
  lib/           - Business logic and utilities
  server/        - Server-side code (API, database, auth)
  types/         - Shared TypeScript type definitions
prisma/          - Database schema and migrations
tests/           - Test files mirroring src/ structure
```

## Conventions
- Conventional commits: `type(scope): message`
- Feature branches: `feature/short-description`, merge via PR
- Server components by default, `'use client'` only when needed
- Validate API inputs with Zod schemas
- Handle loading, error, and empty states in all UI components
- No `any` types. Use `unknown` with type guards
- 80% minimum test coverage on new code

## Environment Variables
- `DATABASE_URL` - PostgreSQL connection string
- `NEXTAUTH_SECRET` - Auth session encryption key
- `NEXTAUTH_URL` - Base URL for auth callbacks

## Key Decisions
- Cursor-based pagination for all list endpoints
- Repository pattern for data access layer
- Error responses follow `{ error: { code, message, details } }` format
- All dates stored and transmitted as ISO 8601 UTC strings
