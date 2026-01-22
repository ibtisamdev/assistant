"""Planning service - business logic for plan manipulation."""

from typing import List, Tuple
from datetime import datetime
from ..models.planning import Plan, ScheduleItem
from ..models.profile import UserProfile
from ..models.session import Memory
from ..exceptions import InvalidPlan


class PlanningService:
    """Plan manipulation and validation - pure business logic."""

    def validate_plan(self, plan: Plan) -> bool:
        """
        Validate plan completeness and consistency.

        NOTE: This should only be called when a plan exists.
        Use `if session.plan: validate_plan(session.plan)` pattern.

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

    def populate_time_estimates(self, plan: Plan) -> Plan:
        """
        Populate estimated_minutes for schedule items from their time ranges.
        This is a fallback if LLM doesn't provide estimates.
        """
        for item in plan.schedule:
            if item.estimated_minutes is None:
                # Use duration from time range as estimate
                item.estimated_minutes = item.extract_duration()

        # Update plan's estimated duration
        plan.calculate_total_duration()
        return plan

    def validate_tracking_data(self, plan: Plan) -> Tuple[bool, List[str]]:
        """
        Validate tracking data consistency across all tasks.

        Returns:
            Tuple of (is_valid, list_of_warnings)
        """
        from .time_tracking_service import TimeTrackingService

        tracking_service = TimeTrackingService()
        all_warnings = []

        for item in plan.schedule:
            warnings = tracking_service.validate_tracking_consistency(item)
            if warnings:
                all_warnings.extend([f"{item.task}: {warning}" for warning in warnings])

        return len(all_warnings) == 0, all_warnings

    def update_planning_history(
        self, profile: UserProfile, memory: Memory, session_date: str
    ) -> UserProfile:
        """
        Update user's planning history based on completed session.

        This auto-learns from session patterns to improve future planning.

        Args:
            profile: User's profile to update
            memory: Completed session memory
            session_date: Date of the session (YYYY-MM-DD)

        Returns:
            Updated profile with learning insights
        """
        # Update basic stats
        profile.planning_history.sessions_completed += 1
        profile.planning_history.last_session_date = session_date

        # Analyze session for patterns
        revision_count = len(
            [
                msg
                for msg in memory.conversation.messages
                if msg.role == "user" and "feedback" in msg.content.lower()
            ]
        )

        # Learn from session patterns
        if revision_count == 0:
            # Plan was accepted without changes - successful pattern
            pattern = self._extract_successful_pattern(memory)
            if pattern and pattern not in profile.planning_history.successful_patterns:
                profile.planning_history.successful_patterns.append(pattern)
                # Keep only last 10 patterns
                profile.planning_history.successful_patterns = (
                    profile.planning_history.successful_patterns[-10:]
                )
        elif revision_count > 0:
            # Learn from adjustments
            adjustments = self._extract_common_adjustments(memory)
            for adjustment in adjustments:
                if adjustment not in profile.planning_history.common_adjustments:
                    profile.planning_history.common_adjustments.append(adjustment)
                    # Keep only last 10
                    profile.planning_history.common_adjustments = (
                        profile.planning_history.common_adjustments[-10:]
                    )

        # Update timestamp
        from datetime import datetime

        profile.last_updated = datetime.now()

        return profile

    def _extract_successful_pattern(self, memory: Memory) -> str:
        """Extract what made this session successful."""
        plan = memory.agent_state.plan
        if not plan:
            return ""

        # Analyze the plan structure
        task_count = len(plan.schedule)
        total_duration = plan.calculate_total_duration()
        avg_task_duration = total_duration // task_count if task_count > 0 else 0

        # Pattern based on structure
        if task_count <= 5 and avg_task_duration >= 60:
            return "Fewer tasks with longer time blocks"
        elif task_count > 8 and avg_task_duration <= 30:
            return "Many short tasks in quick succession"
        elif task_count >= 6 and task_count <= 8:
            return "Moderate number of balanced tasks"

        return "Standard planning approach"

    def _extract_common_adjustments(self, memory: Memory) -> List[str]:
        """Extract common adjustments from feedback."""
        adjustments = []

        # Analyze conversation for adjustment keywords
        feedback_messages = [
            msg.content.lower() for msg in memory.conversation.messages if msg.role == "user"
        ]

        # Check for common adjustment patterns
        all_feedback = " ".join(feedback_messages)

        if "more time" in all_feedback or "longer" in all_feedback:
            adjustments.append("Tends to need more time per task")
        if "less time" in all_feedback or "shorter" in all_feedback:
            adjustments.append("Prefers shorter task durations")
        if "break" in all_feedback:
            adjustments.append("Adjusts break timing")
        if "priority" in all_feedback or "important" in all_feedback:
            adjustments.append("Refines task priorities")
        if "move" in all_feedback or "earlier" in all_feedback or "later" in all_feedback:
            adjustments.append("Adjusts task timing/order")

        return adjustments
