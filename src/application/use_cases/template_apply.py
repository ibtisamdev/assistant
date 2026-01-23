"""Apply template use case."""

import logging
from datetime import datetime

from rich.console import Console
from rich.prompt import Confirm

from ...domain.models import AgentState, ConversationHistory, Memory, Plan, SessionMetadata, State
from ..container import Container

logger = logging.getLogger(__name__)


class ApplyTemplateUseCase:
    """Use case: Apply a saved template to create a new day's plan."""

    def __init__(self, container: Container):
        self.container = container
        self.storage = container.storage
        self.console = Console()

    async def execute(
        self,
        name: str,
        session_id: str | None = None,
        force: bool = False,
    ) -> bool:
        """
        Apply a template to create a new session.

        Args:
            name: Template name to apply
            session_id: Target session date (defaults to today)
            force: Overwrite existing session without prompt

        Returns:
            True if applied successfully
        """
        # Default to today
        if not session_id:
            session_id = datetime.now().strftime("%Y-%m-%d")

        # Load template
        template = await self.storage.load_template(name)
        if not template:
            self.console.print(f"[bold red]Template '{name}' not found.[/bold red]")
            self.console.print("[dim]List templates with: day template list[/dim]")
            return False

        # Check if session already exists
        existing = await self.storage.load_session(session_id)
        if existing and existing.agent_state.plan and not force:
            if not Confirm.ask(f"Session {session_id} already has a plan. Replace it?"):
                self.console.print("[yellow]Cancelled.[/yellow]")
                return False

        # Prepare template for new day (reset statuses)
        prepared = template.prepare_for_new_day()

        # Create plan from template
        plan = Plan(
            schedule=prepared.schedule,
            priorities=prepared.priorities,
            notes=prepared.notes,
        )
        plan.calculate_total_duration()

        # Create or update session
        if existing:
            # Update existing session with new plan
            existing.agent_state.plan = plan
            existing.agent_state.state = State.done
            existing.metadata.last_updated = datetime.now()
            memory = existing
        else:
            # Create new session
            memory = Memory(
                metadata=SessionMetadata(
                    session_id=session_id,
                    created_at=datetime.now(),
                    last_updated=datetime.now(),
                ),
                agent_state=AgentState(
                    state=State.done,
                    plan=plan,
                    questions_asked=True,
                    feedback_received=True,
                ),
                conversation=ConversationHistory(),
            )

        # Save session
        await self.storage.save_session(session_id, memory)

        # Update template usage stats
        template.record_use()
        await self.storage.save_template(name, template)

        # Display result
        self.console.print(f"[bold green]Template '{name}' applied to {session_id}![/bold green]")
        self.console.print(f"[dim]Created plan with {len(plan.schedule)} tasks[/dim]")
        self.console.print(f"[dim]View it with: day show {session_id}[/dim]")
        self.console.print("[dim]Track progress with: day checkin[/dim]")

        # Show plan summary
        formatter = self.container.plan_formatter
        panel = formatter.format_plan(plan)
        self.console.print("\n")
        self.console.print(panel)

        return True
