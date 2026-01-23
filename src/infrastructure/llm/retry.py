"""Retry logic with exponential backoff."""

import asyncio
import logging
from collections.abc import Callable
from functools import wraps
from typing import TypeVar

from ...application.config import RetryConfig

logger = logging.getLogger(__name__)
T = TypeVar("T")


class RetryStrategy:
    """Retry logic with exponential backoff."""

    def __init__(self, config: RetryConfig):
        self.config = config

    def is_retryable(self, error: Exception) -> bool:
        """Determine if error should trigger retry."""
        error_msg = str(error).lower()

        # Non-retryable
        non_retryable = [
            "authentication",
            "invalid_api_key",
            "unauthorized",
            "permission",
            "invalid_request",
            "model_not_found",
        ]
        for keyword in non_retryable:
            if keyword in error_msg:
                return False

        # Retryable
        retryable = [
            "rate_limit",
            "429",
            "timeout",
            "connection",
            "network",
            "500",
            "502",
            "503",
            "504",
            "overloaded",
        ]
        return any(keyword in error_msg for keyword in retryable)

    def calculate_wait_time(self, attempt: int, error: Exception) -> float:
        """Calculate backoff time."""
        error_msg = str(error).lower()
        base = self.config.base_delay * (self.config.exponential_base**attempt)

        if "rate_limit" in error_msg or "429" in error_msg:
            base *= self.config.rate_limit_multiplier

        return min(base, self.config.max_delay)

    def __call__(self, func: Callable[..., T]) -> Callable[..., T]:
        """Decorator for async retry logic."""

        @wraps(func)
        async def wrapper(*args, **kwargs) -> T:
            last_error = None

            for attempt in range(self.config.max_attempts):
                try:
                    return await func(*args, **kwargs)
                except Exception as e:
                    last_error = e

                    if not self.is_retryable(e):
                        logger.error(f"Non-retryable error: {type(e).__name__}")
                        raise

                    if attempt < self.config.max_attempts - 1:
                        wait_time = self.calculate_wait_time(attempt, e)
                        logger.warning(
                            f"Attempt {attempt + 1} failed: {e}. Retrying in {wait_time}s..."
                        )
                        await asyncio.sleep(wait_time)

            raise last_error

        return wrapper
