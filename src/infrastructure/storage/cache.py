"""Async caching layer for storage."""

import asyncio
import logging
import time
from typing import Any

logger = logging.getLogger(__name__)


class StorageCache:
    """Simple in-memory cache for storage operations."""

    def __init__(self, ttl: int = 300):
        """
        Initialize cache.

        Args:
            ttl: Time-to-live in seconds (default 5 minutes)
        """
        self.ttl = ttl
        self._cache: dict[str, tuple[Any, float]] = {}
        self._lock = asyncio.Lock()

    async def get(self, key: str) -> Any | None:
        """Get from cache if not expired."""
        async with self._lock:
            if key in self._cache:
                value, timestamp = self._cache[key]
                if time.time() - timestamp < self.ttl:
                    logger.debug(f"Cache hit: {key}")
                    return value
                else:
                    # Expired
                    del self._cache[key]
                    logger.debug(f"Cache expired: {key}")
        return None

    async def set(self, key: str, value: Any) -> None:
        """Set in cache with current timestamp."""
        async with self._lock:
            self._cache[key] = (value, time.time())
            logger.debug(f"Cache set: {key}")

    async def delete(self, key: str) -> None:
        """Remove from cache."""
        async with self._lock:
            if key in self._cache:
                del self._cache[key]
                logger.debug(f"Cache delete: {key}")

    async def clear(self) -> None:
        """Clear all cache."""
        async with self._lock:
            self._cache.clear()
            logger.debug("Cache cleared")

    async def cleanup_expired(self) -> None:
        """Remove expired entries."""
        async with self._lock:
            current_time = time.time()
            expired_keys = [
                key
                for key, (_, timestamp) in self._cache.items()
                if current_time - timestamp >= self.ttl
            ]
            for key in expired_keys:
                del self._cache[key]
            if expired_keys:
                logger.debug(f"Cleaned up {len(expired_keys)} expired cache entries")
