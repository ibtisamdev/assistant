"""LLM-specific types."""

from typing import Optional
from pydantic import BaseModel


class LLMResponse(BaseModel):
    """Generic LLM response."""

    content: str
    model: str
    tokens_used: Optional[int] = None
    finish_reason: Optional[str] = None
