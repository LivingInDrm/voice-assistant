"""Background worker for speech transcription."""

from typing import Optional

import numpy as np
from PyQt6.QtCore import QObject, QThread, pyqtSignal

from ..core.transcriber import TranscriptionResult, Transcriber
from ..config.settings import WhisperModel


class TranscriptionWorker(QObject):
    """
    Worker for running Whisper transcription in background thread.

    Signals:
        started: Emitted when processing begins
        progress: Emitted with progress message
        finished: Emitted with TranscriptionResult on completion
        error: Emitted with error message on failure
    """

    started = pyqtSignal()
    progress = pyqtSignal(str)
    finished = pyqtSignal(object)  # TranscriptionResult
    error = pyqtSignal(str)

    def __init__(
        self,
        model_size: WhisperModel = WhisperModel.SMALL,
        language: str = "zh",
    ):
        super().__init__()
        self.transcriber = Transcriber(model_size=model_size, language=language)
        self._audio_data: Optional[np.ndarray] = None
        self._sample_rate: int = 16000

    def set_audio(self, audio: np.ndarray, sample_rate: int = 16000) -> None:
        """
        Set the audio data to transcribe.

        Args:
            audio: Audio samples as numpy array
            sample_rate: Sample rate of the audio
        """
        self._audio_data = audio
        self._sample_rate = sample_rate

    def run(self) -> None:
        """Execute transcription (called from thread)."""
        if self._audio_data is None or len(self._audio_data) == 0:
            self.error.emit("No audio data to transcribe")
            return

        try:
            self.started.emit()
            self.progress.emit("Loading model...")

            # Ensure model is loaded
            if not self.transcriber.is_loaded:
                self.transcriber.load_model()

            self.progress.emit("Transcribing...")

            result = self.transcriber.transcribe(
                self._audio_data,
                sample_rate=self._sample_rate,
            )

            self.finished.emit(result)

        except Exception as e:
            self.error.emit(f"Transcription failed: {str(e)}")

        finally:
            self._audio_data = None

    def change_model(self, model_size: WhisperModel) -> None:
        """Change the Whisper model size."""
        self.transcriber.change_model(model_size)

    def change_language(self, language: str) -> None:
        """Change the source language."""
        self.transcriber.change_language(language)


class TranscriptionThread(QThread):
    """
    Thread for running Whisper transcription in background.

    Usage:
        thread = TranscriptionThread()
        thread.result_ready.connect(handle_result)
        thread.error_occurred.connect(handle_error)
        thread.set_audio(audio_data)
        thread.start()
    """

    result_ready = pyqtSignal(object)  # TranscriptionResult
    error_occurred = pyqtSignal(str)
    progress_update = pyqtSignal(str)

    def __init__(
        self,
        model_size: WhisperModel = WhisperModel.SMALL,
        language: str = "zh",
        parent: Optional[QObject] = None,
    ):
        super().__init__(parent)
        self._transcriber = Transcriber(model_size=model_size, language=language)
        self._audio_data: Optional[np.ndarray] = None
        self._sample_rate: int = 16000

    def set_audio(self, audio: np.ndarray, sample_rate: int = 16000) -> None:
        """Set audio data to transcribe."""
        self._audio_data = audio
        self._sample_rate = sample_rate

    def run(self) -> None:
        """Thread entry point - runs transcription directly."""
        if self._audio_data is None or len(self._audio_data) == 0:
            self.error_occurred.emit("No audio data to transcribe")
            return

        try:
            self.progress_update.emit("Loading model...")

            if not self._transcriber.is_loaded:
                self._transcriber.load_model()

            self.progress_update.emit("Transcribing...")

            result = self._transcriber.transcribe(
                self._audio_data,
                sample_rate=self._sample_rate,
            )

            self.result_ready.emit(result)

        except Exception as e:
            self.error_occurred.emit(f"Transcription failed: {str(e)}")

        finally:
            # Clear audio data after processing
            self._audio_data = None

    def change_model(self, model_size: WhisperModel) -> None:
        """Change the Whisper model."""
        self._transcriber.change_model(model_size)

    def change_language(self, language: str) -> None:
        """Change the source language."""
        self._transcriber.change_language(language)
