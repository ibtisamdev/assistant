"""Export protocol for future export features."""

from typing import Protocol

from ..models.planning import Plan


class PlanExporter(Protocol):
    """Protocol for plan export formats."""

    async def export(self, plan: Plan, output_path: str) -> None:
        """Export plan to file."""
        ...

    def to_string(self, plan: Plan) -> str:
        """Convert plan to string format."""
        ...
