"""Tests for export modules."""

import pytest
from datetime import datetime, timedelta
from pathlib import Path
import tempfile
import asyncio

from src.infrastructure.export.markdown import MarkdownExporter
from src.infrastructure.export.summary import SummaryExporter
from src.domain.models.planning import Plan, ScheduleItem, TaskStatus
from src.domain.models.session import Memory, AgentState, SessionMetadata
from src.domain.models.conversation import ConversationHistory


@pytest.fixture
def markdown_exporter():
    """Create MarkdownExporter instance."""
    return MarkdownExporter()


@pytest.fixture
def summary_exporter():
    """Create SummaryExporter instance."""
    return SummaryExporter()


@pytest.fixture
def sample_plan():
    """Create a sample plan with multiple tasks."""
    return Plan(
        schedule=[
            ScheduleItem(
                time="09:00-10:00",
                task="Morning standup",
                estimated_minutes=60,
                priority="high",
            ),
            ScheduleItem(
                time="10:00-12:00",
                task="Deep work session",
                estimated_minutes=120,
                priority="high",
            ),
            ScheduleItem(
                time="12:00-13:00",
                task="Lunch break",
                estimated_minutes=60,
                priority="low",
            ),
        ],
        priorities=["Complete project", "Review PRs"],
        notes="Focus on high-priority items",
    )


@pytest.fixture
def sample_plan_with_tracking():
    """Create a sample plan with time tracking data."""
    now = datetime.now()
    return Plan(
        schedule=[
            ScheduleItem(
                time="09:00-10:00",
                task="Morning standup",
                estimated_minutes=60,
                priority="high",
                status=TaskStatus.completed,
                actual_start=now - timedelta(minutes=75),
                actual_end=now - timedelta(minutes=15),
            ),
            ScheduleItem(
                time="10:00-12:00",
                task="Deep work session",
                estimated_minutes=120,
                priority="high",
                status=TaskStatus.in_progress,
                actual_start=now - timedelta(minutes=10),
            ),
            ScheduleItem(
                time="12:00-13:00",
                task="Lunch break",
                estimated_minutes=60,
                priority="low",
                status=TaskStatus.not_started,
            ),
            ScheduleItem(
                time="14:00-15:00",
                task="Review PRs",
                estimated_minutes=60,
                priority="medium",
                status=TaskStatus.skipped,
            ),
        ],
        priorities=["Complete project", "Review PRs"],
        notes="Focus on high-priority items",
    )


@pytest.fixture
def sample_memory(sample_plan):
    """Create a sample Memory object."""
    return Memory(
        metadata=SessionMetadata(
            session_id="2026-01-22",
            created_at=datetime.now() - timedelta(hours=2),
            last_updated=datetime.now(),
        ),
        agent_state=AgentState(plan=sample_plan),
        conversation=ConversationHistory(),
    )


@pytest.fixture
def sample_memory_with_tracking(sample_plan_with_tracking):
    """Create a sample Memory object with tracking data."""
    return Memory(
        metadata=SessionMetadata(
            session_id="2026-01-22",
            created_at=datetime.now() - timedelta(hours=2),
            last_updated=datetime.now(),
        ),
        agent_state=AgentState(plan=sample_plan_with_tracking),
        conversation=ConversationHistory(),
    )


class TestMarkdownExporter:
    """Tests for MarkdownExporter."""

    def test_to_string_basic(self, markdown_exporter, sample_plan):
        """Test basic plan export to string."""
        result = markdown_exporter.to_string(sample_plan, "2026-01-22")

        assert "# Daily Plan - January 22, 2026" in result
        assert "## Schedule" in result
        assert "## Top Priorities" in result
        assert "## Notes" in result
        assert "Morning standup" in result
        assert "Deep work session" in result
        assert "Complete project" in result
        assert "Focus on high-priority items" in result

    def test_to_string_includes_checkboxes(self, markdown_exporter, sample_plan):
        """Test that checkboxes are included for manual tracking."""
        result = markdown_exporter.to_string(sample_plan)

        assert "- [ ]" in result  # Checkbox markers

    def test_to_string_includes_time_estimates(self, markdown_exporter, sample_plan):
        """Test that time estimates are included."""
        result = markdown_exporter.to_string(sample_plan, "2026-01-22")

        assert "~1h" in result or "~60m" in result  # 60 minutes
        assert "~2h" in result or "~120m" in result  # 120 minutes

    def test_to_string_includes_priority_tags(self, markdown_exporter, sample_plan):
        """Test that priority tags are included for non-medium priorities."""
        result = markdown_exporter.to_string(sample_plan, "2026-01-22")

        assert "[high]" in result
        assert "[low]" in result

    def test_to_string_includes_footer(self, markdown_exporter, sample_plan):
        """Test that footer with metadata is included."""
        result = markdown_exporter.to_string(sample_plan, "2026-01-22")

        assert "Generated by Daily Planning Assistant" in result
        assert "Total estimated time" in result

    def test_to_string_empty_schedule(self, markdown_exporter):
        """Test export of plan with empty schedule."""
        empty_plan = Plan(schedule=[], priorities=[], notes="")

        result = markdown_exporter.to_string(empty_plan)

        assert "No tasks scheduled" in result

    def test_to_string_empty_priorities(self, markdown_exporter):
        """Test export of plan with no priorities."""
        plan = Plan(
            schedule=[ScheduleItem(time="09:00-10:00", task="Test")],
            priorities=[],
            notes="",
        )

        result = markdown_exporter.to_string(plan)

        assert "No priorities set" in result

    @pytest.mark.asyncio
    async def test_export_creates_file(self, markdown_exporter, sample_plan):
        """Test that export creates a file."""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "test-plan.md"

            result = await markdown_exporter.export(sample_plan, output_path, "2026-01-22")

            assert result == output_path
            assert output_path.exists()

            content = output_path.read_text()
            assert "# Daily Plan" in content

    @pytest.mark.asyncio
    async def test_export_creates_parent_directories(self, markdown_exporter, sample_plan):
        """Test that export creates parent directories if needed."""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "nested" / "dirs" / "test-plan.md"

            await markdown_exporter.export(sample_plan, output_path, "2026-01-22")

            assert output_path.exists()


