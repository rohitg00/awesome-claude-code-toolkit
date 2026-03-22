---
name: redis-patterns
description: Redis patterns including caching strategies, pub/sub, streams for event processing, Lua scripts, and data structures
---

# Redis Patterns

## Caching Strategies

```typescript
async function getUser(userId: string): Promise<User> {
  const cacheKey = `user:${userId}`;
  const cached = await redis.get(cacheKey);

  if (cached) {
    return JSON.parse(cached);
  }

  const user = await db.user.findUnique({ where: { id: userId } });
  if (user) {
    await redis.set(cacheKey, JSON.stringify(user), "EX", 3600);
  }

  return user;
}

async function invalidateUser(userId: string): Promise<void> {
  await redis.del(`user:${userId}`);
  await redis.del(`user:${userId}:orders`);
}

async function cacheAside<T>(
  key: string,
  ttlSeconds: number,
  fetcher: () => Promise<T>
): Promise<T> {
  const cached = await redis.get(key);
  if (cached) return JSON.parse(cached);

  const value = await fetcher();
  await redis.set(key, JSON.stringify(value), "EX", ttlSeconds);
  return value;
}
```

## Rate Limiting with Sliding Window

```typescript
async function isRateLimited(
  clientId: string,
  limit: number,
  windowSeconds: number
): Promise<boolean> {
  const key = `ratelimit:${clientId}`;
  const now = Date.now();
  const windowStart = now - windowSeconds * 1000;

  const pipe = redis.multi();
  pipe.zremrangebyscore(key, 0, windowStart);
  pipe.zadd(key, now, `${now}:${crypto.randomUUID()}`);
  pipe.zcard(key);
  pipe.expire(key, windowSeconds);

  const results = await pipe.exec();
  const count = results[2][1] as number;
  return count > limit;
}
```

## Pub/Sub

```typescript
const subscriber = redis.duplicate();
await subscriber.subscribe("notifications", "orders");

subscriber.on("message", (channel, message) => {
  const event = JSON.parse(message);
  switch (channel) {
    case "notifications":
      handleNotification(event);
      break;
    case "orders":
      handleOrderEvent(event);
      break;
  }
});

async function publishEvent(channel: string, event: object): Promise<void> {
  await redis.publish(channel, JSON.stringify(event));
}
```

## Streams for Event Processing

```typescript
async function produceEvent(stream: string, event: Record<string, string>) {
  await redis.xadd(stream, "*", ...Object.entries(event).flat());
}

async function consumeEvents(
  stream: string,
  group: string,
  consumer: string
) {
  try {
    await redis.xgroup("CREATE", stream, group, "0", "MKSTREAM");
  } catch {
    // group already exists
  }

  while (true) {
    const results = await redis.xreadgroup(
      "GROUP", group, consumer,
      "COUNT", 10,
      "BLOCK", 5000,
      "STREAMS", stream, ">"
    );

    if (!results) continue;

    for (const [, messages] of results) {
      for (const [id, fields] of messages) {
        await processMessage(fields);
        await redis.xack(stream, group, id);
      }
    }
  }
}
```

Streams provide durable, consumer-group-based event processing with acknowledgment and replay.

## Lua Script for Atomic Operations

```typescript
const acquireLock = `
  local key = KEYS[1]
  local token = ARGV[1]
  local ttl = ARGV[2]
  if redis.call("SET", key, token, "NX", "EX", ttl) then
    return 1
  end
  return 0
`;

const releaseLock = `
  local key = KEYS[1]
  local token = ARGV[1]
  if redis.call("GET", key) == token then
    return redis.call("DEL", key)
  end
  return 0
`;

async function withLock<T>(
  resource: string,
  ttl: number,
  fn: () => Promise<T>
): Promise<T> {
  const token = crypto.randomUUID();
  const acquired = await redis.eval(acquireLock, 1, `lock:${resource}`, token, ttl);
  if (!acquired) throw new Error("Failed to acquire lock");
  try {
    return await fn();
  } finally {
    await redis.eval(releaseLock, 1, `lock:${resource}`, token);
  }
}
```

## Anti-Patterns

- Storing large objects (>100KB) in Redis without compression
- Using `KEYS *` in production (blocks the server; use `SCAN` instead)
- Not setting TTL on cache entries (memory grows unbounded)
- Using pub/sub for durable messaging (messages are lost if no subscriber is connected)
- Relying on Redis as the sole data store without persistence strategy
- Not using pipelines for multiple sequential commands

## Checklist

- [ ] Cache keys follow a consistent naming convention (`entity:id:field`)
- [ ] All cache entries have a TTL to prevent memory leaks
- [ ] `SCAN` used instead of `KEYS` for pattern matching in production
- [ ] Lua scripts used for operations requiring atomicity
- [ ] Streams used instead of pub/sub when durability is needed
- [ ] Connection pooling configured for high-throughput applications
- [ ] Rate limiting uses sliding window with sorted sets
- [ ] Distributed locks include fencing tokens and TTL
