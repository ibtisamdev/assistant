"""Save template use case."""

import logging
from datetime import datetime

from rich.console import Console
from rich.prompt import Confirm

from ...domain.exceptions import SessionNotFound
from ...domain.models.template import DayTemplate
from ..container import Container

logger = logging.getLogger(__name__)


class SaveTemplateUseCase:
    """Use case: Save a day's plan as a reusable template."""

    def __init__(self, container: Container):
        self.container = container
        self.storage = container.storage
        self.console = Console()

    async def execute(
        self,
        name: str,
        session_id: str | None = None,
        description: str = "",
        force: bool = False,
    ) -> bool:
        """
        Save a day's plan as a template.

        Args:
            name: Template name (e.g., "work-day", "weekend")
            session_id: Session to save as template (defaults to today)
            description: Optional description
            force: Overwrite existing template without prompt

        Returns:
            True if saved successfully

        Raises:
            SessionNotFound: If session doesn't exist or has no plan
        """
        # Default to today
        if not session_id:
            session_id = datetime.now().strftime("%Y-%m-%d")

        # Load session
        memory = await self.storage.load_session(session_id)
        if not memory:
            raise SessionNotFound(f"No session found for {session_id}")

        if not memory.agent_state.plan:
            raise SessionNotFound(f"No plan found in session {session_id}")

        # Check if template already exists
        existing = await self.storage.template_exists(name)
        if existing and not force:
            if not Confirm.ask(f"Template '{name}' already exists. Overwrite?"):
                self.console.print("[yellow]Cancelled.[/yellow]")
                return False

        # Create template from plan
        plan = memory.agent_state.plan
        template = DayTemplate(
            name=name,
            description=description,
            schedule=plan.schedule,
            priorities=plan.priorities,
            notes=plan.notes,
            created_at=datetime.now(),
        )

        # Save template
        await self.storage.save_template(name, template)

        self.console.print(f"[bold green]Template '{name}' saved successfully![/bold green]")
        self.console.print(f"[dim]Contains {len(template.schedule)} tasks from {session_id}[/dim]")
        self.console.print(f"[dim]Apply it with: day template apply {name}[/dim]")

        return True
