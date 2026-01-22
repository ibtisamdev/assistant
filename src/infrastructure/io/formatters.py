"""Rich-formatted output."""

from typing import List, Dict
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.text import Text
from rich.progress import Progress, BarColumn, TextColumn
from rich import box
from ...domain.models.planning import Plan, Question, TaskStatus, ScheduleItem
from ...domain.models.state import State
from ...domain.models.metrics import DailyMetrics, AggregateMetrics, EstimationAccuracy

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

    @staticmethod
    def format_plan_with_progress(plan: Plan) -> Table:
        """
        Format plan with progress tracking indicators.
        Shows status, time tracking, and variance.
        """
        table = Table(
            title="📋 Today's Plan with Progress",
            show_header=True,
            header_style="bold magenta",
            box=box.ROUNDED,
            padding=(0, 1),
        )

        table.add_column("Status", style="cyan", justify="center", width=6)
        table.add_column("Time", style="blue", no_wrap=True, width=13)
        table.add_column("Task", style="white")
        table.add_column("Est.", justify="right", width=8)
        table.add_column("Act.", justify="right", width=8)
        table.add_column("Var.", justify="right", width=8)

        for item in plan.schedule:
            # Status icon with color
            if item.status == TaskStatus.completed:
                status = "[green]✓[/green]"
            elif item.status == TaskStatus.in_progress:
                status = "[yellow]►[/yellow]"
            elif item.status == TaskStatus.skipped:
                status = "[dim]⊗[/dim]"
            else:
                status = "[dim][ ][/dim]"

            # Time estimates
            est = f"{item.estimated_minutes}m" if item.estimated_minutes else "-"
            act = f"{item.actual_minutes}m" if item.actual_minutes else "-"

            # Variance with color coding
            if item.time_variance is not None:
                var = item.time_variance
                if var > 10:
                    var_str = f"[red]+{var}m[/red]"  # Significantly over
                elif var > 0:
                    var_str = f"[yellow]+{var}m[/yellow]"  # Slightly over
                elif var < -10:
                    var_str = f"[green]{var}m[/green]"  # Significantly under
                else:
                    var_str = f"[dim]{var}m[/dim]"  # Slightly under
            else:
                var_str = "[dim]-[/dim]"

            # Task name - dim if completed or skipped
            task_style = (
                "dim" if item.status in [TaskStatus.completed, TaskStatus.skipped] else "white"
            )
            task_text = f"[{task_style}]{item.task}[/{task_style}]"

            table.add_row(status, item.time, task_text, est, act, var_str)

        return table

    @staticmethod
    def format_progress_stats(stats: Dict) -> Panel:
        """
        Format detailed progress statistics.

        Args:
            stats: Dictionary from TimeTrackingService.get_completion_stats()
        """
        # Calculate completion bar
        completion_rate = stats["completion_rate"]
        bar_width = 30
        filled = int(bar_width * completion_rate / 100)
        bar = "█" * filled + "░" * (bar_width - filled)

        # Color code the bar
        if completion_rate >= 80:
            bar_color = "green"
        elif completion_rate >= 50:
            bar_color = "yellow"
        else:
            bar_color = "red"

        # Format time variance
        avg_var = stats["average_variance"]
        if avg_var > 10:
            var_color = "red"
            var_status = "⚠ Underestimating"
        elif avg_var < -10:
            var_color = "green"
            var_status = "✓ Overestimating (good buffer!)"
        else:
            var_color = "cyan"
            var_status = "✓ Accurate estimates"

        content = f"""
[bold]Task Progress[/bold]
[{bar_color}]{bar}[/{bar_color}] {completion_rate}%

[bold]Task Status[/bold]
  ✓ Completed:    {stats["completed"]}
  ► In Progress:  {stats["in_progress"]}
  • Not Started:  {stats["not_started"]}
  ⊗ Skipped:      {stats["skipped"]}
  ─────────────
  📊 Total:       {stats["total_tasks"]}

[bold]Time Tracking[/bold]
  Estimated:      {stats["estimated_total"]} minutes
  Actual:         {stats["actual_total"]} minutes
  Variance:       [{var_color}]{stats["total_variance"]:+d} minutes[/{var_color}]
  Avg per task:   [{var_color}]{avg_var:+.1f} minutes[/{var_color}]
  
[bold]Accuracy[/bold]
  {var_status}
"""

        return Panel(
            content.strip(),
            title="[bold cyan]📊 Progress Statistics[/bold cyan]",
            border_style="cyan",
            padding=(1, 2),
        )

    @staticmethod
    def format_time_comparison_table(plan: Plan) -> Table:
        """
        Format detailed time comparison table for completed tasks.
        """
        table = Table(
            title="⏱️  Estimated vs Actual Time",
            show_header=True,
            header_style="bold magenta",
            box=box.ROUNDED,
        )

        table.add_column("Task", style="white")
        table.add_column("Estimated", justify="right", style="cyan")
        table.add_column("Actual", justify="right", style="blue")
        table.add_column("Variance", justify="right")
        table.add_column("Accuracy", justify="center")

        completed_tasks = [item for item in plan.schedule if item.is_completed]

        if not completed_tasks:
            return table

        for item in completed_tasks:
            est = item.estimated_minutes or 0
            act = item.actual_minutes or 0
            var = item.time_variance or 0

            # Calculate accuracy percentage
            if est > 0:
                accuracy = 100 - (abs(var) / est * 100)
                accuracy_str = f"{accuracy:.0f}%"

                # Color code accuracy
                if accuracy >= 90:
                    accuracy_color = "green"
                elif accuracy >= 70:
                    accuracy_color = "yellow"
                else:
                    accuracy_color = "red"
            else:
                accuracy_str = "N/A"
                accuracy_color = "dim"

            # Variance with color
            if var > 0:
                var_str = f"[red]+{var}m[/red]"
            elif var < 0:
                var_str = f"[green]{var}m[/green]"
            else:
                var_str = "[cyan]0m[/cyan]"

            table.add_row(
                item.task,
                f"{est}m",
                f"{act}m",
                var_str,
                f"[{accuracy_color}]{accuracy_str}[/{accuracy_color}]",
            )

        return table


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


