"""In-process message fan-out backed by a single Redis pubsub connection."""

import asyncio
import json
from collections import defaultdict
from datetime import datetime, timezone
from typing import Any, AsyncGenerator, Dict

import anyio
from anyio import WouldBlock, create_memory_object_stream
from redis.asyncio import Redis

from src.core.logging import get_logger

logger = get_logger(__name__)

# All user event channels follow this pattern, e.g. ws:user:a1b2c3d4
CHANNEL_PATTERN = "ws:user:*"

# Events are dropped (not backpressured) when a client's buffer reaches this limit
MAX_STREAM_BUFFER = 128


class PubSubManager:
    """Background Redis PSUBSCRIBE listener with in-process fan-out to SSE clients.

    Usage:
        manager = PubSubManager(redis_client)
        await manager.start()

        # In an SSE endpoint:
        async for event in manager.subscribe(user_id):
            yield f"data: {json.dumps(event)}\n\\n"

        # To publish:
        await manager.publish(user_id, "event_type", {"key": "value"})
    """

    def __init__(self, redis_client: Redis):
        self.redis = redis_client
        # {user_id: [anyio.ObjectSendStream, ...]}
        self._subscribers: dict[str, list] = defaultdict(list)
        self._stop_event: anyio.Event | None = None
        self._background_task: asyncio.Task | None = None

    # --- Lifecycle ---

    async def start(self) -> None:
        """Launch the background PSUBSCRIBE listener. Call once during app startup."""
        self._stop_event = anyio.Event()
        self._background_task = asyncio.create_task(self._run_listener_loop())
        logger.info("PubSubManager: background listener started")

    async def stop(self) -> None:
        """Signal shutdown and wait for the background listener to finish."""
        if self._stop_event:
            self._stop_event.set()
        if self._background_task is not None:
            self._background_task.cancel()
            try:
                await self._background_task
            except asyncio.CancelledError:
                pass

    # --- Publish (sends to Redis) ---

    async def publish(self, user_id: str, event_type: str, data: Dict[str, Any]) -> None:
        """Publish an event to a user's Redis channel."""
        channel = f"ws:user:{user_id}"
        message = {
            "event_type": event_type,
            "data": data,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }
        await self.redis.publish(channel, json.dumps(message))
        logger.debug("Published event '%s' to user %s", event_type, user_id)

    # --- Subscribe (creates a local in-process stream) ---

    def subscribe(self, user_id: str) -> AsyncGenerator[Dict[str, Any], None]:
        """Return an async generator that yields events for *user_id*.

        This does NOT create any Redis connection — messages arrive via
        the shared background listener and are pushed into an in-process
        anyio memory object stream.
        """
        send_stream, receive_stream = create_memory_object_stream[Dict[str, Any]](
            max_buffer_size=MAX_STREAM_BUFFER
        )
        self._subscribers[user_id].append(send_stream)

        async def _event_stream():
            try:
                async for message in receive_stream:
                    yield message
            finally:
                self._subscribers[user_id].remove(send_stream)
                if not self._subscribers[user_id]:
                    del self._subscribers[user_id]
                await send_stream.aclose()
                await receive_stream.aclose()

        return _event_stream()

    # --- Internal: background listener ---

    async def _run_listener_loop(self) -> None:
        """Continuously listen on the Redis pubsub channel, reconnecting on failure."""
        while not self._stop_event.is_set():
            try:
                await self._subscribe_and_route()
            except Exception:
                logger.exception("Redis pubsub connection lost — reconnecting in 3s")
                try:
                    await anyio.sleep(3)
                except asyncio.CancelledError:
                    break

    async def _subscribe_and_route(self) -> None:
        """Subscribe to the global channel pattern and route messages until broken."""
        pubsub = self.redis.pubsub()
        try:
            await pubsub.psubscribe(CHANNEL_PATTERN)
            logger.info("PubSubManager: subscribed to %s", CHANNEL_PATTERN)

            async for raw_message in pubsub.listen():
                if self._stop_event.is_set():
                    break

                if raw_message["type"] == "pmessage":
                    await self._deliver_to_subscribers(raw_message)
        finally:
            try:
                await pubsub.close()
            except Exception:
                pass

    async def _deliver_to_subscribers(self, raw_message: dict) -> None:
        """Parse a Redis pubsub message and push it to all local SSE streams for that user."""
        user_id = raw_message["channel"].split(":")[-1]

        try:
            payload = json.loads(raw_message["data"])
        except json.JSONDecodeError:
            return

        # Iterate over a copy because subscribers may be removed concurrently
        for send_stream in list(self._subscribers.get(user_id, [])):
            try:
                send_stream.send_nowait(payload)
            except WouldBlock:
                logger.warning(
                    "Event dropped for user %s — client buffer is full", user_id
                )
            except anyio.ClosedResourceError:
                pass
