"""Configuration management using Pydantic Settings."""

import logging
import os
from pathlib import Path
from typing import Any

import yaml
from dotenv import load_dotenv
from pydantic import Field, SecretStr, field_validator, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

from ..domain.exceptions import SetupRequired

logger = logging.getLogger(__name__)

# Application name for directory paths
APP_NAME = "planmyday"


def get_data_dir() -> Path:
    """
    Get XDG data directory for planmyday.

    Linux/macOS: ~/.local/share/planmyday/
    """
    base = Path(os.environ.get("XDG_DATA_HOME", Path.home() / ".local" / "share"))
    return base / APP_NAME


def get_config_dir() -> Path:
    """
    Get XDG config directory for planmyday.

    Linux/macOS: ~/.config/planmyday/
    """
    base = Path(os.environ.get("XDG_CONFIG_HOME", Path.home() / ".config"))
    return base / APP_NAME


class LLMConfig(BaseSettings):
    """LLM provider configuration."""

    provider: str = "openai"
    model: str = "gpt-4o-mini"
    api_key: SecretStr | None = None
    timeout: float = 60.0
    max_retries: int = 3
    temperature: float = 0.7
    max_tokens: int | None = None

    model_config = SettingsConfigDict(env_prefix="OPENAI_")


class RetryConfig(BaseSettings):
    """Retry behavior configuration."""

    max_attempts: int = 3
    base_delay: float = 1.0
    max_delay: float = 60.0
    exponential_base: float = 2.0
    rate_limit_multiplier: float = 2.0


class StorageConfig(BaseSettings):
    """Storage configuration with XDG Base Directory support."""

    backend: str = "json"

    # Base directories (XDG spec) - set via model_validator
    base_data_dir: Path = Field(default_factory=get_data_dir)
    base_config_dir: Path = Field(default_factory=get_config_dir)

    # Storage paths - will be set in model_validator if not provided
    # Using Path with sentinel default that will be replaced
    sessions_dir: Path = Field(default=Path(""))
    profiles_dir: Path = Field(default=Path(""))
    templates_dir: Path = Field(default=Path(""))
    plans_export_dir: Path = Field(default=Path(""))
    summaries_export_dir: Path = Field(default=Path(""))

    # Cache settings
    cache_ttl: int = 300
    enable_compression: bool = False

    # SQLite settings (future)
    db_path: Path | None = None
    connection_pool_size: int = 5

    # Local mode flag (use current directory instead of global)
    use_local: bool = False

    @field_validator(
        "base_data_dir",
        "base_config_dir",
        "sessions_dir",
        "profiles_dir",
        "templates_dir",
        "plans_export_dir",
        "summaries_export_dir",
        mode="before",
    )
    @classmethod
    def convert_to_path(cls, v):
        """Convert string to Path."""
        if isinstance(v, str):
            return Path(v)
        return v

    @model_validator(mode="after")
    def set_default_paths(self) -> "StorageConfig":
        """Set default paths based on XDG spec or local mode."""
        if self.use_local:
            # Development mode: use current directory
            base = Path(".")
            if self.sessions_dir == Path(""):
                self.sessions_dir = base / "sessions"
            if self.profiles_dir == Path(""):
                self.profiles_dir = base / "profiles"
            if self.templates_dir == Path(""):
                self.templates_dir = base / "data" / "templates"
            if self.plans_export_dir == Path(""):
                self.plans_export_dir = base / "data" / "plans"
            if self.summaries_export_dir == Path(""):
                self.summaries_export_dir = base / "data" / "summaries"
        else:
            # Production mode: use XDG directories
            if self.sessions_dir == Path(""):
                self.sessions_dir = self.base_data_dir / "sessions"
            if self.profiles_dir == Path(""):
                self.profiles_dir = self.base_data_dir / "profiles"
            if self.templates_dir == Path(""):
                self.templates_dir = self.base_data_dir / "templates"
            if self.plans_export_dir == Path(""):
                self.plans_export_dir = self.base_data_dir / "exports" / "plans"
            if self.summaries_export_dir == Path(""):
                self.summaries_export_dir = self.base_data_dir / "exports" / "summaries"

        return self


