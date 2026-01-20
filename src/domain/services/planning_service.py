"""Planning service - business logic for plan manipulation."""

from typing import List, Tuple
from ..models.planning import Plan, ScheduleItem
from ..models.profile import UserProfile
from ..exceptions import InvalidPlan


class PlanningService:
    """Plan manipulation and validation - pure business logic."""

    def validate_plan(self, plan: Plan) -> bool:
        """
        Validate plan completeness and consistency.

        Raises:
            InvalidPlan: If validation fails
        """
        if not plan.schedule:
            raise InvalidPlan("Plan must have at least one scheduled item")

        if not plan.priorities:
            raise InvalidPlan("Plan must have at least one priority")

        # Validate schedule items
        for item in plan.schedule:
            if not item.validate_time_format():
                raise InvalidPlan(f"Invalid time format in schedule item: {item.time}")

        # Check for overlaps
        if not plan.validate_no_overlaps():
            raise InvalidPlan("Plan has time conflicts")

        return True

    def format_plan_summary(self, plan: Plan) -> str:
        """Create human-readable summary of plan."""
        schedule_text = "\n".join([f"  {item.time}: {item.task}" for item in plan.schedule])

        priorities_text = "\n".join([f"  - {p}" for p in plan.priorities])

        duration = plan.calculate_total_duration()

        return f"""Schedule:
{schedule_text}

Top Priorities:
{priorities_text}

Notes: {plan.notes}

Total scheduled time: {duration} minutes ({duration // 60}h {duration % 60}m)"""

    def merge_schedule_items(
        self, existing: List[ScheduleItem], new: List[ScheduleItem]
    ) -> List[ScheduleItem]:
        """Merge schedule items, preferring newer items."""
        # Simple merge - replace completely
        # TODO: Implement smart merging
        return new if new else existing

    def calculate_free_time(
        self, plan: Plan, work_hours: Tuple[str, str] = ("09:00", "17:00")
    ) -> int:
        """Calculate available free time during work hours."""
        return plan.get_free_time(work_hours[0], work_hours[1])

    def suggest_breaks(self, plan: Plan, break_frequency: int = 90) -> List[str]:
        """Suggest break times based on schedule and break frequency."""
        suggestions = []

        # Simple implementation - suggest after every N minutes
        total_time = 0
        for i, item in enumerate(plan.schedule):
            duration = item.extract_duration()
            total_time += duration

            if total_time >= break_frequency and i < len(plan.schedule) - 1:
                next_item = plan.schedule[i + 1]
                suggestions.append(f"Consider a break before {next_item.time}")
                total_time = 0

        return suggestions

    def align_with_profile(self, plan: Plan, profile: UserProfile) -> List[str]:
        """Check plan alignment with user profile and return suggestions."""
        suggestions = []

        # Check work hours
        if profile.work_hours:
            # TODO: Validate schedule is within work hours
            pass

        # Check energy patterns
        if profile.energy_pattern:
            # TODO: Suggest moving high-priority tasks to high-energy times
            pass

        # Check recurring tasks
        if profile.recurring_tasks:
            # TODO: Check if recurring tasks are included
            pass

        return suggestions
