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


# Import command groups
from .commands.plan import plan_group
from .commands.session import session_group

cli.add_command(plan_group)
cli.add_command(session_group)


if __name__ == "__main__":
    cli()
