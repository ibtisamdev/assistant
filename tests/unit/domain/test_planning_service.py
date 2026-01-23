"""Tests for planning service."""

from datetime import datetime

import pytest

from src.domain.exceptions import InvalidPlan
from src.domain.models import TaskStatus
from src.domain.models.conversation import ConversationHistory, Message, MessageRole
from src.domain.models.planning import Plan, ScheduleItem
from src.domain.models.profile import RecurringTask, UserProfile, WorkHours
from src.domain.models.session import AgentState, Memory, SessionMetadata
from src.domain.models.state import State
from src.domain.services.planning_service import PlanningService
from tests.fixtures.factories import PlanFactory


@pytest.fixture
def service():
    """Create PlanningService instance."""
    return PlanningService()


@pytest.fixture
def sample_profile():
    """Create a sample user profile."""
    return UserProfile(
        user_id="test-user",
        top_priorities=["Ship feature", "Review code"],
        recurring_tasks=[
            RecurringTask(name="Daily standup", frequency="daily", duration=15),
        ],
        work_hours=WorkHours(start="08:00", end="18:00"),
    )


@pytest.fixture
def sample_memory():
    """Create a sample memory with plan."""
    plan = PlanFactory.create()
    return Memory(
        metadata=SessionMetadata(
            session_id="2026-01-23",
            created_at=datetime.now(),
            last_updated=datetime.now(),
        ),
        agent_state=AgentState(
            state=State.done,
            plan=plan,
        ),
        conversation=ConversationHistory(
            messages=[
                Message(role=MessageRole.user, content="Plan my day"),
                Message(role=MessageRole.assistant, content="Here's your plan"),
            ]
        ),
    )


class TestPlanningService:
    def test_validate_plan_success(self):
        service = PlanningService()
        plan = PlanFactory.create()
        assert service.validate_plan(plan)

    def test_validate_plan_fails_without_schedule(self):
        service = PlanningService()
        plan = PlanFactory.create(schedule=[])

        with pytest.raises(InvalidPlan, match="at least one scheduled item"):
            service.validate_plan(plan)

    def test_validate_plan_fails_without_priorities(self):
        service = PlanningService()
        plan = PlanFactory.create(priorities=[])

        with pytest.raises(InvalidPlan, match="at least one priority"):
            service.validate_plan(plan)

    def test_format_plan_summary(self):
        service = PlanningService()
        plan = PlanFactory.create()
        summary = service.format_plan_summary(plan)

        assert "Schedule:" in summary
        assert "Top Priorities:" in summary
        assert "Notes:" in summary

    def test_calculate_free_time(self):
        service = PlanningService()
        plan = PlanFactory.create()

        # Plan has 5 hours scheduled (09-10, 10-12, 14-16)
        free_time = service.calculate_free_time(plan, ("09:00", "17:00"))

        # 8 hour work day - 5 hours scheduled = 3 hours free
        assert free_time == 180  # 3 hours in minutes


class TestValidatePlanAdvanced:
    """Advanced validation tests."""

    def test_validate_plan_invalid_time_format_raises(self, service):
        """Plan with invalid time format should raise InvalidPlan."""
        plan = Plan(
            schedule=[ScheduleItem(time="invalid-time", task="Task")],
            priorities=["Priority"],
            notes="",
        )

        with pytest.raises(InvalidPlan, match="Invalid time format"):
            service.validate_plan(plan)

    def test_validate_plan_overlapping_times_not_yet_implemented(self, service):
        """Overlap detection is TODO - currently passes validation."""
        plan = Plan(
            schedule=[
                ScheduleItem(time="09:00-11:00", task="Task 1"),
                ScheduleItem(time="10:00-12:00", task="Task 2"),  # Overlaps but not detected
            ],
            priorities=["Priority"],
            notes="",
        )

        # TODO: When overlap detection is implemented, this should raise InvalidPlan
        # For now, it passes validation since validate_no_overlaps returns True
        result = service.validate_plan(plan)
        assert result is True


