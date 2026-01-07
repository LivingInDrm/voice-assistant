#!/usr/bin/env python3
"""Entry point for PyInstaller packaging."""

import sys
from pathlib import Path

# Add src to path for imports
src_dir = Path(__file__).parent / 'src'
if src_dir.exists():
    sys.path.insert(0, str(src_dir))

from voice_assistant.main import main

if __name__ == "__main__":
    sys.exit(main())
