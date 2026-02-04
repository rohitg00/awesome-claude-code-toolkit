---
name: testing-strategies
description: Testing strategies including contract testing, snapshot testing, mutation testing, property-based testing, and test organization
---

# Testing Strategies

## Test Structure (Arrange-Act-Assert)

```typescript
describe("OrderService", () => {
  describe("createOrder", () => {
    it("creates an order with valid items and returns order ID", async () => {
      const repo = new InMemoryOrderRepository();
      const service = new OrderService(repo);
      const input = { customerId: "c1", items: [{ productId: "p1", quantity: 2 }] };

      const result = await service.createOrder(input);

      expect(result.id).toBeDefined();
      expect(result.status).toBe("pending");
      expect(result.items).toHaveLength(1);
      const saved = await repo.findById(result.id);
      expect(saved).toEqual(result);
    });

    it("rejects order with empty items", async () => {
      const service = new OrderService(new InMemoryOrderRepository());

      await expect(
        service.createOrder({ customerId: "c1", items: [] })
      ).rejects.toThrow("Order must have at least one item");
    });
  });
});
```

Name tests by behavior, not method name. Each test should be independent and self-contained.

## Contract Testing (Pact)

```typescript
import { PactV4 } from "@pact-foundation/pact";

const provider = new PactV4({
  consumer: "OrderService",
  provider: "UserService",
});

describe("UserService contract", () => {
  it("returns user by ID", async () => {
    await provider
      .addInteraction()
      .given("user with id user-1 exists")
      .uponReceiving("a request for user user-1")
      .withRequest("GET", "/api/users/user-1")
      .willRespondWith(200, (builder) => {
        builder.jsonBody({
          id: "user-1",
          name: "Alice",
          email: "alice@example.com",
        });
      })
      .executeTest(async (mockServer) => {
        const client = new UserClient(mockServer.url);
        const user = await client.getUser("user-1");
        expect(user.name).toBe("Alice");
      });
  });
});
```

Contract tests verify that consumer expectations match provider capabilities without requiring both services to be running.

## Snapshot Testing

```typescript
import { render } from "@testing-library/react";

it("renders the user profile card", () => {
  const { container } = render(
    <UserCard user={{ name: "Alice", email: "alice@example.com", role: "admin" }} />
  );

  expect(container).toMatchSnapshot();
});

it("renders the order summary with inline snapshot", () => {
  const summary = formatOrderSummary(mockOrder);

  expect(summary).toMatchInlineSnapshot(`
    "Order #123
    Items: 3
    Total: $45.99
    Status: Pending"
  `);
});
```

Use inline snapshots for small outputs. Review snapshot diffs carefully during code review.

## Property-Based Testing

```typescript
import fc from "fast-check";

describe("sortUsers", () => {
  it("always returns the same number of elements", () => {
    fc.assert(
      fc.property(
        fc.array(fc.record({ name: fc.string(), age: fc.nat(120) })),
        (users) => {
          const sorted = sortUsers(users, "name");
          return sorted.length === users.length;
        }
      )
    );
  });

  it("produces a sorted result for any input", () => {
    fc.assert(
      fc.property(
        fc.array(fc.record({ name: fc.string(), age: fc.nat(120) })),
        (users) => {
          const sorted = sortUsers(users, "age");
          for (let i = 1; i < sorted.length; i++) {
            if (sorted[i].age < sorted[i - 1].age) return false;
          }
          return true;
        }
      )
    );
  });
});
```

## Integration Test with Test Containers

```typescript
import { PostgreSqlContainer } from "@testcontainers/postgresql";

let container: any;
let db: Database;

beforeAll(async () => {
  container = await new PostgreSqlContainer("postgres:16").start();
  db = await createDatabase(container.getConnectionUri());
  await db.migrate();
}, 60000);

afterAll(async () => {
  await db.close();
  await container.stop();
});

it("creates and retrieves a user", async () => {
  const user = await db.user.create({ name: "Alice", email: "alice@test.com" });
  const found = await db.user.findById(user.id);
  expect(found).toEqual(user);
});
```

## Test Doubles

```typescript
function createMockEmailService(): EmailService {
  const sent: Array<{ to: string; subject: string }> = [];
  return {
    send: async (to, subject, body) => { sent.push({ to, subject }); },
    getSent: () => sent,
  };
}

const emailService = createMockEmailService();
const service = new NotificationService(emailService);
await service.notifyUser("user-1", "Welcome");
expect(emailService.getSent()).toHaveLength(1);
expect(emailService.getSent()[0].subject).toBe("Welcome");
```

## Anti-Patterns

- Testing implementation details instead of behavior
- Sharing mutable state between tests (no `beforeEach` reset)
- Writing tests that depend on execution order
- Mocking everything instead of using real dependencies for integration tests
- Ignoring flaky tests instead of fixing the root cause
- Testing trivial getters/setters while missing edge cases

## Checklist

- [ ] Tests organized by behavior, not by method or file
- [ ] Each test follows Arrange-Act-Assert structure
- [ ] Contract tests verify inter-service API compatibility
- [ ] Snapshot tests reviewed during code review (not blindly updated)
- [ ] Property-based tests cover invariants for algorithmic code
- [ ] Integration tests use test containers for real dependencies
- [ ] Test doubles are minimal and behavior-focused
- [ ] CI fails on flaky test detection
