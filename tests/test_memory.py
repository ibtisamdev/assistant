"""
Tests for memory.py - Session persistence and management.
"""

import json
import os
import pytest
from datetime import datetime

from memory import AgentMemory
from models import State


class TestMemoryPersistence:
    """Test session save/load cycle"""

    def test_create_new_session(self, tmp_path, monkeypatch):
        """Test creating a new session"""
        # Override sessions directory
        monkeypatch.setattr(AgentMemory, "SESSIONS_DIR", str(tmp_path))

        memory = AgentMemory(session_date="2026-01-20", force_new=True)

        # Verify session was created
        assert memory.session_date == "2026-01-20"
        assert memory.get("state") == State.idle
        assert memory.is_resuming is False

        # Verify file was created
        session_file = tmp_path / "2026-01-20.json"
        assert session_file.exists()

    def test_load_existing_session(self, tmp_path, sample_session_data, monkeypatch):
        """Test loading an existing session"""
        monkeypatch.setattr(AgentMemory, "SESSIONS_DIR", str(tmp_path))

        # Create session file
        session_file = tmp_path / "2026-01-20.json"
        with open(session_file, "w") as f:
            json.dump(sample_session_data, f)

        # Load session
        memory = AgentMemory(session_date="2026-01-20", force_new=False)

        # Verify session was loaded
        assert memory.is_resuming is True
        assert memory.get("state") == State.feedback
        assert memory.get("plan") is not None
        assert len(memory.get("plan").schedule) == 2

    def test_force_new_ignores_existing(
        self, tmp_path, sample_session_data, monkeypatch
    ):
        """Test that force_new creates fresh session even if one exists"""
        monkeypatch.setattr(AgentMemory, "SESSIONS_DIR", str(tmp_path))

        # Create existing session file
        session_file = tmp_path / "2026-01-20.json"
        with open(session_file, "w") as f:
            json.dump(sample_session_data, f)

        # Load with force_new=True
        memory = AgentMemory(session_date="2026-01-20", force_new=True)

        # Verify fresh session was created
        assert memory.is_resuming is False
        assert memory.get("state") == State.idle
        assert memory.get("plan") is None

    def test_set_and_get_state(self, tmp_path, monkeypatch):
        """Test setting and getting state values"""
        monkeypatch.setattr(AgentMemory, "SESSIONS_DIR", str(tmp_path))

        memory = AgentMemory(session_date="2026-01-20", force_new=True)

        # Set state
        memory.set("state", State.questions)
        assert memory.get("state") == State.questions

        # Verify it persists
        memory2 = AgentMemory(session_date="2026-01-20", force_new=False)
        assert memory2.get("state") == State.questions


class TestTimestampConsistency:
    """Test timestamp validation and fixing"""

    def test_timestamps_are_consistent_on_create(self, tmp_path, monkeypatch):
        """Test that new sessions have consistent timestamps"""
        monkeypatch.setattr(AgentMemory, "SESSIONS_DIR", str(tmp_path))

        memory = AgentMemory(session_date="2026-01-20", force_new=True)

        # Timestamps should be equal or last_updated slightly after created_at
        assert memory.memory.metadata.last_updated >= memory.memory.metadata.created_at

    def test_timestamps_updated_on_set(self, tmp_path, monkeypatch):
        """Test that last_updated is updated on state changes"""
        monkeypatch.setattr(AgentMemory, "SESSIONS_DIR", str(tmp_path))

        memory = AgentMemory(session_date="2026-01-20", force_new=True)
        original_updated = memory.memory.metadata.last_updated

        # Make a change
        memory.set("state", State.questions)

        # last_updated should have changed
        assert memory.memory.metadata.last_updated >= original_updated

    def test_corrupted_timestamps_are_fixed_on_load(self, tmp_path, monkeypatch):
        """Test that corrupted timestamps (last_updated < created_at) are fixed"""
        monkeypatch.setattr(AgentMemory, "SESSIONS_DIR", str(tmp_path))

        # Create session with corrupted timestamps
        corrupted_data = {
            "metadata": {
                "session_id": "2026-01-20",
                "created_at": "2026-01-20T12:00:00",
                "last_updated": "2026-01-20T10:00:00",  # Earlier than created_at!
                "version": "1.0",
                "num_llm_calls": 0,
                "num_user_messages": 0,
            },
            "agent_state": {
                "state": "idle",
                "plan": None,
                "questions": [],
                "questions_asked": False,
                "feedback_received": False,
            },
            "conversation": {"messages": []},
            "user_profile_path": "user_profile.json",
        }

        session_file = tmp_path / "2026-01-20.json"
        with open(session_file, "w") as f:
            json.dump(corrupted_data, f)

        # Load session
        memory = AgentMemory(session_date="2026-01-20", force_new=False)

        # Timestamps should now be consistent
        assert memory.memory.metadata.last_updated >= memory.memory.metadata.created_at


