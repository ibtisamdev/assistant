"""Tests for CreatePlanUseCase."""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from src.application.use_cases.create_plan import CreatePlanUseCase
from src.domain.models.session import AgentState
from src.domain.models.state import State
from tests.conftest import (
    MemoryFactory,
    MockInputHandler,
    MockStorage,
    PlanFactory,
    UserProfileFactory,
)


class TestCreatePlanUseCaseInitialization:
    """Test CreatePlanUseCase initialization."""

    def test_init_with_container(self):
        """Test use case can be initialized with a container."""
        mock_container = MagicMock()
        mock_container.agent_service = MagicMock()
        mock_container.storage = MockStorage()
        mock_container.input_handler = MockInputHandler()
        mock_container.plan_formatter = MagicMock()
        mock_container.progress_formatter = MagicMock()

        use_case = CreatePlanUseCase(mock_container)

        assert use_case.agent == mock_container.agent_service
        assert use_case.storage == mock_container.storage


class TestGetOrCreateSession:
    """Tests for _get_or_create_session method."""

    @pytest.fixture
    def use_case(self):
        """Create use case with mocks."""
        mock_container = MagicMock()
        mock_container.agent_service = MagicMock()
        mock_container.storage = MockStorage()
        mock_container.input_handler = MockInputHandler()
        mock_container.plan_formatter = MagicMock()
        mock_container.progress_formatter = MagicMock()
        return CreatePlanUseCase(mock_container)

    @pytest.mark.asyncio
    async def test_creates_new_session_when_none_exists(self, use_case):
        """Test creating a new session when none exists."""
        result = await use_case._get_or_create_session("2026-01-23", force_new=False)

        assert result is not None
        assert result.metadata.session_id == "2026-01-23"
        assert result.agent_state.state == State.idle

    @pytest.mark.asyncio
    async def test_loads_existing_session(self, use_case):
        """Test loading an existing session."""
        # Pre-create a session
        existing = MemoryFactory.create(session_id="2026-01-23")
        existing.agent_state.state = State.feedback
        existing.agent_state.plan = PlanFactory.create()
        await use_case.storage.save_session("2026-01-23", existing)

        result = await use_case._get_or_create_session("2026-01-23", force_new=False)

        assert result.agent_state.state == State.feedback
        assert result.agent_state.plan is not None

    @pytest.mark.asyncio
    async def test_force_new_creates_fresh_session(self, use_case):
        """Test force_new creates a fresh session even if one exists."""
        # Pre-create a session
        existing = MemoryFactory.create(session_id="2026-01-23")
        existing.agent_state.state = State.done
        await use_case.storage.save_session("2026-01-23", existing)

        result = await use_case._get_or_create_session("2026-01-23", force_new=True)

        assert result.agent_state.state == State.idle


class TestInitializeConversation:
    """Tests for _initialize_conversation method."""

    @pytest.fixture
    def use_case(self):
        """Create use case with mocks."""
        mock_container = MagicMock()
        mock_container.agent_service = MagicMock()
        mock_container.storage = MockStorage()
        mock_container.input_handler = MockInputHandler()
        mock_container.plan_formatter = MagicMock()
        mock_container.progress_formatter = MagicMock()
        return CreatePlanUseCase(mock_container)

    @pytest.mark.asyncio
    async def test_initializes_conversation(self, use_case):
        """Test initializing conversation."""
        memory = MemoryFactory.create()

        # This test verifies the method runs without error
        # The actual system prompt loading depends on file existence
        await use_case._initialize_conversation(memory)


