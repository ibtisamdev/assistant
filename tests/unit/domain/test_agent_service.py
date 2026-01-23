"""Tests for AgentService - core agent business logic."""

import pytest

from src.domain.models.profile import (
    EnergyPattern,
    PersonalInfo,
    UserProfile,
    WorkContext,
    WorkHours,
)
from src.domain.models.session import AgentState, Session
from src.domain.models.state import State
from src.domain.services.agent_service import AgentService
from src.domain.services.planning_service import PlanningService
from src.domain.services.state_machine import StateMachine
from tests.conftest import MemoryFactory, MockLLMProvider, PlanFactory, UserProfileFactory


class TestAgentServiceInitialization:
    """Test AgentService initialization."""

    def test_init_with_dependencies(self, mock_llm, state_machine, planning_service):
        """Test agent service can be initialized with dependencies."""
        agent = AgentService(mock_llm, state_machine, planning_service)

        assert agent.llm == mock_llm
        assert agent.state_machine == state_machine
        assert agent.planning == planning_service


class TestProcessUserGoal:
    """Tests for process_user_goal method."""

    @pytest.fixture
    def agent_service(self):
        """Create agent service with mocks."""
        llm = MockLLMProvider(default_state=State.feedback)
        state_machine = StateMachine()
        planning = PlanningService()
        return AgentService(llm, state_machine, planning)

    @pytest.mark.asyncio
    async def test_process_goal_adds_to_conversation(self, agent_service):
        """Test that user goal is added to conversation history."""
        memory = MemoryFactory.create()
        profile = UserProfileFactory.create()

        await agent_service.process_user_goal("Work on project", memory, profile)

        # Check goal was added to conversation
        messages = memory.conversation.messages
        user_messages = [m for m in messages if m.role.value == "user"]
        assert len(user_messages) >= 1
        assert "Work on project" in user_messages[0].content

    @pytest.mark.asyncio
    async def test_process_goal_increments_user_messages(self, agent_service):
        """Test that user message count is incremented."""
        memory = MemoryFactory.create()
        profile = UserProfileFactory.create()
        initial_count = memory.metadata.num_user_messages

        await agent_service.process_user_goal("Work on project", memory, profile)

        assert memory.metadata.num_user_messages == initial_count + 1

    @pytest.mark.asyncio
    async def test_process_goal_increments_llm_calls(self, agent_service):
        """Test that LLM call count is incremented."""
        memory = MemoryFactory.create()
        profile = UserProfileFactory.create()
        initial_count = memory.metadata.num_llm_calls

        await agent_service.process_user_goal("Work on project", memory, profile)

        assert memory.metadata.num_llm_calls == initial_count + 1

    @pytest.mark.asyncio
    async def test_process_goal_returns_agent_state(self, agent_service):
        """Test that process_user_goal returns an AgentState."""
        memory = MemoryFactory.create()
        profile = UserProfileFactory.create()

        result = await agent_service.process_user_goal("Work on project", memory, profile)

        assert isinstance(result, AgentState)
        assert result.state in [State.questions, State.feedback, State.done]

    @pytest.mark.asyncio
    async def test_process_goal_with_questions_state(self):
        """Test processing goal when LLM returns questions."""
        llm = MockLLMProvider(
            default_state=State.questions,
            default_questions=["What's your deadline?", "Any meetings?"],
        )
        agent = AgentService(llm, StateMachine(), PlanningService())
        memory = MemoryFactory.create()
        profile = UserProfileFactory.create()

        result = await agent.process_user_goal("I need to plan my day", memory, profile)

        assert result.state == State.questions
        assert len(result.questions) == 2
        assert result.questions[0].question == "What's your deadline?"

    @pytest.mark.asyncio
    async def test_process_goal_with_feedback_state(self):
        """Test processing goal when LLM returns a plan directly."""
        plan = PlanFactory.create()
        llm = MockLLMProvider(default_state=State.feedback, default_plan=plan)
        agent = AgentService(llm, StateMachine(), PlanningService())
        memory = MemoryFactory.create()
        profile = UserProfileFactory.create()

        result = await agent.process_user_goal("I need to plan my day", memory, profile)

        assert result.state == State.feedback
        assert result.plan is not None
        assert len(result.plan.schedule) > 0

    @pytest.mark.asyncio
    async def test_process_goal_adds_profile_context(self):
        """Test that profile context is added to conversation."""
        llm = MockLLMProvider(default_state=State.feedback)
        agent = AgentService(llm, StateMachine(), PlanningService())
        memory = MemoryFactory.create()
        profile = UserProfile(
            user_id="test",
            personal_info=PersonalInfo(name="John", preferred_name="Johnny"),
            work_hours=WorkHours(start="09:00", end="17:00"),
        )

        await agent.process_user_goal("Plan my day", memory, profile)

        # Check that profile context was added as system message
        messages = memory.conversation.messages
        system_messages = [m for m in messages if m.role.value == "system"]
        assert any("Johnny" in m.content for m in system_messages)


