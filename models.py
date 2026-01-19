import logging
from datetime import datetime
from enum import Enum
from typing import Optional
from pydantic import BaseModel, Field

# Configure logging
logger = logging.getLogger(__name__)


# === Enums ===


class State(Enum):
    """Agent state machine states"""

    idle = "idle"
    questions = "questions"
    feedback = "feedback"
    done = "done"


class Feedback(Enum):
    """User feedback response"""

    yes = "yes"
    no = "no"


class MessageRole(str, Enum):
    """Conversation message roles"""

    system = "system"
    user = "user"
    assistant = "assistant"


# === User Profile Models ===


class WorkHours(BaseModel):
    """User's typical work schedule"""

    start: str = Field(description="Start time in HH:MM format", default="09:00")
    end: str = Field(description="End time in HH:MM format", default="17:00")
    days: list[str] = Field(
        description="Work days",
        default=["Monday", "Tuesday", "Wednesday", "Thursday", "Friday"],
    )


class EnergyPattern(BaseModel):
    """User's energy levels throughout the day"""

    morning: str = Field(description="Morning energy level", default="high")
    afternoon: str = Field(description="Afternoon energy level", default="medium")
    evening: str = Field(description="Evening energy level", default="low")


class RecurringTask(BaseModel):
    """Tasks that repeat regularly"""

    name: str
    frequency: str  # daily, weekly, etc.
    duration: int  # minutes
    preferred_time: Optional[str] = None  # HH:MM format
    priority: str = "medium"  # high/medium/low


class UserProfile(BaseModel):
    """Complete user profile for personalized planning"""

    # Basic info
    timezone: str = Field(default="UTC")

    # Schedule preferences
    work_hours: WorkHours = Field(default_factory=WorkHours)
    energy_pattern: EnergyPattern = Field(default_factory=EnergyPattern)

    # Planning preferences
    preferred_task_duration: int = Field(
        description="Preferred task block duration in minutes", default=60
    )
    break_frequency: int = Field(description="Minutes between breaks", default=90)

    # Habits and constraints
    recurring_tasks: list[RecurringTask] = Field(default_factory=list)
    blocked_times: list[dict[str, str]] = Field(
        description="Times unavailable for planning", default_factory=list
    )  # Format: [{"start": "12:00", "end": "13:00", "reason": "lunch"}]

    # Priorities and goals
    top_priorities: list[str] = Field(
        description="User's current top priorities", default_factory=list
    )
    long_term_goals: list[str] = Field(
        description="Long-term goals to align daily plans with", default_factory=list
    )

    # Metadata
    created_at: datetime = Field(default_factory=datetime.now)
    last_updated: datetime = Field(default_factory=datetime.now)


# === Conversation Models ===


class Message(BaseModel):
    """Strongly-typed conversation message"""

    role: MessageRole
    content: str
    timestamp: datetime = Field(default_factory=datetime.now)


class ConversationHistory(BaseModel):
    """Manages conversation context for LLM"""

    messages: list[Message] = Field(default_factory=list)

    def add_system(self, content: str):
        """Add system message (prompts)"""
        self.messages.append(Message(role=MessageRole.system, content=content))

    def add_user(self, content: str):
        """Add user message"""
        self.messages.append(Message(role=MessageRole.user, content=content))

    def add_assistant(self, content: str):
        """Add assistant message (concise summary, not full Session)"""
        self.messages.append(Message(role=MessageRole.assistant, content=content))

    def to_openai_format(self) -> list[dict]:
        """Convert to OpenAI API format"""
        return [
            {"role": msg.role.value, "content": msg.content} for msg in self.messages
        ]

    def get_recent(self, n: int = 10) -> list[Message]:
        """Get last N messages"""
        return self.messages[-n:]

    def clear_history(self, keep_system: bool = True):
        """Clear all messages except optionally system prompt"""
        if keep_system:
            system_msgs = [m for m in self.messages if m.role == MessageRole.system]
            self.messages = system_msgs
        else:
            self.messages = []


# === Planning Models ===


class Question(BaseModel):
    """Question asked to user"""

    question: str = Field(description="The question asked to the user")
    answer: str = Field(description="The answer given by the user", default="")


class ScheduleItem(BaseModel):
    """Individual task in the schedule"""

    time: str = Field(description="Time in HH:MM-HH:MM format")
    task: str = Field(description="Description of the task")


class Plan(BaseModel):
    """User's daily plan"""

    schedule: list[ScheduleItem] = Field(description="The schedule of the day")
    priorities: list[str] = Field(description="The priorities of the day")
    notes: str = Field(description="Additional notes")


# === Agent State Models ===


class AgentState(BaseModel):
    """Current runtime state of the agent"""

    state: State = Field(default=State.idle)
    plan: Optional[Plan] = Field(default=None)
    questions: list[Question] = Field(default_factory=list)

    # Track what has been done
    questions_asked: bool = Field(default=False)
    feedback_received: bool = Field(default=False)


class SessionMetadata(BaseModel):
    """Session tracking and metadata"""

    session_id: str = Field(description="Session identifier (date in YYYY-MM-DD)")
    created_at: datetime = Field(default_factory=datetime.now)
    last_updated: datetime = Field(default_factory=datetime.now)
    version: str = Field(default="1.0", description="Schema version for migrations")

    # Session stats
    num_llm_calls: int = Field(default=0)
    num_user_messages: int = Field(default=0)


# === Root Memory Model ===


class Memory(BaseModel):
    """
    Complete session state - root model for persistence.
    This is what gets saved to sessions/YYYY-MM-DD.json
    """

    metadata: SessionMetadata
    agent_state: AgentState
    conversation: ConversationHistory

    # Reference to user profile (stored separately)
    user_profile_path: str = Field(default="user_profile.json")

    def update_timestamp(self):
        """Update last_updated timestamp with validation"""
        new_timestamp = datetime.now()

        # Validation: ensure last_updated >= created_at
        if new_timestamp < self.metadata.created_at:
            logger.warning(
                f"Timestamp anomaly detected: new timestamp ({new_timestamp}) "
                f"is before created_at ({self.metadata.created_at}). Using created_at instead."
            )
            self.metadata.last_updated = self.metadata.created_at
        else:
            self.metadata.last_updated = new_timestamp

    def validate_timestamps(self) -> bool:
        """
        Validate timestamp consistency.
        Returns True if valid, False if corrected.
        """
        if self.metadata.last_updated < self.metadata.created_at:
            logger.warning(
                f"Corrupted timestamps detected: "
                f"last_updated ({self.metadata.last_updated}) < "
                f"created_at ({self.metadata.created_at}). Fixing..."
            )
            self.metadata.last_updated = self.metadata.created_at
            return False
        return True

    def increment_llm_calls(self):
        """Track LLM usage"""
        self.metadata.num_llm_calls += 1
        self.update_timestamp()

    def increment_user_messages(self):
        """Track user interaction"""
        self.metadata.num_user_messages += 1
        self.update_timestamp()


# === LLM Response Model ===


class Session(BaseModel):
    """
    What the LLM returns (structured output).
    This is NOT stored in conversation history.
    Only used for parsing LLM responses.
    """

    plan: Plan = Field(description="The plan of the day")
    questions: list[str] = Field(description="Clarifying questions for the user")
    state: State = Field(description="Next state the agent should transition to")
