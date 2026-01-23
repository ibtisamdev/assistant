"""Tests for OpenAIProvider - async OpenAI implementation."""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from pydantic import SecretStr

from src.application.config import LLMConfig
from src.domain.exceptions import LLMError
from src.domain.models.conversation import Message, MessageRole
from src.domain.models.session import Session
from src.domain.models.state import State
from src.infrastructure.llm.openai_provider import OpenAIProvider


class TestOpenAIProviderInitialization:
    """Test OpenAIProvider initialization."""

    def test_init_requires_api_key(self):
        """Test that initialization requires an API key."""
        config = LLMConfig(api_key=None)

        with pytest.raises(ValueError) as exc_info:
            OpenAIProvider(config)

        assert "API key is required" in str(exc_info.value)

    def test_init_validates_api_key_format(self):
        """Test that API key must start with sk-."""
        config = LLMConfig(api_key=SecretStr("invalid-key"))

        with pytest.raises(ValueError) as exc_info:
            OpenAIProvider(config)

        assert "must start with 'sk-'" in str(exc_info.value)

    @patch("src.infrastructure.llm.openai_provider.AsyncOpenAI")
    def test_init_with_valid_key(self, mock_client):
        """Test successful initialization with valid key."""
        config = LLMConfig(
            api_key=SecretStr("sk-test-key-12345"),
            model="gpt-4o-mini",
        )

        provider = OpenAIProvider(config)

        assert provider.config.model == "gpt-4o-mini"
        mock_client.assert_called_once()


class TestGenerate:
    """Tests for generate method (unstructured response)."""

    @pytest.fixture
    def provider(self):
        """Create provider with mocked client."""
        with patch("src.infrastructure.llm.openai_provider.AsyncOpenAI"):
            config = LLMConfig(api_key=SecretStr("sk-test-key-12345"))
            provider = OpenAIProvider(config)
            provider.client = AsyncMock()
            return provider

    @pytest.mark.asyncio
    async def test_generate_returns_content(self, provider):
        """Test that generate returns content from response."""
        # Mock the response
        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].message.content = "Hello, world!"
        provider.client.chat.completions.create = AsyncMock(return_value=mock_response)

        messages = [Message(role=MessageRole.user, content="Say hello")]

        result = await provider.generate(messages)

        assert result == "Hello, world!"

    @pytest.mark.asyncio
    async def test_generate_with_empty_response(self, provider):
        """Test handling of empty response."""
        mock_response = MagicMock()
        mock_response.choices = []
        provider.client.chat.completions.create = AsyncMock(return_value=mock_response)

        messages = [Message(role=MessageRole.user, content="Say hello")]

        with pytest.raises(LLMError) as exc_info:
            await provider.generate(messages)

        assert "No response" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_generate_handles_api_error(self, provider):
        """Test handling of API errors."""
        provider.client.chat.completions.create = AsyncMock(side_effect=Exception("API error"))

        messages = [Message(role=MessageRole.user, content="Say hello")]

        with pytest.raises(LLMError) as exc_info:
            await provider.generate(messages)

        assert "Failed to generate" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_generate_formats_messages_correctly(self, provider):
        """Test that messages are formatted correctly for OpenAI."""
        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].message.content = "Response"
        provider.client.chat.completions.create = AsyncMock(return_value=mock_response)

        messages = [
            Message(role=MessageRole.system, content="You are helpful"),
            Message(role=MessageRole.user, content="Hello"),
        ]

        await provider.generate(messages)

        # Verify the call was made with correct format
        call_args = provider.client.chat.completions.create.call_args
        sent_messages = call_args.kwargs["messages"]

        assert sent_messages[0]["role"] == "system"
        assert sent_messages[0]["content"] == "You are helpful"
        assert sent_messages[1]["role"] == "user"
        assert sent_messages[1]["content"] == "Hello"


