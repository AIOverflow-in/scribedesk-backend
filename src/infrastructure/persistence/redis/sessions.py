import json
import uuid
from typing import Optional, Dict, Any
from redis.asyncio import Redis

class SessionManager:
    def __init__(self, redis_client: Redis):
        self.redis = redis_client
        self.prefix = "session:"
        self.ttl = 86400  

    async def create_session(
        self, 
        token: str, 
        user_id: uuid.UUID, 
        role: str
    ) -> None:
        """Stores session data in Redis with a 24h expiry."""
        key = f"{self.prefix}{token}"
        data = {
            "user_id": str(user_id),
            "role": role
        }
        await self.redis.set(key, json.dumps(data), ex=self.ttl)

    async def get_session(self, token: str) -> Optional[Dict[str, Any]]:
        """
        Retrieves session data and refreshes the TTL (Sliding Window).
        Returns None if session is expired or invalid.
        """
        key = f"{self.prefix}{token}"
        data = await self.redis.get(key)
        
        if not data:
            return None

        # Refresh the 24h timer every time the session is used
        await self.redis.expire(key, self.ttl)
        return json.loads(data)

    async def delete_session(self, token: str) -> None:
        """Removes the session from Redis (Logout)."""
        await self.redis.delete(f"{self.prefix}{token}")