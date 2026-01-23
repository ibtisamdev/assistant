"""CLI entry point using Click."""

import asyncio
import logging
import sys
from datetime import datetime
from pathlib import Path

import click
from rich import print as rprint
from rich.console import Console
from rich.logging import RichHandler
from rich.prompt import Confirm

from ..application.config import AppConfig
from ..application.container import Container
from ..application.session_orchestrator import SessionOrchestrator
from ..domain.exceptions import LLMError, SessionNotFound, SetupRequired
from .profile_setup import ProfileSetupWizard
from .setup_wizard import SetupWizard

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
@click.version_option(version="0.1.0-dev", prog_name="planmyday")
@click.option("--debug", is_flag=True, help="Enable debug mode")
@click.option("--config", type=click.Path(exists=True), help="Config file path")
@click.option("--local", is_flag=True, help="Use current directory for data (dev mode)")
@click.pass_context
def cli(ctx, debug, config, local):
    """
    planmyday - Daily Planning AI Agent

    Your personalized assistant for creating realistic daily plans.

    \b
    Quick start:
      pday start          Create or resume today's plan
      pday checkin        Track task progress
      pday stats          View productivity metrics

    \b
    Full command: planmyday (alias: pday)
    """
    # Setup logging
    log_level = "DEBUG" if debug else "INFO"
    setup_logging(log_level)

    # Store context early for commands that don't need config (like setup)
    ctx.ensure_object(dict)
    ctx.obj["debug"] = debug
    ctx.obj["local"] = local

    # Skip config loading for setup command
    if ctx.invoked_subcommand == "setup":
        return

    # Load configuration
    try:
        env_file = Path(".env") if not config else Path(config).parent / ".env"
        app_config = AppConfig.load(
            env_file=env_file if env_file.exists() else None,
            use_local=local,
        )

        if debug:
            app_config.debug = True
            app_config.log_level = "DEBUG"

        # Create container
        container = Container(app_config)

        # Store in context for subcommands
        ctx.obj["container"] = container
        ctx.obj["config"] = app_config

    except SetupRequired as e:
        console.print(f"[bold yellow]Setup Required[/bold yellow]\n\n{e}")
        sys.exit(1)
    except Exception as e:
        console.print(f"[bold red]Configuration Error:[/bold red] {e}")
        if debug:
            raise
        sys.exit(1)


# ===== Setup & Configuration Commands =====


@cli.command()
@click.pass_context
def setup(ctx):
    """
    First-time setup wizard.

    Configures planmyday for first use:
    - Sets up OpenAI API key
    - Creates config and data directories
    - Validates configuration

    \b
    Run this once after installation:
      pday setup
    """
    wizard = SetupWizard()

    if wizard.is_configured():
        rprint("[yellow]planmyday is already configured.[/yellow]")
        rprint()
        wizard.show_config_paths()
        rprint()
        if not Confirm.ask("Do you want to reconfigure?"):
            return

    success = wizard.run()
    sys.exit(0 if success else 1)


@cli.command("config")
@click.option("--show", "show_config", is_flag=True, help="Show current configuration")
@click.option("--path", "show_path", is_flag=True, help="Show config file paths")
@click.option("--set-key", "set_api_key", is_flag=True, help="Update OpenAI API key")
@click.pass_context
def config_cmd(ctx, show_config, show_path, set_api_key):
    """
    View or update configuration.

    \b
    Examples:
      pday config --path     # Show config file locations
      pday config --show     # Display current config status
      pday config --set-key  # Update OpenAI API key
    """
    wizard = SetupWizard()

    if set_api_key:
        success = wizard.update_api_key()
        sys.exit(0 if success else 1)

    if show_path or (not show_config and not show_path and not set_api_key):
        wizard.show_config_paths()
        return

    if show_config:
        # Show detailed config if available
        if "config" in ctx.obj:
            app_config = ctx.obj["config"]
            rprint("[bold]Current Configuration:[/bold]")
            rprint()
            rprint(f"  Environment: {app_config.environment}")
            rprint(f"  Debug: {app_config.debug}")
            rprint(f"  LLM Provider: {app_config.llm.provider}")
            rprint(f"  LLM Model: {app_config.llm.model}")
            rprint(f"  Storage Backend: {app_config.storage.backend}")
            rprint(f"  Sessions Dir: {app_config.storage.sessions_dir}")
            rprint(f"  Profiles Dir: {app_config.storage.profiles_dir}")
        else:
            wizard.show_config_paths()


# ===== Core Planning Commands =====


