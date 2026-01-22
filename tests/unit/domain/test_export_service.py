"""Tests for ExportService."""

import pytest
from datetime import datetime, timedelta
from pathlib import Path
import tempfile

from src.domain.services.export_service import ExportService, ExportResult
from src.domain.models.planning import Plan, ScheduleItem, TaskStatus
from src.domain.models.session import Memory, AgentState, SessionMetadata
from src.domain.models.conversation import ConversationHistory
from src.application.config import StorageConfig


@pytest.fixture
def storage_config():
    """Create a storage config with temp directories."""
    with tempfile.TemporaryDirectory() as tmpdir:
        tmppath = Path(tmpdir)
        config = StorageConfig(
            plans_export_dir=tmppath / "plans",
            summaries_export_dir=tmppath / "summaries",
        )
        yield config


@pytest.fixture
def export_service(storage_config):
    """Create ExportService instance."""
    return ExportService(storage_config)


@pytest.fixture
def sample_plan():
    """Create a sample plan."""
    return Plan(
        schedule=[
            ScheduleItem(
                time="09:00-10:00",
                task="Morning standup",
                estimated_minutes=60,
            ),
            ScheduleItem(
                time="10:00-12:00",
                task="Deep work",
                estimated_minutes=120,
            ),
        ],
        priorities=["Complete project"],
        notes="Test notes",
    )


@pytest.fixture
def sample_plan_with_tracking():
    """Create a sample plan with tracking data."""
    now = datetime.now()
    return Plan(
        schedule=[
            ScheduleItem(
                time="09:00-10:00",
                task="Morning standup",
                estimated_minutes=60,
                status=TaskStatus.completed,
                actual_start=now - timedelta(minutes=65),
                actual_end=now - timedelta(minutes=5),
            ),
            ScheduleItem(
                time="10:00-12:00",
                task="Deep work",
                estimated_minutes=120,
                status=TaskStatus.not_started,
            ),
        ],
        priorities=["Complete project"],
        notes="Test notes",
    )


@pytest.fixture
def sample_memory(sample_plan):
    """Create a sample Memory object."""
    return Memory(
        metadata=SessionMetadata(
            session_id="2026-01-22",
            created_at=datetime.now(),
            last_updated=datetime.now(),
        ),
        agent_state=AgentState(plan=sample_plan),
        conversation=ConversationHistory(),
    )


@pytest.fixture
def sample_memory_with_tracking(sample_plan_with_tracking):
    """Create a Memory with tracking data."""
    return Memory(
        metadata=SessionMetadata(
            session_id="2026-01-22",
            created_at=datetime.now(),
            last_updated=datetime.now(),
        ),
        agent_state=AgentState(plan=sample_plan_with_tracking),
        conversation=ConversationHistory(),
    )


class TestExportServiceInit:
    """Tests for ExportService initialization."""

    def test_init_with_config(self, storage_config):
        """Test initialization with config."""
        service = ExportService(storage_config)

        assert service.plans_dir == storage_config.plans_export_dir
        assert service.summaries_dir == storage_config.summaries_export_dir
        assert service.markdown_exporter is not None
        assert service.summary_exporter is not None


class TestExportServicePaths:
    """Tests for path generation."""

    def test_get_plan_path(self, export_service, storage_config):
        """Test plan path generation."""
        path = export_service.get_plan_path("2026-01-22")

        assert path == storage_config.plans_export_dir / "2026-01-22.md"

    def test_get_summary_path(self, export_service, storage_config):
        """Test summary path generation."""
        path = export_service.get_summary_path("2026-01-22")

        assert path == storage_config.summaries_export_dir / "2026-01-22-summary.md"


class TestExportPlan:
    """Tests for plan export."""

    @pytest.mark.asyncio
    async def test_export_plan_success(self, export_service, sample_plan):
        """Test successful plan export."""
        result = await export_service.export_plan(sample_plan, "2026-01-22")

        assert result.success is True
        assert result.file_path is not None
        assert result.file_path.exists()
        assert result.error is None

    @pytest.mark.asyncio
    async def test_export_plan_with_custom_path(self, export_service, sample_plan):
        """Test plan export to custom path."""
        with tempfile.TemporaryDirectory() as tmpdir:
            custom_path = Path(tmpdir) / "custom-plan.md"

            result = await export_service.export_plan(sample_plan, "2026-01-22", custom_path)

            assert result.success is True
            assert result.file_path == custom_path
            assert custom_path.exists()

    @pytest.mark.asyncio
    async def test_export_plan_content(self, export_service, sample_plan):
        """Test that exported plan has correct content."""
        result = await export_service.export_plan(sample_plan, "2026-01-22")

        content = result.file_path.read_text()
        assert "# Daily Plan" in content
        assert "Morning standup" in content
        assert "Deep work" in content


