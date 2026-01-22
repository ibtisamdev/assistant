"""Tests for TaskImportService."""

import pytest
from datetime import datetime, timedelta
from src.domain.services.task_import_service import TaskImportService
from src.domain.models.planning import Plan, ScheduleItem, TaskStatus, TaskCategory
from src.domain.models.session import Memory, AgentState, SessionMetadata
from src.domain.models.conversation import ConversationHistory
from src.domain.models.state import State


@pytest.fixture
def service():
    """Create task import service."""
    return TaskImportService()


@pytest.fixture
def sample_item():
    """Create a sample schedule item."""
    return ScheduleItem(
        time="09:00-10:00",
        task="Write report",
        estimated_minutes=60,
        priority="high",
        status=TaskStatus.not_started,
        category=TaskCategory.productive,
    )


@pytest.fixture
def sample_plan():
    """Create a sample plan with various task statuses."""
    return Plan(
        schedule=[
            ScheduleItem(
                time="09:00-10:00",
                task="Morning standup",
                estimated_minutes=30,
                status=TaskStatus.completed,
            ),
            ScheduleItem(
                time="10:00-12:00",
                task="Deep work session",
                estimated_minutes=120,
                status=TaskStatus.not_started,
            ),
            ScheduleItem(
                time="13:00-14:00",
                task="Team meeting",
                estimated_minutes=60,
                status=TaskStatus.in_progress,
                actual_start=datetime.now() - timedelta(minutes=30),
            ),
            ScheduleItem(
                time="14:00-15:00",
                task="Code review",
                estimated_minutes=60,
                status=TaskStatus.skipped,
            ),
        ],
        priorities=["Complete project"],
        notes="Test plan",
    )


@pytest.fixture
def sample_memory(sample_plan):
    """Create a sample memory with a plan."""
    return Memory(
        metadata=SessionMetadata(
            session_id="2026-01-20",
            created_at=datetime.now(),
            last_updated=datetime.now(),
        ),
        agent_state=AgentState(
            state=State.done,
            plan=sample_plan,
        ),
        conversation=ConversationHistory(),
    )


class TestGetIncompleteTasks:
    """Tests for getting incomplete tasks."""

    def test_get_incomplete_tasks(self, service, sample_memory):
        """Test getting incomplete tasks from a session."""
        incomplete = service.get_incomplete_tasks(sample_memory)

        assert len(incomplete) == 2
        assert incomplete[0].task == "Deep work session"
        assert incomplete[1].task == "Team meeting"

    def test_get_incomplete_tasks_empty_plan(self, service):
        """Test with empty plan."""
        memory = Memory(
            metadata=SessionMetadata(session_id="2026-01-20"),
            agent_state=AgentState(state=State.idle, plan=None),
            conversation=ConversationHistory(),
        )

        incomplete = service.get_incomplete_tasks(memory)
        assert len(incomplete) == 0

    def test_get_incomplete_tasks_all_completed(self, service, sample_memory):
        """Test with all tasks completed."""
        for task in sample_memory.agent_state.plan.schedule:
            task.status = TaskStatus.completed

        incomplete = service.get_incomplete_tasks(sample_memory)
        assert len(incomplete) == 0


class TestGetSkippedTasks:
    """Tests for getting skipped tasks."""

    def test_get_skipped_tasks(self, service, sample_memory):
        """Test getting skipped tasks."""
        skipped = service.get_skipped_tasks(sample_memory)

        assert len(skipped) == 1
        assert skipped[0].task == "Code review"

    def test_get_skipped_tasks_none_skipped(self, service, sample_memory):
        """Test when no tasks are skipped."""
        sample_memory.agent_state.plan.schedule[3].status = TaskStatus.not_started

        skipped = service.get_skipped_tasks(sample_memory)
        assert len(skipped) == 0


