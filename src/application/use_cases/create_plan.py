"""Create plan use case."""

import logging
from datetime import datetime
from rich.prompt import Confirm
from ...domain.models.session import Memory, SessionMetadata, AgentState
from ...domain.models.conversation import ConversationHistory
from ...domain.models.state import State
from ...domain.models.profile import UserProfile
from ...domain.services.task_import_service import TaskImportService
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
        self.task_import = TaskImportService()

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
            # Check for incomplete tasks from yesterday
            incomplete_context = await self._check_and_prompt_incomplete_tasks(session_id)

            # Get user goal
            self.progress.print_header("Let's create your daily plan")
            goal = await self.input_handler.get_goal()

            # If user wants to include incomplete tasks, add them to context
            if incomplete_context:
                goal = f"{goal}\n\n{incomplete_context}"

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

        # Update planning history when plan is finalized
        await self._update_planning_history(profile, memory, session_id)

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

    async def _update_planning_history(
        self, profile: UserProfile, memory: Memory, session_id: str
    ) -> None:
        """Update user profile with planning history insights."""
        from ...domain.services.planning_service import PlanningService

        planning_service = PlanningService()

        # Update profile with session insights
        updated_profile = planning_service.update_planning_history(profile, memory, session_id)

        # Save updated profile
        await self.storage.save_profile(profile.user_id, updated_profile)
        logger.info(
            f"Updated planning history for user {profile.user_id} "
            f"(sessions: {updated_profile.planning_history.sessions_completed})"
        )

    async def _check_and_prompt_incomplete_tasks(self, session_id: str) -> str:
        """
        Check for incomplete tasks from yesterday and prompt user to include them.

        Returns:
            Context string to add to goal if user wants to include tasks, empty string otherwise
        """
        from rich.console import Console
        from rich.table import Table
        from ...domain.models.planning import TaskStatus

        console = Console()

        # Get yesterday's session
        yesterday_id = self.task_import.get_yesterday_session_id(session_id)
        yesterday = await self.storage.load_session(yesterday_id)

        if not yesterday or not yesterday.agent_state.plan:
            return ""

        # Get incomplete tasks
        incomplete = self.task_import.get_incomplete_tasks(yesterday)

        if not incomplete:
            return ""

        # Display incomplete tasks
        console.print(
            f"\n[yellow]Found {len(incomplete)} incomplete task(s) from {yesterday_id}:[/yellow]"
        )

        table = Table(show_header=True, box=None)
        table.add_column("#", style="dim", width=3)
        table.add_column("Task")
        table.add_column("Est.", justify="right", width=6)

        for i, task in enumerate(incomplete, 1):
            est = f"{task.estimated_minutes}m" if task.estimated_minutes else "-"
            table.add_row(str(i), task.task, est)

        console.print(table)
        console.print()

        # Ask user if they want to include them
        if Confirm.ask("Include these tasks in today's plan?", default=True):
            # Format tasks for context
            return self.task_import.format_tasks_for_context(incomplete, yesterday_id)

        return ""
