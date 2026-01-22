"""Export plan use case - export daily plan to Markdown."""

import logging
from pathlib import Path
from typing import Optional
from rich.console import Console

from ...domain.services.export_service import ExportService, ExportResult
from ...domain.exceptions import SessionNotFound
from ..container import Container

logger = logging.getLogger(__name__)


class ExportPlanUseCase:
    """Use case: Export a daily plan to Markdown format."""

    def __init__(self, container: Container):
        self.container = container
        self.storage = container.storage
        self.export_service = ExportService(container.config.storage)
        self.console = Console()

    async def execute(
        self,
        session_id: str,
        output_path: Optional[Path] = None,
    ) -> ExportResult:
        """
        Export a daily plan to Markdown.

        Args:
            session_id: Session identifier (usually YYYY-MM-DD)
            output_path: Optional custom output path

        Returns:
            ExportResult with success status and file path

        Raises:
            SessionNotFound: If session doesn't exist
        """
        # Load session
        memory = await self.storage.load_session(session_id)
        if not memory:
            raise SessionNotFound(f"No session found for {session_id}")

        if not memory.agent_state.plan:
            raise SessionNotFound(f"No plan found in session {session_id}")

        # Export the plan
        result = await self.export_service.export_plan(
            memory.agent_state.plan,
            session_id,
            output_path,
        )

        # Display result
        if result.success:
            self.console.print(f"[bold green]Plan exported to:[/bold green] {result.file_path}")
        else:
            self.console.print(f"[bold red]Export failed:[/bold red] {result.error}")

        return result
