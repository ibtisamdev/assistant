"""Summary exporter for end-of-day reviews."""

import logging
from datetime import datetime
from pathlib import Path
from typing import Any

import aiofiles

from ...domain.models.planning import Plan, TaskStatus
from ...domain.models.session import Memory

logger = logging.getLogger(__name__)


class SummaryExporter:
    """Export end-of-day summaries with time analysis."""

    def _format_date_header(self, date_str: str) -> str:
        """Convert YYYY-MM-DD to human-readable format."""
        try:
            date = datetime.strptime(date_str, "%Y-%m-%d")
            return date.strftime("%B %d, %Y")  # e.g., "January 22, 2026"
        except ValueError:
            return date_str

    def _format_duration(self, minutes: int | None) -> str:
        """Format minutes as human-readable duration."""
        if minutes is None:
            return "N/A"
        hours = minutes // 60
        mins = minutes % 60
        if hours > 0 and mins > 0:
            return f"{hours}h {mins}m"
        elif hours > 0:
            return f"{hours}h"
        else:
            return f"{mins}m"

    def _format_variance(self, variance: int | None) -> str:
        """Format time variance with indicator."""
        if variance is None:
            return "N/A"
        if variance > 0:
            return f"+{variance}m"
        elif variance < 0:
            return f"{variance}m"
        else:
            return "0m"

    def _variance_indicator(self, variance: int | None) -> str:
        """Get emoji indicator for variance."""
        if variance is None:
            return ""
        if abs(variance) <= 5:
            return ""  # Within tolerance
        elif variance > 0:
            return ""  # Over time (warning)
        else:
            return ""  # Under time (good)

    def _status_emoji(self, status: TaskStatus) -> str:
        """Get emoji for task status."""
        if status == TaskStatus.completed:
            return ""
        elif status == TaskStatus.in_progress:
            return ""
        elif status == TaskStatus.skipped:
            return ""
        else:
            return ""

    def _calculate_stats(self, plan: Plan) -> dict[str, Any]:
        """Calculate summary statistics for the plan."""
        total_tasks = len(plan.schedule)
        completed = sum(1 for item in plan.schedule if item.status == TaskStatus.completed)
        in_progress = sum(1 for item in plan.schedule if item.status == TaskStatus.in_progress)
        not_started = sum(1 for item in plan.schedule if item.status == TaskStatus.not_started)
        skipped = sum(1 for item in plan.schedule if item.status == TaskStatus.skipped)

        completion_rate = (completed / total_tasks * 100) if total_tasks > 0 else 0

        # Time calculations
        estimated_total = sum(
            (item.estimated_minutes or item.extract_duration()) for item in plan.schedule
        )
        actual_total = sum(
            item.actual_minutes for item in plan.schedule if item.actual_minutes is not None
        )

        # Variance calculations (only for completed tasks)
        completed_tasks = [item for item in plan.schedule if item.status == TaskStatus.completed]
        variances = [
            item.time_variance for item in completed_tasks if item.time_variance is not None
        ]
        total_variance = sum(variances) if variances else None

        # Check if any tracking data exists
        has_tracking = any(item.actual_start or item.actual_end for item in plan.schedule)

        return {
            "total_tasks": total_tasks,
            "completed": completed,
            "in_progress": in_progress,
            "not_started": not_started,
            "skipped": skipped,
            "completion_rate": round(completion_rate, 1),
            "estimated_total": estimated_total,
            "actual_total": actual_total if actual_total > 0 else None,
            "total_variance": total_variance,
            "has_tracking": has_tracking,
        }

    def to_string(self, plan: Plan, date_str: str | None = None, notes: str | None = None) -> str:
        """
        Convert plan to summary Markdown string with time analysis.

        Args:
            plan: Plan to summarize
            date_str: Date string (YYYY-MM-DD) for the header
            notes: Optional notes from the plan

        Returns:
            Markdown-formatted summary string
        """
        lines = []
        stats = self._calculate_stats(plan)

        # Header
        if date_str:
            date_header = self._format_date_header(date_str)
            lines.append(f"# Daily Summary - {date_header}")
        else:
            lines.append("# Daily Summary")
        lines.append("")

        # Completion Overview
        lines.append("## Completion Overview")
        lines.append("")
        lines.append("| Status | Count |")
        lines.append("|--------|-------|")
        if stats["completed"] > 0:
            lines.append(f"| Completed | {stats['completed']} |")
        if stats["in_progress"] > 0:
            lines.append(f"| In Progress | {stats['in_progress']} |")
        if stats["skipped"] > 0:
            lines.append(f"| Skipped | {stats['skipped']} |")
        if stats["not_started"] > 0:
            lines.append(f"| Not Started | {stats['not_started']} |")
        lines.append("")
        lines.append(f"**Completion Rate:** {stats['completion_rate']}%")
        lines.append("")

        # Time Analysis
        lines.append("## Time Analysis")
        lines.append("")

        if stats["has_tracking"]:
            lines.append("| Task | Estimated | Actual | Variance |")
            lines.append("|------|-----------|--------|----------|")

            for item in plan.schedule:
                estimated = item.estimated_minutes or item.extract_duration()
                actual = item.actual_minutes
                variance = item.time_variance

                est_str = self._format_duration(estimated)
                act_str = self._format_duration(actual) if actual else "N/A"
                var_str = self._format_variance(variance)
                indicator = self._variance_indicator(variance)

                task_display = item.task[:40] + "..." if len(item.task) > 40 else item.task
                lines.append(f"| {task_display} | {est_str} | {act_str} | {var_str} {indicator} |")

            lines.append("")

            # Time totals
            lines.append(f"**Total Estimated:** {self._format_duration(stats['estimated_total'])}")
            if stats["actual_total"]:
                lines.append(f"**Total Actual:** {self._format_duration(stats['actual_total'])}")
            if stats["total_variance"] is not None:
                direction = (
                    "took longer than planned"
                    if stats["total_variance"] > 0
                    else "finished faster than planned"
                )
                lines.append(
                    f"**Overall Variance:** {self._format_variance(stats['total_variance'])} ({direction})"
                )
        else:
            lines.append("| Task | Estimated | Actual | Variance |")
            lines.append("|------|-----------|--------|----------|")
            for item in plan.schedule:
                estimated = item.estimated_minutes or item.extract_duration()
                est_str = self._format_duration(estimated)
                task_display = item.task[:40] + "..." if len(item.task) > 40 else item.task
                lines.append(f"| {task_display} | {est_str} | N/A | N/A |")
            lines.append("")
            lines.append(
                "> *No time tracking data recorded. Use `uv run checkin` to track actual time.*"
            )

        lines.append("")

        # Tasks Completed section
        completed_tasks = [item for item in plan.schedule if item.status == TaskStatus.completed]
        if completed_tasks:
            lines.append("## Tasks Completed")
            lines.append("")
            for item in completed_tasks:
                actual_str = (
                    f"(actual: {self._format_duration(item.actual_minutes)})"
                    if item.actual_minutes
                    else ""
                )
                lines.append(f"- [x] **{item.time}** - {item.task} {actual_str}")
            lines.append("")

        # Tasks In Progress section
        in_progress_tasks = [
            item for item in plan.schedule if item.status == TaskStatus.in_progress
        ]
        if in_progress_tasks:
            lines.append("## Tasks In Progress")
            lines.append("")
            for item in in_progress_tasks:
                lines.append(f"- [ ] **{item.time}** - {item.task}")
            lines.append("")

        # Tasks Skipped section
        skipped_tasks = [item for item in plan.schedule if item.status == TaskStatus.skipped]
        if skipped_tasks:
            lines.append("## Tasks Skipped")
            lines.append("")
            for item in skipped_tasks:
                lines.append(f"- {self._status_emoji(item.status)} **{item.time}** - {item.task}")
            lines.append("")

        # Tasks Not Started section
        not_started_tasks = [
            item for item in plan.schedule if item.status == TaskStatus.not_started
        ]
        if not_started_tasks:
            lines.append("## Tasks Not Started")
            lines.append("")
            for item in not_started_tasks:
                lines.append(f"- [ ] **{item.time}** - {item.task}")
            lines.append("")

        # Notes section
        if notes:
            lines.append("## Notes")
            lines.append("")
            lines.append(notes)
            lines.append("")

        # Footer
        lines.append("---")
        lines.append("*Generated by Daily Planning Assistant*")
        if date_str:
            lines.append(f"*Session ID: {date_str}*")

        return "\n".join(lines)

    async def export(
        self,
        memory: Memory,
        output_path: Path,
    ) -> Path:
        """
        Export summary to Markdown file.

        Args:
            memory: Session memory containing plan and metadata
            output_path: Path to write the file

        Returns:
            Path to the created file
        """
        # Ensure parent directory exists
        output_path.parent.mkdir(parents=True, exist_ok=True)

        # Extract data from memory
        plan = memory.agent_state.plan
        if not plan:
            raise ValueError("No plan found in session memory")

        date_str = memory.metadata.session_id
        notes = plan.notes if plan.notes else None

        # Generate markdown content
        content = self.to_string(plan, date_str, notes)

        # Write to file
        async with aiofiles.open(output_path, "w", encoding="utf-8") as f:
            await f.write(content)

        logger.info(f"Exported summary to {output_path}")
        return output_path
