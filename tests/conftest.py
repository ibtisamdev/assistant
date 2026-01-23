"""Shared pytest fixtures for all tests."""

import asyncio
import tempfile
from pathlib import Path
from typing import TypeVar

import pytest

from src.domain.models.conversation import Message
from src.domain.models.planning import Plan, Question, ScheduleItem, TaskCategory, TaskStatus
from src.domain.models.profile import (
    EnergyPattern,
    LearningPreferences,
    PersonalInfo,
    PlanningHistory,
    ProductivityHabits,
    UserProfile,
    WellnessSchedule,
    WorkContext,
    WorkHours,
)
from src.domain.models.session import AgentState, Memory, Session
from src.domain.models.state import State
from src.domain.models.template import DayTemplate
from src.domain.services.planning_service import PlanningService
from src.domain.services.state_machine import StateMachine

# Re-export existing factories for convenience
from tests.fixtures.factories import (
    MemoryFactory,
    PlanFactory,
    QuestionFactory,
    ScheduleItemFactory,
    UserProfileFactory,
)

T = TypeVar("T")


# ==================== Mock Classes ====================


class MockLLMProvider:
    """Mock LLM provider for testing."""

    def __init__(
        self,
        default_state: State = State.done,
        default_plan: Plan | None = None,
        default_questions: list[str] | None = None,
    ):
        self.default_state = default_state
        self.default_plan = default_plan
        self.default_questions = default_questions or []
        self.call_count = 0
        self.last_messages: list[Message] = []
        self.responses: list[Session] = []

    def set_response(self, response: Session) -> None:
        """Set next response."""
        self.responses.append(response)

    async def generate(self, messages: list[Message]) -> str:
        """Generate unstructured response."""
        self.call_count += 1
        self.last_messages = messages
        return "Mock response"

    async def generate_structured(self, messages: list[Message], schema: type[T]) -> T:
        """Generate structured response."""
        self.call_count += 1
        self.last_messages = messages

        # Return queued response if available
        if self.responses:
            return self.responses.pop(0)  # type: ignore

        # Return default Session
        plan = self.default_plan
        if plan is None and self.default_state in [State.feedback, State.done]:
            plan = PlanFactory.create()

        return Session(  # type: ignore
            state=self.default_state,
            plan=plan,
            questions=self.default_questions,
        )

    async def stream_generate(self, messages: list[Message]):
        """Stream response."""
        for chunk in ["Mock ", "streaming ", "response"]:
            yield chunk


class MockStorage:
    """In-memory storage for testing."""

    def __init__(self):
        self.sessions: dict[str, Memory] = {}
        self.profiles: dict[str, UserProfile] = {}
        self.templates: dict[str, DayTemplate] = {}
        self.save_count = 0
        self.load_count = 0

    async def save_session(self, session_id: str, memory: Memory) -> None:
        """Save session."""
        self.save_count += 1
        self.sessions[session_id] = memory

    async def load_session(self, session_id: str) -> Memory | None:
        """Load session."""
        self.load_count += 1
        return self.sessions.get(session_id)

    async def list_sessions(self) -> list[dict]:
        """List all sessions."""
        return [
            {
                "session_id": sid,
                "state": mem.agent_state.state.value,
                "has_plan": mem.agent_state.plan is not None,
                "created_at": str(mem.metadata.created_at),
                "last_updated": str(mem.metadata.last_updated),
            }
            for sid, mem in self.sessions.items()
        ]

    async def delete_session(self, session_id: str) -> bool:
        """Delete session."""
        if session_id in self.sessions:
            del self.sessions[session_id]
            return True
        return False

    async def save_profile(self, user_id: str, profile: UserProfile) -> None:
        """Save profile."""
        self.profiles[user_id] = profile

    async def load_profile(self, user_id: str) -> UserProfile | None:
        """Load profile."""
        return self.profiles.get(user_id)

    async def save_template(self, name: str, template: DayTemplate) -> None:
        """Save template."""
        self.templates[name] = template

    async def load_template(self, name: str) -> DayTemplate | None:
        """Load template."""
        return self.templates.get(name)

    async def list_templates(self) -> list[dict]:
        """List templates."""
        return [{"name": name} for name in self.templates.keys()]

    async def delete_template(self, name: str) -> bool:
        """Delete template."""
        if name in self.templates:
            del self.templates[name]
            return True
        return False

    async def template_exists(self, name: str) -> bool:
        """Check if template exists."""
        return name in self.templates


