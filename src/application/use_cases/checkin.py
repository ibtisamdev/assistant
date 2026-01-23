"""Check-in use case - time tracking workflow."""

import logging
from datetime import datetime

from rich.console import Console
from rich.panel import Panel
from rich.prompt import Confirm, Prompt
from rich.table import Table

from ...domain.exceptions import SessionNotFound
from ...domain.models.planning import TaskCategory, TaskStatus
from ...domain.models.session import Memory
from ...domain.services.time_tracking_service import TimeTrackingService
from ..container import Container

logger = logging.getLogger(__name__)


class CheckinUseCase:
    """Use case: Interactive time tracking and check-in workflow."""

    def __init__(self, container: Container):
        self.container = container
        self.storage = container.storage
        self.tracking_service = TimeTrackingService()
        self.plan_formatter = container.plan_formatter
        self.console = Console()

    async def execute(
        self,
        session_id: str,
        quick_start: str | None = None,
        quick_complete: str | None = None,
        quick_skip: str | None = None,
        show_status_only: bool = False,
    ) -> Memory:
        """
        Execute check-in workflow.

        Args:
            session_id: Session identifier (usually YYYY-MM-DD)
            quick_start: Task name to start (quick mode)
            quick_complete: Task name to complete (quick mode)
            quick_skip: Task name to skip (quick mode)
            show_status_only: Only show status, don't enter interactive mode

        Returns:
            Updated memory

        Raises:
            SessionNotFound: If session doesn't exist
        """
        # Load session
        memory = await self.storage.load_session(session_id)
        if not memory or not memory.agent_state.plan:
            raise SessionNotFound(f"No plan found for {session_id}")

        plan = memory.agent_state.plan

        # Quick actions
        if quick_start:
            await self._quick_start_task(memory, quick_start)
            return memory

        if quick_complete:
            await self._quick_complete_task(memory, quick_complete)
            return memory

        if quick_skip:
            await self._quick_skip_task(memory, quick_skip)
            return memory

        # Show status
        self._display_plan_with_progress(plan)

        if show_status_only:
            self._display_stats(plan)
            return memory

        # Interactive mode
        await self._interactive_menu(memory)
        return memory

    async def _interactive_menu(self, memory: Memory) -> None:
        """Run interactive check-in menu."""
        plan = memory.agent_state.plan

        while True:
            self.console.print("\n[bold cyan]What would you like to do?[/bold cyan]")
            self.console.print("1. 📋 View plan with progress")
            self.console.print("2. ▶️  Start a task")
            self.console.print("3. ✅ Complete current/next task")
            self.console.print("4. ⏭️  Skip a task")
            self.console.print("5. 📊 View progress stats")
            self.console.print("6. ✏️  Edit task times")
            self.console.print("7. 🏷️  Edit task categories")
            self.console.print("8. 🚪 Exit")

            choice = Prompt.ask(
                "\n[bold yellow]Choose an option[/bold yellow]",
                choices=["1", "2", "3", "4", "5", "6", "7", "8"],
                default="8",
            )

            if choice == "1":
                self._display_plan_with_progress(plan)
            elif choice == "2":
                await self._interactive_start_task(memory)
            elif choice == "3":
                await self._interactive_complete_task(memory)
            elif choice == "4":
                await self._interactive_skip_task(memory)
            elif choice == "5":
                self._display_stats(plan)
            elif choice == "6":
                await self._interactive_edit_times(memory)
            elif choice == "7":
                await self._interactive_edit_categories(memory)
            elif choice == "8":
                self.console.print("[green]✓ Check-in complete![/green]")
                break

            # Save after each action
            await self.storage.save_session(memory.metadata.session_id, memory)

    async def _interactive_start_task(self, memory: Memory) -> None:
        """Interactive task start."""
        plan = memory.agent_state.plan
        assert plan is not None  # Verified in execute()

        # Show pending tasks
        pending = [item for item in plan.schedule if item.status == TaskStatus.not_started]

        if not pending:
            self.console.print("[yellow]No pending tasks to start[/yellow]")
            return

        # Display pending tasks
        self.console.print("\n[bold]Pending tasks:[/bold]")
        for i, item in enumerate(pending, 1):
            est_time = f" (~{item.estimated_minutes}m)" if item.estimated_minutes else ""
            self.console.print(f"{i}. {item.task}{est_time}")

        # Suggest current task based on time
        current = self.tracking_service.get_current_task(plan)
        if current and current in pending:
            current_idx = pending.index(current) + 1
            self.console.print(
                f"\n[dim]💡 Suggestion: Task {current_idx} matches current time[/dim]"
            )

        # Get choice
        choice = Prompt.ask(
            "\n[bold yellow]Select task to start[/bold yellow]",
            choices=[str(i) for i in range(1, len(pending) + 1)],
        )

        task = pending[int(choice) - 1]

        # Start task
        try:
            self.tracking_service.start_task(task)
            self.console.print(f"[green]✓ Started: {task.task}[/green]")
        except ValueError as e:
            self.console.print(f"[red]Error: {e}[/red]")

    async def _interactive_complete_task(self, memory: Memory) -> None:
        """Interactive task completion."""
        plan = memory.agent_state.plan
        assert plan is not None  # Verified in execute()

        # Find in-progress or next task
        next_task = self.tracking_service.get_next_task(plan)

        if not next_task:
            self.console.print("[yellow]No tasks to complete[/yellow]")
            return

        # Confirm completion
        confirm = Confirm.ask(
            f"\n[bold yellow]Complete task: {next_task.task}?[/bold yellow]", default=True
        )

        if confirm:
            try:
                self.tracking_service.complete_task(next_task)
                actual = next_task.actual_minutes or 0
                est = next_task.estimated_minutes or 0
                variance = next_task.time_variance or 0

                self.console.print(f"[green]✓ Completed: {next_task.task}[/green]")
                self.console.print(
                    f"[dim]  Actual: {actual}m | Estimated: {est}m | Variance: {variance:+d}m[/dim]"
                )
            except ValueError as e:
                self.console.print(f"[red]Error: {e}[/red]")

    async def _interactive_skip_task(self, memory: Memory) -> None:
        """Interactive task skip."""
        plan = memory.agent_state.plan
        assert plan is not None  # Verified in execute()

        # Show tasks that can be skipped
        skippable = [
            item
            for item in plan.schedule
            if item.status in [TaskStatus.not_started, TaskStatus.in_progress]
        ]

        if not skippable:
            self.console.print("[yellow]No tasks to skip[/yellow]")
            return

        # Display skippable tasks
        self.console.print("\n[bold]Tasks you can skip:[/bold]")
        for i, item in enumerate(skippable, 1):
            self.console.print(f"{i}. {item.task}")

        # Get choice
        choice = Prompt.ask(
            "\n[bold yellow]Select task to skip[/bold yellow]",
            choices=[str(i) for i in range(1, len(skippable) + 1)],
        )

        task = skippable[int(choice) - 1]

        # Get reason (optional)
        reason = Prompt.ask("[dim]Reason (optional)[/dim]", default="")

        # Skip task
        try:
            self.tracking_service.skip_task(task, reason if reason else None)
            self.console.print(f"[yellow]⊗ Skipped: {task.task}[/yellow]")
        except ValueError as e:
            self.console.print(f"[red]Error: {e}[/red]")

    async def _interactive_edit_times(self, memory: Memory) -> None:
        """Interactive timestamp editing with audit trail."""
        plan = memory.agent_state.plan
        assert plan is not None  # Verified in execute()

        # Show tasks with timestamps
        tracked = [item for item in plan.schedule if item.actual_start or item.actual_end]

        if not tracked:
            self.console.print("[yellow]No tasks with timestamps to edit[/yellow]")
            return

        # Display tasks
        self.console.print("\n[bold]Tasks with timestamps:[/bold]")
        for i, item in enumerate(tracked, 1):
            start_str = item.actual_start.strftime("%H:%M") if item.actual_start else "N/A"
            end_str = item.actual_end.strftime("%H:%M") if item.actual_end else "N/A"
            self.console.print(f"{i}. {item.task} ({start_str} - {end_str})")

        # Get task choice
        task_choice = Prompt.ask(
            "\n[bold yellow]Select task to edit[/bold yellow]",
            choices=[str(i) for i in range(1, len(tracked) + 1)],
        )

        task = tracked[int(task_choice) - 1]

        # Get field choice
        field_choice = Prompt.ask(
            "[bold yellow]Edit start or end time?[/bold yellow]",
            choices=["start", "end"],
        )
        field = "actual_start" if field_choice == "start" else "actual_end"

        # Get new time
        time_str = Prompt.ask(f"[bold yellow]Enter new {field_choice} time (HH:MM)[/bold yellow]")

        # Parse time
        try:
            hour, minute = map(int, time_str.split(":"))
            today = datetime.now().replace(hour=hour, minute=minute, second=0, microsecond=0)
        except Exception:
            self.console.print("[red]Invalid time format[/red]")
            return

        # Get reason
        reason = Prompt.ask("[bold yellow]Reason for edit[/bold yellow]")

        # Edit timestamp
        try:
            self.tracking_service.edit_timestamp(task, field, today, reason)
            self.console.print(f"[green]✓ Updated {field_choice} time for: {task.task}[/green]")
            self.console.print(f"[dim]  Reason: {reason}[/dim]")
        except ValueError as e:
            self.console.print(f"[red]Error: {e}[/red]")

    async def _quick_start_task(self, memory: Memory, task_name: str) -> None:
        """Quick start a task by name."""
        plan = memory.agent_state.plan
        assert plan is not None  # Verified in execute()
        task = self.tracking_service.find_task_by_name(plan, task_name)

        if not task:
            self.console.print(f"[red]Task not found: {task_name}[/red]")
            return

        try:
            self.tracking_service.start_task(task)
            self.console.print(f"[green]✓ Started: {task.task}[/green]")
            await self.storage.save_session(memory.metadata.session_id, memory)
        except ValueError as e:
            self.console.print(f"[red]Error: {e}[/red]")

    async def _quick_complete_task(self, memory: Memory, task_name: str) -> None:
        """Quick complete a task by name."""
        plan = memory.agent_state.plan
        assert plan is not None  # Verified in execute()
        task = self.tracking_service.find_task_by_name(plan, task_name)

        if not task:
            self.console.print(f"[red]Task not found: {task_name}[/red]")
            return

        try:
            self.tracking_service.complete_task(task)
            self.console.print(f"[green]✓ Completed: {task.task}[/green]")
            await self.storage.save_session(memory.metadata.session_id, memory)
        except ValueError as e:
            self.console.print(f"[red]Error: {e}[/red]")

    async def _quick_skip_task(self, memory: Memory, task_name: str) -> None:
        """Quick skip a task by name."""
        plan = memory.agent_state.plan
        assert plan is not None  # Verified in execute()
        task = self.tracking_service.find_task_by_name(plan, task_name)

        if not task:
            self.console.print(f"[red]Task not found: {task_name}[/red]")
            return

        try:
            self.tracking_service.skip_task(task)
            self.console.print(f"[yellow]⊗ Skipped: {task.task}[/yellow]")
            await self.storage.save_session(memory.metadata.session_id, memory)
        except ValueError as e:
            self.console.print(f"[red]Error: {e}[/red]")

    async def _interactive_edit_categories(self, memory: Memory) -> None:
        """Interactive category editing for tasks."""
        plan = memory.agent_state.plan
        assert plan is not None  # Verified in execute()

        # Category colors for display
        category_colors = {
            "productive": "green",
            "meetings": "blue",
            "admin": "yellow",
            "breaks": "cyan",
            "wasted": "red",
            "uncategorized": "dim",
        }

        # Display all tasks with their current categories
        self.console.print("\n[bold]Current task categories:[/bold]")
        for i, item in enumerate(plan.schedule, 1):
            color = category_colors.get(item.category.value, "white")
            self.console.print(f"{i}. {item.task[:40]} - [{color}]{item.category.value}[/{color}]")

        # Get task choice
        task_choice = Prompt.ask(
            "\n[bold yellow]Select task to re-categorize (or 'all' for all)[/bold yellow]",
            choices=[str(i) for i in range(1, len(plan.schedule) + 1)] + ["all"],
        )

        # Get available categories (excluding 'uncategorized')
        category_choices = [c.value for c in TaskCategory if c != TaskCategory.uncategorized]

        if task_choice == "all":
            # Bulk edit all tasks
            self.console.print("\n[bold]Select new category for ALL tasks:[/bold]")
            for cat in category_choices:
                color = category_colors.get(cat, "white")
                self.console.print(f"  [{color}]{cat}[/{color}]")

            new_category = Prompt.ask(
                "\n[bold yellow]New category[/bold yellow]",
                choices=category_choices,
            )

            # Apply to all tasks
            for item in plan.schedule:
                item.category = TaskCategory(new_category)

            self.console.print(
                f"[green]✓ Updated all {len(plan.schedule)} tasks to '{new_category}'[/green]"
            )
        else:
            # Single task edit
            task = plan.schedule[int(task_choice) - 1]

            self.console.print(f"\n[bold]Current category:[/bold] {task.category.value}")
            self.console.print("[bold]Available categories:[/bold]")
            for cat in category_choices:
                color = category_colors.get(cat, "white")
                self.console.print(f"  [{color}]{cat}[/{color}]")

            new_category = Prompt.ask(
                "\n[bold yellow]New category[/bold yellow]",
                choices=category_choices,
            )

            task.category = TaskCategory(new_category)
            self.console.print(f"[green]✓ Updated '{task.task[:30]}' to '{new_category}'[/green]")

    def _display_plan_with_progress(self, plan) -> None:
        """Display plan with progress indicators."""
        # Category colors
        category_colors = {
            "productive": "green",
            "meetings": "blue",
            "admin": "yellow",
            "breaks": "cyan",
            "wasted": "red",
            "uncategorized": "dim",
        }

        table = Table(title="Today's Plan")
        table.add_column("Status", style="cyan", width=6)
        table.add_column("Time", style="blue", width=13)
        table.add_column("Task", style="white")
        table.add_column("Category", width=12)
        table.add_column("Est.", justify="right", width=6)
        table.add_column("Act.", justify="right", width=6)

        for item in plan.schedule:
            # Status icon
            if item.status == TaskStatus.completed:
                status = "[green]✓[/green]"
            elif item.status == TaskStatus.in_progress:
                status = "[yellow]►[/yellow]"
            elif item.status == TaskStatus.skipped:
                status = "[dim]⊗[/dim]"
            else:
                status = "[ ]"

            # Category with color
            cat_color = category_colors.get(item.category.value, "white")
            category = f"[{cat_color}]{item.category.value}[/{cat_color}]"

            # Time estimates
            est = f"{item.estimated_minutes}m" if item.estimated_minutes else "-"
            act = f"{item.actual_minutes}m" if item.actual_minutes else "-"

            table.add_row(status, item.time, item.task, category, est, act)

        self.console.print(table)

    def _display_stats(self, plan) -> None:
        """Display progress statistics."""
        stats = self.tracking_service.get_completion_stats(plan)

        panel_content = f"""
[bold]Progress Summary[/bold]

Tasks: {stats["completed"]}/{stats["total_tasks"]} completed ({stats["completion_rate"]}%)
  • Completed: {stats["completed"]}
  • In Progress: {stats["in_progress"]}
  • Not Started: {stats["not_started"]}
  • Skipped: {stats["skipped"]}

Time:
  • Estimated Total: {stats["estimated_total"]} minutes
  • Actual Total: {stats["actual_total"]} minutes
  • Total Variance: {stats["total_variance"]:+d} minutes
  • Average Variance: {stats["average_variance"]:+.1f} minutes per task
"""

        panel = Panel(panel_content, border_style="cyan", title="📊 Statistics")
        self.console.print(panel)
