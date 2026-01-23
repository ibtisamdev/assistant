"""Tests for DayTemplate model."""

from datetime import datetime

import pytest

from src.domain.models.planning import ScheduleItem, TaskCategory, TaskStatus
from src.domain.models.template import DayTemplate, TemplateMetadata


@pytest.fixture
def sample_schedule():
    """Create sample schedule items."""
    return [
        ScheduleItem(
            time="09:00-10:00",
            task="Morning standup",
            estimated_minutes=30,
            priority="medium",
            status=TaskStatus.completed,
            category=TaskCategory.meetings,
        ),
        ScheduleItem(
            time="10:00-12:00",
            task="Deep work",
            estimated_minutes=120,
            priority="high",
            status=TaskStatus.in_progress,
            actual_start=datetime.now(),
            category=TaskCategory.productive,
        ),
    ]


@pytest.fixture
def sample_template(sample_schedule):
    """Create a sample template."""
    return DayTemplate(
        name="work-day",
        description="Standard work day template",
        schedule=sample_schedule,
        priorities=["Complete project", "Review PRs"],
        notes="Focus on high-priority items",
        created_at=datetime.now(),
        use_count=5,
    )


class TestDayTemplate:
    """Tests for DayTemplate model."""

    def test_create_template(self, sample_schedule):
        """Test creating a template."""
        template = DayTemplate(
            name="test-template",
            schedule=sample_schedule,
            priorities=["Test"],
            notes="Test notes",
        )

        assert template.name == "test-template"
        assert len(template.schedule) == 2
        assert template.use_count == 0
        assert template.last_used is None

    def test_prepare_for_new_day(self, sample_template):
        """Test preparing template for a new day."""
        prepared = sample_template.prepare_for_new_day()

        # All tasks should be reset
        for task in prepared.schedule:
            assert task.status == TaskStatus.not_started
            assert task.actual_start is None
            assert task.actual_end is None
            assert len(task.edits) == 0

        # Original schedule should preserve other properties
        assert prepared.schedule[0].task == "Morning standup"
        assert prepared.schedule[0].estimated_minutes == 30
        assert prepared.schedule[0].category == TaskCategory.meetings

    def test_record_use(self, sample_template):
        """Test recording template usage."""
        original_count = sample_template.use_count

        sample_template.record_use()

        assert sample_template.use_count == original_count + 1
        assert sample_template.last_used is not None

    def test_template_with_empty_schedule(self):
        """Test creating template with empty schedule."""
        template = DayTemplate(
            name="empty-template",
            schedule=[],
            priorities=[],
            notes="",
        )

        prepared = template.prepare_for_new_day()
        assert len(prepared.schedule) == 0


class TestTemplateMetadata:
    """Tests for TemplateMetadata model."""

    def test_create_metadata(self):
        """Test creating template metadata."""
        metadata = TemplateMetadata(
            name="work-day",
            description="Standard work day",
            task_count=5,
            created_at=datetime.now(),
            last_used=None,
            use_count=0,
        )

        assert metadata.name == "work-day"
        assert metadata.task_count == 5
        assert metadata.use_count == 0

    def test_metadata_with_last_used(self):
        """Test metadata with last used date."""
        now = datetime.now()
        metadata = TemplateMetadata(
            name="work-day",
            description="",
            task_count=3,
            created_at=now,
            last_used=now,
            use_count=10,
        )

        assert metadata.last_used == now
        assert metadata.use_count == 10
