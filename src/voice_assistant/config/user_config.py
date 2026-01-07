"""User configuration management with JSON persistence."""

import json
from pathlib import Path
from typing import Optional

from .settings import LLMProvider


class UserConfig:
    """Manages user-editable configuration stored in ~/.voice_assistant/config.json."""

    CONFIG_DIR = Path.home() / ".voice_assistant"
    CONFIG_FILE = CONFIG_DIR / "config.json"

    def __init__(self):
        self._anthropic_api_key: Optional[str] = None
        self._openai_api_key: Optional[str] = None
        self._translation_provider: str = LLMProvider.CLAUDE.value
        self.load()

    def load(self) -> None:
        """Load configuration from JSON file."""
        if not self.CONFIG_FILE.exists():
            return

        try:
            with open(self.CONFIG_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
            self._anthropic_api_key = data.get("anthropic_api_key")
            self._openai_api_key = data.get("openai_api_key")
            self._translation_provider = data.get(
                "translation_provider", LLMProvider.CLAUDE.value
            )
        except (json.JSONDecodeError, IOError):
            pass

    def save(self) -> None:
        """Save configuration to JSON file."""
        self.CONFIG_DIR.mkdir(parents=True, exist_ok=True)

        data = {
            "anthropic_api_key": self._anthropic_api_key,
            "openai_api_key": self._openai_api_key,
            "translation_provider": self._translation_provider,
        }

        with open(self.CONFIG_FILE, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)

    @property
    def anthropic_api_key(self) -> Optional[str]:
        return self._anthropic_api_key

    @anthropic_api_key.setter
    def anthropic_api_key(self, value: Optional[str]) -> None:
        self._anthropic_api_key = value if value else None

    @property
    def openai_api_key(self) -> Optional[str]:
        return self._openai_api_key

    @openai_api_key.setter
    def openai_api_key(self, value: Optional[str]) -> None:
        self._openai_api_key = value if value else None

    @property
    def translation_provider(self) -> str:
        return self._translation_provider

    @translation_provider.setter
    def translation_provider(self, value: str) -> None:
        self._translation_provider = value

    def get_api_key(self, provider: LLMProvider) -> Optional[str]:
        """Get API key for the specified provider."""
        if provider == LLMProvider.CLAUDE:
            return self._anthropic_api_key
        return self._openai_api_key

    def set_api_key(self, provider: LLMProvider, key: Optional[str]) -> None:
        """Set API key for the specified provider."""
        if provider == LLMProvider.CLAUDE:
            self._anthropic_api_key = key if key else None
        else:
            self._openai_api_key = key if key else None


_user_config: Optional[UserConfig] = None


def get_user_config() -> UserConfig:
    """Get singleton UserConfig instance."""
    global _user_config
    if _user_config is None:
        _user_config = UserConfig()
    return _user_config
