"""Create plan use case."""

import logging
from datetime import datetime
from ...domain.models.session import Memory, SessionMetadata, AgentState
from ...domain.models.conversation import ConversationHistory
from ...domain.models.state import State
from ...domain.models.profile import UserProfile
from ..container import Container

logger = logging.getLogger(__name__)


class CreatePlanUseCase:
    """Use case: Create new daily plan."""

    def __init__(self, container: Container):
        self.container = container
        self.agent = container.agent_service
        self.storage = container.storage
        self.input_handler = container.input_handler
        self.plan_formatter = container.plan_formatter
        self.progress = container.progress_formatter

    async def execute(self, session_id: str, force_new: bool = False) -> Memory:
        """
        Execute plan creation workflow.

        Args:
            session_id: Session identifier (usually YYYY-MM-DD)
            force_new: If True, create new session even if one exists
        """
        # Load or create session
        memory = await self._get_or_create_session(session_id, force_new)

        # Load user profile
        profile = await self.storage.load_profile(memory.user_profile_id)
        if not profile:
            profile = UserProfile(user_id=memory.user_profile_id)
            await self.storage.save_profile(memory.user_profile_id, profile)

        # Load system prompt
        await self._initialize_conversation(memory)

        # Main workflow
        if memory.agent_state.state == State.idle:
            # Get user goal
            self.progress.print_header("Let's create your daily plan")
            goal = await self.input_handler.get_goal()

            # Process goal
            agent_state = await self.agent.process_user_goal(goal, memory, profile)
            memory.agent_state = agent_state
            await self.storage.save_session(session_id, memory)

        # Handle state-specific logic
        while memory.agent_state.state != State.done:
            if memory.agent_state.state == State.questions:
                await self._handle_questions(memory, session_id, profile)
            elif memory.agent_state.state == State.feedback:
                await self._handle_feedback(memory, session_id)

        self.progress.print_success("Plan finalized!")
        return memory

    async def _get_or_create_session(self, session_id: str, force_new: bool) -> Memory:
        """Load existing session or create new one."""
        if not force_new:
            existing = await self.storage.load_session(session_id)
            if existing:
                logger.info(f"Loaded existing session: {session_id}")
                return existing

        # Create new session
        logger.info(f"Creating new session: {session_id}")
        memory = Memory(
            metadata=SessionMetadata(session_id=session_id),
            agent_state=AgentState(),
            conversation=ConversationHistory(),
        )

        await self.storage.save_session(session_id, memory)
        return memory

    async def _initialize_conversation(self, memory: Memory) -> None:
        """Initialize conversation with system prompt."""
        if len(memory.conversation.messages) == 0:
            # Load system prompt
            from pathlib import Path

            prompt_path = Path("config/prompts/system.txt")
            if prompt_path.exists():
                with open(prompt_path) as f:
                    system_prompt = f.read()
                memory.conversation.add_system(system_prompt)

    async def _handle_questions(
        self, memory: Memory, session_id: str, profile: UserProfile
    ) -> None:
        """Handle clarifying questions state."""
        from rich.console import Console

        console = Console()

        # Display questions
        questions_str = [q.question for q in memory.agent_state.questions]
        panel = self.plan_formatter.format_questions(questions_str)
        console.print(panel)

        # Collect answers
        answers = {}
        for question in memory.agent_state.questions:
            answer = await self.input_handler.get_answer(question.question)
            answers[question.question] = answer
            question.answer = answer

        # Process answers
        agent_state = await self.agent.process_answers(answers, memory)
        memory.agent_state = agent_state
        await self.storage.save_session(session_id, memory)

    async def _handle_feedback(self, memory: Memory, session_id: str) -> None:
        """Handle feedback loop state."""
        from rich.console import Console

        console = Console()

        while memory.agent_state.state == State.feedback:
            # Display plan
            if memory.agent_state.plan:
                panel = self.plan_formatter.format_plan(memory.agent_state.plan)
                console.print(panel)

            # Get feedback
            feedback = await self.input_handler.get_feedback()

            if feedback is None:
                # User is done
                memory.agent_state.state = State.done
                await self.storage.save_session(session_id, memory)
                break

            # Process feedback
            agent_state = await self.agent.process_feedback(feedback, memory)
            memory.agent_state = agent_state
            await self.storage.save_session(session_id, memory)
