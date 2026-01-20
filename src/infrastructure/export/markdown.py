"""Markdown exporter - future implementation stub."""

from ...domain.models.planning import Plan


class MarkdownExporter:
    """Export plans to Markdown format (FUTURE FEATURE)."""

    async def export(self, plan: Plan, output_path: str) -> None:
        """Export plan to Markdown file."""
        raise NotImplementedError("Markdown export coming soon")

    def to_string(self, plan: Plan) -> str:
        """Convert plan to Markdown string."""
        # Simple implementation for future
        md = f"# Daily Plan\n\n"
        md += f"## Schedule\n\n"
        for item in plan.schedule:
            md += f"- **{item.time}**: {item.task}\n"
        md += f"\n## Priorities\n\n"
        for priority in plan.priorities:
            md += f"- {priority}\n"
        md += f"\n## Notes\n\n{plan.notes}\n"
        return md
