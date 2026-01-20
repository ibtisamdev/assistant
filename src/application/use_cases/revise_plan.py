"""Revise plan use case."""

import logging
from ...domain.models.state import State
from ...domain.exceptions import SessionNotFound
from ..container import Container
from .create_plan import CreatePlanUseCase

logger = logging.getLogger(__name__)


class RevisePlanUseCase:
    """Use case: Revise finalized plan."""

    def __init__(self, container: Container):
        self.container = container
        self.storage = container.storage
        self.plan_formatter = container.plan_formatter
        self.progress = container.progress_formatter
        self.state_machine = container.state_machine

        # Reuse create plan logic
        self.create_plan_uc = CreatePlanUseCase(container)

    async def execute(self, session_id: str):
        """Revise a finalized plan."""
        # Load session
        memory = await self.storage.load_session(session_id)

        if not memory:
            raise SessionNotFound(f"No session found for {session_id}")

        # Check if session can be revised
        current_state = memory.agent_state.state

        if current_state != State.done:
            self.progress.print_warning(
                f"Session is not finalized (state: {current_state.value}). Resuming normally..."
            )
            from .resume_session import ResumeSessionUseCase

            resume_uc = ResumeSessionUseCase(self.container)
            return await resume_uc.execute(session_id)

        # Display current plan
        self.progress.print_header(f"Revising plan: {session_id}")

        if memory.agent_state.plan:
            from rich.console import Console

            console = Console()
            panel = self.plan_formatter.format_plan(memory.agent_state.plan)
            console.print(panel)
        else:
            self.progress.print_error("No plan found in session")
            return memory

        self.progress.print_info("What would you like to change?\n")

        # Transition back to feedback state
        memory.agent_state.state = self.state_machine.transition(State.done, State.feedback)
        await self.storage.save_session(session_id, memory)

        # Continue with feedback loop
        await self.create_plan_uc._handle_feedback(memory, session_id)

        self.progress.print_success("Plan revised!")
        return memory
