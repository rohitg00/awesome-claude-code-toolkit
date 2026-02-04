# Example: Multi-Agent Pipeline

Chain multiple Claude Code agents together to build, review, and deploy a feature.

## Architecture

```
[Planner Agent] --> [Developer Agent] --> [Reviewer Agent] --> [Deploy Agent]
      |                    |                     |                    |
  Creates plan      Implements code       Reviews changes      Deploys safely
```

Each agent runs with a specific context that constrains its behavior and focus.

## Step 1: Planner Agent

The planner breaks down a feature request into implementable tasks.

```
> /context load research
> Break down this feature request into implementation tasks:
  "Add Stripe subscription billing with usage-based pricing"
```

The planner agent outputs:
1. Database schema: `subscriptions`, `usage_records`, `invoices` tables.
2. Stripe integration: webhook handler, checkout session, customer portal.
3. Usage tracking: metered event ingestion, aggregation, billing period rollup.
4. API endpoints: subscription CRUD, usage reporting, invoice history.
5. UI: pricing page, billing settings, usage dashboard.

## Step 2: Developer Agent

The developer agent implements each task following project conventions.

```
> /context load dev
> Implement tasks 1-3 from the billing plan. Follow existing patterns in the
  codebase for the repository, service, and API layers.
```

The developer agent:
- Creates migration files for the new tables.
- Implements `SubscriptionRepository`, `UsageRepository`, `InvoiceRepository`.
- Creates `BillingService` with Stripe SDK integration.
- Adds webhook handler with signature verification.
- Writes unit tests for the service layer.
- Commits each logical unit separately with descriptive messages.

## Step 3: Reviewer Agent

The reviewer agent inspects the changes with a security and quality lens.

```
> /context load review
> Review all changes on this branch against main. Focus on security,
  error handling, and Stripe integration correctness.
```

The reviewer agent checks:
- Webhook signature verification is in place.
- Idempotency keys are used for Stripe API calls.
- Failed payment handling covers retry, grace period, and cancellation.
- No raw Stripe API keys in source code.
- Database transactions wrap multi-table writes.
- Tests cover webhook replay, duplicate events, and failed charges.

It leaves structured comments and blocks on critical issues.

## Step 4: Deploy Agent

After review approval, the deploy agent handles the release.

```
> /context load deploy
> Deploy the billing feature to staging. Run the migration and smoke test
  the webhook endpoint.
```

The deploy agent:
- Verifies CI passes on the branch.
- Applies database migrations to staging.
- Deploys the application to the staging environment.
- Sends a test webhook event and verifies the handler responds correctly.
- Monitors error rates and latency for 10 minutes.
- Reports deployment status with health check results.

## Coordination

Agents communicate through structured artifacts:
- **Plans**: Markdown task lists with acceptance criteria.
- **Code**: Git branches with atomic commits.
- **Reviews**: Structured comments with severity prefixes.
- **Deploy reports**: Status, metrics, and rollback instructions.

Each agent reads the output of the previous agent and operates within its context
boundaries. No agent modifies artifacts outside its designated scope.