class TestProcessAnswers:
    """Tests for process_answers method."""

    @pytest.fixture
    def agent_with_questions_state(self):
        """Create agent in questions state."""
        llm = MockLLMProvider(default_state=State.feedback)
        return AgentService(llm, StateMachine(), PlanningService())

    @pytest.mark.asyncio
    async def test_process_answers_adds_to_conversation(self, agent_with_questions_state):
        """Test that answers are added to conversation."""
        memory = MemoryFactory.create()
        memory.agent_state.state = State.questions
        answers = {"What's your deadline?": "End of day", "Any meetings?": "No"}

        await agent_with_questions_state.process_answers(answers, memory)

        messages = memory.conversation.messages
        user_messages = [m for m in messages if m.role.value == "user"]
        assert len(user_messages) == 2

    @pytest.mark.asyncio
    async def test_process_answers_increments_counters(self, agent_with_questions_state):
        """Test that message counters are incremented."""
        memory = MemoryFactory.create()
        memory.agent_state.state = State.questions
        answers = {"Q1": "A1", "Q2": "A2"}

        await agent_with_questions_state.process_answers(answers, memory)

        assert memory.metadata.num_user_messages == 2
        assert memory.metadata.num_llm_calls == 1

    @pytest.mark.asyncio
    async def test_process_answers_transitions_state(self, agent_with_questions_state):
        """Test that answers processing transitions to feedback state."""
        memory = MemoryFactory.create()
        memory.agent_state.state = State.questions

        result = await agent_with_questions_state.process_answers({"Q1": "A1"}, memory)

        assert result.state == State.feedback


class TestProcessFeedback:
    """Tests for process_feedback method."""

    @pytest.fixture
    def agent_with_feedback_state(self):
        """Create agent in feedback state."""
        llm = MockLLMProvider(default_state=State.done)
        return AgentService(llm, StateMachine(), PlanningService())

    @pytest.mark.asyncio
    async def test_process_feedback_accepts_plan(self, agent_with_feedback_state):
        """Test accepting a plan transitions to done state."""
        memory = MemoryFactory.create()
        memory.agent_state.state = State.feedback
        memory.agent_state.plan = PlanFactory.create()

        result = await agent_with_feedback_state.process_feedback("Looks good!", memory)

        assert result.state == State.done

    @pytest.mark.asyncio
    async def test_process_feedback_adds_to_conversation(self, agent_with_feedback_state):
        """Test that feedback is added to conversation."""
        memory = MemoryFactory.create()
        memory.agent_state.state = State.feedback
        memory.agent_state.plan = PlanFactory.create()

        await agent_with_feedback_state.process_feedback("Please adjust schedule", memory)

        messages = memory.conversation.messages
        user_messages = [m for m in messages if m.role.value == "user"]
        assert any("adjust schedule" in m.content for m in user_messages)

    @pytest.mark.asyncio
    async def test_process_feedback_can_revise_plan(self):
        """Test that feedback can request plan revision."""
        # LLM returns feedback state (stay in revision loop)
        llm = MockLLMProvider(default_state=State.feedback)
        agent = AgentService(llm, StateMachine(), PlanningService())
        memory = MemoryFactory.create()
        memory.agent_state.state = State.feedback
        memory.agent_state.plan = PlanFactory.create()

        result = await agent.process_feedback("Move the meeting earlier", memory)

        assert result.state == State.feedback
        assert result.plan is not None


class TestFormatProfileContext:
    """Tests for _format_profile_context method."""

    @pytest.fixture
    def agent_service(self):
        """Create agent service."""
        return AgentService(MockLLMProvider(), StateMachine(), PlanningService())

    def test_format_minimal_profile(self, agent_service):
        """Test formatting a minimal profile returns work hours and energy if set."""
        profile = UserProfile(user_id="test")

        result = agent_service._format_profile_context(profile)

        # Profile has defaults for work_hours and energy_pattern
        # So it will have some context
        assert isinstance(result, str)

    def test_format_profile_with_name(self, agent_service):
        """Test profile with name includes user info."""
        profile = UserProfile(
            user_id="test",
            personal_info=PersonalInfo(name="Alice", preferred_name="Ali"),
        )

        result = agent_service._format_profile_context(profile)

        assert "Ali" in result

    def test_format_profile_with_work_hours(self, agent_service):
        """Test profile with work hours includes schedule."""
        profile = UserProfile(
            user_id="test",
            work_hours=WorkHours(start="09:00", end="17:00", days=["Monday", "Tuesday"]),
        )

        result = agent_service._format_profile_context(profile)

        assert "09:00" in result
        assert "17:00" in result

    def test_format_profile_with_energy_pattern(self, agent_service):
        """Test profile with energy pattern includes levels."""
        profile = UserProfile(
            user_id="test",
            energy_pattern=EnergyPattern(morning="high", afternoon="medium", evening="low"),
        )

        result = agent_service._format_profile_context(profile)

        assert "high" in result
        assert "medium" in result

    def test_format_rich_profile(self, agent_service, rich_profile):
        """Test formatting a rich profile includes all sections."""
        result = agent_service._format_profile_context(rich_profile)

        assert "Tester" in result  # preferred name
        assert "09:00" in result  # work hours
        assert "Software Engineer" in result  # job role
        assert "Python" in result  # skill goals
        assert "Complete project" in result  # priorities