class MockInputHandler:
    """Mock input handler for testing."""

    def __init__(self, responses: list[str] | None = None):
        self.responses = responses or []
        self.response_index = 0
        self.prompts_received: list[str] = []

    def set_responses(self, responses: list[str]) -> None:
        """Set responses to return."""
        self.responses = responses
        self.response_index = 0

    async def get_goal(self) -> str:
        """Get user goal."""
        return await self._get_next_response()

    async def get_feedback(self) -> str | None:
        """Get user feedback."""
        response = await self._get_next_response()
        if response.lower() in ["no", "done", ""]:
            return None
        return response

    async def get_answer(self, question: str) -> str:
        """Get answer to question."""
        self.prompts_received.append(question)
        return await self._get_next_response()

    async def confirm(self, message: str) -> bool:
        """Get confirmation."""
        response = await self._get_next_response()
        return response.lower() in ["yes", "y", "true"]

    async def _get_next_response(self) -> str:
        """Get next queued response."""
        if self.response_index < len(self.responses):
            response = self.responses[self.response_index]
            self.response_index += 1
            return response
        return "default response"


# ==================== Fixtures ====================


@pytest.fixture
def mock_llm() -> MockLLMProvider:
    """Create mock LLM provider."""
    return MockLLMProvider()


@pytest.fixture
def mock_storage() -> MockStorage:
    """Create mock storage."""
    return MockStorage()


@pytest.fixture
def mock_input() -> MockInputHandler:
    """Create mock input handler."""
    return MockInputHandler()


@pytest.fixture
def state_machine() -> StateMachine:
    """Create state machine instance."""
    return StateMachine()


@pytest.fixture
def planning_service() -> PlanningService:
    """Create planning service instance."""
    return PlanningService()


@pytest.fixture
def sample_plan() -> Plan:
    """Create sample plan for testing."""
    return PlanFactory.create()


@pytest.fixture
def sample_memory() -> Memory:
    """Create sample memory for testing."""
    return MemoryFactory.create()


@pytest.fixture
def sample_profile() -> UserProfile:
    """Create sample user profile for testing."""
    return UserProfileFactory.create()


@pytest.fixture
def sample_session_with_plan() -> Memory:
    """Create memory with plan in feedback state."""
    memory = MemoryFactory.create()
    memory.agent_state = AgentState(
        state=State.feedback,
        plan=PlanFactory.create(),
        questions=[],
    )
    return memory


@pytest.fixture
def sample_session_done() -> Memory:
    """Create memory in done state."""
    memory = MemoryFactory.create()
    memory.agent_state = AgentState(
        state=State.done,
        plan=PlanFactory.create(),
        questions=[],
    )
    return memory


@pytest.fixture
def sample_schedule_item() -> ScheduleItem:
    """Create sample schedule item."""
    return ScheduleItemFactory.create()


@pytest.fixture
def sample_questions() -> list[Question]:
    """Create sample questions."""
    return [
        QuestionFactory.create(question="What is your main priority?"),
        QuestionFactory.create(question="Any meetings today?"),
        QuestionFactory.create(question="What time do you want to finish?"),
    ]


