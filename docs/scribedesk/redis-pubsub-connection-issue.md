# Redis Pub/Sub Connection Exhaustion — Problem & Solution

## Current Architecture

```
Browser (SSE)  →  FastAPI  →  self.redis.pubsub().subscribe("ws:user:{id}")
                              ↑ 1 dedicated TCP connection per SSE client
```

Each SSE connection calls `self.redis.pubsub().subscribe()`, which **acquires a
dedicated TCP connection from the Redis pool and holds it for the entire
lifetime of that SSE stream** (potentially hours). The connection is only
released when the client disconnects and the `finally` block runs.

## The Problem

- **Upstash Redis free tier** caps connections at ~10–30.
- Every SSE tab = 1 held Redis connection.
- When 10+ users have the SSE tab open, all connections are consumed by SSE.
- **Normal API requests** (login, page load, fetch data) need connections too
  — they're left waiting, causing `too many connections` errors.
- Unclean disconnects (browser crash, network drop) can leak connections,
  compounding the issue.

**Session Manager** (`get`/`set`/`expire`) is fine — it grabs a connection for
~5–50ms and returns it. One connection serves hundreds of requests/second.

## Why Not WebSocket?

The transport (SSE vs WebSocket) is irrelevant. Both would call
`self.redis.pubsub().subscribe()` internally, and both would hold a dedicated
Redis connection. The root cause is **per-client Redis pubsub subscriptions**,
not SSE itself.

## Solution: Single Subscriber + In-Process Fan-Out

Instead of N subscribers for N users, use **1 subscriber** that listens to
all channels via `PSUBSCRIBE "ws:user:*"` and delivers messages in-process.

```
┌─────────────────────────────────────────────┐
│  App Server                                 │
│                                              │
│  Redis ──[1 TCP conn]──► PSUBSCRIBE          │
│                           "ws:user:*"         │
│                              │                │
│                      ┌───────┴───────┐        │
│                      ▼               ▼        │
│               User 5 SSE      User 9 SSE     │
│               (in-process)    (in-process)    │
└─────────────────────────────────────────────┘
```

Redis broadcasts to all subscribers of a pattern. Each instance receives every
message and routes locally — only the instance where the user is connected
delivers it. Other instances simply see no matching subscriber and drop it.

### With multiple app instances

```
Instance A ──redis──► PSUBSCRIBE "ws:user:*"  ──fan-out──► Local clients
Instance B ──redis──► PSUBSCRIBE "ws:user:*"  ──fan-out──► Local clients
```

Works out of the box. Every instance receives every message. If user 5 is
connected to Instance A, only Instance A delivers. No extra infra needed.

## Memory & CPU — 100 Concurrent Users

| Resource | Per user | 100 users |
|---|---|---|
| `create_memory_object_stream` | 1 stream (2 ends) | 200 objects |
| Message in buffer (max 128) | ~2 KB worst case | ~256 KB total |
| Dict entry in `_subscribers` | ~200 bytes | ~20 KB |

- **RAM**: Negligible (~300 KB for 100 users). The stream buffers at most 128
  messages per user; if the client is slow, older messages are dropped instead
  of accumulating.
- **CPU**: `async for` loop is single-threaded async — it's either awaiting the
  next Redis message or awaiting `send.send()`. No polling, no busy-waiting.
- **Redis**: 1 TCP connection for all SSE users. The 30-connection free tier
  is now more than enough.

Essentially zero measurable impact at 100 concurrent users.

## Publish Side — No Change

Every existing `pubsub_manager.publish(user_id=..., event_type=..., data=...)`
call works identically. The channel format `ws:user:{user_id}` doesn't change.

## File Changes

| File | Action | Details |
|---|---|---|
| `src/infrastructure/persistence/redis/pubsub.py` | Rewrite | Replace per-connection subscribe with single PSUBSCRIBE + in-process fan-out. `publish()` stays identical. |
| `src/core/lifecycle.py` | Modify | Add `await pubsub.start()` after `init_redis()` to launch background listener. |
| `src/dependencies/infra.py` | Modify | Make `PubSubManager` a singleton (referencing the started instance) instead of creating a new one per request. |
| Everywhere else | None | All imports, type hints, and `publish()` calls remain unchanged. |

## Implementation Notes

1. **`pubsub.start()`** must be called exactly once at app startup. It runs an
   `async for` loop that lives for the app's lifetime.

2. The dependency (`get_pubsub_manager`) must return the **same** started
   instance. Easiest: store it on `app.state` during lifespan startup.

3. On shutdown, the background listener stops naturally when the Redis
   connection is closed (already handled in `close_redis()`).

4. If the listener crashes (unlikely — Redis pubsub doesn't error on
   messages), the app should log and restart it. For now, `close_redis()` on
   shutdown handles cleanup.
