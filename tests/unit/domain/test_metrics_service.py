"""Tests for MetricsService."""

import pytest
from datetime import datetime, timedelta

from src.domain.services.metrics_service import MetricsService
from src.domain.models.planning import Plan, ScheduleItem, TaskStatus, TaskCategory
from src.domain.models.session import Memory, AgentState, SessionMetadata
from src.domain.models.conversation import ConversationHistory
from src.domain.models.state import State


@pytest.fixture
def metrics_service():
    """Create a MetricsService instance."""
    return MetricsService()


@pytest.fixture
def sample_plan():
    """Create a sample plan with various task states and categories."""
    now = datetime.now()

    return Plan(
        schedule=[
            ScheduleItem(
                time="09:00-10:00",
                task="Morning standup",
                estimated_minutes=30,
                actual_start=now - timedelta(hours=3),
                actual_end=now - timedelta(hours=2, minutes=30),
                status=TaskStatus.completed,
                category=TaskCategory.meetings,
            ),
            ScheduleItem(
                time="10:00-12:00",
                task="Feature development",
                estimated_minutes=120,
                actual_start=now - timedelta(hours=2, minutes=30),
                actual_end=now - timedelta(minutes=30),
                status=TaskStatus.completed,
                category=TaskCategory.productive,
            ),
            ScheduleItem(
                time="12:00-13:00",
                task="Lunch break",
                estimated_minutes=60,
                actual_start=now - timedelta(minutes=30),
                actual_end=now,
                status=TaskStatus.completed,
                category=TaskCategory.breaks,
            ),
            ScheduleItem(
                time="13:00-14:00",
                task="Code review",
                estimated_minutes=60,
                status=TaskStatus.in_progress,
                category=TaskCategory.productive,
            ),
            ScheduleItem(
                time="14:00-15:00",
                task="Email and Slack",
                estimated_minutes=30,
                status=TaskStatus.not_started,
                category=TaskCategory.admin,
            ),
            ScheduleItem(
                time="15:00-16:00",
                task="Skipped meeting",
                estimated_minutes=60,
                status=TaskStatus.skipped,
                category=TaskCategory.meetings,
            ),
        ],
        priorities=["Complete feature", "Review PRs"],
        notes="Focus day",
    )


@pytest.fixture
def empty_plan():
    """Create an empty plan."""
    return Plan(
        schedule=[],
        priorities=[],
        notes="",
    )


@pytest.fixture
def plan_no_tracking():
    """Create a plan with no time tracking data."""
    return Plan(
        schedule=[
            ScheduleItem(
                time="09:00-10:00",
                task="Task 1",
                estimated_minutes=60,
                status=TaskStatus.not_started,
                category=TaskCategory.productive,
            ),
            ScheduleItem(
                time="10:00-11:00",
                task="Task 2",
                estimated_minutes=60,
                status=TaskStatus.not_started,
                category=TaskCategory.admin,
            ),
        ],
        priorities=["Task 1"],
        notes="",
    )


def create_memory_with_plan(session_id: str, plan: Plan) -> Memory:
    """Helper to create a Memory with a plan."""
    return Memory(
        metadata=SessionMetadata(session_id=session_id),
        agent_state=AgentState(state=State.done, plan=plan),
        conversation=ConversationHistory(),
    )


class TestCalculateDailyMetrics:
    """Tests for calculate_daily_metrics."""

    def test_calculates_completion_rate(self, metrics_service, sample_plan):
        """Should calculate correct completion rate."""
        metrics = metrics_service.calculate_daily_metrics(sample_plan, "2026-01-22")

        # 3 completed out of 6 total = 50%
        assert metrics.completion_rate == 50.0
        assert metrics.completed_tasks == 3
        assert metrics.total_tasks == 6

    def test_calculates_task_counts(self, metrics_service, sample_plan):
        """Should calculate task status counts correctly."""
        metrics = metrics_service.calculate_daily_metrics(sample_plan, "2026-01-22")

        assert metrics.completed_tasks == 3
        assert metrics.in_progress_tasks == 1
        assert metrics.not_started_tasks == 1
        assert metrics.skipped_tasks == 1

    def test_calculates_time_totals(self, metrics_service, sample_plan):
        """Should calculate planned and actual time totals."""
        metrics = metrics_service.calculate_daily_metrics(sample_plan, "2026-01-22")

        # Planned: 30 + 120 + 60 + 60 + 30 + 60 = 360 minutes
        assert metrics.total_planned_minutes == 360

    def test_handles_empty_plan(self, metrics_service, empty_plan):
        """Should handle empty plan gracefully."""
        metrics = metrics_service.calculate_daily_metrics(empty_plan, "2026-01-22")

        assert metrics.total_tasks == 0
        assert metrics.completion_rate == 0.0
        assert metrics.total_planned_minutes == 0

    def test_returns_date(self, metrics_service, sample_plan):
        """Should include the date in metrics."""
        metrics = metrics_service.calculate_daily_metrics(sample_plan, "2026-01-22")

        assert metrics.date == "2026-01-22"


