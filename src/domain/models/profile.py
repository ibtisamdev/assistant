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


class PersonalInfo(BaseModel):
    """User's personal information and communication preferences."""

    name: Optional[str] = Field(default=None, description="User's full name")
    preferred_name: Optional[str] = Field(default=None, description="Nickname or preferred name")
    communication_style: str = Field(
        default="balanced",
        description="Preferred communication style: concise, detailed, or balanced",
    )


class ProductivityHabits(BaseModel):
    """User's productivity patterns and preferences."""

    focus_session_length: int = Field(
        default=25, description="Minutes per focus block (e.g., Pomodoro)"
    )
    max_deep_work_hours: int = Field(default=4, description="Maximum hours of deep work per day")
    distraction_triggers: List[str] = Field(
        default_factory=list,
        description="Known distraction sources (e.g., social media, email)",
    )
    procrastination_patterns: List[str] = Field(
        default_factory=list,
        description="Patterns when procrastination occurs (e.g., afternoons, large tasks)",
    )
    peak_productivity_time: Optional[str] = Field(
        default=None, description="Best time for productivity: morning, afternoon, evening"
    )


class WellnessSchedule(BaseModel):
    """Health and wellness timing preferences."""

    wake_time: Optional[str] = Field(default=None, description="Typical wake time in HH:MM format")
    sleep_time: Optional[str] = Field(
        default=None, description="Typical sleep time in HH:MM format"
    )
    meal_times: List[dict] = Field(
        default_factory=list,
        description="Regular meal times: [{'name': 'lunch', 'time': '12:00', 'duration': 30}]",
    )
    exercise_times: List[dict] = Field(
        default_factory=list,
        description="Exercise schedule: [{'day': 'Monday', 'time': '07:00', 'duration': 60}]",
    )


class WorkContext(BaseModel):
    """Professional work context and collaboration patterns."""

    job_role: Optional[str] = Field(default=None, description="User's job title or role")
    meeting_heavy_days: List[str] = Field(
        default_factory=list, description="Days with many meetings (e.g., Tuesday, Thursday)"
    )
    deadline_patterns: Optional[str] = Field(
        default=None,
        description="Typical deadline patterns (e.g., end of sprint, monthly, quarterly)",
    )
    collaboration_preference: str = Field(
        default="async",
        description="Preferred collaboration style: sync, async, or mixed",
    )
    typical_meeting_duration: int = Field(
        default=30, description="Average meeting length in minutes"
    )


class LearningPreferences(BaseModel):
    """Learning style and development goals."""

    learning_style: str = Field(
        default="mixed",
        description="Preferred learning style: visual, auditory, kinesthetic, reading, mixed",
    )
    skill_development_goals: List[str] = Field(
        default_factory=list, description="Skills currently being developed"
    )
    areas_of_interest: List[str] = Field(
        default_factory=list, description="Topics of interest for learning"
    )
    preferred_learning_time: Optional[str] = Field(
        default=None, description="Best time for learning activities"
    )


class PlanningHistory(BaseModel):
    """Learned patterns from past planning sessions (auto-updated by agent)."""

    successful_patterns: List[str] = Field(
        default_factory=list, description="Planning approaches that worked well"
    )
    avoided_patterns: List[str] = Field(
        default_factory=list, description="Planning approaches that didn't work"
    )
    common_adjustments: List[str] = Field(
        default_factory=list, description="Frequent plan modifications made by user"
    )
    feedback_notes: List[str] = Field(
        default_factory=list, description="User's explicit feedback on plans"
    )
    sessions_completed: int = Field(
        default=0, description="Total number of completed planning sessions"
    )
    last_session_date: Optional[str] = Field(
        default=None, description="Date of most recent session (YYYY-MM-DD)"
    )


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

    # Extended profile sections
    personal_info: PersonalInfo = Field(
        default_factory=PersonalInfo,
        description="Personal information and communication preferences",
    )
    productivity_habits: ProductivityHabits = Field(
        default_factory=ProductivityHabits,
        description="Productivity patterns and work preferences",
    )
    wellness_schedule: WellnessSchedule = Field(
        default_factory=WellnessSchedule,
        description="Health and wellness timing",
    )
    work_context: WorkContext = Field(
        default_factory=WorkContext,
        description="Professional work context",
    )
    learning_preferences: LearningPreferences = Field(
        default_factory=LearningPreferences,
        description="Learning style and development goals",
    )
    planning_history: PlanningHistory = Field(
        default_factory=PlanningHistory,
        description="Learned patterns from past sessions (auto-updated)",
    )

    # Metadata
    created_at: datetime = Field(default_factory=datetime.now)
    last_updated: datetime = Field(default_factory=datetime.now)
