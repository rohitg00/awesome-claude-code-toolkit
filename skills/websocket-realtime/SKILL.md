---
name: websocket-realtime
description: Real-time communication patterns with WebSocket, Socket.io, Server-Sent Events, and scaling strategies
---

# WebSocket & Real-Time

## WebSocket Server

```typescript
import { WebSocketServer, WebSocket } from "ws";

const wss = new WebSocketServer({ port: 8080 });

const rooms = new Map<string, Set<WebSocket>>();

wss.on("connection", (ws, req) => {
  const userId = authenticateFromUrl(req.url);
  if (!userId) {
    ws.close(4001, "Unauthorized");
    return;
  }

  ws.on("message", (data) => {
    const message = JSON.parse(data.toString());

    switch (message.type) {
      case "join":
        joinRoom(message.room, ws);
        break;
      case "leave":
        leaveRoom(message.room, ws);
        break;
      case "broadcast":
        broadcastToRoom(message.room, message.payload, ws);
        break;
    }
  });

  ws.on("close", () => {
    rooms.forEach((members) => members.delete(ws));
  });

  ws.send(JSON.stringify({ type: "connected", userId }));
});

function joinRoom(room: string, ws: WebSocket) {
  if (!rooms.has(room)) rooms.set(room, new Set());
  rooms.get(room)!.add(ws);
}

function broadcastToRoom(room: string, payload: unknown, sender: WebSocket) {
  const members = rooms.get(room);
  if (!members) return;
  const message = JSON.stringify({ type: "message", room, payload });
  members.forEach((client) => {
    if (client !== sender && client.readyState === WebSocket.OPEN) {
      client.send(message);
    }
  });
}
```

## Socket.io with Rooms

```typescript
import { Server } from "socket.io";
import { createAdapter } from "@socket.io/redis-adapter";
import { createClient } from "redis";

const io = new Server(httpServer, {
  cors: { origin: "https://app.example.com" },
  pingTimeout: 20000,
  pingInterval: 25000,
});

const pubClient = createClient({ url: "redis://localhost:6379" });
const subClient = pubClient.duplicate();
await Promise.all([pubClient.connect(), subClient.connect()]);
io.adapter(createAdapter(pubClient, subClient));

io.use(async (socket, next) => {
  const token = socket.handshake.auth.token;
  try {
    socket.data.user = verifyToken(token);
    next();
  } catch {
    next(new Error("Authentication failed"));
  }
});

io.on("connection", (socket) => {
  socket.join(`user:${socket.data.user.id}`);

  socket.on("chat:join", (roomId) => {
    socket.join(`chat:${roomId}`);
    socket.to(`chat:${roomId}`).emit("chat:userJoined", socket.data.user);
  });

  socket.on("chat:message", async ({ roomId, text }) => {
    const message = await saveMessage(roomId, socket.data.user.id, text);
    io.to(`chat:${roomId}`).emit("chat:message", message);
  });

  socket.on("disconnect", () => {
    console.log(`User ${socket.data.user.id} disconnected`);
  });
});
```

## Server-Sent Events (SSE)

```typescript
app.get("/events/:userId", authenticate, (req, res) => {
  res.writeHead(200, {
    "Content-Type": "text/event-stream",
    "Cache-Control": "no-cache",
    Connection: "keep-alive",
  });

  const sendEvent = (event: string, data: unknown) => {
    res.write(`event: ${event}\n`);
    res.write(`data: ${JSON.stringify(data)}\n\n`);
  };

  sendEvent("connected", { userId: req.params.userId });

  const interval = setInterval(() => {
    res.write(":heartbeat\n\n");
  }, 30000);

  const listener = (message: string) => {
    const event = JSON.parse(message);
    sendEvent(event.type, event.data);
  };

  redis.subscribe(`user:${req.params.userId}`, listener);

  req.on("close", () => {
    clearInterval(interval);
    redis.unsubscribe(`user:${req.params.userId}`, listener);
  });
});
```

SSE is simpler than WebSocket for server-to-client unidirectional streaming. Works through HTTP proxies and load balancers without special configuration.

## Client Reconnection

```typescript
class ReconnectingWebSocket {
  private ws: WebSocket | null = null;
  private retryCount = 0;
  private maxRetries = 10;

  constructor(private url: string) {
    this.connect();
  }

  private connect() {
    this.ws = new WebSocket(this.url);
    this.ws.onopen = () => { this.retryCount = 0; };
    this.ws.onclose = () => { this.scheduleReconnect(); };
    this.ws.onerror = () => { this.ws?.close(); };
  }

  private scheduleReconnect() {
    if (this.retryCount >= this.maxRetries) return;
    const delay = Math.min(1000 * 2 ** this.retryCount, 30000);
    this.retryCount++;
    setTimeout(() => this.connect(), delay);
  }

  send(data: string) {
    if (this.ws?.readyState === WebSocket.OPEN) {
      this.ws.send(data);
    }
  }
}
```

## Anti-Patterns

- Not authenticating WebSocket connections during the handshake
- Sending unbounded payloads without message size limits
- Missing heartbeat/ping-pong to detect stale connections
- Using WebSocket when SSE would suffice (server-to-client only)
- Not using a Redis adapter for horizontal scaling with Socket.io
- Blocking the event loop with synchronous processing of messages

## Checklist

- [ ] WebSocket connections authenticated during handshake
- [ ] Message size limits enforced on incoming data
- [ ] Heartbeat mechanism detects and closes stale connections
- [ ] Client implements exponential backoff reconnection
- [ ] Redis pub/sub adapter used for multi-server deployment
- [ ] SSE used when communication is server-to-client only
- [ ] Room/channel membership cleaned up on disconnect
- [ ] Rate limiting applied to prevent message flooding