class TestFormatPlanSummary:
    """Tests for format_plan_summary method."""

    def test_format_plan_summary_shows_hours_and_minutes(self, service):
        """Should show duration in hours and minutes."""
        plan = Plan(
            schedule=[
                ScheduleItem(time="09:00-12:30", task="Long task"),  # 3.5 hours
            ],
            priorities=["Test"],
            notes="Test note",
        )

        summary = service.format_plan_summary(plan)
        assert "210 minutes" in summary  # 3.5 hours = 210 min
        assert "3h 30m" in summary


class TestMergeScheduleItems:
    """Tests for merge_schedule_items method."""

    def test_merge_replaces_with_new(self, service):
        """New items should replace existing."""
        existing = [ScheduleItem(time="09:00-10:00", task="Old")]
        new = [ScheduleItem(time="10:00-11:00", task="New")]

        result = service.merge_schedule_items(existing, new)

        assert len(result) == 1
        assert result[0].task == "New"

    def test_merge_keeps_existing_if_new_empty(self, service):
        """If new is empty, keep existing."""
        existing = [ScheduleItem(time="09:00-10:00", task="Old")]

        result = service.merge_schedule_items(existing, [])

        assert len(result) == 1
        assert result[0].task == "Old"


class TestSuggestBreaks:
    """Tests for suggest_breaks method."""

    def test_suggest_breaks_after_long_blocks(self, service):
        """Should suggest breaks after specified duration."""
        plan = Plan(
            schedule=[
                ScheduleItem(time="09:00-10:30", task="Task 1"),  # 90 min
                ScheduleItem(time="10:30-12:00", task="Task 2"),  # 90 min
                ScheduleItem(time="12:00-13:00", task="Task 3"),  # 60 min
            ],
            priorities=["Test"],
            notes="",
        )

        suggestions = service.suggest_breaks(plan, break_frequency=90)

        assert len(suggestions) >= 1
        assert any("break" in s.lower() for s in suggestions)

    def test_suggest_breaks_empty_for_short_tasks(self, service):
        """No break suggestions for short tasks."""
        plan = Plan(
            schedule=[
                ScheduleItem(time="09:00-09:30", task="Short 1"),
                ScheduleItem(time="09:30-10:00", task="Short 2"),
            ],
            priorities=["Test"],
            notes="",
        )

        suggestions = service.suggest_breaks(plan, break_frequency=120)

        # Short tasks don't exceed 120 min threshold
        assert len(suggestions) == 0


class TestAlignWithProfile:
    """Tests for align_with_profile method."""

    def test_align_returns_list(self, service, sample_profile):
        """Should return a list of suggestions."""
        plan = PlanFactory.create()
        suggestions = service.align_with_profile(plan, sample_profile)

        assert isinstance(suggestions, list)

    def test_align_empty_for_minimal_profile(self, service):
        """Empty profile yields no suggestions (TODOs not implemented)."""
        minimal_profile = UserProfile(user_id="minimal")
        plan = PlanFactory.create()

        suggestions = service.align_with_profile(plan, minimal_profile)

        # Currently returns empty (TODOs in code)
        assert suggestions == []


class TestPopulateTimeEstimates:
    """Tests for populate_time_estimates method."""

    def test_populate_estimates_from_time_range(self, service):
        """Should populate estimated_minutes from time ranges."""
        plan = Plan(
            schedule=[
                ScheduleItem(time="09:00-10:30", task="Task 1"),  # 90 min
                ScheduleItem(time="11:00-12:00", task="Task 2"),  # 60 min
            ],
            priorities=["Test"],
            notes="",
        )

        result = service.populate_time_estimates(plan)

        assert result.schedule[0].estimated_minutes == 90
        assert result.schedule[1].estimated_minutes == 60

    def test_populate_preserves_existing_estimates(self, service):
        """Should not overwrite existing estimates."""
        plan = Plan(
            schedule=[
                ScheduleItem(time="09:00-10:00", task="Task", estimated_minutes=45),
            ],
            priorities=["Test"],
            notes="",
        )

        result = service.populate_time_estimates(plan)

        # Existing estimate preserved
        assert result.schedule[0].estimated_minutes == 45