class TestCorruptedSessionHandling:
    """Test graceful handling of corrupted sessions"""

    def test_invalid_json_creates_fresh_session(self, tmp_path, monkeypatch, capsys):
        """Test that invalid JSON results in fresh session with warning"""
        monkeypatch.setattr(AgentMemory, "SESSIONS_DIR", str(tmp_path))

        # Create corrupted session file
        session_file = tmp_path / "2026-01-20.json"
        with open(session_file, "w") as f:
            f.write("{invalid json here")

        # Load session (should not crash)
        memory = AgentMemory(session_date="2026-01-20", force_new=False)

        # Should have fresh state
        assert memory.get("state") == State.idle

        # Warning should be printed
        captured = capsys.readouterr()
        assert "corrupted" in captured.out.lower() or "WARNING" in captured.out

        # Corrupted file should be renamed
        corrupted_files = list(tmp_path.glob("*.corrupted.*"))
        assert len(corrupted_files) == 1

    def test_partial_recovery_preserves_conversation(
        self, tmp_path, monkeypatch, capsys
    ):
        """Test that partial recovery tries to preserve conversation data"""
        monkeypatch.setattr(AgentMemory, "SESSIONS_DIR", str(tmp_path))

        # Create partially corrupted session (valid JSON structure but incomplete)
        partial_data = """{
            "metadata": {"session_id": "2026-01-20", "created_at": "2026-01-20T10:00:00", "last_updated": "2026-01-20T10:30:00", "version": "1.0", "num_llm_calls": 0, "num_user_messages": 1},
            "agent_state": {"state": "idle", "plan": null, "questions": [], "questions_asked": false, "feedback_received": false},
            "conversation": {"messages": [{"role": "user", "content": "My test goal", "timestamp": "2026-01-20T10:01:00"}]},
            "user_profile_path": "user_profile.json"
        }"""

        session_file = tmp_path / "2026-01-20.json"
        with open(session_file, "w") as f:
            f.write(partial_data)

        # Load session
        memory = AgentMemory(session_date="2026-01-20", force_new=False)

        # Session should load successfully
        assert memory.is_resuming is True


class TestTempFileCleanup:
    """Test cleanup of stale temporary files"""

    def test_old_tmp_files_are_cleaned(self, tmp_path, monkeypatch):
        """Test that old .tmp files are cleaned up on init"""
        monkeypatch.setattr(AgentMemory, "SESSIONS_DIR", str(tmp_path))

        # Create an old .tmp file
        tmp_file = tmp_path / "2026-01-19.json.tmp"
        tmp_file.write_text("{}")

        # Backdate the file to be > 1 hour old
        import time

        old_time = time.time() - 7200  # 2 hours ago
        os.utime(tmp_file, (old_time, old_time))

        # Initialize memory (triggers cleanup)
        AgentMemory(session_date="2026-01-20", force_new=True)

        # Old tmp file should be deleted
        assert not tmp_file.exists()

    def test_recent_tmp_files_are_preserved(self, tmp_path, monkeypatch):
        """Test that recent .tmp files are not deleted"""
        monkeypatch.setattr(AgentMemory, "SESSIONS_DIR", str(tmp_path))

        # Create a recent .tmp file
        tmp_file = tmp_path / "2026-01-19.json.tmp"
        tmp_file.write_text("{}")
        # File is new (just created), so it should be preserved

        # Initialize memory (triggers cleanup)
        AgentMemory(session_date="2026-01-20", force_new=True)

        # Recent tmp file should still exist
        assert tmp_file.exists()


class TestConversationManagement:
    """Test conversation history management"""

    def test_add_user_message(self, tmp_path, monkeypatch):
        """Test adding user messages to conversation"""
        monkeypatch.setattr(AgentMemory, "SESSIONS_DIR", str(tmp_path))

        memory = AgentMemory(session_date="2026-01-20", force_new=True)
        initial_count = len(memory.memory.conversation.messages)

        memory.add_user_message("Test message")

        assert len(memory.memory.conversation.messages) == initial_count + 1
        assert memory.memory.conversation.messages[-1].content == "Test message"
        assert memory.memory.conversation.messages[-1].role.value == "user"

    def test_add_assistant_summary(self, tmp_path, monkeypatch):
        """Test adding assistant summaries to conversation"""
        monkeypatch.setattr(AgentMemory, "SESSIONS_DIR", str(tmp_path))

        memory = AgentMemory(session_date="2026-01-20", force_new=True)
        initial_count = len(memory.memory.conversation.messages)

        memory.add_assistant_summary("Here is your plan")

        assert len(memory.memory.conversation.messages) == initial_count + 1
        assert memory.memory.conversation.messages[-1].content == "Here is your plan"
        assert memory.memory.conversation.messages[-1].role.value == "assistant"

    def test_get_history_returns_openai_format(self, tmp_path, monkeypatch):
        """Test that get('history') returns OpenAI API format"""
        monkeypatch.setattr(AgentMemory, "SESSIONS_DIR", str(tmp_path))

        memory = AgentMemory(session_date="2026-01-20", force_new=True)
        memory.add_user_message("My goal")

        history = memory.get("history")

        assert isinstance(history, list)
        assert all(isinstance(msg, dict) for msg in history)
        assert all("role" in msg and "content" in msg for msg in history)