class TestShouldAskQuestions:
    """Tests for should_ask_questions method."""

    @pytest.fixture
    def agent_service(self):
        """Create agent service."""
        return AgentService(MockLLMProvider(), StateMachine(), PlanningService())

    def test_short_goal_asks_questions(self, agent_service):
        """Test that very short goals trigger questions."""
        profile = UserProfileFactory.create()

        result = agent_service.should_ask_questions("Work", profile)

        assert result is True

    def test_sparse_profile_asks_questions(self, agent_service):
        """Test that sparse profile triggers questions."""
        profile = UserProfile(user_id="test")
        goal = "I want to have a productive day working on my project and exercising"

        result = agent_service.should_ask_questions(goal, profile)

        assert result is True

    def test_rich_profile_with_detailed_goal_skips_questions(self, agent_service, rich_profile):
        """Test that rich profile with detailed goal skips questions."""
        goal = (
            "I want to focus on my Python project in the morning, "
            "have meetings in the afternoon, and exercise in the evening"
        )

        result = agent_service.should_ask_questions(goal, rich_profile)

        assert result is False

    def test_moderate_profile_with_vague_goal_asks_questions(self, agent_service):
        """Test moderate profile with vague goal asks questions."""
        profile = UserProfile(
            user_id="test",
            top_priorities=["Work", "Exercise"],
            work_context=WorkContext(job_role="Developer"),
        )

        result = agent_service.should_ask_questions("Plan my day", profile)

        assert result is True


class TestBuildAgentState:
    """Tests for _build_agent_state method."""

    @pytest.fixture
    def agent_service(self):
        """Create agent service."""
        return AgentService(MockLLMProvider(), StateMachine(), PlanningService())

    def test_build_state_with_questions(self, agent_service):
        """Test building state with questions."""
        session = Session(
            state=State.questions,
            questions=["Q1?", "Q2?"],
            plan=None,
        )

        result = agent_service._build_agent_state(session, State.idle)

        assert result.state == State.questions
        assert len(result.questions) == 2
        assert result.questions[0].question == "Q1?"
        assert result.questions_asked is True

    def test_build_state_with_plan(self, agent_service):
        """Test building state with plan."""
        plan = PlanFactory.create()
        session = Session(
            state=State.feedback,
            questions=[],
            plan=plan,
        )

        result = agent_service._build_agent_state(session, State.idle)

        assert result.state == State.feedback
        assert result.plan is not None
        assert len(result.plan.schedule) > 0

    def test_build_state_invalid_transition_fallback(self, agent_service):
        """Test that invalid transition falls back to current state."""
        # Create a session with questions state (valid from idle)
        # then simulate an invalid transition scenario
        session = Session(
            state=State.questions,
            questions=["Q1?"],
            plan=None,
        )

        # Try to build from done state (done->questions is invalid)
        result = agent_service._build_agent_state(session, State.done)

        # Should fallback to done since done->questions is invalid
        assert result.state == State.done


class TestFormatSessionSummary:
    """Tests for _format_session_summary method."""

    @pytest.fixture
    def agent_service(self):
        """Create agent service."""
        return AgentService(MockLLMProvider(), StateMachine(), PlanningService())

    def test_format_questions_state(self, agent_service):
        """Test formatting summary for questions state."""
        session = Session(
            state=State.questions,
            questions=["What's your priority?", "Any constraints?"],
            plan=None,
        )

        result = agent_service._format_session_summary(session)

        assert "2 clarifying questions" in result
        assert "priority" in result

    def test_format_feedback_state_with_plan(self, agent_service):
        """Test formatting summary for feedback state with plan."""
        plan = PlanFactory.create()
        session = Session(
            state=State.feedback,
            questions=[],
            plan=plan,
        )

        result = agent_service._format_session_summary(session)

        assert len(result) > 0
        # Should include plan summary elements

    def test_format_done_state(self, agent_service):
        """Test formatting summary for done state."""
        session = Session(
            state=State.done,
            questions=[],
            plan=PlanFactory.create(),
        )

        result = agent_service._format_session_summary(session)

        assert "finalized" in result.lower()
