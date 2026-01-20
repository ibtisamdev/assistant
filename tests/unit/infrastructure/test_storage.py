"""Tests for storage."""

import pytest
from tests.fixtures.factories import MemoryFactory
from tests.fixtures.mocks import MockStorage


@pytest.mark.asyncio
class TestMockStorage:
    async def test_save_and_load_session(self):
        storage = MockStorage()
        memory = MemoryFactory.create(session_id="2026-01-20")

        await storage.save_session("2026-01-20", memory)
        loaded = await storage.load_session("2026-01-20")

        assert loaded is not None
        assert loaded.metadata.session_id == "2026-01-20"

    async def test_load_nonexistent_session_returns_none(self):
        storage = MockStorage()
        loaded = await storage.load_session("nonexistent")
        assert loaded is None

    async def test_list_sessions(self):
        storage = MockStorage()

        mem1 = MemoryFactory.create(session_id="2026-01-20")
        mem2 = MemoryFactory.create(session_id="2026-01-21")

        await storage.save_session("2026-01-20", mem1)
        await storage.save_session("2026-01-21", mem2)

        sessions = await storage.list_sessions()
        assert len(sessions) == 2

    async def test_delete_session(self):
        storage = MockStorage()
        memory = MemoryFactory.create(session_id="2026-01-20")

        await storage.save_session("2026-01-20", memory)
        success = await storage.delete_session("2026-01-20")

        assert success
        loaded = await storage.load_session("2026-01-20")
        assert loaded is None
