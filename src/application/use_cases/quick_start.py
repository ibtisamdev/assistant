"""Quick start use case - fast plan creation based on previous patterns."""

import logging
from datetime import datetime, timedelta
from typing import Optional, List
from rich.console import Console
from rich import print as rprint

from ...domain.models import (
    State,
    Memory,
    AgentState,
    SessionMetadata,
    ConversationHistory,
    Plan,
    ScheduleItem,
)
from ...domain.models.profile import UserProfile
from ...domain.services.task_import_service import TaskImportService
from ..container import Container

logger = logging.getLogger(__name__)


class QuickStartUseCase:
    """
    Use case: Quick plan creation using previous day's pattern.

    This use case enables rapid plan creation for users with established routines.
    It:
    - Uses yesterday's plan as a template
    - Includes incomplete tasks from yesterday
    - Injects profile context
    - Goes directly to feedback state (skips questions)
    - Falls back to normal start if conditions aren't met
    """

    def __init__(self, container: Container):
        self.container = container
        self.agent = container.agent_service
        self.storage = container.storage
        self.input_handler = container.input_handler
        self.plan_formatter = container.plan_formatter
        self.progress = container.progress_formatter
        self.task_import = TaskImportService()
        self.console = Console()

    async def execute(
        self,
        session_id: Optional[str] = None,
        from_template: Optional[str] = None,
    ) -> Optional[Memory]:
        """
        Execute quick start workflow.

        Args:
            session_id: Target session date (defaults to today)
            from_template: Optional template name to use instead of yesterday

        Returns:
            Memory if successful, None if fell back to normal start
        """
        # Default to today
        if not session_id:
            session_id = datetime.now().strftime("%Y-%m-%d")

        # Check if session already exists
        existing = await self.storage.load_session(session_id)
        if existing and existing.agent_state.plan:
            self.console.print(f"[yellow]Session {session_id} already has a plan.[/yellow]")
            self.console.print(
                "[dim]Use 'day revise' to modify it, or 'day start' to replace it.[/dim]"
            )
            return existing

        # Load profile
        profile = await self.storage.load_profile("default")
        if not profile:
            profile = UserProfile(user_id="default")

        # Check quick start viability
        viability = await self._check_viability(session_id, profile, from_template)

        if not viability["viable"]:
            self.console.print(f"[yellow]{viability['reason']}[/yellow]")
            self.console.print("[dim]Starting normal planning flow...[/dim]\n")
            return None  # Signal to fall back to normal start

        # Display quick start context
        self._display_quick_start_info(viability, session_id)

        # Generate quick plan
        memory = await self._generate_quick_plan(
            session_id=session_id,
            profile=profile,
            source_plan=viability["source_plan"],
            incomplete_tasks=viability["incomplete_tasks"],
            source_date=viability["source_date"],
        )

        # Enter feedback loop
        await self._handle_feedback(memory, session_id)

        # Update planning history
        from ...domain.services.planning_service import PlanningService

        planning_service = PlanningService()
        updated_profile = planning_service.update_planning_history(profile, memory, session_id)
        await self.storage.save_profile(profile.user_id, updated_profile)

        self.progress.print_success("Plan finalized!")
        return memory

    async def _check_viability(
        self, session_id: str, profile: UserProfile, template_name: Optional[str]
    ) -> dict:
        """
        Check if quick start is viable.

        Returns dict with:
        - viable: bool
        - reason: str (if not viable)
        - source_plan: Plan (if viable)
        - source_date: str
        - incomplete_tasks: List[ScheduleItem]
        """
        # If template specified, use that
        if template_name:
            template = await self.storage.load_template(template_name)
            if template:
                prepared = template.prepare_for_new_day()
                return {
                    "viable": True,
                    "source": "template",
                    "source_date": template_name,
                    "source_plan": Plan(
                        schedule=prepared.schedule,
                        priorities=prepared.priorities,
                        notes=prepared.notes,
                    ),
                    "incomplete_tasks": [],
                }
            else:
                return {
                    "viable": False,
                    "reason": f"Template '{template_name}' not found.",
                }

        # Get yesterday's session
        yesterday_id = self.task_import.get_yesterday_session_id(session_id)
        yesterday = await self.storage.load_session(yesterday_id)

        if not yesterday:
            return {
                "viable": False,
                "reason": f"No previous session found for {yesterday_id}.",
            }

        if not yesterday.agent_state.plan:
            return {
                "viable": False,
                "reason": f"Previous session {yesterday_id} has no plan.",
            }

        if yesterday.agent_state.state != State.done:
            return {
                "viable": False,
                "reason": f"Previous session {yesterday_id} was not completed.",
            }

        # Check profile completeness (need at least some context)
        profile_score = self._calculate_profile_score(profile)
        if profile_score < 2:
            return {
                "viable": False,
                "reason": "Profile too sparse for quick start. Run 'day profile' to set it up.",
            }

        # Get incomplete tasks
        incomplete = self.task_import.get_incomplete_tasks(yesterday)

        return {
            "viable": True,
            "source": "yesterday",
            "source_date": yesterday_id,
            "source_plan": yesterday.agent_state.plan,
            "incomplete_tasks": incomplete,
        }

    def _calculate_profile_score(self, profile: UserProfile) -> int:
        """Calculate profile completeness score (0-10)."""
        score = 0

        if profile.top_priorities:
            score += 2
        if profile.work_hours.start != "09:00" or profile.work_hours.end != "17:00":
            score += 1  # User customized work hours
        if profile.recurring_tasks:
            score += 2
        if profile.blocked_times:
            score += 1
        if profile.productivity_habits.peak_productivity_time:
            score += 1
        if profile.planning_history.sessions_completed > 0:
            score += 2
        if profile.work_context.job_role:
            score += 1

        return score

    def _display_quick_start_info(self, viability: dict, session_id: str) -> None:
        """Display information about the quick start."""
        self.console.print(f"\n[bold cyan]Quick Start for {session_id}[/bold cyan]")
        self.console.print(f"[dim]Based on: {viability['source_date']}[/dim]")

        if viability.get("incomplete_tasks"):
            count = len(viability["incomplete_tasks"])
            self.console.print(
                f"[yellow]Carrying over {count} incomplete task(s) from yesterday[/yellow]"
            )

        self.console.print()

    async def _generate_quick_plan(
        self,
        session_id: str,
        profile: UserProfile,
        source_plan: Plan,
        incomplete_tasks: List[ScheduleItem],
        source_date: str,
    ) -> Memory:
        """Generate a quick plan based on source plan and incomplete tasks."""
        # Prepare tasks for new day
        prepared_tasks = self.task_import.prepare_tasks_for_import(source_plan.schedule)

        # If there are incomplete tasks, prioritize them
        if incomplete_tasks:
            # Reset incomplete tasks
            reset_incomplete = self.task_import.prepare_tasks_for_import(incomplete_tasks)
            # Put incomplete tasks first (they're carry-overs)
            # But we need to be smart - don't duplicate if task name already exists
            existing_names = {t.task.lower() for t in prepared_tasks}
            unique_incomplete = [
                t for t in reset_incomplete if t.task.lower() not in existing_names
            ]
            prepared_tasks = unique_incomplete + prepared_tasks

        # Create plan
        plan = Plan(
            schedule=prepared_tasks,
            priorities=source_plan.priorities.copy() if source_plan.priorities else [],
            notes=f"Quick start based on {source_date}",
        )
        plan.calculate_total_duration()

        # Create session
        memory = Memory(
            metadata=SessionMetadata(
                session_id=session_id,
                created_at=datetime.now(),
                last_updated=datetime.now(),
            ),
            agent_state=AgentState(
                state=State.feedback,  # Skip questions, go straight to feedback
                plan=plan,
                questions_asked=True,  # Skip questions
                feedback_received=False,
            ),
            conversation=ConversationHistory(),
        )

        # Add system prompt
        from pathlib import Path

        prompt_path = Path("config/prompts/system.txt")
        if prompt_path.exists():
            with open(prompt_path) as f:
                memory.conversation.add_system(f.read())

        # Add context about quick start
        context = f"""QUICK START MODE:
This plan was generated using quick start based on {source_date}.
The user wants to follow a similar pattern to yesterday."""

        if incomplete_tasks:
            context += (
                f"\n\nCarried over {len(incomplete_tasks)} incomplete task(s) from yesterday."
            )

        memory.conversation.add_system(context)

        # Add profile context
        profile_context = self.agent._format_profile_context(profile)
        if profile_context:
            memory.conversation.add_system(f"USER PROFILE:\n{profile_context}")

        # Save initial session
        await self.storage.save_session(session_id, memory)

        return memory

    async def _handle_feedback(self, memory: Memory, session_id: str) -> None:
        """Handle feedback loop for quick start plan."""
        while memory.agent_state.state == State.feedback:
            # Display plan
            if memory.agent_state.plan:
                panel = self.plan_formatter.format_plan(memory.agent_state.plan)
                self.console.print(panel)

            # Get feedback
            self.console.print("\n[bold]Quick Start Plan Ready![/bold]")
            self.console.print(
                "[dim]Press Enter to accept, or type changes you'd like to make.[/dim]"
            )

            feedback = await self.input_handler.get_feedback()

            if feedback is None:
                # User accepts the plan
                memory.agent_state.state = State.done
                memory.agent_state.feedback_received = True
                await self.storage.save_session(session_id, memory)
                break

            # Process feedback through LLM
            agent_state = await self.agent.process_feedback(feedback, memory)
            memory.agent_state = agent_state
            await self.storage.save_session(session_id, memory)
