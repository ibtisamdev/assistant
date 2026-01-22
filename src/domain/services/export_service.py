"""Export service - orchestrates plan and summary exports."""

import logging
from dataclasses import dataclass
from pathlib import Path
from typing import Optional, Dict, Any

from ..models.planning import Plan
from ..models.session import Memory
from ...application.config import StorageConfig
from ...infrastructure.export.markdown import MarkdownExporter
from ...infrastructure.export.summary import SummaryExporter

logger = logging.getLogger(__name__)


@dataclass
class ExportResult:
    """Result of an export operation."""

    success: bool
    file_path: Optional[Path]
    error: Optional[str] = None
    stats: Optional[Dict[str, Any]] = None


class ExportService:
    """Orchestrates plan and summary exports."""

    def __init__(self, config: StorageConfig):
        """
        Initialize export service.

        Args:
            config: Storage configuration with export paths
        """
        self.plans_dir = config.plans_export_dir
        self.summaries_dir = config.summaries_export_dir
        self.markdown_exporter = MarkdownExporter()
        self.summary_exporter = SummaryExporter()

    def get_plan_path(self, date_str: str) -> Path:
        """
        Get the expected path for a plan export.

        Args:
            date_str: Date in YYYY-MM-DD format

        Returns:
            Path to the plan file
        """
        return self.plans_dir / f"{date_str}.md"

    def get_summary_path(self, date_str: str) -> Path:
        """
        Get the expected path for a summary export.

        Args:
            date_str: Date in YYYY-MM-DD format

        Returns:
            Path to the summary file
        """
        return self.summaries_dir / f"{date_str}-summary.md"

    async def export_plan(
        self,
        plan: Plan,
        date_str: str,
        output_path: Optional[Path] = None,
    ) -> ExportResult:
        """
        Export a plan to Markdown.

        Args:
            plan: Plan to export
            date_str: Date string for the filename and header
            output_path: Optional custom output path

        Returns:
            ExportResult with success status and file path
        """
        try:
            path = output_path or self.get_plan_path(date_str)
            await self.markdown_exporter.export(plan, path, date_str)

            logger.info(f"Plan exported successfully to {path}")
            return ExportResult(
                success=True,
                file_path=path,
            )
        except Exception as e:
            logger.error(f"Failed to export plan: {e}")
            return ExportResult(
                success=False,
                file_path=None,
                error=str(e),
            )

    async def export_summary(
        self,
        memory: Memory,
        output_path: Optional[Path] = None,
    ) -> ExportResult:
        """
        Export an end-of-day summary to Markdown.

        Args:
            memory: Session memory containing the plan
            output_path: Optional custom output path

        Returns:
            ExportResult with success status, file path, and stats
        """
        try:
            if not memory.agent_state.plan:
                return ExportResult(
                    success=False,
                    file_path=None,
                    error="No plan found in session",
                )

            date_str = memory.metadata.session_id
            path = output_path or self.get_summary_path(date_str)

            await self.summary_exporter.export(memory, path)

            # Calculate stats to return
            stats = self._calculate_stats(memory.agent_state.plan)

            logger.info(f"Summary exported successfully to {path}")
            return ExportResult(
                success=True,
                file_path=path,
                stats=stats,
            )
        except Exception as e:
            logger.error(f"Failed to export summary: {e}")
            return ExportResult(
                success=False,
                file_path=None,
                error=str(e),
            )

    async def export_all(
        self,
        memory: Memory,
        plan_path: Optional[Path] = None,
        summary_path: Optional[Path] = None,
    ) -> Dict[str, ExportResult]:
        """
        Export both plan and summary.

        Args:
            memory: Session memory containing the plan
            plan_path: Optional custom plan output path
            summary_path: Optional custom summary output path

        Returns:
            Dictionary with 'plan' and 'summary' ExportResults
        """
        results = {}

        if memory.agent_state.plan:
            date_str = memory.metadata.session_id
            results["plan"] = await self.export_plan(
                memory.agent_state.plan,
                date_str,
                plan_path,
            )
            results["summary"] = await self.export_summary(
                memory,
                summary_path,
            )
        else:
            error = ExportResult(
                success=False,
                file_path=None,
                error="No plan found in session",
            )
            results["plan"] = error
            results["summary"] = error

        return results

    def _calculate_stats(self, plan: Plan) -> Dict[str, Any]:
        """Calculate summary statistics for the plan."""
        from ..models.planning import TaskStatus

        total_tasks = len(plan.schedule)
        completed = sum(1 for item in plan.schedule if item.status == TaskStatus.completed)
        skipped = sum(1 for item in plan.schedule if item.status == TaskStatus.skipped)

        completion_rate = (completed / total_tasks * 100) if total_tasks > 0 else 0

        estimated_total = sum(
            (item.estimated_minutes or item.extract_duration()) for item in plan.schedule
        )
        actual_total = sum(
            item.actual_minutes for item in plan.schedule if item.actual_minutes is not None
        )

        return {
            "total_tasks": total_tasks,
            "completed": completed,
            "skipped": skipped,
            "completion_rate": round(completion_rate, 1),
            "estimated_total": estimated_total,
            "actual_total": actual_total if actual_total > 0 else None,
        }