class TestValidateTrackingData:
    """Tests for validate_tracking_data method."""

    def test_validate_tracking_no_warnings_for_clean_plan(self, service):
        """Clean plan should have no tracking warnings."""
        plan = PlanFactory.create()
        is_valid, warnings = service.validate_tracking_data(plan)

        assert is_valid is True
        assert warnings == []

    def test_validate_tracking_returns_tuple(self, service):
        """Should return tuple of (bool, list)."""
        plan = Plan(
            schedule=[
                ScheduleItem(
                    time="09:00-10:00",
                    task="Task",
                    status=TaskStatus.completed,
                ),
            ],
            priorities=["Test"],
            notes="",
        )

        is_valid, warnings = service.validate_tracking_data(plan)

        assert isinstance(is_valid, bool)
        assert isinstance(warnings, list)


class TestUpdatePlanningHistory:
    """Tests for update_planning_history method."""

    def test_updates_session_count(self, service, sample_memory, sample_profile):
        """Should increment sessions_completed."""
        initial_count = sample_profile.planning_history.sessions_completed

        updated = service.update_planning_history(sample_profile, sample_memory, "2026-01-23")

        assert updated.planning_history.sessions_completed == initial_count + 1

    def test_updates_last_session_date(self, service, sample_memory, sample_profile):
        """Should update last_session_date."""
        updated = service.update_planning_history(sample_profile, sample_memory, "2026-01-23")

        assert updated.planning_history.last_session_date == "2026-01-23"

    def test_updates_last_updated_timestamp(self, service, sample_memory, sample_profile):
        """Should update profile's last_updated timestamp."""
        before = sample_profile.last_updated

        updated = service.update_planning_history(sample_profile, sample_memory, "2026-01-23")

        assert updated.last_updated >= before

    def test_extracts_adjustments_from_feedback(self, service, sample_profile):
        """Should extract adjustments from feedback messages."""
        plan = PlanFactory.create()
        memory = Memory(
            metadata=SessionMetadata(
                session_id="2026-01-23",
                created_at=datetime.now(),
                last_updated=datetime.now(),
            ),
            agent_state=AgentState(state=State.done, plan=plan),
            conversation=ConversationHistory(
                messages=[
                    Message(role=MessageRole.user, content="Plan my day"),
                    Message(role=MessageRole.assistant, content="Here's your plan"),
                    Message(
                        role=MessageRole.user, content="I need more time for feedback on the PR"
                    ),
                ]
            ),
        )

        updated = service.update_planning_history(sample_profile, memory, "2026-01-23")

        # Should have extracted an adjustment about more time
        assert any("time" in adj.lower() for adj in updated.planning_history.common_adjustments)


class TestExtractSuccessfulPattern:
    """Tests for _extract_successful_pattern method."""

    def test_extract_few_long_tasks_pattern(self, service):
        """Should identify 'fewer tasks with longer blocks' pattern."""
        plan = Plan(
            schedule=[
                ScheduleItem(time="09:00-11:00", task="Task 1"),  # 120 min
                ScheduleItem(time="11:00-13:00", task="Task 2"),  # 120 min
            ],
            priorities=["Test"],
            notes="",
        )

        memory = Memory(
            metadata=SessionMetadata(
                session_id="test",
                created_at=datetime.now(),
                last_updated=datetime.now(),
            ),
            agent_state=AgentState(state=State.done, plan=plan),
            conversation=ConversationHistory(),
        )

        pattern = service._extract_successful_pattern(memory)

        assert "longer" in pattern.lower() or "fewer" in pattern.lower()

    def test_extract_many_short_tasks_pattern(self, service):
        """Should identify 'many short tasks' pattern."""
        plan = Plan(
            schedule=[
                ScheduleItem(
                    time=f"{9 + i // 3:02d}:{(i % 3) * 20:02d}-{9 + i // 3:02d}:{(i % 3) * 20 + 20:02d}",
                    task=f"Task {i}",
                )
                for i in range(9)  # 9 tasks, 20 min each
            ],
            priorities=["Test"],
            notes="",
        )

        memory = Memory(
            metadata=SessionMetadata(
                session_id="test",
                created_at=datetime.now(),
                last_updated=datetime.now(),
            ),
            agent_state=AgentState(state=State.done, plan=plan),
            conversation=ConversationHistory(),
        )

        pattern = service._extract_successful_pattern(memory)

        assert "many" in pattern.lower() or "short" in pattern.lower()

    def test_extract_returns_empty_for_no_plan(self, service):
        """Should return empty string if no plan."""
        memory = Memory(
            metadata=SessionMetadata(
                session_id="test",
                created_at=datetime.now(),
                last_updated=datetime.now(),
            ),
            agent_state=AgentState(state=State.idle, plan=None),
            conversation=ConversationHistory(),
        )

        pattern = service._extract_successful_pattern(memory)

        assert pattern == ""


