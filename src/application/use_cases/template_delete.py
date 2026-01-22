"""Delete template use case."""

import logging
from rich.console import Console
from rich.prompt import Confirm

from ..container import Container

logger = logging.getLogger(__name__)


class DeleteTemplateUseCase:
    """Use case: Delete a saved template."""

    def __init__(self, container: Container):
        self.container = container
        self.storage = container.storage
        self.console = Console()

    async def execute(self, name: str, force: bool = False) -> bool:
        """
        Delete a template.

        Args:
            name: Template name to delete
            force: Skip confirmation

        Returns:
            True if deleted successfully
        """
        # Check if template exists
        template = await self.storage.load_template(name)
        if not template:
            self.console.print(f"[bold red]Template '{name}' not found.[/bold red]")
            return False

        # Confirm deletion
        if not force:
            self.console.print(f"Template '{name}' has {len(template.schedule)} tasks")
            self.console.print(f"Used {template.use_count} times")
            if not Confirm.ask(f"Delete template '{name}'?"):
                self.console.print("[yellow]Cancelled.[/yellow]")
                return False

        # Delete
        success = await self.storage.delete_template(name)

        if success:
            self.console.print(f"[bold green]Template '{name}' deleted.[/bold green]")
        else:
            self.console.print(f"[bold red]Failed to delete template '{name}'.[/bold red]")

        return success
