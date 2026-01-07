"""Background worker for model downloading."""

from typing import Optional

from PyQt6.QtCore import QThread, pyqtSignal

from ..config.settings import WhisperModel
from ..core.model_manager import ModelManager


class ModelDownloadThread(QThread):
    """
    Thread for downloading Whisper models in background.

    Signals:
        progress_update: Emitted with status text during download
        download_finished: Emitted with (model, success) when download completes
        error_occurred: Emitted with error message on failure
    """

    progress_update = pyqtSignal(str)
    download_finished = pyqtSignal(object, bool)  # (WhisperModel, success)
    error_occurred = pyqtSignal(str)

    def __init__(
        self,
        model: WhisperModel,
        parent=None,
    ):
        super().__init__(parent)
        self._model = model

    @property
    def model(self) -> WhisperModel:
        """Get the model being downloaded."""
        return self._model

    def run(self) -> None:
        """Thread entry point - downloads the model."""
        try:
            self.progress_update.emit(f"Downloading {self._model.display_name}...")

            # Perform the download
            ModelManager.download_model(
                self._model,
                progress_callback=self._on_progress,
            )

            self.download_finished.emit(self._model, True)

        except Exception as e:
            self.error_occurred.emit(f"Download failed: {str(e)}")
            self.download_finished.emit(self._model, False)

    def _on_progress(self, message: str) -> None:
        """Handle progress updates from ModelManager."""
        self.progress_update.emit(message)
