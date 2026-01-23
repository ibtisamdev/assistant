"""Session and agent state models."""

import logging
from datetime import datetime

from pydantic import BaseModel, Field, model_validator

from .conversation import ConversationHistory
from .planning import Plan, Question
from .state import State

logger = logging.getLogger(__name__)


class AgentState(BaseModel):
    """Current runtime state of the agent."""

    state: State = Field(default=State.idle)
    plan: Plan | None = Field(default=None)
    questions: list[Question] = Field(default_factory=list)

    # Track what has been done
    questions_asked: bool = Field(default=False)
    feedback_received: bool = Field(default=False)


class SessionMetadata(BaseModel):
    """Session tracking and metadata."""

    session_id: str = Field(description="Session identifier (date in YYYY-MM-DD)")
    created_at: datetime = Field(default_factory=datetime.now)
    last_updated: datetime = Field(default_factory=datetime.now)
    version: str = Field(default="2.0", description="Schema version for migrations")

    # Session stats
    num_llm_calls: int = Field(default=0)
    num_user_messages: int = Field(default=0)


class Memory(BaseModel):
    """
    Complete session state - root model for persistence.
    This is what gets saved to sessions/YYYY-MM-DD.json
    """

    metadata: SessionMetadata
    agent_state: AgentState
    conversation: ConversationHistory

    # Reference to user profile (stored separately)
    user_profile_id: str = Field(default="default")

    def update_timestamp(self) -> None:
        """Update last_updated timestamp with validation."""
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

    def increment_llm_calls(self) -> None:
        """Track LLM usage."""
        self.metadata.num_llm_calls += 1
        self.update_timestamp()

    def increment_user_messages(self) -> None:
        """Track user interaction."""
        self.metadata.num_user_messages += 1
        self.update_timestamp()


class Session(BaseModel):
    """
    What the LLM returns (structured output).
    This is NOT stored in conversation history.
    Only used for parsing LLM responses.
    """

    plan: Plan | None = Field(
        default=None, description="The plan of the day (optional in questions state)"
    )
    questions: list[str] = Field(description="Clarifying questions for the user")
    state: State = Field(description="Next state the agent should transition to")

    @model_validator(mode="after")
    def validate_plan_by_state(self) -> "Session":
        """Ensure plan exists when state requires it."""
        if self.state in [State.feedback, State.done]:
            if self.plan is None:
                raise ValueError(f"Plan is required when state is {self.state.value}")
        return self
