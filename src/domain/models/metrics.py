"""Productivity metrics models."""

from pydantic import BaseModel, Field
from typing import Dict, List, Optional


class TaskMetric(BaseModel):
    """Metrics for a single task."""

    task: str = Field(description="Task description")
    category: str = Field(description="Task category")
    estimated_minutes: Optional[int] = Field(default=None, description="Estimated duration")
    actual_minutes: Optional[int] = Field(default=None, description="Actual duration")
    variance: Optional[int] = Field(
        default=None, description="Difference (actual - estimated), positive = over time"
    )
    status: str = Field(description="Task status")


class EstimationAccuracy(BaseModel):
    """Breakdown of estimation accuracy metrics."""

    total_tasks_with_tracking: int = Field(
        description="Number of tasks with both estimated and actual time"
    )
    avg_variance: float = Field(description="Average variance in minutes")
    median_variance: float = Field(description="Median variance in minutes")
    tasks_within_15min: int = Field(description="Count of tasks within +/- 15 min of estimate")
    tasks_within_15min_percent: float = Field(description="Percentage within +/- 15 min")
    underestimated_count: int = Field(description="Number of tasks that took longer than estimated")
    overestimated_count: int = Field(description="Number of tasks that took less than estimated")
    most_underestimated: Optional[str] = Field(
        default=None, description="Task name with largest positive variance"
    )
    most_overestimated: Optional[str] = Field(
        default=None, description="Task name with largest negative variance"
    )


class DailyMetrics(BaseModel):
    """Complete metrics for a single day."""

    date: str = Field(description="Session date (YYYY-MM-DD)")

    # Time analysis
    total_planned_minutes: int = Field(description="Total estimated/planned time")
    total_actual_minutes: int = Field(description="Total actual time spent")
    time_variance: int = Field(description="Total variance (actual - planned)")
    time_by_category: Dict[str, int] = Field(
        default_factory=dict, description="Minutes spent per category"
    )
    productive_minutes: int = Field(default=0, description="Total productive time")
    wasted_minutes: int = Field(default=0, description="Total wasted time")

    # Task analysis
    total_tasks: int = Field(description="Total number of tasks")
    completed_tasks: int = Field(description="Number of completed tasks")
    in_progress_tasks: int = Field(default=0, description="Number of in-progress tasks")
    skipped_tasks: int = Field(default=0, description="Number of skipped tasks")
    not_started_tasks: int = Field(default=0, description="Number of not started tasks")
    completion_rate: float = Field(description="Percentage of tasks completed (0-100)")

    # Estimation accuracy
    estimation_accuracy: Optional[EstimationAccuracy] = Field(
        default=None, description="Estimation accuracy breakdown"
    )

    # Top time consumers
    top_time_consumers: List[TaskMetric] = Field(
        default_factory=list, description="Most time-consuming tasks"
    )


class ProductivityPattern(BaseModel):
    """Identified pattern from historical data."""

    pattern_type: str = Field(
        description="Type of pattern: peak_time, time_sink, successful_habit, improvement"
    )
    description: str = Field(description="Human-readable description of the pattern")
    confidence: float = Field(description="Confidence score (0-1)")
    supporting_data: List[str] = Field(
        default_factory=list, description="Day references supporting this pattern"
    )


class AggregateMetrics(BaseModel):
    """Metrics aggregated across multiple days."""

    period_start: str = Field(description="Start date of the period (YYYY-MM-DD)")
    period_end: str = Field(description="End date of the period (YYYY-MM-DD)")
    period_type: str = Field(description="Type of period: week, month, or custom")
    days_with_data: int = Field(description="Number of days with tracking data")
    total_days: int = Field(description="Total days in the period")

    # Aggregate time
    total_planned_minutes: int = Field(description="Total planned time across all days")
    total_actual_minutes: int = Field(description="Total actual time across all days")
    avg_daily_planned_minutes: float = Field(description="Average planned time per day")
    avg_daily_actual_minutes: float = Field(description="Average actual time per day")

    # Category breakdown (aggregate)
    total_by_category: Dict[str, int] = Field(
        default_factory=dict, description="Total minutes per category across all days"
    )
    avg_daily_by_category: Dict[str, float] = Field(
        default_factory=dict, description="Average daily minutes per category"
    )
    category_percentages: Dict[str, float] = Field(
        default_factory=dict, description="Percentage of time per category"
    )

    # Completion trends
    avg_completion_rate: float = Field(description="Average completion rate across days")
    completion_rate_by_day: Dict[str, float] = Field(
        default_factory=dict, description="Completion rate per day for trend visualization"
    )
    total_tasks: int = Field(default=0, description="Total tasks across all days")
    total_completed: int = Field(default=0, description="Total completed tasks")
    best_day: Optional[str] = Field(default=None, description="Day with highest completion rate")
    worst_day: Optional[str] = Field(default=None, description="Day with lowest completion rate")

    # Estimation trends
    avg_estimation_accuracy: float = Field(
        default=0.0, description="Average tasks within +/- 15 min percentage"
    )
    avg_variance: float = Field(default=0.0, description="Average time variance across all tasks")

    # Patterns (insights)
    patterns: List[ProductivityPattern] = Field(
        default_factory=list, description="Identified productivity patterns"
    )
