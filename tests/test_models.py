"""
Tests for models.py - Pydantic models and validation.
"""

import pytest
from datetime import datetime, timedelta

from models import (
    State,
    Feedback,
    MessageRole,
    Memory,
    SessionMetadata,
    AgentState,
    ConversationHistory,
    Message,
    Plan,
    ScheduleItem,
    Question,
)


class TestStateEnum:
    """Test State enum values"""

    def test_all_states_defined(self):
        """Test that all expected states are defined"""
        assert State.idle.value == "idle"
        assert State.questions.value == "questions"
        assert State.feedback.value == "feedback"
        assert State.done.value == "done"

    def test_state_from_string(self):
        """Test creating State from string value"""
        assert State("idle") == State.idle
        assert State("questions") == State.questions
        assert State("feedback") == State.feedback
        assert State("done") == State.done


class TestFeedbackEnum:
    """Test Feedback enum values"""

    def test_feedback_values(self):
        """Test that feedback values are defined"""
        assert Feedback.yes.value == "yes"
        assert Feedback.no.value == "no"


class TestConversationHistory:
    """Test ConversationHistory model"""

    def test_add_system_message(self):
        """Test adding system message"""
        history = ConversationHistory()
        history.add_system("You are a helpful assistant")

        assert len(history.messages) == 1
        assert history.messages[0].role == MessageRole.system
        assert history.messages[0].content == "You are a helpful assistant"

    def test_add_user_message(self):
        """Test adding user message"""
        history = ConversationHistory()
        history.add_user("Hello")

        assert len(history.messages) == 1
        assert history.messages[0].role == MessageRole.user

    def test_add_assistant_message(self):
        """Test adding assistant message"""
        history = ConversationHistory()
        history.add_assistant("Here is your plan")

        assert len(history.messages) == 1
        assert history.messages[0].role == MessageRole.assistant

    def test_to_openai_format(self):
        """Test converting to OpenAI API format"""
        history = ConversationHistory()
        history.add_system("System prompt")
        history.add_user("User message")
        history.add_assistant("Assistant response")

        openai_format = history.to_openai_format()

        assert len(openai_format) == 3
        assert openai_format[0] == {"role": "system", "content": "System prompt"}
        assert openai_format[1] == {"role": "user", "content": "User message"}
        assert openai_format[2] == {
            "role": "assistant",
            "content": "Assistant response",
        }

    def test_get_recent(self):
        """Test getting recent messages"""
        history = ConversationHistory()
        for i in range(15):
            history.add_user(f"Message {i}")

        recent = history.get_recent(5)

        assert len(recent) == 5
        assert recent[0].content == "Message 10"
        assert recent[-1].content == "Message 14"

    def test_clear_history_keeps_system(self):
        """Test clearing history while keeping system messages"""
        history = ConversationHistory()
        history.add_system("System prompt")
        history.add_user("User message")
        history.add_assistant("Response")

        history.clear_history(keep_system=True)

        assert len(history.messages) == 1
        assert history.messages[0].role == MessageRole.system

    def test_clear_history_removes_all(self):
        """Test clearing all history"""
        history = ConversationHistory()
        history.add_system("System prompt")
        history.add_user("User message")

        history.clear_history(keep_system=False)

        assert len(history.messages) == 0


class TestMemoryTimestamps:
    """Test Memory timestamp validation"""

    def test_validate_timestamps_returns_true_when_valid(self):
        """Test that valid timestamps return True"""
        now = datetime.now()
        metadata = SessionMetadata(
            session_id="test",
            created_at=now,
            last_updated=now + timedelta(minutes=5),
        )
        agent_state = AgentState()
        conversation = ConversationHistory()

        memory = Memory(
            metadata=metadata, agent_state=agent_state, conversation=conversation
        )

        assert memory.validate_timestamps() is True

    def test_validate_timestamps_fixes_invalid(self):
        """Test that invalid timestamps are fixed"""
        now = datetime.now()
        metadata = SessionMetadata(
            session_id="test",
            created_at=now,
            last_updated=now - timedelta(hours=1),  # Invalid: before created_at
        )
        agent_state = AgentState()
        conversation = ConversationHistory()

        memory = Memory(
            metadata=metadata, agent_state=agent_state, conversation=conversation
        )

        # Should return False (was invalid) and fix it
        result = memory.validate_timestamps()

        assert result is False
        assert memory.metadata.last_updated >= memory.metadata.created_at

    def test_update_timestamp_validates(self):
        """Test that update_timestamp validates the new timestamp"""
        now = datetime.now()
        metadata = SessionMetadata(session_id="test", created_at=now, last_updated=now)
        agent_state = AgentState()
        conversation = ConversationHistory()

        memory = Memory(
            metadata=metadata, agent_state=agent_state, conversation=conversation
        )

        memory.update_timestamp()

        # last_updated should be >= created_at
        assert memory.metadata.last_updated >= memory.metadata.created_at


class TestPlanModel:
    """Test Plan model"""

    def test_plan_creation(self):
        """Test creating a valid plan"""
        plan = Plan(
            schedule=[
                ScheduleItem(time="09:00-10:00", task="Morning routine"),
                ScheduleItem(time="10:00-12:00", task="Deep work"),
            ],
            priorities=["Complete project", "Exercise"],
            notes="Focus on deep work in the morning",
        )

        assert len(plan.schedule) == 2
        assert len(plan.priorities) == 2
        assert plan.notes == "Focus on deep work in the morning"

    def test_schedule_item_fields(self):
        """Test ScheduleItem fields"""
        item = ScheduleItem(time="14:00-15:00", task="Meeting with team")

        assert item.time == "14:00-15:00"
        assert item.task == "Meeting with team"


class TestQuestionModel:
    """Test Question model"""

    def test_question_default_answer(self):
        """Test that question has empty default answer"""
        question = Question(question="What is your main goal?")

        assert question.question == "What is your main goal?"
        assert question.answer == ""

    def test_question_with_answer(self):
        """Test question with answer"""
        question = Question(
            question="What is your main goal?", answer="Complete the project"
        )

        assert question.answer == "Complete the project"


class TestAgentState:
    """Test AgentState model"""

    def test_default_state(self):
        """Test default agent state values"""
        state = AgentState()

        assert state.state == State.idle
        assert state.plan is None
        assert state.questions == []
        assert state.questions_asked is False
        assert state.feedback_received is False
