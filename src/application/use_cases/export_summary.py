"""Export summary use case - export end-of-day summary to Markdown."""

import logging
from pathlib import Path

from rich.console import Console
from rich.panel import Panel

from ...domain.exceptions import SessionNotFound
from ...domain.services.export_service import ExportResult, ExportService
from ..container import Container

logger = logging.getLogger(__name__)


class ExportSummaryUseCase:
    """Use case: Export an end-of-day summary to Markdown format."""

    def __init__(self, container: Container):
        self.container = container
        self.storage = container.storage
        self.export_service = ExportService(container.config.storage)
        self.console = Console()

    async def execute(
        self,
        session_id: str,
        output_path: Path | None = None,
    ) -> ExportResult:
        """
        Export an end-of-day summary to Markdown.

        Args:
            session_id: Session identifier (usually YYYY-MM-DD)
            output_path: Optional custom output path

        Returns:
            ExportResult with success status, file path, and stats

        Raises:
            SessionNotFound: If session doesn't exist
        """
        # Load session
        memory = await self.storage.load_session(session_id)
        if not memory:
            raise SessionNotFound(f"No session found for {session_id}")

        if not memory.agent_state.plan:
            raise SessionNotFound(f"No plan found in session {session_id}")

        # Export the summary
        result = await self.export_service.export_summary(memory, output_path)

        # Display result
        if result.success:
            self.console.print(f"[bold green]Summary exported to:[/bold green] {result.file_path}")

            # Display quick stats if available
            if result.stats:
                self._display_quick_stats(result.stats)
        else:
            self.console.print(f"[bold red]Export failed:[/bold red] {result.error}")

        return result

    def _display_quick_stats(self, stats: dict) -> None:
        """Display quick summary statistics."""
        completion_rate = stats.get("completion_rate", 0)
        total_tasks = stats.get("total_tasks", 0)
        completed = stats.get("completed", 0)

        # Format time
        estimated = stats.get("estimated_total", 0)
        actual = stats.get("actual_total")

        time_info = f"Estimated: {self._format_duration(estimated)}"
        if actual:
            time_info += f" | Actual: {self._format_duration(actual)}"

        panel_content = f"""[bold]Quick Summary[/bold]

Completion: {completed}/{total_tasks} tasks ({completion_rate}%)
{time_info}"""

        panel = Panel(panel_content, border_style="cyan")
        self.console.print(panel)

    def _format_duration(self, minutes: int) -> str:
        """Format minutes as human-readable duration."""
        if not minutes:
            return "0m"
        hours = minutes // 60
        mins = minutes % 60
        if hours > 0 and mins > 0:
            return f"{hours}h {mins}m"
        elif hours > 0:
            return f"{hours}h"
        else:
            return f"{mins}m"