class MetricsFormatter:
    """Productivity metrics formatting."""

    @staticmethod
    def _format_minutes(minutes: int) -> str:
        """Format minutes as hours and minutes."""
        if minutes < 60:
            return f"{minutes}m"
        hours = minutes // 60
        mins = minutes % 60
        if mins == 0:
            return f"{hours}h"
        return f"{hours}h {mins}m"

    @staticmethod
    def format_daily_metrics(metrics: DailyMetrics) -> Panel:
        """Format daily metrics as Rich panel."""
        # Header stats
        completion_bar_width = 30
        filled = int(completion_bar_width * metrics.completion_rate / 100)
        completion_bar = "█" * filled + "░" * (completion_bar_width - filled)

        # Color based on completion rate
        if metrics.completion_rate >= 80:
            bar_color = "green"
        elif metrics.completion_rate >= 50:
            bar_color = "yellow"
        else:
            bar_color = "red"

        # Time variance coloring
        variance = metrics.time_variance
        if variance > 30:
            var_color = "red"
            var_sign = "+"
        elif variance > 0:
            var_color = "yellow"
            var_sign = "+"
        elif variance < -30:
            var_color = "green"
            var_sign = ""
        else:
            var_color = "cyan"
            var_sign = "" if variance < 0 else "+"

        planned_str = MetricsFormatter._format_minutes(metrics.total_planned_minutes)
        actual_str = MetricsFormatter._format_minutes(metrics.total_actual_minutes)
        variance_str = MetricsFormatter._format_minutes(abs(variance))

        # Build header section
        header = f"""[bold]Completion Rate:[/bold] [{bar_color}]{completion_bar}[/{bar_color}] {metrics.completion_rate:.0f}%
[bold]Tasks:[/bold] {metrics.completed_tasks}/{metrics.total_tasks} completed"""

        if metrics.skipped_tasks > 0:
            header += f", {metrics.skipped_tasks} skipped"
        if metrics.in_progress_tasks > 0:
            header += f", {metrics.in_progress_tasks} in progress"

        header += f"""

[bold]Time:[/bold] {planned_str} planned → {actual_str} actual ([{var_color}]{var_sign}{variance_str}[/{var_color}])"""

        return Panel(
            header,
            title=f"[bold cyan]📊 Daily Stats: {metrics.date}[/bold cyan]",
            border_style="cyan",
            padding=(1, 2),
        )

    @staticmethod
    def format_category_breakdown(metrics: DailyMetrics) -> Table:
        """Format time by category as a table with distribution bars."""
        table = Table(
            title="Time by Category",
            show_header=True,
            header_style="bold magenta",
            box=box.ROUNDED,
            padding=(0, 1),
        )

        table.add_column("Category", style="cyan", width=12)
        table.add_column("Time", justify="right", width=8)
        table.add_column("Distribution", width=30)

        # Calculate total for percentages
        total_time = sum(metrics.time_by_category.values())

        # Category colors
        category_colors = {
            "productive": "green",
            "meetings": "blue",
            "admin": "yellow",
            "breaks": "cyan",
            "wasted": "red",
            "uncategorized": "dim",
        }

        # Sort categories by time (descending)
        sorted_cats = sorted(metrics.time_by_category.items(), key=lambda x: x[1], reverse=True)

        for category, minutes in sorted_cats:
            if minutes == 0:
                continue

            percentage = (minutes / total_time * 100) if total_time > 0 else 0
            bar_width = int(percentage / 100 * 20)
            bar = "█" * bar_width

            color = category_colors.get(category, "white")
            time_str = MetricsFormatter._format_minutes(minutes)

            table.add_row(
                f"[{color}]{category.title()}[/{color}]",
                time_str,
                f"[{color}]{bar}[/{color}] {percentage:.0f}%",
            )

        return table

    @staticmethod
    def format_estimation_accuracy(accuracy: EstimationAccuracy) -> Panel:
        """Format estimation accuracy section."""
        # Determine overall accuracy status
        if accuracy.tasks_within_15min_percent >= 80:
            status_icon = "✓"
            status_color = "green"
            status_text = "Excellent estimation accuracy!"
        elif accuracy.tasks_within_15min_percent >= 60:
            status_icon = "•"
            status_color = "yellow"
            status_text = "Good accuracy, room for improvement"
        else:
            status_icon = "⚠"
            status_color = "red"
            status_text = "Estimates need calibration"

        # Variance direction
        if accuracy.avg_variance > 5:
            direction = "Tasks took longer than planned"
            direction_color = "yellow"
        elif accuracy.avg_variance < -5:
            direction = "Tasks finished faster than planned"
            direction_color = "green"
        else:
            direction = "Estimates were accurate"
            direction_color = "cyan"

        content = f"""[{status_color}]{status_icon} {status_text}[/{status_color}]

[bold]Metrics:[/bold]
  • Average variance: [{direction_color}]{accuracy.avg_variance:+.0f} min[/{direction_color}] ({direction})
  • Tasks within ±15 min: {accuracy.tasks_within_15min}/{accuracy.total_tasks_with_tracking} ({accuracy.tasks_within_15min_percent:.0f}%)
  • Underestimated: {accuracy.underestimated_count} tasks
  • Overestimated: {accuracy.overestimated_count} tasks"""

        if accuracy.most_underestimated:
            content += f'\n\n[bold]Most underestimated:[/bold] "{accuracy.most_underestimated}"'
        if accuracy.most_overestimated:
            content += f'\n[bold]Most overestimated:[/bold] "{accuracy.most_overestimated}"'

        return Panel(
            content,
            title="[bold yellow]⏱️  Estimation Accuracy[/bold yellow]",
            border_style="yellow",
            padding=(1, 2),
        )

    @staticmethod
    def format_top_consumers(metrics: DailyMetrics) -> Table:
        """Format top time-consuming tasks."""
        table = Table(
            title="Top Time Consumers",
            show_header=True,
            header_style="bold magenta",
            box=box.ROUNDED,
            padding=(0, 1),
        )

        table.add_column("#", style="dim", width=3)
        table.add_column("Task", style="white")
        table.add_column("Category", style="cyan", width=12)
        table.add_column("Time", justify="right", width=8)

        for i, task in enumerate(metrics.top_time_consumers, 1):
            time_val = task.actual_minutes or task.estimated_minutes or 0
            time_str = MetricsFormatter._format_minutes(time_val)

            # Status indicator
            if task.status == "completed":
                status = "[green]✓[/green]"
            elif task.status == "in_progress":
                status = "[yellow]►[/yellow]"
            else:
                status = "[dim]•[/dim]"

            table.add_row(
                f"{status} {i}",
                task.task[:40] + "..." if len(task.task) > 40 else task.task,
                task.category.title(),
                time_str,
            )

        return table

    @staticmethod
    def format_aggregate_metrics(metrics: AggregateMetrics) -> Panel:
        """Format aggregate metrics header panel."""
        # Period description
        if metrics.period_type == "week":
            period_title = f"Weekly Summary: {metrics.period_start} to {metrics.period_end}"
        elif metrics.period_type == "month":
            period_title = f"Monthly Summary: {metrics.period_start} to {metrics.period_end}"
        else:
            period_title = f"Summary: {metrics.period_start} to {metrics.period_end}"

        # Days tracked
        days_str = f"{metrics.days_with_data} of {metrics.total_days} days tracked"

        # Time summary
        planned_str = MetricsFormatter._format_minutes(metrics.total_planned_minutes)
        actual_str = MetricsFormatter._format_minutes(metrics.total_actual_minutes)
        variance = metrics.total_actual_minutes - metrics.total_planned_minutes
        var_sign = "+" if variance >= 0 else ""
        var_str = MetricsFormatter._format_minutes(abs(variance))

        avg_planned = MetricsFormatter._format_minutes(int(metrics.avg_daily_planned_minutes))
        avg_actual = MetricsFormatter._format_minutes(int(metrics.avg_daily_actual_minutes))

        # Completion rate bar
        bar_width = 25
        filled = int(bar_width * metrics.avg_completion_rate / 100)
        bar = "█" * filled + "░" * (bar_width - filled)

        if metrics.avg_completion_rate >= 80:
            bar_color = "green"
        elif metrics.avg_completion_rate >= 50:
            bar_color = "yellow"
        else:
            bar_color = "red"

        content = f"""[bold]Days tracked:[/bold] {days_str}

[bold]Total Time:[/bold]
  Planned: {planned_str} | Actual: {actual_str} ({var_sign}{var_str})
  
[bold]Daily Average:[/bold]
  Planned: {avg_planned} | Actual: {avg_actual}

[bold]Completion Rate:[/bold]
  [{bar_color}]{bar}[/{bar_color}] {metrics.avg_completion_rate:.0f}%
  Total: {metrics.total_completed}/{metrics.total_tasks} tasks completed"""

        if metrics.best_day and metrics.worst_day:
            content += f"\n\n[bold]Best day:[/bold] {metrics.best_day} | [bold]Worst day:[/bold] {metrics.worst_day}"

        return Panel(
            content,
            title=f"[bold cyan]📈 {period_title}[/bold cyan]",
            border_style="cyan",
            padding=(1, 2),
        )

    @staticmethod
    def format_completion_trend(metrics: AggregateMetrics) -> Panel:
        """Format completion rate trend as ASCII chart."""
        if not metrics.completion_rate_by_day:
            return Panel("[dim]No data available[/dim]", title="Completion Trend")

        # Sort by date
        sorted_days = sorted(metrics.completion_rate_by_day.items())

        # Build trend visualization
        lines = []
        for date, rate in sorted_days:
            # Use just day name or short date
            from datetime import datetime

            try:
                day_dt = datetime.strptime(date, "%Y-%m-%d")
                day_label = day_dt.strftime("%a")  # Mon, Tue, etc.
            except ValueError:
                day_label = date[-5:]  # Fallback to MM-DD

            bar_width = int(rate / 100 * 20)
            bar = "█" * bar_width

            # Color based on rate
            if rate >= 80:
                color = "green"
            elif rate >= 50:
                color = "yellow"
            else:
                color = "red"

            lines.append(f"{day_label} │[{color}]{bar:<20}[/{color}] {rate:.0f}%")

        content = "\n".join(lines)

        return Panel(
            content,
            title="[bold magenta]📉 Completion Trend[/bold magenta]",
            border_style="magenta",
            padding=(1, 2),
        )

    @staticmethod
    def format_aggregate_categories(metrics: AggregateMetrics) -> Table:
        """Format aggregate category breakdown."""
        table = Table(
            title="Category Distribution (Total)",
            show_header=True,
            header_style="bold magenta",
            box=box.ROUNDED,
            padding=(0, 1),
        )

        table.add_column("Category", style="cyan", width=12)
        table.add_column("Total", justify="right", width=10)
        table.add_column("Avg/Day", justify="right", width=10)
        table.add_column("%", justify="right", width=8)

        category_colors = {
            "productive": "green",
            "meetings": "blue",
            "admin": "yellow",
            "breaks": "cyan",
            "wasted": "red",
            "uncategorized": "dim",
        }

        # Sort by total time
        sorted_cats = sorted(metrics.total_by_category.items(), key=lambda x: x[1], reverse=True)

        for category, total_mins in sorted_cats:
            if total_mins == 0:
                continue

            color = category_colors.get(category, "white")
            total_str = MetricsFormatter._format_minutes(total_mins)
            avg_mins = metrics.avg_daily_by_category.get(category, 0)
            avg_str = MetricsFormatter._format_minutes(int(avg_mins))
            pct = metrics.category_percentages.get(category, 0)

            table.add_row(
                f"[{color}]{category.title()}[/{color}]",
                total_str,
                avg_str,
                f"{pct:.0f}%",
            )

        return table

    @staticmethod
    def format_patterns(metrics: AggregateMetrics) -> Panel:
        """Format identified patterns."""
        if not metrics.patterns:
            return Panel(
                "[dim]Not enough data to identify patterns yet. Keep tracking![/dim]",
                title="[bold green]🔍 Patterns[/bold green]",
                border_style="green",
                padding=(1, 2),
            )

        pattern_icons = {
            "time_sink": "⚠",
            "improvement": "📈",
            "decline": "📉",
            "successful_habit": "✓",
            "peak_time": "⏰",
        }

        pattern_colors = {
            "time_sink": "yellow",
            "improvement": "green",
            "decline": "red",
            "successful_habit": "green",
            "peak_time": "cyan",
        }

        lines = []
        for pattern in metrics.patterns:
            icon = pattern_icons.get(pattern.pattern_type, "•")
            color = pattern_colors.get(pattern.pattern_type, "white")
            confidence_bar = "●" * int(pattern.confidence * 5) + "○" * (
                5 - int(pattern.confidence * 5)
            )

            lines.append(f"[{color}]{icon} {pattern.description}[/{color}]")
            lines.append(f"   [dim]Confidence: {confidence_bar}[/dim]")

        content = "\n".join(lines)

        return Panel(
            content,
            title="[bold green]🔍 Patterns Identified[/bold green]",
            border_style="green",
            padding=(1, 2),
        )
