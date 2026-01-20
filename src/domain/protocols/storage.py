"""Storage provider protocol."""

from typing import Protocol, Optional, List
from ..models.session import Memory
from ..models.profile import UserProfile


class StorageProvider(Protocol):
    """Protocol for storage backends - enables swappable storage."""

    async def save_session(self, session_id: str, memory: Memory) -> None:
        """Save session data."""
        ...

    async def load_session(self, session_id: str) -> Optional[Memory]:
        """Load session data."""
        ...

    async def list_sessions(self) -> List[dict]:
        """List all sessions with metadata."""
        ...

    async def delete_session(self, session_id: str) -> bool:
        """Delete a session."""
        ...

    async def save_profile(self, user_id: str, profile: UserProfile) -> None:
        """Save user profile."""
        ...

    async def load_profile(self, user_id: str) -> Optional[UserProfile]:
        """Load user profile."""
        ...
