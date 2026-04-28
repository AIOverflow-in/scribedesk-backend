"""Redis Pub/Sub manager — per-user channels for real-time WebSocket events."""

import json
from datetime import datetime, timezone
from typing import Any, AsyncGenerator, Dict

from redis.asyncio import Redis

from src.core.logging import get_logger

logger = get_logger(__name__)


class PubSubManager:
    """Publish and subscribe to per-user Redis channels for WebSocket events."""

    def __init__(self, redis_client: Redis):
        self.redis = redis_client
        self.channel_prefix = "ws:user:"

    async def publish(self, user_id: str, event_type: str, data: Dict[str, Any]) -> None:
        """Publish an event to a specific user's channel."""
        channel = f"{self.channel_prefix}{user_id}"
        message = {
            "event_type": event_type,
            "data": data,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }
        await self.redis.publish(channel, json.dumps(message))
        logger.debug(f"Published event '{event_type}' to user {user_id}")

    async def subscribe(self, user_id: str) -> AsyncGenerator[Dict[str, Any], None]:
        """Subscribe to a user's channel and yield messages as they arrive."""
        channel_name = f"{self.channel_prefix}{user_id}"
        pubsub = self.redis.pubsub()
        await pubsub.subscribe(channel_name)

        logger.info(f"Subscribed to Redis channel: {channel_name}")

        try:
            async for message in pubsub.listen():
                if message["type"] == "message":
                    data = json.loads(message["data"])
                    if "event" in data and "event_type" not in data:
                        data["event_type"] = data["event"]
                        del data["event"]
                    yield data
        finally:
            try:
                await pubsub.unsubscribe(channel_name)
                await pubsub.close()
                logger.info(f"Unsubscribed from Redis channel: {channel_name}")
            except Exception as e:
                logger.debug(f"Error during pubsub cleanup (connection already closed): {e}")
