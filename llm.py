import os
import time
import logging
from typing import Optional

from openai import OpenAI

from models import Session

# Configure logging
logger = logging.getLogger(__name__)


class LLMError(Exception):
    """Custom exception for LLM-related errors"""

    pass


class LLMClient:
    def __init__(self):
        """
        Initialize the LLM client with API key validation.

        Raises:
            ValueError: If OPENAI_API_KEY is missing or invalid
        """
        # Validate API key before initializing client
        api_key = os.getenv("OPENAI_API_KEY")

        if not api_key:
            raise ValueError(
                "OPENAI_API_KEY not found in environment.\n"
                "Please add it to your .env file:\n"
                "  OPENAI_API_KEY=your_key_here"
            )

        if not api_key.startswith("sk-"):
            raise ValueError(
                "OPENAI_API_KEY appears to be invalid (should start with 'sk-').\n"
                "Please check your .env file."
            )

        self.client = OpenAI(api_key=api_key)
        self.model = "gpt-4o-mini"
        logger.info("LLM client initialized successfully")

    def call(self, history: list, max_retries: int = 3) -> Session:
        """
        Call the LLM with retry logic and comprehensive error handling.

        Args:
            history: Conversation history in OpenAI format
            max_retries: Maximum number of retry attempts

        Returns:
            Parsed Session object

        Raises:
            LLMError: If all retries fail
        """
        last_error: Optional[Exception] = None

        for attempt in range(max_retries):
            try:
                response = self.client.responses.parse(
                    model=self.model,
                    input=history,
                    text_format=Session,
                    timeout=60.0,  # 60 second timeout
                )

                # Validate response structure before accessing
                if not response.output or len(response.output) == 0:
                    raise ValueError("Empty response from API")

                if (
                    not response.output[0].content
                    or len(response.output[0].content) == 0
                ):
                    raise ValueError("Empty content in API response")

                parsed = response.output[0].content[0].parsed
                if parsed is None:
                    raise ValueError("Parsed content is None")

                return parsed

            except Exception as e:
                last_error = e
                error_type = type(e).__name__
                error_msg = str(e).lower()

                logger.error(
                    f"LLM call failed (attempt {attempt + 1}/{max_retries}): "
                    f"{error_type} - {str(e)}"
                )

                # Check if we should retry
                is_retryable = self._is_retryable_error(error_msg)

                if not is_retryable:
                    # Non-retryable error (e.g., authentication, invalid request)
                    logger.error(f"Non-retryable error: {error_type}")
                    break

                # Calculate wait time with exponential backoff
                wait_time = self._calculate_wait_time(error_msg, attempt)

                if attempt < max_retries - 1:
                    logger.info(f"Retrying in {wait_time}s...")
                    time.sleep(wait_time)

        # All retries failed
        raise LLMError(
            f"Failed to get response from OpenAI after {max_retries} attempts. "
            f"Last error: {str(last_error)}"
        )

    def _is_retryable_error(self, error_msg: str) -> bool:
        """
        Determine if an error is retryable.

        Args:
            error_msg: Lowercase error message

        Returns:
            True if error is retryable, False otherwise
        """
        # Non-retryable errors
        non_retryable_keywords = [
            "authentication",
            "invalid_api_key",
            "invalid api key",
            "unauthorized",
            "permission",
            "invalid_request",
            "model_not_found",
        ]

        for keyword in non_retryable_keywords:
            if keyword in error_msg:
                return False

        # Retryable errors
        retryable_keywords = [
            "rate_limit",
            "rate limit",
            "429",
            "timeout",
            "timed out",
            "connection",
            "network",
            "dns",
            "server_error",
            "500",
            "502",
            "503",
            "504",
            "overloaded",
            "capacity",
        ]

        for keyword in retryable_keywords:
            if keyword in error_msg:
                return True

        # Default: retry unknown errors
        return True

    def _calculate_wait_time(self, error_msg: str, attempt: int) -> float:
        """
        Calculate wait time based on error type and attempt number.

        Args:
            error_msg: Lowercase error message
            attempt: Current attempt number (0-indexed)

        Returns:
            Wait time in seconds
        """
        base_wait = 2**attempt  # Exponential backoff: 1s, 2s, 4s

        # Rate limit errors get longer wait times
        if "rate_limit" in error_msg or "rate limit" in error_msg or "429" in error_msg:
            return base_wait * 2  # 2s, 4s, 8s

        # Timeout errors - shorter wait
        if "timeout" in error_msg or "timed out" in error_msg:
            return 1.0

        return base_wait
