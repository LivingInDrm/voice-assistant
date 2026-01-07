# -*- mode: python ; coding: utf-8 -*-
"""PyInstaller spec file for Voice Assistant."""

import sys
from pathlib import Path

block_cipher = None

# Get the project root
PROJECT_ROOT = Path(SPECPATH)
SRC_DIR = PROJECT_ROOT / 'src'

a = Analysis(
    [str(PROJECT_ROOT / 'run.py')],
    pathex=[str(SRC_DIR), str(PROJECT_ROOT)],
    binaries=[],
    datas=[],
    hiddenimports=[
        # MLX modules
        'mlx',
        'mlx.core',
        'mlx.nn',
        'mlx_whisper',
        # HuggingFace
        'huggingface_hub',
        'huggingface_hub.constants',
        # PyQt6
        'PyQt6.QtCore',
        'PyQt6.QtGui',
        'PyQt6.QtWidgets',
        'PyQt6.sip',
        # Audio
        'sounddevice',
        '_sounddevice_data',
        # Other
        'numpy',
        'pynput',
        'pynput.keyboard',
        'pynput.keyboard._darwin',
        'pydantic',
        'pydantic_settings',
        'anthropic',
        'openai',
        'dotenv',
        'tqdm',
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[
        'tkinter',
        'matplotlib',
        'PIL',
        'scipy',
        'pandas',
    ],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='Voice Assistant',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,  # UPX can cause issues on macOS
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch='arm64',  # Apple Silicon
    codesign_identity=None,
    entitlements_file=None,
)

coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=False,
    upx_exclude=[],
    name='Voice Assistant',
)

app = BUNDLE(
    coll,
    name='Voice Assistant.app',
    icon=None,  # Will generate icon programmatically
    bundle_identifier='com.voiceassistant.app',
    info_plist={
        'CFBundleName': 'Voice Assistant',
        'CFBundleDisplayName': 'Voice Assistant',
        'CFBundleVersion': '0.1.0',
        'CFBundleShortVersionString': '0.1.0',
        'LSMinimumSystemVersion': '12.0',
        'LSArchitecturePriority': ['arm64'],
        'NSHighResolutionCapable': True,
        'NSMicrophoneUsageDescription': 'Voice Assistant needs microphone access to record and transcribe speech.',
        'NSAppleEventsUsageDescription': 'Voice Assistant needs accessibility access for global hotkeys.',
    },
)
