"""Metrics service - business logic for productivity metrics calculation."""

import logging
from datetime import datetime, timedelta
from statistics import median

from ..models.metrics import (
    AggregateMetrics,
    DailyMetrics,
    EstimationAccuracy,
    ProductivityPattern,
    TaskMetric,
)
from ..models.planning import Plan, TaskCategory, TaskStatus
from ..models.session import Memory

logger = logging.getLogger(__name__)


class MetricsService:
    """Business logic for productivity metrics calculation."""

    def calculate_daily_metrics(self, plan: Plan, date: str) -> DailyMetrics:
        """
        Calculate comprehensive metrics for a single day's plan.

        Args:
            plan: The plan to analyze
            date: Session date (YYYY-MM-DD)

        Returns:
            DailyMetrics with all calculated values
        """
        # Time by category
        time_by_category = self.calculate_time_by_category(plan)

        # Task counts by status
        completed = sum(1 for item in plan.schedule if item.status == TaskStatus.completed)
        in_progress = sum(1 for item in plan.schedule if item.status == TaskStatus.in_progress)
        skipped = sum(1 for item in plan.schedule if item.status == TaskStatus.skipped)
        not_started = sum(1 for item in plan.schedule if item.status == TaskStatus.not_started)
        total_tasks = len(plan.schedule)

        # Completion rate
        completion_rate = (completed / total_tasks * 100) if total_tasks > 0 else 0.0

        # Time totals
        total_planned = sum(
            item.estimated_minutes or item.extract_duration() for item in plan.schedule
        )
        total_actual = sum(item.actual_minutes or 0 for item in plan.schedule)

        # Productive vs wasted time (from actual time or estimated if not tracked)
        productive_minutes = time_by_category.get(TaskCategory.productive.value, 0)
        wasted_minutes = time_by_category.get(TaskCategory.wasted.value, 0)

        # Estimation accuracy
        estimation_accuracy = self.calculate_estimation_accuracy(plan)

        # Top time consumers
        top_consumers = self.get_time_consuming_tasks(plan, top_n=5)

        return DailyMetrics(
            date=date,
            total_planned_minutes=total_planned,
            total_actual_minutes=total_actual,
            time_variance=total_actual - total_planned,
            time_by_category={k: v for k, v in time_by_category.items()},
            productive_minutes=productive_minutes,
            wasted_minutes=wasted_minutes,
            total_tasks=total_tasks,
            completed_tasks=completed,
            in_progress_tasks=in_progress,
            skipped_tasks=skipped,
            not_started_tasks=not_started,
            completion_rate=round(completion_rate, 1),
            estimation_accuracy=estimation_accuracy,
            top_time_consumers=top_consumers,
        )

    def calculate_time_by_category(self, plan: Plan) -> dict[str, int]:
        """
        Calculate total time spent per category.

        Uses actual_minutes if available, otherwise estimated_minutes.

        Args:
            plan: Plan to analyze

        Returns:
            Dictionary mapping category name to total minutes
        """
        time_by_category: dict[str, int] = {}

        for item in plan.schedule:
            category = item.category.value
            # Use actual time if available, otherwise estimated or extracted from time range
            minutes = item.actual_minutes or item.estimated_minutes or item.extract_duration()

            if category not in time_by_category:
                time_by_category[category] = 0
            time_by_category[category] += minutes

        return time_by_category

    def calculate_estimation_accuracy(self, plan: Plan) -> EstimationAccuracy | None:
        """
        Analyze estimation accuracy for completed tasks.

        Args:
            plan: Plan to analyze

        Returns:
            EstimationAccuracy breakdown or None if no trackable tasks
        """
        # Get tasks with both estimated and actual time
        trackable_tasks = [
            item
            for item in plan.schedule
            if item.status == TaskStatus.completed
            and item.estimated_minutes is not None
            and item.actual_minutes is not None
        ]

        if not trackable_tasks:
            return None

        # Calculate variances
        variances = [
            item.time_variance for item in trackable_tasks if item.time_variance is not None
        ]

        if not variances:
            return None

        # Stats
        avg_variance = sum(variances) / len(variances)
        median_variance = median(variances) if variances else 0.0

        # Count within +/- 15 minutes
        within_15 = sum(1 for v in variances if abs(v) <= 15)
        within_15_percent = (within_15 / len(variances) * 100) if variances else 0.0

        # Count under/over estimated
        underestimated = sum(1 for v in variances if v > 0)  # Took longer than expected
        overestimated = sum(1 for v in variances if v < 0)  # Took less than expected

        # Find most under/over estimated tasks
        most_under = None
        most_over = None
        max_under_variance = 0
        max_over_variance = 0

        for item in trackable_tasks:
            if item.time_variance is not None:
                if item.time_variance > max_under_variance:
                    max_under_variance = item.time_variance
                    most_under = item.task
                if item.time_variance < max_over_variance:
                    max_over_variance = item.time_variance
                    most_over = item.task

        return EstimationAccuracy(
            total_tasks_with_tracking=len(trackable_tasks),
            avg_variance=round(avg_variance, 1),
            median_variance=round(median_variance, 1),
            tasks_within_15min=within_15,
            tasks_within_15min_percent=round(within_15_percent, 1),
            underestimated_count=underestimated,
            overestimated_count=overestimated,
            most_underestimated=most_under,
            most_overestimated=most_over,
        )

    def get_time_consuming_tasks(self, plan: Plan, top_n: int = 5) -> list[TaskMetric]:
        """
        Get the most time-consuming tasks.

        Args:
            plan: Plan to analyze
            top_n: Number of top tasks to return

        Returns:
            List of TaskMetric for top time consumers
        """
        task_metrics = []

        for item in plan.schedule:
            # Use actual time if available, otherwise estimated
            item.actual_minutes or item.estimated_minutes or item.extract_duration()

            task_metrics.append(
                TaskMetric(
                    task=item.task,
                    category=item.category.value,
                    estimated_minutes=item.estimated_minutes,
                    actual_minutes=item.actual_minutes,
                    variance=item.time_variance,
                    status=item.status.value,
                )
            )

        # Sort by time spent (actual or estimated), descending
        task_metrics.sort(key=lambda t: t.actual_minutes or t.estimated_minutes or 0, reverse=True)

        return task_metrics[:top_n]

    def calculate_aggregate_metrics(
        self,
        sessions: list[Memory],
        period_start: str,
        period_end: str,
        period_type: str = "custom",
    ) -> AggregateMetrics:
        """
        Calculate aggregate metrics across multiple sessions.

        Args:
            sessions: List of Memory objects with plans
            period_start: Start date (YYYY-MM-DD)
            period_end: End date (YYYY-MM-DD)
            period_type: "week", "month", or "custom"

        Returns:
            AggregateMetrics with aggregated values
        """
        # Filter sessions that have plans and are within date range
        valid_sessions = [
            s
            for s in sessions
            if s.agent_state.plan is not None
            and period_start <= s.metadata.session_id <= period_end
        ]

        # Calculate total days in period
        start_date = datetime.strptime(period_start, "%Y-%m-%d")
        end_date = datetime.strptime(period_end, "%Y-%m-%d")
        total_days = (end_date - start_date).days + 1

        if not valid_sessions:
            return AggregateMetrics(
                period_start=period_start,
                period_end=period_end,
                period_type=period_type,
                days_with_data=0,
                total_days=total_days,
                total_planned_minutes=0,
                total_actual_minutes=0,
                avg_daily_planned_minutes=0.0,
                avg_daily_actual_minutes=0.0,
                avg_completion_rate=0.0,
            )

        # Aggregate metrics
        total_planned = 0
        total_actual = 0
        total_by_category: dict[str, int] = {}
        completion_rates: list[float] = []
        completion_rate_by_day: dict[str, float] = {}
        total_tasks = 0
        total_completed = 0
        all_variances: list[float] = []
        tasks_within_15: list[float] = []

        for session in valid_sessions:
            plan = session.agent_state.plan
            if plan is None:
                continue
            date = session.metadata.session_id

            # Daily metrics
            daily = self.calculate_daily_metrics(plan, date)

            total_planned += daily.total_planned_minutes
            total_actual += daily.total_actual_minutes

            # Category aggregation
            for cat, minutes in daily.time_by_category.items():
                if cat not in total_by_category:
                    total_by_category[cat] = 0
                total_by_category[cat] += minutes

            # Completion tracking
            completion_rates.append(daily.completion_rate)
            completion_rate_by_day[date] = daily.completion_rate
            total_tasks += daily.total_tasks
            total_completed += daily.completed_tasks

            # Estimation accuracy aggregation
            if daily.estimation_accuracy:
                all_variances.append(daily.estimation_accuracy.avg_variance)
                tasks_within_15.append(daily.estimation_accuracy.tasks_within_15min_percent)

        days_with_data = len(valid_sessions)

        # Calculate averages
        avg_planned = total_planned / days_with_data if days_with_data > 0 else 0.0
        avg_actual = total_actual / days_with_data if days_with_data > 0 else 0.0
        avg_completion = sum(completion_rates) / len(completion_rates) if completion_rates else 0.0

        # Category averages and percentages
        avg_by_category = {
            cat: minutes / days_with_data for cat, minutes in total_by_category.items()
        }
        total_time = sum(total_by_category.values())
        category_percentages = {
            cat: (minutes / total_time * 100) if total_time > 0 else 0.0
            for cat, minutes in total_by_category.items()
        }

        # Best and worst days
        best_day = (
            max(completion_rate_by_day.keys(), key=lambda k: completion_rate_by_day[k])
            if completion_rate_by_day
            else None
        )
        worst_day = (
            min(completion_rate_by_day.keys(), key=lambda k: completion_rate_by_day[k])
            if completion_rate_by_day
            else None
        )

        # Estimation accuracy averages
        avg_variance = sum(all_variances) / len(all_variances) if all_variances else 0.0
        avg_accuracy = sum(tasks_within_15) / len(tasks_within_15) if tasks_within_15 else 0.0

        # Identify patterns
        patterns = self.identify_patterns(valid_sessions)

        return AggregateMetrics(
            period_start=period_start,
            period_end=period_end,
            period_type=period_type,
            days_with_data=days_with_data,
            total_days=total_days,
            total_planned_minutes=total_planned,
            total_actual_minutes=total_actual,
            avg_daily_planned_minutes=round(avg_planned, 1),
            avg_daily_actual_minutes=round(avg_actual, 1),
            total_by_category=total_by_category,
            avg_daily_by_category={k: round(v, 1) for k, v in avg_by_category.items()},
            category_percentages={k: round(v, 1) for k, v in category_percentages.items()},
            avg_completion_rate=round(avg_completion, 1),
            completion_rate_by_day=completion_rate_by_day,
            total_tasks=total_tasks,
            total_completed=total_completed,
            best_day=best_day,
            worst_day=worst_day,
            avg_estimation_accuracy=round(avg_accuracy, 1),
            avg_variance=round(avg_variance, 1),
            patterns=patterns,
        )

    def calculate_weekly_metrics(
        self, sessions: list[Memory], week_start: str | None = None
    ) -> AggregateMetrics:
        """
        Calculate metrics for a week (Monday-Sunday).

        Args:
            sessions: All available sessions
            week_start: Start of week (YYYY-MM-DD), defaults to current week's Monday

        Returns:
            AggregateMetrics for the week
        """
        if week_start:
            start_date = datetime.strptime(week_start, "%Y-%m-%d")
        else:
            # Get current week's Monday
            today = datetime.now()
            start_date = today - timedelta(days=today.weekday())

        end_date = start_date + timedelta(days=6)

        return self.calculate_aggregate_metrics(
            sessions=sessions,
            period_start=start_date.strftime("%Y-%m-%d"),
            period_end=end_date.strftime("%Y-%m-%d"),
            period_type="week",
        )

    def calculate_monthly_metrics(
        self, sessions: list[Memory], year: int | None = None, month: int | None = None
    ) -> AggregateMetrics:
        """
        Calculate metrics for a month.

        Args:
            sessions: All available sessions
            year: Year (defaults to current)
            month: Month (defaults to current)

        Returns:
            AggregateMetrics for the month
        """
        today = datetime.now()
        year = year or today.year
        month = month or today.month

        # First day of month
        start_date = datetime(year, month, 1)

        # Last day of month
        if month == 12:
            end_date = datetime(year + 1, 1, 1) - timedelta(days=1)
        else:
            end_date = datetime(year, month + 1, 1) - timedelta(days=1)

        return self.calculate_aggregate_metrics(
            sessions=sessions,
            period_start=start_date.strftime("%Y-%m-%d"),
            period_end=end_date.strftime("%Y-%m-%d"),
            period_type="month",
        )

    def identify_patterns(self, sessions: list[Memory]) -> list[ProductivityPattern]:
        """
        Analyze sessions to identify productivity patterns.

        Args:
            sessions: Sessions to analyze

        Returns:
            List of identified patterns
        """
        patterns: list[ProductivityPattern] = []

        if len(sessions) < 3:
            # Need at least 3 days to identify patterns
            return patterns

        # Pattern 1: Consistent time sinks (tasks that always take longer)
        time_sink_pattern = self._find_time_sink_patterns(sessions)
        if time_sink_pattern:
            patterns.append(time_sink_pattern)

        # Pattern 2: Completion rate trends
        trend_pattern = self._find_completion_trends(sessions)
        if trend_pattern:
            patterns.append(trend_pattern)

        # Pattern 3: Category consistency
        category_pattern = self._find_category_patterns(sessions)
        if category_pattern:
            patterns.append(category_pattern)

        return patterns

    def _find_time_sink_patterns(self, sessions: list[Memory]) -> ProductivityPattern | None:
        """Find tasks that consistently take longer than estimated."""
        # Track variance by task keywords
        task_variances: dict[str, list[int]] = {}

        for session in sessions:
            plan = session.agent_state.plan
            if not plan:
                continue

            for item in plan.schedule:
                if item.time_variance is not None and item.time_variance > 15:
                    # Simplify task name to first few words
                    key = " ".join(item.task.lower().split()[:3])
                    if key not in task_variances:
                        task_variances[key] = []
                    task_variances[key].append(item.time_variance)

        # Find tasks that are consistently over time (appear 2+ times)
        consistent_sinks = [
            (task, sum(variances) / len(variances))
            for task, variances in task_variances.items()
            if len(variances) >= 2
        ]

        if consistent_sinks:
            # Sort by average variance, get worst one
            consistent_sinks.sort(key=lambda x: x[1], reverse=True)
            worst_sink, avg_var = consistent_sinks[0]

            return ProductivityPattern(
                pattern_type="time_sink",
                description=f"Tasks like '{worst_sink}' consistently take {int(avg_var)} min longer than estimated",
                confidence=min(0.9, 0.5 + len(task_variances[worst_sink]) * 0.1),
                supporting_data=[s.metadata.session_id for s in sessions[-3:]],
            )

        return None

    def _find_completion_trends(self, sessions: list[Memory]) -> ProductivityPattern | None:
        """Find trends in completion rates."""
        completion_rates = []

        for session in sessions:
            plan = session.agent_state.plan
            if not plan:
                continue

            total = len(plan.schedule)
            completed = sum(1 for item in plan.schedule if item.status == TaskStatus.completed)
            rate = (completed / total * 100) if total > 0 else 0
            completion_rates.append((session.metadata.session_id, rate))

        if len(completion_rates) < 3:
            return None

        # Check if recent rates are better than earlier ones
        recent_avg = sum(r[1] for r in completion_rates[-3:]) / 3
        earlier_avg = sum(r[1] for r in completion_rates[:-3]) / max(1, len(completion_rates) - 3)

        if recent_avg > earlier_avg + 10:
            return ProductivityPattern(
                pattern_type="improvement",
                description=f"Completion rate improved by {int(recent_avg - earlier_avg)}% recently",
                confidence=0.7,
                supporting_data=[r[0] for r in completion_rates[-3:]],
            )
        elif earlier_avg > recent_avg + 10:
            return ProductivityPattern(
                pattern_type="decline",
                description=f"Completion rate declined by {int(earlier_avg - recent_avg)}% recently",
                confidence=0.7,
                supporting_data=[r[0] for r in completion_rates[-3:]],
            )

        return None

    def _find_category_patterns(self, sessions: list[Memory]) -> ProductivityPattern | None:
        """Find patterns in category distribution."""
        category_counts: dict[str, int] = {}

        for session in sessions:
            plan = session.agent_state.plan
            if not plan:
                continue

            daily_categories = set()
            for item in plan.schedule:
                daily_categories.add(item.category.value)

            for cat in daily_categories:
                category_counts[cat] = category_counts.get(cat, 0) + 1

        # Find categories present every day
        num_sessions = len(sessions)
        consistent_cats = [cat for cat, count in category_counts.items() if count == num_sessions]

        if len(consistent_cats) >= 2:
            return ProductivityPattern(
                pattern_type="successful_habit",
                description=f"Consistent daily categories: {', '.join(consistent_cats)}",
                confidence=0.8,
                supporting_data=[s.metadata.session_id for s in sessions[-3:]],
            )

        return None
