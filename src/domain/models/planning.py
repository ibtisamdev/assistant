"""Planning domain models."""

from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import datetime
from enum import Enum
import re


class TaskStatus(Enum):
    """Status of a task in the schedule."""

    not_started = "not_started"
    in_progress = "in_progress"
    completed = "completed"
    skipped = "skipped"


class TimeEdit(BaseModel):
    """Audit trail for manual time edits."""

    edited_at: datetime = Field(default_factory=datetime.now)
    field: str = Field(description="Field that was edited (actual_start or actual_end)")
    old_value: Optional[datetime] = Field(description="Previous value")
    new_value: datetime = Field(description="New value")
    reason: Optional[str] = Field(default=None, description="Reason for edit")


class ScheduleItem(BaseModel):
    """Individual task in schedule."""

    time: str = Field(description="Time in HH:MM-HH:MM format")
    task: str = Field(description="Description of the task")
    duration_minutes: Optional[int] = None
    priority: str = "medium"  # high/medium/low

    # Time tracking fields
    estimated_minutes: Optional[int] = Field(
        default=None, description="LLM-estimated duration in minutes"
    )
    actual_start: Optional[datetime] = Field(default=None, description="When task actually started")
    actual_end: Optional[datetime] = Field(default=None, description="When task actually completed")
    status: TaskStatus = Field(default=TaskStatus.not_started, description="Current task status")

    # Audit trail for manual edits
    edits: List[TimeEdit] = Field(default_factory=list, description="History of manual time edits")

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

    @property
    def actual_minutes(self) -> Optional[int]:
        """Calculate actual duration from start/end timestamps."""
        if self.actual_start and self.actual_end:
            delta = self.actual_end - self.actual_start
            return int(delta.total_seconds() / 60)
        return None

    @property
    def time_variance(self) -> Optional[int]:
        """
        Calculate difference between estimated and actual time.
        Positive = took longer than expected
        Negative = took less time than expected
        """
        if self.estimated_minutes is not None and self.actual_minutes is not None:
            return self.actual_minutes - self.estimated_minutes
        return None

    @property
    def is_completed(self) -> bool:
        """Check if task is completed."""
        return self.status == TaskStatus.completed

    @property
    def is_in_progress(self) -> bool:
        """Check if task is currently in progress."""
        return self.status == TaskStatus.in_progress


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

    # Time tracking metadata
    estimated_duration_minutes: Optional[int] = None
    actual_duration_minutes: Optional[int] = None
    completion_rate: Optional[float] = Field(
        default=None, description="Percentage of tasks completed (0-100)"
    )

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

    def calculate_actual_duration(self) -> int:
        """Calculate total actual time spent in minutes."""
        total = sum(item.actual_minutes for item in self.schedule if item.actual_minutes)
        self.actual_duration_minutes = total
        return total

    def calculate_completion_rate(self) -> float:
        """Calculate percentage of tasks completed."""
        if not self.schedule:
            return 0.0

        completed = sum(1 for item in self.schedule if item.is_completed)
        rate = (completed / len(self.schedule)) * 100
        self.completion_rate = rate
        return rate

    def get_completed_tasks(self) -> List[ScheduleItem]:
        """Get list of completed tasks."""
        return [item for item in self.schedule if item.is_completed]

    def get_pending_tasks(self) -> List[ScheduleItem]:
        """Get list of not started tasks."""
        return [item for item in self.schedule if item.status == TaskStatus.not_started]

    def get_in_progress_tasks(self) -> List[ScheduleItem]:
        """Get list of tasks currently in progress."""
        return [item for item in self.schedule if item.is_in_progress]
