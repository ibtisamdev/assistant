"""Time tracking service - business logic for tracking task progress."""

import logging
from datetime import datetime

from ..models.planning import Plan, ScheduleItem, TaskStatus, TimeEdit

logger = logging.getLogger(__name__)


class TimeTrackingService:
    """Business logic for time tracking and progress monitoring."""

    def start_task(self, item: ScheduleItem) -> ScheduleItem:
        """
        Mark task as started with current timestamp.

        Args:
            item: Schedule item to start

        Returns:
            Updated schedule item

        Raises:
            ValueError: If task is already completed or in progress
        """
        if item.status == TaskStatus.completed:
            raise ValueError(f"Cannot start completed task: {item.task}")

        if item.status == TaskStatus.in_progress:
            logger.warning(f"Task already in progress: {item.task}")
            return item

        item.actual_start = datetime.now()
        item.status = TaskStatus.in_progress
        logger.info(f"Started task: {item.task}")
        return item

    def complete_task(self, item: ScheduleItem) -> ScheduleItem:
        """
        Mark task as completed with current timestamp.

        Args:
            item: Schedule item to complete

        Returns:
            Updated schedule item

        Raises:
            ValueError: If task hasn't been started
        """
        if item.status == TaskStatus.completed:
            logger.warning(f"Task already completed: {item.task}")
            return item

        if item.status == TaskStatus.not_started:
            # Auto-start if not started
            logger.info(f"Auto-starting task before completion: {item.task}")
            item.actual_start = datetime.now()

        item.actual_end = datetime.now()
        item.status = TaskStatus.completed
        logger.info(f"Completed task: {item.task} (took {item.actual_minutes} minutes)")
        return item

    def skip_task(self, item: ScheduleItem, reason: str | None = None) -> ScheduleItem:
        """
        Mark task as skipped.

        Args:
            item: Schedule item to skip
            reason: Optional reason for skipping

        Returns:
            Updated schedule item
        """
        if item.status == TaskStatus.completed:
            raise ValueError(f"Cannot skip completed task: {item.task}")

        item.status = TaskStatus.skipped
        logger.info(f"Skipped task: {item.task}" + (f" - {reason}" if reason else ""))
        return item

    def edit_timestamp(
        self,
        item: ScheduleItem,
        field: str,
        new_value: datetime,
        reason: str | None = None,
    ) -> ScheduleItem:
        """
        Manually edit a timestamp with audit trail.

        Args:
            item: Schedule item to edit
            field: Field to edit ("actual_start" or "actual_end")
            new_value: New timestamp value
            reason: Reason for the edit

        Returns:
            Updated schedule item with audit entry

        Raises:
            ValueError: If field is invalid
        """
        if field not in ["actual_start", "actual_end"]:
            raise ValueError(f"Invalid field: {field}. Must be 'actual_start' or 'actual_end'")

        # Get old value
        old_value = getattr(item, field)

        # Create audit entry
        edit = TimeEdit(field=field, old_value=old_value, new_value=new_value, reason=reason)
        item.edits.append(edit)

        # Update value
        setattr(item, field, new_value)

        logger.info(
            f"Edited {field} for task '{item.task}': {old_value} -> {new_value}"
            + (f" (Reason: {reason})" if reason else "")
        )
        return item

    def calculate_variance(self, item: ScheduleItem) -> int | None:
        """
        Calculate time variance for a task.

        Returns:
            Variance in minutes (positive = over time, negative = under time)
        """
        return item.time_variance

    def get_completion_stats(self, plan: Plan) -> dict[str, int | float]:
        """
        Calculate completion statistics for a plan.

        Returns:
            Dictionary with stats:
            - total_tasks: Total number of tasks
            - completed: Number of completed tasks
            - in_progress: Number of in-progress tasks
            - not_started: Number of not started tasks
            - skipped: Number of skipped tasks
            - completion_rate: Percentage completed (0-100)
            - estimated_total: Total estimated time
            - actual_total: Total actual time spent
            - total_variance: Total time variance
            - average_variance: Average variance per completed task
        """
        total_tasks = len(plan.schedule)
        completed = sum(1 for item in plan.schedule if item.status == TaskStatus.completed)
        in_progress = sum(1 for item in plan.schedule if item.status == TaskStatus.in_progress)
        not_started = sum(1 for item in plan.schedule if item.status == TaskStatus.not_started)
        skipped = sum(1 for item in plan.schedule if item.status == TaskStatus.skipped)

        completion_rate = (completed / total_tasks * 100) if total_tasks > 0 else 0

        # Time calculations
        estimated_total = sum(
            item.estimated_minutes for item in plan.schedule if item.estimated_minutes
        )
        actual_total = sum(item.actual_minutes for item in plan.schedule if item.actual_minutes)

        # Variance calculations (only for completed tasks)
        completed_tasks = [item for item in plan.schedule if item.status == TaskStatus.completed]
        variances = [
            item.time_variance for item in completed_tasks if item.time_variance is not None
        ]

        total_variance = sum(variances) if variances else 0
        average_variance = (total_variance / len(variances)) if variances else 0

        return {
            "total_tasks": total_tasks,
            "completed": completed,
            "in_progress": in_progress,
            "not_started": not_started,
            "skipped": skipped,
            "completion_rate": round(completion_rate, 1),
            "estimated_total": estimated_total,
            "actual_total": actual_total,
            "total_variance": total_variance,
            "average_variance": round(average_variance, 1),
        }

    def get_current_task(self, plan: Plan) -> ScheduleItem | None:
        """
        Find the task that should be happening now based on current time.

        Returns:
            Schedule item if found, None otherwise
        """
        now = datetime.now()
        current_time = now.hour * 60 + now.minute  # Convert to minutes since midnight

        for item in plan.schedule:
            try:
                # Parse time range (e.g., "09:00-10:00")
                start_str, end_str = item.time.split("-")
                start_h, start_m = map(int, start_str.strip().split(":"))
                end_h, end_m = map(int, end_str.strip().split(":"))

                start_mins = start_h * 60 + start_m
                end_mins = end_h * 60 + end_m

                # Check if current time falls within this task's time range
                if start_mins <= current_time < end_mins:
                    return item

            except Exception as e:
                logger.warning(f"Failed to parse time for task '{item.task}': {e}")
                continue

        return None

    def get_next_task(self, plan: Plan) -> ScheduleItem | None:
        """
        Find the next pending task (not started or in progress).

        Returns:
            Next pending schedule item, or None if all tasks are done
        """
        # First check if there's an in-progress task
        for item in plan.schedule:
            if item.status == TaskStatus.in_progress:
                return item

        # Then find first not-started task
        for item in plan.schedule:
            if item.status == TaskStatus.not_started:
                return item

        return None

    def find_task_by_name(self, plan: Plan, task_name: str) -> ScheduleItem | None:
        """
        Find a task by name (case-insensitive partial match).

        Args:
            plan: Plan to search
            task_name: Task name or partial name to find

        Returns:
            Matching schedule item or None
        """
        task_name_lower = task_name.lower()

        # First try exact match
        for item in plan.schedule:
            if item.task.lower() == task_name_lower:
                return item

        # Then try partial match
        for item in plan.schedule:
            if task_name_lower in item.task.lower():
                return item

        return None

    def validate_tracking_consistency(self, item: ScheduleItem) -> list[str]:
        """
        Validate tracking data consistency.

        Returns:
            List of validation warnings (empty if valid)
        """
        warnings = []

        # Check if end time is before start time
        if item.actual_start and item.actual_end:
            if item.actual_end < item.actual_start:
                warnings.append(
                    f"End time ({item.actual_end}) is before start time ({item.actual_start})"
                )

        # Check if completed status but no end time
        if item.status == TaskStatus.completed and not item.actual_end:
            warnings.append("Task marked completed but has no end time")

        # Check if in progress but has end time
        if item.status == TaskStatus.in_progress and item.actual_end:
            warnings.append("Task in progress but has an end time")

        return warnings
