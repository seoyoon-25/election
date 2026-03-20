"""
Redis client for caching and token blacklist.

Provides async Redis client with connection pooling.
"""

from typing import Optional
import redis.asyncio as redis
from contextlib import asynccontextmanager

from app.config import settings


class RedisClient:
    """Async Redis client wrapper with connection pooling."""

    _pool: Optional[redis.ConnectionPool] = None
    _client: Optional[redis.Redis] = None

    @classmethod
    async def get_client(cls) -> redis.Redis:
        """
        Get or create Redis client with connection pool.

        Returns:
            Async Redis client instance
        """
        if cls._client is None:
            cls._pool = redis.ConnectionPool.from_url(
                str(settings.redis_url),
                encoding="utf-8",
                decode_responses=True,
            )
            cls._client = redis.Redis(connection_pool=cls._pool)
        return cls._client

    @classmethod
    async def close(cls) -> None:
        """Close Redis connection pool."""
        if cls._client:
            await cls._client.close()
            cls._client = None
        if cls._pool:
            await cls._pool.disconnect()
            cls._pool = None


async def get_redis() -> redis.Redis:
    """
    Dependency to get Redis client.

    Usage:
        @router.get("/example")
        async def example(redis: Annotated[Redis, Depends(get_redis)]):
            await redis.set("key", "value")
    """
    return await RedisClient.get_client()


@asynccontextmanager
async def redis_lifespan():
    """
    Lifespan context manager for Redis connection.

    Usage in FastAPI app:
        @asynccontextmanager
        async def lifespan(app: FastAPI):
            async with redis_lifespan():
                yield
    """
    yield
    await RedisClient.close()
