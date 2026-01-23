"""Domain models."""

from .conversation import ConversationHistory, Message, MessageRole
from .metrics import (
    AggregateMetrics,
    DailyMetrics,
    EstimationAccuracy,
    ProductivityPattern,
    TaskMetric,
)
from .planning import Plan, Question, ScheduleItem, TaskCategory, TaskStatus
from .profile import EnergyPattern, RecurringTask, UserProfile, WorkHours
from .session import AgentState, Memory, Session, SessionMetadata
from .state import VALID_STATE_TRANSITIONS, Feedback, State
from .template import DayTemplate, TemplateMetadata

__all__ = [
    "State",
    "Feedback",
    "VALID_STATE_TRANSITIONS",
    "Plan",
    "ScheduleItem",
    "Question",
    "TaskStatus",
    "TaskCategory",
    "Message",
    "MessageRole",
    "ConversationHistory",
    "UserProfile",
    "WorkHours",
    "EnergyPattern",
    "RecurringTask",
    "Memory",
    "AgentState",
    "SessionMetadata",
    "Session",
    "TaskMetric",
    "EstimationAccuracy",
    "DailyMetrics",
    "ProductivityPattern",
    "AggregateMetrics",
    "DayTemplate",
    "TemplateMetadata",
]