@cli.command()
@click.argument("date", required=False)
@click.pass_context
def start(ctx, date):
    """Create or resume a daily plan (smart default)."""
    container = ctx.obj["container"]
    orchestrator = SessionOrchestrator(container)

    async def _start():
        try:
            await orchestrator.run_new_session(date, force_new=False)
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
@click.argument("date", required=False)
@click.option("--template", help="Use a saved template instead of yesterday's plan")
@click.pass_context
def quick(ctx, date, template):
    """
    Quick start - create plan from previous pattern.

    Uses yesterday's plan structure and carries over incomplete tasks.
    Skips clarifying questions for faster planning.

    Falls back to normal 'pday start' if no previous session exists.
    """
    from ..application.use_cases.quick_start import QuickStartUseCase

    container = ctx.obj["container"]
    use_case = QuickStartUseCase(container)
    orchestrator = SessionOrchestrator(container)

    async def _quick():
        try:
            result = await use_case.execute(date, from_template=template)

            if result is None:
                # Fall back to normal start
                rprint("[dim]Falling back to normal planning...[/dim]\n")
                await orchestrator.run_new_session(date, force_new=False)

            rprint("\n[bold green]Session complete![/bold green]\n")
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
        asyncio.run(_quick())
    except KeyboardInterrupt:
        pass


@cli.command()
@click.argument("date", required=False)
@click.pass_context
def revise(ctx, date):
    """Revise an existing plan."""
    container = ctx.obj["container"]
    orchestrator = SessionOrchestrator(container)

    async def _revise():
        try:
            rprint("[bold yellow]Revising plan...[/bold yellow]\n")
            await orchestrator.run_revise(date)
            rprint("\n[bold green]✓ Plan revised![/bold green]")
        except SessionNotFound as e:
            rprint(f"[bold red]Error:[/bold red] {e}")
            rprint("[dim]Hint: Create a plan first with 'pday start'[/dim]")
        except KeyboardInterrupt:
            rprint("\n[yellow]Cancelled. Progress saved.[/yellow]")
        except Exception as e:
            rprint(f"\n[bold red]Error:[/bold red] {e}")
            if ctx.obj["config"].debug:
                raise

    try:
        asyncio.run(_revise())
    except KeyboardInterrupt:
        pass


@cli.command()
@click.argument("date")
@click.pass_context
def show(ctx, date):
    """Display a saved plan."""
    container = ctx.obj["container"]

    async def _show():
        storage = container.storage
        memory = await storage.load_session(date)

        if not memory or not memory.agent_state.plan:
            rprint(f"[red]No plan found for {date}[/red]")
            rprint("[dim]Hint: Create a plan first with 'pday start'[/dim]")
            return

        formatter = container.plan_formatter
        panel = formatter.format_plan(memory.agent_state.plan)
        console.print(panel)

    asyncio.run(_show())


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


# ===== Task Import =====


@cli.command(name="import")
@click.argument("date", required=False)
@click.option("--from", "from_date", help="Source session date (defaults to yesterday)")
@click.option("--all", "import_all", is_flag=True, help="Import all without prompting")
@click.option("--include-skipped", is_flag=True, help="Also include skipped tasks")
@click.pass_context
def import_tasks(ctx, date, from_date, import_all, include_skipped):
    """
    Import incomplete tasks from a previous session.

    By default, imports from yesterday into today's plan.

    \b
    Examples:
      pday import                    # Import from yesterday to today
      pday import --from 2026-01-20  # Import from specific date
      pday import --all              # Import all without prompting
    """
    from ..application.use_cases.import_tasks import ImportTasksUseCase

    container = ctx.obj["container"]
    use_case = ImportTasksUseCase(container)

    async def _import():
        try:
            await use_case.execute(
                target_session_id=date,
                source_session_id=from_date,
                import_all=import_all,
                include_skipped=include_skipped,
            )
        except SessionNotFound as e:
            rprint(f"[bold red]Error:[/bold red] {e}")
            rprint("[dim]Hint: Create a plan first with 'pday start' or 'pday quick'[/dim]")
        except KeyboardInterrupt:
            rprint("\n[yellow]Import cancelled.[/yellow]")
        except Exception as e:
            rprint(f"\n[bold red]Error:[/bold red] {e}")
            if ctx.obj["config"].debug:
                raise

    try:
        asyncio.run(_import())
    except KeyboardInterrupt:
        pass


# ===== Time Tracking =====


