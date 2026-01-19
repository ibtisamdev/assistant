"""
Pytest fixtures for Daily Planning AI Agent tests.
"""

import os
import pytest
from pathlib import Path


@pytest.fixture
def temp_sessions_dir(tmp_path):
    """Create temporary sessions directory"""
    sessions = tmp_path / "sessions"
    sessions.mkdir()
    return sessions


@pytest.fixture(autouse=True)
def mock_env(monkeypatch):
    """Mock environment variables for tests"""
    monkeypatch.setenv("OPENAI_API_KEY", "sk-test-key-for-testing-purposes-only")


@pytest.fixture
def sample_session_data():
    """Return sample valid session data"""
    return {
        "metadata": {
            "session_id": "2026-01-20",
            "created_at": "2026-01-20T10:00:00",
            "last_updated": "2026-01-20T10:30:00",
            "version": "1.0",
            "num_llm_calls": 2,
            "num_user_messages": 3,
        },
        "agent_state": {
            "state": "feedback",
            "plan": {
                "schedule": [
                    {"time": "09:00-10:00", "task": "Morning routine"},
                    {"time": "10:00-12:00", "task": "Deep work"},
                ],
                "priorities": ["Complete project", "Exercise"],
                "notes": "Test notes",
            },
            "questions": [],
            "questions_asked": True,
            "feedback_received": False,
        },
        "conversation": {
            "messages": [
                {
                    "role": "system",
                    "content": "You are a planning assistant.",
                    "timestamp": "2026-01-20T10:00:00",
                },
                {
                    "role": "user",
                    "content": "Help me plan my day",
                    "timestamp": "2026-01-20T10:01:00",
                },
            ]
        },
        "user_profile_path": "user_profile.json",
    }


@pytest.fixture
def corrupted_session_data():
    """Return intentionally corrupted JSON string"""
    return '{"metadata": {"session_id": "2026-01-20", invalid json here'


@pytest.fixture
def partial_corrupted_session_data():
    """Return partially valid JSON (conversation intact, rest corrupted)"""
    return """{
        "metadata": {"session_id": "2026-01-20", "created_at": "2026-01-20T10:00:00"},
        "agent_state": {"state": "idle", "plan": null, "questions": [],
        "conversation": {
            "messages": [
                {"role": "system", "content": "Test prompt", "timestamp": "2026-01-20T10:00:00"}
            ]
        },
        "user_profile_path": "user_profile.json"
    }"""
