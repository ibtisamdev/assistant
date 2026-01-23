"""Tests for StorageCache - async in-memory cache."""

import asyncio

import pytest

from src.infrastructure.storage.cache import StorageCache


class TestStorageCacheBasics:
    """Basic cache operations tests."""

    @pytest.fixture
    def cache(self):
        """Create a cache with 1 second TTL for fast tests."""
        return StorageCache(ttl=1)

    @pytest.mark.asyncio
    async def test_get_nonexistent_key(self, cache):
        """Test getting a key that doesn't exist."""
        result = await cache.get("nonexistent")

        assert result is None

    @pytest.mark.asyncio
    async def test_set_and_get(self, cache):
        """Test setting and getting a value."""
        await cache.set("key1", "value1")

        result = await cache.get("key1")

        assert result == "value1"

    @pytest.mark.asyncio
    async def test_set_overwrites_existing(self, cache):
        """Test that set overwrites existing value."""
        await cache.set("key1", "value1")
        await cache.set("key1", "value2")

        result = await cache.get("key1")

        assert result == "value2"

    @pytest.mark.asyncio
    async def test_set_and_get_complex_object(self, cache):
        """Test caching complex objects."""
        data = {"name": "test", "items": [1, 2, 3], "nested": {"a": 1}}

        await cache.set("complex", data)
        result = await cache.get("complex")

        assert result == data

    @pytest.mark.asyncio
    async def test_delete_key(self, cache):
        """Test deleting a key."""
        await cache.set("key1", "value1")

        await cache.delete("key1")

        assert await cache.get("key1") is None

    @pytest.mark.asyncio
    async def test_delete_nonexistent_key(self, cache):
        """Test deleting a key that doesn't exist (should not raise)."""
        await cache.delete("nonexistent")  # Should not raise

    @pytest.mark.asyncio
    async def test_clear(self, cache):
        """Test clearing all cache."""
        await cache.set("key1", "value1")
        await cache.set("key2", "value2")

        await cache.clear()

        assert await cache.get("key1") is None
        assert await cache.get("key2") is None


class TestStorageCacheTTL:
    """Tests for TTL (time-to-live) behavior."""

    @pytest.mark.asyncio
    async def test_expired_key_returns_none(self):
        """Test that expired keys return None."""
        cache = StorageCache(ttl=0.1)  # 100ms TTL

        await cache.set("key1", "value1")

        # Wait for expiration
        await asyncio.sleep(0.2)

        result = await cache.get("key1")
        assert result is None

    @pytest.mark.asyncio
    async def test_non_expired_key_returns_value(self):
        """Test that non-expired keys return their value."""
        cache = StorageCache(ttl=10)  # 10 second TTL

        await cache.set("key1", "value1")

        # Don't wait
        result = await cache.get("key1")
        assert result == "value1"

    @pytest.mark.asyncio
    async def test_cleanup_expired(self):
        """Test cleanup_expired removes expired entries."""
        cache = StorageCache(ttl=0.1)

        await cache.set("key1", "value1")
        await cache.set("key2", "value2")

        # Wait for expiration
        await asyncio.sleep(0.2)

        # Add a new key that won't be expired
        await cache.set("key3", "value3")

        await cache.cleanup_expired()

        # Expired keys should be gone
        assert await cache.get("key1") is None
        assert await cache.get("key2") is None

        # New key should still exist
        assert await cache.get("key3") == "value3"


class TestStorageCacheConcurrency:
    """Tests for concurrent access."""

    @pytest.mark.asyncio
    async def test_concurrent_reads(self):
        """Test concurrent reads don't cause issues."""
        cache = StorageCache(ttl=10)
        await cache.set("key1", "value1")

        async def read_key():
            return await cache.get("key1")

        # Run many concurrent reads
        tasks = [read_key() for _ in range(100)]
        results = await asyncio.gather(*tasks)

        # All should return the same value
        assert all(r == "value1" for r in results)

    @pytest.mark.asyncio
    async def test_concurrent_writes(self):
        """Test concurrent writes don't cause issues."""
        cache = StorageCache(ttl=10)

        async def write_key(i):
            await cache.set(f"key{i}", f"value{i}")

        # Run many concurrent writes
        tasks = [write_key(i) for i in range(100)]
        await asyncio.gather(*tasks)

        # All keys should be written
        for i in range(100):
            result = await cache.get(f"key{i}")
            assert result == f"value{i}"

    @pytest.mark.asyncio
    async def test_concurrent_read_write(self):
        """Test concurrent reads and writes."""
        cache = StorageCache(ttl=10)

        async def read_write(i):
            await cache.set(f"key{i}", f"value{i}")
            return await cache.get(f"key{i}")

        tasks = [read_write(i) for i in range(50)]
        results = await asyncio.gather(*tasks)

        # All should succeed
        for i, result in enumerate(results):
            assert result == f"value{i}"


class TestStorageCacheDefaultTTL:
    """Tests for default TTL configuration."""

    def test_default_ttl(self):
        """Test default TTL is 5 minutes (300 seconds)."""
        cache = StorageCache()

        assert cache.ttl == 300

    def test_custom_ttl(self):
        """Test custom TTL is respected."""
        cache = StorageCache(ttl=600)

        assert cache.ttl == 600
