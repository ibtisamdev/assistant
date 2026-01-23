"""LLM-specific types."""

from pydantic import BaseModel


class LLMResponse(BaseModel):
    """Generic LLM response."""

    content: str
    model: str
    tokens_used: int | None = None
    finish_reason: str | None = None
