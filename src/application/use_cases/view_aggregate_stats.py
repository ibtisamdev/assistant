"""View aggregate productivity statistics use case."""

import logging
from datetime import datetime, timedelta
from typing import Optional, List

from rich.console import Console

from ..container import Container
from ...domain.exceptions import SessionNotFound
from ...domain.services.metrics_service import MetricsService
from ...domain.models.metrics import AggregateMetrics
from ...domain.models.session import Memory
from ...infrastructure.io.formatters import MetricsFormatter

logger = logging.getLogger(__name__)


class ViewAggregateStatsUseCase:
    """Display aggregate productivity statistics (weekly/monthly)."""

    def __init__(self, container: Container):
        self.container = container
        self.storage = container.storage
        self.metrics_service = MetricsService()
        self.console = Console()

    async def execute(
        self,
        week: bool = False,
        month: bool = False,
        from_date: Optional[str] = None,
        to_date: Optional[str] = None,
        output_json: bool = False,
    ) -> AggregateMetrics:
        """
        Load sessions and display aggregate metrics.

        Args:
            week: If True, show current week's summary
            month: If True, show current month's summary
            from_date: Start date for custom range (YYYY-MM-DD)
            to_date: End date for custom range (YYYY-MM-DD)
            output_json: If True, output as JSON instead of formatted display

        Returns:
            AggregateMetrics object

        Raises:
            SessionNotFound: If no sessions found in the specified range
        """
        # Load all sessions
        all_sessions = await self._load_all_sessions()

        if not all_sessions:
            raise SessionNotFound("No sessions found. Create some plans first!")

        # Calculate metrics based on options
        if week:
            metrics = self.metrics_service.calculate_weekly_metrics(all_sessions)
        elif month:
            metrics = self.metrics_service.calculate_monthly_metrics(all_sessions)
        elif from_date and to_date:
            metrics = self.metrics_service.calculate_aggregate_metrics(
                sessions=all_sessions,
                period_start=from_date,
                period_end=to_date,
                period_type="custom",
            )
        else:
            # Default to current week
            metrics = self.metrics_service.calculate_weekly_metrics(all_sessions)

        if metrics.days_with_data == 0:
            raise SessionNotFound(
                f"No sessions with plans found for {metrics.period_start} to {metrics.period_end}"
            )

        if output_json:
            self.console.print(metrics.model_dump_json(indent=2))
        else:
            self._display_metrics(metrics)

        logger.info(
            f"Displayed {metrics.period_type} stats: {metrics.period_start} to {metrics.period_end}"
        )
        return metrics

    async def _load_all_sessions(self) -> List[Memory]:
        """Load all sessions that have plans."""
        session_list = await self.storage.list_sessions()
        sessions = []

        for session_meta in session_list:
            if session_meta.get("has_plan"):
                memory = await self.storage.load_session(session_meta["session_id"])
                if memory and memory.agent_state.plan:
                    sessions.append(memory)

        return sessions

    def _display_metrics(self, metrics: AggregateMetrics) -> None:
        """Display formatted aggregate metrics to console."""
        # Summary panel
        summary_panel = MetricsFormatter.format_aggregate_metrics(metrics)
        self.console.print(summary_panel)
        self.console.print()

        # Completion trend
        if metrics.completion_rate_by_day:
            trend_panel = MetricsFormatter.format_completion_trend(metrics)
            self.console.print(trend_panel)
            self.console.print()

        # Category breakdown
        if metrics.total_by_category:
            category_table = MetricsFormatter.format_aggregate_categories(metrics)
            self.console.print(category_table)
            self.console.print()

        # Patterns
        patterns_panel = MetricsFormatter.format_patterns(metrics)
        self.console.print(patterns_panel)
