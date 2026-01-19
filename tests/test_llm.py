"""
Tests for llm.py - LLM client error handling.
"""

import pytest
from unittest.mock import Mock, patch, MagicMock

from llm import LLMClient, LLMError
from models import Session, State, Plan, ScheduleItem


class TestAPIKeyValidation:
    """Test API key validation on initialization"""

    def test_missing_api_key_raises_error(self, monkeypatch):
        """Test that missing API key raises clear ValueError"""
        monkeypatch.delenv("OPENAI_API_KEY", raising=False)

        with pytest.raises(ValueError) as exc_info:
            LLMClient()

        assert "OPENAI_API_KEY not found" in str(exc_info.value)

    def test_empty_api_key_raises_error(self, monkeypatch):
        """Test that empty API key raises error"""
        monkeypatch.setenv("OPENAI_API_KEY", "")

        with pytest.raises(ValueError) as exc_info:
            LLMClient()

        assert "OPENAI_API_KEY not found" in str(exc_info.value)

    def test_invalid_api_key_format_raises_error(self, monkeypatch):
        """Test that API key not starting with sk- raises error"""
        monkeypatch.setenv("OPENAI_API_KEY", "invalid-key-format")

        with pytest.raises(ValueError) as exc_info:
            LLMClient()

        assert "invalid" in str(exc_info.value).lower()

    @patch("llm.OpenAI")
    def test_valid_api_key_initializes_client(self, mock_openai, monkeypatch):
        """Test that valid API key initializes client successfully"""
        monkeypatch.setenv("OPENAI_API_KEY", "sk-valid-test-key")

        client = LLMClient()

        assert client.model == "gpt-4o-mini"
        mock_openai.assert_called_once()


class TestRetryLogic:
    """Test retry logic for API calls"""

    @patch("llm.OpenAI")
    @patch("llm.time.sleep")  # Mock sleep to speed up tests
    def test_retry_on_network_error(self, mock_sleep, mock_openai, monkeypatch):
        """Test that network errors trigger retry"""
        monkeypatch.setenv("OPENAI_API_KEY", "sk-test-key")

        client = LLMClient()

        # Create a mock successful response
        mock_session = Session(
            state=State.done,
            plan=Plan(
                schedule=[ScheduleItem(time="09:00-10:00", task="Test")],
                priorities=["Test"],
                notes="Test",
            ),
            questions=[],
        )

        mock_parsed = Mock()
        mock_parsed.parsed = mock_session

        mock_content = Mock()
        mock_content.content = [mock_parsed]

        mock_response = Mock()
        mock_response.output = [mock_content]

        # First call fails with network error, second succeeds
        client.client.responses.parse = Mock(
            side_effect=[ConnectionError("Network error"), mock_response]
        )

        result = client.call([{"role": "user", "content": "test"}])

        assert result.state == State.done
        assert client.client.responses.parse.call_count == 2

    @patch("llm.OpenAI")
    @patch("llm.time.sleep")
    def test_max_retries_exceeded_raises_llm_error(
        self, mock_sleep, mock_openai, monkeypatch
    ):
        """Test that exceeding max retries raises LLMError"""
        monkeypatch.setenv("OPENAI_API_KEY", "sk-test-key")

        client = LLMClient()

        # All calls fail
        client.client.responses.parse = Mock(
            side_effect=ConnectionError("Persistent network error")
        )

        with pytest.raises(LLMError) as exc_info:
            client.call([{"role": "user", "content": "test"}], max_retries=2)

        assert "Failed to get response" in str(exc_info.value)
        assert client.client.responses.parse.call_count == 2

    @patch("llm.OpenAI")
    def test_non_retryable_error_fails_immediately(self, mock_openai, monkeypatch):
        """Test that authentication errors don't retry"""
        monkeypatch.setenv("OPENAI_API_KEY", "sk-test-key")

        client = LLMClient()

        # Auth error should not retry
        client.client.responses.parse = Mock(
            side_effect=Exception("Invalid API key - authentication failed")
        )

        with pytest.raises(LLMError):
            client.call([{"role": "user", "content": "test"}], max_retries=3)

        # Should only try once for auth errors
        assert client.client.responses.parse.call_count == 1


