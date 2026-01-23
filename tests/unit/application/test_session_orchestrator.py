"""Tests for session orchestrator."""

from datetime import datetime
from unittest.mock import AsyncMock, MagicMock

import pytest

from src.application.container import Container
from src.application.session_orchestrator import SessionOrchestrator
from src.domain.models.conversation import ConversationHistory
from src.domain.models.session import AgentState, Memory, SessionMetadata
from src.domain.models.state import State


@pytest.fixture
def mock_container():
    """Create mock container."""
    container = MagicMock(spec=Container)
    container.storage = AsyncMock()
    return container


@pytest.fixture
def sample_memory():
    """Create sample memory for testing."""
    return Memory(
        metadata=SessionMetadata(
            session_id="2026-01-23",
            created_at=datetime.now(),
            last_updated=datetime.now(),
        ),
        agent_state=AgentState(state=State.done),
        conversation=ConversationHistory(),
    )


class TestSessionOrchestratorInit:
    """Tests for orchestrator initialization."""

    def test_init_creates_use_cases(self, mock_container):
        """Should create use cases on initialization."""
        orchestrator = SessionOrchestrator(mock_container)

        assert orchestrator.container is mock_container
        assert orchestrator.create_plan_uc is not None
        assert orchestrator.resume_session_uc is not None
        assert orchestrator.revise_plan_uc is not None
        assert orchestrator.storage is mock_container.storage


class TestRunNewSession:
    """Tests for run_new_session method."""

    @pytest.mark.asyncio
    async def test_run_new_session_with_date(self, mock_container, sample_memory):
        """Should start session with specified date."""
        orchestrator = SessionOrchestrator(mock_container)
        orchestrator.create_plan_uc.execute = AsyncMock(return_value=sample_memory)

        result = await orchestrator.run_new_session(date="2026-01-23")

        assert result == sample_memory
        orchestrator.create_plan_uc.execute.assert_called_once_with("2026-01-23", False)

    @pytest.mark.asyncio
    async def test_run_new_session_defaults_to_today(self, mock_container, sample_memory):
        """Should default to today's date."""
        orchestrator = SessionOrchestrator(mock_container)
        orchestrator.create_plan_uc.execute = AsyncMock(return_value=sample_memory)

        today = datetime.now().strftime("%Y-%m-%d")
        await orchestrator.run_new_session()

        orchestrator.create_plan_uc.execute.assert_called_once_with(today, False)

    @pytest.mark.asyncio
    async def test_run_new_session_force_new(self, mock_container, sample_memory):
        """Should pass force_new flag."""
        orchestrator = SessionOrchestrator(mock_container)
        orchestrator.create_plan_uc.execute = AsyncMock(return_value=sample_memory)

        await orchestrator.run_new_session(date="2026-01-23", force_new=True)

        orchestrator.create_plan_uc.execute.assert_called_once_with("2026-01-23", True)


class TestRunResume:
    """Tests for run_resume method."""

    @pytest.mark.asyncio
    async def test_run_resume_calls_use_case(self, mock_container, sample_memory):
        """Should call resume use case with date."""
        orchestrator = SessionOrchestrator(mock_container)
        orchestrator.resume_session_uc.execute = AsyncMock(return_value=sample_memory)

        result = await orchestrator.run_resume("2026-01-23")

        assert result == sample_memory
        orchestrator.resume_session_uc.execute.assert_called_once_with("2026-01-23")


class TestRunRevise:
    """Tests for run_revise method."""

    @pytest.mark.asyncio
    async def test_run_revise_with_date(self, mock_container, sample_memory):
        """Should revise session with specified date."""
        orchestrator = SessionOrchestrator(mock_container)
        orchestrator.revise_plan_uc.execute = AsyncMock(return_value=sample_memory)

        result = await orchestrator.run_revise(date="2026-01-23")

        assert result == sample_memory
        orchestrator.revise_plan_uc.execute.assert_called_once_with("2026-01-23")

    @pytest.mark.asyncio
    async def test_run_revise_defaults_to_today(self, mock_container, sample_memory):
        """Should default to today's date."""
        orchestrator = SessionOrchestrator(mock_container)
        orchestrator.revise_plan_uc.execute = AsyncMock(return_value=sample_memory)

        today = datetime.now().strftime("%Y-%m-%d")
        await orchestrator.run_revise()

        orchestrator.revise_plan_uc.execute.assert_called_once_with(today)


class TestListSessions:
    """Tests for list_sessions method."""

    @pytest.mark.asyncio
    async def test_list_sessions_delegates_to_storage(self, mock_container):
        """Should delegate to storage."""
        mock_container.storage.list_sessions = AsyncMock(
            return_value=["2026-01-20", "2026-01-21", "2026-01-22"]
        )
        orchestrator = SessionOrchestrator(mock_container)

        result = await orchestrator.list_sessions()

        assert result == ["2026-01-20", "2026-01-21", "2026-01-22"]
        mock_container.storage.list_sessions.assert_called_once()


class TestDeleteSession:
    """Tests for delete_session method."""

    @pytest.mark.asyncio
    async def test_delete_session_delegates_to_storage(self, mock_container):
        """Should delegate to storage."""
        mock_container.storage.delete_session = AsyncMock(return_value=True)
        orchestrator = SessionOrchestrator(mock_container)

        result = await orchestrator.delete_session("2026-01-23")

        assert result is True
        mock_container.storage.delete_session.assert_called_once_with("2026-01-23")

    @pytest.mark.asyncio
    async def test_delete_session_returns_false_if_not_found(self, mock_container):
        """Should return False if session not found."""
        mock_container.storage.delete_session = AsyncMock(return_value=False)
        orchestrator = SessionOrchestrator(mock_container)

        result = await orchestrator.delete_session("nonexistent")

        assert result is False
