"""CLI entry point using Click."""

import asyncio
import logging
import sys
from pathlib import Path
from typing import Optional
import click
from rich.console import Console
from rich import print as rprint
from rich.logging import RichHandler

from ..application.config import AppConfig
from ..application.container import Container
from ..application.session_orchestrator import SessionOrchestrator
from ..domain.exceptions import SessionNotFound, LLMError, StorageError
from .profile_setup import ProfileSetupWizard

console = Console()


def setup_logging(level: str = "INFO"):
    """Configure logging with Rich handler."""
    logging.basicConfig(
        level=level,
        format="%(message)s",
        datefmt="[%X]",
        handlers=[RichHandler(rich_tracebacks=True, console=console)],
    )


@click.group()
@click.option("--debug", is_flag=True, help="Enable debug mode")
@click.option("--config", type=click.Path(exists=True), help="Config file path")
@click.pass_context
def cli(ctx, debug, config):
    """
    Daily Planning AI Agent

    Your personalized planning assistant for creating realistic daily plans.
    """
    # Setup logging
    log_level = "DEBUG" if debug else "INFO"
    setup_logging(log_level)

    # Load configuration
    try:
        env_file = Path(".env") if not config else Path(config).parent / ".env"
        app_config = AppConfig.load(env_file=env_file if env_file.exists() else None)

        if debug:
            app_config.debug = True
            app_config.log_level = "DEBUG"

        # Create container
        container = Container(app_config)

        # Store in context for subcommands
        ctx.ensure_object(dict)
        ctx.obj["container"] = container
        ctx.obj["config"] = app_config

    except Exception as e:
        console.print(f"[bold red]Configuration Error:[/bold red] {e}")
        sys.exit(1)


# ===== Quick Commands (Shortcuts) =====


@cli.command()
@click.option("--date", help="Session date (YYYY-MM-DD)")
@click.option("--new", is_flag=True, help="Force create new session")
@click.pass_context
def start(ctx, date, new):
    """Quick start - create or resume today's plan."""
    container = ctx.obj["container"]
    orchestrator = SessionOrchestrator(container)

    async def _start():
        try:
            memory = await orchestrator.run_new_session(date, force_new=new)
            rprint("\n[bold green]✓ Session complete![/bold green]\n")
        except KeyboardInterrupt:
            rprint("\n[yellow]Session interrupted. Progress saved.[/yellow]")
        except LLMError as e:
            rprint(f"\n[bold red]AI Service Error:[/bold red] {e}")
            rprint("[dim]Please try again in a few moments.[/dim]")
        except Exception as e:
            rprint(f"\n[bold red]Error:[/bold red] {e}")
            if ctx.obj["config"].debug:
                raise

    try:
        asyncio.run(_start())
    except KeyboardInterrupt:
        pass


@cli.command()
@click.pass_context
def list(ctx):
    """List all saved sessions."""
    container = ctx.obj["container"]
    storage = container.storage
    formatter = container.session_formatter

    async def _list():
        sessions = await storage.list_sessions()
        if not sessions:
            rprint("[yellow]No saved sessions found.[/yellow]")
            return

        table = formatter.format_session_list(sessions)
        console.print(table)

    asyncio.run(_list())


@cli.command()
@click.option("--date", help="Session date (defaults to today)")
@click.option("--start", help="Quick start task by name")
@click.option("--complete", help="Quick complete task by name")
@click.option("--skip", help="Quick skip task by name")
@click.option("--status", is_flag=True, help="Show progress status only")
@click.pass_context
def checkin(ctx, date, start, complete, skip, status):
    """Check in and track task progress (shortcut)."""
    from datetime import datetime
    from ..application.use_cases.checkin import CheckinUseCase
    from ..domain.exceptions import SessionNotFound

    container = ctx.obj["container"]
    use_case = CheckinUseCase(container)

    # Default to today
    session_id = date or datetime.now().strftime("%Y-%m-%d")

    async def _checkin():
        try:
            await use_case.execute(
                session_id=session_id,
                quick_start=start,
                quick_complete=complete,
                quick_skip=skip,
                show_status_only=status,
            )
        except SessionNotFound as e:
            rprint(f"[bold red]Error:[/bold red] {e}")
            rprint(f"[dim]Hint: Create a plan first with 'uv run plan start'[/dim]")
        except KeyboardInterrupt:
            rprint("\n[yellow]Check-in cancelled.[/yellow]")
        except Exception as e:
            rprint(f"\n[bold red]Error:[/bold red] {e}")
            if ctx.obj["config"].debug:
                raise

    try:
        asyncio.run(_checkin())
    except KeyboardInterrupt:
        pass


