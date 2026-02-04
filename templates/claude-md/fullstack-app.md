# TaskFlow

Project management app with real-time collaboration, Kanban boards, and team dashboards.

## Stack
- **Language**: TypeScript 5.x
- **Frontend**: Next.js 15 (App Router), Tailwind CSS 4, shadcn/ui
- **Backend**: Next.js API Routes + tRPC 11 for type-safe RPC
- **Database**: PostgreSQL 16, Drizzle ORM
- **Auth**: NextAuth.js 5 (GitHub + Google OAuth, magic link)
- **Real-time**: Liveblocks (collaborative cursors, presence, storage)
- **File Storage**: Uploadthing (S3-backed uploads)
- **Email**: React Email + Resend
- **Testing**: Vitest (unit), Playwright (e2e)
- **Package Manager**: pnpm
- **Deployment**: Vercel (frontend), Neon (serverless Postgres)

## Commands
- `pnpm install` - Install dependencies
- `pnpm dev` - Start Next.js dev server (localhost:3000)
- `pnpm build` - Production build
- `pnpm start` - Start production server
- `pnpm test` - Run Vitest unit tests
- `pnpm test:e2e` - Run Playwright tests
- `pnpm test:e2e --ui` - Playwright tests with UI mode
- `pnpm lint` - ESLint + Prettier check
- `pnpm typecheck` - TypeScript compiler check
- `pnpm db:push` - Push schema changes to database
- `pnpm db:migrate` - Generate and apply migrations
- `pnpm db:studio` - Open Drizzle Studio (localhost:4983)
- `pnpm db:seed` - Seed database with sample data
- `pnpm email:dev` - Preview email templates (localhost:3001)

## Project Structure
```
src/
  app/
    (auth)/           - Auth pages (sign-in, sign-up, verify)
    (dashboard)/      - Authenticated dashboard layout
      projects/       - Project list and detail pages
      boards/         - Kanban board views
      settings/       - User and team settings
    api/
      trpc/[trpc]/    - tRPC HTTP handler
      webhooks/       - Stripe, GitHub webhook handlers
      uploadthing/    - File upload endpoint
  components/
    ui/               - shadcn/ui primitives (Button, Dialog, Card)
    layout/           - Shell, Sidebar, Header, Breadcrumbs
    boards/           - Kanban-specific components (Column, Card, DragOverlay)
    forms/            - Form components with react-hook-form + zod
  server/
    db/
      schema.ts       - Drizzle schema definitions
      index.ts        - Database client
      migrations/     - Generated migration SQL files
    trpc/
      router.ts       - Root tRPC router
      context.ts      - tRPC context (session, db)
      procedures/     - Individual procedure files (projects, tasks, teams)
    auth/
      config.ts       - NextAuth.js configuration
      providers.ts    - OAuth provider setup
    email/
      templates/      - React Email components
      send.ts         - Resend client wrapper
  lib/
    utils.ts          - Utility functions (cn, formatDate, slugify)
    constants.ts      - App-wide constants
    validators.ts     - Shared Zod schemas
  hooks/              - Custom React hooks (useDebounce, useMediaQuery)
  types/              - Shared TypeScript types
public/               - Static assets (favicon, og-image)
```

## Conventions

### Frontend
- Server Components by default. Add `'use client'` only for interactivity.
- Use `next/image` for all images. No raw `<img>` tags.
- Forms use `react-hook-form` with `zodResolver` for validation.
- Loading states: use Next.js `loading.tsx` and Suspense boundaries.
- Error states: use `error.tsx` boundaries with retry buttons.
- Optimistic updates via TanStack Query `onMutate` for mutations.

### Backend
- All data access through tRPC procedures. No direct database calls in components.
- Input validation with Zod schemas at the procedure level.
- Use `protectedProcedure` for authenticated endpoints (enforces session check).
- Transactions for multi-table writes using `db.transaction()`.
- Background tasks: trigger via API route, process in Vercel Cron or Edge Functions.

### Database
- Drizzle schema as source of truth. Generate migrations with `drizzle-kit`.
- Use `serial` for internal IDs, `text` with `cuid2()` for public-facing IDs.
- All tables include `createdAt` and `updatedAt` with database defaults.
- Soft delete via `deletedAt` column for projects and tasks.
- Index foreign keys and columns used in filters.

### Testing
- 80% coverage minimum on `server/` directory.
- Unit test tRPC procedures with mocked database.
- E2E tests for: auth flow, project CRUD, board drag-and-drop, team invite.
- Visual regression tests for key UI states using Playwright screenshots.

## Environment Variables
- `DATABASE_URL` - Neon PostgreSQL connection string
- `NEXTAUTH_SECRET` - Auth session encryption key
- `NEXTAUTH_URL` - Base URL (http://localhost:3000 in dev)
- `GITHUB_CLIENT_ID` / `GITHUB_CLIENT_SECRET` - GitHub OAuth
- `GOOGLE_CLIENT_ID` / `GOOGLE_CLIENT_SECRET` - Google OAuth
- `LIVEBLOCKS_SECRET_KEY` - Real-time collaboration
- `UPLOADTHING_SECRET` - File upload service
- `RESEND_API_KEY` - Email sending
- `STRIPE_SECRET_KEY` / `STRIPE_WEBHOOK_SECRET` - Payments

## Key Decisions
| Date | Decision | Rationale |
|------|----------|-----------|
| 2025-07-01 | Drizzle over Prisma | Better SQL control, lighter runtime, edge-compatible |
| 2025-07-15 | tRPC over REST | End-to-end type safety, reduced boilerplate |
| 2025-08-01 | Liveblocks over PartyKit | Managed service, presence + storage primitives |
| 2025-09-10 | shadcn/ui over Radix directly | Pre-styled, copy-paste, full ownership |
| 2025-10-20 | Neon over Supabase | Serverless branching, Vercel integration |
