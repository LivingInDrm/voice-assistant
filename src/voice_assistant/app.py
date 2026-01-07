"""Main application controller."""

from typing import Optional

from PyQt6.QtCore import QObject, QTimer, pyqtSlot
from PyQt6.QtWidgets import QApplication, QMessageBox

from .config.settings import Settings, WhisperModel, get_settings
from .core.audio_recorder import AudioRecorder, AudioConfig
from .core.model_manager import ModelManager
from .core.translator import Translator
from .hotkeys.manager import HotkeyManager, HotkeyAction
from .ui.main_window import MainWindow
from .workers.download_worker import ModelDownloadThread
from .workers.transcription_worker import TranscriptionThread
from .workers.translation_worker import TranslationThread


class VoiceAssistantApp(QObject):
    """
    Main application controller.

    Coordinates between UI, audio recording, transcription, and translation.
    """

    def __init__(self):
        super().__init__()

        self.settings = get_settings()

        # Components
        self.window: Optional[MainWindow] = None
        self.recorder: Optional[AudioRecorder] = None
        self.transcription_thread: Optional[TranscriptionThread] = None
        self.translator: Optional[Translator] = None
        self.translation_thread: Optional[TranslationThread] = None
        self.hotkey_manager: Optional[HotkeyManager] = None
        self.download_thread: Optional[ModelDownloadThread] = None

        # State
        self._is_recording = False
        self._current_model: WhisperModel = self.settings.whisper_model

    def initialize(self) -> bool:
        """
        Initialize all application components.

        Returns:
            True if initialization successful
        """
        # Check permissions
        if not self._check_permissions():
            return False

        # Initialize UI
        self.window = MainWindow()
        self._connect_window_signals()

        # Initialize audio recorder
        self.recorder = AudioRecorder(
            config=AudioConfig(
                sample_rate=self.settings.audio_sample_rate,
                channels=self.settings.audio_channels,
            ),
            on_volume_change=self._on_volume_change,
        )

        # Initialize transcription worker
        self.transcription_thread = TranscriptionThread(
            model_size=self.settings.whisper_model,
            language=self.settings.whisper_language,
        )
        self._connect_transcription_signals()

        # Initialize translator if API key available
        self._init_translator()

        # Initialize hotkeys
        self.hotkey_manager = HotkeyManager()
        self.hotkey_manager.register(
            HotkeyAction.TOGGLE_RECORDING,
            self._on_hotkey_toggle_recording,
        )
        self.hotkey_manager.register(
            HotkeyAction.SHOW_WINDOW,
            self._on_hotkey_show_window,
        )

        return True

    def _check_permissions(self) -> bool:
        """Check required system permissions."""
        # Check microphone permission
        if not HotkeyManager.check_microphone_permission():
            reply = QMessageBox.question(
                None,
                "Microphone Permission Required",
                "This app needs microphone access to record audio.\n\n"
                "Would you like to open System Preferences?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            )
            if reply == QMessageBox.StandardButton.Yes:
                HotkeyManager.request_microphone_permission()
            return False

        return True

    def _connect_window_signals(self) -> None:
        """Connect window signals to handlers."""
        self.window.recording_started.connect(self._start_recording)
        self.window.recording_stopped.connect(self._stop_recording)
        self.window.model_changed.connect(self._on_model_changed)
        self.window.translation_toggled.connect(self._on_translation_toggled)
        self.window.settings_changed.connect(self._on_settings_changed)

    def _connect_transcription_signals(self) -> None:
        """Connect transcription worker signals."""
        self.transcription_thread.result_ready.connect(self._on_transcription_result)
        self.transcription_thread.error_occurred.connect(self._on_transcription_error)
        self.transcription_thread.progress_update.connect(self._on_transcription_progress)

    def start(self) -> None:
        """Start the application."""
        # Start hotkey listener
        if self.hotkey_manager:
            if not self.hotkey_manager.start():
                self.window.set_status(
                    "Warning: Hotkeys disabled (Accessibility permission needed)"
                )

        # Check model download status and update UI
        self._update_model_status()

        # Show window
        self.window.show()

    def _update_model_status(self) -> None:
        """Update UI with model download status."""
        for model in WhisperModel:
            downloaded = ModelManager.is_model_downloaded(model)
            self.window.set_model_downloaded(model.value, downloaded)

        # Check if current model is downloaded
        current_downloaded = ModelManager.is_model_downloaded(self._current_model)
        self.window.set_record_enabled(current_downloaded)

        if not current_downloaded:
            self.window.set_status(f"Model {self._current_model.value} not downloaded")

    def _on_volume_change(self, level: float) -> None:
        """Handle volume level update from recorder."""
        if self.window:
            # Convert 0-1 to 0-100
            self.window.set_volume(int(level * 100))

    @pyqtSlot()
    def _start_recording(self) -> None:
        """Start audio recording."""
        if self._is_recording:
            return

        self._is_recording = True
        self.recorder.start()
        self.window.set_status("Recording... Speak now")

    @pyqtSlot()
    def _stop_recording(self) -> None:
        """Stop recording and start transcription."""
        if not self._is_recording:
            return

        self._is_recording = False

        # Get recorded audio
        audio_data = self.recorder.stop()

        if len(audio_data) == 0:
            self.window.set_status("No audio recorded")
            self.window.reset_recording_state()
            return

        # Check minimum audio length (0.5 seconds)
        min_samples = int(0.5 * self.settings.audio_sample_rate)
        if len(audio_data) < min_samples:
            self.window.set_status("Recording too short")
            self.window.reset_recording_state()
            return

        # Start transcription in background
        self.window.set_status("Processing...")
        self.transcription_thread.set_audio(
            audio_data,
            self.settings.audio_sample_rate,
        )
        self.transcription_thread.start()

    @pyqtSlot(object)
    def _on_transcription_result(self, result) -> None:
        """Handle transcription result."""
        self.window.set_transcription(result.text)
        self.window.set_processing_time(result.duration, result.audio_duration)
        self.window.reset_recording_state()

        # Translate if enabled
        if self.settings.translation_enabled and self.translator and result.text:
            self._translate_text(result.text)

    @pyqtSlot(str)
    def _on_transcription_error(self, error: str) -> None:
        """Handle transcription error."""
        self.window.set_status(f"Error: {error}")
        self.window.reset_recording_state()

    @pyqtSlot(str)
    def _on_transcription_progress(self, message: str) -> None:
        """Handle transcription progress update."""
        self.window.set_status(message)

    @pyqtSlot(str)
    def _on_model_changed(self, model: str) -> None:
        """Handle model selection change."""
        try:
            model_enum = WhisperModel(model)
            self._current_model = model_enum

            if ModelManager.is_model_downloaded(model_enum):
                # Model is downloaded, switch to it
                self.transcription_thread.change_model(model_enum)
                self.window.set_record_enabled(True)
                self.window.set_status(f"Model: {model}")
            else:
                # Model not downloaded, start download
                self.window.set_record_enabled(False)
                self._start_model_download(model_enum)
        except ValueError:
            pass

    def _start_model_download(self, model: WhisperModel) -> None:
        """Start downloading a model in the background."""
        # Cancel any existing download
        if self.download_thread and self.download_thread.isRunning():
            self.download_thread.terminate()
            self.download_thread.wait()

        self.download_thread = ModelDownloadThread(model)
        self.download_thread.progress_update.connect(self._on_download_progress)
        self.download_thread.download_finished.connect(self._on_download_finished)
        self.download_thread.error_occurred.connect(self._on_download_error)
        self.download_thread.start()

    @pyqtSlot(str)
    def _on_download_progress(self, message: str) -> None:
        """Handle download progress update."""
        self.window.set_status(message)

    @pyqtSlot(object, bool)
    def _on_download_finished(self, model: WhisperModel, success: bool) -> None:
        """Handle download completion."""
        if success:
            # Update model status in UI
            self.window.set_model_downloaded(model.value, True)

            # If this is the currently selected model, enable recording
            if model == self._current_model:
                self.transcription_thread.change_model(model)
                self.window.set_record_enabled(True)
                self.window.set_status(f"Model {model.value} ready")
        else:
            self.window.set_status(f"Failed to download {model.value}")

    @pyqtSlot(str)
    def _on_download_error(self, error: str) -> None:
        """Handle download error."""
        self.window.set_status(f"Download error: {error}")

    @pyqtSlot(bool)
    def _on_translation_toggled(self, enabled: bool) -> None:
        """Handle translation toggle."""
        self.settings.translation_enabled = enabled

        if enabled and not self.settings.can_translate:
            self.window.set_status(
                "Translation requires API key. Configure in Settings."
            )

    def _init_translator(self) -> None:
        """Initialize or reinitialize the translator with current settings."""
        if self.settings.can_translate:
            provider = self.settings.get_translation_provider()
            api_key = (
                self.settings.get_claude_key()
                if provider.value == "claude"
                else self.settings.get_openai_key()
            )
            self.translator = Translator(
                provider=provider,
                api_key=api_key,
                target_language="English",
            )
        else:
            self.translator = None

    @pyqtSlot()
    def _on_settings_changed(self) -> None:
        """Handle settings change from settings dialog."""
        from .config.user_config import get_user_config
        get_user_config().load()
        self._init_translator()
        if self.settings.can_translate:
            self.window.set_status("API key configured")
        else:
            self.window.set_status("Ready")

    def _translate_text(self, text: str) -> None:
        """Translate text using configured LLM in background thread."""
        if not self.translator:
            return

        # Create new translation thread for each request
        self.translation_thread = TranslationThread(self.translator)
        self.translation_thread.result_ready.connect(self._on_translation_result)
        self.translation_thread.error_occurred.connect(self._on_translation_error)
        self.translation_thread.progress_update.connect(self._on_translation_progress)
        self.translation_thread.set_text(text)
        self.translation_thread.start()

    @pyqtSlot(object)
    def _on_translation_result(self, result) -> None:
        """Handle translation result."""
        self.window.set_translation(result.translated)
        self.window.set_status("Ready")

    @pyqtSlot(str)
    def _on_translation_error(self, error: str) -> None:
        """Handle translation error."""
        self.window.set_status(f"Translation error: {error}")

    @pyqtSlot(str)
    def _on_translation_progress(self, message: str) -> None:
        """Handle translation progress update."""
        self.window.set_status(message)

    def _on_hotkey_toggle_recording(self) -> None:
        """Handle hotkey to toggle recording."""
        if self.window:
            # Use QTimer to ensure we're on the main thread
            QTimer.singleShot(0, self.window.toggle_recording)

    def _on_hotkey_show_window(self) -> None:
        """Handle hotkey to show window."""
        if self.window:
            QTimer.singleShot(0, self._show_window)

    def _show_window(self) -> None:
        """Show and activate the main window."""
        self.window.show()
        self.window.activateWindow()
        self.window.raise_()

    def cleanup(self) -> None:
        """Clean up resources on shutdown."""
        if self.hotkey_manager:
            self.hotkey_manager.stop()

        if self.recorder and self.recorder.is_recording:
            self.recorder.stop()

        # Wait for transcription thread to finish (it runs synchronously in run())
        if self.transcription_thread and self.transcription_thread.isRunning():
            self.transcription_thread.wait(5000)  # Wait up to 5 seconds

        # Wait for translation thread to finish
        if self.translation_thread and self.translation_thread.isRunning():
            self.translation_thread.wait(5000)  # Wait up to 5 seconds

        # Wait for download thread to finish
        if self.download_thread and self.download_thread.isRunning():
            self.download_thread.terminate()
            self.download_thread.wait(5000)
