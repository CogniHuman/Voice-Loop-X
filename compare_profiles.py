#!/usr/bin/env python3
"""
Convenience wrapper for comparing VoiceLoop-X profile JSON files
from a source checkout without installing the package.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent / "src"))

from voiceloop.profile_tools import main


if __name__ == "__main__":
    main()
