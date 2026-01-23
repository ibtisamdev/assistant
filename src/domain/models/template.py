"""Day template models for reusable planning patterns."""

from datetime import datetime

from pydantic import BaseModel, Field

from .planning import ScheduleItem, TaskStatus


class DayTemplate(BaseModel):
    """A reusable template for daily plans.

    Templates allow users to save common daily patterns (work day, weekend,
    focus day) and quickly apply them to new days without going through
    the full planning process.
    """

    name: str = Field(description="Template identifier (e.g., 'work-day', 'weekend')")
    description: str = Field(
        default="", description="Optional description of when to use this template"
    )
    schedule: list[ScheduleItem] = Field(default_factory=list, description="Template tasks")
    priorities: list[str] = Field(
        default_factory=list, description="Default priorities for this template"
    )
    notes: str = Field(default="", description="Default notes")

    # Metadata
    created_at: datetime = Field(default_factory=datetime.now)
    last_used: datetime | None = Field(default=None, description="When template was last applied")
    use_count: int = Field(default=0, description="Number of times template has been used")

    def prepare_for_new_day(self) -> "DayTemplate":
        """
        Prepare template for application to a new day.

        Resets all task statuses and timestamps while preserving
        the template structure.
        """
        new_schedule = []
        for item in self.schedule:
            # Create a fresh copy with reset tracking fields
            new_item = item.model_copy(
                update={
                    "status": TaskStatus.not_started,
                    "actual_start": None,
                    "actual_end": None,
                    "edits": [],
                }
            )
            new_schedule.append(new_item)

        return self.model_copy(update={"schedule": new_schedule})

    def record_use(self) -> None:
        """Record that this template was used."""
        self.last_used = datetime.now()
        self.use_count += 1


class TemplateMetadata(BaseModel):
    """Lightweight template info for listing without loading full template."""

    name: str
    description: str
    task_count: int
    created_at: datetime
    last_used: datetime | None
    use_count: int
