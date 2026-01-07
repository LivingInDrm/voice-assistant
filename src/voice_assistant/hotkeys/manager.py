"""Global hotkey manager using pynput."""

import platform
import subprocess
from dataclasses import dataclass
from enum import Enum
from typing import Callable, Dict, Optional

from pynput import keyboard


class HotkeyAction(Enum):
    """Available hotkey actions."""
    TOGGLE_RECORDING = "toggle_recording"
    SHOW_WINDOW = "show_window"


@dataclass
class HotkeyConfig:
    """Hotkey configuration."""
    toggle_recording: str = "<cmd>+<shift>+v"
    show_window: str = "<cmd>+<shift>+a"


class HotkeyManager:
    """
    Global hotkey manager for macOS.

    Note: Requires Accessibility permission on macOS.
    """

    def __init__(self, config: Optional[HotkeyConfig] = None):
        """
        Initialize the hotkey manager.

        Args:
            config: Hotkey configuration
        """
        self.config = config or HotkeyConfig()
        self._callbacks: Dict[HotkeyAction, Callable] = {}
        self._hotkeys: Optional[keyboard.GlobalHotKeys] = None
        self._is_running = False

    def register(self, action: HotkeyAction, callback: Callable) -> None:
        """
        Register a callback for a hotkey action.

        Args:
            action: The hotkey action to register
            callback: Function to call when hotkey is pressed
        """
        self._callbacks[action] = callback

    def _on_toggle_recording(self) -> None:
        """Handle toggle recording hotkey."""
        if HotkeyAction.TOGGLE_RECORDING in self._callbacks:
            self._callbacks[HotkeyAction.TOGGLE_RECORDING]()

    def _on_show_window(self) -> None:
        """Handle show window hotkey."""
        if HotkeyAction.SHOW_WINDOW in self._callbacks:
            self._callbacks[HotkeyAction.SHOW_WINDOW]()

    def start(self) -> bool:
        """
        Start listening for hotkeys.

        Returns:
            True if started successfully, False otherwise
        """
        if self._is_running:
            return True

        # Check accessibility permission on macOS
        if platform.system() == "Darwin" and not self.check_accessibility():
            return False

        try:
            hotkey_mapping = {
                self.config.toggle_recording: self._on_toggle_recording,
                self.config.show_window: self._on_show_window,
            }

            self._hotkeys = keyboard.GlobalHotKeys(hotkey_mapping)
            self._hotkeys.start()
            self._is_running = True
            return True

        except Exception as e:
            print(f"Failed to start hotkey listener: {e}")
            return False

    def stop(self) -> None:
        """Stop listening for hotkeys."""
        if self._hotkeys:
            self._hotkeys.stop()
            self._hotkeys = None
        self._is_running = False

    @property
    def is_running(self) -> bool:
        """Check if hotkey listener is running."""
        return self._is_running

    @staticmethod
    def check_accessibility() -> bool:
        """
        Check if the app has Accessibility permission on macOS.

        Returns:
            True if permission is granted, False otherwise
        """
        if platform.system() != "Darwin":
            return True

        try:
            # Try to check using AppleScript
            result = subprocess.run(
                [
                    "osascript",
                    "-e",
                    'tell application "System Events" to return true',
                ],
                capture_output=True,
                text=True,
                timeout=5,
            )
            return result.returncode == 0
        except Exception:
            # If we can't check, assume we have permission
            return True

    @staticmethod
    def request_accessibility() -> None:
        """Open System Preferences to Accessibility settings."""
        if platform.system() == "Darwin":
            subprocess.run([
                "open",
                "x-apple.systempreferences:com.apple.preference.security?Privacy_Accessibility",
            ])

    @staticmethod
    def check_microphone_permission() -> bool:
        """
        Check if the app has microphone permission.

        Returns:
            True if permission is granted
        """
        try:
            import sounddevice as sd
            # Try to open an input stream briefly
            with sd.InputStream(channels=1, blocksize=1024):
                pass
            return True
        except Exception:
            return False

    @staticmethod
    def request_microphone_permission() -> None:
        """Open System Preferences to Microphone settings."""
        if platform.system() == "Darwin":
            subprocess.run([
                "open",
                "x-apple.systempreferences:com.apple.preference.security?Privacy_Microphone",
            ])
