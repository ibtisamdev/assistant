"""Tests for CheckinUseCase - time tracking workflow."""

from datetime import datetime
from unittest.mock import MagicMock, patch

import pytest

from src.application.use_cases.checkin import CheckinUseCase
from src.domain.exceptions import SessionNotFound
from src.domain.models.planning import TaskCategory, TaskStatus
from tests.conftest import (
    MemoryFactory,
    MockStorage,
    PlanFactory,
    create_plan_with_tasks,
)


class TestCheckinUseCaseInitialization:
    """Test CheckinUseCase initialization."""

    def test_init_with_container(self):
        """Test use case can be initialized with a container."""
        mock_container = MagicMock()
        mock_container.storage = MockStorage()
        mock_container.plan_formatter = MagicMock()

        use_case = CheckinUseCase(mock_container)

        assert use_case.storage == mock_container.storage


class TestCheckinExecute:
    """Tests for execute method."""

    @pytest.fixture
    def use_case(self):
        """Create use case with mocks."""
        mock_container = MagicMock()
        mock_container.storage = MockStorage()
        mock_container.plan_formatter = MagicMock()
        return CheckinUseCase(mock_container)

    @pytest.mark.asyncio
    async def test_raises_when_no_session(self, use_case):
        """Test that SessionNotFound is raised when no session exists."""
        with pytest.raises(SessionNotFound):
            await use_case.execute("nonexistent")

    @pytest.mark.asyncio
    async def test_raises_when_no_plan(self, use_case):
        """Test that SessionNotFound is raised when session has no plan."""
        memory = MemoryFactory.create(session_id="2026-01-23")
        memory.agent_state.plan = None
        await use_case.storage.save_session("2026-01-23", memory)

        with pytest.raises(SessionNotFound):
            await use_case.execute("2026-01-23")

    @pytest.mark.asyncio
    async def test_show_status_only(self, use_case):
        """Test show_status_only mode returns without interaction."""
        memory = MemoryFactory.create(session_id="2026-01-23")
        memory.agent_state.plan = PlanFactory.create()
        await use_case.storage.save_session("2026-01-23", memory)

        with patch.object(use_case, "_display_plan_with_progress"):
            with patch.object(use_case, "_display_stats"):
                result = await use_case.execute("2026-01-23", show_status_only=True)

        assert result is not None
        assert result.agent_state.plan is not None


