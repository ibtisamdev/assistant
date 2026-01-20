"""Conversation and messaging models."""

from enum import Enum
from datetime import datetime
from pydantic import BaseModel, Field
from typing import List


class MessageRole(str, Enum):
    """Conversation message roles."""

    system = "system"
    user = "user"
    assistant = "assistant"


class Message(BaseModel):
    """Strongly-typed conversation message."""

    role: MessageRole
    content: str
    timestamp: datetime = Field(default_factory=datetime.now)


class ConversationHistory(BaseModel):
    """Manages conversation context for LLM."""

    messages: List[Message] = Field(default_factory=list)

    def add_system(self, content: str) -> None:
        """Add system message (prompts)."""
        self.messages.append(Message(role=MessageRole.system, content=content))

    def add_user(self, content: str) -> None:
        """Add user message."""
        self.messages.append(Message(role=MessageRole.user, content=content))

    def add_assistant(self, content: str) -> None:
        """Add assistant message (concise summary, not full Session)."""
        self.messages.append(Message(role=MessageRole.assistant, content=content))

    def to_openai_format(self) -> List[dict]:
        """Convert to OpenAI API format."""
        return [{"role": msg.role.value, "content": msg.content} for msg in self.messages]

    def get_recent(self, n: int = 10) -> List[Message]:
        """Get last N messages."""
        return self.messages[-n:]

    def clear_history(self, keep_system: bool = True) -> None:
        """Clear all messages except optionally system prompt."""
        if keep_system:
            system_msgs = [m for m in self.messages if m.role == MessageRole.system]
            self.messages = system_msgs
        else:
            self.messages = []

    def get_total_length(self) -> int:
        """Get total character length of all messages."""
        return sum(len(msg.content) for msg in self.messages)