class TestExtractCommonAdjustments:
    """Tests for _extract_common_adjustments method."""

    def test_extract_more_time_adjustment(self, service):
        """Should detect 'needs more time' adjustment."""
        memory = Memory(
            metadata=SessionMetadata(
                session_id="test",
                created_at=datetime.now(),
                last_updated=datetime.now(),
            ),
            agent_state=AgentState(state=State.done),
            conversation=ConversationHistory(
                messages=[
                    Message(role=MessageRole.user, content="I need more time for the meeting"),
                ]
            ),
        )

        adjustments = service._extract_common_adjustments(memory)

        assert any("more time" in adj.lower() for adj in adjustments)

    def test_extract_less_time_adjustment(self, service):
        """Should detect 'shorter duration' adjustment."""
        memory = Memory(
            metadata=SessionMetadata(
                session_id="test",
                created_at=datetime.now(),
                last_updated=datetime.now(),
            ),
            agent_state=AgentState(state=State.done),
            conversation=ConversationHistory(
                messages=[
                    Message(role=MessageRole.user, content="Make the standup shorter"),
                ]
            ),
        )

        adjustments = service._extract_common_adjustments(memory)

        assert any("shorter" in adj.lower() for adj in adjustments)

    def test_extract_break_adjustment(self, service):
        """Should detect break adjustment."""
        memory = Memory(
            metadata=SessionMetadata(
                session_id="test",
                created_at=datetime.now(),
                last_updated=datetime.now(),
            ),
            agent_state=AgentState(state=State.done),
            conversation=ConversationHistory(
                messages=[
                    Message(role=MessageRole.user, content="Add a break between meetings"),
                ]
            ),
        )

        adjustments = service._extract_common_adjustments(memory)

        assert any("break" in adj.lower() for adj in adjustments)

    def test_extract_priority_adjustment(self, service):
        """Should detect priority adjustment."""
        memory = Memory(
            metadata=SessionMetadata(
                session_id="test",
                created_at=datetime.now(),
                last_updated=datetime.now(),
            ),
            agent_state=AgentState(state=State.done),
            conversation=ConversationHistory(
                messages=[
                    Message(role=MessageRole.user, content="This is more important, prioritize it"),
                ]
            ),
        )

        adjustments = service._extract_common_adjustments(memory)

        assert any("priorit" in adj.lower() for adj in adjustments)

    def test_extract_timing_adjustment(self, service):
        """Should detect timing/order adjustment."""
        memory = Memory(
            metadata=SessionMetadata(
                session_id="test",
                created_at=datetime.now(),
                last_updated=datetime.now(),
            ),
            agent_state=AgentState(state=State.done),
            conversation=ConversationHistory(
                messages=[
                    Message(role=MessageRole.user, content="Move the meeting earlier"),
                ]
            ),
        )

        adjustments = service._extract_common_adjustments(memory)

        assert any("timing" in adj.lower() or "order" in adj.lower() for adj in adjustments)

    def test_extract_no_adjustments_for_empty_conversation(self, service):
        """Should return empty list for no feedback."""
        memory = Memory(
            metadata=SessionMetadata(
                session_id="test",
                created_at=datetime.now(),
                last_updated=datetime.now(),
            ),
            agent_state=AgentState(state=State.done),
            conversation=ConversationHistory(),
        )

        adjustments = service._extract_common_adjustments(memory)

        assert adjustments == []
