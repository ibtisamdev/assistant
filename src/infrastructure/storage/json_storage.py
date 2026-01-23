"""Async JSON file storage - optimized for DB migration."""

import asyncio
import json
import logging
from pathlib import Path

import aiofiles

from ...application.config import StorageConfig
from ...domain.exceptions import StorageError
from ...domain.models.profile import UserProfile
from ...domain.models.session import Memory
from ...domain.models.template import DayTemplate, TemplateMetadata

logger = logging.getLogger(__name__)


class JSONStorage:
    """Async JSON file storage."""

    def __init__(self, config: StorageConfig):
        self.config = config
        self.sessions_dir = config.sessions_dir
        self.profiles_dir = config.profiles_dir
        self.templates_dir = config.templates_dir

        # Ensure directories exist (parents=True for fresh installs without setup)
        self.sessions_dir.mkdir(parents=True, exist_ok=True)
        self.profiles_dir.mkdir(parents=True, exist_ok=True)
        self.templates_dir.mkdir(parents=True, exist_ok=True)

        logger.info(f"JSON storage initialized: {self.sessions_dir}")

    async def save_session(self, session_id: str, memory: Memory) -> None:
        """Atomic async save."""
        path = self.sessions_dir / f"{session_id}.json"
        temp_path = path.with_suffix(".tmp")

        try:
            # Serialize
            data = memory.model_dump(mode="json")
            json_str = json.dumps(data, indent=2)

            # Write atomically
            async with aiofiles.open(temp_path, "w") as f:
                await f.write(json_str)

            # Atomic rename
            await asyncio.to_thread(temp_path.replace, path)
            logger.debug(f"Saved session {session_id}")

        except Exception as e:
            logger.error(f"Failed to save session {session_id}: {e}")
            if temp_path.exists():
                try:
                    await asyncio.to_thread(temp_path.unlink)
                except Exception:
                    pass
            raise StorageError(f"Failed to save session: {e}") from e

    async def load_session(self, session_id: str) -> Memory | None:
        """Load with corruption recovery."""
        path = self.sessions_dir / f"{session_id}.json"

        if not path.exists():
            return None

        try:
            async with aiofiles.open(path) as f:
                content = await f.read()

            data = json.loads(content)
            memory = Memory.model_validate(data)

            # Validate and fix timestamps if needed
            if not memory.validate_timestamps():
                logger.info(f"Fixed corrupted timestamps in session {session_id}")
                await self.save_session(session_id, memory)

            logger.debug(f"Loaded session {session_id}")
            return memory

        except json.JSONDecodeError as e:
            logger.error(f"Corrupted session {session_id}: {e}")
            await self._handle_corrupted_session(session_id, path)
            return None
        except Exception as e:
            logger.error(f"Failed to load session {session_id}: {e}")
            return None

    async def list_sessions(self) -> list[dict]:
        """List all sessions (metadata only for performance)."""
        sessions = []

        for path in self.sessions_dir.glob("*.json"):
            if path.stem.endswith(".corrupted") or path.suffix == ".tmp":
                continue

            try:
                # Only read metadata for listing (not full session)
                async with aiofiles.open(path) as f:
                    content = await f.read()
                data = json.loads(content)

                sessions.append(
                    {
                        "session_id": data["metadata"]["session_id"],
                        "created_at": data["metadata"]["created_at"],
                        "last_updated": data["metadata"]["last_updated"],
                        "state": data["agent_state"]["state"],
                        "has_plan": data["agent_state"]["plan"] is not None,
                    }
                )
            except Exception as e:
                logger.error(f"Failed to read session metadata from {path}: {e}")

        sessions.sort(key=lambda x: x["session_id"], reverse=True)
        return sessions

    async def delete_session(self, session_id: str) -> bool:
        """Delete session file."""
        path = self.sessions_dir / f"{session_id}.json"
        if path.exists():
            try:
                await asyncio.to_thread(path.unlink)
                logger.info(f"Deleted session {session_id}")
                return True
            except Exception as e:
                logger.error(f"Failed to delete session {session_id}: {e}")
                return False
        return False

    async def save_profile(self, user_id: str, profile: UserProfile) -> None:
        """Save user profile."""
        path = self.profiles_dir / f"{user_id}.json"

        try:
            data = profile.model_dump(mode="json")
            json_str = json.dumps(data, indent=2)

            async with aiofiles.open(path, "w") as f:
                await f.write(json_str)

            logger.debug(f"Saved profile {user_id}")

        except Exception as e:
            logger.error(f"Failed to save profile {user_id}: {e}")
            raise StorageError(f"Failed to save profile: {e}") from e

    async def load_profile(self, user_id: str) -> UserProfile | None:
        """Load user profile."""
        path = self.profiles_dir / f"{user_id}.json"

        if not path.exists():
            # Create default profile
            logger.info(f"Creating default profile for {user_id}")
            default_profile = UserProfile(user_id=user_id)
            await self.save_profile(user_id, default_profile)
            return default_profile

        try:
            async with aiofiles.open(path) as f:
                content = await f.read()
            data = json.loads(content)
            return UserProfile.model_validate(data)
        except Exception as e:
            logger.error(f"Failed to load profile {user_id}: {e}")
            return None

    async def _handle_corrupted_session(self, session_id: str, path: Path) -> None:
        """Handle corrupted session file."""
        from datetime import datetime

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        corrupted_path = path.parent / f"{path.stem}.corrupted.{timestamp}.json"

        try:
            await asyncio.to_thread(path.rename, corrupted_path)
            logger.warning(f"Renamed corrupted session to {corrupted_path.name}")
        except Exception as e:
            logger.error(f"Failed to rename corrupted session: {e}")

    # ==================== Template Storage Methods ====================

    async def save_template(self, name: str, template: DayTemplate) -> None:
        """Save a day template."""
        # Sanitize name for filename
        safe_name = self._sanitize_template_name(name)
        path = self.templates_dir / f"{safe_name}.json"

        try:
            data = template.model_dump(mode="json")
            json_str = json.dumps(data, indent=2)

            async with aiofiles.open(path, "w") as f:
                await f.write(json_str)

            logger.debug(f"Saved template '{name}'")

        except Exception as e:
            logger.error(f"Failed to save template '{name}': {e}")
            raise StorageError(f"Failed to save template: {e}") from e

    async def load_template(self, name: str) -> DayTemplate | None:
        """Load a day template by name."""
        safe_name = self._sanitize_template_name(name)
        path = self.templates_dir / f"{safe_name}.json"

        if not path.exists():
            return None

        try:
            async with aiofiles.open(path) as f:
                content = await f.read()

            data = json.loads(content)
            template = DayTemplate.model_validate(data)
            logger.debug(f"Loaded template '{name}'")
            return template

        except json.JSONDecodeError as e:
            logger.error(f"Corrupted template '{name}': {e}")
            return None
        except Exception as e:
            logger.error(f"Failed to load template '{name}': {e}")
            return None

    async def list_templates(self) -> list[TemplateMetadata]:
        """List all saved templates (metadata only)."""
        templates = []

        for path in self.templates_dir.glob("*.json"):
            try:
                async with aiofiles.open(path) as f:
                    content = await f.read()
                data = json.loads(content)

                templates.append(
                    TemplateMetadata(
                        name=data.get("name", path.stem),
                        description=data.get("description", ""),
                        task_count=len(data.get("schedule", [])),
                        created_at=data.get("created_at"),
                        last_used=data.get("last_used"),
                        use_count=data.get("use_count", 0),
                    )
                )
            except Exception as e:
                logger.error(f"Failed to read template metadata from {path}: {e}")

        # Sort by use_count (most used first), then by name
        templates.sort(key=lambda x: (-x.use_count, x.name))
        return templates

    async def delete_template(self, name: str) -> bool:
        """Delete a template by name."""
        safe_name = self._sanitize_template_name(name)
        path = self.templates_dir / f"{safe_name}.json"

        if path.exists():
            try:
                await asyncio.to_thread(path.unlink)
                logger.info(f"Deleted template '{name}'")
                return True
            except Exception as e:
                logger.error(f"Failed to delete template '{name}': {e}")
                return False
        return False

    async def template_exists(self, name: str) -> bool:
        """Check if a template exists."""
        safe_name = self._sanitize_template_name(name)
        path = self.templates_dir / f"{safe_name}.json"
        return path.exists()

    def _sanitize_template_name(self, name: str) -> str:
        """Sanitize template name for use as filename."""
        import re

        # Replace spaces and special chars with hyphens, lowercase
        safe = re.sub(r"[^\w\-]", "-", name.lower())
        # Remove consecutive hyphens
        safe = re.sub(r"-+", "-", safe)
        # Remove leading/trailing hyphens
        return safe.strip("-")
