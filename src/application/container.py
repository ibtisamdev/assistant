"""Dependency injection container - lazy initialization."""

from typing import Any

from ..domain.services.agent_service import AgentService
from ..domain.services.export_service import ExportService
from ..domain.services.planning_service import PlanningService
from ..domain.services.state_machine import StateMachine
from ..domain.services.time_tracking_service import TimeTrackingService
from ..infrastructure.io.formatters import PlanFormatter, ProgressFormatter, SessionFormatter
from ..infrastructure.io.input_handler import InputHandler
from ..infrastructure.llm.openai_provider import OpenAIProvider
from ..infrastructure.llm.retry import RetryStrategy
from ..infrastructure.storage.cache import StorageCache
from ..infrastructure.storage.json_storage import JSONStorage
from .config import AppConfig


class Container:
    """Dependency injection container with lazy initialization."""

    def __init__(self, config: AppConfig):
        self.config = config

        # Private attributes for lazy init
        self._llm_provider: OpenAIProvider | None = None
        self._storage: Any = None  # Can be JSONStorage or SQLiteStorage
        self._cache: StorageCache | None = None
        self._state_machine: StateMachine | None = None
        self._planning_service: PlanningService | None = None
        self._agent_service: AgentService | None = None
        self._input_handler: InputHandler | None = None
        self._plan_formatter: PlanFormatter | None = None
        self._session_formatter: SessionFormatter | None = None
        self._progress_formatter: ProgressFormatter | None = None
        self._time_tracking_service: TimeTrackingService | None = None
        self._export_service: ExportService | None = None

    @property
    def llm_provider(self) -> OpenAIProvider:
        """Get LLM provider with retry wrapper."""
        if not self._llm_provider:
            provider = OpenAIProvider(self.config.llm)

            # Wrap generate_structured with retry strategy
            retry_strategy = RetryStrategy(self.config.retry)
            original_method = provider.generate_structured
            setattr(provider, "generate_structured", retry_strategy(original_method))

            self._llm_provider = provider

        return self._llm_provider

    @property
    def storage(self) -> JSONStorage:
        """Get storage backend."""
        if self._storage is None:
            if self.config.storage.backend == "json":
                self._storage = JSONStorage(self.config.storage)
            elif self.config.storage.backend == "sqlite":
                from ..infrastructure.storage.sqlite_storage import SQLiteStorage

                self._storage = SQLiteStorage(self.config.storage)
            else:
                raise ValueError(f"Unknown storage backend: {self.config.storage.backend}")

        return self._storage

    @property
    def cache(self) -> StorageCache:
        """Get cache layer."""
        if not self._cache:
            self._cache = StorageCache(ttl=self.config.storage.cache_ttl)
        return self._cache

    @property
    def state_machine(self) -> StateMachine:
        """Get state machine."""
        if not self._state_machine:
            self._state_machine = StateMachine()
        return self._state_machine

    @property
    def planning_service(self) -> PlanningService:
        """Get planning service."""
        if not self._planning_service:
            self._planning_service = PlanningService()
        return self._planning_service

    @property
    def agent_service(self) -> AgentService:
        """Get agent service."""
        if not self._agent_service:
            self._agent_service = AgentService(
                llm_provider=self.llm_provider,
                state_machine=self.state_machine,
                planning_service=self.planning_service,
            )
        return self._agent_service

    @property
    def input_handler(self) -> InputHandler:
        """Get input handler."""
        if not self._input_handler:
            self._input_handler = InputHandler(self.config.input)
        return self._input_handler

    @property
    def plan_formatter(self) -> PlanFormatter:
        """Get plan formatter."""
        if not self._plan_formatter:
            self._plan_formatter = PlanFormatter()
        return self._plan_formatter

    @property
    def session_formatter(self) -> SessionFormatter:
        """Get session formatter."""
        if not self._session_formatter:
            self._session_formatter = SessionFormatter()
        return self._session_formatter

    @property
    def progress_formatter(self) -> ProgressFormatter:
        """Get progress formatter."""
        if not self._progress_formatter:
            self._progress_formatter = ProgressFormatter()
        return self._progress_formatter

    @property
    def time_tracking_service(self) -> TimeTrackingService:
        """Get time tracking service."""
        if not self._time_tracking_service:
            self._time_tracking_service = TimeTrackingService()
        return self._time_tracking_service

    @property
    def export_service(self) -> ExportService:
        """Get export service."""
        if not self._export_service:
            self._export_service = ExportService(self.config.storage)
        return self._export_service
