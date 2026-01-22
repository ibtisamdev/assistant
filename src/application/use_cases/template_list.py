"""List templates use case."""

import logging
from typing import List
from rich.console import Console
from rich.table import Table

from ...domain.models.template import TemplateMetadata
from ..container import Container

logger = logging.getLogger(__name__)


class ListTemplatesUseCase:
    """Use case: List all saved day templates."""

    def __init__(self, container: Container):
        self.container = container
        self.storage = container.storage
        self.console = Console()

    async def execute(self) -> List[TemplateMetadata]:
        """
        List all saved templates.

        Returns:
            List of template metadata
        """
        templates = await self.storage.list_templates()

        if not templates:
            self.console.print("[yellow]No templates found.[/yellow]")
            self.console.print("[dim]Create one with 'day template save <name>'[/dim]")
            return []

        # Display as table
        table = Table(title="Day Templates", show_header=True)
        table.add_column("Name", style="cyan")
        table.add_column("Description")
        table.add_column("Tasks", justify="right")
        table.add_column("Uses", justify="right")
        table.add_column("Last Used")

        for t in templates:
            last_used = t.last_used.strftime("%Y-%m-%d") if t.last_used else "Never"
            table.add_row(
                t.name,
                t.description[:40] + "..." if len(t.description) > 40 else t.description,
                str(t.task_count),
                str(t.use_count),
                last_used,
            )

        self.console.print(table)
        return templates
