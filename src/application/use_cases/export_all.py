"""Export all use case - export both plan and summary to Markdown."""

import logging
from pathlib import Path

from rich.console import Console

from ...domain.exceptions import SessionNotFound
from ...domain.services.export_service import ExportResult, ExportService
from ..container import Container

logger = logging.getLogger(__name__)


class ExportAllUseCase:
    """Use case: Export both daily plan and summary to Markdown format."""

    def __init__(self, container: Container):
        self.container = container
        self.storage = container.storage
        self.export_service = ExportService(container.config.storage)
        self.console = Console()

    async def execute(
        self,
        session_id: str,
        plan_path: Path | None = None,
        summary_path: Path | None = None,
    ) -> dict[str, ExportResult]:
        """
        Export both plan and summary to Markdown.

        Args:
            session_id: Session identifier (usually YYYY-MM-DD)
            plan_path: Optional custom path for plan export
            summary_path: Optional custom path for summary export

        Returns:
            Dictionary with 'plan' and 'summary' ExportResults

        Raises:
            SessionNotFound: If session doesn't exist
        """
        # Load session
        memory = await self.storage.load_session(session_id)
        if not memory:
            raise SessionNotFound(f"No session found for {session_id}")

        if not memory.agent_state.plan:
            raise SessionNotFound(f"No plan found in session {session_id}")

        # Export both
        results = await self.export_service.export_all(
            memory,
            plan_path,
            summary_path,
        )

        # Display results
        self._display_results(results)

        return results

    def _display_results(self, results: dict[str, ExportResult]) -> None:
        """Display export results."""
        self.console.print()

        plan_result = results.get("plan")
        summary_result = results.get("summary")

        if plan_result and plan_result.success:
            self.console.print(
                f"[bold green]Plan exported to:[/bold green] {plan_result.file_path}"
            )
        elif plan_result:
            self.console.print(f"[bold red]Plan export failed:[/bold red] {plan_result.error}")

        if summary_result and summary_result.success:
            self.console.print(
                f"[bold green]Summary exported to:[/bold green] {summary_result.file_path}"
            )
        elif summary_result:
            self.console.print(
                f"[bold red]Summary export failed:[/bold red] {summary_result.error}"
            )

        # Summary stats
        if summary_result and summary_result.success and summary_result.stats:
            stats = summary_result.stats
            self.console.print()
            self.console.print(
                f"[dim]Completion: {stats['completed']}/{stats['total_tasks']} tasks "
                f"({stats['completion_rate']}%)[/dim]"
            )