@pytest.fixture
def rich_profile() -> UserProfile:
    """Create a profile with rich context."""
    return UserProfile(
        user_id="rich_user",
        personal_info=PersonalInfo(
            name="Test User",
            preferred_name="Tester",
            communication_style="direct",
        ),
        work_hours=WorkHours(start="09:00", end="17:00", days=["Monday", "Tuesday", "Wednesday"]),
        energy_pattern=EnergyPattern(morning="high", afternoon="medium", evening="low"),
        productivity_habits=ProductivityHabits(
            peak_productivity_time="morning",
            focus_session_length=45,
            distraction_triggers=["email", "slack"],
            procrastination_patterns=["complex tasks"],
        ),
        wellness_schedule=WellnessSchedule(
            wake_time="07:00",
            sleep_time="23:00",
            meal_times=[{"name": "lunch", "time": "12:30"}],
            exercise_times=[{"day": "Monday", "time": "18:00", "duration": 60}],
        ),
        work_context=WorkContext(
            job_role="Software Engineer",
            meeting_heavy_days=["Monday", "Friday"],
            deadline_patterns="end of sprint",
            collaboration_preference="sync",
        ),
        learning_preferences=LearningPreferences(
            skill_development_goals=["Python", "Testing"],
            areas_of_interest=["AI", "Architecture"],
            preferred_learning_time="evening",
        ),
        top_priorities=["Complete project", "Learn testing"],
        long_term_goals=["Career growth", "Better work-life balance"],
        recurring_tasks=[],
        blocked_times=[{"start": "12:00", "end": "13:00", "reason": "lunch"}],
        planning_history=PlanningHistory(
            sessions_completed=10,
            successful_patterns=["Morning deep work", "Afternoon meetings"],
            avoided_patterns=["Late night work"],
        ),
    )


@pytest.fixture
def temp_dir():
    """Create temporary directory for file-based tests."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir)


@pytest.fixture
def storage_config(temp_dir):
    """Create storage config with temp directories."""
    from src.application.config import StorageConfig

    return StorageConfig(
        sessions_dir=temp_dir / "sessions",
        profiles_dir=temp_dir / "profiles",
        templates_dir=temp_dir / "templates",
    )


@pytest.fixture
def llm_config():
    """Create LLM config for testing."""
    from pydantic import SecretStr

    from src.application.config import LLMConfig

    return LLMConfig(
        api_key=SecretStr("sk-test-key-for-testing-purposes-only"),
        model="gpt-4o-mini",
        temperature=0.7,
        max_tokens=4096,
        timeout=30.0,
    )


@pytest.fixture
def retry_config():
    """Create retry config for testing."""
    from src.application.config import RetryConfig

    return RetryConfig(
        max_attempts=3,
        base_delay=0.1,  # Short delays for testing
        max_delay=1.0,
        exponential_base=2.0,
        rate_limit_multiplier=2.0,
    )


# ==================== Async Helpers ====================


@pytest.fixture
def event_loop():
    """Create event loop for async tests."""
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()


# ==================== Plan Builders ====================


def create_plan_with_tasks(
    tasks: list[dict],
    priorities: list[str] | None = None,
    notes: str = "",
) -> Plan:
    """Helper to create plan with specific tasks."""
    schedule = []
    for task in tasks:
        schedule.append(
            ScheduleItem(
                time=task.get("time", "09:00-10:00"),
                task=task.get("task", "Test task"),
                status=task.get("status", TaskStatus.not_started),
                category=task.get("category", TaskCategory.productive),
                estimated_minutes=task.get("estimated_minutes"),
                actual_minutes=task.get("actual_minutes"),
                actual_start=task.get("actual_start"),
                actual_end=task.get("actual_end"),
            )
        )

    return Plan(
        schedule=schedule,
        priorities=priorities or ["Priority 1", "Priority 2"],
        notes=notes,
    )


def create_session_response(
    state: State,
    plan: Plan | None = None,
    questions: list[str] | None = None,
) -> Session:
    """Helper to create Session response."""
    return Session(
        state=state,
        plan=plan,
        questions=questions or [],
    )