@cli.command(name="export")
@click.argument("date", required=False)
@click.option("--output", type=click.Path(), help="Output file path")
@click.pass_context
def export_shortcut(ctx, date, output):
    """Export plan to Markdown (shortcut for 'plan export')."""
    from datetime import datetime
    from pathlib import Path
    from ..application.use_cases.export_plan import ExportPlanUseCase
    from ..domain.exceptions import SessionNotFound

    container = ctx.obj["container"]
    use_case = ExportPlanUseCase(container)

    # Default to today
    session_id = date or datetime.now().strftime("%Y-%m-%d")
    output_path = Path(output) if output else None

    async def _export():
        try:
            await use_case.execute(session_id, output_path)
        except SessionNotFound as e:
            rprint(f"[bold red]Error:[/bold red] {e}")
            rprint(f"[dim]Hint: Create a plan first with 'uv run plan start'[/dim]")
        except Exception as e:
            rprint(f"\n[bold red]Error:[/bold red] {e}")
            if ctx.obj["config"].debug:
                raise

    try:
        asyncio.run(_export())
    except KeyboardInterrupt:
        pass


@cli.command(name="summary")
@click.argument("date", required=False)
@click.option("--output", type=click.Path(), help="Output file path")
@click.pass_context
def summary_shortcut(ctx, date, output):
    """Export end-of-day summary (shortcut for 'plan summary')."""
    from datetime import datetime
    from pathlib import Path
    from ..application.use_cases.export_summary import ExportSummaryUseCase
    from ..domain.exceptions import SessionNotFound

    container = ctx.obj["container"]
    use_case = ExportSummaryUseCase(container)

    # Default to today
    session_id = date or datetime.now().strftime("%Y-%m-%d")
    output_path = Path(output) if output else None

    async def _export():
        try:
            await use_case.execute(session_id, output_path)
        except SessionNotFound as e:
            rprint(f"[bold red]Error:[/bold red] {e}")
            rprint(f"[dim]Hint: Create a plan first with 'uv run plan start'[/dim]")
        except Exception as e:
            rprint(f"\n[bold red]Error:[/bold red] {e}")
            if ctx.obj["config"].debug:
                raise

    try:
        asyncio.run(_export())
    except KeyboardInterrupt:
        pass


@cli.command(name="export-all")
@click.argument("date", required=False)
@click.pass_context
def export_all_shortcut(ctx, date):
    """Export both plan and summary (shortcut for 'plan export-all')."""
    from datetime import datetime
    from ..application.use_cases.export_all import ExportAllUseCase
    from ..domain.exceptions import SessionNotFound

    container = ctx.obj["container"]
    use_case = ExportAllUseCase(container)

    # Default to today
    session_id = date or datetime.now().strftime("%Y-%m-%d")

    async def _export():
        try:
            await use_case.execute(session_id)
        except SessionNotFound as e:
            rprint(f"[bold red]Error:[/bold red] {e}")
            rprint(f"[dim]Hint: Create a plan first with 'uv run plan start'[/dim]")
        except Exception as e:
            rprint(f"\n[bold red]Error:[/bold red] {e}")
            if ctx.obj["config"].debug:
                raise

    try:
        asyncio.run(_export())
    except KeyboardInterrupt:
        pass