class TestGenerateStructured:
    """Tests for generate_structured method."""

    @pytest.fixture
    def provider(self):
        """Create provider with mocked client."""
        with patch("src.infrastructure.llm.openai_provider.AsyncOpenAI"):
            config = LLMConfig(api_key=SecretStr("sk-test-key-12345"))
            provider = OpenAIProvider(config)
            provider.client = AsyncMock()
            return provider

    @pytest.mark.asyncio
    async def test_generate_structured_returns_parsed_object(self, provider):
        """Test that generate_structured returns a parsed object."""
        from tests.conftest import PlanFactory

        # Mock the parsed response
        mock_parsed = Session(
            state=State.feedback,
            questions=[],
            plan=PlanFactory.create(),
        )
        mock_content = MagicMock()
        mock_content.parsed = mock_parsed
        mock_output = MagicMock()
        mock_output.content = [mock_content]
        mock_response = MagicMock()
        mock_response.output = [mock_output]

        provider.client.responses.parse = AsyncMock(return_value=mock_response)

        messages = [Message(role=MessageRole.user, content="Plan my day")]

        result = await provider.generate_structured(messages, Session)

        assert result.state == State.feedback

    @pytest.mark.asyncio
    async def test_generate_structured_empty_response(self, provider):
        """Test handling of empty structured response."""
        mock_response = MagicMock()
        mock_response.output = []

        provider.client.responses.parse = AsyncMock(return_value=mock_response)

        messages = [Message(role=MessageRole.user, content="Plan my day")]

        with pytest.raises(LLMError) as exc_info:
            await provider.generate_structured(messages, Session)

        assert "Empty response" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_generate_structured_parse_failure(self, provider):
        """Test handling of parse failure."""
        mock_content = MagicMock()
        mock_content.parsed = None
        mock_output = MagicMock()
        mock_output.content = [mock_content]
        mock_response = MagicMock()
        mock_response.output = [mock_output]

        provider.client.responses.parse = AsyncMock(return_value=mock_response)

        messages = [Message(role=MessageRole.user, content="Plan my day")]

        with pytest.raises(LLMError) as exc_info:
            await provider.generate_structured(messages, Session)

        assert "Failed to parse" in str(exc_info.value)


class TestStreamGenerate:
    """Tests for stream_generate method."""

    @pytest.fixture
    def provider(self):
        """Create provider with mocked client."""
        with patch("src.infrastructure.llm.openai_provider.AsyncOpenAI"):
            config = LLMConfig(api_key=SecretStr("sk-test-key-12345"))
            provider = OpenAIProvider(config)
            provider.client = AsyncMock()
            return provider

    @pytest.mark.asyncio
    async def test_stream_yields_chunks(self, provider):
        """Test that stream_generate yields content chunks."""

        # Create mock async iterator
        async def mock_stream():
            chunks = ["Hello", " ", "world", "!"]
            for chunk_text in chunks:
                mock_chunk = MagicMock()
                mock_chunk.choices = [MagicMock()]
                mock_chunk.choices[0].delta.content = chunk_text
                yield mock_chunk

        provider.client.chat.completions.create = AsyncMock(return_value=mock_stream())

        messages = [Message(role=MessageRole.user, content="Say hello")]

        chunks = []
        async for chunk in provider.stream_generate(messages):
            chunks.append(chunk)

        assert chunks == ["Hello", " ", "world", "!"]


class TestConfigPassthrough:
    """Tests for config values being passed correctly."""

    @patch("src.infrastructure.llm.openai_provider.AsyncOpenAI")
    def test_model_config_passed(self, mock_client):
        """Test that model config is passed to client."""
        config = LLMConfig(
            api_key=SecretStr("sk-test-key-12345"),
            model="gpt-4o",
            timeout=45.0,
        )

        provider = OpenAIProvider(config)

        assert provider.config.model == "gpt-4o"
        assert provider.config.timeout == 45.0

    @patch("src.infrastructure.llm.openai_provider.AsyncOpenAI")
    def test_temperature_used_in_calls(self, mock_client):
        """Test that temperature is used in API calls."""
        config = LLMConfig(
            api_key=SecretStr("sk-test-key-12345"),
            temperature=0.5,
        )

        provider = OpenAIProvider(config)

        assert provider.config.temperature == 0.5
