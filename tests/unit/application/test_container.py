"""Tests for dependency injection container."""

from unittest.mock import MagicMock, patch

import pytest

from src.application.config import AppConfig, InputConfig, LLMConfig, RetryConfig, StorageConfig
from src.application.container import Container
from src.domain.services.agent_service import AgentService
from src.domain.services.export_service import ExportService
from src.domain.services.planning_service import PlanningService
from src.domain.services.state_machine import StateMachine
from src.domain.services.time_tracking_service import TimeTrackingService
from src.infrastructure.storage.cache import StorageCache
from src.infrastructure.storage.json_storage import JSONStorage


@pytest.fixture
def test_config(tmp_path):
    """Create test config with local paths."""
    return AppConfig(
        llm=LLMConfig(api_key="test-key", model="gpt-4o-mini"),
        storage=StorageConfig(
            backend="json",
            use_local=True,
            sessions_dir=tmp_path / "sessions",
            profiles_dir=tmp_path / "profiles",
            templates_dir=tmp_path / "templates",
            plans_export_dir=tmp_path / "plans",
            summaries_export_dir=tmp_path / "summaries",
        ),
        input=InputConfig(),
        retry=RetryConfig(),
    )


@pytest.fixture
def container(test_config, tmp_path):
    """Create container with test config."""
    return Container(test_config)


class TestContainerInitialization:
    """Tests for container initialization."""

    def test_container_stores_config(self, container, test_config):
        """Container should store the config."""
        assert container.config == test_config

    def test_container_starts_with_none_services(self, container):
        """All services should be None initially."""
        assert container._llm_provider is None
        assert container._storage is None
        assert container._cache is None
        assert container._state_machine is None
        assert container._planning_service is None
        assert container._agent_service is None


class TestLazyInitialization:
    """Tests for lazy initialization of services."""

    @patch("src.application.container.OpenAIProvider")
    def test_llm_provider_lazy_init(self, mock_provider_class, container):
        """LLM provider should be initialized lazily."""
        mock_provider = MagicMock()
        mock_provider_class.return_value = mock_provider

        # First access initializes
        provider = container.llm_provider
        assert provider is not None
        mock_provider_class.assert_called_once_with(container.config.llm)

        # Second access returns same instance
        provider2 = container.llm_provider
        assert provider2 is provider
        mock_provider_class.assert_called_once()  # Still just one call

    def test_storage_lazy_init_json(self, container):
        """JSON storage should be initialized lazily."""
        assert container._storage is None

        storage = container.storage
        assert isinstance(storage, JSONStorage)

        # Second access returns same instance
        storage2 = container.storage
        assert storage2 is storage

    def test_cache_lazy_init(self, container):
        """Cache should be initialized lazily."""
        assert container._cache is None

        cache = container.cache
        assert isinstance(cache, StorageCache)

        # Second access returns same instance
        cache2 = container.cache
        assert cache2 is cache

    def test_state_machine_lazy_init(self, container):
        """State machine should be initialized lazily."""
        assert container._state_machine is None

        sm = container.state_machine
        assert isinstance(sm, StateMachine)

        sm2 = container.state_machine
        assert sm2 is sm

    def test_planning_service_lazy_init(self, container):
        """Planning service should be initialized lazily."""
        assert container._planning_service is None

        ps = container.planning_service
        assert isinstance(ps, PlanningService)

        ps2 = container.planning_service
        assert ps2 is ps

    @patch("src.application.container.OpenAIProvider")
    def test_agent_service_lazy_init(self, mock_provider_class, container):
        """Agent service should be initialized lazily with dependencies."""
        mock_provider = MagicMock()
        mock_provider_class.return_value = mock_provider

        assert container._agent_service is None

        agent = container.agent_service
        assert isinstance(agent, AgentService)

        agent2 = container.agent_service
        assert agent2 is agent

    def test_time_tracking_service_lazy_init(self, container):
        """Time tracking service should be initialized lazily."""
        assert container._time_tracking_service is None

        tts = container.time_tracking_service
        assert isinstance(tts, TimeTrackingService)

        tts2 = container.time_tracking_service
        assert tts2 is tts

    def test_export_service_lazy_init(self, container):
        """Export service should be initialized lazily."""
        assert container._export_service is None

        es = container.export_service
        assert isinstance(es, ExportService)

        es2 = container.export_service
        assert es2 is es


class TestStorageBackends:
    """Tests for different storage backends."""

    def test_json_storage_backend(self, test_config):
        """Should create JSON storage for json backend."""
        test_config.storage.backend = "json"
        container = Container(test_config)

        storage = container.storage
        assert isinstance(storage, JSONStorage)

    @patch("src.infrastructure.storage.sqlite_storage.SQLiteStorage")
    def test_sqlite_storage_backend(self, mock_sqlite_class, test_config):
        """Should create SQLite storage for sqlite backend."""
        test_config.storage.backend = "sqlite"
        container = Container(test_config)

        mock_sqlite = MagicMock()
        mock_sqlite_class.return_value = mock_sqlite

        storage = container.storage
        assert storage is mock_sqlite
        mock_sqlite_class.assert_called_once_with(test_config.storage)

    def test_unknown_storage_backend_raises(self, test_config):
        """Should raise error for unknown storage backend."""
        test_config.storage.backend = "unknown"
        container = Container(test_config)

        with pytest.raises(ValueError, match="Unknown storage backend"):
            _ = container.storage


class TestCacheConfiguration:
    """Tests for cache configuration."""

    def test_cache_uses_config_ttl(self, test_config):
        """Cache should use TTL from config."""
        test_config.storage.cache_ttl = 120
        container = Container(test_config)

        cache = container.cache
        assert cache.ttl == 120
