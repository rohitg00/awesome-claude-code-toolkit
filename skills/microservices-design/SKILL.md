---
name: microservices-design
description: Microservices design patterns including service mesh, event-driven architecture, saga pattern, and API gateway
---

# Microservices Design

## Service Boundaries

Define services around business capabilities, not technical layers. Each service owns its data store and exposes a clear API contract.

```
order-service/       -> owns orders table, publishes OrderCreated events
inventory-service/   -> owns inventory table, subscribes to OrderCreated
payment-service/     -> owns payments table, handles payment processing
notification-service -> stateless, subscribes to events, sends emails/SMS
```

## Event-Driven Communication

```typescript
interface DomainEvent {
  eventId: string;
  eventType: string;
  aggregateId: string;
  timestamp: string;
  version: number;
  payload: Record<string, unknown>;
}

const orderCreatedEvent: DomainEvent = {
  eventId: crypto.randomUUID(),
  eventType: "order.created",
  aggregateId: orderId,
  timestamp: new Date().toISOString(),
  version: 1,
  payload: { customerId, items, totalAmount },
};

await broker.publish("orders", orderCreatedEvent);
```

```typescript
async function handleOrderCreated(event: DomainEvent) {
  const { items } = event.payload as OrderPayload;

  for (const item of items) {
    await db.inventory.update({
      where: { productId: item.productId },
      data: { quantity: { decrement: item.quantity } },
    });
  }

  await markEventProcessed(event.eventId);
}
```

Use idempotency keys (`eventId`) to handle duplicate deliveries safely.

## Saga Pattern (Orchestration)

```typescript
class OrderSaga {
  private steps: SagaStep[] = [
    {
      name: "reserveInventory",
      execute: (ctx) => inventoryService.reserve(ctx.items),
      compensate: (ctx) => inventoryService.release(ctx.items),
    },
    {
      name: "processPayment",
      execute: (ctx) => paymentService.charge(ctx.customerId, ctx.amount),
      compensate: (ctx) => paymentService.refund(ctx.paymentId),
    },
    {
      name: "confirmOrder",
      execute: (ctx) => orderService.confirm(ctx.orderId),
      compensate: (ctx) => orderService.cancel(ctx.orderId),
    },
  ];

  async run(context: SagaContext): Promise<void> {
    const completed: SagaStep[] = [];

    for (const step of this.steps) {
      try {
        const result = await step.execute(context);
        Object.assign(context, result);
        completed.push(step);
      } catch (error) {
        for (const s of completed.reverse()) {
          await s.compensate(context);
        }
        throw new SagaFailedError(step.name, error);
      }
    }
  }
}
```

## API Gateway Pattern

```yaml
# Kong or similar gateway config
services:
  - name: orders
    url: http://order-service:3000
    routes:
      - paths: ["/api/v1/orders"]
        methods: [GET, POST]
    plugins:
      - name: rate-limiting
        config:
          minute: 100
      - name: jwt
      - name: correlation-id

  - name: users
    url: http://user-service:3000
    routes:
      - paths: ["/api/v1/users"]
    plugins:
      - name: rate-limiting
        config:
          minute: 200
```

## Health Check Pattern

```typescript
app.get("/health", async (req, res) => {
  const checks = {
    database: await checkDatabase(),
    cache: await checkRedis(),
    broker: await checkMessageBroker(),
  };

  const healthy = Object.values(checks).every(c => c.status === "up");

  res.status(healthy ? 200 : 503).json({
    status: healthy ? "healthy" : "degraded",
    checks,
    version: process.env.APP_VERSION,
    uptime: process.uptime(),
  });
});
```

## Anti-Patterns

- Sharing a database between services (tight coupling)
- Synchronous HTTP chains across multiple services (cascading failures)
- Building a distributed monolith (services cannot deploy independently)
- Missing circuit breakers on inter-service calls
- Not implementing idempotency for event handlers
- Using distributed transactions instead of sagas

## Checklist

- [ ] Each service owns its own data store
- [ ] Services communicate via events for async workflows
- [ ] Saga pattern used for multi-service transactions with compensation
- [ ] Circuit breakers protect against cascading failures
- [ ] API gateway handles routing, rate limiting, and authentication
- [ ] Health check endpoints report dependency status
- [ ] Event handlers are idempotent (safe to process duplicates)
- [ ] Services can be deployed and scaled independently