class TestQuickActions:
    """Tests for quick action methods."""

    @pytest.fixture
    def use_case_with_plan(self):
        """Create use case with a pre-populated session."""
        mock_container = MagicMock()
        storage = MockStorage()
        mock_container.storage = storage
        mock_container.plan_formatter = MagicMock()

        # Create a session with a plan
        memory = MemoryFactory.create(session_id="2026-01-23")
        memory.agent_state.plan = create_plan_with_tasks(
            [
                {
                    "time": "09:00-10:00",
                    "task": "Morning routine",
                    "status": TaskStatus.not_started,
                },
                {"time": "10:00-12:00", "task": "Deep work", "status": TaskStatus.not_started},
                {"time": "14:00-16:00", "task": "Meetings", "status": TaskStatus.not_started},
            ]
        )

        use_case = CheckinUseCase(mock_container)

        return use_case, memory, storage

    @pytest.mark.asyncio
    async def test_quick_start_task(self, use_case_with_plan):
        """Test quick start a task by name."""
        use_case, memory, storage = use_case_with_plan
        await storage.save_session("2026-01-23", memory)

        with patch.object(use_case.console, "print"):
            await use_case._quick_start_task(memory, "Morning routine")

        # Verify task was started
        task = memory.agent_state.plan.schedule[0]
        assert task.status == TaskStatus.in_progress
        assert task.actual_start is not None

    @pytest.mark.asyncio
    async def test_quick_complete_task(self, use_case_with_plan):
        """Test quick complete a task by name."""
        use_case, memory, storage = use_case_with_plan
        # First start the task
        memory.agent_state.plan.schedule[0].status = TaskStatus.in_progress
        memory.agent_state.plan.schedule[0].actual_start = datetime.now()
        await storage.save_session("2026-01-23", memory)

        with patch.object(use_case.console, "print"):
            await use_case._quick_complete_task(memory, "Morning routine")

        # Verify task was completed
        task = memory.agent_state.plan.schedule[0]
        assert task.status == TaskStatus.completed
        assert task.actual_end is not None

    @pytest.mark.asyncio
    async def test_quick_skip_task(self, use_case_with_plan):
        """Test quick skip a task by name."""
        use_case, memory, storage = use_case_with_plan
        await storage.save_session("2026-01-23", memory)

        with patch.object(use_case.console, "print"):
            await use_case._quick_skip_task(memory, "Meetings")

        # Verify task was skipped
        task = memory.agent_state.plan.schedule[2]
        assert task.status == TaskStatus.skipped

    @pytest.mark.asyncio
    async def test_quick_start_nonexistent_task(self, use_case_with_plan):
        """Test quick start with nonexistent task name."""
        use_case, memory, storage = use_case_with_plan
        await storage.save_session("2026-01-23", memory)

        with patch.object(use_case.console, "print") as mock_print:
            await use_case._quick_start_task(memory, "Nonexistent task")

        # Should print error message
        mock_print.assert_called()
        call_args = str(mock_print.call_args)
        assert "not found" in call_args.lower()


class TestDisplayMethods:
    """Tests for display helper methods."""

    @pytest.fixture
    def use_case(self):
        """Create use case with mocks."""
        mock_container = MagicMock()
        mock_container.storage = MockStorage()
        mock_container.plan_formatter = MagicMock()
        return CheckinUseCase(mock_container)

    def test_display_plan_with_progress(self, use_case):
        """Test plan display with progress indicators."""
        plan = create_plan_with_tasks(
            [
                {"time": "09:00-10:00", "task": "Task 1", "status": TaskStatus.completed},
                {"time": "10:00-12:00", "task": "Task 2", "status": TaskStatus.in_progress},
                {"time": "14:00-16:00", "task": "Task 3", "status": TaskStatus.not_started},
            ]
        )

        with patch.object(use_case.console, "print"):
            # Should not raise
            use_case._display_plan_with_progress(plan)

    def test_display_stats(self, use_case):
        """Test stats display."""
        plan = create_plan_with_tasks(
            [
                {
                    "time": "09:00-10:00",
                    "task": "Task 1",
                    "status": TaskStatus.completed,
                    "estimated_minutes": 60,
                    "actual_minutes": 55,
                },
                {
                    "time": "10:00-12:00",
                    "task": "Task 2",
                    "status": TaskStatus.in_progress,
                    "estimated_minutes": 120,
                },
            ]
        )

        with patch.object(use_case.console, "print"):
            # Should not raise
            use_case._display_stats(plan)


