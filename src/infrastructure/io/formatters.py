"""Rich-formatted output."""

from typing import List
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.text import Text
from rich import box
from ...domain.models.planning import Plan, Question
from ...domain.models.state import State

console = Console()


class PlanFormatter:
    """Rich-formatted plan display."""

    @staticmethod
    def format_plan(plan: Plan) -> Panel:
        """Format plan as Rich panel."""
        # Create schedule table
        table = Table(show_header=True, header_style="bold magenta", box=box.SIMPLE, padding=(0, 1))
        table.add_column("Time", style="cyan", no_wrap=True)
        table.add_column("Task", style="white")

        for item in plan.schedule:
            table.add_row(item.time, item.task)

        # Create priorities section
        priorities_text = "\n".join([f"• {p}" for p in plan.priorities])

        # Calculate duration
        duration = plan.calculate_total_duration()
        hours = duration // 60
        minutes = duration % 60
        duration_str = f"{hours}h {minutes}m" if hours > 0 else f"{minutes}m"

        # Build content with proper sections
        from io import StringIO
        from rich.console import Console as RichConsole

        # Render table to string
        string_console = RichConsole(file=StringIO(), width=60)
        string_console.print(table)
        table_str = string_console.file.getvalue()

        # Combine into content
        content = Text()
        content.append("Schedule:\n", style="bold")
        content.append(table_str)
        content.append("\nTop Priorities:\n", style="bold")
        content.append(priorities_text)
        content.append(f"\n\nNotes: ", style="bold")
        content.append(plan.notes)
        content.append(f"\n\n⏱  Total time: {duration_str}", style="dim")

        return Panel(
            content,
            title="[bold green]📅 Your Daily Plan[/bold green]",
            border_style="green",
            padding=(1, 2),
        )

    @staticmethod
    def format_questions(questions: List[str]) -> Panel:
        """Format questions."""
        questions_text = "\n\n".join(
            [f"[bold cyan]{i + 1}.[/bold cyan] {q}" for i, q in enumerate(questions)]
        )

        return Panel(
            questions_text,
            title="[bold yellow]❓ Clarifying Questions[/bold yellow]",
            border_style="yellow",
            padding=(1, 2),
        )

    @staticmethod
    def format_plan_summary(plan: Plan) -> str:
        """Format plan as plain text summary (for LLM context)."""
        schedule_text = "\n".join([f"  {item.time}: {item.task}" for item in plan.schedule])
        priorities_text = "\n".join([f"  - {p}" for p in plan.priorities])

        return f"""Here's your daily plan:

Schedule:
{schedule_text}

Top Priorities:
{priorities_text}

Notes: {plan.notes}

What do you think? Any changes needed?"""


class SessionFormatter:
    """Session info formatting."""

    @staticmethod
    def format_session_list(sessions: List[dict]) -> Table:
        """Format session list as table."""
        from datetime import datetime

        table = Table(
            title="📋 Available Sessions",
            show_header=True,
            header_style="bold magenta",
            box=box.ROUNDED,
        )
        table.add_column("Date", style="cyan", no_wrap=True)
        table.add_column("State", style="yellow")
        table.add_column("Plan", justify="center")
        table.add_column("Last Updated", style="dim")

        today = datetime.now().strftime("%Y-%m-%d")

        for session in sessions:
            is_today = session["session_id"] == today
            date_str = (
                f"{session['session_id']} [bold](TODAY)[/bold]"
                if is_today
                else session["session_id"]
            )

            # State with emoji
            state_emoji = {"idle": "⏳", "questions": "❓", "feedback": "💬", "done": "✅"}
            state_str = f"{state_emoji.get(session['state'], '•')} {session['state']}"

            # Plan indicator
            plan_str = "✓" if session["has_plan"] else "✗"

            # Format timestamp
            try:
                dt = datetime.fromisoformat(session["last_updated"].replace("Z", "+00:00"))
                time_str = dt.strftime("%b %d, %H:%M")
            except Exception:
                time_str = "Unknown"

            table.add_row(date_str, state_str, plan_str, time_str)

        return table

    @staticmethod
    def format_session_info(info: dict) -> Panel:
        """Format detailed session info."""
        content = f"""
[bold]Session ID:[/bold] {info["session_id"]}
[bold]State:[/bold] {info["state"]}
[bold]Created:[/bold] {info["created_at"]}
[bold]Last Updated:[/bold] {info["last_updated"]}
[bold]LLM Calls:[/bold] {info["num_llm_calls"]}
[bold]Messages:[/bold] {info["num_messages"]}
"""

        return Panel(
            content.strip(),
            title="[bold]Session Information[/bold]",
            border_style="blue",
            padding=(1, 2),
        )


class ProgressFormatter:
    """Progress and status formatting."""

    @staticmethod
    def print_header(title: str) -> None:
        """Print section header."""
        console.print()
        console.rule(f"[bold cyan]{title}[/bold cyan]")
        console.print()

    @staticmethod
    def print_success(message: str) -> None:
        """Print success message."""
        console.print(f"[bold green]✓[/bold green] {message}")

    @staticmethod
    def print_error(message: str) -> None:
        """Print error message."""
        console.print(f"[bold red]✗[/bold red] {message}")

    @staticmethod
    def print_warning(message: str) -> None:
        """Print warning message."""
        console.print(f"[bold yellow]⚠[/bold yellow] {message}")

    @staticmethod
    def print_info(message: str) -> None:
        """Print info message."""
        console.print(f"[bold blue]ℹ[/bold blue] {message}")