@cli.command()
@click.argument("date", required=False)
@click.option("--start", help="Quick start task by name")
@click.option("--complete", help="Quick complete task by name")
@click.option("--skip", help="Quick skip task by name")
@click.option("--status", is_flag=True, help="Show progress status only")
@click.pass_context
def checkin(ctx, date, start, complete, skip, status):
    """Check in and track task progress."""
    from ..application.use_cases.checkin import CheckinUseCase

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
            rprint("[dim]Hint: Create a plan first with 'pday start'[/dim]")
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


# ===== Export Commands =====


@cli.command()
@click.argument("date", required=False)
@click.option("--output", type=click.Path(), help="Output file path")
@click.pass_context
def export(ctx, date, output):
    """Export plan to Markdown."""
    from ..application.use_cases.export_plan import ExportPlanUseCase

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
            rprint("[dim]Hint: Create a plan first with 'pday start'[/dim]")
        except Exception as e:
            rprint(f"\n[bold red]Error:[/bold red] {e}")
            if ctx.obj["config"].debug:
                raise

    try:
        asyncio.run(_export())
    except KeyboardInterrupt:
        pass


@cli.command()
@click.argument("date", required=False)
@click.option("--output", type=click.Path(), help="Output file path")
@click.pass_context
def summary(ctx, date, output):
    """Export end-of-day summary."""
    from ..application.use_cases.export_summary import ExportSummaryUseCase

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
            rprint("[dim]Hint: Create a plan first with 'pday start'[/dim]")
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
def export_all(ctx, date):
    """Export both plan and summary."""
    from ..application.use_cases.export_all import ExportAllUseCase

    container = ctx.obj["container"]
    use_case = ExportAllUseCase(container)

    # Default to today
    session_id = date or datetime.now().strftime("%Y-%m-%d")

    async def _export():
        try:
            await use_case.execute(session_id)
        except SessionNotFound as e:
            rprint(f"[bold red]Error:[/bold red] {e}")
            rprint("[dim]Hint: Create a plan first with 'pday start'[/dim]")
        except Exception as e:
            rprint(f"\n[bold red]Error:[/bold red] {e}")
            if ctx.obj["config"].debug:
                raise

    try:
        asyncio.run(_export())
    except KeyboardInterrupt:
        pass


# ===== Productivity Metrics =====


@cli.command()
@click.argument("date", required=False)
@click.option("--week", is_flag=True, help="Show weekly summary")
@click.option("--month", is_flag=True, help="Show monthly summary")
@click.option("--from", "from_date", help="Start date for custom range (YYYY-MM-DD)")
@click.option("--to", "to_date", help="End date for custom range (YYYY-MM-DD)")
@click.option("--json", "output_json", is_flag=True, help="Output as JSON")
@click.pass_context
def stats(ctx, date, week, month, from_date, to_date, output_json):
    """
    View productivity statistics.

    \b
    Examples:
      pday stats              # Today's stats
      pday stats 2026-01-20   # Specific day
      pday stats --week       # This week's summary
      pday stats --month      # This month's summary
      pday stats --from 2026-01-01 --to 2026-01-15  # Custom range
    """
    container = ctx.obj["container"]

    async def _stats():
        try:
            if week or month or (from_date and to_date):
                # Aggregate stats
                from ..application.use_cases.view_aggregate_stats import ViewAggregateStatsUseCase

                use_case = ViewAggregateStatsUseCase(container)
                await use_case.execute(
                    week=week,
                    month=month,
                    from_date=from_date,
                    to_date=to_date,
                    output_json=output_json,
                )
            else:
                # Daily stats
                from ..application.use_cases.view_stats import ViewStatsUseCase

                daily_use_case = ViewStatsUseCase(container)
                session_id = date or datetime.now().strftime("%Y-%m-%d")
                await daily_use_case.execute(session_id, output_json=output_json)

        except SessionNotFound as e:
            rprint(f"[bold red]Error:[/bold red] {e}")
            rprint("[dim]Hint: Create a plan first with 'pday start'[/dim]")
        except Exception as e:
            rprint(f"\n[bold red]Error:[/bold red] {e}")
            if ctx.obj["config"].debug:
                raise

    try:
        asyncio.run(_stats())
    except KeyboardInterrupt:
        pass


# ===== Session Management =====


@cli.command()
@click.argument("date")
@click.option("--force", is_flag=True, help="Skip confirmation")
@click.pass_context
def delete(ctx, date, force):
    """Delete a session."""
    if not force:
        if not Confirm.ask(f"Delete session for {date}?"):
            rprint("[yellow]Cancelled[/yellow]")
            return

    container = ctx.obj["container"]
    orchestrator = SessionOrchestrator(container)

    async def _delete():
        success = await orchestrator.delete_session(date)
        if success:
            rprint(f"[green]✓ Deleted session {date}[/green]")
        else:
            rprint(f"[red]Session {date} not found[/red]")

    asyncio.run(_delete())


