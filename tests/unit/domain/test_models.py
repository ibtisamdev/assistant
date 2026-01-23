"""Tests for domain models."""

from datetime import datetime

from src.domain.models import TaskStatus
from src.domain.models.conversation import ConversationHistory, MessageRole
from src.domain.models.planning import Plan, ScheduleItem
from src.domain.models.session import AgentState, Memory, SessionMetadata
from src.domain.models.state import State


class TestConversationHistory:
    """Tests for ConversationHistory model."""

    def test_add_system_message(self):
        """Should add system message."""
        history = ConversationHistory()
        history.add_system("You are a helpful assistant")

        assert len(history.messages) == 1
        assert history.messages[0].role == MessageRole.system
        assert history.messages[0].content == "You are a helpful assistant"

    def test_add_user_message(self):
        """Should add user message."""
        history = ConversationHistory()
        history.add_user("Hello")

        assert len(history.messages) == 1
        assert history.messages[0].role == MessageRole.user

    def test_add_assistant_message(self):
        """Should add assistant message."""
        history = ConversationHistory()
        history.add_assistant("Hi there!")

        assert len(history.messages) == 1
        assert history.messages[0].role == MessageRole.assistant

    def test_to_openai_format(self):
        """Should convert to OpenAI format."""
        history = ConversationHistory()
        history.add_system("System prompt")
        history.add_user("User message")
        history.add_assistant("Assistant response")

        openai_format = history.to_openai_format()

        assert len(openai_format) == 3
        assert openai_format[0] == {"role": "system", "content": "System prompt"}
        assert openai_format[1] == {"role": "user", "content": "User message"}
        assert openai_format[2] == {"role": "assistant", "content": "Assistant response"}

    def test_get_recent_messages(self):
        """Should get last N messages."""
        history = ConversationHistory()
        for i in range(10):
            history.add_user(f"Message {i}")

        recent = history.get_recent(3)

        assert len(recent) == 3
        assert recent[0].content == "Message 7"
        assert recent[2].content == "Message 9"

    def test_clear_history_keeps_system(self):
        """Should keep system messages when clearing."""
        history = ConversationHistory()
        history.add_system("System prompt")
        history.add_user("User message")
        history.add_assistant("Response")

        history.clear_history(keep_system=True)

        assert len(history.messages) == 1
        assert history.messages[0].role == MessageRole.system

    def test_clear_history_removes_all(self):
        """Should remove all messages."""
        history = ConversationHistory()
        history.add_system("System prompt")
        history.add_user("User message")

        history.clear_history(keep_system=False)

        assert len(history.messages) == 0

    def test_get_total_length(self):
        """Should calculate total character length."""
        history = ConversationHistory()
        history.add_user("Hello")  # 5 chars
        history.add_assistant("Hi there")  # 8 chars

        total = history.get_total_length()

        assert total == 13


class TestScheduleItem:
    """Tests for ScheduleItem model."""

    def test_validate_time_format_valid(self):
        """Should validate correct time format."""
        item = ScheduleItem(time="09:00-10:00", task="Meeting")
        assert item.validate_time_format() is True

    def test_validate_time_format_invalid(self):
        """Should reject invalid time format."""
        item = ScheduleItem(time="invalid", task="Meeting")
        assert item.validate_time_format() is False

    def test_extract_duration(self):
        """Should extract duration in minutes."""
        item = ScheduleItem(time="09:00-10:30", task="Meeting")
        assert item.extract_duration() == 90

    def test_is_completed_property(self):
        """Should check if task is completed."""
        item = ScheduleItem(time="09:00-10:00", task="Task")
        assert item.is_completed is False

        item.status = TaskStatus.completed
        assert item.is_completed is True

    def test_is_in_progress_property(self):
        """Should check if task is in progress."""
        item = ScheduleItem(time="09:00-10:00", task="Task")
        assert item.is_in_progress is False

        item.status = TaskStatus.in_progress
        assert item.is_in_progress is True


class TestPlan:
    """Tests for Plan model."""

    def test_calculate_total_duration(self):
        """Should calculate total scheduled duration."""
        plan = Plan(
            schedule=[
                ScheduleItem(time="09:00-10:00", task="Task 1"),  # 60 min
                ScheduleItem(time="10:00-11:30", task="Task 2"),  # 90 min
            ],
            priorities=["Priority"],
            notes="Notes",
        )

        duration = plan.calculate_total_duration()

        assert duration == 150
        assert plan.estimated_duration_minutes == 150

    def test_calculate_actual_duration(self):
        """Should calculate actual time spent from actual_start/actual_end."""
        from datetime import timedelta

        now = datetime.now()
        plan = Plan(
            schedule=[
                ScheduleItem(
                    time="09:00-10:00",
                    task="Task 1",
                    actual_start=now,
                    actual_end=now + timedelta(minutes=55),
                ),
                ScheduleItem(
                    time="10:00-11:00",
                    task="Task 2",
                    actual_start=now + timedelta(minutes=60),
                    actual_end=now + timedelta(minutes=130),  # 70 min
                ),
            ],
            priorities=["Priority"],
            notes="Notes",
        )

        duration = plan.calculate_actual_duration()

        assert duration == 125
        assert plan.actual_duration_minutes == 125

    def test_calculate_completion_rate(self):
        """Should calculate completion percentage."""
        plan = Plan(
            schedule=[
                ScheduleItem(time="09:00-10:00", task="Task 1", status=TaskStatus.completed),
                ScheduleItem(time="10:00-11:00", task="Task 2", status=TaskStatus.completed),
                ScheduleItem(time="11:00-12:00", task="Task 3", status=TaskStatus.not_started),
                ScheduleItem(time="12:00-13:00", task="Task 4", status=TaskStatus.not_started),
            ],
            priorities=["Priority"],
            notes="Notes",
        )

        rate = plan.calculate_completion_rate()

        assert rate == 50.0
        assert plan.completion_rate == 50.0

    def test_calculate_completion_rate_empty_schedule(self):
        """Should return 0 for empty schedule."""
        plan = Plan(schedule=[], priorities=["Test"], notes="Test")

        rate = plan.calculate_completion_rate()

        assert rate == 0.0

    def test_get_free_time(self):
        """Should calculate free time during work hours."""
        plan = Plan(
            schedule=[
                ScheduleItem(time="09:00-10:00", task="Task"),  # 60 min
            ],
            priorities=["Priority"],
            notes="Notes",
        )

        free_time = plan.get_free_time("09:00", "11:00")

        # 2 hours work = 120 min - 60 min scheduled = 60 min free
        assert free_time == 60


class TestMemory:
    """Tests for Memory model."""

    def test_memory_creation(self):
        """Should create memory with defaults."""
        memory = Memory(
            metadata=SessionMetadata(
                session_id="2026-01-23",
                created_at=datetime.now(),
                last_updated=datetime.now(),
            ),
            agent_state=AgentState(state=State.idle),
            conversation=ConversationHistory(),
        )

        assert memory.metadata.session_id == "2026-01-23"
        assert memory.agent_state.state == State.idle
        assert len(memory.conversation.messages) == 0


class TestAgentState:
    """Tests for AgentState model."""

    def test_default_state_is_idle(self):
        """Default state should be idle."""
        state = AgentState()
        assert state.state == State.idle

    def test_state_with_plan(self):
        """Should store plan in state."""
        plan = Plan(
            schedule=[ScheduleItem(time="09:00-10:00", task="Task")],
            priorities=["Test"],
            notes="Notes",
        )
        state = AgentState(state=State.done, plan=plan)

        assert state.plan is plan
        assert state.state == State.done
