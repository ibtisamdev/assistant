"""Show template use case."""

import logging

from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from ...domain.models.template import DayTemplate
from ..container import Container

logger = logging.getLogger(__name__)


class ShowTemplateUseCase:
    """Use case: Display details of a template."""

    def __init__(self, container: Container):
        self.container = container
        self.storage = container.storage
        self.console = Console()

    async def execute(self, name: str) -> DayTemplate | None:
        """
        Display template details.

        Args:
            name: Template name to show

        Returns:
            Template if found, None otherwise
        """
        template = await self.storage.load_template(name)

        if not template:
            self.console.print(f"[bold red]Template '{name}' not found.[/bold red]")
            self.console.print("[dim]List templates with: day template list[/dim]")
            return None

        # Display template info
        self._display_template(template)
        return template

    def _display_template(self, template: DayTemplate) -> None:
        """Display template in a formatted panel."""
        # Header info
        info_lines = []
        if template.description:
            info_lines.append(f"[dim]{template.description}[/dim]")
        info_lines.append(f"Created: {template.created_at.strftime('%Y-%m-%d %H:%M')}")
        if template.last_used:
            info_lines.append(f"Last used: {template.last_used.strftime('%Y-%m-%d')}")
        info_lines.append(f"Times used: {template.use_count}")
        info_lines.append("")

        # Schedule table
        schedule_table = Table(show_header=True, box=None, padding=(0, 1))
        schedule_table.add_column("#", style="dim", width=3)
        schedule_table.add_column("Time", style="cyan", width=12)
        schedule_table.add_column("Task")
        schedule_table.add_column("Est.", justify="right", width=6)
        schedule_table.add_column("Priority", width=8)
        schedule_table.add_column("Category", width=12)

        total_minutes = 0
        for i, item in enumerate(template.schedule, 1):
            est = f"{item.estimated_minutes}m" if item.estimated_minutes else "-"
            if item.estimated_minutes:
                total_minutes += item.estimated_minutes

            priority_color = {"high": "red", "medium": "yellow", "low": "green"}.get(
                item.priority, "white"
            )
            category = item.category.value if item.category else "uncategorized"

            schedule_table.add_row(
                str(i),
                item.time,
                item.task,
                est,
                f"[{priority_color}]{item.priority}[/{priority_color}]",
                category,
            )

        # Summary
        summary_lines = []
        if template.priorities:
            summary_lines.append("\n[bold]Priorities:[/bold]")
            for p in template.priorities:
                summary_lines.append(f"  - {p}")

        if template.notes:
            summary_lines.append(f"\n[bold]Notes:[/bold]\n  {template.notes}")

        # Build content
        content_parts = [
            "\n".join(info_lines),
            "[bold]Schedule:[/bold]",
        ]

        # Create panel
        self.console.print(
            Panel(
                "\n".join(content_parts),
                title=f"Template: {template.name}",
                border_style="blue",
            )
        )
        self.console.print(schedule_table)

        if total_minutes > 0:
            hours = total_minutes // 60
            mins = total_minutes % 60
            time_str = f"{hours}h {mins}m" if hours else f"{mins}m"
            self.console.print(f"\n[dim]Total estimated time: {time_str}[/dim]")

        if summary_lines:
            self.console.print("\n".join(summary_lines))
