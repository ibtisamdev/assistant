"""View daily productivity statistics use case."""

import logging

from rich.console import Console

from ...domain.exceptions import SessionNotFound
from ...domain.models.metrics import DailyMetrics
from ...domain.services.metrics_service import MetricsService
from ...infrastructure.io.formatters import MetricsFormatter
from ..container import Container

logger = logging.getLogger(__name__)


class ViewStatsUseCase:
    """Display daily productivity statistics."""

    def __init__(self, container: Container):
        self.container = container
        self.storage = container.storage
        self.metrics_service = MetricsService()
        self.console = Console()

    async def execute(self, session_id: str, output_json: bool = False) -> DailyMetrics:
        """
        Load session and display daily metrics.

        Args:
            session_id: Session date (YYYY-MM-DD)
            output_json: If True, output as JSON instead of formatted display

        Returns:
            DailyMetrics object

        Raises:
            SessionNotFound: If no session exists for the given date
        """
        # Load session
        memory = await self.storage.load_session(session_id)

        if not memory:
            raise SessionNotFound(f"No session found for {session_id}")

        if not memory.agent_state.plan:
            raise SessionNotFound(f"Session {session_id} has no plan yet")

        # Calculate metrics
        metrics = self.metrics_service.calculate_daily_metrics(memory.agent_state.plan, session_id)

        if output_json:
            # Output as JSON
            self.console.print(metrics.model_dump_json(indent=2))
        else:
            # Display formatted output
            self._display_metrics(metrics)

        logger.info(f"Displayed stats for session {session_id}")
        return metrics

    def _display_metrics(self, metrics: DailyMetrics) -> None:
        """Display formatted metrics to console."""
        # Summary panel
        summary_panel = MetricsFormatter.format_daily_metrics(metrics)
        self.console.print(summary_panel)
        self.console.print()

        # Category breakdown
        if metrics.time_by_category:
            category_table = MetricsFormatter.format_category_breakdown(metrics)
            self.console.print(category_table)
            self.console.print()

        # Estimation accuracy (only if we have tracking data)
        if metrics.estimation_accuracy:
            accuracy_panel = MetricsFormatter.format_estimation_accuracy(
                metrics.estimation_accuracy
            )
            self.console.print(accuracy_panel)
            self.console.print()

        # Top time consumers
        if metrics.top_time_consumers:
            consumers_table = MetricsFormatter.format_top_consumers(metrics)
            self.console.print(consumers_table)