class TestPrepareTaskForImport:
    """Tests for preparing tasks for import."""

    def test_prepare_task_resets_status(self, service):
        """Test that task status is reset."""
        task = ScheduleItem(
            time="09:00-10:00",
            task="Test task",
            status=TaskStatus.in_progress,
            actual_start=datetime.now(),
            actual_end=datetime.now(),
            edits=[],
        )

        prepared = service.prepare_task_for_import(task)

        assert prepared.status == TaskStatus.not_started
        assert prepared.actual_start is None
        assert prepared.actual_end is None
        assert len(prepared.edits) == 0

    def test_prepare_task_preserves_properties(self, service):
        """Test that task properties are preserved."""
        task = ScheduleItem(
            time="09:00-10:00",
            task="Test task",
            estimated_minutes=60,
            priority="high",
            category=TaskCategory.productive,
            status=TaskStatus.completed,
        )

        prepared = service.prepare_task_for_import(task)

        assert prepared.time == "09:00-10:00"
        assert prepared.task == "Test task"
        assert prepared.estimated_minutes == 60
        assert prepared.priority == "high"
        assert prepared.category == TaskCategory.productive


class TestPrepareTasksForImport:
    """Tests for preparing multiple tasks."""

    def test_prepare_multiple_tasks(self, service, sample_memory):
        """Test preparing multiple tasks."""
        incomplete = service.get_incomplete_tasks(sample_memory)
        prepared = service.prepare_tasks_for_import(incomplete)

        assert len(prepared) == 2
        for task in prepared:
            assert task.status == TaskStatus.not_started
            assert task.actual_start is None


class TestFormatTasksForContext:
    """Tests for formatting tasks for LLM context."""

    def test_format_tasks_for_context(self, service, sample_memory):
        """Test formatting tasks for context injection."""
        incomplete = service.get_incomplete_tasks(sample_memory)
        context = service.format_tasks_for_context(incomplete, "2026-01-20")

        assert "Incomplete tasks from 2026-01-20" in context
        assert "Deep work session" in context
        assert "Team meeting" in context

    def test_format_empty_tasks(self, service):
        """Test formatting empty task list."""
        context = service.format_tasks_for_context([], "2026-01-20")
        assert context == ""


class TestFormatTasksForDisplay:
    """Tests for formatting tasks for CLI display."""

    def test_format_tasks_for_display(self, service, sample_memory):
        """Test formatting tasks for display."""
        incomplete = service.get_incomplete_tasks(sample_memory)
        display = service.format_tasks_for_display(incomplete)

        assert len(display) == 2
        assert display[0]["index"] == 1
        assert display[0]["task"] == "Deep work session"
        assert display[0]["status"] == "not_started"


class TestMergeImportedWithPlan:
    """Tests for merging imported tasks with existing plan."""

    def test_merge_at_start(self, service, sample_plan):
        """Test merging at start of plan."""
        imported = [ScheduleItem(time="08:00-09:00", task="Imported task", estimated_minutes=60)]

        merged = service.merge_imported_with_plan(imported, sample_plan, position="start")

        assert len(merged.schedule) == 5
        assert merged.schedule[0].task == "Imported task"

    def test_merge_at_end(self, service, sample_plan):
        """Test merging at end of plan."""
        imported = [ScheduleItem(time="16:00-17:00", task="Imported task", estimated_minutes=60)]

        merged = service.merge_imported_with_plan(imported, sample_plan, position="end")

        assert len(merged.schedule) == 5
        assert merged.schedule[-1].task == "Imported task"


class TestGetYesterdaySessionId:
    """Tests for getting yesterday's session ID."""

    def test_get_yesterday_from_date(self, service):
        """Test getting yesterday's session ID from a date."""
        yesterday = service.get_yesterday_session_id("2026-01-22")
        assert yesterday == "2026-01-21"

    def test_get_yesterday_handles_month_boundary(self, service):
        """Test handling month boundary."""
        yesterday = service.get_yesterday_session_id("2026-02-01")
        assert yesterday == "2026-01-31"


class TestSummarizeImportCandidates:
    """Tests for summarizing import candidates."""

    def test_summarize_candidates(self, service, sample_memory):
        """Test summarizing import candidates."""
        incomplete = service.get_incomplete_tasks(sample_memory)
        skipped = service.get_skipped_tasks(sample_memory)

        summary = service.summarize_import_candidates(incomplete, skipped)

        assert summary["incomplete_count"] == 2
        assert summary["skipped_count"] == 1
        assert summary["total_count"] == 3
        assert summary["has_candidates"] is True

    def test_summarize_no_candidates(self, service):
        """Test summary when no candidates."""
        summary = service.summarize_import_candidates([], [])

        assert summary["incomplete_count"] == 0
        assert summary["skipped_count"] == 0
        assert summary["has_candidates"] is False
