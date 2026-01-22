"""Configuration management using Pydantic Settings."""

import logging
import yaml
from pathlib import Path
from typing import Optional
from dotenv import load_dotenv
from pydantic import Field, SecretStr, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

logger = logging.getLogger(__name__)


class LLMConfig(BaseSettings):
    """LLM provider configuration."""

    provider: str = "openai"
    model: str = "gpt-4o-mini"
    api_key: Optional[SecretStr] = None
    timeout: float = 60.0
    max_retries: int = 3
    temperature: float = 0.7
    max_tokens: Optional[int] = None

    model_config = SettingsConfigDict(env_prefix="OPENAI_")


class RetryConfig(BaseSettings):
    """Retry behavior configuration."""

    max_attempts: int = 3
    base_delay: float = 1.0
    max_delay: float = 60.0
    exponential_base: float = 2.0
    rate_limit_multiplier: float = 2.0


class StorageConfig(BaseSettings):
    """Storage configuration."""

    backend: str = "json"
    sessions_dir: Path = Path("sessions")
    profiles_dir: Path = Path("profiles")
    templates_dir: Path = Path("data/templates")
    plans_export_dir: Path = Path("data/plans")
    summaries_export_dir: Path = Path("data/summaries")
    cache_ttl: int = 300
    enable_compression: bool = False

    # SQLite settings (future)
    db_path: Optional[Path] = None
    connection_pool_size: int = 5

    @field_validator(
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
    def load(cls, env_file: Optional[Path] = None, yaml_file: Optional[Path] = None) -> "AppConfig":
        """
        Load configuration with priority: env vars > .env file > YAML > defaults.

        Follows 12-factor app and Pydantic Settings best practices.
        Environment variables are loaded explicitly for clarity and global availability.
        """
        # 1. Load .env file into environment (if exists)
        env_path = env_file or Path(".env")
        if env_path.exists():
            logger.debug(f"Loading environment from: {env_path.absolute()}")
            load_dotenv(env_path, override=False)  # Respect existing env vars
        else:
            logger.debug("No .env file found, using environment variables only")

        # 2. Load YAML config (optional layer)
        yaml_config = {}
        yaml_path = yaml_file or Path("config/default.yaml")
        if yaml_path.exists():
            logger.debug(f"Loading YAML config from: {yaml_path.absolute()}")
            with open(yaml_path) as f:
                yaml_config = yaml.safe_load(f) or {}

        # 3. Create config instance (Pydantic reads from os.environ)
        config = cls(**yaml_config)

        # 4. Validate critical configuration
        if not config.llm.api_key:
            raise ValueError(
                "OPENAI_API_KEY is required but not found.\n"
                "Please set it in your .env file or as an environment variable.\n"
                f"Searched locations: {env_path.absolute()}"
            )

        logger.info("Configuration loaded successfully")
        return config
