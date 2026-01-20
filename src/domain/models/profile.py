"""User profile models."""

from datetime import datetime
from pydantic import BaseModel, Field
from typing import Optional, List


class WorkHours(BaseModel):
    """User's typical work schedule."""

    start: str = Field(description="Start time in HH:MM format", default="09:00")
    end: str = Field(description="End time in HH:MM format", default="17:00")
    days: List[str] = Field(
        description="Work days",
        default=["Monday", "Tuesday", "Wednesday", "Thursday", "Friday"],
    )


class EnergyPattern(BaseModel):
    """User's energy levels throughout the day."""

    morning: str = Field(description="Morning energy level", default="high")
    afternoon: str = Field(description="Afternoon energy level", default="medium")
    evening: str = Field(description="Evening energy level", default="low")


class RecurringTask(BaseModel):
    """Tasks that repeat regularly."""

    name: str
    frequency: str  # daily, weekly, etc.
    duration: int  # minutes
    preferred_time: Optional[str] = None  # HH:MM format
    priority: str = "medium"  # high/medium/low


class UserProfile(BaseModel):
    """Complete user profile for personalized planning."""

    # Basic info
    user_id: str = Field(default="default")
    timezone: str = Field(default="UTC")

    # Schedule preferences
    work_hours: WorkHours = Field(default_factory=WorkHours)
    energy_pattern: EnergyPattern = Field(default_factory=EnergyPattern)

    # Planning preferences
    preferred_task_duration: int = Field(
        description="Preferred task block duration in minutes", default=60
    )
    break_frequency: int = Field(description="Minutes between breaks", default=90)

    # Habits and constraints
    recurring_tasks: List[RecurringTask] = Field(default_factory=list)
    blocked_times: List[dict] = Field(
        description="Times unavailable for planning", default_factory=list
    )  # Format: [{"start": "12:00", "end": "13:00", "reason": "lunch"}]

    # Priorities and goals
    top_priorities: List[str] = Field(
        description="User's current top priorities", default_factory=list
    )
    long_term_goals: List[str] = Field(
        description="Long-term goals to align daily plans with", default_factory=list
    )

    # Metadata
    created_at: datetime = Field(default_factory=datetime.now)
    last_updated: datetime = Field(default_factory=datetime.now)
