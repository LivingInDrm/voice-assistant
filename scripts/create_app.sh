#!/bin/bash
# Create macOS .app bundle for Voice Assistant

APP_NAME="Voice Assistant"
APP_DIR="$HOME/Applications/${APP_NAME}.app"
CONTENTS_DIR="${APP_DIR}/Contents"
MACOS_DIR="${CONTENTS_DIR}/MacOS"
RESOURCES_DIR="${CONTENTS_DIR}/Resources"

# Get the project directory (where this script lives)
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"
VENV_DIR="${PROJECT_DIR}/.venv"

echo "Creating ${APP_NAME}.app in ~/Applications..."

# Create directory structure
mkdir -p "${MACOS_DIR}"
mkdir -p "${RESOURCES_DIR}"

# Create launcher script
cat > "${MACOS_DIR}/${APP_NAME}" << 'LAUNCHER'
#!/bin/bash
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
APP_DIR="$(dirname "$(dirname "$SCRIPT_DIR")")"

# Read the project path from config
PROJECT_DIR="$(cat "${APP_DIR}/../.voice-assistant-path" 2>/dev/null || echo "$HOME/program/voice_assistant")"
VENV_DIR="${PROJECT_DIR}/.venv"

# Activate venv and run
source "${VENV_DIR}/bin/activate"
exec python -m voice_assistant.main
LAUNCHER

chmod +x "${MACOS_DIR}/${APP_NAME}"

# Save project path
echo "${PROJECT_DIR}" > "$HOME/Applications/.voice-assistant-path"

# Create Info.plist
cat > "${CONTENTS_DIR}/Info.plist" << PLIST
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>CFBundleExecutable</key>
    <string>${APP_NAME}</string>
    <key>CFBundleIdentifier</key>
    <string>com.voiceassistant.app</string>
    <key>CFBundleName</key>
    <string>${APP_NAME}</string>
    <key>CFBundleDisplayName</key>
    <string>${APP_NAME}</string>
    <key>CFBundlePackageType</key>
    <string>APPL</string>
    <key>CFBundleVersion</key>
    <string>0.1.0</string>
    <key>CFBundleShortVersionString</key>
    <string>0.1.0</string>
    <key>LSMinimumSystemVersion</key>
    <string>12.0</string>
    <key>LSUIElement</key>
    <false/>
    <key>NSHighResolutionCapable</key>
    <true/>
    <key>NSMicrophoneUsageDescription</key>
    <string>Voice Assistant needs microphone access to record and transcribe speech.</string>
    <key>NSAppleEventsUsageDescription</key>
    <string>Voice Assistant needs accessibility access for global hotkeys.</string>
</dict>
</plist>
PLIST

echo "✓ Created ${APP_DIR}"
echo ""
echo "You can now:"
echo "  1. Open ~/Applications in Finder"
echo "  2. Drag 'Voice Assistant' to your Dock"
echo ""
echo "To run: open '${APP_DIR}'"
