#!/usr/bin/env python3
"""Compatibility wrapper for v1.5+.

The protocol-valid path is now scripts/run_v13_keyword_counts_frozen.py,
which consumes frozen extracted text and implements exact case-insensitive
regex matching with alphanumeric boundaries.
"""
from __future__ import annotations

import sys
from pathlib import Path

# Allow direct execution from the scripts directory.
sys.path.insert(0, str(Path(__file__).resolve().parent))
from run_v13_keyword_counts_frozen import main  # noqa: E402

if __name__ == "__main__":
    raise SystemExit(main())
