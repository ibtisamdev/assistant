"""
Tests for agent.py - Agent control loop and input validation.
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
from io import StringIO

from agent import Agent, VALID_STATE_TRANSITIONS
from models import State, Feedback


class TestInputValidation:
    """Test input validation helper"""

    @patch("llm.OpenAI")
    def test_empty_input_rejected(self, mock_openai, tmp_path, monkeypatch, capsys):
        """Test that empty input prompts for retry"""
        from memory import AgentMemory

        monkeypatch.setattr(AgentMemory, "SESSIONS_DIR", str(tmp_path))
        monkeypatch.setenv("OPENAI_API_KEY", "sk-test-key")

        agent = Agent(session_date="2026-01-20", force_new=True)

        # Simulate: first input empty, second input valid
        inputs = iter(["", "valid input"])
        monkeypatch.setattr("builtins.input", lambda _: next(inputs))

        result = agent._get_validated_input("Test prompt: ", allow_empty=False)

        assert result == "valid input"
        captured = capsys.readouterr()
        assert "cannot be empty" in captured.out.lower()

    @patch("llm.OpenAI")
    def test_empty_input_allowed_when_specified(
        self, mock_openai, tmp_path, monkeypatch
    ):
        """Test that empty input is allowed when allow_empty=True"""
        from memory import AgentMemory

        monkeypatch.setattr(AgentMemory, "SESSIONS_DIR", str(tmp_path))
        monkeypatch.setenv("OPENAI_API_KEY", "sk-test-key")

        agent = Agent(session_date="2026-01-20", force_new=True)

        monkeypatch.setattr("builtins.input", lambda _: "")

        result = agent._get_validated_input("Test prompt: ", allow_empty=True)

        assert result == ""

    @patch("llm.OpenAI")
    def test_long_input_rejected(self, mock_openai, tmp_path, monkeypatch, capsys):
        """Test that excessively long input prompts for retry"""
        from memory import AgentMemory

        monkeypatch.setattr(AgentMemory, "SESSIONS_DIR", str(tmp_path))
        monkeypatch.setenv("OPENAI_API_KEY", "sk-test-key")

        agent = Agent(session_date="2026-01-20", force_new=True)

        # First input too long, second is valid
        long_input = "x" * 100
        short_input = "valid"
        inputs = iter([long_input, short_input])
        monkeypatch.setattr("builtins.input", lambda _: next(inputs))

        result = agent._get_validated_input("Test: ", max_length=50)

        assert result == short_input
        captured = capsys.readouterr()
        assert "too long" in captured.out.lower()

    @patch("llm.OpenAI")
    def test_input_is_stripped(self, mock_openai, tmp_path, monkeypatch):
        """Test that input is stripped of whitespace"""
        from memory import AgentMemory

        monkeypatch.setattr(AgentMemory, "SESSIONS_DIR", str(tmp_path))
        monkeypatch.setenv("OPENAI_API_KEY", "sk-test-key")

        agent = Agent(session_date="2026-01-20", force_new=True)

        monkeypatch.setattr("builtins.input", lambda _: "  valid input  ")

        result = agent._get_validated_input("Test: ")

        assert result == "valid input"


class TestFeedbackExitKeywords:
    """Test case-insensitive exit keywords in feedback"""

    @patch("llm.OpenAI")
    def test_lowercase_no_exits(self, mock_openai, tmp_path, monkeypatch):
        """Test that 'no' exits feedback loop"""
        from memory import AgentMemory

        monkeypatch.setattr(AgentMemory, "SESSIONS_DIR", str(tmp_path))
        monkeypatch.setenv("OPENAI_API_KEY", "sk-test-key")

        agent = Agent(session_date="2026-01-20", force_new=True)
        monkeypatch.setattr("builtins.input", lambda _: "no")

        result = agent._get_feedback()

        assert result == Feedback.no

    @patch("llm.OpenAI")
    def test_uppercase_no_exits(self, mock_openai, tmp_path, monkeypatch):
        """Test that 'NO' exits feedback loop"""
        from memory import AgentMemory

        monkeypatch.setattr(AgentMemory, "SESSIONS_DIR", str(tmp_path))
        monkeypatch.setenv("OPENAI_API_KEY", "sk-test-key")

        agent = Agent(session_date="2026-01-20", force_new=True)
        monkeypatch.setattr("builtins.input", lambda _: "NO")

        result = agent._get_feedback()

        assert result == Feedback.no

    @patch("llm.OpenAI")
    def test_n_shortcut_exits(self, mock_openai, tmp_path, monkeypatch):
        """Test that 'n' exits feedback loop"""
        from memory import AgentMemory

        monkeypatch.setattr(AgentMemory, "SESSIONS_DIR", str(tmp_path))
        monkeypatch.setenv("OPENAI_API_KEY", "sk-test-key")

        agent = Agent(session_date="2026-01-20", force_new=True)
        monkeypatch.setattr("builtins.input", lambda _: "n")

        result = agent._get_feedback()

        assert result == Feedback.no

    @patch("llm.OpenAI")
    def test_done_keyword_exits(self, mock_openai, tmp_path, monkeypatch):
        """Test that 'done' exits feedback loop"""
        from memory import AgentMemory

        monkeypatch.setattr(AgentMemory, "SESSIONS_DIR", str(tmp_path))
        monkeypatch.setenv("OPENAI_API_KEY", "sk-test-key")

        agent = Agent(session_date="2026-01-20", force_new=True)
        monkeypatch.setattr("builtins.input", lambda _: "done")

        result = agent._get_feedback()

        assert result == Feedback.no

    @patch("llm.OpenAI")
    def test_actual_feedback_continues(self, mock_openai, tmp_path, monkeypatch):
        """Test that actual feedback returns Feedback.yes"""
        from memory import AgentMemory

        monkeypatch.setattr(AgentMemory, "SESSIONS_DIR", str(tmp_path))
        monkeypatch.setenv("OPENAI_API_KEY", "sk-test-key")

        agent = Agent(session_date="2026-01-20", force_new=True)
        monkeypatch.setattr("builtins.input", lambda _: "Please add more breaks")

        result = agent._get_feedback()

        assert result == Feedback.yes


class TestStateTransitionValidation:
    """Test state machine transition validation"""

    def test_valid_transitions_defined(self):
        """Test that valid state transitions are defined"""
        assert State.idle in VALID_STATE_TRANSITIONS
        assert State.questions in VALID_STATE_TRANSITIONS
        assert State.feedback in VALID_STATE_TRANSITIONS
        assert State.done in VALID_STATE_TRANSITIONS

    def test_idle_can_go_to_questions_or_feedback(self):
        """Test idle state valid transitions"""
        valid = VALID_STATE_TRANSITIONS[State.idle]
        assert State.questions in valid
        assert State.feedback in valid

    def test_questions_can_go_to_feedback_or_done(self):
        """Test questions state valid transitions"""
        valid = VALID_STATE_TRANSITIONS[State.questions]
        assert State.feedback in valid
        assert State.done in valid

    def test_feedback_can_go_to_questions_done_or_stay(self):
        """Test feedback state valid transitions"""
        valid = VALID_STATE_TRANSITIONS[State.feedback]
        assert State.questions in valid
        assert State.done in valid
        assert State.feedback in valid  # Can stay in feedback

    def test_done_can_only_go_to_feedback(self):
        """Test done state can only transition via revise"""
        valid = VALID_STATE_TRANSITIONS[State.done]
        assert valid == [State.feedback]

    @patch("llm.OpenAI")
    def test_invalid_transition_logs_warning(
        self, mock_openai, tmp_path, monkeypatch, caplog
    ):
        """Test that invalid state transitions log a warning"""
        import logging
        from memory import AgentMemory

        monkeypatch.setattr(AgentMemory, "SESSIONS_DIR", str(tmp_path))
        monkeypatch.setenv("OPENAI_API_KEY", "sk-test-key")

        agent = Agent(session_date="2026-01-20", force_new=True)

        with caplog.at_level(logging.WARNING):
            # Simulate invalid transition: idle -> done (skipping questions/feedback)
            agent._validate_state_transition(State.idle, State.done)

        assert "Unusual state transition" in caplog.text


class TestResumeHandling:
    """Test session resume scenarios"""

    @patch("llm.OpenAI")
    def test_resume_done_session_without_revise_returns_false(
        self, mock_openai, tmp_path, monkeypatch, capsys
    ):
        """Test that resuming done session without --revise shows plan and returns False"""
        from memory import AgentMemory
        import json

        monkeypatch.setattr(AgentMemory, "SESSIONS_DIR", str(tmp_path))
        monkeypatch.setenv("OPENAI_API_KEY", "sk-test-key")

        # Create a completed session
        session_data = {
            "metadata": {
                "session_id": "2026-01-20",
                "created_at": "2026-01-20T10:00:00",
                "last_updated": "2026-01-20T10:30:00",
                "version": "1.0",
                "num_llm_calls": 2,
                "num_user_messages": 3,
            },
            "agent_state": {
                "state": "done",
                "plan": {
                    "schedule": [{"time": "09:00-10:00", "task": "Test"}],
                    "priorities": ["Test"],
                    "notes": "Test",
                },
                "questions": [],
                "questions_asked": True,
                "feedback_received": True,
            },
            "conversation": {"messages": []},
            "user_profile_path": "user_profile.json",
        }

        session_file = tmp_path / "2026-01-20.json"
        with open(session_file, "w") as f:
            json.dump(session_data, f)

        agent = Agent(session_date="2026-01-20", force_new=False, revise=False)
        result = agent._handle_resume()

        assert result is False
        captured = capsys.readouterr()
        assert "already completed" in captured.out.lower()

    @patch("llm.OpenAI")
    def test_resume_done_session_with_revise_returns_true(
        self, mock_openai, tmp_path, monkeypatch, capsys
    ):
        """Test that resuming done session with --revise reopens for editing"""
        from memory import AgentMemory
        import json

        monkeypatch.setattr(AgentMemory, "SESSIONS_DIR", str(tmp_path))
        monkeypatch.setenv("OPENAI_API_KEY", "sk-test-key")

        # Create a completed session
        session_data = {
            "metadata": {
                "session_id": "2026-01-20",
                "created_at": "2026-01-20T10:00:00",
                "last_updated": "2026-01-20T10:30:00",
                "version": "1.0",
                "num_llm_calls": 2,
                "num_user_messages": 3,
            },
            "agent_state": {
                "state": "done",
                "plan": {
                    "schedule": [{"time": "09:00-10:00", "task": "Test"}],
                    "priorities": ["Test"],
                    "notes": "Test",
                },
                "questions": [],
                "questions_asked": True,
                "feedback_received": True,
            },
            "conversation": {"messages": []},
            "user_profile_path": "user_profile.json",
        }

        session_file = tmp_path / "2026-01-20.json"
        with open(session_file, "w") as f:
            json.dump(session_data, f)

        agent = Agent(session_date="2026-01-20", force_new=False, revise=True)
        result = agent._handle_resume()

        assert result is True
        assert agent.memory.get("state") == State.feedback
        captured = capsys.readouterr()
        assert "revision mode" in captured.out.lower()