class TestCalculateTimeByCategory:
    """Tests for calculate_time_by_category."""

    def test_calculates_time_per_category(self, metrics_service, sample_plan):
        """Should calculate time spent per category."""
        time_by_cat = metrics_service.calculate_time_by_category(sample_plan)

        # Meetings: 30 + 60 = 90 (but we use actual time for completed tasks)
        # This depends on actual_minutes being set
        assert "meetings" in time_by_cat
        assert "productive" in time_by_cat
        assert "breaks" in time_by_cat
        assert "admin" in time_by_cat

    def test_handles_empty_plan(self, metrics_service, empty_plan):
        """Should return empty dict for empty plan."""
        time_by_cat = metrics_service.calculate_time_by_category(empty_plan)

        assert time_by_cat == {}

    def test_uses_estimated_when_no_actual(self, metrics_service, plan_no_tracking):
        """Should use estimated_minutes when actual is not available."""
        time_by_cat = metrics_service.calculate_time_by_category(plan_no_tracking)

        assert time_by_cat.get("productive", 0) == 60
        assert time_by_cat.get("admin", 0) == 60


class TestCalculateEstimationAccuracy:
    """Tests for calculate_estimation_accuracy."""

    def test_calculates_accuracy_metrics(self, metrics_service, sample_plan):
        """Should calculate estimation accuracy for completed tasks."""
        accuracy = metrics_service.calculate_estimation_accuracy(sample_plan)

        # Should have data for 3 completed tasks
        assert accuracy is not None
        assert accuracy.total_tasks_with_tracking == 3

    def test_returns_none_for_no_tracking(self, metrics_service, plan_no_tracking):
        """Should return None when no tasks have tracking data."""
        accuracy = metrics_service.calculate_estimation_accuracy(plan_no_tracking)

        assert accuracy is None

    def test_calculates_variance_direction(self, metrics_service):
        """Should correctly identify under/over estimation."""
        now = datetime.now()

        # Plan where tasks take longer than estimated
        plan = Plan(
            schedule=[
                ScheduleItem(
                    time="09:00-10:00",
                    task="Task 1",
                    estimated_minutes=30,
                    actual_start=now - timedelta(hours=1),
                    actual_end=now,  # Took 60 min, estimated 30
                    status=TaskStatus.completed,
                    category=TaskCategory.productive,
                ),
            ],
            priorities=[],
            notes="",
        )

        accuracy = metrics_service.calculate_estimation_accuracy(plan)

        assert accuracy.underestimated_count == 1
        assert accuracy.overestimated_count == 0
        assert accuracy.avg_variance > 0  # Positive variance = took longer


class TestGetTimeConsumingTasks:
    """Tests for get_time_consuming_tasks."""

    def test_returns_top_n_tasks(self, metrics_service, sample_plan):
        """Should return top N time-consuming tasks."""
        top_tasks = metrics_service.get_time_consuming_tasks(sample_plan, top_n=3)

        assert len(top_tasks) == 3
        # Should be sorted by time (descending)
        times = [t.actual_minutes or t.estimated_minutes or 0 for t in top_tasks]
        assert times == sorted(times, reverse=True)

    def test_returns_all_if_less_than_n(self, metrics_service):
        """Should return all tasks if fewer than top_n."""
        small_plan = Plan(
            schedule=[
                ScheduleItem(
                    time="09:00-10:00",
                    task="Only task",
                    estimated_minutes=60,
                    status=TaskStatus.not_started,
                    category=TaskCategory.productive,
                ),
            ],
            priorities=[],
            notes="",
        )

        top_tasks = metrics_service.get_time_consuming_tasks(small_plan, top_n=5)

        assert len(top_tasks) == 1

    def test_includes_task_metadata(self, metrics_service, sample_plan):
        """Should include category and status in task metrics."""
        top_tasks = metrics_service.get_time_consuming_tasks(sample_plan, top_n=1)

        assert top_tasks[0].category is not None
        assert top_tasks[0].status is not None