class TestResponseValidation:
    """Test validation of API responses"""

    @patch("llm.OpenAI")
    def test_empty_response_raises_error(self, mock_openai, monkeypatch):
        """Test that empty response triggers retry/error"""
        monkeypatch.setenv("OPENAI_API_KEY", "sk-test-key")

        client = LLMClient()

        # Empty output
        mock_response = Mock()
        mock_response.output = []

        client.client.responses.parse = Mock(return_value=mock_response)

        with pytest.raises(LLMError):
            client.call([{"role": "user", "content": "test"}], max_retries=1)

    @patch("llm.OpenAI")
    def test_none_parsed_content_raises_error(self, mock_openai, monkeypatch):
        """Test that None parsed content raises error"""
        monkeypatch.setenv("OPENAI_API_KEY", "sk-test-key")

        client = LLMClient()

        # Parsed is None
        mock_parsed = Mock()
        mock_parsed.parsed = None

        mock_content = Mock()
        mock_content.content = [mock_parsed]

        mock_response = Mock()
        mock_response.output = [mock_content]

        client.client.responses.parse = Mock(return_value=mock_response)

        with pytest.raises(LLMError):
            client.call([{"role": "user", "content": "test"}], max_retries=1)


class TestErrorClassification:
    """Test error classification for retry decisions"""

    @patch("llm.OpenAI")
    def test_rate_limit_is_retryable(self, mock_openai, monkeypatch):
        """Test that rate limit errors are identified as retryable"""
        monkeypatch.setenv("OPENAI_API_KEY", "sk-test-key")

        client = LLMClient()

        assert client._is_retryable_error("rate_limit exceeded") is True
        assert client._is_retryable_error("error 429 too many requests") is True

    @patch("llm.OpenAI")
    def test_timeout_is_retryable(self, mock_openai, monkeypatch):
        """Test that timeout errors are identified as retryable"""
        monkeypatch.setenv("OPENAI_API_KEY", "sk-test-key")

        client = LLMClient()

        assert client._is_retryable_error("request timed out") is True
        assert client._is_retryable_error("timeout error occurred") is True

    @patch("llm.OpenAI")
    def test_auth_error_is_not_retryable(self, mock_openai, monkeypatch):
        """Test that auth errors are not retryable"""
        monkeypatch.setenv("OPENAI_API_KEY", "sk-test-key")

        client = LLMClient()

        assert client._is_retryable_error("authentication failed") is False
        assert client._is_retryable_error("invalid_api_key") is False
        assert client._is_retryable_error("unauthorized access") is False


class TestWaitTimeCalculation:
    """Test exponential backoff wait time calculation"""

    @patch("llm.OpenAI")
    def test_exponential_backoff(self, mock_openai, monkeypatch):
        """Test that wait times increase exponentially"""
        monkeypatch.setenv("OPENAI_API_KEY", "sk-test-key")

        client = LLMClient()

        wait_0 = client._calculate_wait_time("generic error", 0)
        wait_1 = client._calculate_wait_time("generic error", 1)
        wait_2 = client._calculate_wait_time("generic error", 2)

        assert wait_1 > wait_0
        assert wait_2 > wait_1

    @patch("llm.OpenAI")
    def test_rate_limit_gets_longer_wait(self, mock_openai, monkeypatch):
        """Test that rate limit errors get longer wait times"""
        monkeypatch.setenv("OPENAI_API_KEY", "sk-test-key")

        client = LLMClient()

        generic_wait = client._calculate_wait_time("generic error", 1)
        rate_limit_wait = client._calculate_wait_time("rate_limit error", 1)

        assert rate_limit_wait > generic_wait
