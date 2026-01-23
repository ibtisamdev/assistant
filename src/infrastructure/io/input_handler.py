"""Async user input with validation."""

import asyncio

from rich.console import Console
from rich.prompt import Prompt

from ...application.config import InputConfig

console = Console()


class InputHandler:
    """Async user input with validation."""

    def __init__(self, config: InputConfig):
        self.config = config

    async def get_goal(self) -> str:
        """Get user goal with validation."""
        return await self._get_validated_input(
            prompt="Enter your goal",
            max_length=self.config.max_goal_length,
            allow_empty=False,
        )

    async def get_feedback(self) -> str | None:
        """Get feedback (can exit with special keywords)."""
        feedback = await self._get_validated_input(
            prompt="Enter feedback (or 'no'/'done' to finish)",
            max_length=self.config.max_feedback_length,
            allow_empty=False,
        )

        # Check exit keywords
        if feedback.lower() in ["no", "n", "done", "exit", "quit", "q"]:
            return None

        return feedback

    async def get_answer(self, question: str) -> str:
        """Get answer to clarifying question."""
        return await self._get_validated_input(
            prompt=question,
            max_length=self.config.max_answer_length,
            allow_empty=False,
        )

    async def confirm(self, question: str) -> bool:
        """Get yes/no confirmation."""
        response = await self._get_validated_input(
            prompt=f"{question} (yes/no)",
            max_length=10,
            allow_empty=False,
        )
        return response.lower() in ["yes", "y"]

    async def _get_validated_input(
        self,
        prompt: str,
        max_length: int,
        allow_empty: bool = False,
    ) -> str:
        """Get and validate user input."""
        while True:
            try:
                # Use asyncio.to_thread to avoid blocking
                user_input = await asyncio.to_thread(Prompt.ask, f"[bold cyan]{prompt}[/bold cyan]")

                user_input = user_input.strip()

                # Validate empty
                if not user_input and not allow_empty:
                    console.print("[yellow]  Input cannot be empty. Please try again.[/yellow]")
                    continue

                # Validate length
                if len(user_input) > max_length:
                    console.print(
                        f"[yellow]  Input too long (max {max_length} chars). Please shorten.[/yellow]"
                    )
                    continue

                return user_input

            except EOFError:
                # Handle piped input or closed stdin
                if allow_empty:
                    return ""
                raise KeyboardInterrupt("Input stream closed")
            except KeyboardInterrupt:
                raise
            except Exception as e:
                console.print(f"[red]Error reading input: {e}[/red]")
                if not allow_empty:
                    raise
                return ""
