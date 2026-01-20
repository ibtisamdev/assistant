"""Session management commands."""

import asyncio
import click
from rich import print as rprint
from rich.prompt import Confirm
from ...application.session_orchestrator import SessionOrchestrator
from ...domain.exceptions import SessionNotFound


@click.group(name="session")
def session_group():
    """Session management commands."""
    pass


@session_group.command(name="list")
@click.pass_context
def list_sessions(ctx):
    """List all saved sessions."""
    container = ctx.obj["container"]
    formatter = container.session_formatter
    storage = container.storage

    async def _list():
        sessions = await storage.list_sessions()

        if not sessions:
            rprint("[yellow]No saved sessions found.[/yellow]")
            return

        table = formatter.format_session_list(sessions)
        from rich.console import Console

        Console().print(table)

    asyncio.run(_list())


@session_group.command(name="resume")
@click.argument("date")
@click.pass_context
def resume_session(ctx, date):
    """Resume an existing session."""
    container = ctx.obj["container"]
    orchestrator = SessionOrchestrator(container)

    async def _resume():
        try:
            memory = await orchestrator.run_resume(date)
            rprint("\n[bold green]✓ Session complete![/bold green]")
        except SessionNotFound as e:
            rprint(f"[bold red]Error:[/bold red] {e}")
        except KeyboardInterrupt:
            rprint("\n[yellow]Cancelled. Progress saved.[/yellow]")
        except Exception as e:
            rprint(f"\n[bold red]Error:[/bold red] {e}")
            if ctx.obj["config"].debug:
                raise

    try:
        asyncio.run(_resume())
    except KeyboardInterrupt:
        pass


@session_group.command(name="delete")
@click.argument("date")
@click.option("--force", is_flag=True, help="Skip confirmation")
@click.pass_context
def delete_session(ctx, date, force):
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


@session_group.command(name="info")
@click.argument("date")
@click.pass_context
def session_info(ctx, date):
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
        from rich.console import Console

        Console().print(panel)

    asyncio.run(_info())
