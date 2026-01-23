"""Task import service - business logic for importing tasks from previous sessions."""

import logging
from datetime import datetime, timedelta

from ..models.planning import Plan, ScheduleItem, TaskStatus
from ..models.session import Memory

logger = logging.getLogger(__name__)


class TaskImportService:
    """Business logic for importing incomplete tasks from previous sessions."""

    def get_incomplete_tasks(self, memory: Memory) -> list[ScheduleItem]:
        """
        Get incomplete tasks from a session.

        Args:
            memory: Session memory to extract tasks from

        Returns:
            List of incomplete tasks (not_started or in_progress)
        """
        if not memory.agent_state.plan:
            return []

        return [
            item
            for item in memory.agent_state.plan.schedule
            if item.status in [TaskStatus.not_started, TaskStatus.in_progress]
        ]

    def get_skipped_tasks(self, memory: Memory) -> list[ScheduleItem]:
        """
        Get skipped tasks from a session (user may want to retry).

        Args:
            memory: Session memory to extract tasks from

        Returns:
            List of skipped tasks
        """
        if not memory.agent_state.plan:
            return []

        return [
            item for item in memory.agent_state.plan.schedule if item.status == TaskStatus.skipped
        ]

    def prepare_task_for_import(self, task: ScheduleItem) -> ScheduleItem:
        """
        Prepare a task for import to a new day.

        Resets status and timestamps while preserving task details.

        Args:
            task: Original task to copy

        Returns:
            New task ready for the new day
        """
        return task.model_copy(
            update={
                "status": TaskStatus.not_started,
                "actual_start": None,
                "actual_end": None,
                "edits": [],
                # Preserve: time, task, duration_minutes, priority, estimated_minutes, category
            }
        )

    def prepare_tasks_for_import(self, tasks: list[ScheduleItem]) -> list[ScheduleItem]:
        """
        Prepare multiple tasks for import.

        Args:
            tasks: List of tasks to prepare

        Returns:
            List of reset tasks ready for new day
        """
        return [self.prepare_task_for_import(task) for task in tasks]

    def format_tasks_for_context(self, tasks: list[ScheduleItem], source_date: str) -> str:
        """
        Format tasks for LLM context injection.

        Creates a human-readable summary of tasks to carry over.

        Args:
            tasks: Tasks to format
            source_date: Date the tasks came from (e.g., "2026-01-21")

        Returns:
            Formatted string for LLM context
        """
        if not tasks:
            return ""

        lines = [f"Incomplete tasks from {source_date} to carry over:"]
        for i, task in enumerate(tasks, 1):
            priority_marker = {"high": "!", "medium": "-", "low": "."}.get(task.priority, "-")
            estimated = f" (~{task.estimated_minutes}min)" if task.estimated_minutes else ""
            lines.append(f"  {i}. [{priority_marker}] {task.task}{estimated}")

        return "\n".join(lines)

    def format_tasks_for_display(self, tasks: list[ScheduleItem]) -> list[dict]:
        """
        Format tasks for CLI display.

        Args:
            tasks: Tasks to format

        Returns:
            List of dictionaries with display info
        """
        return [
            {
                "index": i + 1,
                "task": task.task,
                "time": task.time,
                "priority": task.priority,
                "estimated_minutes": task.estimated_minutes,
                "status": task.status.value,
                "category": task.category.value if task.category else "uncategorized",
            }
            for i, task in enumerate(tasks)
        ]

    def merge_imported_with_plan(
        self, imported_tasks: list[ScheduleItem], existing_plan: Plan, position: str = "start"
    ) -> Plan:
        """
        Merge imported tasks into an existing plan.

        Args:
            imported_tasks: Tasks to import
            existing_plan: Current plan
            position: Where to insert - "start", "end", or "smart"

        Returns:
            Updated plan with imported tasks
        """
        prepared_tasks = self.prepare_tasks_for_import(imported_tasks)

        if position == "start":
            new_schedule = prepared_tasks + existing_plan.schedule
        elif position == "end":
            new_schedule = existing_plan.schedule + prepared_tasks
        else:  # "smart" - interleave based on time
            # For smart merge, we'd need to parse times and insert appropriately
            # For now, default to start
            new_schedule = prepared_tasks + existing_plan.schedule

        return existing_plan.model_copy(update={"schedule": new_schedule})

    def get_yesterday_session_id(self, reference_date: str | None = None) -> str:
        """
        Get the session ID for yesterday's date.

        Args:
            reference_date: Optional reference date (defaults to today)

        Returns:
            Session ID for yesterday (YYYY-MM-DD format)
        """
        if reference_date:
            reference = datetime.strptime(reference_date, "%Y-%m-%d")
        else:
            reference = datetime.now()

        yesterday = reference - timedelta(days=1)
        return yesterday.strftime("%Y-%m-%d")

    def summarize_import_candidates(
        self, incomplete: list[ScheduleItem], skipped: list[ScheduleItem]
    ) -> dict:
        """
        Create a summary of import candidates.

        Args:
            incomplete: Incomplete tasks
            skipped: Skipped tasks

        Returns:
            Summary dictionary with counts and totals
        """
        incomplete_time = sum(t.estimated_minutes for t in incomplete if t.estimated_minutes) or 0
        skipped_time = sum(t.estimated_minutes for t in skipped if t.estimated_minutes) or 0

        return {
            "incomplete_count": len(incomplete),
            "incomplete_estimated_minutes": incomplete_time,
            "skipped_count": len(skipped),
            "skipped_estimated_minutes": skipped_time,
            "total_count": len(incomplete) + len(skipped),
            "total_estimated_minutes": incomplete_time + skipped_time,
            "has_candidates": len(incomplete) > 0 or len(skipped) > 0,
        }