class TestSummaryExporter:
    """Tests for SummaryExporter."""

    def test_to_string_basic(self, summary_exporter, sample_plan):
        """Test basic summary export."""
        result = summary_exporter.to_string(sample_plan, "2026-01-22")

        assert "# Daily Summary - January 22, 2026" in result
        assert "## Completion Overview" in result
        assert "## Time Analysis" in result

    def test_to_string_with_completion_stats(self, summary_exporter, sample_plan_with_tracking):
        """Test summary with completion statistics."""
        result = summary_exporter.to_string(sample_plan_with_tracking, "2026-01-22")

        assert "Completed" in result
        assert "Skipped" in result
        assert "Completion Rate" in result

    def test_to_string_with_time_tracking(self, summary_exporter, sample_plan_with_tracking):
        """Test summary with time tracking data."""
        result = summary_exporter.to_string(sample_plan_with_tracking, "2026-01-22")

        assert "Estimated" in result
        assert "Actual" in result
        assert "Variance" in result

    def test_to_string_without_tracking_shows_na(self, summary_exporter, sample_plan):
        """Test that N/A is shown when no tracking data."""
        result = summary_exporter.to_string(sample_plan, "2026-01-22")

        assert "N/A" in result
        assert "No time tracking data recorded" in result

    def test_to_string_completed_section(self, summary_exporter, sample_plan_with_tracking):
        """Test that completed tasks section is present."""
        result = summary_exporter.to_string(sample_plan_with_tracking, "2026-01-22")

        assert "## Tasks Completed" in result
        assert "[x]" in result  # Checked checkbox

    def test_to_string_skipped_section(self, summary_exporter, sample_plan_with_tracking):
        """Test that skipped tasks section is present."""
        result = summary_exporter.to_string(sample_plan_with_tracking, "2026-01-22")

        assert "## Tasks Skipped" in result

    def test_to_string_includes_notes(self, summary_exporter, sample_plan_with_tracking):
        """Test that notes are included."""
        result = summary_exporter.to_string(
            sample_plan_with_tracking, "2026-01-22", notes="Some important notes"
        )

        assert "## Notes" in result
        assert "Some important notes" in result

    def test_to_string_includes_footer(self, summary_exporter, sample_plan):
        """Test that footer is included."""
        result = summary_exporter.to_string(sample_plan, "2026-01-22")

        assert "Generated by Daily Planning Assistant" in result
        assert "Session ID: 2026-01-22" in result

    @pytest.mark.asyncio
    async def test_export_creates_file(self, summary_exporter, sample_memory_with_tracking):
        """Test that export creates a file."""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "test-summary.md"

            result = await summary_exporter.export(sample_memory_with_tracking, output_path)

            assert result == output_path
            assert output_path.exists()

            content = output_path.read_text()
            assert "# Daily Summary" in content

    @pytest.mark.asyncio
    async def test_export_raises_if_no_plan(self, summary_exporter):
        """Test that export raises if no plan in memory."""
        memory = Memory(
            metadata=SessionMetadata(
                session_id="2026-01-22",
                created_at=datetime.now(),
                last_updated=datetime.now(),
            ),
            agent_state=AgentState(plan=None),
            conversation=ConversationHistory(),
        )

        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "test-summary.md"

            with pytest.raises(ValueError, match="No plan found"):
                await summary_exporter.export(memory, output_path)


class TestMarkdownExporterDateFormatting:
    """Tests for date formatting in MarkdownExporter."""

    def test_format_date_header_valid(self, markdown_exporter):
        """Test valid date formatting."""
        result = markdown_exporter._format_date_header("2026-01-22")

        assert result == "January 22, 2026"

    def test_format_date_header_invalid_returns_original(self, markdown_exporter):
        """Test invalid date returns original string."""
        result = markdown_exporter._format_date_header("invalid-date")

        assert result == "invalid-date"


class TestMarkdownExporterDurationFormatting:
    """Tests for duration formatting in MarkdownExporter."""

    def test_format_duration_minutes(self, markdown_exporter):
        """Test formatting minutes only."""
        assert markdown_exporter._format_duration(30) == "30m"

    def test_format_duration_hours(self, markdown_exporter):
        """Test formatting hours only."""
        assert markdown_exporter._format_duration(120) == "2h"

    def test_format_duration_hours_and_minutes(self, markdown_exporter):
        """Test formatting hours and minutes."""
        assert markdown_exporter._format_duration(90) == "1h 30m"

    def test_format_duration_none(self, markdown_exporter):
        """Test formatting None duration."""
        assert markdown_exporter._format_duration(None) == ""


class TestSummaryExporterVarianceFormatting:
    """Tests for variance formatting in SummaryExporter."""

    def test_format_variance_positive(self, summary_exporter):
        """Test formatting positive variance."""
        result = summary_exporter._format_variance(15)
        assert result == "+15m"

    def test_format_variance_negative(self, summary_exporter):
        """Test formatting negative variance."""
        result = summary_exporter._format_variance(-10)
        assert result == "-10m"

    def test_format_variance_zero(self, summary_exporter):
        """Test formatting zero variance."""
        result = summary_exporter._format_variance(0)
        assert result == "0m"

    def test_format_variance_none(self, summary_exporter):
        """Test formatting None variance."""
        result = summary_exporter._format_variance(None)
        assert result == "N/A"
