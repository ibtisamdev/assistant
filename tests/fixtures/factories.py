"""Test data factories."""

from datetime import datetime

from src.domain.models.conversation import ConversationHistory
from src.domain.models.planning import Plan, Question, ScheduleItem
from src.domain.models.profile import EnergyPattern, UserProfile, WorkHours
from src.domain.models.session import AgentState, Memory, SessionMetadata
from src.domain.models.state import State


class ScheduleItemFactory:
    @staticmethod
    def create(**kwargs):
        defaults = {
            "time": "09:00-10:00",
            "task": "Test task",
        }
        defaults.update(kwargs)
        return ScheduleItem(**defaults)


class PlanFactory:
    @staticmethod
    def create(**kwargs):
        defaults = {
            "schedule": [
                ScheduleItem(time="09:00-10:00", task="Morning routine"),
                ScheduleItem(time="10:00-12:00", task="Deep work"),
                ScheduleItem(time="14:00-16:00", task="Meetings"),
            ],
            "priorities": ["Complete project", "Exercise", "Review emails"],
            "notes": "Test plan for unit testing",
        }
        defaults.update(kwargs)
        return Plan(**defaults)


class QuestionFactory:
    @staticmethod
    def create(**kwargs):
        defaults = {
            "question": "What is your main goal today?",
            "answer": "",
        }
        defaults.update(kwargs)
        return Question(**defaults)


class AgentStateFactory:
    @staticmethod
    def create(**kwargs):
        defaults = {
            "state": State.idle,
            "plan": None,
            "questions": [],
        }
        defaults.update(kwargs)
        return AgentState(**defaults)


class SessionMetadataFactory:
    @staticmethod
    def create(**kwargs):
        defaults = {
            "session_id": "2026-01-20",
            "created_at": datetime.now(),
            "last_updated": datetime.now(),
        }
        defaults.update(kwargs)
        return SessionMetadata(**defaults)


class ConversationHistoryFactory:
    @staticmethod
    def create(**kwargs):
        return ConversationHistory(**kwargs)


class MemoryFactory:
    @staticmethod
    def create(session_id: str = "2026-01-20", **kwargs):
        defaults = {
            "metadata": SessionMetadataFactory.create(session_id=session_id),
            "agent_state": AgentStateFactory.create(),
            "conversation": ConversationHistoryFactory.create(),
        }
        defaults.update(kwargs)
        return Memory(**defaults)


class UserProfileFactory:
    @staticmethod
    def create(**kwargs):
        defaults = {
            "user_id": "test_user",
            "work_hours": WorkHours(),
            "energy_pattern": EnergyPattern(),
        }
        defaults.update(kwargs)
        return UserProfile(**defaults)