@cli.command()
@click.argument("section", required=False)
@click.option("--user-id", default="default", help="User profile ID")
@click.pass_context
def profile(ctx, section, user_id):
    """
    Setup or update user profile.

    Run without arguments for full setup, or specify a section:

    \b
    Sections:
      personal     - Personal info and communication style
      schedule     - Work hours and energy patterns
      productivity - Productivity habits and preferences
      wellness     - Health and wellness schedule
      work         - Work context and collaboration
      learning     - Learning preferences and goals
      priorities   - Top priorities and long-term goals
      tasks        - Recurring tasks
      blocked      - Blocked times
    """
    container = ctx.obj["container"]
    storage = container.storage
    wizard = ProfileSetupWizard()

    async def _setup_profile():
        try:
            # Load existing profile
            existing_profile = await storage.load_profile(user_id)

            # Run wizard
            if section:
                if not existing_profile:
                    rprint(
                        f"[yellow]No existing profile found for '{user_id}'. Creating new profile.[/yellow]\n"
                    )
                    from ..domain.models.profile import UserProfile

                    existing_profile = UserProfile(user_id=user_id)

                updated_profile = wizard.setup_section(section, existing_profile)
            else:
                # Full setup
                updated_profile = wizard.run_full_setup(existing_profile)

            # Save updated profile
            await storage.save_profile(user_id, updated_profile)
            rprint(f"\n[bold green]✓ Profile saved successfully![/bold green]")

        except KeyboardInterrupt:
            rprint("\n[yellow]Profile setup cancelled.[/yellow]")
        except Exception as e:
            rprint(f"\n[bold red]Error:[/bold red] {e}")
            if ctx.obj["config"].debug:
                raise

    try:
        asyncio.run(_setup_profile())
    except KeyboardInterrupt:
        pass


@cli.command()
@click.option("--user-id", default="default", help="User profile ID")
@click.pass_context
def show_profile(ctx, user_id):
    """Display current user profile."""
    container = ctx.obj["container"]
    storage = container.storage

    async def _show():
        try:
            profile = await storage.load_profile(user_id)
            if not profile:
                rprint(f"[yellow]No profile found for '{user_id}'.[/yellow]")
                rprint("[dim]Run 'uv run plan profile' to create one.[/dim]")
                return

            # Display profile in a readable format
            from rich.panel import Panel
            from rich.table import Table

            # Create summary table
            table = Table(show_header=False, box=None, padding=(0, 2))
            table.add_column("Field", style="cyan")
            table.add_column("Value")

            # Basic info
            if profile.personal_info.name:
                table.add_row("Name", profile.personal_info.name)
            if profile.personal_info.preferred_name:
                table.add_row("Preferred Name", profile.personal_info.preferred_name)
            table.add_row("Timezone", profile.timezone)
            table.add_row("Communication", profile.personal_info.communication_style)

            # Work schedule
            table.add_row("", "")  # Spacer
            table.add_row("[bold]Work Schedule[/bold]", "")
            work_days = ", ".join(profile.work_hours.days[:3])
            if len(profile.work_hours.days) > 3:
                work_days += f", +{len(profile.work_hours.days) - 3} more"
            table.add_row("Hours", f"{profile.work_hours.start} - {profile.work_hours.end}")
            table.add_row("Days", work_days)

            # Energy
            table.add_row("", "")
            table.add_row("[bold]Energy Pattern[/bold]", "")
            table.add_row("Morning", profile.energy_pattern.morning)
            table.add_row("Afternoon", profile.energy_pattern.afternoon)
            table.add_row("Evening", profile.energy_pattern.evening)

            # Productivity
            if profile.productivity_habits.peak_productivity_time:
                table.add_row("", "")
                table.add_row("[bold]Productivity[/bold]", "")
                table.add_row("Peak Time", profile.productivity_habits.peak_productivity_time)
                table.add_row(
                    "Focus Length", f"{profile.productivity_habits.focus_session_length} min"
                )

            # Work context
            if profile.work_context.job_role:
                table.add_row("", "")
                table.add_row("[bold]Work Context[/bold]", "")
                table.add_row("Role", profile.work_context.job_role)

            # Priorities
            if profile.top_priorities:
                table.add_row("", "")
                table.add_row("[bold]Top Priorities[/bold]", "")
                for priority in profile.top_priorities[:3]:
                    table.add_row("•", priority)

            # Stats
            table.add_row("", "")
            table.add_row("[bold]Stats[/bold]", "")
            table.add_row("Sessions", str(profile.planning_history.sessions_completed))
            if profile.planning_history.last_session_date:
                table.add_row("Last Session", profile.planning_history.last_session_date)

            panel = Panel(
                table,
                title=f"User Profile: {user_id}",
                border_style="green",
            )
            console.print(panel)

        except Exception as e:
            rprint(f"\n[bold red]Error:[/bold red] {e}")
            if ctx.obj["config"].debug:
                raise

    asyncio.run(_show())


# Import command groups
from .commands.plan import plan_group
from .commands.session import session_group

cli.add_command(plan_group)
cli.add_command(session_group)


if __name__ == "__main__":
    cli()
