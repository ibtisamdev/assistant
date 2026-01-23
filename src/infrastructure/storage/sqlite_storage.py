"""SQLite storage backend - future implementation stub."""

import logging

from ...application.config import StorageConfig
from ...domain.models.profile import UserProfile
from ...domain.models.session import Memory

logger = logging.getLogger(__name__)


class SQLiteStorage:
    """
    SQLite storage backend - future implementation.

    Benefits over JSON:
    - Faster queries (indexed lookups)
    - Atomic transactions
    - Better for multi-user scenarios
    - Easier migration paths
    - Full-text search capabilities
    """

    def __init__(self, config: StorageConfig):
        self.config = config
        logger.info("SQLite storage not yet implemented")
        raise NotImplementedError("SQLite storage coming soon. Use 'json' backend for now.")

    async def save_session(self, session_id: str, memory: Memory) -> None:
        """Save to SQLite."""
        # TODO: INSERT OR REPLACE INTO sessions ...
        pass

    async def load_session(self, session_id: str) -> Memory | None:
        """Load from SQLite."""
        # TODO: SELECT * FROM sessions WHERE id = ?
        pass

    async def list_sessions(self) -> list[dict[str, object]]:
        """List sessions with metadata."""
        # TODO: SELECT metadata FROM sessions ORDER BY created_at DESC
        return []

    async def delete_session(self, session_id: str) -> bool:
        """Delete session."""
        # TODO: DELETE FROM sessions WHERE id = ?
        return False

    async def save_profile(self, user_id: str, profile: UserProfile) -> None:
        """Save profile."""
        # TODO: INSERT OR REPLACE INTO profiles ...
        pass

    async def load_profile(self, user_id: str) -> UserProfile | None:
        """Load profile."""
        # TODO: SELECT * FROM profiles WHERE id = ?
        pass
