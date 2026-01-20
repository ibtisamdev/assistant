"""LLM provider protocol."""

from typing import Protocol, TypeVar, Type, List
from ..models.conversation import Message

T = TypeVar("T")


class LLMProvider(Protocol):
    """Protocol for LLM providers - enables dependency inversion."""

    async def generate(self, messages: List[Message]) -> str:
        """Generate unstructured response."""
        ...

    async def generate_structured(self, messages: List[Message], schema: Type[T]) -> T:
        """Generate structured response (Pydantic model)."""
        ...

    async def stream_generate(self, messages: List[Message]):
        """Stream response (for future real-time feedback)."""
        ...
