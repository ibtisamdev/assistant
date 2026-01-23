"""Import tasks use case - import incomplete tasks from previous sessions."""

from __future__ import annotations

import logging
from datetime import datetime
from typing import TYPE_CHECKING

from rich.console import Console
from rich.prompt import Confirm
from rich.table import Table

from ...domain.exceptions import SessionNotFound
from ...domain.models import ScheduleItem, TaskStatus
from ...domain.services.task_import_service import TaskImportService
from ..container import Container

if TYPE_CHECKING:
    from ...domain.models.session import Memory

logger = logging.getLogger(__name__)


class ImportTasksUseCase:
    """
    Use case: Import incomplete tasks from a previous session.

    This allows users to:
    - View incomplete tasks from yesterday (or another date)
    - Select which tasks to import
    - Add them to the current day's plan
    """

    def __init__(self, container: Container):
        self.container = container
        self.storage = container.storage
        self.task_import = TaskImportService()
        self.console = Console()

    async def execute(
        self,
        target_session_id: str | None = None,
        source_session_id: str | None = None,
        import_all: bool = False,
        include_skipped: bool = False,
    ) -> bool:
        """
        Import incomplete tasks from a previous session.

        Args:
            target_session_id: Session to import into (defaults to today)
            source_session_id: Session to import from (defaults to yesterday)
            import_all: Import all tasks without prompting
            include_skipped: Also include skipped tasks

        Returns:
            True if tasks were imported

        Raises:
            SessionNotFound: If target or source session doesn't exist
        """
        # Default dates
        if not target_session_id:
            target_session_id = datetime.now().strftime("%Y-%m-%d")

        if not source_session_id:
            source_session_id = self.task_import.get_yesterday_session_id(target_session_id)

        # Load source session
        source = await self.storage.load_session(source_session_id)
        if not source:
            raise SessionNotFound(f"No session found for {source_session_id}")

        if not source.agent_state.plan:
            raise SessionNotFound(f"No plan found in session {source_session_id}")

        # Load target session
        target = await self.storage.load_session(target_session_id)
        if not target:
            raise SessionNotFound(
                f"No session found for {target_session_id}. "
                f"Create a plan first with 'day start' or 'day quick'."
            )

        if not target.agent_state.plan:
            raise SessionNotFound(f"No plan found in session {target_session_id}")

        # Get incomplete tasks
        incomplete = self.task_import.get_incomplete_tasks(source)
        skipped = self.task_import.get_skipped_tasks(source) if include_skipped else []

        candidates = incomplete + skipped

        if not candidates:
            self.console.print(f"[green]No incomplete tasks from {source_session_id}.[/green]")
            return False

        # Display candidates
        self._display_candidates(candidates, source_session_id)

        # Select tasks to import
        if import_all:
            selected = candidates
        else:
            selected = await self._select_tasks(candidates)

        if not selected:
            self.console.print("[yellow]No tasks selected for import.[/yellow]")
            return False

        # Import selected tasks
        await self._import_tasks(target, selected, target_session_id)

        self.console.print(
            f"\n[bold green]Imported {len(selected)} task(s) to {target_session_id}![/bold green]"
        )
        self.console.print(f"[dim]View updated plan with: day show {target_session_id}[/dim]")

        return True

    def _display_candidates(self, tasks: list[ScheduleItem], source_date: str) -> None:
        """Display import candidates in a table."""
        self.console.print(f"\n[bold]Incomplete tasks from {source_date}:[/bold]\n")

        table = Table(show_header=True)
        table.add_column("#", style="dim", width=3)
        table.add_column("Task")
        table.add_column("Time", style="cyan", width=12)
        table.add_column("Status", width=12)
        table.add_column("Est.", justify="right", width=6)

        for i, task in enumerate(tasks, 1):
            status_style = {
                TaskStatus.not_started: "yellow",
                TaskStatus.in_progress: "blue",
                TaskStatus.skipped: "red",
            }.get(task.status, "white")

            est = f"{task.estimated_minutes}m" if task.estimated_minutes else "-"

            table.add_row(
                str(i),
                task.task,
                task.time,
                f"[{status_style}]{task.status.value}[/{status_style}]",
                est,
            )

        self.console.print(table)

    async def _select_tasks(self, tasks: list[ScheduleItem]) -> list[ScheduleItem]:
        """Let user select which tasks to import."""
        self.console.print("\n[bold]Select tasks to import:[/bold]")
        self.console.print("[dim]Enter task numbers (comma-separated), 'all', or 'none'[/dim]")

        selection = input("> ").strip().lower()

        if selection == "none" or selection == "n":
            return []

        if selection == "all" or selection == "a":
            return tasks

        # Parse comma-separated numbers
        try:
            indices = [int(x.strip()) - 1 for x in selection.split(",")]
            selected = [tasks[i] for i in indices if 0 <= i < len(tasks)]
            return selected
        except (ValueError, IndexError):
            self.console.print("[red]Invalid selection. Importing all tasks.[/red]")
            if Confirm.ask("Import all tasks?"):
                return tasks
            return []

    async def _import_tasks(
        self, target: Memory, tasks: list[ScheduleItem], session_id: str
    ) -> None:
        """Import tasks into target session."""
        if target.agent_state.plan is None:
            self.console.print("[red]No plan exists to import tasks into[/red]")
            return

        # Prepare tasks for new day
        prepared = self.task_import.prepare_tasks_for_import(tasks)

        # Merge into existing plan
        target.agent_state.plan = self.task_import.merge_imported_with_plan(
            prepared,
            target.agent_state.plan,
            position="start",  # Put imported tasks first
        )

        # Recalculate duration
        target.agent_state.plan.calculate_total_duration()

        # Update metadata
        target.metadata.last_updated = datetime.now()

        # Save
        await self.storage.save_session(session_id, target)


async def check_for_incomplete_tasks(storage, session_id: str) -> dict:
    """
    Check if there are incomplete tasks from yesterday.

    Helper function for use in create_plan auto-prompt.

    Returns:
        Dict with 'has_incomplete', 'count', 'tasks', 'source_date'
    """
    task_import = TaskImportService()
    yesterday_id = task_import.get_yesterday_session_id(session_id)

    yesterday = await storage.load_session(yesterday_id)
    if not yesterday or not yesterday.agent_state.plan:
        return {"has_incomplete": False, "count": 0, "tasks": [], "source_date": yesterday_id}

    incomplete = task_import.get_incomplete_tasks(yesterday)

    return {
        "has_incomplete": len(incomplete) > 0,
        "count": len(incomplete),
        "tasks": incomplete,
        "source_date": yesterday_id,
    }
