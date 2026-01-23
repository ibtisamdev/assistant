"""Resume session use case."""

import logging

from ...domain.exceptions import SessionNotFound
from ...domain.models.state import State
from ..container import Container
from .create_plan import CreatePlanUseCase

logger = logging.getLogger(__name__)


class ResumeSessionUseCase:
    """Use case: Resume existing session."""

    def __init__(self, container: Container):
        self.container = container
        self.storage = container.storage
        self.plan_formatter = container.plan_formatter
        self.progress = container.progress_formatter

        # Reuse create plan logic
        self.create_plan_uc = CreatePlanUseCase(container)

    async def execute(self, session_id: str):
        """Resume an existing session."""
        # Load session
        memory = await self.storage.load_session(session_id)

        if not memory:
            raise SessionNotFound(f"No session found for {session_id}")

        # Display resume info
        self.progress.print_header(f"Resuming session: {session_id}")

        current_state = memory.agent_state.state

        if current_state == State.done:
            # Session is complete - just display plan
            self.progress.print_info("This session is already complete.")
            if memory.agent_state.plan:
                from rich.console import Console

                console = Console()
                panel = self.plan_formatter.format_plan(memory.agent_state.plan)
                console.print(panel)
            self.progress.print_info("Use --revise to modify this plan")
            return memory

        elif current_state == State.questions:
            self.progress.print_info("Continuing with clarifying questions...")

        elif current_state == State.feedback:
            self.progress.print_info("Continuing with plan feedback...")
            if memory.agent_state.plan:
                from rich.console import Console

                console = Console()
                panel = self.plan_formatter.format_plan(memory.agent_state.plan)
                console.print(panel)

        # Continue workflow using create plan logic
        profile = await self.storage.load_profile(memory.user_profile_id)
        if not profile:
            from ...domain.models.profile import UserProfile

            profile = UserProfile(user_id=memory.user_profile_id)

        while memory.agent_state.state != State.done:
            if memory.agent_state.state == State.questions:
                await self.create_plan_uc._handle_questions(memory, session_id, profile)
            elif memory.agent_state.state == State.feedback:
                await self.create_plan_uc._handle_feedback(memory, session_id)

        # Update planning history when resuming completes
        await self.create_plan_uc._update_planning_history(profile, memory, session_id)

        self.progress.print_success("Session resumed and completed!")
        return memory