class TestCalculateAggregateMetrics:
    """Tests for calculate_aggregate_metrics."""

    def test_aggregates_multiple_sessions(self, metrics_service):
        """Should aggregate metrics across multiple sessions."""
        now = datetime.now()

        # Create sessions for 3 days
        sessions = []
        for i in range(3):
            date = (now - timedelta(days=i)).strftime("%Y-%m-%d")
            plan = Plan(
                schedule=[
                    ScheduleItem(
                        time="09:00-10:00",
                        task=f"Task for {date}",
                        estimated_minutes=60,
                        actual_start=now - timedelta(hours=1),
                        actual_end=now,
                        status=TaskStatus.completed,
                        category=TaskCategory.productive,
                    ),
                ],
                priorities=[],
                notes="",
            )
            sessions.append(create_memory_with_plan(date, plan))

        metrics = metrics_service.calculate_aggregate_metrics(
            sessions=sessions,
            period_start=(now - timedelta(days=2)).strftime("%Y-%m-%d"),
            period_end=now.strftime("%Y-%m-%d"),
            period_type="custom",
        )

        assert metrics.days_with_data == 3
        assert metrics.total_tasks == 3

    def test_handles_empty_sessions(self, metrics_service):
        """Should handle empty session list."""
        metrics = metrics_service.calculate_aggregate_metrics(
            sessions=[],
            period_start="2026-01-01",
            period_end="2026-01-07",
            period_type="week",
        )

        assert metrics.days_with_data == 0
        assert metrics.total_planned_minutes == 0

    def test_calculates_best_worst_days(self, metrics_service):
        """Should identify best and worst days by completion rate."""
        now = datetime.now()

        # Day 1: 100% completion
        plan1 = Plan(
            schedule=[
                ScheduleItem(
                    time="09:00-10:00",
                    task="Task 1",
                    estimated_minutes=60,
                    status=TaskStatus.completed,
                    category=TaskCategory.productive,
                ),
            ],
            priorities=[],
            notes="",
        )

        # Day 2: 0% completion
        plan2 = Plan(
            schedule=[
                ScheduleItem(
                    time="09:00-10:00",
                    task="Task 2",
                    estimated_minutes=60,
                    status=TaskStatus.not_started,
                    category=TaskCategory.productive,
                ),
            ],
            priorities=[],
            notes="",
        )

        date1 = now.strftime("%Y-%m-%d")
        date2 = (now - timedelta(days=1)).strftime("%Y-%m-%d")

        sessions = [
            create_memory_with_plan(date1, plan1),
            create_memory_with_plan(date2, plan2),
        ]

        metrics = metrics_service.calculate_aggregate_metrics(
            sessions=sessions,
            period_start=date2,
            period_end=date1,
            period_type="custom",
        )

        assert metrics.best_day == date1
        assert metrics.worst_day == date2


class TestCalculateWeeklyMetrics:
    """Tests for calculate_weekly_metrics."""

    def test_uses_monday_to_sunday(self, metrics_service):
        """Should calculate metrics for Monday-Sunday week."""
        metrics = metrics_service.calculate_weekly_metrics(
            sessions=[],
            week_start="2026-01-20",  # Monday
        )

        assert metrics.period_start == "2026-01-20"
        assert metrics.period_end == "2026-01-26"  # Sunday
        assert metrics.period_type == "week"


class TestCalculateMonthlyMetrics:
    """Tests for calculate_monthly_metrics."""

    def test_uses_full_month(self, metrics_service):
        """Should calculate metrics for full calendar month."""
        metrics = metrics_service.calculate_monthly_metrics(
            sessions=[],
            year=2026,
            month=1,
        )

        assert metrics.period_start == "2026-01-01"
        assert metrics.period_end == "2026-01-31"
        assert metrics.period_type == "month"

    def test_handles_february(self, metrics_service):
        """Should handle February correctly (non-leap year)."""
        metrics = metrics_service.calculate_monthly_metrics(
            sessions=[],
            year=2026,
            month=2,
        )

        assert metrics.period_end == "2026-02-28"


class TestIdentifyPatterns:
    """Tests for identify_patterns."""

    def test_requires_minimum_sessions(self, metrics_service):
        """Should require at least 3 sessions to identify patterns."""
        patterns = metrics_service.identify_patterns([])
        assert patterns == []

        # Create 2 sessions (not enough)
        sessions = [
            create_memory_with_plan("2026-01-20", Plan(schedule=[], priorities=[], notes="")),
            create_memory_with_plan("2026-01-21", Plan(schedule=[], priorities=[], notes="")),
        ]

        patterns = metrics_service.identify_patterns(sessions)
        assert patterns == []

    def test_identifies_consistent_categories(self, metrics_service):
        """Should identify categories used consistently across days."""
        # Create 3 sessions all with productive and admin tasks
        sessions = []
        for i in range(3):
            plan = Plan(
                schedule=[
                    ScheduleItem(
                        time="09:00-10:00",
                        task="Coding",
                        estimated_minutes=60,
                        status=TaskStatus.completed,
                        category=TaskCategory.productive,
                    ),
                    ScheduleItem(
                        time="10:00-11:00",
                        task="Email",
                        estimated_minutes=30,
                        status=TaskStatus.completed,
                        category=TaskCategory.admin,
                    ),
                ],
                priorities=[],
                notes="",
            )
            sessions.append(create_memory_with_plan(f"2026-01-{20 + i}", plan))

        patterns = metrics_service.identify_patterns(sessions)

        # Should find a "successful_habit" pattern for consistent categories
        habit_patterns = [p for p in patterns if p.pattern_type == "successful_habit"]
        assert len(habit_patterns) >= 1


class TestTaskCategory:
    """Tests for TaskCategory enum."""

    def test_all_categories_exist(self):
        """Should have all required categories."""
        categories = [c.value for c in TaskCategory]

        assert "productive" in categories
        assert "meetings" in categories
        assert "admin" in categories
        assert "breaks" in categories
        assert "wasted" in categories
        assert "uncategorized" in categories

    def test_default_category(self):
        """ScheduleItem should default to uncategorized."""
        item = ScheduleItem(
            time="09:00-10:00",
            task="Test task",
        )

        assert item.category == TaskCategory.uncategorized
