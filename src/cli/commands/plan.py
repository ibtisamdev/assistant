"""Planning commands."""

import asyncio
import click
from rich import print as rprint
from ...application.session_orchestrator import SessionOrchestrator
from ...domain.exceptions import SessionNotFound, LLMError


@click.group(name="plan")
def plan_group():
    """Planning commands."""
    pass


@plan_group.command(name="create")
@click.option("--date", help="Session date (YYYY-MM-DD)")
@click.option("--force", is_flag=True, help="Force create new (ignore existing)")
@click.pass_context
def create_plan(ctx, date, force):
    """Create a new daily plan."""
    container = ctx.obj["container"]
    orchestrator = SessionOrchestrator(container)

    async def _create():
        try:
            rprint("[bold green]Creating new daily plan...[/bold green]\n")
            memory = await orchestrator.run_new_session(date, force_new=force)
            rprint("\n[bold green]✓ Plan created successfully![/bold green]")
        except KeyboardInterrupt:
            rprint("\n[yellow]Cancelled. Progress saved.[/yellow]")
        except LLMError as e:
            rprint(f"\n[bold red]AI Error:[/bold red] {e}")
        except Exception as e:
            rprint(f"\n[bold red]Error:[/bold red] {e}")
            if ctx.obj["config"].debug:
                raise

    try:
        asyncio.run(_create())
    except KeyboardInterrupt:
        pass


@plan_group.command(name="revise")
@click.option("--date", help="Session date (defaults to today)")
@click.pass_context
def revise_plan(ctx, date):
    """Revise an existing plan."""
    container = ctx.obj["container"]
    orchestrator = SessionOrchestrator(container)

    async def _revise():
        try:
            rprint("[bold yellow]Revising plan...[/bold yellow]\n")
            memory = await orchestrator.run_revise(date)
            rprint("\n[bold green]✓ Plan revised![/bold green]")
        except SessionNotFound as e:
            rprint(f"[bold red]Error:[/bold red] {e}")
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


@plan_group.command(name="show")
@click.argument("date")
@click.pass_context
def show_plan(ctx, date):
    """Display a saved plan."""
    container = ctx.obj["container"]

    async def _show():
        storage = container.storage
        memory = await storage.load_session(date)

        if not memory or not memory.agent_state.plan:
            rprint(f"[red]No plan found for {date}[/red]")
            return

        formatter = container.plan_formatter
        panel = formatter.format_plan(memory.agent_state.plan)
        from rich.console import Console

        Console().print(panel)

    asyncio.run(_show())


@plan_group.command(name="export")
@click.argument("date")
@click.option("--format", type=click.Choice(["md", "pdf", "ical"]), default="md")
@click.option("--output", type=click.Path(), help="Output file path")
@click.pass_context
def export_plan(ctx, date, format, output):
    """Export plan to file (FUTURE FEATURE)."""
    rprint("[yellow]📦 Export feature coming soon![/yellow]")
    rprint(f"[dim]  Will export {date} to {format} format[/dim]")
    # TODO: Implement when export infrastructure is ready


@plan_group.command(name="checkin")
@click.option("--date", help="Session date (defaults to today)")
@click.option("--start", help="Quick start task by name")
@click.option("--complete", help="Quick complete task by name")
@click.option("--skip", help="Quick skip task by name")
@click.option("--status", is_flag=True, help="Show progress status only")
@click.pass_context
def checkin(ctx, date, start, complete, skip, status):
    """Check in and track task progress."""
    from datetime import datetime
    from ...application.use_cases.checkin import CheckinUseCase
    from ...domain.exceptions import SessionNotFound

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
            rprint(f"[dim]Hint: Create a plan first with 'uv run plan create'[/dim]")
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
