"""Speech-to-text transcription using Whisper."""

import time
from dataclasses import dataclass
from typing import Optional

import numpy as np

from ..config.settings import WhisperModel


@dataclass
class TranscriptionResult:
    """Result of speech transcription."""
    text: str
    language: str
    duration: float  # Processing time in seconds
    audio_duration: float  # Length of audio in seconds


class Transcriber:
    """
    Whisper-based speech transcriber.

    Uses mlx-whisper for Apple Silicon optimization.
    """

    def __init__(
        self,
        model_size: WhisperModel = WhisperModel.SMALL,
        language: str = "zh",
    ):
        """
        Initialize the transcriber.

        Args:
            model_size: Whisper model size to use
            language: Source language code (e.g., "zh", "en")
        """
        self.model_size = model_size
        self.language = language
        self._model_path: Optional[str] = None
        self._is_loaded = False

    def load_model(self) -> None:
        """
        Load the Whisper model.

        Model will be downloaded from HuggingFace on first use.
        """
        if self._is_loaded:
            return

        # Use the HuggingFace repo path from the model enum
        self._model_path = self.model_size.hf_repo
        self._is_loaded = True

    def transcribe(
        self,
        audio: np.ndarray,
        sample_rate: int = 16000,
    ) -> TranscriptionResult:
        """
        Transcribe audio to text.

        Args:
            audio: Audio samples as numpy array (float32, mono)
            sample_rate: Sample rate of the audio (default 16kHz)

        Returns:
            TranscriptionResult with text and metadata
        """
        import mlx_whisper

        if not self._is_loaded:
            self.load_model()

        # Calculate audio duration
        audio_duration = len(audio) / sample_rate

        start_time = time.time()

        result = mlx_whisper.transcribe(
            audio,
            path_or_hf_repo=self._model_path,
            language=self.language,
            fp16=True,  # Use half precision for speed
        )

        processing_duration = time.time() - start_time

        return TranscriptionResult(
            text=result["text"].strip(),
            language=result.get("language", self.language),
            duration=processing_duration,
            audio_duration=audio_duration,
        )

    def change_model(self, model_size: WhisperModel) -> None:
        """
        Change the Whisper model size.

        Args:
            model_size: New model size to use
        """
        if model_size != self.model_size:
            self.model_size = model_size
            self._is_loaded = False
            self._model_path = None

    def change_language(self, language: str) -> None:
        """
        Change the source language.

        Args:
            language: New language code
        """
        self.language = language

    @property
    def is_loaded(self) -> bool:
        """Check if model is loaded."""
        return self._is_loaded

    @staticmethod
    def get_model_info(model_size: WhisperModel) -> dict:
        """
        Get information about a Whisper model.

        Args:
            model_size: Model size to get info for

        Returns:
            Dict with model parameters, memory requirements, etc.
        """
        info = {
            WhisperModel.SMALL: {
                "parameters": "244M",
                "memory": "~2GB",
                "speed": "fast",
                "quality": "very good",
            },
            WhisperModel.LARGE: {
                "parameters": "809M",
                "memory": "~6GB",
                "speed": "fast",
                "quality": "excellent",
            },
        }
        return info.get(model_size, {})
