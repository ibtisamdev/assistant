"""Session orchestrator - high-level session management."""

import logging
from datetime import datetime

from ..domain.models.session import Memory
from .container import Container
from .use_cases.create_plan import CreatePlanUseCase
from .use_cases.resume_session import ResumeSessionUseCase
from .use_cases.revise_plan import RevisePlanUseCase

logger = logging.getLogger(__name__)


class SessionOrchestrator:
    """High-level session management."""

    def __init__(self, container: Container):
        self.container = container
        self.create_plan_uc = CreatePlanUseCase(container)
        self.resume_session_uc = ResumeSessionUseCase(container)
        self.revise_plan_uc = RevisePlanUseCase(container)
        self.storage = container.storage

    async def run_new_session(self, date: str | None = None, force_new: bool = False) -> Memory:
        """
        Start new planning session.

        Args:
            date: Session date (YYYY-MM-DD), defaults to today
            force_new: Force create new session even if exists
        """
        session_id = date or datetime.now().strftime("%Y-%m-%d")
        logger.info(f"Starting new session: {session_id}")

        return await self.create_plan_uc.execute(session_id, force_new)

    async def run_resume(self, date: str) -> Memory:
        """
        Resume existing session.

        Args:
            date: Session date (YYYY-MM-DD)
        """
        logger.info(f"Resuming session: {date}")
        return await self.resume_session_uc.execute(date)

    async def run_revise(self, date: str | None = None) -> Memory:
        """
        Revise finalized plan.

        Args:
            date: Session date (YYYY-MM-DD), defaults to today
        """
        session_id = date or datetime.now().strftime("%Y-%m-%d")
        logger.info(f"Revising plan: {session_id}")

        return await self.revise_plan_uc.execute(session_id)

    async def list_sessions(self) -> list:
        """List all saved sessions."""
        return await self.storage.list_sessions()

    async def delete_session(self, date: str) -> bool:
        """Delete a session."""
        logger.info(f"Deleting session: {date}")
        return await self.storage.delete_session(date)