class TestExportSummary:
    """Tests for summary export."""

    @pytest.mark.asyncio
    async def test_export_summary_success(self, export_service, sample_memory):
        """Test successful summary export."""
        result = await export_service.export_summary(sample_memory)

        assert result.success is True
        assert result.file_path is not None
        assert result.file_path.exists()
        assert result.error is None
        assert result.stats is not None

    @pytest.mark.asyncio
    async def test_export_summary_with_custom_path(self, export_service, sample_memory):
        """Test summary export to custom path."""
        with tempfile.TemporaryDirectory() as tmpdir:
            custom_path = Path(tmpdir) / "custom-summary.md"

            result = await export_service.export_summary(sample_memory, custom_path)

            assert result.success is True
            assert result.file_path == custom_path
            assert custom_path.exists()

    @pytest.mark.asyncio
    async def test_export_summary_returns_stats(self, export_service, sample_memory_with_tracking):
        """Test that summary export returns statistics."""
        result = await export_service.export_summary(sample_memory_with_tracking)

        assert result.stats is not None
        assert "total_tasks" in result.stats
        assert "completed" in result.stats
        assert "completion_rate" in result.stats

    @pytest.mark.asyncio
    async def test_export_summary_no_plan_fails(self, export_service):
        """Test that summary export fails when no plan."""
        memory = Memory(
            metadata=SessionMetadata(
                session_id="2026-01-22",
                created_at=datetime.now(),
                last_updated=datetime.now(),
            ),
            agent_state=AgentState(plan=None),
            conversation=ConversationHistory(),
        )

        result = await export_service.export_summary(memory)

        assert result.success is False
        assert result.error is not None
        assert "No plan found" in result.error


class TestExportAll:
    """Tests for combined export."""

    @pytest.mark.asyncio
    async def test_export_all_success(self, export_service, sample_memory):
        """Test successful combined export."""
        results = await export_service.export_all(sample_memory)

        assert "plan" in results
        assert "summary" in results
        assert results["plan"].success is True
        assert results["summary"].success is True

    @pytest.mark.asyncio
    async def test_export_all_creates_both_files(self, export_service, sample_memory):
        """Test that both files are created."""
        results = await export_service.export_all(sample_memory)

        assert results["plan"].file_path.exists()
        assert results["summary"].file_path.exists()

    @pytest.mark.asyncio
    async def test_export_all_with_custom_paths(self, export_service, sample_memory):
        """Test combined export with custom paths."""
        with tempfile.TemporaryDirectory() as tmpdir:
            plan_path = Path(tmpdir) / "custom-plan.md"
            summary_path = Path(tmpdir) / "custom-summary.md"

            results = await export_service.export_all(sample_memory, plan_path, summary_path)

            assert results["plan"].file_path == plan_path
            assert results["summary"].file_path == summary_path

    @pytest.mark.asyncio
    async def test_export_all_no_plan_fails(self, export_service):
        """Test combined export fails when no plan."""
        memory = Memory(
            metadata=SessionMetadata(
                session_id="2026-01-22",
                created_at=datetime.now(),
                last_updated=datetime.now(),
            ),
            agent_state=AgentState(plan=None),
            conversation=ConversationHistory(),
        )

        results = await export_service.export_all(memory)

        assert results["plan"].success is False
        assert results["summary"].success is False


class TestExportResult:
    """Tests for ExportResult dataclass."""

    def test_success_result(self):
        """Test creating a success result."""
        result = ExportResult(
            success=True,
            file_path=Path("/tmp/test.md"),
        )

        assert result.success is True
        assert result.error is None
        assert result.stats is None

    def test_failure_result(self):
        """Test creating a failure result."""
        result = ExportResult(
            success=False,
            file_path=None,
            error="Something went wrong",
        )

        assert result.success is False
        assert result.file_path is None
        assert result.error == "Something went wrong"

    def test_result_with_stats(self):
        """Test creating result with stats."""
        result = ExportResult(
            success=True,
            file_path=Path("/tmp/test.md"),
            stats={"total_tasks": 5, "completed": 3},
        )

        assert result.stats is not None
        assert result.stats["total_tasks"] == 5