@cli.command()
@click.argument("date")
@click.pass_context
def info(ctx, date):
    """Show detailed session information."""
    container = ctx.obj["container"]

    async def _info():
        storage = container.storage
        memory = await storage.load_session(date)

        if not memory:
            rprint(f"[red]Session {date} not found[/red]")
            return

        info = {
            "session_id": memory.metadata.session_id,
            "state": memory.agent_state.state.value,
            "created_at": str(memory.metadata.created_at),
            "last_updated": str(memory.metadata.last_updated),
            "num_llm_calls": memory.metadata.num_llm_calls,
            "num_messages": len(memory.conversation.messages),
        }

        formatter = container.session_formatter
        panel = formatter.format_session_info(info)
        console.print(panel)

    asyncio.run(_info())


# ===== Profile Management =====


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
            rprint("\n[bold green]✓ Profile saved successfully![/bold green]")

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


# ===== Template Management =====


@cli.group()
@click.pass_context
def template(ctx):
    """
    Manage daily templates.

    Templates let you save and reuse common daily patterns.
    """
    pass


@template.command(name="list")
@click.pass_context
def template_list(ctx):
    """List all saved templates."""
    from ..application.use_cases.template_list import ListTemplatesUseCase

    container = ctx.obj["container"]
    use_case = ListTemplatesUseCase(container)

    async def _list():
        await use_case.execute()

    try:
        asyncio.run(_list())
    except KeyboardInterrupt:
        pass


@template.command(name="save")
@click.argument("name")
@click.option("--date", help="Source session date (defaults to today)")
@click.option("--description", "-d", default="", help="Template description")
@click.option("--force", is_flag=True, help="Overwrite without confirmation")
@click.pass_context
def template_save(ctx, name, date, description, force):
    """
    Save a day's plan as a template.

    Example: pday template save work-day --description "Standard work day"
    """
    from ..application.use_cases.template_save import SaveTemplateUseCase

    container = ctx.obj["container"]
    use_case = SaveTemplateUseCase(container)

    async def _save():
        try:
            await use_case.execute(name, date, description, force)
        except SessionNotFound as e:
            rprint(f"[bold red]Error:[/bold red] {e}")
            rprint("[dim]Hint: Create a plan first with 'pday start'[/dim]")
        except Exception as e:
            rprint(f"\n[bold red]Error:[/bold red] {e}")
            if ctx.obj["config"].debug:
                raise

    try:
        asyncio.run(_save())
    except KeyboardInterrupt:
        pass


@template.command(name="show")
@click.argument("name")
@click.pass_context
def template_show(ctx, name):
    """Display details of a template."""
    from ..application.use_cases.template_show import ShowTemplateUseCase

    container = ctx.obj["container"]
    use_case = ShowTemplateUseCase(container)

    async def _show():
        await use_case.execute(name)

    try:
        asyncio.run(_show())
    except KeyboardInterrupt:
        pass


@template.command(name="apply")
@click.argument("name")
@click.option("--date", help="Target session date (defaults to today)")
@click.option("--force", is_flag=True, help="Overwrite without confirmation")
@click.pass_context
def template_apply(ctx, name, date, force):
    """
    Apply a template to create a new plan.

    Example: pday template apply work-day
    """
    from ..application.use_cases.template_apply import ApplyTemplateUseCase

    container = ctx.obj["container"]
    use_case = ApplyTemplateUseCase(container)

    async def _apply():
        try:
            await use_case.execute(name, date, force)
        except Exception as e:
            rprint(f"\n[bold red]Error:[/bold red] {e}")
            if ctx.obj["config"].debug:
                raise

    try:
        asyncio.run(_apply())
    except KeyboardInterrupt:
        pass


@template.command(name="delete")
@click.argument("name")
@click.option("--force", is_flag=True, help="Skip confirmation")
@click.pass_context
def template_delete(ctx, name, force):
    """Delete a template."""
    from ..application.use_cases.template_delete import DeleteTemplateUseCase

    container = ctx.obj["container"]
    use_case = DeleteTemplateUseCase(container)

    async def _delete():
        await use_case.execute(name, force)

    try:
        asyncio.run(_delete())
    except KeyboardInterrupt:
        pass


# ===== Profile Management (continued) =====


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
                rprint("[dim]Run 'pday profile' to create one.[/dim]")
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


if __name__ == "__main__":
    cli()