class TestHandleQuestions:
    """Tests for _handle_questions method."""

    @pytest.fixture
    def use_case(self):
        """Create use case with mocks."""
        mock_container = MagicMock()
        mock_container.agent_service = MagicMock()
        mock_container.agent_service.process_answers = AsyncMock(
            return_value=AgentState(state=State.feedback, plan=PlanFactory.create())
        )
        mock_container.storage = MockStorage()
        mock_container.input_handler = MockInputHandler(["Answer 1", "Answer 2"])
        mock_container.plan_formatter = MagicMock()
        mock_container.plan_formatter.format_questions = MagicMock(return_value="")
        mock_container.progress_formatter = MagicMock()
        return CreatePlanUseCase(mock_container)

    @pytest.mark.asyncio
    async def test_collects_answers_for_questions(self, use_case):
        """Test that answers are collected for each question."""
        from src.domain.models.planning import Question

        memory = MemoryFactory.create()
        memory.agent_state.state = State.questions
        memory.agent_state.questions = [
            Question(question="Q1?", answer=""),
            Question(question="Q2?", answer=""),
        ]
        profile = UserProfileFactory.create()

        with patch("rich.console.Console"):
            await use_case._handle_questions(memory, "2026-01-23", profile)

        # After handling, agent transitions to feedback state
        # Questions are processed by the agent
        assert memory.agent_state.state == State.feedback


class TestHandleFeedback:
    """Tests for _handle_feedback method."""

    @pytest.fixture
    def use_case(self):
        """Create use case with mocks."""
        mock_container = MagicMock()
        mock_container.agent_service = MagicMock()
        mock_container.storage = MockStorage()
        mock_container.input_handler = MockInputHandler(["done"])  # Accept plan
        mock_container.plan_formatter = MagicMock()
        mock_container.plan_formatter.format_plan = MagicMock(return_value="")
        mock_container.progress_formatter = MagicMock()
        return CreatePlanUseCase(mock_container)

    @pytest.mark.asyncio
    async def test_accepts_plan_when_user_done(self, use_case):
        """Test that plan is accepted when user says done."""
        memory = MemoryFactory.create()
        memory.agent_state.state = State.feedback
        memory.agent_state.plan = PlanFactory.create()

        with patch("rich.console.Console"):
            await use_case._handle_feedback(memory, "2026-01-23")

        assert memory.agent_state.state == State.done


class TestUpdatePlanningHistory:
    """Tests for _update_planning_history method."""

    @pytest.fixture
    def use_case(self):
        """Create use case with mocks."""
        mock_container = MagicMock()
        mock_container.agent_service = MagicMock()
        mock_container.storage = MockStorage()
        mock_container.input_handler = MockInputHandler()
        mock_container.plan_formatter = MagicMock()
        mock_container.progress_formatter = MagicMock()
        return CreatePlanUseCase(mock_container)

    @pytest.mark.asyncio
    async def test_updates_profile_history(self, use_case):
        """Test that profile planning history is updated."""
        memory = MemoryFactory.create(session_id="2026-01-23")
        memory.agent_state.state = State.done
        memory.agent_state.plan = PlanFactory.create()
        profile = UserProfileFactory.create()

        await use_case._update_planning_history(profile, memory, "2026-01-23")

        # Verify profile was saved
        assert use_case.storage.profiles.get(profile.user_id) is not None


class TestCheckAndPromptIncompleteTasks:
    """Tests for _check_and_prompt_incomplete_tasks method."""

    @pytest.fixture
    def use_case(self):
        """Create use case with mocks."""
        mock_container = MagicMock()
        mock_container.agent_service = MagicMock()
        mock_container.storage = MockStorage()
        mock_container.input_handler = MockInputHandler()
        mock_container.plan_formatter = MagicMock()
        mock_container.progress_formatter = MagicMock()
        return CreatePlanUseCase(mock_container)

    @pytest.mark.asyncio
    async def test_returns_empty_when_no_yesterday_session(self, use_case):
        """Test returns empty string when no yesterday session exists."""
        with patch("rich.console.Console"):
            result = await use_case._check_and_prompt_incomplete_tasks("2026-01-23")

        assert result == ""

    @pytest.mark.asyncio
    async def test_returns_empty_when_yesterday_has_no_plan(self, use_case):
        """Test returns empty when yesterday has no plan."""
        # Create yesterday's session without a plan
        yesterday = MemoryFactory.create(session_id="2026-01-22")
        await use_case.storage.save_session("2026-01-22", yesterday)

        with patch("rich.console.Console"):
            result = await use_case._check_and_prompt_incomplete_tasks("2026-01-23")

        assert result == ""
