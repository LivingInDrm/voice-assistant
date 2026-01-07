"""Audio recording module using sounddevice."""

from collections import deque
from dataclasses import dataclass, field
from typing import Callable, Optional

import numpy as np
import sounddevice as sd


@dataclass
class AudioConfig:
    """Audio recording configuration."""
    sample_rate: int = 16000  # Whisper requires 16kHz
    channels: int = 1  # Mono
    dtype: type = np.float32
    block_size: int = 1024  # Samples per callback
    max_duration: float = 120.0  # Max recording duration in seconds


class AudioRecorder:
    """Real-time audio recorder using sounddevice."""

    def __init__(
        self,
        config: Optional[AudioConfig] = None,
        on_volume_change: Optional[Callable[[float], None]] = None,
    ):
        """
        Initialize the audio recorder.

        Args:
            config: Audio configuration settings
            on_volume_change: Callback for volume level updates (0.0-1.0)
        """
        self.config = config or AudioConfig()
        self.on_volume_change = on_volume_change
        self._audio_buffer: deque = deque()
        self._is_recording = False
        self._stream: Optional[sd.InputStream] = None

    def _audio_callback(
        self,
        indata: np.ndarray,
        frames: int,
        time_info: dict,
        status: sd.CallbackFlags,
    ) -> None:
        """Callback function for audio stream."""
        if status:
            print(f"Audio status: {status}")

        # Store audio data
        self._audio_buffer.append(indata.copy())

        # Calculate and report volume level
        if self.on_volume_change:
            # RMS volume calculation
            volume = np.sqrt(np.mean(indata**2))
            # Normalize to 0-1 range (approximate)
            normalized = min(1.0, volume * 10)
            self.on_volume_change(float(normalized))

    def start(self) -> None:
        """Start recording audio."""
        if self._is_recording:
            return

        self._audio_buffer.clear()
        self._stream = sd.InputStream(
            samplerate=self.config.sample_rate,
            channels=self.config.channels,
            dtype=self.config.dtype,
            blocksize=self.config.block_size,
            callback=self._audio_callback,
        )
        self._stream.start()
        self._is_recording = True

    def stop(self) -> np.ndarray:
        """
        Stop recording and return audio data.

        Returns:
            numpy array of audio samples
        """
        if not self._is_recording:
            return np.array([], dtype=np.float32)

        if self._stream:
            self._stream.stop()
            self._stream.close()
            self._stream = None

        self._is_recording = False

        # Concatenate all audio chunks
        if self._audio_buffer:
            audio_data = np.concatenate(list(self._audio_buffer), axis=0)
            self._audio_buffer.clear()
            return audio_data.flatten()

        return np.array([], dtype=np.float32)

    @property
    def is_recording(self) -> bool:
        """Check if currently recording."""
        return self._is_recording

    @staticmethod
    def list_devices() -> list[dict]:
        """List available audio input devices."""
        devices = sd.query_devices()
        input_devices = []
        for i, dev in enumerate(devices):
            if dev["max_input_channels"] > 0:
                input_devices.append({
                    "index": i,
                    "name": dev["name"],
                    "channels": dev["max_input_channels"],
                    "sample_rate": dev["default_samplerate"],
                })
        return input_devices

    @staticmethod
    def get_default_device() -> Optional[dict]:
        """Get default input device info."""
        try:
            device_id = sd.default.device[0]
            if device_id is not None:
                device = sd.query_devices(device_id)
                return {
                    "index": device_id,
                    "name": device["name"],
                    "channels": device["max_input_channels"],
                    "sample_rate": device["default_samplerate"],
                }
        except Exception:
            pass
        return None
