"""Redis cache client."""

import json
from typing import Any, Optional

import redis.asyncio as redis

from evo_ai.config import settings
from evo_ai.infrastructure.observability.logging import get_logger

logger = get_logger(__name__)


class RedisCache:
    """
    Redis cache client for:
    - Round execution status (pub/sub)
    - Campaign data caching
    - Rate limiting
    - Session management
    """

    def __init__(self) -> None:
        """Initialize Redis client."""
        self.client = redis.from_url(
            settings.redis_url,
            encoding="utf-8",
            decode_responses=True
        )
        self.ttl = settings.redis_cache_ttl

    async def close(self) -> None:
        """Close Redis connection."""
        await self.client.close()

    async def get(self, key: str) -> Optional[str]:
        """
        Get value from cache.

        Args:
            key: Cache key

        Returns:
            Cached value or None if not found
        """
        try:
            value = await self.client.get(key)
            if value:
                logger.debug("cache_hit", key=key)
            else:
                logger.debug("cache_miss", key=key)
            return value
        except redis.RedisError as e:
            logger.error("cache_get_failed", key=key, error=str(e))
            return None

    async def get_json(self, key: str) -> Optional[Any]:
        """Get JSON value from cache."""
        value = await self.get(key)
        if value:
            try:
                return json.loads(value)
            except json.JSONDecodeError as e:
                logger.error("cache_json_decode_failed", key=key, error=str(e))
                return None
        return None

    async def set(
        self,
        key: str,
        value: str,
        ttl: Optional[int] = None
    ) -> bool:
        """
        Set value in cache.

        Args:
            key: Cache key
            value: Value to cache
            ttl: Time to live in seconds (uses default if not provided)

        Returns:
            True if successful
        """
        try:
            await self.client.set(
                key,
                value,
                ex=ttl or self.ttl
            )
            logger.debug("cache_set", key=key, ttl=ttl or self.ttl)
            return True
        except redis.RedisError as e:
            logger.error("cache_set_failed", key=key, error=str(e))
            return False

    async def set_json(
        self,
        key: str,
        value: Any,
        ttl: Optional[int] = None
    ) -> bool:
        """Set JSON value in cache."""
        try:
            json_value = json.dumps(value)
            return await self.set(key, json_value, ttl)
        except (TypeError, ValueError) as e:
            logger.error("cache_json_encode_failed", key=key, error=str(e))
            return False

    async def delete(self, key: str) -> bool:
        """Delete key from cache."""
        try:
            deleted = await self.client.delete(key)
            logger.debug("cache_delete", key=key, deleted=bool(deleted))
            return bool(deleted)
        except redis.RedisError as e:
            logger.error("cache_delete_failed", key=key, error=str(e))
            return False

    async def publish(self, channel: str, message: str) -> int:
        """
        Publish message to channel (for pub/sub).

        Args:
            channel: Channel name (e.g., "round:123")
            message: Message to publish (typically JSON)

        Returns:
            Number of subscribers that received the message
        """
        try:
            subscribers = await self.client.publish(channel, message)
            logger.debug("cache_publish", channel=channel, subscribers=subscribers)
            return subscribers
        except redis.RedisError as e:
            logger.error("cache_publish_failed", channel=channel, error=str(e))
            return 0

    async def publish_json(self, channel: str, data: Any) -> int:
        """Publish JSON data to channel."""
        try:
            message = json.dumps(data)
            return await self.publish(channel, message)
        except (TypeError, ValueError) as e:
            logger.error("cache_publish_json_failed", channel=channel, error=str(e))
            return 0

    async def subscribe(self, channel: str):
        """
        Subscribe to channel (async generator).

        Args:
            channel: Channel name

        Yields:
            Messages published to the channel

        Example:
            async for message in redis_cache.subscribe("round:123"):
                print(message)
        """
        pubsub = self.client.pubsub()
        await pubsub.subscribe(channel)

        try:
            async for message in pubsub.listen():
                if message['type'] == 'message':
                    yield message['data']
        finally:
            await pubsub.unsubscribe(channel)
            await pubsub.close()
