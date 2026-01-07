"""LLM-based translation module."""

import asyncio
from dataclasses import dataclass
from typing import AsyncIterator, Optional

from ..config.settings import LLMProvider


@dataclass
class TranslationResult:
    """Result of text translation."""
    original: str
    translated: str
    provider: str
    source_language: str
    target_language: str


class Translator:
    """
    LLM-based translator supporting Claude and OpenAI.
    """

    SYSTEM_PROMPT = """You are a professional translator.
Translate the following text to {target_language}.
Only output the translation, no explanations or additional text.
Maintain the original tone and style."""

    def __init__(
        self,
        provider: LLMProvider = LLMProvider.CLAUDE,
        api_key: Optional[str] = None,
        target_language: str = "English",
    ):
        """
        Initialize the translator.

        Args:
            provider: LLM provider to use
            api_key: API key for the provider
            target_language: Target language for translation
        """
        self.provider = provider
        self.api_key = api_key
        self.target_language = target_language
        self._client = None

    def _get_system_prompt(self) -> str:
        """Get the system prompt with target language."""
        return self.SYSTEM_PROMPT.format(target_language=self.target_language)

    def _init_client(self) -> None:
        """Initialize the API client."""
        if self._client is not None:
            return

        if self.provider == LLMProvider.CLAUDE:
            import anthropic
            self._client = anthropic.AsyncAnthropic(api_key=self.api_key)
        else:
            from openai import AsyncOpenAI
            self._client = AsyncOpenAI(api_key=self.api_key)

    async def translate(self, text: str) -> TranslationResult:
        """
        Translate text to target language.

        Args:
            text: Text to translate

        Returns:
            TranslationResult with original and translated text
        """
        self._init_client()

        if self.provider == LLMProvider.CLAUDE:
            translated = await self._translate_claude(text)
        else:
            translated = await self._translate_openai(text)

        return TranslationResult(
            original=text,
            translated=translated,
            provider=self.provider.value,
            source_language="auto",
            target_language=self.target_language,
        )

    async def _translate_claude(self, text: str) -> str:
        """Translate using Claude API."""
        message = await self._client.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=1024,
            system=self._get_system_prompt(),
            messages=[{"role": "user", "content": text}],
        )
        return message.content[0].text

    async def _translate_openai(self, text: str) -> str:
        """Translate using OpenAI API."""
        response = await self._client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": self._get_system_prompt()},
                {"role": "user", "content": text},
            ],
        )
        return response.choices[0].message.content

    async def translate_stream(self, text: str) -> AsyncIterator[str]:
        """
        Translate text with streaming output.

        Args:
            text: Text to translate

        Yields:
            Translation chunks as they become available
        """
        self._init_client()

        if self.provider == LLMProvider.CLAUDE:
            async for chunk in self._translate_claude_stream(text):
                yield chunk
        else:
            async for chunk in self._translate_openai_stream(text):
                yield chunk

    async def _translate_claude_stream(self, text: str) -> AsyncIterator[str]:
        """Stream translation using Claude API."""
        async with self._client.messages.stream(
            model="claude-sonnet-4-20250514",
            max_tokens=1024,
            system=self._get_system_prompt(),
            messages=[{"role": "user", "content": text}],
        ) as stream:
            async for chunk in stream.text_stream:
                yield chunk

    async def _translate_openai_stream(self, text: str) -> AsyncIterator[str]:
        """Stream translation using OpenAI API."""
        stream = await self._client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": self._get_system_prompt()},
                {"role": "user", "content": text},
            ],
            stream=True,
        )
        async for chunk in stream:
            if chunk.choices[0].delta.content:
                yield chunk.choices[0].delta.content

    def translate_sync(self, text: str) -> TranslationResult:
        """
        Synchronous translation (convenience wrapper).

        Args:
            text: Text to translate

        Returns:
            TranslationResult
        """
        return asyncio.run(self.translate(text))

    def change_provider(
        self,
        provider: LLMProvider,
        api_key: Optional[str] = None,
    ) -> None:
        """
        Change the LLM provider.

        Args:
            provider: New provider to use
            api_key: API key for the new provider
        """
        self.provider = provider
        if api_key:
            self.api_key = api_key
        self._client = None  # Reset client

    def change_target_language(self, language: str) -> None:
        """
        Change the target translation language.

        Args:
            language: New target language
        """
        self.target_language = language
