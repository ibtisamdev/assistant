"""Tests for RetryStrategy - exponential backoff retry logic."""

import pytest

from src.application.config import RetryConfig
from src.infrastructure.llm.retry import RetryStrategy


class TestRetryStrategyInitialization:
    """Test RetryStrategy initialization."""

    def test_init_with_config(self):
        """Test initialization with config."""
        config = RetryConfig(
            max_attempts=5,
            base_delay=1.0,
            max_delay=30.0,
            exponential_base=2.0,
            rate_limit_multiplier=3.0,
        )

        strategy = RetryStrategy(config)

        assert strategy.config.max_attempts == 5
        assert strategy.config.base_delay == 1.0


class TestIsRetryable:
    """Tests for is_retryable method."""

    @pytest.fixture
    def strategy(self):
        """Create retry strategy with test config."""
        return RetryStrategy(RetryConfig())

    def test_rate_limit_is_retryable(self, strategy):
        """Test that rate limit errors are retryable."""
        error = Exception("rate_limit_exceeded")

        assert strategy.is_retryable(error) is True

    def test_429_is_retryable(self, strategy):
        """Test that 429 errors are retryable."""
        error = Exception("HTTP 429 Too Many Requests")

        assert strategy.is_retryable(error) is True

    def test_timeout_is_retryable(self, strategy):
        """Test that timeout errors are retryable."""
        error = Exception("Request timeout")

        assert strategy.is_retryable(error) is True

    def test_connection_error_is_retryable(self, strategy):
        """Test that connection errors are retryable."""
        error = Exception("Connection refused")

        assert strategy.is_retryable(error) is True

    def test_500_error_is_retryable(self, strategy):
        """Test that 500 errors are retryable."""
        error = Exception("Internal server error 500")

        assert strategy.is_retryable(error) is True

    def test_502_error_is_retryable(self, strategy):
        """Test that 502 errors are retryable."""
        error = Exception("502 Bad Gateway")

        assert strategy.is_retryable(error) is True

    def test_503_error_is_retryable(self, strategy):
        """Test that 503 errors are retryable."""
        error = Exception("503 Service Unavailable")

        assert strategy.is_retryable(error) is True

    def test_authentication_error_not_retryable(self, strategy):
        """Test that authentication errors are not retryable."""
        error = Exception("Authentication failed")

        assert strategy.is_retryable(error) is False

    def test_invalid_api_key_not_retryable(self, strategy):
        """Test that invalid API key errors are not retryable."""
        error = Exception("invalid_api_key")

        assert strategy.is_retryable(error) is False

    def test_unauthorized_not_retryable(self, strategy):
        """Test that unauthorized errors are not retryable."""
        error = Exception("Unauthorized: 401")

        assert strategy.is_retryable(error) is False

    def test_permission_denied_not_retryable(self, strategy):
        """Test that permission errors are not retryable."""
        error = Exception("Permission denied")

        assert strategy.is_retryable(error) is False

    def test_invalid_request_not_retryable(self, strategy):
        """Test that invalid request errors are not retryable."""
        error = Exception("invalid_request_error")

        assert strategy.is_retryable(error) is False

    def test_model_not_found_not_retryable(self, strategy):
        """Test that model not found errors are not retryable."""
        error = Exception("model_not_found: gpt-5")

        assert strategy.is_retryable(error) is False


class TestCalculateWaitTime:
    """Tests for calculate_wait_time method."""

    @pytest.fixture
    def strategy(self):
        """Create retry strategy with known config."""
        config = RetryConfig(
            base_delay=1.0,
            max_delay=60.0,
            exponential_base=2.0,
            rate_limit_multiplier=2.0,
        )
        return RetryStrategy(config)

    def test_first_attempt_wait_time(self, strategy):
        """Test wait time for first retry attempt."""
        error = Exception("timeout")

        wait = strategy.calculate_wait_time(0, error)

        # base_delay * (2^0) = 1.0 * 1 = 1.0
        assert wait == 1.0

    def test_second_attempt_wait_time(self, strategy):
        """Test wait time for second retry attempt."""
        error = Exception("timeout")

        wait = strategy.calculate_wait_time(1, error)

        # base_delay * (2^1) = 1.0 * 2 = 2.0
        assert wait == 2.0

    def test_third_attempt_wait_time(self, strategy):
        """Test wait time for third retry attempt."""
        error = Exception("timeout")

        wait = strategy.calculate_wait_time(2, error)

        # base_delay * (2^2) = 1.0 * 4 = 4.0
        assert wait == 4.0

    def test_rate_limit_multiplier_applied(self, strategy):
        """Test that rate limit errors get extra wait time."""
        error = Exception("rate_limit_exceeded")

        wait = strategy.calculate_wait_time(0, error)

        # base_delay * (2^0) * rate_limit_multiplier = 1.0 * 1 * 2.0 = 2.0
        assert wait == 2.0

    def test_max_delay_cap(self, strategy):
        """Test that wait time is capped at max_delay."""
        error = Exception("timeout")

        # Large attempt number
        wait = strategy.calculate_wait_time(10, error)

        # Should be capped at max_delay (60.0)
        assert wait == 60.0


class TestRetryDecorator:
    """Tests for the retry decorator functionality."""

    @pytest.mark.asyncio
    async def test_successful_call_no_retry(self):
        """Test that successful calls don't retry."""
        config = RetryConfig(max_attempts=3, base_delay=0.01)
        strategy = RetryStrategy(config)
        call_count = 0

        @strategy
        async def success_func():
            nonlocal call_count
            call_count += 1
            return "success"

        result = await success_func()

        assert result == "success"
        assert call_count == 1

    @pytest.mark.asyncio
    async def test_retries_on_transient_error(self):
        """Test that transient errors trigger retries."""
        config = RetryConfig(max_attempts=3, base_delay=0.01)
        strategy = RetryStrategy(config)
        call_count = 0

        @strategy
        async def fail_then_succeed():
            nonlocal call_count
            call_count += 1
            if call_count < 3:
                raise Exception("timeout error")
            return "success"

        result = await fail_then_succeed()

        assert result == "success"
        assert call_count == 3

    @pytest.mark.asyncio
    async def test_raises_after_max_attempts(self):
        """Test that error is raised after max attempts."""
        config = RetryConfig(max_attempts=3, base_delay=0.01)
        strategy = RetryStrategy(config)
        call_count = 0

        @strategy
        async def always_fail():
            nonlocal call_count
            call_count += 1
            raise Exception("timeout error")

        with pytest.raises(Exception) as exc_info:
            await always_fail()

        assert "timeout" in str(exc_info.value)
        assert call_count == 3

    @pytest.mark.asyncio
    async def test_no_retry_on_permanent_error(self):
        """Test that permanent errors don't retry."""
        config = RetryConfig(max_attempts=3, base_delay=0.01)
        strategy = RetryStrategy(config)
        call_count = 0

        @strategy
        async def auth_fail():
            nonlocal call_count
            call_count += 1
            raise Exception("authentication failed")

        with pytest.raises(Exception) as exc_info:
            await auth_fail()

        assert "authentication" in str(exc_info.value)
        assert call_count == 1  # No retries for auth errors

    @pytest.mark.asyncio
    async def test_preserves_function_return_type(self):
        """Test that decorator preserves return type."""
        config = RetryConfig(max_attempts=3, base_delay=0.01)
        strategy = RetryStrategy(config)

        @strategy
        async def return_dict():
            return {"key": "value", "number": 42}

        result = await return_dict()

        assert isinstance(result, dict)
        assert result["key"] == "value"
        assert result["number"] == 42
