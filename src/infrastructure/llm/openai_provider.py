"""Async OpenAI implementation."""

import logging
from typing import Type, TypeVar, List
from openai import AsyncOpenAI
from ...domain.models.conversation import Message
from ...domain.exceptions import LLMError
from ...application.config import LLMConfig

logger = logging.getLogger(__name__)
T = TypeVar("T")


class OpenAIProvider:
    """Async OpenAI implementation."""

    def __init__(self, config: LLMConfig):
        self.config = config

        # Validate API key
        if not config.api_key:
            raise ValueError(
                "OpenAI API key is required but not configured.\n\n"
                "To fix this:\n"
                "1. Create a .env file in the project root\n"
                "2. Add: OPENAI_API_KEY=your_key_here\n"
                "3. Or set the OPENAI_API_KEY environment variable\n\n"
                "See .env.example for reference."
            )

        api_key_str = config.api_key.get_secret_value()
        if not api_key_str.startswith("sk-"):
            raise ValueError(
                "Invalid OpenAI API key format.\n\n"
                "OpenAI API keys must start with 'sk-'\n"
                "Get a valid key from: https://platform.openai.com/api-keys"
            )

        self.client = AsyncOpenAI(
            api_key=api_key_str,
            timeout=config.timeout,
        )

        logger.info(f"OpenAI provider initialized with model: {config.model}")

    async def generate(self, messages: List[Message]) -> str:
        """Generate unstructured response."""
        try:
            response = await self.client.chat.completions.create(
                model=self.config.model,
                messages=[{"role": m.role.value, "content": m.content} for m in messages],
                temperature=self.config.temperature,
                max_tokens=self.config.max_tokens,
            )

            if not response.choices:
                raise LLMError("No response from OpenAI")

            return response.choices[0].message.content or ""

        except Exception as e:
            logger.error(f"OpenAI generation failed: {e}")
            raise LLMError(f"Failed to generate response: {e}") from e

    async def generate_structured(self, messages: List[Message], schema: Type[T]) -> T:
        """Generate structured response using OpenAI's responses.parse."""
        try:
            # Convert messages to OpenAI format
            openai_messages = [{"role": m.role.value, "content": m.content} for m in messages]

            response = await self.client.responses.parse(
                model=self.config.model,
                input=openai_messages,
                text_format=schema,
                timeout=self.config.timeout,
            )

            # Validate response structure
            if not response.output or len(response.output) == 0:
                raise LLMError("Empty response from OpenAI")

            if not response.output[0].content or len(response.output[0].content) == 0:
                raise LLMError("Empty content in OpenAI response")

            parsed = response.output[0].content[0].parsed
            if parsed is None:
                raise LLMError("Failed to parse structured output")

            return parsed

        except LLMError:
            raise
        except Exception as e:
            logger.error(f"OpenAI structured generation failed: {e}")
            raise LLMError(f"Failed to generate structured response: {e}") from e

    async def stream_generate(self, messages: List[Message]):
        """Stream response (for future real-time feedback)."""
        try:
            stream = await self.client.chat.completions.create(
                model=self.config.model,
                messages=[{"role": m.role.value, "content": m.content} for m in messages],
                stream=True,
                temperature=self.config.temperature,
            )

            async for chunk in stream:
                if chunk.choices[0].delta.content:
                    yield chunk.choices[0].delta.content

        except Exception as e:
            logger.error(f"OpenAI streaming failed: {e}")
            raise LLMError(f"Failed to stream response: {e}") from e
