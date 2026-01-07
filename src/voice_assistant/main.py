"""Main entry point for Voice Assistant."""

import sys

from PyQt6.QtWidgets import QApplication

from .app import VoiceAssistantApp


def main() -> int:
    """
    Main entry point.

    Returns:
        Exit code (0 for success)
    """
    # Create Qt application
    app = QApplication(sys.argv)
    app.setApplicationName("Voice Assistant")
    app.setOrganizationName("VoiceAssistant")

    # Don't quit when last window is closed (we have system tray)
    app.setQuitOnLastWindowClosed(False)

    # Create and initialize the app controller
    voice_app = VoiceAssistantApp()

    if not voice_app.initialize():
        return 1

    # Start the application
    voice_app.start()

    # Run event loop
    exit_code = app.exec()

    # Cleanup
    voice_app.cleanup()

    return exit_code


if __name__ == "__main__":
    sys.exit(main())
