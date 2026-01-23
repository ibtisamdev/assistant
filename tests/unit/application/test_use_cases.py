"""Tests for remaining use cases to increase coverage."""

from unittest.mock import MagicMock

import pytest

from tests.conftest import (
    MockInputHandler,
    MockStorage,
)


class TestViewStatsUseCase:
    """Tests for ViewStatsUseCase."""

    @pytest.fixture
    def mock_container(self):
        """Create mock container."""
        container = MagicMock()
        container.storage = MockStorage()
        return container

    @pytest.mark.asyncio
    async def test_view_stats_initialization(self, mock_container):
        """Test use case can be initialized."""
        from src.application.use_cases.view_stats import ViewStatsUseCase

        use_case = ViewStatsUseCase(mock_container)
        assert use_case.storage == mock_container.storage


class TestViewAggregateStatsUseCase:
    """Tests for ViewAggregateStatsUseCase."""

    @pytest.fixture
    def mock_container(self):
        """Create mock container."""
        container = MagicMock()
        container.storage = MockStorage()
        return container

    @pytest.mark.asyncio
    async def test_aggregate_stats_initialization(self, mock_container):
        """Test use case can be initialized."""
        from src.application.use_cases.view_aggregate_stats import ViewAggregateStatsUseCase

        use_case = ViewAggregateStatsUseCase(mock_container)
        assert use_case.storage == mock_container.storage


class TestExportPlanUseCase:
    """Tests for ExportPlanUseCase."""

    @pytest.fixture
    def mock_container(self):
        """Create mock container."""
        container = MagicMock()
        container.storage = MockStorage()
        return container

    @pytest.mark.asyncio
    async def test_export_plan_initialization(self, mock_container):
        """Test use case can be initialized."""
        from src.application.use_cases.export_plan import ExportPlanUseCase

        use_case = ExportPlanUseCase(mock_container)
        assert use_case.storage == mock_container.storage


class TestExportSummaryUseCase:
    """Tests for ExportSummaryUseCase."""

    @pytest.fixture
    def mock_container(self):
        """Create mock container."""
        container = MagicMock()
        container.storage = MockStorage()
        return container

    @pytest.mark.asyncio
    async def test_export_summary_initialization(self, mock_container):
        """Test use case can be initialized."""
        from src.application.use_cases.export_summary import ExportSummaryUseCase

        use_case = ExportSummaryUseCase(mock_container)
        assert use_case.storage == mock_container.storage


class TestExportAllUseCase:
    """Tests for ExportAllUseCase."""

    @pytest.fixture
    def mock_container(self):
        """Create mock container."""
        container = MagicMock()
        container.storage = MockStorage()
        return container

    @pytest.mark.asyncio
    async def test_export_all_initialization(self, mock_container):
        """Test use case can be initialized."""
        from src.application.use_cases.export_all import ExportAllUseCase

        use_case = ExportAllUseCase(mock_container)
        assert use_case.storage == mock_container.storage


class TestTemplateListUseCase:
    """Tests for ListTemplatesUseCase."""

    @pytest.fixture
    def mock_container(self):
        """Create mock container."""
        container = MagicMock()
        container.storage = MockStorage()
        return container

    @pytest.mark.asyncio
    async def test_list_templates_initialization(self, mock_container):
        """Test use case can be initialized."""
        from src.application.use_cases.template_list import ListTemplatesUseCase

        use_case = ListTemplatesUseCase(mock_container)
        assert use_case.storage == mock_container.storage


class TestTemplateSaveUseCase:
    """Tests for SaveTemplateUseCase."""

    @pytest.fixture
    def mock_container(self):
        """Create mock container."""
        container = MagicMock()
        container.storage = MockStorage()
        return container

    @pytest.mark.asyncio
    async def test_save_template_initialization(self, mock_container):
        """Test use case can be initialized."""
        from src.application.use_cases.template_save import SaveTemplateUseCase

        use_case = SaveTemplateUseCase(mock_container)
        assert use_case.storage == mock_container.storage


