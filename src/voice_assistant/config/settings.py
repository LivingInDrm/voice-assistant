"""Application settings using pydantic-settings."""

from enum import Enum
from functools import lru_cache
from pathlib import Path
from typing import Optional

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class WhisperModel(str, Enum):
    """Available Whisper model sizes."""
    SMALL = "small"
    LARGE = "large"

    @property
    def display_name(self) -> str:
        """Human-readable name for UI."""
        names = {
            WhisperModel.SMALL: "Small (快速)",
            WhisperModel.LARGE: "Large (高精度)",
        }
        return names.get(self, self.value)

    @property
    def hf_repo(self) -> str:
        """HuggingFace repository path."""
        repos = {
            WhisperModel.SMALL: "mlx-community/whisper-small-mlx",
            WhisperModel.LARGE: "mlx-community/whisper-large-v3-turbo",
        }
        return repos.get(self, "")

    @property
    def size_mb(self) -> int:
        """Approximate download size in MB."""
        sizes = {
            WhisperModel.SMALL: 500,
            WhisperModel.LARGE: 1600,
        }
        return sizes.get(self, 0)


class LLMProvider(str, Enum):
    """Available LLM providers for translation."""
    CLAUDE = "claude"
    OPENAI = "openai"


class Settings(BaseSettings):
    """Application settings."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
    )

    # Whisper settings
    whisper_model: WhisperModel = Field(
        default=WhisperModel.SMALL,
        description="Whisper model size to use"
    )
    whisper_language: str = Field(
        default="zh",
        description="Source language for transcription"
    )

    # LLM API Keys
    anthropic_api_key: Optional[str] = Field(
        default=None,
        description="Anthropic API key for Claude"
    )
    openai_api_key: Optional[str] = Field(
        default=None,
        description="OpenAI API key"
    )

    # Translation settings
    translation_enabled: bool = Field(
        default=False,
        description="Enable translation feature"
    )
    translation_provider: LLMProvider = Field(
        default=LLMProvider.CLAUDE,
        description="LLM provider for translation"
    )
    translation_target_language: str = Field(
        default="en",
        description="Target language for translation"
    )

    # Hotkeys
    hotkey_toggle_recording: str = Field(
        default="<cmd>+<shift>+v",
        description="Hotkey to toggle recording"
    )
    hotkey_show_window: str = Field(
        default="<cmd>+<shift>+a",
        description="Hotkey to show/hide window"
    )

    # Audio settings
    audio_sample_rate: int = Field(
        default=16000,
        description="Audio sample rate (Whisper requires 16kHz)"
    )
    audio_channels: int = Field(
        default=1,
        description="Number of audio channels (mono)"
    )
    max_recording_duration: float = Field(
        default=120.0,
        description="Maximum recording duration in seconds"
    )

    # UI settings
    window_always_on_top: bool = Field(
        default=False,
        description="Keep window always on top"
    )
    minimize_to_tray: bool = Field(
        default=True,
        description="Minimize to system tray on close"
    )

    @property
    def has_claude_key(self) -> bool:
        """Check if Claude API key is configured (user config or env)."""
        from .user_config import get_user_config
        user_config = get_user_config()
        return bool(user_config.anthropic_api_key or self.anthropic_api_key)

    @property
    def has_openai_key(self) -> bool:
        """Check if OpenAI API key is configured (user config or env)."""
        from .user_config import get_user_config
        user_config = get_user_config()
        return bool(user_config.openai_api_key or self.openai_api_key)

    def get_claude_key(self) -> Optional[str]:
        """Get Claude API key (user config takes priority)."""
        from .user_config import get_user_config
        user_config = get_user_config()
        return user_config.anthropic_api_key or self.anthropic_api_key

    def get_openai_key(self) -> Optional[str]:
        """Get OpenAI API key (user config takes priority)."""
        from .user_config import get_user_config
        user_config = get_user_config()
        return user_config.openai_api_key or self.openai_api_key

    def get_translation_provider(self) -> "LLMProvider":
        """Get translation provider (user config takes priority)."""
        from .user_config import get_user_config
        user_config = get_user_config()
        provider_value = user_config.translation_provider
        if provider_value:
            return LLMProvider(provider_value)
        return self.translation_provider

    @property
    def can_translate(self) -> bool:
        """Check if translation is possible."""
        provider = self.get_translation_provider()
        if provider == LLMProvider.CLAUDE:
            return self.has_claude_key
        return self.has_openai_key


@lru_cache
def get_settings() -> Settings:
    """Get cached settings instance."""
    return Settings()
