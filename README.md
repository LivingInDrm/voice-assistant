# Voice Assistant

A local voice input assistant that transcribes speech to text using Whisper, with optional Chinese to English translation.

## Features

- **Local Speech Recognition**: Uses Whisper models running locally on your Mac (Apple Silicon optimized)
- **Real-time Transcription**: Record and transcribe speech with a button click or hotkey
- **Optional Translation**: Translate Chinese text to English using Claude or OpenAI
- **System Tray**: Runs in background with quick access via system tray
- **Global Hotkeys**: Control recording from anywhere with Cmd+Shift+V

## Requirements

- macOS (Apple Silicon recommended)
- Python 3.11+
- Microphone access

## Installation

```bash
# Install system dependencies
brew install portaudio ffmpeg

# Create virtual environment
python3 -m venv .venv
source .venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Install in development mode
pip install -e .
```

## Configuration

Create a `.env` file based on `.env.example`:

```bash
cp .env.example .env
```

Configure your API keys for translation (optional):
- `ANTHROPIC_API_KEY` - For Claude translation
- `OPENAI_API_KEY` - For GPT translation

## Usage

```bash
# Activate virtual environment
source .venv/bin/activate

# Run the application
voice-assistant

# Or run directly
python -m voice_assistant.main
```

### Hotkeys

- `Cmd+Shift+V` - Toggle recording
- `Cmd+Shift+A` - Show/hide window

### Whisper Models

| Model | Parameters | Memory | Speed | Quality |
|-------|-----------|--------|-------|---------|
| tiny | 39M | ~1GB | Fastest | Basic |
| base | 74M | ~1GB | Very Fast | Good |
| **small** | 244M | ~2GB | Fast | Very Good |
| medium | 769M | ~5GB | Moderate | Excellent |
| large-v3 | 1550M | ~10GB | Slow | Best |

Default: `small` (recommended for most users)

## Project Structure

```
voice_assistant/
├── src/voice_assistant/
│   ├── main.py           # Entry point
│   ├── app.py            # Application controller
│   ├── core/             # Core modules
│   │   ├── audio_recorder.py
│   │   ├── transcriber.py
│   │   └── translator.py
│   ├── ui/               # User interface
│   │   └── main_window.py
│   ├── workers/          # Background threads
│   └── hotkeys/          # Global hotkey handling
├── pyproject.toml
└── requirements.txt
```

## License

MIT