class TestTemplateShowUseCase:
    """Tests for ShowTemplateUseCase."""

    @pytest.fixture
    def mock_container(self):
        """Create mock container."""
        container = MagicMock()
        container.storage = MockStorage()
        return container

    @pytest.mark.asyncio
    async def test_show_template_initialization(self, mock_container):
        """Test use case can be initialized."""
        from src.application.use_cases.template_show import ShowTemplateUseCase

        use_case = ShowTemplateUseCase(mock_container)
        assert use_case.storage == mock_container.storage


class TestTemplateApplyUseCase:
    """Tests for ApplyTemplateUseCase."""

    @pytest.fixture
    def mock_container(self):
        """Create mock container."""
        container = MagicMock()
        container.storage = MockStorage()
        return container

    @pytest.mark.asyncio
    async def test_apply_template_initialization(self, mock_container):
        """Test use case can be initialized."""
        from src.application.use_cases.template_apply import ApplyTemplateUseCase

        use_case = ApplyTemplateUseCase(mock_container)
        assert use_case.storage == mock_container.storage


class TestTemplateDeleteUseCase:
    """Tests for DeleteTemplateUseCase."""

    @pytest.fixture
    def mock_container(self):
        """Create mock container."""
        container = MagicMock()
        container.storage = MockStorage()
        return container

    @pytest.mark.asyncio
    async def test_delete_template_initialization(self, mock_container):
        """Test use case can be initialized."""
        from src.application.use_cases.template_delete import DeleteTemplateUseCase

        use_case = DeleteTemplateUseCase(mock_container)
        assert use_case.storage == mock_container.storage


class TestResumeSessionUseCase:
    """Tests for ResumeSessionUseCase."""

    @pytest.fixture
    def mock_container(self):
        """Create mock container."""
        container = MagicMock()
        container.storage = MockStorage()
        container.agent_service = MagicMock()
        container.input_handler = MockInputHandler()
        container.plan_formatter = MagicMock()
        container.progress_formatter = MagicMock()
        return container

    @pytest.mark.asyncio
    async def test_resume_initialization(self, mock_container):
        """Test use case can be initialized."""
        from src.application.use_cases.resume_session import ResumeSessionUseCase

        use_case = ResumeSessionUseCase(mock_container)
        assert use_case.storage == mock_container.storage


class TestRevisePlanUseCase:
    """Tests for RevisePlanUseCase."""

    @pytest.fixture
    def mock_container(self):
        """Create mock container."""
        container = MagicMock()
        container.storage = MockStorage()
        container.agent_service = MagicMock()
        container.input_handler = MockInputHandler()
        container.plan_formatter = MagicMock()
        container.progress_formatter = MagicMock()
        return container

    @pytest.mark.asyncio
    async def test_revise_initialization(self, mock_container):
        """Test use case can be initialized."""
        from src.application.use_cases.revise_plan import RevisePlanUseCase

        use_case = RevisePlanUseCase(mock_container)
        assert use_case.storage == mock_container.storage


class TestImportTasksUseCase:
    """Tests for ImportTasksUseCase."""

    @pytest.fixture
    def mock_container(self):
        """Create mock container."""
        container = MagicMock()
        container.storage = MockStorage()
        return container

    @pytest.mark.asyncio
    async def test_import_initialization(self, mock_container):
        """Test use case can be initialized."""
        from src.application.use_cases.import_tasks import ImportTasksUseCase

        use_case = ImportTasksUseCase(mock_container)
        assert use_case.storage == mock_container.storage


class TestQuickStartUseCase:
    """Tests for QuickStartUseCase."""

    @pytest.fixture
    def mock_container(self):
        """Create mock container."""
        container = MagicMock()
        container.storage = MockStorage()
        container.agent_service = MagicMock()
        container.input_handler = MockInputHandler()
        container.plan_formatter = MagicMock()
        container.progress_formatter = MagicMock()
        return container

    @pytest.mark.asyncio
    async def test_quick_start_initialization(self, mock_container):
        """Test use case can be initialized."""
        from src.application.use_cases.quick_start import QuickStartUseCase

        use_case = QuickStartUseCase(mock_container)
        assert use_case.storage == mock_container.storage
