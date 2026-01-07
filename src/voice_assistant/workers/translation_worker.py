"""Background worker for text translation."""

import asyncio
from typing import Optional

from PyQt6.QtCore import QThread, QObject, pyqtSignal

from ..core.translator import Translator, TranslationResult
from ..config.settings import LLMProvider


class TranslationThread(QThread):
    """
    Thread for running LLM translation in background.

    Usage:
        thread = TranslationThread(translator)
        thread.result_ready.connect(handle_result)
        thread.error_occurred.connect(handle_error)
        thread.set_text("要翻译的文本")
        thread.start()
    """

    result_ready = pyqtSignal(object)  # TranslationResult
    error_occurred = pyqtSignal(str)
    progress_update = pyqtSignal(str)

    def __init__(
        self,
        translator: Translator,
        parent: Optional[QObject] = None,
    ):
        super().__init__(parent)
        self._translator = translator
        self._text: Optional[str] = None

    def set_text(self, text: str) -> None:
        """Set the text to translate."""
        self._text = text

    def run(self) -> None:
        """Thread entry point - runs translation."""
        if not self._text:
            self.error_occurred.emit("No text to translate")
            return

        try:
            self.progress_update.emit("Translating...")

            # Create a new event loop for this thread
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)

            try:
                result = loop.run_until_complete(
                    self._translator.translate(self._text)
                )
                self.result_ready.emit(result)
            finally:
                loop.close()

        except Exception as e:
            self.error_occurred.emit(f"Translation failed: {str(e)}")

        finally:
            self._text = None