class InputConfig(BaseSettings):
    """User input validation."""

    max_goal_length: int = 1000
    max_feedback_length: int = 1000
    max_answer_length: int = 500
    allow_empty_feedback: bool = False


class SessionConfig(BaseSettings):
    """Session management."""

    auto_save: bool = True
    save_debounce_ms: int = 500
    max_conversation_messages: int = 100
    cleanup_temp_files_older_than_hours: int = 1


class AppConfig(BaseSettings):
    """Application configuration - root config object."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_nested_delimiter="__",
        case_sensitive=False,
        extra="ignore",  # Ignore extra fields from environment
    )

    # Environment
    environment: str = Field(default="development")
    debug: bool = Field(default=False)
    log_level: str = Field(default="INFO")

    # Sub-configurations
    llm: LLMConfig = Field(default_factory=LLMConfig)
    retry: RetryConfig = Field(default_factory=RetryConfig)
    storage: StorageConfig = Field(default_factory=StorageConfig)
    input: InputConfig = Field(default_factory=InputConfig)
    session: SessionConfig = Field(default_factory=SessionConfig)

    # Feature flags
    enable_multi_agent: bool = False
    enable_export: bool = True
    enable_calendar_sync: bool = False

    @classmethod
    def load(
        cls,
        env_file: Path | None = None,
        yaml_file: Path | None = None,
        use_local: bool = False,
    ) -> "AppConfig":
        """
        Load configuration with priority: env vars > .env file > global config > defaults.

        Follows 12-factor app and Pydantic Settings best practices.
        Environment variables are loaded explicitly for clarity and global availability.

        Args:
            env_file: Optional path to .env file
            yaml_file: Optional path to YAML config file
            use_local: If True, use current directory for data (dev mode)
        """
        # Determine config locations
        global_config_dir = get_config_dir()
        global_env_file = global_config_dir / ".env"
        global_yaml_file = global_config_dir / "config.yaml"

        # 1. Load .env files (local takes precedence over global)
        # First load global config .env
        if global_env_file.exists():
            logger.debug(f"Loading global environment from: {global_env_file}")
            load_dotenv(global_env_file, override=False)

        # Then load local .env (or custom path)
        local_env_path = env_file or Path(".env")
        if local_env_path.exists():
            logger.debug(f"Loading local environment from: {local_env_path.absolute()}")
            load_dotenv(local_env_path, override=True)  # Local overrides global

        # 2. Load YAML config (optional layer)
        yaml_path = yaml_file or global_yaml_file
        yaml_config: dict[str, Any] = {}
        if yaml_path.exists():
            logger.debug(f"Loading YAML config from: {yaml_path}")
            with open(yaml_path) as f:
                yaml_config = yaml.safe_load(f) or {}

        # 3. Create config instance
        # Set use_local in storage config
        if use_local:
            if "storage" not in yaml_config:
                yaml_config["storage"] = {}
            yaml_config["storage"]["use_local"] = True

        config = cls(**yaml_config) if yaml_config else cls()

        # Override use_local if passed explicitly
        if use_local:
            config.storage.use_local = True
            # Re-run path validation
            config.storage = config.storage.model_copy()

        # 4. Validate critical configuration
        if not config.llm.api_key:
            # Check if setup has been run (global config exists)
            if not global_config_dir.exists() or not any(global_config_dir.iterdir()):
                raise SetupRequired(
                    "planmyday is not configured yet.\n\n"
                    "Run 'pday setup' to configure your API key and get started.\n"
                    "Or set OPENAI_API_KEY environment variable."
                )
            else:
                raise ValueError(
                    "OPENAI_API_KEY is required but not found.\n\n"
                    "Set it via:\n"
                    f"  1. {global_env_file}\n"
                    "  2. Environment variable: export OPENAI_API_KEY=sk-...\n"
                    "  3. Local .env file"
                )

        logger.info("Configuration loaded successfully")
        return config