class TestInteractiveMethods:
    """Tests for interactive methods."""

    @pytest.fixture
    def use_case_with_plan(self):
        """Create use case with a pre-populated session."""
        mock_container = MagicMock()
        storage = MockStorage()
        mock_container.storage = storage
        mock_container.plan_formatter = MagicMock()

        memory = MemoryFactory.create(session_id="2026-01-23")
        memory.agent_state.plan = create_plan_with_tasks(
            [
                {"time": "09:00-10:00", "task": "Task 1", "status": TaskStatus.not_started},
                {"time": "10:00-12:00", "task": "Task 2", "status": TaskStatus.not_started},
            ]
        )

        use_case = CheckinUseCase(mock_container)

        return use_case, memory, storage

    @pytest.mark.asyncio
    async def test_interactive_start_task(self, use_case_with_plan):
        """Test interactive task start."""
        use_case, memory, storage = use_case_with_plan
        await storage.save_session("2026-01-23", memory)

        with patch.object(use_case.console, "print"):
            with patch("src.application.use_cases.checkin.Prompt") as mock_prompt:
                mock_prompt.ask.return_value = "1"  # Select first task
                await use_case._interactive_start_task(memory)

        # Verify first task was started
        assert memory.agent_state.plan.schedule[0].status == TaskStatus.in_progress

    @pytest.mark.asyncio
    async def test_interactive_complete_task(self, use_case_with_plan):
        """Test interactive task completion."""
        use_case, memory, storage = use_case_with_plan
        # Start a task first
        memory.agent_state.plan.schedule[0].status = TaskStatus.in_progress
        memory.agent_state.plan.schedule[0].actual_start = datetime.now()
        await storage.save_session("2026-01-23", memory)

        with patch.object(use_case.console, "print"):
            with patch("src.application.use_cases.checkin.Confirm") as mock_confirm:
                mock_confirm.ask.return_value = True
                await use_case._interactive_complete_task(memory)

        # Verify task was completed
        assert memory.agent_state.plan.schedule[0].status == TaskStatus.completed

    @pytest.mark.asyncio
    async def test_interactive_skip_task(self, use_case_with_plan):
        """Test interactive task skip."""
        use_case, memory, storage = use_case_with_plan
        await storage.save_session("2026-01-23", memory)

        with patch.object(use_case.console, "print"):
            with patch("src.application.use_cases.checkin.Prompt") as mock_prompt:
                mock_prompt.ask.side_effect = ["1", ""]  # Select first task, no reason
                await use_case._interactive_skip_task(memory)

        # Verify task was skipped
        assert memory.agent_state.plan.schedule[0].status == TaskStatus.skipped


class TestCategoryEditing:
    """Tests for category editing functionality."""

    @pytest.fixture
    def use_case_with_plan(self):
        """Create use case with a pre-populated session."""
        mock_container = MagicMock()
        storage = MockStorage()
        mock_container.storage = storage
        mock_container.plan_formatter = MagicMock()

        memory = MemoryFactory.create(session_id="2026-01-23")
        memory.agent_state.plan = create_plan_with_tasks(
            [
                {"time": "09:00-10:00", "task": "Task 1", "category": TaskCategory.uncategorized},
                {"time": "10:00-12:00", "task": "Task 2", "category": TaskCategory.uncategorized},
            ]
        )

        use_case = CheckinUseCase(mock_container)

        return use_case, memory, storage

    @pytest.mark.asyncio
    async def test_edit_single_task_category(self, use_case_with_plan):
        """Test editing a single task's category."""
        use_case, memory, storage = use_case_with_plan
        await storage.save_session("2026-01-23", memory)

        with patch.object(use_case.console, "print"):
            with patch("src.application.use_cases.checkin.Prompt") as mock_prompt:
                mock_prompt.ask.side_effect = [
                    "1",
                    "productive",
                ]  # Select task 1, set to productive
                await use_case._interactive_edit_categories(memory)

        # Verify category was changed
        assert memory.agent_state.plan.schedule[0].category == TaskCategory.productive

    @pytest.mark.asyncio
    async def test_edit_all_task_categories(self, use_case_with_plan):
        """Test editing all tasks' categories at once."""
        use_case, memory, storage = use_case_with_plan
        await storage.save_session("2026-01-23", memory)

        with patch.object(use_case.console, "print"):
            with patch("src.application.use_cases.checkin.Prompt") as mock_prompt:
                mock_prompt.ask.side_effect = ["all", "meetings"]  # All tasks, set to meetings
                await use_case._interactive_edit_categories(memory)

        # Verify all categories were changed
        assert memory.agent_state.plan.schedule[0].category == TaskCategory.meetings
        assert memory.agent_state.plan.schedule[1].category == TaskCategory.meetings
