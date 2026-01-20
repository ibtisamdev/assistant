"""Planning domain models."""

from pydantic import BaseModel, Field
from typing import List, Optional
import re


class ScheduleItem(BaseModel):
    """Individual task in schedule."""

    time: str = Field(description="Time in HH:MM-HH:MM format")
    task: str = Field(description="Description of the task")
    duration_minutes: Optional[int] = None
    priority: str = "medium"  # high/medium/low

    def validate_time_format(self) -> bool:
        """Validate time format HH:MM-HH:MM."""
        pattern = r"^\d{2}:\d{2}-\d{2}:\d{2}$"
        return bool(re.match(pattern, self.time))

    def extract_duration(self) -> int:
        """Extract duration in minutes from time field."""
        if self.duration_minutes:
            return self.duration_minutes

        try:
            start, end = self.time.split("-")
            start_h, start_m = map(int, start.split(":"))
            end_h, end_m = map(int, end.split(":"))

            start_mins = start_h * 60 + start_m
            end_mins = end_h * 60 + end_m

            return end_mins - start_mins
        except Exception:
            return 0


class Question(BaseModel):
    """Clarifying question."""

    question: str = Field(description="The question asked to the user")
    answer: str = Field(description="The answer given by the user", default="")
    is_required: bool = True


class Plan(BaseModel):
    """User's daily plan."""

    schedule: List[ScheduleItem] = Field(description="The schedule of the day")
    priorities: List[str] = Field(description="The priorities of the day")
    notes: str = Field(description="Additional notes")
    estimated_duration_minutes: Optional[int] = None

    def calculate_total_duration(self) -> int:
        """Calculate total scheduled time in minutes."""
        total = sum(item.extract_duration() for item in self.schedule)
        self.estimated_duration_minutes = total
        return total

    def validate_no_overlaps(self) -> bool:
        """Ensure no time conflicts in schedule."""
        # Simple validation - can be enhanced
        if len(self.schedule) < 2:
            return True

        # TODO: Implement overlap detection
        return True

    def get_free_time(self, work_start: str = "09:00", work_end: str = "17:00") -> int:
        """Calculate free time during work hours."""
        # Parse work hours
        work_start_h, work_start_m = map(int, work_start.split(":"))
        work_end_h, work_end_m = map(int, work_end.split(":"))

        work_minutes = (work_end_h * 60 + work_end_m) - (work_start_h * 60 + work_start_m)
        scheduled_minutes = self.calculate_total_duration()

        return max(0, work_minutes - scheduled_minutes)
