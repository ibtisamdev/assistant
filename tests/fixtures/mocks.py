"""Mock implementations for testing."""

from typing import Type, TypeVar, List, Optional, Dict
from src.domain.models.conversation import Message
from src.domain.models.session import Memory, Session
from src.domain.models.profile import UserProfile
from src.domain.models.state import State
from .factories import PlanFactory

T = TypeVar("T")


class MockLLMProvider:
    """Mock LLM for testing."""

    def __init__(self, responses: Optional[Dict] = None):
        self.responses = responses or {}
        self.call_count = 0
        self.last_messages = []

    async def generate(self, messages: List[Message]) -> str:
        self.call_count += 1
        self.last_messages = messages
        return self.responses.get("default", "Mock response")

    async def generate_structured(self, messages: List[Message], schema: Type[T]) -> T:
        self.call_count += 1
        self.last_messages = messages

        # Return a mock Session object
        if schema.__name__ == "Session":
            state = self.responses.get("state", State.done)
            # Provide a plan for states that require it
            plan = self.responses.get("plan")
            if plan is None and state in [State.feedback, State.done]:
                plan = PlanFactory.create()

            return Session(
                plan=plan,
                questions=self.responses.get("questions", []),
                state=state,
            )

        # Default: return empty instance
        return schema()

    async def stream_generate(self, messages: List[Message]):
        for chunk in ["Mock ", "streaming ", "response"]:
            yield chunk


class MockStorage:
    """In-memory storage for testing."""

    def __init__(self):
        self.sessions: Dict[str, Memory] = {}
        self.profiles: Dict[str, UserProfile] = {}
        self.save_count = 0
        self.load_count = 0

    async def save_session(self, session_id: str, memory: Memory) -> None:
        self.save_count += 1
        self.sessions[session_id] = memory

    async def load_session(self, session_id: str) -> Optional[Memory]:
        self.load_count += 1
        return self.sessions.get(session_id)

    async def list_sessions(self) -> List[dict]:
        return [
            {
                "session_id": sid,
                "state": mem.agent_state.state.value,
                "has_plan": mem.agent_state.plan is not None,
                "created_at": str(mem.metadata.created_at),
                "last_updated": str(mem.metadata.last_updated),
            }
            for sid, mem in self.sessions.items()
        ]

    async def delete_session(self, session_id: str) -> bool:
        if session_id in self.sessions:
            del self.sessions[session_id]
            return True
        return False

    async def save_profile(self, user_id: str, profile: UserProfile) -> None:
        self.profiles[user_id] = profile

    async def load_profile(self, user_id: str) -> Optional[UserProfile]:
        return self.profiles.get(user_id)


class MockInputHandler:
    """Mock input handler for testing."""

    def __init__(self, responses: Optional[List[str]] = None):
        self.responses = responses or []
        self.response_index = 0
        self.prompts_received = []

    async def get_goal(self) -> str:
        return await self._get_next_response()

    async def get_feedback(self) -> Optional[str]:
        response = await self._get_next_response()
        if response.lower() in ["no", "done"]:
            return None
        return response

    async def get_answer(self, question: str) -> str:
        self.prompts_received.append(question)
        return await self._get_next_response()

    async def confirm(self, question: str) -> bool:
        response = await self._get_next_response()
        return response.lower() in ["yes", "y"]

    async def _get_next_response(self) -> str:
        if self.response_index < len(self.responses):
            response = self.responses[self.response_index]
            self.response_index += 1
            return response
        return "default response"
